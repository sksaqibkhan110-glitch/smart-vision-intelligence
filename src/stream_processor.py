import os
import time
import datetime
import cv2
import numpy as np
from ultralytics import YOLO
from src.database import AlertDatabase

class StreamProcessor:
    def __init__(self, source=0, model_path="yolov8n.pt", cooldown=3):
        self.source = source
        self.detector = YOLO(model_path)
        self.db = AlertDatabase()
        self.cooldown = cooldown
        self.last_alert_time = 0
        self.storage_path = "data/alerts"
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.roi_boundary = np.array([
            [300, 100], 
            [620, 100], 
            [620, 460], 
            [300, 460]
        ], np.int32)

    def _is_inside_roi(self, point):
        return cv2.pointPolygonTest(self.roi_boundary, point, False) >= 0

    def start_pipeline(self):
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            return

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            overlay = frame.copy()
            cv2.polylines(frame, [self.roi_boundary], True, (0, 0, 255), 2)
            cv2.fillPoly(overlay, [self.roi_boundary], (0, 0, 255))
            blended = cv2.addWeighted(overlay, 0.25, frame, 0.75, 0)
            cv2.putText(blended, "SECURE ZONE", (305, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            detections = self.detector(frame, stream=True, verbose=False)
            has_breach = False
            top_conf = 0.0
            now = time.time()

            for det in detections:
                blended = det.plot()
                for b in det.boxes:
                    cls_id = int(b.cls[0])
                    label = self.detector.names[cls_id]
                    score = float(b.conf[0])

                    if label == "person":
                        x1, y1, x2, y2 = map(int, b.xyxy[0])
                        ground_point = (int((x1 + x2) / 2), y2)

                        if self._is_inside_roi(ground_point):
                            has_breach = True
                            if score > top_conf:
                                top_conf = score

            if has_breach:
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(
                    blended, 
                    f"BREACH WARNING [{ts}]", 
                    (25, 45), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.8, 
                    (0, 0, 255), 
                    2
                )

                if now - self.last_alert_time > self.cooldown:
                    path = f"{self.storage_path}/breach_{int(now)}.jpg"
                    cv2.imwrite(path, frame)
                    self.db.log_alert("zone_intrusion", top_conf, path)
                    self.last_alert_time = now

            cv2.imshow("Multi-Feed Edge Processor", blended)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()