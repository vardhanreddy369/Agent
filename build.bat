@echo off
echo Installing PyInstaller...
pip install pyinstaller

echo Building Agent.exe...
pyinstaller --noconfirm --onefile --windowed --add-data "credentials.json;." --add-data "form.html;." main.py

echo.
echo Build Complete! Look in the 'dist' folder for 'main.exe'.
pause
