import os
import json
import time
import threading
import subprocess
import ctypes
from ctypes import wintypes

from pynput import mouse, keyboard

from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
from comtypes import CLSCTX_ALL


# ------------------------------------------------------------
# AUDIO DETECTION (PER-SESSION, WHAT WORKED FOR YOU)
# ------------------------------------------------------------

def is_audio_playing(threshold=0.01):
    """
    Returns True if any audio session is outputting sound above threshold.
    Muted sessions do NOT count (Option B).
    """
    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            try:
                if session.SimpleAudioVolume.GetMute():
                    continue

                meter = session._ctl.QueryInterface(IAudioMeterInformation)
                peak = meter.GetPeakValue()  # 0.0–1.0

                if peak > threshold:
                    return True

            except Exception:
                continue
    except Exception:
        return False

    return False


# ------------------------------------------------------------
# MONITOR ENUMERATION
# ------------------------------------------------------------

def get_monitors():
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
    """
    Launches the .scr as a normal process and moves its windows
    to the given monitor rectangle.
    """
    proc = subprocess.Popen(f'"{scr_path}" /s', shell=True)

    time.sleep(0.7)

    hwnds = get_windows_for_pid(proc.pid)
    for hwnd in hwnds:
        move_window_to_monitor(hwnd, monitor_rect)

    return proc


# ------------------------------------------------------------
# OPTIONAL FULLSCREEN DETECTION (SECONDARY LAYER)
# ------------------------------------------------------------

def is_fullscreen_active_any_monitor():
    """
    Returns True if ANY visible window appears fullscreen on ANY monitor.
    If this isn’t reliable for you, you can just have this always return False.
    """
    monitors = get_monitors()

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def enum_windows(hwnd, lParam):
        if not ctypes.windll.user32.IsWindowVisible(hwnd):
            return True

        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))

        win_left, win_top, win_right, win_bottom = (
            rect.left, rect.top, rect.right, rect.bottom
        )

        for mon_left, mon_top, mon_right, mon_bottom in monitors:
            if (win_left <= mon_left + 5 and
                win_top <= mon_top + 5 and
                win_right >= mon_right - 5 and
                win_bottom >= mon_bottom - 5):
                return False

        return True

    result = ctypes.windll.user32.EnumWindows(enum_windows, 0)
    return not result


# ------------------------------------------------------------
# MAIN CLASS WITH VIRTUAL IDLE TIMER
# ------------------------------------------------------------

class Screensaver:
    def __init__(self, config):
        # timeout is in ms; if user gave tiny value, treat as minutes
        t = config.get("timeout", 60000)
        if t < 1000:
            t *= 60000
        self.timeout = t

        self.lock_on_activate = config.get("lock_on_activate", False)
        self.screensaver_file = os.path.join(
            "C:\\Windows\\System32",
            config.get("screensaver", "Mystify.scr")
        )

        # Virtual idle timer based on "last activity"
        # Activity = mouse/keyboard OR audio/fullscreen
        self.last_activity_time = time.time()

        self.screensaver_active = False
        self.screensaver_processes = []

        print(f"Config loaded: timeout={self.timeout} ms, "
              f"lock_on_activate={self.lock_on_activate}, "
              f"screensaver={self.screensaver_file}")

        threading.Thread(target=self.track_mouse_movement, daemon=True).start()
        threading.Thread(target=self.track_keyboard_input, daemon=True).start()

        self.check_activity()

    # --------------------------------------------------------

    def register_activity(self, reason):
        self.last_activity_time = time.time()
        # Uncomment for debug:
        # print(f"[ACTIVITY] {reason} at {self.last_activity_time}")

    # --------------------------------------------------------

    def check_activity(self):
        last_logged_bucket = -1

        while True:
            now = time.time()
            audio = is_audio_playing()
            fullscreen = is_fullscreen_active_any_monitor()

            # While audio/fullscreen are active, we treat it as activity:
            if audio or fullscreen:
                self.register_activity("Audio or fullscreen")

            virtual_idle_ms = int((now - self.last_activity_time) * 1000)

            bucket = int(virtual_idle_ms / 5000)
            if bucket != last_logged_bucket:
                last_logged_bucket = bucket
                print(f"VirtualIdle={virtual_idle_ms} ms, "
                      f"audio={audio}, fullscreen={fullscreen}")

            if virtual_idle_ms >= self.timeout and not self.screensaver_active:
                print("Virtual idle timeout reached, activating screensaver...")
                self.activate_screensaver()

            time.sleep(1)

    # --------------------------------------------------------

    def activate_screensaver(self):
        if self.screensaver_active:
            return

        monitors = get_monitors()
        print(f"Activating screensaver on monitors: {monitors}")
        self.screensaver_processes = []

        for mon in monitors:
            proc = run_screensaver_on_monitor(self.screensaver_file, mon)
            self.screensaver_processes.append(proc)
            print(f"Started screensaver PID={proc.pid} on monitor {mon}")

        self.screensaver_active = True

    # --------------------------------------------------------

    def reset_screensaver_if_active(self, reason):
        # Any real input counts as activity
        self.register_activity(reason)

        if not self.screensaver_active:
            return

        print(f"{reason} → exiting screensaver")

        for proc in self.screensaver_processes:
            try:
                if proc.poll() is None:
                    proc.terminate()
            except Exception:
                pass

        self.screensaver_processes = []
        self.screensaver_active = False

        if self.lock_on_activate:
            os.system("rundll32.exe user32.dll, LockWorkStation")

    # --------------------------------------------------------

    def track_mouse_movement(self):
        last_pos = [None, None]

        def on_move(x, y):
            if last_pos[0] is None:
                last_pos[0], last_pos[1] = x, y
                return

            if (x, y) != (last_pos[0], last_pos[1]):
                last_pos[0], last_pos[1] = x, y
                self.reset_screensaver_if_active("Mouse movement")

        with mouse.Listener(on_move=on_move) as listener:
            listener.join()

    # --------------------------------------------------------

    def track_keyboard_input(self):
        def on_press(key):
            self.reset_screensaver_if_active(f"Key {key} pressed")

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()


# ------------------------------------------------------------
# CONFIG LOADING
# ------------------------------------------------------------

def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        config.setdefault("timeout", 60000)
        config.setdefault("lock_on_activate", False)
        config.setdefault("screensaver", "Mystify.scr")
    except Exception as e:
        print(f"Failed to load config ({e}), using defaults.")
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