CHCP 65001
rmdir "build" /s /q
rmdir "dist" /s /q
pyinstaller _script.spec
rmdir "build" /s /q