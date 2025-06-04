import tkinter as tk
import json
import os
import time
import pyautogui
from pynput import keyboard

class Screensaver:
    def __init__(self, config):
        self.timeout = config.get("timeout", 60000)  # Timeout in milliseconds
        self.lock_on_activate = config.get("lock_on_activate", False)  # Lock screen option
        self.last_activity_time = time.time()  # Track last activity time
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")

        self.screensaver_active = False
        self.root.withdraw()  # Start hidden

        self.after_id = None  # Track scheduled timer
        self.schedule_screensaver()

    def schedule_screensaver(self):
        """Starts a fresh timer for screensaver activation."""
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)  # Cancel previous timer

        self.after_id = self.root.after(self.timeout, self.activate_screensaver)  # Start new countdown

    def activate_screensaver(self):
        """Triggers the screensaver when timeout expires."""
        if not self.screensaver_active:
            print("⏳ Timer expired! Activating screensaver...")
            self.screensaver_active = True
            self.root.deiconify()

            if self.lock_on_activate:
                os.system("rundll32.exe user32.dll, LockWorkStation")

    def reset_timer(self, event=None):
        """Stops screensaver and fully resets idle timer on user activity."""
        print("🔄 Activity detected! Resetting timer...")

        self.last_activity_time = time.time()  # Reset idle tracker

        if self.screensaver_active:
            print("❌ Hiding screensaver due to activity...")
            self.root.withdraw()  # Hide screensaver
            self.screensaver_active = False  # Mark as inactive

        # Ensure timer restarts from scratch
        self.schedule_screensaver()

    def track_mouse_movement(self):
        """Continuously checks for system-wide mouse movement."""
        last_mouse_pos = pyautogui.position()
        
        while True:
            time.sleep(1)  # Check every second
            current_mouse_pos = pyautogui.position()

            if current_mouse_pos != last_mouse_pos:  # Detect movement
                self.reset_timer()
                print("🖱 Mouse movement detected! Resetting timer...")
                last_mouse_pos = current_mouse_pos  # Update last position

    def track_keyboard_input(self):
        """Listens for system-wide keyboard input to reset the timer."""
        def on_press(key):
            print(f"⌨️ Key '{key}' pressed! Resetting timer...")
            self.reset_timer()

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def run(self):
        """Keeps the screensaver running & tracks mouse + keyboard input properly."""
        import threading
        threading.Thread(target=self.track_mouse_movement, daemon=True).start()
        threading.Thread(target=self.track_keyboard_input, daemon=True).start()
        self.root.mainloop()

def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception:
        config = {"timeout": 1, "lock_on_activate": False}  # Default: 1 minute

    if config["timeout"] < 1000:
        config["timeout"] *= 60000  # Convert minutes to milliseconds

    return config

if __name__ == "__main__":
    config = load_config()
    screensaver = Screensaver(config)
    screensaver.run()