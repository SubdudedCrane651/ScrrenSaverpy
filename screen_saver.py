import tkinter as tk
import json
import os
import time
import pyautogui
import threading
from pynput import keyboard

class Screensaver:
    def __init__(self, config):
        self.timeout = config.get("timeout", 60000)  # milliseconds
        self.lock_on_activate = config.get("lock_on_activate", False)
        self.last_activity_time = time.time()

        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")
        self.root.withdraw()  # Start hidden

        self.screensaver_active = False

        # Bind direct input events
        self.root.bind_all("<Motion>", lambda e: self.reset_timer(event=e, source="Tkinter Mouse"))
        self.root.bind_all("<Key>", lambda e: self.reset_timer(event=e, source="Tkinter Key"))

        # Start tracking
        threading.Thread(target=self.track_mouse_movement, daemon=True).start()
        threading.Thread(target=self.track_keyboard_input, daemon=True).start()

        # Start screensaver timer
        self.check_inactivity()

    def check_inactivity(self):
        elapsed = time.time() - self.last_activity_time
        if not self.screensaver_active and elapsed >= self.timeout / 1000:
            print("⏳ No activity detected. Activating screensaver...")
            self.activate_screensaver()
        self.root.after(100, self.check_inactivity)  # Check every 100ms

    def activate_screensaver(self):
        self.screensaver_active = True
        self.root.config(cursor="none")
        self.root.deiconify()

    def reset_timer(self, event=None, source="Unknown"):
        print(f"🔄 Activity detected from {source}! Resetting timer...")
        self.last_activity_time = time.time()

        if self.screensaver_active:
            print("❌ Hiding screensaver due to activity...")
            self.root.withdraw()
            self.root.config(cursor="arrow")
            self.screensaver_active = False
            if self.lock_on_activate:
                self.lock_screen()

    def lock_screen(self):
        print("🔒 Locking screen due to activity...")
        os.system("rundll32.exe user32.dll, LockWorkStation")

    def track_mouse_movement(self):
        last_mouse_pos = pyautogui.position()
        while True:
            time.sleep(0.1)
            current_mouse_pos = pyautogui.position()
            if current_mouse_pos != last_mouse_pos:
                self.reset_timer(source="Mouse")
                last_mouse_pos = current_mouse_pos

    def track_keyboard_input(self):
        def on_press(key):
            self.reset_timer(source="Keyboard")
        listener = keyboard.Listener(on_press=on_press)
        listener.start()

    def run(self):
        self.root.mainloop()

def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception:
        config = {"timeout": 1, "lock_on_activate": False}

    # Convert minutes to milliseconds
    config["timeout"] = max(config.get("timeout", 1), 1) * 60 * 1000
    return config

if __name__ == "__main__":
    config = load_config()
    screensaver = Screensaver(config)
    screensaver.run()