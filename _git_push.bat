@ECHO OFF
CHCP 65001
CLS

powershell -NoProfile -Command "Write-Host 'START %USERNAME% at: %DATE% - %TIME% Remote work' -BackgroundColor Green"
powershell -NoProfile -Command "Write-Host '=====================Attention!!!============================' -ForegroundColor Blue"
powershell -NoProfile -Command "Write-Host 'Remote push' -ForegroundColor Blue"
powershell -NoProfile -Command "Write-Host '=====================Attention!!!============================' -ForegroundColor Blue"

pause

for /f %%a in ('git remote') do (
 ECHO =====================START %%a============================
 @git push %%a --all
)

powershell write-host -back Green END %username% at: %date% - %time%
cmd /c pause