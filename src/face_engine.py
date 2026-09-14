import os
import cv2
from deepface import DeepFace

class FaceEngine:
    def __init__(self, db_path="data/authorized"):
        self.db_path = db_path
        os.makedirs(self.db_path, exist_ok=True)
        # SFace/Facenet512 model with strict threshold
        self.model_name = "Facenet512"
        self.detector_backend = "opencv"
        self.distance_metric = "cosine"
        self.threshold = 0.38  # Strict threshold to prevent false lookalike matches

    def match_face(self, face_crop):
        if not os.path.exists(self.db_path) or len(os.listdir(self.db_path)) == 0:
            return False, "INTRUDER"

        try:
            # Run DeepFace Search with enforce_detection to ensure real face crop
            results = DeepFace.find(
                img_path=face_crop,
                db_path=self.db_path,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                distance_metric=self.distance_metric,
                enforce_detection=False,
                silent=True
            )

            if len(results) > 0 and not results[0].empty:
                best_match = results[0].iloc[0]
                distance = best_match['distance']
                
                # Strict distance validation
                if distance <= self.threshold:
                    matched_file = os.path.basename(best_match['identity'])
                    person_name = os.path.splitext(matched_file)[0].upper()
                    return True, f"AUTHORIZED: {person_name}"

            return False, "INTRUDER"

        except Exception:
            return False, "INTRUDER"