import re
from queue import Queue
import os
from datetime import datetime

from ProjectClass.cl_appmanagement import AppManagement
from ProjectClass.cl_encode import CLEncodeThread
from ProjectClass.cl_printmsg import CLPrintMsg


class CLWorkFile:

    @staticmethod
    def check_email(email) -> bool:
        """
        Проверка e-mail по шаблону
        :param email:
        :return: True - удовлетворяет условиям
        """
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        # pass the regular expression and the string into the fullmatch() method
        if re.fullmatch(regex, email):
            return True
        return False

    @staticmethod
    def get_local_file_list(folder: str, printmsg: CLPrintMsg):
        """
        Получить список файлов
       :param folder:
       :param printmsg:
       :return: список {filepath, filename, filedate}
       """
        printmsg.print_header('Start. Получение локального списка файлов')
        printmsg.print_header(f'\tКаталог: {folder}')
        result = []
        for filename in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, filename)):
                file_time_stamp = os.path.getmtime(os.path.join(folder, filename))
                file_date = datetime.fromtimestamp(file_time_stamp)  # int в формате YYYYMMDD
                result.append({"filepath": os.path.join(folder, filename), "filename": filename,
                               "filedate": datetime(file_date.year, file_date.month, file_date.day, file_date.hour,
                                                    file_date.minute, file_date.second)})

        printmsg.print_success(f'\tКол-во файлов: {len(result)}')
        return sorted(result, key=lambda item: item['filename'])

    @staticmethod
    def check_result_folder(app_management: AppManagement, printmsg: CLPrintMsg) -> bool:
        """
        Проверить каталог на наличие *.TXT_WIN1251 - то надо удалить все файлы (предыдущий запуск окончился ошибкой)
        :param app_management:
        :param printmsg:
        :return: True - были ошибки нужна принудительная обработка
        """
        printmsg.print_header(f'Start. Проверка каталога результата')
        result: bool = False

        for filename in os.listdir(app_management.download_folder):
            if os.path.isfile(os.path.join(app_management.download_folder, filename)):
                name, extension = os.path.splitext(filename)
                if extension.lower() == ".txt_win1251":
                    result = True
                    break

        printmsg.print_success(f'\tТребуется удаление: {result}')

        # Остались файлы от предыдущего процесса - удаляем все файлы промежуточные и результат
        count: int = 0
        if result:
            try:
                for filename in os.listdir(app_management.download_folder):
                    if os.path.isfile(os.path.join(app_management.download_folder, filename)):
                        name, extension = os.path.splitext(filename)
                        if extension.lower() == ".txt" or extension.lower() == ".txt_win1251":
                            count = count + 1
                            printmsg.print_debug(f'\tУдалить файл: {app_management.download_folder}{filename}')
                            os.remove(os.path.join(app_management.download_folder, filename).lower())

                printmsg.print_success(f'\tУдалено: {count}')
            except Exception as ex:
                printmsg.print_error(f'\tОшибка удаления файлов: {ex}')

        return result

    @staticmethod
    def get_max_date_from_folder(folder: str, printmsg: CLPrintMsg, date_only: bool = True) -> datetime:
        """
        Получение максимальной даты файла в локальном каталоге

        :param date_only:
        :param folder: каталог проверки
        :param printmsg:
        :return: максимальная дата (отбрасываем время) файла *.txt
        """
        printmsg.print_header('Start. Получение максимальной локальной даты')
        printmsg.print_header(f'\tКаталог: {folder}')

        result: datetime = datetime(1, 1, 1, 0, 0)
        try:
            for filename in os.listdir(folder):
                if os.path.isfile(os.path.join(folder, filename)):
                    name, extension = os.path.splitext(filename)
                    if extension.lower() == '.txt':
                        # дата модификации файла
                        time_stamp = os.path.getmtime(os.path.join(folder, filename))
                        cur_file_date = datetime.fromtimestamp(time_stamp)  # int в формате YYYYMMDD
                        if result < cur_file_date:
                            result = cur_file_date

            printmsg.print_success(f'\tДата: {result.strftime("%Y/%m/%d %H:%M:%S")}')
        except Exception as ex:
            printmsg.print_error(f'\t{type(ex)}')  # the exception instance
            printmsg.print_error(f'\t{ex.args}')  # arguments stored in .args
            printmsg.print_error(f'\t{ex}')  # __str__ allows args to be printed directly,

        if date_only:
            result = datetime(result.year, result.month, result.day)
        return result

    @staticmethod
    def read_version_from_file(file_path: str, printmsg: CLPrintMsg) -> str:
        """
        Получение версии из файла, ожидается, что есть типизированная строка (* ВЕРСИЯ: 9.1.12.0) с номером версии (берем первую попавшуюся)

        :param file_path:
        :param printmsg:
        :return:
        """
        result: str = ''
        try:
            with open(file_path.lower(), 'r', encoding='UTF-8') as fr:
                for line in fr.readlines():
                    if line.lower().find('* версия:') != -1:
                        result = line.lower().replace('* версия:', '').strip()
                        break
        except Exception as e:
            printmsg.print_error(f'\tОшибка чтения версии из файла: {file_path}. {e}')

        return result

    @staticmethod
    def read_versions(app_management: AppManagement, printmsg: CLPrintMsg):
        """
        Получение списка файлов с версий из файлов *.txt в исходном каталоге до его очистки для сравнения
        Иногда при изменениях дата файла не меняется и как следствие не входит в список рассылки

        :param app_management:
        :param printmsg:
        :return: список {filepath, filename, version, filedate}
        """
        result = []
        printmsg.print_header(f'Start. Получение версий файлов')
        try:
            for filename in os.listdir(app_management.result_folder):
                if os.path.isfile(os.path.join(app_management.result_folder, filename)):
                    name, extension = os.path.splitext(filename)
                    if extension.lower() == ".txt":
                        file_time_stamp = os.path.getmtime(os.path.join(app_management.result_folder, filename))
                        file_date = datetime.fromtimestamp(file_time_stamp)  # int в формате YYYYMMDD

                        version = CLWorkFile.read_version_from_file(
                            os.path.join(app_management.result_folder, filename), printmsg)

                        row = {"filepath": os.path.join(app_management.result_folder, filename),
                               "filename": filename,
                               "version": version,
                               "filedate": file_date
                               }
                        result.append(row)
                        printmsg.print_debug(f'\t{row}', 1)

            printmsg.print_success(f'\tПолучены версии для: {len(result)} файлов')
        except Exception as ex:
            printmsg.print_error(f'\tОшибка: {ex}')
        return result

    @staticmethod
    def encode_files(app_management: AppManagement, printmsg: CLPrintMsg):
        """
        Перекодирование файлов в UTF8 т. к. GIT не поддерживает WIN1251

        :param app_management:
        :param printmsg:
        :return:
        """
        # Файлы для перекодировки
        printmsg.print_header(f'Start. Перекодировка файлов UTF-8')
        encode_file_list = []

        for filename in os.listdir(app_management.result_folder):
            if os.path.isfile(os.path.join(app_management.result_folder, filename)):
                name, extension = os.path.splitext(filename)
                if extension.lower() == ".txt_win1251":
                    # дата модификации файла
                    time_stamp = os.path.getmtime(os.path.join(app_management.result_folder, filename))
                    cur_file_date = datetime.fromtimestamp(time_stamp)  # int в формате YYYYMMDD
                    new_file_name = re.sub('_WIN1251', '', filename, flags=re.IGNORECASE)
                    row = {"filename": new_file_name,
                           "filepathfrom": f'{os.path.join(app_management.result_folder, filename)}',
                           "filepathto": f'{os.path.join(app_management.result_folder, new_file_name)}',
                           "filedate": cur_file_date}
                    encode_file_list.append(row)
                    printmsg.print_debug(f'\t{row}', 1)

        printmsg.print_success(f'\tКол-во файлов (Win1251): {len(encode_file_list)}')

        try:
            workers = []
            queue = Queue()
            # Запускаем потом и очередь
            for i in range(10):
                t = CLEncodeThread(str(i), queue, printmsg)
                t.daemon = True
                t.start()

            # Даем очереди нужные нам ссылки для скачивания
            for el in encode_file_list:
                queue.put(el)

            for _ in workers:
                queue.put(None)

            # Ждем завершения работы очереди
            queue.join()

            for t in workers:
                t.join()

            printmsg.print_success(f'Encode {len(encode_file_list)} files')
        except Exception as ex:
            printmsg.print_error(f'Encode file: {ex}')

    @staticmethod
    def get_new_text(file_list, printmsg: CLPrintMsg) -> str:
        """
        Получение из файла текста новых правок (задачи с '* ПЕРВОЕ РЕШЕНИЕ: NEW')
        :param file_list: Список файлов для получения данных
        :param printmsg:
        :return: Текст файла
        """
        printmsg.print_header('Start. Получение текста патчей')
        result = '\n<h2>File content (new issue)</h2>\n'
        try:
            index_f: int = 0
            for el in file_list:
                index_f = index_f + 1
                filename = el.get("filename")
                filepath = el.get("filepath")
                origin_name = el.get("origin_name")
                version_old = el.get("version_old")
                version_new = el.get("version")

                result += f'<h3>{index_f} File: {filename} ({origin_name})</h3>\n'
                result += f'<p><b>Версия:</b> {version_old} => {version_new}</p>\n'

                start_i: bool = False  # Начало задачи
                issue_header: bool = False  # Начало текста задачи
                issue_text = ''  # Текст задачи
                is_new_issue: bool = False  # Признак новой задачи
                skip_file: bool = False  # Признак пропуска файла, новые задачи вначале - дальше файл можно пропустить
                index = 0
                index_i: int = 0
                with open(filepath, 'r', encoding='UTF-8') as fr:
                    for line in fr.readlines():
                        index = index + 1
                        if skip_file:
                            printmsg.print_debug(f'\tExit line: {index}', 3)
                            break

                        # Начало задачи
                        if line.find('* ЗАДАЧА В JIRA:') != -1 and not start_i:
                            issue_header = True
                            start_i = True
                            is_new_issue = False
                            issue_text = ''

                        # Конец задачи
                        if line.find('* * *') != -1 and start_i:
                            start_i = False

                            if is_new_issue:
                                result += f'{issue_text}\n'

                        # признак новой задачи
                        if line.find('* ПЕРВОЕ РЕШЕНИЕ:') != -1 and start_i:
                            if line.find(': NEW') != -1 and start_i:
                                is_new_issue = True
                            else:
                                skip_file = True

                        if issue_header:
                            index_i = index_i + 1
                            issue_header = False
                            issue_text += f'<p><b>{index_f}.{index_i} {line[:-1]}</b></p>\n'
                        else:
                            cur_str = str(line[:-1])
                            if cur_str != '' and cur_str is not None and cur_str:
                                issue_text += f'{cur_str}<br>\n'

            printmsg.print_debug(f'\t{result}', 2)
            printmsg.print_success(f'\tПолучен текст')
        except Exception as ex:
            printmsg.print_error(f'\t{type(ex)}')  # the exception instance
            printmsg.print_error(f'\t{ex.args}')  # arguments stored in .args
            printmsg.print_error(f'\t{ex}')  # __str__ allows args to be printed directly,

        return result

    @staticmethod
    def write_log(folder: str, value: str):
        now = datetime.now()

        #  Log e-mail
        start_log_folder = os.path.join(folder, "EStartLog")
        if not os.path.exists(start_log_folder):
            os.makedirs(start_log_folder)

        with open(os.path.join(start_log_folder, f'Log.txt'), 'a', encoding='utf-8') as f:
            f.writelines(f'{now.strftime("%Y.%m.%d %H-%M-%S")} | {value}\n')
