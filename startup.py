import sys
from pathlib import Path
import winreg

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "EITS"

def enable_startup():
    try:
        cmd = f"\"{sys.executable}\" \"{Path(sys.argv[0]).resolve()}\""
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def disable_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, VALUE_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def is_startup_enabled():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, VALUE_NAME)
        winreg.CloseKey(key)
        return bool(val)
    except Exception:
        return False
