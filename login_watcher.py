import time
import win32gui
import subprocess

def wait_for_unlock():
    """Continuously monitor login status and restart the screensaver after unlocking."""
    while True:
        time.sleep(2)  # Short pause before checking again
        hwnd = win32gui.GetForegroundWindow()
        if hwnd == win32gui.GetDesktopWindow():
            subprocess.Popen(["python", "screensaver.py"])  # Restart screensaver
            time.sleep(10)  # Give time for reset before looping again

if __name__ == "__main__":
    wait_for_unlock()