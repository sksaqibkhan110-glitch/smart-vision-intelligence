import os
import cv2
from deepface import DeepFace

class FaceEngine:
    def __init__(self, db_path="data/authorized"):
        self.db_path = db_path
        os.makedirs(self.db_path, exist_ok=True)
        self.model_name = "VGG-Face"

    def match_face(self, person_crop):
        if person_crop is None or person_crop.size == 0:
            return False, "UNKNOWN INTRUDER"

        valid_files = [
            os.path.join(self.db_path, f) 
            for f in os.listdir(self.db_path) 
            if f.lower().endswith(('.jpg', '.png', '.jpeg'))
        ]

        if not valid_files:
            return False, "UNKNOWN INTRUDER"

        for ref_img in valid_files:
            try:
                # Direct in-memory array verification with skip detector
                res = DeepFace.verify(
                    img1_path=person_crop,
                    img2_path=ref_img,
                    model_name=self.model_name,
                    detector_backend="skip",
                    distance_metric="cosine",
                    enforce_detection=False
                )
                
                dist = res.get("distance", 1.0)
                is_verified = res.get("verified", False)

                if is_verified or dist <= 0.60:
                    raw_name = os.path.basename(ref_img).split('_')[0].split('.')[0]
                    return True, f"AUTHORIZED: {raw_name.upper()}"
            except Exception:
                continue

        return False, "UNKNOWN INTRUDER"