from redminelib import Redmine

from ProjectClass.cl_appsettings import AppSettings
from ProjectClass.cl_printmsg import CLPrintMsg
from ProjectClass.cl_workfile import CLWorkFile


class CLRedMine:

    @staticmethod
    def get_email_from_red_mine(app_settings: AppSettings, printmsg: CLPrintMsg) -> str:
        """
        Получение наблюдателей из задачи RedMine, а у наблюдателей адреса почты
        :param app_settings:
        :param printmsg:
        :return: получаем список e-mail из RedMine, если он пустой подменяем на MailTo
        """
        printmsg.print_header('Start. Получение e-mail из ReMine')
        result = str(app_settings.MailTo)

        try:
            redmine = Redmine(app_settings.RedMineHost, key=app_settings.RedMineApiKey)
            issue = redmine.issue.get(app_settings.RedMineIssueId, include=['watchers'])
            printmsg.print_debug(f'\tКоличество наблюдателей RedMine = {len(issue.watchers)}')

            emails: str = ''
            if len(issue.watchers) > 0:
                for user in issue.watchers:
                    usr = redmine.user.get(user.id)
                    printmsg.print_debug(f'\t{user} = {usr.mail}')
                    if CLWorkFile.check_email(str(usr.mail).strip()):
                        if len(emails) == 0:
                            emails = f'{str(usr.mail).strip()}'
                        else:
                            emails = f'{emails}, {str(usr.mail).strip()}'

            result = emails
        except Exception as inst:
            printmsg.print_error(f'\t{type(inst)}')  # the exception instance
            printmsg.print_error(f'\t{inst.args}')  # arguments stored in .args
            printmsg.print_error(f'\t{inst}')  # __str__ allows args to be printed directly,

        return result