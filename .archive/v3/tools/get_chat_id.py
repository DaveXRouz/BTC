"""Utility to retrieve Telegram chat_id from recent bot messages.

Usage: python3 nps/tools/get_chat_id.py

1. Send any message to your bot on Telegram
2. Run this script
3. The chat_id will be auto-saved to config.json
"""

import json
import sys
import os
import urllib.request

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    from engines.config import load_config, get, set as config_set

    load_config()
    token = get("telegram.bot_token", "")

    if not token:
        print("Error: No bot_token in config.json")
        sys.exit(1)

    print(f"Using bot token: {token[:10]}...{token[-5:]}")
    print("Fetching recent messages...")

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NPS/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error fetching updates: {e}")
        sys.exit(1)

    if not data.get("ok"):
        print(f"Telegram API error: {data}")
        sys.exit(1)

    results = data.get("result", [])
    if not results:
        print("No messages found. Send a message to your bot first, then re-run.")
        sys.exit(0)

    chat_id = str(results[-1]["message"]["chat"]["id"])
    chat_name = results[-1]["message"]["chat"].get("first_name", "Unknown")
    print(f"Found chat_id: {chat_id} (from: {chat_name})")

    config_set("telegram.chat_id", chat_id)
    print(f"Saved chat_id to config.json")
    print("Telegram notifications are now configured!")


if __name__ == "__main__":
    main()
