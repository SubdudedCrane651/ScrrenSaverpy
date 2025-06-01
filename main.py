import tkinter as tk
import os

class Screensaver:
    def __init__(self, timeout=60000):  # Timeout in milliseconds (1 minute)
        self.timeout = timeout
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")
        self.root.bind("<Motion>", self.quit_screensaver)
        self.root.bind("<KeyPress>", self.quit_screensaver)

        self.root.withdraw()  # Start with the screensaver hidden
        self.schedule_screensaver()  # Start the countdown

    def schedule_screensaver(self):
        """Restart the timer every time screensaver is dismissed."""
        self.root.after(self.timeout, self.show_screensaver)

    def show_screensaver(self):
        self.root.deiconify()

    def quit_screensaver(self, event=None):
        self.root.withdraw()
        self.schedule_screensaver()  # Restart countdown for next activation
        # Uncomment the line below if you want to lock the screen
        # os.system("rundll32.exe user32.dll, LockWorkStation")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    Screensaver(timeout=60000).run()  # 1-minute timeout