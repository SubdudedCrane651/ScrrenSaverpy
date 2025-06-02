import tkinter as tk
import time

class Screensaver:
    def __init__(self, timeout_seconds=60):
        self.timeout = timeout_seconds
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")

        # Bind mouse movement and key press events to reset the timer immediately
        self.root.bind("<Motion>", self.reset_timer)
        self.root.bind("<KeyPress>", self.reset_timer)

        self.screensaver_active = False
        self.after_id = None

        self.schedule_screensaver()

    def schedule_screensaver(self):
        """Starts or restarts the timer for the screensaver activation."""
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)  # Cancel the old timer

        self.after_id = self.root.after(self.timeout * 1000, self.fade_to_black)  # Convert seconds to milliseconds

    def fade_to_black(self):
        """Gradually fade the screen to black."""
        self.screensaver_active = True
        self.root.deiconify()
        
        for i in range(0, 101, 5):  # Increase darkness in steps
            alpha = i / 100
            self.root.attributes("-alpha", alpha)
            time.sleep(0.05)  # Adjust for smoother fade

    def reset_timer(self, event=None):
        """Resets the countdown immediately when mouse or keyboard activity is detected."""
        if self.screensaver_active:
            self.root.withdraw()  # Hide screensaver
            self.screensaver_active = False
            self.root.attributes("-alpha", 1)  # Reset transparency

        # Cancel existing timer & restart countdown
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        self.schedule_screensaver()  # Restart countdown

    def run(self):
        """Start screensaver hidden, ensuring multiple activations work."""
        self.root.withdraw()
        self.root.mainloop()

if __name__ == "__main__":
    screensaver = Screensaver(timeout_seconds=60)  # 1-minute idle timeout
    screensaver.run()import tkinter as tk
import time

class Screensaver:
    def __init__(self, timeout_seconds=60):
        self.timeout = timeout_seconds
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")

        # Bind mouse movement and key press events to reset the timer immediately
        self.root.bind("<Motion>", self.reset_timer)
        self.root.bind("<KeyPress>", self.reset_timer)

        self.screensaver_active = False
        self.after_id = None

        self.schedule_screensaver()

    def schedule_screensaver(self):
        """Starts or restarts the timer for the screensaver activation."""
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)  # Cancel the old timer

        self.after_id = self.root.after(self.timeout * 1000, self.fade_to_black)  # Convert seconds to milliseconds

    def fade_to_black(self):
        """Gradually fade the screen to black."""
        self.screensaver_active = True
        self.root.deiconify()
        
        for i in range(0, 101, 5):  # Increase darkness in steps
            alpha = i / 100
            self.root.attributes("-alpha", alpha)
            time.sleep(0.05)  # Adjust for smoother fade

    def reset_timer(self, event=None):
        """Resets the countdown immediately when mouse or keyboard activity is detected."""
        if self.screensaver_active:
            self.root.withdraw()  # Hide screensaver
            self.screensaver_active = False
            self.root.attributes("-alpha", 1)  # Reset transparency

        # Cancel existing timer & restart countdown
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        self.schedule_screensaver()  # Restart countdown

    def run(self):
        """Start screensaver hidden, ensuring multiple activations work."""
        self.root.withdraw()
        self.root.mainloop()

if __name__ == "__main__":
    screensaver = Screensaver(timeout_seconds=60)  # 1-minute idle timeout
    screensaver.run()