@echo off

rem Use current directory
set path=%cd%

cd /d %path%

python -m PyInstaller ^
--noconsole ^
--add-data "resources/*;resources/" ^
--icon "resources/icon.ico" ^
--clean ^
main.py
