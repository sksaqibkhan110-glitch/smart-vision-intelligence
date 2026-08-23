import os
import time
import datetime
import threading
import cv2
import numpy as np
import pygame
from ultralytics import YOLO
from src.database import AlertDatabase

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

        self.custom_points = []
        self.roi_poly = np.array([[300, 100], [620, 100], [620, 460], [300, 460]], np.int32)
        self.prev_frame_time = 0

    def _play_siren(self):
        try:
            if os.path.exists(self.sound_file):
                pygame.mixer.music.load(self.sound_file)
                pygame.mixer.music.play()
        except Exception:
            pass

    def _check_point_in_zone(self, pt):
        return cv2.pointPolygonTest(self.roi_poly, pt, False) >= 0

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.custom_points) >= 4:
                self.custom_points = []
            self.custom_points.append([x, y])
            if len(self.custom_points) == 4:
                self.roi_poly = np.array(self.custom_points, np.int32)

    def _render_hud(self, img, fps, person_count, breach_active):
        h, w, _ = img.shape
        cv2.rectangle(img, (10, 10), (260, 100), (20, 20, 20), -1)
        cv2.rectangle(img, (10, 10), (260, 100), (80, 80, 80), 1)

        cv2.putText(img, f"FPS: {fps:.1f}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
        cv2.putText(img, f"Persons In Frame: {person_count}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        threat_color = (0, 0, 255) if breach_active else (0, 255, 0)
        threat_text = "CRITICAL (BREACH)" if breach_active else "NORMAL"
        cv2.putText(img, f"Threat Status: {threat_text}", (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, threat_color, 2)

    def process_frame(self, frame):
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - self.prev_frame_time) if self.prev_frame_time > 0 else 30.0
        self.prev_frame_time = new_frame_time

        overlay = frame.copy()
        cv2.polylines(frame, [self.roi_poly], True, (0, 0, 255), 2)
        cv2.fillPoly(overlay, [self.roi_poly], (0, 0, 255))
        blended = cv2.addWeighted(overlay, 0.2, frame, 0.8, 0)

        predictions = self.detector(frame, stream=True, verbose=False)
        breach_flag = False
        peak_confidence = 0.0
        person_count = 0
        now = time.time()

        for pred in predictions:
            blended = pred.plot()
            for b in pred.boxes:
                cls_idx = int(b.cls[0])
                entity_type = self.detector.names[cls_idx]
                score = float(b.conf[0])

                if entity_type == "person":
                    person_count += 1
                    x1, y1, x2, y2 = map(int, b.xyxy[0])
                    base_point = (int((x1 + x2) / 2), y2)

                    if self._check_point_in_zone(base_point):
                        breach_flag = True
                        if score > peak_confidence:
                            peak_confidence = score

        if breach_flag and (now - self.last_capture_ts > self.cooldown_sec):
            threading.Thread(target=self._play_siren, daemon=True).start()
            img_name = f"{self.storage_dir}/breach_{int(now)}.jpg"
            cv2.imwrite(img_name, frame)
            self.db_manager.log_alert("zone_intrusion", peak_confidence, img_name)
            self.last_capture_ts = now

        self._render_hud(blended, fps, person_count, breach_flag)
        return blended

    def run_live_feed(self):
        stream = cv2.VideoCapture(0)
        if not stream.isOpened():
            return

        window_name = "Smart Vision Intelligence"
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
            elif key == ord('r'):
                self.roi_poly = np.array([[300, 100], [620, 100], [620, 460], [300, 460]], np.int32)
                self.custom_points = []

        stream.release()
        cv2.destroyAllWindows()