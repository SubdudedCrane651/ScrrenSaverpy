import os
import json
import time
import subprocess
import ctypes
from ctypes import wintypes

from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
from comtypes import CLSCTX_ALL
import threading


# ------------------------------------------------------------
# WINDOWS REAL IDLE TIME
# ------------------------------------------------------------

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_uint),
        ('dwTime', ctypes.c_uint),
    ]

def get_system_idle_ms():
    """Return system idle time in ms using GetLastInputInfo."""
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
    return ctypes.windll.kernel32.GetTickCount() - info.dwTime

# ------------------------------------------------------------
# AUDIO DETECTION (PER-SESSION, WORKS FOR YOU)
# ------------------------------------------------------------

def is_audio_playing(threshold=0.01):
    """Detect audio activity across all sessions (muted sessions ignored)."""
    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            try:
                if session.SimpleAudioVolume.GetMute():
                    continue

                meter = session._ctl.QueryInterface(IAudioMeterInformation)
                if meter.GetPeakValue() > threshold:
                    return True
            except:
                continue
    except:
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

    MONPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong,
        ctypes.POINTER(RECT), ctypes.c_double
    )

    ctypes.windll.user32.EnumDisplayMonitors(
        0, 0, MONPROC(callback), 0
    )

    return monitors


# ------------------------------------------------------------
# WINDOW ENUMERATION FOR SCREENSAVER
# ------------------------------------------------------------

def get_windows_for_pid(pid):
    hwnds = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def enum_windows(hwnd, lParam):
        proc_id = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(
            hwnd, ctypes.byref(proc_id)
        )
        if proc_id.value == pid and ctypes.windll.user32.IsWindowVisible(hwnd):
            hwnds.append(hwnd)
        return True

    ctypes.windll.user32.EnumWindows(enum_windows, 0)
    return hwnds


def move_window_to_monitor(hwnd, rect):
    left, top, right, bottom = rect
    ctypes.windll.user32.SetWindowPos(
        hwnd, None,
        left, top,
        right - left, bottom - top,
        0x0040
    )


# ------------------------------------------------------------
# RUN SCREENSAVER
# ------------------------------------------------------------

def run_screensaver_on_monitor(scr_path, rect):
    proc = subprocess.Popen(f'"{scr_path}" /s', shell=True)
    time.sleep(0.7)

    for hwnd in get_windows_for_pid(proc.pid):
        move_window_to_monitor(hwnd, rect)

    return proc


# ------------------------------------------------------------
# FULLSCREEN DETECTION
# ------------------------------------------------------------

def is_fullscreen_active_any_monitor():
    monitors = get_monitors()

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def enum_windows(hwnd, lParam):
        if not ctypes.windll.user32.IsWindowVisible(hwnd):
            return True

        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))

        for ml, mt, mr, mb in monitors:
            if (rect.left <= ml + 5 and rect.top <= mt + 5 and
                rect.right >= mr - 5 and rect.bottom >= mb - 5):
                return False

        return True

    return not ctypes.windll.user32.EnumWindows(enum_windows, 0)
    


# ------------------------------------------------------------
# MAIN CLASS (NO PYNPUT)
# ------------------------------------------------------------

class Screensaver:
    def __init__(self, config):
        t = config.get("timeout", 60000)
        if t < 1000:
            t *= 60000
        self.timeout = t

        self.lock_on_activate = config.get("lock_on_activate", False)
        self.scr_file = os.path.join(
            "C:\\Windows\\System32",
            config.get("screensaver", "Mystify.scr")
        )

        self.screensaver_active = False
        self.screensaver_processes = []

        print(f"Loaded config: timeout={self.timeout}, lock={self.lock_on_activate}")

        # Virtual idle timer
        self.last_activity = time.time()
        threading.Thread(target=self.monitor_screensaver, daemon=True).start()

        self.loop()

    # --------------------------------------------------------

    def register_activity(self, reason):
        self.last_activity = time.time()

    # --------------------------------------------------------

    def loop(self):
        last_bucket = -1

        while True:
            now = time.time()

            audio = is_audio_playing()
            fullscreen = is_fullscreen_active_any_monitor()

            # Treat audio/fullscreen as activity
            if audio or fullscreen:
                self.register_activity("media")

            # Real input automatically updates GetLastInputInfo
            real_idle = get_system_idle_ms()
            if real_idle < 2000:
                self.register_activity("real input")

            virtual_idle = int((now - self.last_activity) * 1000)

            bucket = virtual_idle // 5000
            if bucket != last_bucket:
                last_bucket = bucket
                print(f"Idle={virtual_idle}ms audio={audio} fullscreen={fullscreen}")

            if virtual_idle >= self.timeout and not self.screensaver_active:
                self.activate_screensaver()

            time.sleep(1)

    def monitor_screensaver(self):
        """Check every 2 seconds whether the screensaver processes have exited."""
        while True:
            if self.screensaver_active:
                all_dead = True
                for proc in self.screensaver_processes:
                    try:
                        if proc.poll() is None:  # still running
                            all_dead = False
                            break
                    except:
                        pass

                if all_dead:
                    # Screensaver has fully exited
                    self.screensaver_active = False
                    self.screensaver_processes = []
                    print("Screensaver exited — flag reset")

            time.sleep(2)  # check every 2 seconds            

    # --------------------------------------------------------

    def activate_screensaver(self):
        self.screensaver_active = True
        self.screensaver_processes = []

        for rect in get_monitors():
            proc = run_screensaver_on_monitor(self.scr_file, rect)
            self.screensaver_processes.append(proc)

    # --------------------------------------------------------

    def exit_screensaver(self):
        for proc in self.screensaver_processes:
            try:
                if proc.poll() is None:
                    proc.terminate()
            except:
                pass

        self.screensaver_processes = []
        self.screensaver_active = False

        if self.lock_on_activate:
            os.system("rundll32.exe user32.dll, LockWorkStation")


# ------------------------------------------------------------
# CONFIG LOADING
# ------------------------------------------------------------

def load_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except:
        return {
            "timeout": 60000,
            "lock_on_activate": False,
            "screensaver": "Mystify.scr"
        }


# ------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------

if __name__ == "__main__":
    Screensaver(load_config())