# controller.py

import threading

class DarwinController:
    def __init__(self):
        self.idle_flag = True
        self.response_flag = False
        self._lock = threading.Lock()

    def set_idle(self):
        with self._lock:
            self.idle_flag = True
            self.response_flag = False

    def set_response(self):
        with self._lock:
            self.idle_flag = False
            self.response_flag = True

    def is_idle(self):
        with self._lock:
            return self.idle_flag

    def is_response(self):
        with self._lock:
            return self.response_flag
