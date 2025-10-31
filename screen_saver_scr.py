import os
import json
import time
import threading
import subprocess
import ctypes
from pynput import mouse, keyboard

class Screensaver:
    def __init__(self, config):
        self.timeout = config.get("timeout", 60000)  # Timeout in milliseconds
        self.lock_on_activate = config.get("lock_on_activate", False)  # Lock screen option
        self.screensaver_file = config.get("screensaver_path", "C:\\Windows\\System32\\Mystify.scr")  # Default screensaver

        self.last_activity_time = time.time()
        self.screensaver_active = False

        # Start activity tracking threads
        threading.Thread(target=self.track_mouse_movement, daemon=True).start()
        threading.Thread(target=self.track_keyboard_input, daemon=True).start()

        # Start activity monitoring
        self.check_activity()

    def check_activity(self):
        """Continuously checks for activity and triggers the screensaver when idle."""
        while True:
            current_time = time.time()
            idle_time = (current_time - self.last_activity_time) * 1000  # Convert to milliseconds

            if idle_time >= self.timeout and not self.screensaver_active:
                self.activate_screensaver()

            time.sleep(1)  # Check every second

    def activate_screensaver(self):
        """Runs the Windows screensaver properly in full screen after restoring the Python window."""
        if not self.screensaver_active:
            print("⏳ Timer expired! Restoring Python window and activating screensaver...")
            
            # Restore minimized Python window
            self.restore_python_window()

            # Run `.scr` exactly as Windows does when you click it
            self.force_hide_cursor()
            command = f'start "" "{self.screensaver_file}" /s'
            self.screensaver_process = subprocess.Popen(command, shell=True)
            self.screensaver_active = True

    def force_hide_cursor(self):
        while ctypes.windll.user32.ShowCursor(False) >= 0:
            pass

    def restore_python_window(self):
        """Finds and restores the minimized Python script window."""
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE (Restores minimized window)
            ctypes.windll.user32.SetForegroundWindow(hwnd)

    def reset_timer(self, event_type):
        print(f"🔄 {event_type} detected! Resetting timer...")
        self.last_activity_time = time.time()

        if self.screensaver_active:
            print("❌ Hiding screensaver due to activity...")
            ctypes.windll.user32.ShowCursor(True)

            self.screensaver_active = False

            # Try to terminate screensaver process
            if self.screensaver_process and self.screensaver_process.poll() is None:
                try:
                    self.screensaver_process.terminate()
                except Exception as e:
                    print(f"⚠️ Failed to terminate screensaver: {e}")

            # Lock screen now
            if self.lock_on_activate:
                self.lock_screen()

    def lock_screen(self):
        """Locks the screen after mouse or keyboard activity."""
        print("🔒 Locking screen due to activity...")
        os.system("rundll32.exe user32.dll, LockWorkStation")

    def track_mouse_movement(self):
        """Listens for system-wide mouse movement."""
        def on_move(x, y):
            self.reset_timer("Mouse movement")

        with mouse.Listener(on_move=on_move) as listener:
            listener.join()

    def track_keyboard_input(self):
        """Listens for system-wide keyboard input."""
        def on_press(key):
            self.reset_timer(f"Key '{key}' pressed")

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        if config["timeout"] < 1000:
            config["timeout"] *= 60000  # Convert minutes to milliseconds
        
        config["lock_on_activate"] = config.get("lock_on_activate", False)    

    except Exception:
        config = {"timeout": 1, "lock_on_activate": False, "screensaver_path": "C:\\Windows\\System32\\VideoScreenSaver.scr"}

    return config

if __name__ == "__main__":
    config = load_config()
    screensaver = Screensaver(config)