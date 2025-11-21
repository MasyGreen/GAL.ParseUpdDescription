@ECHO OFF
CHCP 65001
CLS
powershell write-host -back Green START %username% at: %date% - %time% Remote work

SET "PROGECTNAME=GAL.ParseUpdDescription"
SET "GITUSER=MasyGreen"

@powershell write-host -fore Blue =====================Attention!!!============================
@powershell write-host -fore Blue Remote add
powershell write-host -fore Blue  =====================Attention!!!============================

pause

powershell write-host -fore Blue -=Список существующих=-

git remote -v

powershell write-host -fore Blue -=Удаление=-

for /f %%a in ('git remote') do @git remote rm %%a

git remote -v

powershell write-host -fore Blue -=Добавление=-

SET "MY_ARRAY=origin#github.com originbit#bitbucket.org"

SETLOCAL EnableDelayedExpansion
FOR %%m IN (%MY_ARRAY%) DO (
	SET CURSTR=%%m	
	FOR /F "tokens=1,2 delims=#" %%E IN ("!CURSTR!") DO (
    SET part1=%%E
    SET part2=%%F
	)
	
	for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "('!part1!').Trim()"`) do set "part1=%%T"
	for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "('!part2!').Trim()"`) do set "part2=%%T"
	
	powershell write-host -fore Yellow "* !part1! !part2!"
	git remote add "!part1!" "git@!part2!:%GITUSER%/%PROGECTNAME%.git"
)

SET "MY_ARRAY=originloc#localhost:3000"

SETLOCAL EnableDelayedExpansion
FOR %%m IN (%MY_ARRAY%) DO (
	SET CURSTR=%%m	
	FOR /F "tokens=1,2 delims=#" %%E IN ("!CURSTR!") DO (
    SET part1=%%E
    SET part2=%%F
	)
	
	for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "('!part1!').Trim()"`) do set "part1=%%T"
	for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "('!part2!').Trim()"`) do set "part2=%%T"
	
	powershell write-host -fore Yellow "* !part1! !part2!"
	git remote add "!part1!" "http://!part2!/%GITUSER%/%PROGECTNAME%.git"
)

ENDLOCAL

powershell write-host -fore Blue -=Результат=-
git remote -v
powershell write-host -back Green END %username% at: %date% - %time%
cmd /c pause