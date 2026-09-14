import cv2
import time
import os
import threading
import gc
import numpy as np
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
        
        self.reload_zones()
        
        self.target_classes = {
            0: "Person", 67: "Cell Phone", 24: "Backpack", 43: "Knife", 76: "Scissors", 77: "Teddy Bear"
        }

        self.last_alert_time = 0
        self.cooldown_sec = 3.0
        self.frame_count = 0
        
        # Face Verification Cache
        self.face_cache = {}
        self.checking_boxes = set()
        
        # Caution Continuous Trigger State
        self.caution_entry_time = None
        self.last_unauthorized_seen = 0
        self.caution_limit_sec = 3.0
        self.grace_period_sec = 1.2
        self.caution_alarm_active = False

        # FPS Optimization Buffers
        self.cached_boxes = []
        self.cached_is_live = False
        self.cached_blinks = 0
        self.fps_start_time = time.time()
        self.fps_counter = 0
        self.current_fps = 0.0

    def reload_zones(self):
        zones = load_zones()
        raw_z1 = zones.get("zone1_caution", {}).get("polygon", [])
        raw_z2 = zones.get("zone2_critical", {}).get("polygon", [])

        self.z1_poly = np.array(raw_z1, dtype=np.int32) if len(raw_z1) >= 3 else np.array([], dtype=np.int32)
        self.z2_poly = np.array(raw_z2, dtype=np.int32) if len(raw_z2) >= 3 else np.array([], dtype=np.int32)

        self.z1_x_max = float(zones.get("zone1_caution", {}).get("x_max", 0.40))
        self.z2_x_min = float(zones.get("zone2_critical", {}).get("x_min", 0.60))

    def check_point_in_zone(self, cx, cy, w, h):
        if len(self.z2_poly) >= 3:
            if cv2.pointPolygonTest(self.z2_poly, (float(cx), float(cy)), False) >= 0:
                return "ZONE 2 (CRITICAL)", (0, 0, 255)
        elif cx / w >= self.z2_x_min:
            return "ZONE 2 (CRITICAL)", (0, 0, 255)

        if len(self.z1_poly) >= 3:
            if cv2.pointPolygonTest(self.z1_poly, (float(cx), float(cy)), False) >= 0:
                return "ZONE 1 (CAUTION)", (0, 255, 255)
        elif cx / w <= self.z1_x_max:
            return "ZONE 1 (CAUTION)", (0, 255, 255)

        return "SECURE ZONE", (0, 255, 0)

    def _verify_individual_face(self, crop, box_id):
        try:
            is_auth, name_label = self.face_engine.match_face(crop)
            status = name_label if is_auth else "INTRUDER"
            self.face_cache[box_id] = (status, time.time())
        except Exception:
            self.face_cache[box_id] = ("INTRUDER", time.time())
        finally:
            self.checking_boxes.discard(box_id)

    def process_frame(self, frame):
        if frame is None or frame.size == 0:
            return frame

        self.frame_count += 1
        h, w, _ = frame.shape
        now = time.time()

        # Real-Time FPS Calculation
        self.fps_counter += 1
        if now - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter / (now - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = now

        # Periodic Memory Cleanup (Every 200 frames)
        if self.frame_count % 200 == 0:
            gc.collect()

        # Alternating Frame Inference (Run YOLO every 2nd frame for 2x FPS Boost)
        if self.frame_count % 2 == 0 or not self.cached_boxes:
            results = self.model(frame, conf=0.20, iou=0.40, verbose=False)[0]
            new_boxes = []
            if results.boxes is not None and len(results.boxes) > 0:
                for box in results.boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())

                    if cls_id not in self.target_classes:
                        continue
                    if cls_id == 0 and conf < 0.40:
                        continue

                    coords = list(map(int, box.xyxy[0].tolist()))
                    new_boxes.append((cls_id, conf, coords))
            self.cached_boxes = new_boxes

        # Downscaled Fast Liveness Check (Every 3rd frame)
        if self.frame_count % 3 == 0:
            small_frame = cv2.resize(frame, (320, 240))
            is_live, _, blinks = self.liveness.check_liveness(small_frame)
            self.cached_is_live = is_live
            self.cached_blinks = blinks

        # Draw Zones
        if len(self.z1_poly) >= 3:
            cv2.polylines(frame, [self.z1_poly], isClosed=True, color=(0, 255, 255), thickness=2)
            cv2.putText(frame, "ZONE 1 (CAUTION)", (int(self.z1_poly[0][0]), max(25, int(self.z1_poly[0][1]))),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        else:
            z1_w = int(w * self.z1_x_max)
            cv2.line(frame, (z1_w, 0), (z1_w, h), (0, 255, 255), 2)
            cv2.putText(frame, "ZONE 1 (CAUTION)", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        if len(self.z2_poly) >= 3:
            cv2.polylines(frame, [self.z2_poly], isClosed=True, color=(0, 0, 255), thickness=2)
            cv2.putText(frame, "ZONE 2 (CRITICAL)", (int(self.z2_poly[0][0]), max(25, int(self.z2_poly[0][1]))),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            z2_w = int(w * self.z2_x_min)
            cv2.line(frame, (z2_w, 0), (z2_w, h), (0, 0, 255), 2)
            cv2.putText(frame, "ZONE 2 (CRITICAL)", (z2_w + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        unauthorized_in_caution = False
        active_threat_name = "UNAUTHORIZED_OBJECT"

        # Process Cached Detection Boxes
        for cls_id, conf, (x1, y1, x2, y2) in self.cached_boxes:
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            zone_label, zone_color = self.check_point_in_zone(cx, cy, w, h)
            obj_name = self.target_classes.get(cls_id, f"Item_{cls_id}")
            display_label = f"{obj_name} {conf:.2f}"
            is_this_item_authorized = False

            # Person Biometrics
            if cls_id == 0:
                crop = frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                box_key = f"{int(cx/60)}_{int(cy/60)}"

                if crop.size > 0:
                    cached_entry = self.face_cache.get(box_key)
                    if cached_entry is None or (now - cached_entry[1] > 2.5):
                        if box_key not in self.checking_boxes:
                            self.checking_boxes.add(box_key)
                            threading.Thread(target=self._verify_individual_face, args=(crop.copy(), box_key), daemon=True).start()

                    person_status = self.face_cache.get(box_key, ("VERIFYING...", 0))[0]

                    if "AUTHORIZED" in person_status:
                        if self.cached_is_live:
                            is_this_item_authorized = True
                            display_label = f"{person_status} [LIVE: {self.cached_blinks}]"
                            zone_color = (0, 255, 0)
                        else:
                            display_label = f"{person_status} [BLINK NEEDED]"
                            zone_color = (0, 255, 255)
                    elif person_status == "VERIFYING...":
                        display_label = f"VERIFYING... ({conf:.2f})"
                        zone_color = (0, 255, 255)
                    else:
                        display_label = f"INTRUDER ({conf:.2f})"
                        if zone_label == "ZONE 2 (CRITICAL)":
                            zone_color = (0, 0, 255)
            else:
                is_this_item_authorized = False
                if zone_label == "ZONE 2 (CRITICAL)":
                    zone_color = (0, 0, 255)

            if zone_label == "ZONE 1 (CAUTION)" and not is_this_item_authorized:
                unauthorized_in_caution = True
                active_threat_name = obj_name
                self.last_unauthorized_seen = now

            # Render Detection Box
            full_tag = f"{display_label} | {zone_label}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), zone_color, 2)
            cv2.circle(frame, (cx, cy), 4, zone_color, -1)
            cv2.putText(frame, full_tag, (x1, max(25, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, zone_color, 2)

            # Zone 2 Critical Dispatch
            if zone_label == "ZONE 2 (CRITICAL)" and not is_this_item_authorized:
                if now - self.last_alert_time > self.cooldown_sec:
                    self.last_alert_time = now
                    snap_path = f"data/alerts/breach_{int(now)}.jpg"
                    cv2.imwrite(snap_path, frame)
                    threat_desc = f"CRITICAL_BREACH_{obj_name.upper()}"
                    self.db.log_alert(threat_desc, conf, snap_path)
                    self.notifier.dispatch_alert(threat_desc, conf, snap_path)

        # Caution Zone Continuous Logic
        is_caution_occupied = unauthorized_in_caution or (now - self.last_unauthorized_seen < self.grace_period_sec)

        if is_caution_occupied:
            if self.caution_entry_time is None:
                self.caution_entry_time = now

            elapsed = now - self.caution_entry_time
            remaining = max(0, int(self.caution_limit_sec - elapsed + 0.99))

            if self.caution_alarm_active or elapsed >= self.caution_limit_sec:
                self.caution_alarm_active = True

                cv2.rectangle(frame, (10, 45), (370, 85), (0, 0, 0), -1)
                cv2.rectangle(frame, (10, 45), (370, 85), (0, 0, 255), 2)
                cv2.putText(frame, "🚨 ACTIVE THREAT IN CAUTION ZONE!", (18, 72),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)

                if now - self.last_alert_time > self.cooldown_sec:
                    self.last_alert_time = now
                    snap_path = f"data/alerts/loiter_{int(now)}.jpg"
                    cv2.imwrite(snap_path, frame)
                    threat_desc = f"PERSISTENT_THREAT_{active_threat_name.upper()}"
                    self.db.log_alert(threat_desc, 0.95, snap_path)
                    self.notifier.dispatch_alert(threat_desc, 0.95, snap_path)
            else:
                cv2.rectangle(frame, (10, 45), (330, 85), (0, 0, 0), -1)
                cv2.rectangle(frame, (10, 45), (330, 85), (0, 0, 255), 2)
                cv2.putText(frame, f"CAUTION COUNTDOWN: {remaining}s", (20, 72),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)
        else:
            self.caution_entry_time = None
            self.caution_alarm_active = False

        # Live FPS Overlay Tag
        cv2.putText(frame, f"FPS: {self.current_fps:.1f}", (w - 110, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return frame