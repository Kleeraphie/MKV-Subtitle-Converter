@echo off
echo Do you want to edit the subtitles?
echo 1) Yes
echo 2) No (Default)
set /p edit=Your Input:
echo Do you want to save the images of the PGS subtitles?
echo 1) Yes
echo 2) No (Default)
set /p save=Your Input: 

echo.

python app.py %edit% %save%
pause