@echo off

rem Use current directory
set path=%cd%

cd /d %path%

pyinstaller ^
--noconsole ^
--add-data "resources/*;resources/" ^
--icon "resources/icon.ico" ^
--clean ^
main.py
