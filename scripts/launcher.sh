#!/bin/bash
cd /Users/hamzeh/Desktop/GitHub/BTC && git pull origin main --ff-only 2>/dev/null
cp -f /Users/hamzeh/Desktop/GitHub/BTC/scripts/launcher.sh /Users/hamzeh/Desktop/NPS.app/Contents/MacOS/NPS 2>/dev/null
open -a /Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app --args /Users/hamzeh/Desktop/GitHub/BTC/nps/main.py
