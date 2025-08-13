#!/bin/bash

# Exit on error
set -e

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate environment
source venv/bin/activate

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "[INFO] Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "[WARN] requirements.txt not found. Installing base packages..."
    pip install python-telegram-bot jinja2 python-dotenv colorlog rich
fi

# Deactivate
deactivate

echo "[OK] Setup completed. Use ./start.sh to run the bot."