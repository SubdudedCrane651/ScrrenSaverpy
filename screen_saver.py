import tkinter as tk
import json

class Screensaver:
    def __init__(self, config):
        self.timeout = config.get("timeout", 60000)  # Timeout in milliseconds
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")

        # Bind mouse/keyboard events to exit screensaver
        self.root.bind("<Motion>", self.deactivate_screensaver)
        self.root.bind("<KeyPress>", self.deactivate_screensaver)

        self.screensaver_active = False
        self.after_id = None
        self.schedule_screensaver()

    def schedule_screensaver(self):
        """Resets the timer so it runs repeatedly."""
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)  # Cancel old timer
        self.after_id = self.root.after(self.timeout, self.activate_screensaver)

    def activate_screensaver(self):
        """Triggers the blank screen and ensures repeat activation."""
        if not self.screensaver_active:
            self.root.deiconify()
            self.screensaver_active = True

    def deactivate_screensaver(self, event=None):
        """Hides the screensaver and resets the timer."""
        if self.screensaver_active:
            self.root.withdraw()
            self.screensaver_active = False
            self.schedule_screensaver()  # Restart countdown immediately

    def run(self):
        """Start screensaver hidden, ensuring multiple activations work."""
        self.root.withdraw()
        self.root.mainloop()

def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception:
        config = {"timeout": 60000}  # Default: 1 minute
    config["timeout"] *= 60000 if config["timeout"] < 1000 else 1  # Convert minutes if needed
    return config

if __name__ == "__main__":
    config = load_config()
    screensaver = Screensaver(config)
    screensaver.run()