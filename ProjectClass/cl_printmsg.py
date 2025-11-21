from colorama import Fore

class CLPrintMsg:
    """Дополнительный класс красивой печати типовых сообщений"""

    """Признак вывода отладочных сообщений"""
    IS_PRINT_DEBUG: bool = False

    """Уровень вывода отладочных сообщений"""
    PRINT_DEBUG_LEVEL: int = 0

    @classmethod
    def set_debug(cls, flag: bool):
        cls.IS_PRINT_DEBUG = bool(flag)

    @classmethod
    def set_debug_level(cls, flag: int):
        cls.PRINT_DEBUG_LEVEL = int(flag)

    @classmethod
    def print_header(cls, value, level: int = 0):
        if level <= cls.PRINT_DEBUG_LEVEL:
            print(f'{Fore.BLUE}{value}{Fore.WHITE}')

    @staticmethod
    def print_error(value):
        print(f'{Fore.RED}{value}{Fore.WHITE}')

    @classmethod
    def print_success(cls, value, level: int = 0):
        if level <= cls.PRINT_DEBUG_LEVEL:
            print(f'{Fore.GREEN}{value}{Fore.WHITE}')

    @classmethod
    def print_service_message(cls, value, level: int = 0):
        if level <= cls.PRINT_DEBUG_LEVEL:
            print(f'{Fore.CYAN}{value}{Fore.WHITE}')

    @classmethod
    def print_debug(cls, value, level: int = 0):
        if cls.IS_PRINT_DEBUG and level <= cls.PRINT_DEBUG_LEVEL:
            print(f'{Fore.MAGENTA}{value}{Fore.WHITE}')
