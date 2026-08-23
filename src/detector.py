import cv2
from ultralytics import YOLO
import datetime
import os
import time
from src.database import AlertDatabase

class VisionDetector:
    def __init__(self, model_name="yolov8n.pt"):
        self.model = YOLO(model_name)
        self.db = AlertDatabase()
        self.last_alert_time = 0
        self.alert_cooldown = 3  # Har 3 second me 1 baar log karega
        os.makedirs("data/alerts", exist_ok=True)

    def process_frame(self, frame):
        results = self.model(frame, stream=True, verbose=False)
        detected_objects = []
        highest_conf = 0.0

        for result in results:
            annotated_frame = result.plot()
            for box in result.boxes:
                class_id = int(box.cls[0])
                label = self.model.names[class_id]
                conf = float(box.conf[0])
                detected_objects.append(label)
                if conf > highest_conf:
                    highest_conf = conf

        current_time = time.time()
        # Agar person detect ho aur 3 second ka gap ho chuka ho
        if "person" in detected_objects:
            timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Draw Alert Banner
            cv2.putText(
                annotated_frame,
                f"ALERT: Person Detected [{timestamp_str}]",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

            # Log to DB and save frame
            if current_time - self.last_alert_time > self.alert_cooldown:
                file_name = f"data/alerts/alert_{int(current_time)}.jpg"
                cv2.imwrite(file_name, frame)
                self.db.log_alert("person", highest_conf, file_name)
                self.last_alert_time = current_time

        return annotated_frame

    def run_live_feed(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Camera not found.")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            processed_frame = self.process_frame(frame)
            cv2.imshow("Smart Vision Intelligence", processed_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()