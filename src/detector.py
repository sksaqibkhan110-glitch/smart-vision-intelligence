import os
import time
import datetime
import cv2
import numpy as np
from ultralytics import YOLO
from src.database import AlertDatabase

class VisionDetector:
    def __init__(self, model_path="yolov8n.pt"):
        self.detector = YOLO(model_path)
        self.db_manager = AlertDatabase()
        self.last_capture_ts = 0
        self.cooldown_sec = 3
        self.storage_dir = "data/alerts"
        os.makedirs(self.storage_dir, exist_ok=True)

        self.roi_poly = np.array([
            [300, 100], 
            [620, 100], 
            [620, 460], 
            [300, 460]
        ], np.int32)

    def _check_point_in_zone(self, pt):
        return cv2.pointPolygonTest(self.roi_poly, pt, False) >= 0

    def _render_zone_overlay(self, img):
        mask = img.copy()
        cv2.polylines(img, [self.roi_poly], True, (0, 0, 255), 2)
        cv2.fillPoly(mask, [self.roi_poly], (0, 0, 255))
        blended = cv2.addWeighted(mask, 0.2, img, 0.8, 0)
        cv2.putText(blended, "RESTRICTED SECURITY ZONE", (305, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
        return blended

    def process_frame(self, frame):
        annotated_canvas = self._render_zone_overlay(frame)
        predictions = self.detector(frame, stream=True, verbose=False)
        
        breach_flag = False
        peak_confidence = 0.0
        now = time.time()

        for pred in predictions:
            annotated_canvas = pred.plot()
            for b in pred.boxes:
                cls_idx = int(b.cls[0])
                entity_type = self.detector.names[cls_idx]
                score = float(b.conf[0])

                if entity_type == "person":
                    x1, y1, x2, y2 = map(int, b.xyxy[0])
                    base_point = (int((x1 + x2) / 2), y2)

                    if self._check_point_in_zone(base_point):
                        breach_flag = True
                        if score > peak_confidence:
                            peak_confidence = score

        if breach_flag:
            curr_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(
                annotated_canvas,
                f"CRITICAL: ZONE BREACH [{curr_str}]",
                (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 0, 255),
                2
            )

            if now - self.last_capture_ts > self.cooldown_sec:
                img_name = f"{self.storage_dir}/breach_{int(now)}.jpg"
                cv2.imwrite(img_name, frame)
                self.db_manager.log_alert("zone_intrusion", peak_confidence, img_name)
                self.last_capture_ts = now

        return annotated_canvas

    def run_live_feed(self):
        stream = cv2.VideoCapture(0)
        if not stream.isOpened():
            return

        while True:
            ret, frame = stream.read()
            if not ret:
                break

            output_frame = self.process_frame(frame)
            cv2.imshow("Smart Vision Intelligence", output_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        stream.release()
        cv2.destroyAllWindows()