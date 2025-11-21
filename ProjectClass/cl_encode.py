import os
import threading

from ProjectClass.cl_printmsg import CLPrintMsg

PRINT_LOCK = threading.Lock()

class CLEncodeThread(threading.Thread):
    """
    Потоковое перекодирование файла windows-1251 -> UTF-8
    """

    def __init__(self, name: str, queue, printmsg: CLPrintMsg):
        """Инициализация потока"""
        threading.Thread.__init__(self)
        self.name = name
        self.queue = queue
        self.printmsg = printmsg

    def run(self):
        """Запуск потока"""
        while True:
            # Получаем параметры из очереди
            params = self.queue.get()

            if params is None:
                self.queue.task_done()
                break

            # Обработка
            self.encode(params)

            # Отправляем сигнал о том, что задача завершена
            self.queue.task_done()

    def encode(self, params):
        """
        Реализация: Перекодирование одного файла
        :param params:
        :return:
        """

        file_datetime = params.get("filedate")
        file_name = params.get("filename")
        path_from = params.get("filepathfrom")
        path_to = params.get("filepathto")

        # Считаем хеш - чтоб разделить потоки для журнализации
        cur_hash = str(hash(file_name))

        with PRINT_LOCK:
            self.printmsg.print_header(f'\t\tENCODE ({self.name}|{cur_hash}). File: {file_name}', 2)
        try:
            encode_text = ''

            # Построчно читаем исходный файл удаляя стоки с номерами задач (начинаются с '№')
            # Назначение: в файле все задачи нумеруются всегда от 1, и задачи в предыдущем файле тоже начинаются от 1
            with open(path_from, 'r', encoding='windows-1251') as fr:
                for codeText in fr.readlines():
                    # №1
                    if codeText[0] != '№':
                        encode_text += codeText[:-1] + '\n'  # \r\n

            # Перекодируем файл и записываем под новым именем
            with open(path_to, 'w', encoding='UTF-8') as fw:
                fw.write(encode_text)

            # Синхронизация времени файла
            dt_epoch = file_datetime.timestamp()
            os.utime(path_to, (dt_epoch, dt_epoch))

            with PRINT_LOCK:
                self.printmsg.print_success(f'\t\t\tENCODE ({cur_hash}). {path_from}>>>{path_to}', 2)
        except Exception as ex:
            with PRINT_LOCK:
                self.printmsg.print_error(f'\t\t\tENCODE ({cur_hash}). {type(ex)}')  # the exception instance
                self.printmsg.print_error(f'\t\t\tENCODE ({cur_hash}). {ex.args}')  # arguments stored in .args
                self.printmsg.print_error(
                    f'\t\t\tENCODE ({cur_hash}). {ex}')  # __str__ allows args to be printed directly