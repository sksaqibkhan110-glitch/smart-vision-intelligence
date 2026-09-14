import cv2
import threading
import time

class CameraStream:
    def __init__(self, src=0):
        self.src = src
        self.cap = cv2.VideoCapture(self.src)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.ret, self.frame = self.cap.read()
        self.running = True
        self.lock = threading.Lock()
        
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.ret = ret
                        self.frame = frame
                else:
                    time.sleep(0.02)
            else:
                time.sleep(0.05)

    def get_frame(self):
        with self.lock:
            if self.frame is not None:
                return self.ret, self.frame.copy()
            return False, None

    def switch_source(self, new_src):
        with self.lock:
            self.running = False
        if self.cap.isOpened():
            self.cap.release()
        
        self.src = new_src
        self.cap = cv2.VideoCapture(self.src)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def release(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()

_camera_instance = None

def get_camera(src=0):
    global _camera_instance
    if _camera_instance is None:
        _camera_instance = CameraStream(src=src)
    return _camera_instance