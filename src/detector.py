import os
import time
import datetime
import threading
import cv2
import numpy as np
import pygame
from ultralytics import YOLO
from src.database import AlertDatabase
from src.notifier import trigger_alert

class VisionDetector:
    def __init__(self, model_path="yolov8n.pt"):
        self.detector = YOLO(model_path)
        self.db_manager = AlertDatabase()
        self.last_capture_ts = 0
        self.cooldown_sec = 3
        self.storage_dir = "data/alerts"
        self.sound_file = "data/siren.mp3"
        os.makedirs(self.storage_dir, exist_ok=True)

        pygame.mixer.init()
        self.alert_sound = None
        if os.path.exists(self.sound_file):
            try:
                self.alert_sound = pygame.mixer.Sound(self.sound_file)
            except Exception:
                self.alert_sound = None

        self.target_classes = {
            "person": "Person",
            "cell phone": "Electronic Device",
            "remote": "Electronic Device",
            "laptop": "Electronic Device",
            "tv": "Display Screen",
            "backpack": "Baggage",
            "handbag": "Baggage",
            "suitcase": "Baggage"
        }

        self.warning_zone = np.array([[40, 145], [280, 145], [280, 455], [40, 455]], np.int32)
        self.critical_zone = np.array([[360, 145], [600, 145], [600, 455], [360, 455]], np.int32)
        
        self.edit_mode = 0  # 0: None, 1: Zone 1, 2: Zone 2
        self.temp_points = []
        self.prev_frame_time = 0

    def _play_siren(self):
        try:
            if self.alert_sound:
                self.alert_sound.play()
        except Exception:
            pass

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and self.edit_mode in [1, 2]:
            self.temp_points.append([x, y])
            if len(self.temp_points) == 4:
                if self.edit_mode == 1:
                    self.warning_zone = np.array(self.temp_points, np.int32)
                elif self.edit_mode == 2:
                    self.critical_zone = np.array(self.temp_points, np.int32)
                
                self.temp_points = []
                self.edit_mode = 0

    def _render_zones(self, frame):
        overlay = frame.copy()
        
        cv2.polylines(frame, [self.warning_zone], True, (0, 215, 255), 2)
        cv2.fillPoly(overlay, [self.warning_zone], (0, 215, 255))
        
        cv2.polylines(frame, [self.critical_zone], True, (0, 0, 255), 2)
        cv2.fillPoly(overlay, [self.critical_zone], (0, 0, 255))
        
        blended = cv2.addWeighted(overlay, 0.18, frame, 0.82, 0)
        
        cv2.rectangle(blended, (40, 120), (200, 144), (20, 20, 20), -1)
        cv2.putText(blended, "ZONE 1: CAUTION", (45, 137), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 215, 255), 1)

        cv2.rectangle(blended, (360, 120), (525, 144), (20, 20, 20), -1)
        cv2.putText(blended, "ZONE 2: CRITICAL", (365, 137), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
        
        for pt in self.temp_points:
            cv2.circle(blended, tuple(pt), 5, (0, 255, 255), -1)
            
        return blended

    def _render_hud(self, img, fps, threat_level, active_entities):
        cv2.rectangle(img, (10, 10), (320, 115), (15, 15, 15), -1)
        cv2.rectangle(img, (10, 10), (320, 115), (70, 70, 70), 1)

        cv2.putText(img, f"FPS: {fps:.1f}", (20, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        
        entity_str = ", ".join(active_entities) if active_entities else "None"
        cv2.putText(img, f"Tracked: {entity_str}", (20, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1)

        if threat_level == "CRITICAL":
            col, txt = (0, 0, 255), "LEVEL 2: CRITICAL BREACH"
        elif threat_level == "WARNING":
            col, txt = (0, 215, 255), "LEVEL 1: WARNING"
        else:
            col, txt = (0, 255, 0), "LEVEL 0: SECURE"

        cv2.putText(img, f"Threat: {txt}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.46, col, 2)

        if self.edit_mode == 1:
            calib_msg = f"CALIBRATING ZONE 1: Click {4 - len(self.temp_points)} pts"
            cv2.putText(img, calib_msg, (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 215, 255), 1)
        elif self.edit_mode == 2:
            calib_msg = f"CALIBRATING ZONE 2: Click {4 - len(self.temp_points)} pts"
            cv2.putText(img, calib_msg, (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 255), 1)
        else:
            cv2.putText(img, "Calib: [1] Zone 1  [2] Zone 2  [R] Reset", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 180, 180), 1)

    def process_frame(self, frame):
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - self.prev_frame_time) if self.prev_frame_time > 0 else 30.0
        self.prev_frame_time = new_frame_time

        blended = self._render_zones(frame)
        predictions = self.detector(frame, stream=True, verbose=False, conf=0.35)
        
        threat_level = "SECURE"
        highest_conf = 0.0
        active_items = []
        now = time.time()

        for pred in predictions:
            for b in pred.boxes:
                cls_idx = int(b.cls[0])
                raw_label = self.detector.names[cls_idx]
                score = float(b.conf[0])
                x1, y1, x2, y2 = map(int, b.xyxy[0])

                center_pt = (int((x1 + x2) / 2), int((y1 + y2) / 2))
                
                in_critical = cv2.pointPolygonTest(self.critical_zone, center_pt, False) >= 0
                in_warning = cv2.pointPolygonTest(self.warning_zone, center_pt, False) >= 0

                if raw_label in self.target_classes:
                    display_tag = self.target_classes[raw_label]
                    active_items.append(raw_label)

                    if in_critical:
                        threat_level = "CRITICAL"
                        if score > highest_conf:
                            highest_conf = score
                        cv2.rectangle(blended, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.rectangle(blended, (x1, y2 - 20), (x1 + 140, y2), (0, 0, 255), -1)
                        cv2.putText(blended, f"{display_tag} {score:.2f}", (x1 + 4, y2 - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)
                    elif in_warning:
                        if threat_level != "CRITICAL":
                            threat_level = "WARNING"
                        if score > highest_conf:
                            highest_conf = score
                        cv2.rectangle(blended, (x1, y1), (x2, y2), (0, 215, 255), 2)
                        cv2.rectangle(blended, (x1, y2 - 20), (x1 + 140, y2), (0, 215, 255), -1)
                        cv2.putText(blended, f"{display_tag} {score:.2f}", (x1 + 4, y2 - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1)

        if threat_level == "CRITICAL":
            if now - self.last_capture_ts > self.cooldown_sec:
                threading.Thread(target=self._play_siren, daemon=True).start()
                img_name = f"{self.storage_dir}/critical_{int(now)}.jpg"
                cv2.imwrite(img_name, frame)
                self.db_manager.log_alert("critical_zone_breach", highest_conf, img_name)
                
                # Instant Alert Dispatch via Background Thread
                primary_item = active_items[0] if active_items else "Unknown Intruder"
                trigger_alert("CRITICAL (Zone 2)", primary_item, highest_conf, img_name)
                
                self.last_capture_ts = now
        elif threat_level == "WARNING":
            if now - self.last_capture_ts > self.cooldown_sec:
                img_name = f"{self.storage_dir}/warning_{int(now)}.jpg"
                cv2.imwrite(img_name, frame)
                self.db_manager.log_alert("warning_zone_entry", highest_conf, img_name)
                self.last_capture_ts = now

        self._render_hud(blended, fps, threat_level, list(set(active_items)))
        return blended

    def run_live_feed(self):
        stream = cv2.VideoCapture(0)
        if not stream.isOpened():
            return

        window_name = "Smart Vision Intelligence - Multi Zone"
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, self.mouse_callback)

        while True:
            ret, frame = stream.read()
            if not ret:
                break

            output_frame = self.process_frame(frame)
            cv2.imshow(window_name, output_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('1'):
                self.edit_mode = 1
                self.temp_points = []
            elif key == ord('2'):
                self.edit_mode = 2
                self.temp_points = []
            elif key == ord('r'):
                self.warning_zone = np.array([[40, 145], [280, 145], [280, 455], [40, 455]], np.int32)
                self.critical_zone = np.array([[360, 145], [600, 145], [600, 455], [360, 455]], np.int32)
                self.edit_mode = 0
                self.temp_points = []

        stream.release()
        cv2.destroyAllWindows()