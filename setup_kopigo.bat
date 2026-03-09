@echo off
echo === Setting up KopiGo environment ===

REM 1. Create virtual environment
echo [1/5] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM 2. Install Python dependencies
echo [2/5] Installing Python dependencies...
pip install flask flask-sqlalchemy pymysql boto3 pillow flask-bcrypt pandas pymongo requests

REM 3. Prompt for MySQL password
set /p MYSQL_PASS=Enter your MySQL password: 

REM 4. Create MariaDB database
echo [3/5] Creating MariaDB database...
mysql -u root -p%MYSQL_PASS% -e "CREATE DATABASE IF NOT EXISTS KopiGo;"

REM 5. Import schema.sql
echo [4/5] Importing SQL schema...
mysql -u root -p%MYSQL_PASS% KopiGo < schema.sql

REM 6. Run the Flask app
echo [5/5] Running Flask app...
set MYSQL_PASS=%MYSQL_PASS%
python app.py

echo === Setup complete! Visit http://127.0.0.1:5000/ in your browser ===
pause