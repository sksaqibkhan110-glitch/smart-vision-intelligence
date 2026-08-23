import requests

# Apna exact Token aur Chat ID yahan daalo
BOT_TOKEN = "PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE"
CHAT_ID = "PASTE_YOUR_NUMERIC_CHAT_ID_HERE"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": "🚨 *Test Security Alert:* Telegram connection successful!",
    "parse_mode": "Markdown"
}

print(f"Connecting to Telegram API with Chat ID: {CHAT_ID}...")
response = requests.post(url, json=payload)
print("Status Code:", response.status_code)
print("Response Body:", response.json())