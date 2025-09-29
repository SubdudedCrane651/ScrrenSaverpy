import tkinter as tk
import json
import os
import time
import pyautogui
import threading
from pynput import keyboard

class Screensaver:
    def __init__(self, config):
        self.timeout = config.get("timeout", 60000)
        self.lock_on_activate = config.get("lock_on_activate", False)
        self.last_activity_time = time.time()

        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")
        self.root.withdraw()  # Start hidden

        self.screensaver_active = False
        self.after_id = None

        # Start tracking
        threading.Thread(target=self.track_mouse_movement, daemon=True).start()
        threading.Thread(target=self.track_keyboard_input, daemon=True).start()

        # Start screensaver timer
        self.check_inactivity()
        
    def check_inactivity(self):
        if not self.screensaver_active:
            elapsed = time.time() - self.last_activity_time
            if elapsed >= self.timeout / 1000:
                print("⏳ No activity detected. Activating screensaver...")
                self.screensaver_active = True
                self.root.config(cursor="none")
                self.root.deiconify()
        self.root.after(1000, self.check_inactivity)        

    def schedule_screensaver(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)

        self.after_id = self.root.after(self.timeout, self.activate_screensaver)

    def activate_screensaver(self):
        if not self.screensaver_active:
            print("⏳ Timer expired! Activating screensaver...")
            self.screensaver_active = True
            self.root.config(cursor="none")  # Hide mouse pointer
            self.root.deiconify()

    def reset_timer(self, event=None):
        print("🔄 Activity detected! Resetting timer...")
        self.last_activity_time = time.time()
        self.root.config(cursor="arrow")  # Restore mouse pointer
        self.root.withdraw()

        if self.screensaver_active:
            print("❌ Hiding screensaver due to activity...")
            self.root.withdraw()
            self.screensaver_active = False

            if self.lock_on_activate:
                self.lock_screen()

        self.schedule_screensaver()

    def lock_screen(self):
        print("🔒 Locking screen due to activity...")
        os.system("rundll32.exe user32.dll, LockWorkStation")

    def track_mouse_movement(self):
        last_mouse_pos = pyautogui.position()

        while True:
            time.sleep(1)
            current_mouse_pos = pyautogui.position()

            if current_mouse_pos != last_mouse_pos:
                print("🖱 Mouse movement detected!")
                self.reset_timer()
                last_mouse_pos = current_mouse_pos

    def track_keyboard_input(self):
        def on_press(key):
            print(f"⌨️ Key '{key}' pressed!")
            self.reset_timer()

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def run(self):
        self.root.mainloop()

def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception:
        config = {"timeout": 1, "lock_on_activate": False}

    if config["timeout"] < 1000:
        config["timeout"] *= 60000

    return config

if __name__ == "__main__":
    config = load_config()
    screensaver = Screensaver(config)
    screensaver.run()