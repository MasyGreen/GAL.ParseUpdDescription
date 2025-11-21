from datetime import datetime, timezone
import os
import threading

from ftplib import FTP
from queue import Queue

from ProjectClass.cl_appmanagement import AppManagement
from ProjectClass.cl_appsettings import AppSettings
from ProjectClass.cl_printmsg import CLPrintMsg
from ProjectClass.cl_uncdate import CLUNCDate

PRINT_LOCK = threading.Lock()


class CLFTPDownloadThread(threading.Thread):
    """Потоковое скачивание файлов с FTP"""

    def __init__(self, name: str, queue, appsettings: AppSettings, appmanagement: AppManagement, printmsg: CLPrintMsg):
        """Инициализация потока"""
        threading.Thread.__init__(self)
        self.name = name
        self.queue = queue
        self.app_settings: AppSettings = appsettings
        self.app_management: AppManagement = appmanagement
        self.printmsg: CLPrintMsg = printmsg

    def run(self):
        """Запуск потока"""
        while True:
            # Получаем параметры из очереди
            params = self.queue.get()

            if params is None:
                self.queue.task_done()
                break

            # Обработка
            self.download(params)

            # Отправляем сигнал о том, что задача завершена
            self.queue.task_done()

    def download(self, params):
        """
        Реализация: загрузка FTP
        :param params:
        :return:
        """
        ftp_name = params.get("filename")

        local_file_path = os.path.join(self.app_management.download_folder, ftp_name)

        # Считаем хеш - чтоб разделить потоки для журнализации
        cur_hash = str(hash(ftp_name))

        with PRINT_LOCK:
            self.printmsg.print_header(f'\t\tFTP ({self.name}|{cur_hash}). {ftp_name}', 1)

        try:
            ftp = FTP(self.app_settings.FTPHost, timeout=400)
            with PRINT_LOCK:
                self.printmsg.print_debug(
                    f"\t\t\tFTP ({self.name}|{cur_hash}). Login: {self.app_settings.FTPHost}, try goto {self.app_settings.FTPDir}. {ftp.login()}",
                    1)
            ftp.cwd(self.app_settings.FTPDir)

            # получить время изменения на сервере (UTC)
            try:
                dt_utc = self.ftp_get_modify_datetime(ftp, ftp_name)
            except Exception as ex:
                self.printmsg.print_error(f'Не удалось получить время с FTP: {ex}')
                dt_utc = None

            # скачать файл корректно (закроет файловый дескриптор)
            with open(local_file_path, 'wb') as f:
                ftp.retrbinary("RETR " + ftp_name, f.write)

            ftp.quit()
            ftp.close()

            file_date = CLUNCDate.unc_to_moskow(dt_utc, self.printmsg)

            dt_epoch = file_date.timestamp()
            os.utime(local_file_path, (dt_epoch, dt_epoch))
            with PRINT_LOCK:
                self.printmsg.print_success(f'\t\t\tFTP ({self.name}|{cur_hash}). {ftp_name}>>>{local_file_path}', 1)

        except Exception as ex:
            with PRINT_LOCK:
                self.printmsg.print_error(f'\t\t\tFTP ({self.name}|{cur_hash}). {type(ex)}')  # the exception instance
                self.printmsg.print_error(f'\t\t\tFTP ({self.name}|{cur_hash}). {ex.args}')  # arguments stored in .args
                self.printmsg.print_error(
                    f'\t\t\tFTP ({self.name}|{cur_hash}). {ex}')  # __str__ allows args to be printed directly,
        finally:
            ftp.close()  # Close FTP connection

    @staticmethod
    def ftp_get_modify_datetime(ftp: FTP, filename: str) -> datetime:
        """
        Попытаться получить время изменения файла с FTP.
        Использует MDTM (возвращает время в UTC по RFC). Возвращает timezone-aware datetime (UTC).
        """
        resp = ftp.sendcmd(f"MDTM {filename}")
        # Ожидается ответ вида: "213 YYYYMMDDHHMMSS"
        if resp.startswith("213 "):
            timestr = resp[4:].strip()
            dt_utc = datetime.strptime(timestr, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            return dt_utc
        raise RuntimeError(f"Unexpected MDTM response: {resp}")


class CLFTPReaderThread:
    """Дополнительный класс работа с FTP"""

    def __init__(self, appsettings: AppSettings, appmanagement: AppManagement, printmsg: CLPrintMsg):
        self.app_settings = appsettings
        self.app_management = appmanagement
        self.printmsg = printmsg

    def download(self, download_list):
        self.printmsg.print_header(f'Start. Загрузка данных FTP')
        try:
            workers = []
            queue = Queue()
            # Запускаем потом и очередь
            for i in range(10):
                t = CLFTPDownloadThread(str(i), queue, self.app_settings, self.app_management, self.printmsg)
                t.daemon = True
                t.start()
                workers.append(t)

            # Даем очереди нужные нам ссылки для скачивания
            for el in download_list:
                queue.put(el)

            for _ in workers:
                queue.put(None)

            # Ждем завершения работы очереди
            queue.join()

            for t in workers:
                t.join()

            self.printmsg.print_success(f'\tЗагружено {len(download_list)} файлов')
        except Exception as ex:
            self.printmsg.print_error(f'\tError: {ex}')

    def get_file_list(self):
        self.printmsg.print_header(f'Start. Получение списка файлов FTP')
        result = []
        try:
            ftp = FTP(self.app_settings.FTPHost)
            self.printmsg.print_debug(
                f"\tLogin to FTP: {self.app_settings.FTPHost}, try goto {self.app_settings.FTPDir}. {ftp.login()}")

            # Список файлов FTP
            files = ftp.mlsd(self.app_settings.FTPDir)

            # Формат: file=('Z_StaffOrders_RES_912720.txt', {'type': 'file', 'size': '1586019', 'modify': '20251114082947'})
            for file in files:
                file_name = file[0]

                if file[1]['type'] == 'file' and file_name.lower().find('.txt') != -1:
                    # Дата\время файла
                    time_stamp = file[1]['modify']
                    dt = datetime.strptime(str(int(time_stamp)), '%Y%m%d%H%M%S')

                    dt = CLUNCDate.unc_to_moskow(dt, self.printmsg)

                    # Полный путь к FTP, имя файла, дата
                    _row = {"filepath": f'{self.app_settings.FTPHost}/{self.app_settings.FTPDir}/{file_name}',
                            "filename": file_name,
                            "filedate": dt
                            }
                    result.append(_row)

                    ftp.close()
            self.printmsg.print_success(f'\tКол-во файлов: {len(result)}')
        except Exception as ex:
            self.printmsg.print_error(f'\t{type(ex)}')  # the exception instance
            self.printmsg.print_error(f'\t{ex.args}')  # arguments stored in .args
            self.printmsg.print_error(f'\t{ex}')  # __str__ allows args to be printed directly,

        return sorted(result, key=lambda item: item['filename'])
