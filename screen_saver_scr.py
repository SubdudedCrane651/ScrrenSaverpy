import os
import json
import time
import threading
import subprocess
import ctypes
from ctypes import wintypes
from pynput import mouse, keyboard


# ------------------------------------------------------------
# ENUMERATE MONITORS
# ------------------------------------------------------------

def get_monitors():
    """Returns a list of monitor rectangles: (left, top, right, bottom)."""
    monitors = []

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
        r = lprcMonitor.contents
        monitors.append((r.left, r.top, r.right, r.bottom))
        return True

    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(RECT),
        ctypes.c_double
    )

    ctypes.windll.user32.EnumDisplayMonitors(
        0, 0, MONITORENUMPROC(callback), 0
    )

    return monitors


# ------------------------------------------------------------
# ENUMERATE WINDOWS FOR A PROCESS
# ------------------------------------------------------------

def get_windows_for_pid(pid):
    hwnds = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def enum_windows(hwnd, lParam):
        proc_id = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))

        if proc_id.value == pid and ctypes.windll.user32.IsWindowVisible(hwnd):
            hwnds.append(hwnd)

        return True

    ctypes.windll.user32.EnumWindows(enum_windows, 0)
    return hwnds


# ------------------------------------------------------------
# MOVE WINDOW TO MONITOR
# ------------------------------------------------------------

def move_window_to_monitor(hwnd, rect):
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top

    ctypes.windll.user32.SetWindowPos(
        hwnd, None,
        left, top, width, height,
        0x0040  # SWP_NOZORDER
    )


# ------------------------------------------------------------
# RUN SCREENSAVER ON SPECIFIC MONITOR
# ------------------------------------------------------------

def run_screensaver_on_monitor(scr_path, monitor_rect):
    proc = subprocess.Popen(f'"{scr_path}" /s', shell=True)

    # Give it time to create windows
    time.sleep(0.7)

    hwnds = get_windows_for_pid(proc.pid)

    for hwnd in hwnds:
        move_window_to_monitor(hwnd, monitor_rect)

    return proc


# ------------------------------------------------------------
# MAIN CLASS
# ------------------------------------------------------------

class Screensaver:
    def __init__(self, config):
        self.timeout = config.get("timeout", 60000)
        self.lock_on_activate = config.get("lock_on_activate", False)
        self.screensaver_file = "C:\\Windows\\System32\\" + config.get("screensaver", "Mystify.scr")

        self.last_activity_time = time.time()
        self.screensaver_active = False
        self.screensaver_processes = []

        # Start listeners
        threading.Thread(target=self.track_mouse_movement, daemon=True).start()
        threading.Thread(target=self.track_keyboard_input, daemon=True).start()

        # Start activity loop
        self.check_activity()

    # --------------------------------------------------------

    def check_activity(self):
        while True:
            idle_ms = (time.time() - self.last_activity_time) * 1000

            if idle_ms >= self.timeout and not self.screensaver_active:
                self.activate_screensaver()

            time.sleep(1)

    # --------------------------------------------------------

    def activate_screensaver(self):
        if self.screensaver_active:
            return

        print("⏳ Activating screensaver on all monitors...")

        self.restore_python_window()
        self.force_hide_cursor()

        monitors = get_monitors()
        self.screensaver_processes = []

        for mon in monitors:
            proc = run_screensaver_on_monitor(self.screensaver_file, mon)
            self.screensaver_processes.append(proc)

        self.screensaver_active = True

    # --------------------------------------------------------

    def force_hide_cursor(self):
        while ctypes.windll.user32.ShowCursor(False) >= 0:
            pass

    # --------------------------------------------------------

    def restore_python_window(self):
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)
            ctypes.windll.user32.SetForegroundWindow(hwnd)

    # --------------------------------------------------------

    def reset_timer(self, event_type):
        # Ignore popup focus changes
        foreground = ctypes.windll.user32.GetForegroundWindow()
        console = ctypes.windll.kernel32.GetConsoleWindow()

        if foreground != console and not self.screensaver_active:
            return

        print(f"🔄 {event_type} detected! Resetting timer...")
        self.last_activity_time = time.time()

        if self.screensaver_active:
            print("❌ Hiding screensaver due to activity...")
            ctypes.windll.user32.ShowCursor(True)

            for proc in self.screensaver_processes:
                try:
                    if proc.poll() is None:
                        proc.terminate()
                except Exception as e:
                    print(f"⚠️ Failed to terminate screensaver: {e}")

            self.screensaver_processes = []
            self.screensaver_active = False

            if self.lock_on_activate:
                self.lock_screen()

    # --------------------------------------------------------

    def lock_screen(self):
        print("🔒 Locking screen due to activity...")
        os.system("rundll32.exe user32.dll, LockWorkStation")

    # --------------------------------------------------------

    def track_mouse_movement(self):
        last_pos = [None, None]

        def on_move(x, y):
            if last_pos[0] is None:
                last_pos[0], last_pos[1] = x, y
                return

            # Only count REAL movement
            if abs(x - last_pos[0]) > 1 or abs(y - last_pos[1]) > 1:
                last_pos[0], last_pos[1] = x, y
                self.reset_timer("Mouse movement")

        with mouse.Listener(on_move=on_move) as listener:
            listener.join()

    # --------------------------------------------------------

    def track_keyboard_input(self):
        def on_press(key):
            # Ignore modifier-only events
            if key in {
                keyboard.Key.shift, keyboard.Key.shift_r,
                keyboard.Key.ctrl, keyboard.Key.ctrl_r,
                keyboard.Key.alt, keyboard.Key.alt_r,
                keyboard.Key.cmd, keyboard.Key.cmd_r
            }:
                return

            self.reset_timer(f"Key '{key}' pressed")

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()


# ------------------------------------------------------------
# CONFIG LOADING
# ------------------------------------------------------------

def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        if config["timeout"] < 1000:
            config["timeout"] *= 60000

        config["lock_on_activate"] = config.get("lock_on_activate", False)
        config["screensaver"] = config.get("screensaver", "Mystify.scr")

    except Exception:
        config = {
            "timeout": 60000,
            "lock_on_activate": False,
            "screensaver": "Mystify.scr"
        }

    return config


# ------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------

if __name__ == "__main__":
    config = load_config()
    Screensaver(config)