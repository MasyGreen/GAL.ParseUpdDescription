import json
import os
import re
import shutil
import sys
from datetime import datetime

import keyboard

from ProjectClass.cl_appmanagement import AppManagement
from ProjectClass.cl_appsettings import AppSettings
from ProjectClass.cl_email import CLEMail
from ProjectClass.cl_ftpreader import CLFTPReaderThread
from ProjectClass.cl_printmsg import CLPrintMsg
from ProjectClass.cl_uncdate import CLUNCDate
from ProjectClass.cl_workfile import CLWorkFile


# Чтение файла настроек
def read_settings(settings_file_name: str):
    app_settings = AppSettings()
    members = [attr for attr in dir(app_settings) if
               not callable(getattr(app_settings, attr)) and not attr.startswith("__")]

    # Создание файла настроек по умолчанию
    if not os.path.exists(settings_file_name):
        printmsg.print_header(f'Настройки. Создание нового файла: {settings_file_name}')

        default = {}

        # Заполнение настроек по умолчанию
        for member in members:
            default[member] = getattr(app_settings, member)

        # Сохранение настроек в файл
        with open(settings_file_name, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)

        return False, app_settings

    # Чтение существующего файла
    printmsg.print_header(f'Настройки. Чтение файла: {settings_file_name}')
    with open(settings_file_name, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Получение значений
    for member in members:
        setattr(app_settings, member, cfg.get(member, getattr(app_settings, member)))

    return True, app_settings


# Получить дату без времени
def get_date_from_datetime(value: datetime) -> datetime:
    return datetime(value.year, value.month, value.day, 0, 0, 0, 0)


# Синхронизация каталога FTP и DIR
def sync_catalogs(app_settings: AppSettings, app_management: AppManagement) -> None:
    printmsg.print_header(f'Start. Синхронизация DIR + FTP')

    # Список файлов DIR
    local_file_list = CLWorkFile.get_local_file_list(app_management.download_folder, printmsg)

    # Список файлов FTP
    ftp_reader = CLFTPReaderThread(app_settings, app_management, printmsg)
    ftp_file_list = []

    if len(app_management.debug_list) > 0:
        # Отладка: ограничение по началу файла (как будто на FTP только эти файлы)
        ftp_file_list_tmp = ftp_reader.get_file_list()
        for ftp_file in ftp_file_list_tmp:
            if any(ftp_file["filename"].lower().startswith(p) for p in app_management.debug_list):
                ftp_file_list.append(ftp_file)
    elif app_settings.DebugCount > 0:
        # Отладка: ограничение количеству первых (как будто на FTP только эти файлы)
        ftp_file_list = ftp_reader.get_file_list()[: app_settings.DebugCount]
    else:
        ftp_file_list = ftp_reader.get_file_list()

    printmsg.print_debug(f'DIR ({len(local_file_list)}): {local_file_list}\n',2)
    printmsg.print_debug(f'FTP ({len(ftp_file_list)}): {ftp_file_list}\n',2)

    # Отбираем только имена файлов (нижний регистр для сравнения) в списки
    ids1 = {str(item['filename']).lower() for item in local_file_list}
    ids2 = {str(item['filename']).lower() for item in ftp_file_list}

    # Только файлы присутствующие и в DIR и на FTP
    common_ids = ids1.intersection(ids2)
    printmsg.print_debug(f'ПЕРЕСЕЧЕНИЕ ({len(common_ids)}): {common_ids}\n')

    count_same: int = 0
    count_diff: int = 0
    count_diff_date: int = 0
    for item in local_file_list:
        if str(item['filename']).lower() not in common_ids:
            count_diff += 1
            # Удаляем файл из DIR если его нет на FTP
            try:
                os.remove(item["filepath"])
                printmsg.print_success(f'Файл {item["filepath"]} отсутствует на FTP и удален успешно')
            except OSError as ex:
                printmsg.print_error(f'Error. Файл {item["filepath"]} отсутствует на FTP и не удален: {ex}')
        else:
            # Если файл есть в DIR и на FTP сравниваем даты
            found_ftp_item = [element for element in ftp_file_list if
                              str(element["filename"]).lower() == str(item['filename']).lower()]
            if len(found_ftp_item) > 0:
                # Удаляем файл из DIR если его дата (отбрасываем время т.к. разные тайм-зоны) отличается от FTP
                if CLUNCDate.get_only_date(found_ftp_item[0]["filedate"]) != CLUNCDate.get_only_date(item['filedate']):
                    count_diff_date += 1
                    try:
                        os.remove(item["filepath"])
                        printmsg.print_success(
                            f'Файл {item["filepath"]} ({item['filedate']}) отличается по дате с FTP ({found_ftp_item[0]["filedate"]}) и удален успешно')
                    except Exception as ex:
                        printmsg.print_error(
                            f'Error. Файл {item["filepath"]} отличается по дате с FTP и не удален: {ex}')
                else:
                    count_same += 1
    printmsg.print_debug(f'Файлы: одинаковые {count_same}; лишние {count_diff}; отличаются по дате {count_diff_date}\n')

    # Перестраиваем Список файлов DIR - остались только синхронизированные файлы с FTP (не нужно загружать)
    local_file_list = CLWorkFile.get_local_file_list(app_management.download_folder, printmsg)
    ids1 = {str(item['filename']).lower() for item in local_file_list}
    printmsg.print_debug(f'DIR ({len(ids1)}): {ids1}\n',2)

    printmsg.print_success(f'\n============================================\n')

    # Строим список файлов к закачке из FTP (все отсутствующие в DIR)
    download_list = []
    for item in ftp_file_list:
        if str(item['filename']).lower() not in ids1:
            download_list.append(item)
    printmsg.print_debug(f'ЗАГРУЗИТЬ FTP ({len(download_list)}): {download_list}')

    printmsg.print_success(f'\n============================================\n')

    # Докачиваем в DIR данные из FTP
    if len(download_list) > 0:
        ftp_reader = CLFTPReaderThread(app_settings, app_management, printmsg)
        ftp_reader.download(download_list)


def main():
    # True - Включение отладки: отбираем из FTP файлы начинающиеся с (словарь)
    app_management = AppManagement()

    app_management.current_folder = os.getcwd()
    app_management.result_folder = os.path.join(os.getcwd(), 'Download')
    app_management.download_folder = os.path.join(os.getcwd(), 'DownloadFTP')

    # Список-фильтр для отладки, содержит начала файлов для загрузки с FTP
    # app_management.debug_list = ["c_common_res", "l_soprbase_res", "l_soprdoc_res", "l_makedo_res", "c_diadoc_res"]

    # Создаем рабочий каталог
    if not os.path.exists(app_management.result_folder):
        os.makedirs(app_management.result_folder)

    # Создаем рабочий каталог FTP
    if not os.path.exists(app_management.download_folder):
        os.makedirs(app_management.download_folder)

    printmsg.print_debug(f'\n{app_management}\n')

    # Получение настроек
    settings_file_name = os.path.join(app_management.current_folder, 'config.json')
    is_exist, app_settings = read_settings(settings_file_name)

    printmsg.set_debug(app_settings.IsPrintDebug)
    printmsg.set_debug_level(app_settings.PrintDebugLevel)

    if not is_exist:
        printmsg.print_success(f'Нажмите ПРОБЕЛ для выхода...')
        keyboard.wait("space")
        sys.exit()

    printmsg.print_debug(f'\n{app_settings}\n', 1)

    printmsg.print_success(f'\n============================================\n')
    sync_catalogs(app_settings, app_management)

    printmsg.print_success(f'\n============================================\n')

    # Ошибки предыдущего запуска в каталоге DIR
    is_error_result_folder = CLWorkFile.check_result_folder(app_management, printmsg)

    # Максимальная дата файла в каталоге DIR и FTP
    cur_dt = CLWorkFile.get_max_date_from_folder(app_management.result_folder, printmsg)
    ftp_dt = CLWorkFile.get_max_date_from_folder(app_management.download_folder, printmsg)

    # Количество файлов в каталоге DIR и FTP
    local_file_list = CLWorkFile.get_local_file_list(app_management.result_folder, printmsg)
    ftp_file_list = CLWorkFile.get_local_file_list(app_management.download_folder, printmsg)

    if (not is_error_result_folder) or ftp_dt != cur_dt or len(ftp_file_list) != len(local_file_list) or len(
            local_file_list) == 0:
        message = f'\tПредыдущий запуск: {is_error_result_folder} ({'успешно' if is_error_result_folder == True else 'с ошибками'}). Ошибка: {not is_error_result_folder}\n'
        message += f'\tДата: DIR = {cur_dt}; FTP = {ftp_dt}. Ошибка: {ftp_dt != cur_dt}\n'
        message += f'\tКоличество файлов: DIR = {len(local_file_list)}; FTP = {len(ftp_file_list)}. Ошибка: {len(ftp_file_list) != len(local_file_list)}'

        CLWorkFile.write_log(os.getcwd(), message)
        printmsg.print_debug(message)

        # Получаем версии файлов из унифицированных названий (без версии) ATLMQ_DLL.txt из локального FTP
        file_version_exist = CLWorkFile.read_versions(app_management, printmsg)
        printmsg.print_debug(f'Version (exist) ({len(file_version_exist)}): {file_version_exist}\n')

        # Удаляем все файлы (не будем разбираться какие отличаются - достаточно версии)
        for filename in os.listdir(app_management.result_folder):
            name, extension = os.path.splitext(filename)
            if extension.lower() == ".txt" or extension.lower() == ".txt_win1251":
                os.remove(os.path.join(app_management.result_folder, filename).lower())
        printmsg.print_debug(f'Очищен каталог (*.txt, *.txt_win1251): {app_management.result_folder}\n')

        # Копируем все файлы из синхронизированного каталога FTP с унификацией по имени
        unification_files = []  # Собираем соответствие имен
        for filename in os.listdir(app_management.download_folder):
            name, extension = os.path.splitext(filename)
            if extension.lower() == ".txt":
                # ATLHYPERLINK_EXE_55230 -> ATLHYPERLINK_EXE
                # FNSNDSCAWS_2COM_DLL_9130
                # FNSNDSCAWSCOM_DLL_9110
                new_file_name = re.sub(r'_(\d+$)', '', name)
                printmsg.print_debug(f'{name.ljust(30)} -> {new_file_name}', 2)

                # Возможно ошибочное срабатывание когда на FTP выложены сразу два файла одного компонента, но с разной версией
                # GalDiadocConnectS_DLL_91180.txt
                # GalDiadocConnectS_DLL_91190.txt
                double_item = [item for item in unification_files if
                            item['filenamenew'] == f'{new_file_name}.txt']
                if len(double_item) > 0:
                    message = f'Два файла одной версии: {new_file_name} [{double_item[0]["filenameold"]}]/[{filename}]'
                    CLWorkFile.write_log(os.getcwd(), message)
                    printmsg.print_error(message)

                unification_files.append({"filenameold": filename, "filenamenew": f'{new_file_name}.txt'})

                new_file_name = f'{new_file_name}.TXT_WIN1251'
                shutil.copy2(os.path.join(app_management.download_folder, filename),
                             os.path.join(app_management.result_folder, new_file_name))
        printmsg.print_debug(f'Заполнен каталог: {app_management.result_folder}\n')

        # Перекодировать в UTF8
        CLWorkFile.encode_files(app_management, printmsg)

        printmsg.print_success(f'\n============================================\n')
        # Удаляем все не перекодированные файлы
        for filename in os.listdir(app_management.result_folder):
            name, extension = os.path.splitext(filename)
            if extension.lower() == ".txt_win1251":
                os.remove(os.path.join(app_management.result_folder, filename).lower())
        printmsg.print_debug(f'Очищен каталог (*.txt_win1251): {app_management.result_folder}\n')

        printmsg.print_success(f'\n============================================\n')
        # Считаем, что файлы с максимальной датой - файлы последних патчей

        # Версии файлов из унифицированных названий (без версии) ATLMQ_DLL.txt
        file_version_new = CLWorkFile.read_versions(app_management, printmsg)
        printmsg.print_debug(f'Version (new) ({len(file_version_new)}): {file_version_new}\n')

        # Максимальная дата
        cur_dt = CLWorkFile.get_max_date_from_folder(app_management.result_folder, printmsg)

        # Файлы с максимальной датой (считаем их патчами)
        file_version_new = [item for item in file_version_new if
                            item['filedate'].strftime("%Y/%m/%d") == cur_dt.strftime("%Y/%m/%d")]

        # Обновление справочных данных
        for el in file_version_new:
            element = [item for item in file_version_exist if item['filename'].lower() == el['filename'].lower()]
            if len(element) == 1:
                el['version_old'] = element[0]['version']
            element = [item for item in unification_files if item['filenamenew'].lower() == el['filename'].lower()]
            if len(element) == 1:
                el['origin_name'] = element[0]['filenameold']

        cur_dt = CLWorkFile.get_max_date_from_folder(app_management.result_folder, printmsg, False)
        printmsg.print_debug(
            f'Update ({cur_dt.strftime('%Y/%m/%d %H:%M:%S')}) ({len(file_version_new)}): {file_version_new}\n')

        CLWorkFile.write_log(os.getcwd(), f'{app_settings.IsSendMail=}; {app_settings.IsCreateDescription=}; {len(file_version_new)=}')

        if (app_settings.IsSendMail or app_settings.IsCreateDescription) and len(file_version_new) > 0:
            CLEMail.sending_email(cur_dt, file_version_new, app_settings, app_management, printmsg)
        else:
            printmsg.print_service_message('Отправка не предусмотрена настройками')
    else:
        CLWorkFile.write_log(os.getcwd(), 'Нет обновлений')
        printmsg.print_service_message('Нет обновлений')


if __name__ == '__main__':
    printmsg = CLPrintMsg()

    printmsg.print_service_message('-=Start=-')
    printmsg.print_service_message(f'Last update: Cherepanov Maxim masygreen@gmail.com (c), 11.2025')
    printmsg.print_service_message(f'Скачивание описаний обновлений Галактика ERP')

    CLWorkFile.write_log(os.getcwd(), 'Start')
    try:
        main()
    except Exception as ex:
        printmsg.print_error(f'{ex}')
        CLWorkFile.write_log(os.getcwd(), f'{ex}')
    CLWorkFile.write_log(os.getcwd(), 'End\n')

    printmsg.print_service_message('-=End=-')
    sys.exit()
