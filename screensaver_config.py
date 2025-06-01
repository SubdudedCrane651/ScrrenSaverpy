import tkinter as tk
from tkinter import messagebox
import json
import winreg
import os

CONFIG_FILE = "screensaver_config.json"
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"

def load_config():
    """Load settings from JSON file or use defaults."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except Exception:
        config = {"timeout": 1, "enable_screensaver": True}  # Default: 1 minute, enabled
    return config

def save_config(config):
    """Save configuration to JSON file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def set_windows_screensaver(timeout_minutes, enable_screensaver):
    """Modify Windows registry to set screensaver timeout and activation."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
            timeout_seconds = timeout_minutes * 60  # Convert minutes to seconds
            winreg.SetValueEx(key, "ScreenSaveActive", 0, winreg.REG_SZ, "1" if enable_screensaver else "0")
            winreg.SetValueEx(key, "ScreenSaverTimeout", 0, winreg.REG_SZ, str(timeout_seconds))
        messagebox.showinfo("Success", "Screensaver settings updated!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update registry: {e}")

def submit():
    try:
        timeout_minutes = int(timeout_entry.get())
        enable_screensaver = enable_var.get()
        config = {"timeout": timeout_minutes, "enable_screensaver": enable_screensaver}
        save_config(config)
        set_windows_screensaver(timeout_minutes, enable_screensaver)
    except ValueError:
        messagebox.showerror("Error", "Timeout must be a whole number (in minutes)!")

config = load_config()

root = tk.Tk()
root.title("Windows Screensaver Configurator")
root.geometry("400x200")

tk.Label(root, text="Timeout (minutes):").pack(pady=5)
timeout_entry = tk.Entry(root)
timeout_entry.insert(0, str(config.get("timeout", 1)))
timeout_entry.pack(pady=5)

enable_var = tk.BooleanVar(value=config.get("enable_screensaver", True))
tk.Checkbutton(root, text="Enable Screensaver", variable=enable_var).pack(pady=5)

tk.Button(root, text="Save Configuration", command=submit).pack(pady=20)

root.mainloop()