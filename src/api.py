import cv2
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from src.database import AlertDatabase
from src.detector import VisionDetector

app = FastAPI(title="Smart Vision Security API")

db = AlertDatabase()
detector = None

def get_detector():
    global detector
    if detector is None:
        detector = VisionDetector()
    return detector

@app.get("/")
def health_check():
    return {"status": "operational", "system": "Smart Vision Edge Detector"}

@app.get("/alerts")
def get_alerts(limit: int = 10):
    return {"alerts": db.fetch_recent_alerts(limit=limit)}

@app.get("/analytics")
def get_analytics():
    return db.get_threat_analytics()

def generate_frames():
    det = get_detector()
    # cv2.CAP_DSHOW prevents Windows MSMF async frame drops
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    while True:
        success, frame = cap.read()
        if not success:
            break
        
        processed_frame = det.process_frame(frame)
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
               
    cap.release()

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        generate_frames(), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )