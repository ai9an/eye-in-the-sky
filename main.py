import threading
from gui_manager import SteamPriceTrackerGUI
from scheduler import run_scheduler
import os
import sys
import shutil
import json
import ctypes
from time import sleep

APP_NAME = "EyeInTheSky"
INSTALL_DIR = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "EyeInTheSky")
INSTALL_EXE = os.path.join(INSTALL_DIR, f"{APP_NAME}.exe")
APPDATA_DIR = os.path.join(os.environ['APPDATA'], APP_NAME)
CONFIG_FILE = os.path.join(APPDATA_DIR, "config.json")
DESKTOP_SHORTCUT = os.path.join(os.path.join(os.environ['USERPROFILE'], 'Desktop'), f"{APP_NAME}.lnk")
ICON_FILE = INSTALL_EXE  # Using the exe itself as icon

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def ensure_config():
    os.makedirs(APPDATA_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        default_config = {"example_setting": True}
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f)

def create_shortcut():
    try:
        from win32com.client import Dispatch
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(DESKTOP_SHORTCUT)
        shortcut.Targetpath = INSTALL_EXE
        shortcut.WorkingDirectory = INSTALL_DIR
        shortcut.IconLocation = ICON_FILE
        shortcut.save()
    except Exception as e:
        print("Could not create shortcut:", e)

def install_and_restart():
    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR, exist_ok=True)
    # Copy the executable
    shutil.copy(sys.executable, INSTALL_EXE)
    # Create shortcut
    create_shortcut()
    # Relaunch from install location
    os.startfile(INSTALL_EXE)
    sys.exit()
if sys.executable != INSTALL_EXE:
    if not is_admin():
        # Relaunch as admin
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, "", None, 1)
        sys.exit()
    install_and_restart()

# ------------------ ENSURE CONFIG ------------------
ensure_config()

# ------------------ LOAD CONFIG ------------------
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

# ------------------ YOUR APP STARTS HERE ------------------
print("App running from install location. Config loaded:", config)

def main():
    # Run scheduler in the background
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()

    # Launch GUI
    app = SteamPriceTrackerGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
