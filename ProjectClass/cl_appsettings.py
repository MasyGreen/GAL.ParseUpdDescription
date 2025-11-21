# Addition class - settings/Дополнительный класс хранения настроек из CFG
class AppSettings:
    def __init__(self):
        # E-Mail SMTP Сервер
        self.MailSMTPServer: str = 'smtp.gmail.com'
        # E-Mail
        self.MailPassword: str = '****Replace mail hash password***'
        # E-Mail
        self.MailSMTPPort: int = 587
        # E-Mail
        self.MailFrom: str = 'put@gmail.com'
        # E-Mail (если RedMineOverloadMail = True, используем этот список)
        self.MailTo: str = 'get1@gmail.com, get2@gmail.com'
        # E-Mail
        self.MailAdditionText: str = 'You can read text from GIT'
        # E-Mail
        self.IsSendMail: bool = False
        # E-Mail
        self.IsIncludeNewInMail: bool = False

        # Галактика ERP
        self.FTPHost: str = 'ftp.galaktika.ru'
        # Галактика ERP
        self.FTPDir: str = 'pub/support/galaktika/bug_fix/GAL910/DESCRIPTIONS'

        # RedMine
        self.RedMineHost: str = 'http://192.168.1.1'
        # RedMine
        self.RedMineApiKey: str = ''
        # RedMine
        self.RedMineIssueId: str = ''
        # RedMine
        self.RedMineOverloadMail: bool = False

        # E-Mail
        self.IsCreateDescription: bool = True

        # Debug - выводить отладочную информацию
        self.IsPrintDebug: bool = False

        # Debug - выводить отладочную информацию (уровень 0..2)
        self.PrintDebugLevel: int = 0

        # Debug - при отличном от 0 значении ограничивает первые файлы
        self.DebugCount:int = 0

    def __str__(self):
        return f'AppSettings:\n{";\n".join(f'{k}: {v}' for k,v in self.__dict__.items())} '