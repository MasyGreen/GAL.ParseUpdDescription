class AppManagement:
    def __init__(self):
        self.debug_list = [] # список файлов для теста через ','
        self.result_folder: str = ''  # Каталог сохранения файлов
        self.download_folder: str = '' # Каталог сохранения файлов FTP
        self.current_folder: str = '' # Каталог запуска

    def __str__(self):
        return f'AppManagement:\n{";\n".join(f'{k.ljust(25)}: {v}' for k, v in self.__dict__.items())} '
