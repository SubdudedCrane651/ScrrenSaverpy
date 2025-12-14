import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
import json
import glob
import os
import subprocess

CONFIG_FILE = "config.json"
SYSTEM32 = os.path.join(os.environ["WINDIR"], "System32")

# -------------------------------
# Utility functions
# -------------------------------
def list_screensavers():
    """Return list of .scr files in System32."""
    return [os.path.basename(f) for f in glob.glob(os.path.join(SYSTEM32, "*.scr"))]

def load_config():
    """Load config.json or return defaults."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except Exception:
        config = {"timeout": 1, "lock_on_activate": False, "screensaver": None}
    return config

def save_config(config):
    """Save config.json with pretty formatting."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# -------------------------------
# Tkinter callbacks
# -------------------------------
def submit():
    """Save user selections to config.json."""
    try:
        timeout_minutes = int(timeout_entry.get())
        use_lock = lock_var.get()
        chosen_saver = screensaver_var.get()

        config = {
            "timeout": timeout_minutes,
            "lock_on_activate": use_lock,
            "screensaver": chosen_saver
        }
        save_config(config)
        messagebox.showinfo("Success", "Configuration saved!")
    except ValueError:
        messagebox.showerror("Error", "Timeout must be a whole number (in minutes)!")

def preview_screensaver():
    """Run the chosen screensaver immediately (preview)."""
    chosen_saver = screensaver_var.get()
    if chosen_saver:
        saver_path = os.path.join(SYSTEM32, chosen_saver)
        try:
            subprocess.Popen([saver_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not launch screensaver:\n{e}")

# -------------------------------
# Tkinter UI setup
# -------------------------------
config = load_config()
screensavers = list_screensavers()

root = tk.Tk()
root.title("Screensaver Configurator")
root.geometry("400x250")

# Timeout
tk.Label(root, text="Timeout (minutes):").pack(pady=5)
timeout_entry = tk.Entry(root)
timeout_entry.insert(0, str(config.get("timeout", 1)))
timeout_entry.pack(pady=5)

# Lock option
lock_var = tk.BooleanVar(value=config.get("lock_on_activate", False))
tk.Checkbutton(root, text="Go to logon screen on trigger", variable=lock_var).pack(pady=5)

# Screensaver dropdown
tk.Label(root, text="Choose Screensaver:").pack(pady=5)
screensaver_var = tk.StringVar(value=config.get("screensaver", screensavers[0] if screensavers else ""))
screensaver_combo = ttk.Combobox(root, textvariable=screensaver_var, values=screensavers, state="readonly")
screensaver_combo.pack(pady=5)

# Buttons
tk.Button(root, text="Save Configuration", command=submit).pack(pady=10)
tk.Button(root, text="Preview Screensaver", command=preview_screensaver).pack(pady=5)

root.mainloop()