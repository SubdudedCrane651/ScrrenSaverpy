import os

def activate_screensaver():
    """Manually trigger the Windows screensaver."""
    #os.system("rundll32.exe user32.dll, ScreenSaverProc")
    #os.system("rundll32.exe user32.dll, LockWorkStation")
    os.system(r"C:\Windows\System32\VideoScreenSaver.scr")

if __name__ == "__main__":
    activate_screensaver()