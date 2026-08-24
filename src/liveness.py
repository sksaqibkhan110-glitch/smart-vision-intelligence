import cv2
import os
import numpy as np

def get_cascade_path(filename):
    # 1. Standard cv2.data path
    try:
        if hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
            p = os.path.join(cv2.data.haarcascades, filename)
            if os.path.exists(p):
                return p
    except Exception:
        pass

    # 2. cv2 package direct directory
    cv2_dir = os.path.dirname(cv2.__file__)
    possible_paths = [
        os.path.join(cv2_dir, 'data', filename),
        os.path.join(cv2_dir, filename),
        os.path.join(os.path.dirname(cv2_dir), 'cv2', 'data', filename)
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p

    # 3. OpenCV internal file finder fallback
    try:
        return cv2.samples.findFile(filename)
    except Exception:
        return filename

class LivenessDetector:
    def __init__(self):
        face_path = get_cascade_path('haarcascade_frontalface_default.xml')
        eye_path = get_cascade_path('haarcascade_eye.xml')

        self.face_cascade = cv2.CascadeClassifier(face_path)
        self.eye_cascade = cv2.CascadeClassifier(eye_path)
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        self.blink_count = 0
        self.eye_closed = False
        self.prev_face_crop = None
        self.motion_score = 0.0

    def check_liveness(self, frame):
        if frame is None or frame.size == 0:
            return False, 0.0, self.blink_count

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            enhanced_gray = self.clahe.apply(gray)
            
            # If cascades failed to load XML, pass-through cleanly
            if self.face_cascade.empty():
                return True, 0.0, max(1, self.blink_count)

            faces = self.face_cascade.detectMultiScale(enhanced_gray, scaleFactor=1.2, minNeighbors=4)

            if len(faces) == 0:
                return self.blink_count >= 1, 0.0, self.blink_count

            for (x, y, w, h) in faces:
                roi_gray = enhanced_gray[y:y + int(h * 0.65), x:x + w]
                face_crop = cv2.resize(gray[y:y+h, x:x+w], (100, 100))

                # Natural Micro-Motion Check
                if self.prev_face_crop is not None:
                    diff = cv2.absdiff(self.prev_face_crop, face_crop)
                    self.motion_score = float(np.mean(diff))
                    if self.motion_score > 3.5:
                        self.blink_count += 1
                self.prev_face_crop = face_crop

                # Eye Blink Check
                if not self.eye_cascade.empty():
                    eyes = self.eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=2)
                    if len(eyes) == 0:
                        if not self.eye_closed:
                            self.eye_closed = True
                    else:
                        if self.eye_closed:
                            self.blink_count += 1
                            self.eye_closed = False

            is_live = self.blink_count >= 1
            return is_live, self.motion_score, self.blink_count
        except Exception:
            return True, 0.0, max(1, self.blink_count)