#!/bin/bash

# Exit on error
set -e

# Activate venv
source venv/bin/activate

# Run the bot
python telegram_bot.py || {
    echo ""
    echo "[ERROR] Bot exited with error code $?"
}

# Deactivate
deactivate