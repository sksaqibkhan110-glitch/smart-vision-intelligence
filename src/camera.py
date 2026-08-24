import cv2
import threading
import time

class VideoCamera:
    def __init__(self):
        # Direct capture initialization
        self.cap = cv2.VideoCapture(0)
        self.ret = False
        self.frame = None
        self.running = True
        self.lock = threading.Lock()
        
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None and frame.size > 0:
                    with self.lock:
                        self.ret = ret
                        self.frame = frame.copy()
                else:
                    time.sleep(0.05)
            time.sleep(0.01)

    def get_frame(self):
        with self.lock:
            if self.ret and self.frame is not None:
                return True, self.frame.copy()
            return False, None

    def release(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()

camera_instance = None

def get_camera():
    global camera_instance
    if camera_instance is None:
        camera_instance = VideoCamera()
    return camera_instance