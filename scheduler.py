import time
from datetime import datetime, timezone
from threading import Event
from config_manager import load_config, save_config
from steam_api import fetch_game_data
from notifications import notify_windows_toast

_stop_event = Event()

def minutes_since(iso: str | None) -> float:
    if not iso:
        return 1e9
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - t).total_seconds() / 60.0
    except Exception:
        return 1e9

def should_check(game: dict, default_interval: int) -> bool:
    interval = int(game.get("check_interval_minutes") or default_interval)
    return minutes_since(game.get("last_checked_iso")) >= interval

def should_notify(game: dict, cooldown: int) -> bool:
    if (game.get("discount_percent") or 0) <= 0:
        return False
    return minutes_since(game.get("last_discount_notified_iso")) >= cooldown

def run_scheduler(tick_seconds: int = 60):
    while not _stop_event.is_set():
        cfg = load_config()
        changed = False
        for g in cfg["tracked_games"]:
            if should_check(g, cfg["default_check_interval_minutes"]):
                data = fetch_game_data(g["app_id"])
                now_iso = datetime.now(timezone.utc).isoformat()
                if data:
                    g["name"] = data["name"]
                    g["currency"] = data["currency"]
                    g["last_price"] = data["price"]
                    g["discount_percent"] = data["discount_percent"]
                    g["last_checked_iso"] = now_iso
                    changed = True
        if changed:
            save_config(cfg)
        cfg = load_config()
        for g in cfg["tracked_games"]:
            if should_notify(g, int(cfg.get("notify_cooldown_minutes") or 240)):
                title = "EITS: Steam discount"
                body = f"{g.get('name','')} is {g.get('discount_percent',0)}% off at {g.get('currency','')} {g.get('last_price',0):.2f}"
                if cfg.get("notify_windows"):
                    notify_windows_toast(title, body)
                g["last_discount_notified_iso"] = datetime.now(timezone.utc).isoformat()
                save_config(cfg)
        time.sleep(tick_seconds)

def stop_scheduler():
    _stop_event.set()
