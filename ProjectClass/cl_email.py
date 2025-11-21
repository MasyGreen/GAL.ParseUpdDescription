import os
from datetime import datetime
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ProjectClass.cl_appmanagement import AppManagement
from ProjectClass.cl_appsettings import AppSettings
from ProjectClass.cl_printmsg import CLPrintMsg
from ProjectClass.cl_redmine import CLRedMine
from ProjectClass.cl_workfile import CLWorkFile


class CLEMail:

    @staticmethod
    def sending_email(work_date: datetime, file_list, app_settings: AppSettings, app_management: AppManagement,
                      printmsg: CLPrintMsg):
        """
        Отправка e-mail (формирование файла новых патчей)
        :param app_management:
        :param work_date: дата патчей
        :param file_list: список файлов патчей
        :param app_settings:
        :param printmsg:
        :return:
        """
        printmsg.print_header('Start. Отправка e-mail')

        message = '<html><head></head><body>'
        message += f"<p>Check time (время проверки): <b>{datetime.now().strftime('%d %b %Y, %H:%M')}</b></p>\n"
        message += f"<p>FTP updated time (время патчей): <b>{work_date.strftime('%d %b %Y, %H:%M')}</b></p>\n"
        message += f"<p>{app_settings.MailAdditionText}</p>\n\n"

        message += f"<h2>Updated files list:</h2>\n<ul>\n"
        for el in file_list:
            message += f'<li>{el.get("filename")} v.{el.get("version")}</li>\n'
        message += f"</ul>\n"

        if app_settings.IsIncludeNewInMail:
            message += CLWorkFile.get_new_text(file_list, printmsg)

        message += '</body></html>'

        # Список получателей из RedMine
        email_list = []

        if app_settings.RedMineOverloadMail:
            email_list = CLRedMine.get_email_from_red_mine(app_settings, printmsg).split(',')
        else:
            email_list = app_settings.MailTo.split(',')

        printmsg.print_debug(f'\tСписок получателей: {email_list}')

        # Копирование тела письма в каталог
        if app_settings.IsCreateDescription:
            try:
                now = datetime.now()

                #  Log e-mail
                log_file_folder = os.path.join(app_management.current_folder, "EMailLog")
                if not os.path.exists(log_file_folder):
                    os.makedirs(log_file_folder)

                logfile = os.path.join(log_file_folder,
                                       f'mail_{now.strftime("%Y.%m.%d %H-%M-%S")}.html')
                with open(logfile, 'a', encoding='utf-8') as f:
                    f.write(f"{email_list}\n\n{message}\n")
            except Exception as ex:
                printmsg.print_error(f'\t{type(ex)}')  # the exception instance
                printmsg.print_error(f'\t{ex.args}')  # arguments stored in .args
                printmsg.print_error(f'\t{ex}')  # __str__ allows args to be printed directly,

        # Отправка сообщения
        if app_settings.IsSendMail:
            try:
                for cur_email in email_list:
                    printmsg.print_service_message(f'\tSend e-mail: {cur_email}')

                    # Формирование текста сообщения e-mail
                    e_mail_msg = MIMEMultipart()
                    e_mail_msg["From"] = app_settings.MailFrom
                    e_mail_msg["To"] = cur_email
                    e_mail_msg["Subject"] = "Update ftp.galaktika.ru"
                    e_mail_msg.attach(MIMEText(message, 'html'))

                    printmsg.print_debug(f'\t{e_mail_msg.as_string()}')

                    try:
                        server = smtplib.SMTP(app_settings.MailSMTPServer, app_settings.MailSMTPPort)
                        server.starttls()
                        server.login(app_settings.MailFrom, app_settings.MailPassword)

                        text = e_mail_msg.as_string()
                        server.sendmail(app_settings.MailFrom, cur_email, text)
                        server.quit()
                        printmsg.print_success(f'\tSending e-mail')
                    except Exception as ex:
                        printmsg.print_error(f'\t{type(ex)}')  # the exception instance
                        printmsg.print_error(f'\t{ex.args}')  # arguments stored in .args
                        printmsg.print_error(f'\t{ex}')  # __str__ allows args to be printed directly,

            except Exception as ex:
                printmsg.print_error(f'\t{type(ex)}')  # the exception instance
                printmsg.print_error(f'\t{ex.args}')  # arguments stored in .args
                printmsg.print_error(f'\t{ex}')  # __str__ allows args to be printed directly,