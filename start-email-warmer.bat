@echo off
echo Starting Email Warmer...

:: Activate Python environment
py -m venv venv 2>nul
call venv\Scripts\activate.bat

:: Install dependencies if needed
pip install -r requirements.txt 2>nul

:: Run the application
python run.py

pause 