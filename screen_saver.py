import ctypes
import time
import os
import tkinter as tk

class Screensaver:
    def __init__(self, timeout_seconds=60):
        self.timeout = timeout_seconds
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")

        self.screensaver_active = False

        self.check_idle_time()

    def get_idle_time(self):
        """Get system idle time using Windows API."""
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        idle_time = (ctypes.windll.kernel32.GetTickCount() - lii.dwTime) // 1000  # Convert to seconds
        return idle_time

    def check_idle_time(self):
        """Continuously check system idle time."""
        while True:
            idle_time = self.get_idle_time()
            if idle_time >= self.timeout and not self.screensaver_active:
                self.activate_screensaver()
            elif idle_time < self.timeout and self.screensaver_active:
                self.deactivate_screensaver()

            time.sleep(1)  # Check every second

    def activate_screensaver(self):
        """Triggers the blank screen when system is idle."""
        self.root.deiconify()
        self.screensaver_active = True

    def deactivate_screensaver(self):
        """Hides the screensaver when system is active."""
        self.root.withdraw()
        self.screensaver_active = False

    def run(self):
        self.root.withdraw()
        self.root.mainloop()

if __name__ == "__main__":
    screensaver = Screensaver(timeout_seconds=60)  # 1-minute idle timeout
    screensaver.run()