@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 exit /b 1
py -3.13 -c "import pygame, PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Install the dependencies in Command Prompt first:
    echo py -3.13 -m pip install -r requirements.txt
    echo py -3.13 -m pip install --upgrade pyinstaller
    goto failed
)
py -3.13 -m PyInstaller --noconfirm --clean --onefile --windowed --name ApexRacing --add-data "data:data" main.py
if errorlevel 1 goto failed
echo.
echo Build complete: dist\ApexRacing.exe
echo Test the executable before distributing it.
popd
pause
exit /b 0
:failed
echo.
echo Build did not complete. See the message above.
popd
pause
exit /b 1
