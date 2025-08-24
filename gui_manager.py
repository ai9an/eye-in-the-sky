import customtkinter as ctk
from tkinter import messagebox
from url_parser import extract_app_id
from steam_api import fetch_game_data
from config_manager import load_config, save_config
from startup import enable_startup, disable_startup
from notifications import notify_windows_toast
import pystray
from PIL import Image, ImageDraw
import threading

PRIMARY_BG = "#2e1e12"
SURFACE_BG = "#3b2819"
PRIMARY_ORANGE = "#e95420"
SECONDARY_ORANGE = "#ffa64d"
TEXT_COLOR = "#f4e3d7"

class SteamPriceTrackerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("Eye in the Sky (EITS)")
        self.configure(fg_color=PRIMARY_BG)
        self.geometry("560x520")
        self.minsize(560, 520)
        self.config_data = load_config()

        # Close-to-tray behavior
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.tray_icon = None
        self.create_tray_icon()

        # URL entry
        self.url_entry = ctk.CTkEntry(
            self, placeholder_text="Paste Steam URL",
            fg_color=SURFACE_BG, text_color=TEXT_COLOR
        )
        self.url_entry.pack(pady=8, padx=10, fill="x")

        # Top buttons bar
        self.top_bar = ctk.CTkFrame(self, fg_color=PRIMARY_BG)
        self.top_bar.pack(padx=10, fill="x")

        self.add_btn = ctk.CTkButton(
            self.top_bar, text="Add Game",
            fg_color=PRIMARY_ORANGE, hover_color=SECONDARY_ORANGE,
            text_color=TEXT_COLOR, command=self.add_game
        )
        self.add_btn.pack(side="left", padx=4, pady=6)

        self.refresh_btn = ctk.CTkButton(
            self.top_bar, text="Refresh",
            fg_color=PRIMARY_ORANGE, hover_color=SECONDARY_ORANGE,
            text_color=TEXT_COLOR, command=self.manual_refresh
        )
        self.refresh_btn.pack(side="left", padx=4, pady=6)

        self.settings_btn = ctk.CTkButton(
            self.top_bar, text="Settings", width=80,
            fg_color=SURFACE_BG, hover_color="#5a3a24",
            text_color=TEXT_COLOR, command=self.open_settings
        )
        self.settings_btn.pack(side="right", padx=4, pady=6)

        # Scrollable list for tracked games
        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color=SURFACE_BG, width=520, height=360
        )
        self.list_frame.pack(padx=10, pady=8, fill="both", expand=True)

        # Status label
        self.status = ctk.CTkLabel(self, text="", text_color=TEXT_COLOR)
        self.status.pack(pady=4)

        self.refresh_ui()
        self.after(60000, self.auto_refresh)

    def add_game(self):
        url = self.url_entry.get().strip()
        app_id = extract_app_id(url)
        if not app_id:
            messagebox.showerror("Error", "Could not parse Steam URL.")
            return
        existing = [g for g in self.config_data["tracked_games"] if g.get("app_id") == app_id]
        if existing:
            messagebox.showinfo("Info", "Game is already tracked.")
            return
        data = fetch_game_data(app_id)
        if not data:
            messagebox.showerror("Error", "Failed to fetch game data.")
            return
        entry = {
            "app_id": app_id,
            "url": url,
            "name": data["name"],
            "last_price": data["price"],
            "discount_percent": data["discount_percent"],
            "check_interval_minutes": self.config_data["default_check_interval_minutes"],
            "last_checked_iso": None,
            "last_discount_notified_iso": None,
            "currency": data.get("currency") or "USD"
        }
        self.config_data["tracked_games"].append(entry)
        save_config(self.config_data)
        self.url_entry.delete(0, "end")
        self.refresh_ui()

    def remove_game(self, app_id: str):
        self.config_data["tracked_games"] = [
            g for g in self.config_data["tracked_games"] if g.get("app_id") != app_id
        ]
        save_config(self.config_data)
        self.refresh_ui()

    def manual_refresh(self):
        self.config_data = load_config()
        self.refresh_ui()

    def auto_refresh(self):
        self.manual_refresh()
        self.after(60000, self.auto_refresh)

    def refresh_ui(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        games = list(self.config_data.get("tracked_games", []))
        games.sort(key=lambda x: x.get("name","").lower())
        for g in games:
            row = ctk.CTkFrame(self.list_frame, fg_color=PRIMARY_BG)
            row.pack(fill="x", padx=6, pady=4)
            name = g.get("name","")
            price = g.get("last_price", 0.0)
            disc = g.get("discount_percent", 0)
            curr = g.get("currency","USD")
            txt = f"{name}   {curr} {price:.2f}   -{disc}%"
            lbl = ctk.CTkLabel(row, text=txt, text_color=TEXT_COLOR)
            lbl.pack(side="left", padx=8, pady=8)
            del_btn = ctk.CTkButton(
                row, text="🗑", width=36,
                fg_color=PRIMARY_ORANGE, hover_color=SECONDARY_ORANGE,
                text_color=TEXT_COLOR,
                command=lambda a=g.get('app_id'): self.remove_game(a)
            )
            del_btn.pack(side="right", padx=6, pady=6)
        self.status.configure(text=f"Tracked: {len(games)}")

    def open_settings(self):
        win = ctk.CTkToplevel(self)
        win.transient(self)
        win.grab_set()
        self.lift()
        self.focus_force()
        win.geometry("400x280")
        win.title("EITS Settings")
        win.configure(fg_color=PRIMARY_BG)
        cfg = self.config_data

        # Default interval
        ctk.CTkLabel(win, text="Default check interval (minutes):",
                     text_color=TEXT_COLOR, fg_color=PRIMARY_BG).pack(pady=6)
        interval = ctk.CTkEntry(win, fg_color=SURFACE_BG, text_color=TEXT_COLOR)
        interval.insert(0, str(cfg.get("default_check_interval_minutes",360)))
        interval.pack(pady=4)

        # Windows notifications toggle
        windows_var = ctk.BooleanVar(value=cfg.get("notify_windows", False))
        ctk.CTkCheckBox(win, text="Show Windows notifications",
                        variable=windows_var, text_color=TEXT_COLOR,
                        fg_color=PRIMARY_BG).pack(pady=6)

        # Startup
        startup_var = ctk.BooleanVar(value=cfg.get("startup_enabled", False))
        ctk.CTkCheckBox(win, text="Run on Windows startup",
                        variable=startup_var, text_color=TEXT_COLOR,
                        fg_color=PRIMARY_BG).pack(pady=6)

        def save_settings():
            try:
                cfg["default_check_interval_minutes"] = int(interval.get())
            except ValueError:
                cfg["default_check_interval_minutes"] = 360
            cfg["notify_windows"] = windows_var.get()
            cfg["startup_enabled"] = startup_var.get()
            save_config(cfg)
            if cfg["startup_enabled"]:
                enable_startup()
            else:
                disable_startup()
            win.destroy()

        ctk.CTkButton(win, text="Save Settings",
                      fg_color=PRIMARY_ORANGE, hover_color=SECONDARY_ORANGE,
                      text_color=TEXT_COLOR, command=save_settings).pack(pady=12)

    # --- Tray methods ---
    def hide_to_tray(self):
        self.withdraw()
        if self.tray_icon:
            self.tray_icon.visible = True

    def create_tray_icon(self):
        # Create simple circular icon
        image = Image.new("RGB", (64,64), PRIMARY_BG)
        draw = ImageDraw.Draw(image)
        draw.ellipse((8,8,56,56), fill=PRIMARY_ORANGE)
        self.tray_icon = pystray.Icon("EITS", image, "EITS")
        self.tray_icon.menu = pystray.Menu(
            pystray.MenuItem("Restore", self.restore_from_tray),
            pystray.MenuItem("Exit", self.exit_app)
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def restore_from_tray(self, icon=None, item=None):
        self.deiconify()
        self.lift()
        self.focus_force()

    def exit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()
