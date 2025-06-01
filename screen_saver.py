import tkinter as tk
import json
import os

class Screensaver:
    def __init__(self, config):
        self.timeout = config.get("timeout", 60000)  # Timeout in milliseconds
        self.lock_on_activate = config.get("lock_on_activate", False)  # Lock screen option
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")

        # Bind mouse movement and key press events to pause/restart the timer
        self.root.bind("<Motion>", self.pause_timer)
        self.root.bind("<KeyPress>", self.pause_timer)

        self.screensaver_active = False
        self.after_id = None
        self.timer_paused = False  # Track whether the timer is paused

        self.schedule_screensaver()

    def schedule_screensaver(self):
        """Resets the timer so it runs repeatedly."""
        if self.timer_paused:  # If paused, don't restart the timer
            return

        if self.after_id is not None:
            self.root.after_cancel(self.after_id)  # Cancel old timer

        self.after_id = self.root.after(self.timeout, self.activate_screensaver)

    def activate_screensaver(self):
        """Triggers the blank screen and ensures repeat activation."""
        if not self.screensaver_active:
            self.root.deiconify()
            self.screensaver_active = True

            # Lock the screen if the option is enabled
            if self.lock_on_activate:
                os.system("rundll32.exe user32.dll, LockWorkStation")

    def deactivate_screensaver(self, event=None):
        """Hides the screensaver and resets the timer."""
        if self.screensaver_active:
            self.root.withdraw()
            self.screensaver_active = False
            self.schedule_screensaver()  # Restart countdown immediately

    def pause_timer(self, event=None):
        """Pauses the timer when mouse moves or key is pressed, and resumes after idle."""
        self.timer_paused = True
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)  # Cancel pending activation

        # Resume countdown after short idle period
        self.root.after(5000, self.resume_timer)  # Resume countdown after 5 sec of no movement or key press

    def resume_timer(self):
        """Resumes the countdown when the user stops moving the mouse or pressing keys."""
        self.timer_paused = False
        self.schedule_screensaver()

    def run(self):
        """Start screensaver hidden, ensuring multiple activations work."""
        self.root.withdraw()
        self.root.mainloop()

def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception:
        config = {"timeout": 60000, "lock_on_activate": False}  # Default: 1 minute, no lock
    config["timeout"] *= 60000 if config["timeout"] < 1000 else 1  # Convert minutes if needed
    return config

if __name__ == "__main__":
    config = load_config()
    screensaver = Screensaver(config)
    screensaver.run()