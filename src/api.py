import cv2
import time
import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from src.detector import VisionDetector
from src.database import AlertDatabase
from src.face_engine import FaceEngine
from src.zone_config import load_zones, save_zones, save_polygon_zones
from src.camera import get_camera

app = FastAPI(title="Smart Vision Intelligence API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detector_instance: Optional[VisionDetector] = None
db = AlertDatabase()

def get_detector() -> VisionDetector:
    global detector_instance
    if detector_instance is None:
        detector_instance = VisionDetector()
    return detector_instance

class ZoneUpdateRequest(BaseModel):
    caution_max: float
    critical_min: float

class PolygonUpdateRequest(BaseModel):
    zone1_poly: List[List[int]]
    zone2_poly: List[List[int]]

class CameraSwitchRequest(BaseModel):
    source: str

def generate_frames():
    cam = get_camera()
    detector = get_detector()

    while True:
        success, frame = cam.get_frame()
        if not success or frame is None:
            time.sleep(0.03)
            continue
        
        try:
            processed_frame = detector.process_frame(frame)
        except Exception:
            processed_frame = frame
        
        ret, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.02)

@app.get("/")
def root():
    return {"status": "online", "message": "Smart Vision Intelligence Server Running"}

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/alerts")
def get_alerts(limit: int = 15):
    try:
        logs = db.fetch_recent_alerts(limit)
        return {"status": "success", "alerts": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
def get_analytics():
    try:
        stats = db.fetch_analytics_summary()
        return {"status": "success", "analytics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/zones")
def get_zones():
    return load_zones()

@app.post("/zones")
def update_zones(req: ZoneUpdateRequest):
    saved = save_zones(req.caution_max, req.critical_min)
    detector = get_detector()
    detector.reload_zones()
    return {"status": "success", "zones": saved}

@app.post("/zones_polygon")
def update_polygon_zones(req: PolygonUpdateRequest):
    saved = save_polygon_zones(req.zone1_poly, req.zone2_poly)
    detector = get_detector()
    detector.reload_zones()
    return {"status": "success", "zones": saved}

@app.post("/switch_camera")
def switch_camera(req: CameraSwitchRequest):
    src_val = req.source.strip()
    if src_val.isdigit():
        src_val = int(src_val)
    cam = get_camera()
    cam.switch_source(src_val)
    return {"status": "success", "active_source": str(src_val)}

@app.post("/register_member")
async def register_member(name: str = Form(...), file: UploadFile = File(...)):
    try:
        os.makedirs("data/authorized", exist_ok=True)
        clean_name = name.strip().replace(" ", "_").upper()
        file_path = f"data/authorized/{clean_name}.jpg"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        detector = get_detector()
        detector.face_engine = FaceEngine()
        return {"status": "success", "message": f"Member {clean_name} enrolled successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))