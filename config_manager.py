import json
import os
from pathlib import Path
from copy import deepcopy

APPDATA = Path(os.getenv("APPDATA") or ".") / "EITS"
CONFIG_PATH = APPDATA / "config.json"

DEFAULT_CONFIG = {
    "default_check_interval_minutes": 360,
    "notify_windows": False,
    "notify_email": False,
    "notify_cooldown_minutes": 240,
    "startup_enabled": False,
    "smtp": {
        "host": "",
        "port": 587,
        "use_tls": True,
        "username": "",
        "password": "",
        "from_addr": "",
        "to_addr": ""
    },
    "tracked_games": []
}

def load_config() -> dict:
    APPDATA.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = deepcopy(DEFAULT_CONFIG)
        save_config(cfg)
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = deepcopy(v)
    for g in cfg["tracked_games"]:
        g.setdefault("discount_percent", 0)
        g.setdefault("last_price", 0.0)
        g.setdefault("check_interval_minutes", cfg["default_check_interval_minutes"])
        g.setdefault("last_checked_iso", None)
        g.setdefault("last_discount_notified_iso", None)
        g.setdefault("currency", "USD")
        g.setdefault("name", "")
        g.setdefault("url", f"https://store.steampowered.com/app/{g.get('app_id','')}/")
    return cfg

def save_config(cfg: dict) -> None:
    APPDATA.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
