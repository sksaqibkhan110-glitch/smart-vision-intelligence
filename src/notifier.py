import threading
import os
import requests
import pygame
import winsound

class AlertNotifier:
    def __init__(self, siren_path="data/siren.mp3"):
        self.siren_path = siren_path
        self.bot_token = "8905501478:AAFAFHDf-S1xIeVc4nAFJabGVjCohoeWIr8"
        self.chat_id = "8130783483"
        
        try:
            pygame.mixer.init()
        except Exception:
            pass

    def _play_siren_async(self):
        # 1. Custom MP3 playback
        if os.path.exists(self.siren_path):
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.load(self.siren_path)
                pygame.mixer.music.play()
                return
            except Exception as e:
                print(f"[Audio Error]: {e}")

        # 2. Hardware fallback buzzer
        try:
            winsound.Beep(2500, 1000)
        except Exception:
            pass

    def _send_telegram_async(self, threat_type: str, confidence: float, snapshot_path: str):
        try:
            caption = (
                f"🚨 *CRITICAL SECURITY BREACH*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🎯 *Threat:* `{threat_type}`\n"
                f"📊 *Confidence:* `{confidence:.2f}`\n"
                f"📍 *Zone:* `Zone 2 (Restricted Perimeter)`\n"
                f"⚠️ *Status:* Intruder Escalation Active"
            )

            if snapshot_path and os.path.exists(snapshot_path):
                url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
                with open(snapshot_path, "rb") as photo_file:
                    requests.post(
                        url,
                        data={"chat_id": self.chat_id, "caption": caption, "parse_mode": "Markdown"},
                        files={"photo": photo_file},
                        timeout=10
                    )
            else:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                requests.post(
                    url,
                    json={"chat_id": self.chat_id, "text": caption, "parse_mode": "Markdown"},
                    timeout=10
                )
        except Exception:
            pass

    def dispatch_alert(self, threat_type: str, confidence: float, snapshot_path: str = None):
        print(f"\n[ALERT TRIGGERED] -> {threat_type} at {confidence:.2f}")
        threading.Thread(target=self._play_siren_async, daemon=True).start()
        threading.Thread(target=self._send_telegram_async, args=(threat_type, confidence, snapshot_path), daemon=True).start()