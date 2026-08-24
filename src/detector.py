import cv2
import time
import os
import threading
from ultralytics import YOLO
from src.database import AlertDatabase
from src.notifier import AlertNotifier
from src.face_engine import FaceEngine
from src.zone_config import load_zones
from src.liveness import LivenessDetector

class VisionDetector:
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)
        self.db = AlertDatabase()
        self.notifier = AlertNotifier()
        self.face_engine = FaceEngine()
        self.liveness = LivenessDetector()
        
        zones = load_zones()
        self.z1_x_min = zones["zone1_caution"]["x_min"]
        self.z1_x_max = zones["zone1_caution"]["x_max"]
        self.z2_x_min = zones["zone2_critical"]["x_min"]
        self.z2_x_max = zones["zone2_critical"]["x_max"]
        
        self.target_classes = {0: "Person", 67: "Cell Phone", 24: "Backpack"}
        self.last_alert_time = 0
        self.cooldown_sec = 6
        self.frame_count = 0
        self.last_verified_status = "UNKNOWN"
        self.is_checking_face = False

    def get_spatial_zone(self, cx, width):
        norm_x = cx / width
        if norm_x <= self.z1_x_max:
            return "ZONE 1 (CAUTION)", (0, 255, 255)
        elif norm_x >= self.z2_x_min:
            return "ZONE 2 (CRITICAL)", (0, 0, 255)
        return "SECURE ZONE", (0, 255, 0)

    def _verify_async(self, crop):
        try:
            is_auth, name_label = self.face_engine.match_face(crop)
            self.last_verified_status = name_label if is_auth else "INTRUDER"
        finally:
            self.is_checking_face = False

    def process_frame(self, frame):
        if frame is None or frame.size == 0:
            return frame

        self.frame_count += 1
        h, w, _ = frame.shape
        results = self.model(frame, verbose=False)[0]

        is_live, _, blinks = self.liveness.check_liveness(frame)

        # Draw Clear Single Line Boundaries
        z1_w = int(w * self.z1_x_max)
        z2_w = int(w * self.z2_x_min)
        cv2.line(frame, (z1_w, 0), (z1_w, h), (0, 255, 255), 2)
        cv2.putText(frame, "ZONE 1 (CAUTION)", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.line(frame, (z2_w, 0), (z2_w, h), (0, 0, 255), 2)
        cv2.putText(frame, "ZONE 2 (CRITICAL)", (z2_w + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        for box in results.boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            min_thresh = 0.25 if cls_id == 67 else 0.40

            if cls_id in self.target_classes and conf > min_thresh:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                
                zone_label, zone_color = self.get_spatial_zone(cx, w)
                is_authorized = False
                display_label = f"{self.target_classes[cls_id]} {conf:.2f}"

                if cls_id == 0:
                    crop = frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                    if crop.size > 0:
                        if self.frame_count % 10 == 0 and not self.is_checking_face:
                            self.is_checking_face = True
                            threading.Thread(target=self._verify_async, args=(crop.copy(),), daemon=True).start()

                        if "AUTHORIZED" in self.last_verified_status:
                            if is_live:
                                is_authorized = True
                                display_label = f"{self.last_verified_status} [LIVE: {blinks}]"
                                zone_color = (0, 255, 0)
                            else:
                                display_label = f"{self.last_verified_status} [BLINK NEEDED]"
                                zone_color = (0, 255, 255)
                        else:
                            display_label = f"INTRUDER ({conf:.2f})"
                else:
                    is_authorized = False
                    if zone_label == "ZONE 2 (CRITICAL)":
                        zone_color = (0, 0, 255)

                full_tag = f"{display_label} | {zone_label}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), zone_color, 2)
                cv2.circle(frame, (cx, cy), 4, zone_color, -1)
                cv2.putText(frame, full_tag, (x1, max(25, y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, zone_color, 2)

                if zone_label == "ZONE 2 (CRITICAL)" and not is_authorized:
                    current_time = time.time()
                    if current_time - self.last_alert_time > self.cooldown_sec:
                        self.last_alert_time = current_time
                        snap_path = f"data/alerts/breach_{int(current_time)}.jpg"
                        cv2.imwrite(snap_path, frame)
                        threat_desc = f"UNAUTHORIZED_{self.target_classes[cls_id].upper()}"
                        self.db.log_alert(threat_desc, conf, snap_path)
                        self.notifier.dispatch_alert(threat_desc, conf, snap_path)

        return frame