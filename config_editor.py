import tkinter as tk
from tkinter import messagebox
import json

CONFIG_FILE = "config.json"

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except Exception:
        config = {"timeout": 1, "use_lock": False}  # Default: 1 minute
    return config

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def submit():
    try:
        timeout_minutes = int(timeout_entry.get())
        use_lock = lock_var.get()
        config = {"timeout": timeout_minutes, "use_lock": use_lock}
        save_config(config)
        messagebox.showinfo("Success", "Configuration saved!")
    except ValueError:
        messagebox.showerror("Error", "Timeout must be a whole number (in minutes)!")

config = load_config()

root = tk.Tk()
root.title("Screensaver Configurator")
root.geometry("400x200")

tk.Label(root, text="Timeout (minutes):").pack(pady=5)
timeout_entry = tk.Entry(root)
timeout_entry.insert(0, str(config.get("timeout", 1)))
timeout_entry.pack(pady=5)

lock_var = tk.BooleanVar(value=config.get("use_lock", False))
tk.Checkbutton(root, text="Go to logon screen on trigger", variable=lock_var).pack(pady=5)

tk.Button(root, text="Save Configuration", command=submit).pack(pady=20)

root.mainloop()