#!/bin/bash

echo "=== Setting up KopiGo environment ==="

# 1. Create virtual environment
echo "[1/5] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 2. Install Python dependencies
echo "[2/5] Installing Python dependencies..."
pip install flask flask-sqlalchemy pymysql boto3 pillow flask-bcrypt pandas pymongo requests

# Prompt for password (without showing input)
read -sp "Enter your MySQL password: " MYSQL_PASS
echo ""

# 3. Set up MariaDB
echo "[3/5] Creating MariaDB database..."
mysql -u root -p"$MYSQL_PASS" -e "CREATE DATABASE IF NOT EXISTS KopiGo;"

# 4. Import schema.sql
echo "[4/5] Importing SQL schema..."
mysql -u root -p"$MYSQL_PASS" KopiGo < schema.sql

# 5. Run the Flask app
echo "[5/5] Running Flask app..."
export MYSQL_PASS  # In case your app.py reads it
python app.py

echo "=== Setup complete! Visit http://127.0.0.1:5000/ in your browser ==="