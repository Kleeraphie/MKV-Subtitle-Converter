@echo off
echo Do you want to edit the subtitles?
echo 1) Yes
echo 2) No
set /p edit=Your Input: 

echo.

python app.py %edit%
pause