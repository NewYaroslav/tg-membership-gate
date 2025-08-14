@echo off
setlocal
cd /d "%~dp0"

REM Creating a virtual environment (if it doesn't exist)
if not exist "venv\Scripts\python.exe" (
    py -3 -m venv venv || (echo Failed to create venv & exit /b 1)
)

REM Activating the virtual environment
call "%~dp0venv\Scripts\activate.bat"

REM Installing dependencies
python -m pip install --upgrade pip
if exist requirements.txt (
    echo Installing dependencies from requirements.txt...
    python -m pip install -r requirements.txt
) else (
    echo requirements.txt not found. Installing basic libraries...
    python -m pip install telethon python-dotenv colorlog rich
)

python -c "import sys; print('Python:', sys.executable)"

REM Deactivating the virtual environment
call "%~dp0venv\Scripts\deactivate.bat"

echo Setup completed. Use start.bat to run the program.
pause
