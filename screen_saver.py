import tkinter as tk
import os
import json
import subprocess

class Screensaver:
    def __init__(self, config):
        self.timeout = config.get("timeout", 60000)  # Timeout in milliseconds
        self.use_lock = config.get("use_lock", False)  # Lock screen trigger option
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")
        
        self.root.bind("<Motion>", self.reset_timer)
        self.root.bind("<KeyPress>", self.reset_timer)

        self.screensaver_active = False
        self.after_id = None
        self.schedule_screensaver()  # Start the countdown

    def schedule_screensaver(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        self.after_id = self.root.after(self.timeout, self.activate_screensaver)

    def activate_screensaver(self):
        if not self.screensaver_active:
            self.root.deiconify()  # Show the full-screen window
            self.screensaver_active = True
            
            if self.use_lock:
                self.go_to_logon()

    def go_to_logon(self):
        """Lock the screen and start background watcher."""
        os.system("rundll32.exe user32.dll, LockWorkStation")
        subprocess.Popen(["python", "login_watcher.py"])
        self.root.withdraw()

    def reset_timer(self, event=None):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if self.screensaver_active:
            self.root.withdraw()
            self.screensaver_active = False
        else:
            self.schedule_screensaver()

    def run(self):
        self.root.withdraw()
        self.root.mainloop()

def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception:
        config = {"timeout": 1, "use_lock": False}  # Default: 1 minute
    config["timeout"] *= 60000  # Convert minutes to milliseconds
    return config

if __name__ == "__main__":
    config = load_config()
    screensaver = Screensaver(config)
    screensaver.run()