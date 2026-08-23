import threading
import requests

BOT_TOKEN = "8905501478:AAFAFHDf-S1xIeVc4nAFJabGVjCohoeWIr8"
CHAT_ID = "8130783483"

def _send_telegram(message: str, image_path: str = None):
    try:
        # 1. Send text details
        text_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(text_url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=8)

        # 2. Send snapshot photo
        if image_path:
            photo_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(image_path, "rb") as photo:
                requests.post(photo_url, data={"chat_id": CHAT_ID}, files={"photo": photo}, timeout=10)
    except Exception as e:
        print(f"[Notifier Error]: {e}")

def trigger_alert(threat_type: str, item: str, confidence: float, image_path: str = None):
    msg = (
        f"🚨 *CRITICAL SECURITY BREACH* 🚨\n\n"
        f"• *Threat Level:* {threat_type}\n"
        f"• *Object Detected:* {item}\n"
        f"• *Confidence:* {confidence:.2f}\n"
        f"• *Zone:* Restricted Area (Zone 2)"
    )
    threading.Thread(target=_send_telegram, args=(msg, image_path), daemon=True).start()