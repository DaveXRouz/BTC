#!/bin/bash

export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Library/Frameworks/Python.framework/Versions/3.12/bin:$PATH"

REPO=/Users/hamzeh/Desktop/GitHub/BTC
PYTHON=/Library/Frameworks/Python.framework/Versions/3.12/bin/python3

# Auto-update in background (non-blocking)
(cd "$REPO" && git pull origin main --ff-only 2>/dev/null && cp -f "$REPO/scripts/launcher.sh" /Users/hamzeh/Desktop/NPS.app/Contents/MacOS/NPS 2>/dev/null) &

# Kill any previous NPS server
lsof -ti:8000 | xargs kill 2>/dev/null
sleep 0.5

# Start V4 API + frontend (single server, survives script exit)
cd "$REPO/v4/api"
nohup arch -arm64 "$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --loop asyncio > /tmp/nps-server.log 2>&1 &
disown

# Wait for server to be ready (up to 15s), then open browser
for i in $(seq 1 15); do
  curl -s -o /dev/null http://127.0.0.1:8000/api/health && break
  sleep 1
done
open http://127.0.0.1:8000
