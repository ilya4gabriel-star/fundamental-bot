#!/bin/bash
cd /app/services
python3 -c "
import urllib.request
files = ['signals.py', 'paper_trading.py', 'alerts.py']
for f in files:
    try:
        urllib.request.urlretrieve(f'https://raw.githubusercontent.com/ilya4gabriel-star/fundamental-bot/main/services/{f}', f)
    except: pass
"
cd /app
python3 -c "
import urllib.request
for f in ['handlers/commands.py', 'main.py']:
    try:
        urllib.request.urlretrieve(f'https://raw.githubusercontent.com/ilya4gabriel-star/fundamental-bot/main/{f}', f)
    except: pass
"
python3 main.py
