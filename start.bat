@echo off
cd /d "%~dp0backend"
if not exist venv (
  echo Creating virtual environment...
  python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing dependencies...
python -m pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org -q
python -m pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
if errorlevel 1 (
  echo.
  echo ERROR: Failed to install packages. See message above.
  pause
  exit /b 1
)
echo.
echo Starting NeoCard at http://localhost:8000
python run.py
pause
