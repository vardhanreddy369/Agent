@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Running the agent...
python main.py

echo.
echo script finished.
pause
