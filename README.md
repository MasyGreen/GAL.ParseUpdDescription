# Назначение

Скачивание патчей обновлений для Галактики ERP 9.1 с ftp.galaktika.ru и рассылка изменений

# Настройки config.json

Файл создается при первом запуске со значениями по умолчанию

```json
{
  "FTPDir": "pub/support/galaktika/bug_fix/GAL910/DESCRIPTIONS", // Каталог с текстами изменений
  "FTPHost": "ftp.galaktika.ru", // FTP - предпологается анонимный доступ
  "IsCreateDescription": true, // Включать в тело письма текст изменений
  "IsIncludeNewInMail": true,
  "IsPrintDebug": true, // Отладочная информация в консоль
  "PrintDebugLevel": 0, // Уровень отладочных сообщений 0-3
  "IsSendMail": false, // Выполнять рассылку e-mail
  "MailAdditionText": "Дополнительный текст в e-mail",
  "MailFrom": "put@gmail.com - отправитель",
  "MailPassword": "пароль или код от e-mail",
  "MailSMTPPort": 587,// Порт smtp
  "MailSMTPServer": "smtp.gmail.com", // smtp сервер
  "MailTo": "get1@gmail.com, get2@gmail.com", // Список рассылки (для подмены если RedMineOverloadMail = true)
  "RedMineApiKey": "", // API key RedMine при интеграции через задачу
  "RedMineHost": "http://192.168.1.1", // Адрес RedMine
  "RedMineIssueId": "3535", // Задача RedMine - все наблюдатели получат рассылку на почту контакта
  "RedMineOverloadMail": false, // Замещать список рассылки MailTo 
  "DebugCount": 0 // Отладка, ограничить файлы FTP
}
```

# Шаги

Алгоритм

* Синхронизация файлов FTP и DownloadFTP *.txt
* Синхронизация файлов Download и DownloadFTP *.txt
  * Из имени файла убираем версию и добавляя к расширению '_win1251'
  * Перекодируем все файлы с '_win1251' из win1251 в UTF-8, в новом имени файла убираем '_win1251'
  * Удаляем не перекодированные файлы
* Отбираем файлы совпадающие по времени с последними патчами + отличающиеся по версии, выбираем только новые сообщения и производим рассылку по выбранным почтовым ящикам

# Известные проблемы
На FTP могут быть 2 файла разных версий, загрузится случайный

# Run/Запуск

* Запустить первый раз как инициализацию с полным скачиванием

## Опционально GIT

Для удобства отслеживания изменений

* В каталоге Download создать репозиторий GIT (InitGit.bat)
* В планировщике Windows **worker.bat** (~15:00)