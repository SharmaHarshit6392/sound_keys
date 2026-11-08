import threading

import json
import os
import sys
import shutil
import tempfile
import zipfile

import tkinter.messagebox as messagebox

from tkinter import filedialog

from pathlib import Path
import pygame

import customtkinter as ctk

from sound_engine import SoundEngine

from sound_library import SoundLibrary

from key_mapping import KeyMapping

import config

# ============================================================

# THEME

# ============================================================

ctk.set_appearance_mode("dark")

ctk.set_default_color_theme("blue")

BG = "#070B16"

SIDEBAR = "#0A1020"

PANEL = "#0D1527"

PANEL_ALT = "#111D33"

BORDER = "#20395A"

BLUE = "#00C8FF"

PURPLE = "#A855F7"

WHITE = "#EAF4FF"

MUTED = "#8295B4"

GREEN = "#31F7A1"

RED = "#FF4778"

# ============================================================

# APPLICATION

# ============================================================

class SoundKeysApp(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.engine = None

        self.sound_library = SoundLibrary()

        self.key_mapping = KeyMapping(self.sound_library)

        self.preview_sound = None

        self._exit_requested = threading.Event()

        self._closing = False

        self.tray_icon = None
        self._tray_available = False
        self.master_volume = 0.80
        self.startup_enabled = False

        self.mode = "Chaos Mode"

        self.running = False

        # Prevent overlapping Start/Stop actions from the window and tray.
        self._engine_action_busy = False
        self._pending_stop = False

        self.muted = False

        self.mechanical_profile = getattr(config, "MECHANICAL_PROFILE", "blue")

        self.mechanical_volume = float(getattr(config, "MECHANICAL_VOLUME", 0.65))

        local_app_data = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
        self.user_data_dir = local_app_data / "SoundKeys"
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.mechanical_settings_file = self.user_data_dir / "mechanical_settings.json"

        self._load_mechanical_settings()

        self.active_page = "HOME"

        self.nav_buttons = {}

        self.title("SoundKeys | Cyberpunk Edition")

        self._set_window_icon()

        self.geometry("1100x740")

        self.minsize(900, 650)

        self.configure(fg_color=BG)

        self.build_layout()

        self.show_page("HOME")

        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        self.after(150, self.sync_engine_status)
        if "--startup" in sys.argv:
            self.after(500, self.minimize_to_tray)

    def _resource_path(self, filename):
        """Resolve bundled assets in development and PyInstaller builds."""
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        return base / filename

    def _set_window_icon(self):
        """Apply the SoundKeys icon to the title bar and Windows taskbar."""
        icon_path = self._resource_path("SoundKeys.ico")
        if not icon_path.exists():
            return
        try:
            self.iconbitmap(default=str(icon_path))
        except Exception as error:
            print(f"Could not set window icon: {error}")
        try:
            from PIL import Image, ImageTk
            with Image.open(icon_path) as icon_image:
                self._window_icon_image = ImageTk.PhotoImage(icon_image.convert("RGBA"))
            self.iconphoto(True, self._window_icon_image)
        except Exception as error:
            print(f"Could not set taskbar image: {error}")

    # ========================================================

    # MAIN LAYOUT

    # ========================================================

    def build_layout(self):

        self.grid_columnconfigure(1, weight=1)

        self.grid_rowconfigure(0, weight=1)

        # Sidebar

        self.sidebar = ctk.CTkFrame(

            self,

            width=205,

            corner_radius=0,

            fg_color=SIDEBAR,

            border_width=1,

            border_color=BORDER

        )

        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(

            self.sidebar,

            text="〰",

            font=("Segoe UI", 48, "bold"),

            text_color=BLUE

        ).pack(pady=(25, 0))

        ctk.CTkLabel(

            self.sidebar,

            text="SOUNDKEYS",

            font=("Segoe UI", 21, "bold"),

            text_color=WHITE

        ).pack(pady=(0, 3))

        ctk.CTkLabel(

            self.sidebar,

            text="YOUR KEYBOARD. YOUR SOUND.",

            font=("Segoe UI", 8, "bold"),

            text_color=MUTED

        ).pack(pady=(0, 28))

        navigation = [

            ("HOME", "⌂"),

            ("KEY MAPPING", "⌨"),

            ("ABOUT", "ⓘ")

        ]

        for name, icon in navigation:

            button = ctk.CTkButton(

                self.sidebar,

                text=f"   {icon}     {name}",

                anchor="w",

                height=43,

                corner_radius=8,

                font=("Segoe UI", 12, "bold"),

                fg_color="transparent",

                hover_color=PANEL_ALT,

                text_color=MUTED,

                command=lambda page=name: self.show_page(page)

            )

            button.pack(fill="x", padx=12, pady=4)

            self.nav_buttons[name] = button

        ctk.CTkFrame(

            self.sidebar,

            height=2,

            fg_color=BORDER

        ).pack(fill="x", padx=15, pady=(22, 12))

        ctk.CTkLabel(

            self.sidebar,

            text="SYSTEM STATUS",

            font=("Segoe UI", 10, "bold"),

            text_color=MUTED

        ).pack(anchor="w", padx=20)

        self.sidebar_status = ctk.CTkLabel(

            self.sidebar,

            text="● OFFLINE",

            font=("Segoe UI", 12, "bold"),

            text_color=RED

        )

        self.sidebar_status.pack(anchor="w", padx=20, pady=(8, 0))

        ctk.CTkLabel(

            self.sidebar,

            text="SOUNDKEYS\nCYBERPUNK EDITION",

            justify="left",

            font=("Segoe UI", 10, "bold"),

            text_color=PURPLE

        ).pack(side="bottom", anchor="w", padx=20, pady=22)

        # Main content

        self.content = ctk.CTkFrame(

            self,

            fg_color=BG,

            corner_radius=0

        )

        self.content.grid(

            row=0,

            column=1,

            sticky="nsew",

            padx=18,

            pady=15

        )

        self.content.grid_columnconfigure(0, weight=1)

        self.content.grid_rowconfigure(1, weight=1)

        # Header

        header = ctk.CTkFrame(

            self.content,

            fg_color="transparent"

        )

        header.grid(

            row=0,

            column=0,

            sticky="ew",

            pady=(3, 18)

        )

        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(

            header,

            text="SOUNDKEYS  /  CONTROL CENTER",

            font=("Segoe UI", 19, "bold"),

            text_color=WHITE

        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(

            header,

            text="DESKTOP EDITION  •  v0.1",

            font=("Consolas", 10),

            text_color=BLUE

        ).grid(row=1, column=0, sticky="w", pady=(5, 0))

        self.header_badge = ctk.CTkLabel(

            header,

            text="● READY",

            font=("Segoe UI", 11, "bold"),

            text_color=GREEN,

            fg_color=PANEL,

            corner_radius=8

        )

        self.header_badge.grid(

            row=0,

            column=1,

            rowspan=2,

            padx=8,

            ipadx=12,

            ipady=8

        )

        # Page container

        self.page = ctk.CTkFrame(

            self.content,

            fg_color="transparent"

        )

        self.page.grid(row=1, column=0, sticky="nsew")

        self.page.grid_columnconfigure(0, weight=1)

    # ========================================================

    # REUSABLE PANEL

    # ========================================================

    def make_panel(self, parent, title, subtitle=None):

        panel = ctk.CTkFrame(

            parent,

            fg_color=PANEL,

            corner_radius=14,

            border_width=1,

            border_color=BORDER

        )

        ctk.CTkLabel(

            panel,

            text=title,

            font=("Segoe UI", 12, "bold"),

            text_color=BLUE

        ).pack(anchor="w", padx=16, pady=(12, 4))

        if subtitle:

            ctk.CTkLabel(

                panel,

                text=subtitle,

                font=("Segoe UI", 10),

                text_color=MUTED,

                wraplength=420,

                justify="left"

            ).pack(anchor="w", padx=16, pady=(0, 8))

        return panel

    # ========================================================

    # PAGE NAVIGATION

    # ========================================================

    def clear_page(self):

        for widget in self.page.winfo_children():

            widget.destroy()

    def show_page(self, page_name):

        self.active_page = page_name

        for name, button in self.nav_buttons.items():

            button.configure(

                fg_color=(

                    "#132A46" if name == page_name

                    else "transparent"

                ),

                text_color=(

                    BLUE if name == page_name

                    else MUTED

                )

            )

        self.clear_page()

        builders = {

            "HOME": self.build_home,

            "KEY MAPPING": self.build_key_mapping,

            "ABOUT": self.build_about

        }

        builders.get(page_name, self.build_home)()

    # ========================================================

    # HOME PAGE

    # ========================================================

    def build_home(self):

        # Important layout fix:

        # Rows 0 and 1 retain the space their contents need.

        # Row 2 absorbs the remaining vertical space.

        self.page.grid_columnconfigure(0, weight=3, uniform="home")

        self.page.grid_columnconfigure(1, weight=2, uniform="home")

        self.page.grid_rowconfigure(0, weight=0)

        self.page.grid_rowconfigure(1, weight=0)

        self.page.grid_rowconfigure(2, weight=1)

        # ----------------------------------------------------

        # MODE SELECTION

        # ----------------------------------------------------

        mode_panel = self.make_panel(

            self.page,

            "01  /  SELECT YOUR MODE",

            "Choose how your keyboard triggers sound effects."

        )

        mode_panel.grid(

            row=0,

            column=0,

            columnspan=2,

            sticky="ew",

            pady=(0, 10)

        )

        modes = ctk.CTkFrame(

            mode_panel,

            fg_color="transparent"

        )

        modes.pack(fill="x", padx=12, pady=(0, 12))

        modes.grid_columnconfigure((0, 1, 2), weight=1)

        self.mode_buttons = {}

        mode_options = [

            ("Chaos Mode", "Random sounds\non selected keys", PURPLE),

            ("Custom Mode", "Choose a sound\nfor each key", BLUE),

            ("Mechanical Mode", "Mechanical sounds\non every keypress", GREEN)

        ]

        for col, (name, desc, accent) in enumerate(mode_options):

            selected = self.mode == name

            button = ctk.CTkButton(

                modes,

                text=(

                    f"{'✦' if name == 'Chaos Mode' else '⌨' if name == 'Mechanical Mode' else '⌘'}\n\n"

                    f"{name.upper()}\n\n{desc}"

                ),

                height=105,

                corner_radius=12,

                border_width=1,

                border_color=accent if selected else BORDER,

                fg_color=(

                    ("#201638" if name == "Chaos Mode" else "#123126" if name == "Mechanical Mode" else "#10283A")

                    if selected else PANEL_ALT

                ),

                hover_color="#202A45",

                text_color=WHITE,

                font=("Segoe UI", 12, "bold"),

                command=lambda chosen=name: self.select_mode(chosen)

            )

            button.grid(row=0, column=col, sticky="ew", padx=5)

            self.mode_buttons[name] = button

        # Mechanical sound profile controls (used when Mechanical Mode is selected).

        mechanical_controls = ctk.CTkFrame(

            mode_panel,

            fg_color="transparent"

        )

        mechanical_controls.pack(fill="x", padx=16, pady=(0, 12))

        mechanical_controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(

            mechanical_controls,

            text="SWITCH PROFILE",

            text_color=MUTED,

            font=("Segoe UI", 10, "bold")

        ).grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.mechanical_profile_menu = ctk.CTkOptionMenu(

            mechanical_controls,

            values=["blue", "red", "brown", "black"],

            width=115,

            height=30,

            fg_color=PANEL_ALT,

            button_color="#075985",

            button_hover_color="#0369A1",

            text_color=WHITE,

            command=self.set_mechanical_profile

        )

        self.mechanical_profile_menu.set(self.mechanical_profile)

        self.mechanical_profile_menu.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            mechanical_controls, text="VOLUME", text_color=MUTED,
            font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=2, sticky="e", padx=(18, 8))

        # One universal volume control for Chaos, Custom and Mechanical modes.
        self.volume_slider = ctk.CTkSlider(
            mechanical_controls, from_=0.0, to=1.0, number_of_steps=100,
            width=150, command=self.set_master_volume
        )
        self.volume_slider.set(self.master_volume)
        self.volume_slider.grid(row=0, column=3, sticky="e")

        self.volume_label = ctk.CTkLabel(
            mechanical_controls, text=f"{round(self.master_volume * 100)}%",
            text_color=BLUE, width=38, font=("Consolas", 10, "bold")
        )
        self.volume_label.grid(row=0, column=4, sticky="e", padx=(6, 0))

        # ----------------------------------------------------

        # ENGINE STATUS

        # ----------------------------------------------------

        status_panel = self.make_panel(

            self.page,

            "02  /  ENGINE STATUS",

            "Current application state."

        )

        status_panel.grid(

            row=1,

            column=0,

            sticky="nsew",

            padx=(0, 5),

            pady=(0, 10)

        )

        self.status_text = ctk.CTkLabel(

            status_panel,

            text="RUNNING" if self.running else "STOPPED",

            font=("Segoe UI", 26, "bold"),

            text_color=GREEN if self.running else RED

        )

        self.status_text.pack(pady=(8, 0))

        self.status_detail = ctk.CTkLabel(

            status_panel,

            text=(

                f"{self.mode} • Keyboard detection active"

                if self.running else "Keyboard detection stopped"

            ),

            font=("Consolas", 10),

            text_color=MUTED

        )

        self.status_detail.pack(pady=(3, 10))

        # ----------------------------------------------------

        # QUICK CONTROLS

        # ----------------------------------------------------

        controls = self.make_panel(

            self.page,

            "03  /  QUICK CONTROLS",

            "Control the sound engine."

        )

        controls.grid(

            row=1,

            column=1,

            sticky="nsew",

            padx=(5, 0),

            pady=(0, 10)

        )

        # Compact buttons and reduced padding prevent clipping.

        self.start_button = ctk.CTkButton(

            controls,

            text="▶   START",

            height=34,

            corner_radius=9,

            fg_color="#075985",

            hover_color="#0369A1",

            text_color=WHITE,

            font=("Segoe UI", 12, "bold"),

            command=self.start_soundkeys

        )

        self.start_button.pack(

            fill="x",

            padx=12,

            pady=(2, 3)

        )

        self.stop_button = ctk.CTkButton(

            controls,

            text="■   STOP",

            height=34,

            corner_radius=9,

            fg_color="#252D40",

            hover_color="#39445C",

            text_color=WHITE if self.running else MUTED,

            font=("Segoe UI", 12, "bold"),

            state="normal" if self.running else "disabled",

            command=self.stop_soundkeys

        )

        self.stop_button.pack(

            fill="x",

            padx=12,

            pady=3

        )

        self.mute_button = ctk.CTkButton(

            controls,

            text="🔇   UNMUTE" if self.muted else "🔊   MUTE",

            height=34,

            corner_radius=9,

            fg_color="#24203A",

            hover_color="#3A2D58",

            text_color=WHITE,

            font=("Segoe UI", 12, "bold"),

            command=self.toggle_mute

        )

        self.mute_button.pack(

            fill="x",

            padx=12,

            pady=(3, 8)

        )

        # ----------------------------------------------------

        # KEYBOARD PREVIEW

        # ----------------------------------------------------

        if self.mode == "Custom Mode":
            mappings = self.key_mapping.list_mappings()
            # Only keys with an actual saved mapping are highlighted.
            active_keys = {
                key.upper()
                for key, filename in mappings.items()
                if filename and filename in self.available_mapping_sounds()
            }
        elif self.mode == "Mechanical Mode":
            active_keys = {
                "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
                "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P",
                "A", "S", "D", "F", "G", "H", "J", "K", "L",
                "Z", "X", "C", "V", "B", "N", "M", "SPACE", "ENTER",
                "TAB", "BACKSPACE", "SHIFT", "CTRL", "ALT"
            }
        else:
            active_keys = {"A", "S", "D", "SPACE", "ENTER"}

        keyboard_panel = self.make_panel(

            self.page,

            "04  /  KEYBOARD PREVIEW",

        )

        keyboard_panel.grid(

            row=2,

            column=0,

            columnspan=2,

            sticky="nsew",

            pady=(0, 8)

        )

        keyboard_frame = ctk.CTkFrame(

            keyboard_panel,

            fg_color="transparent"

        )

        keyboard_frame.pack(

            fill="both",

            expand=True,

            padx=12,

            pady=(0, 8)

        )

        # Responsive ANSI keyboard with compact vertical sizing.
        # Each row uses 60 proportional grid units and fits the preview panel.
        rows = [
            [("ESC", 4), ("F1", 4), ("F2", 4), ("F3", 4), ("F4", 4),
             ("F5", 4), ("F6", 4), ("F7", 4), ("F8", 4), ("F9", 4),
             ("F10", 4), ("F11", 4), ("F12", 4)],
            [("`", 4), ("1", 4), ("2", 4), ("3", 4), ("4", 4),
             ("5", 4), ("6", 4), ("7", 4), ("8", 4), ("9", 4),
             ("0", 4), ("-", 4), ("=", 4), ("BACKSPACE", 8)],
            [("TAB", 6), ("Q", 4), ("W", 4), ("E", 4), ("R", 4),
             ("T", 4), ("Y", 4), ("U", 4), ("I", 4), ("O", 4),
             ("P", 4), ("[", 4), ("]", 4), ("\\\\", 6)],
            [("CAPS", 7), ("A", 4), ("S", 4), ("D", 4), ("F", 4),
             ("G", 4), ("H", 4), ("J", 4), ("K", 4), ("L", 4),
             (";", 4), ("'", 4), ("ENTER", 9)],
            [("SHIFT", 9), ("Z", 4), ("X", 4), ("C", 4), ("V", 4),
             ("B", 4), ("N", 4), ("M", 4), (",", 4), (".", 4),
             ("/", 4), ("SHIFT", 9)],
            [("CTRL", 5), ("WIN", 4), ("ALT", 5), ("SPACE", 24),
             ("ALT", 5), ("WIN", 4), ("MENU", 4), ("CTRL", 5)],
        ]

        special_active = {
            "BACKSPACE": "BACKSPACE", "TAB": "TAB", "CAPS": "CAPS LOCK",
            "ENTER": "ENTER", "SHIFT": "SHIFT", "CTRL": "CTRL",
            "ALT": "ALT", "SPACE": "SPACE"
        }

        keyboard_key_labels = []
        for row_index, row_keys in enumerate(rows):
            row_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=0)
            for unit in range(60):
                row_frame.grid_columnconfigure(unit, weight=1, uniform="keyboard_units")

            total_units = sum(span for _, span in row_keys)
            column = max(0, (60 - total_units) // 2)

            for key, span in row_keys:
                active_key = special_active.get(key, key)
                active = (
                    self.mode == "Mechanical Mode"
                    or key in active_keys
                    or active_key in active_keys
                )
                label = ctk.CTkLabel(
                    row_frame,
                    text=key,
                    height=16,
                    corner_radius=5,
                    fg_color="#172A43" if active else "#101827",
                    text_color=BLUE if active else MUTED,
                    font=("Consolas", 7 if len(key) > 4 else 8, "bold"),
                    border_width=1,
                    border_color=PURPLE if active else BORDER
                )
                label.grid(
                    row=0,
                    column=column,
                    columnspan=span,
                    sticky="nsew",
                    padx=1,
                    pady=0
                )
                keyboard_key_labels.append(label)
                column += span

        # Recalculate key height from the actual space available in the panel.
        # Do not enforce a minimum that can make six rows taller than the panel;
        # that was causing the bottom keyboard row to be clipped in short windows.
        def fit_keyboard_preview(event=None):
            available_height = keyboard_frame.winfo_height()
            if available_height <= 1:
                return
            key_height = max(6, min(20, (available_height - 4) // 6))
            for key_label in keyboard_key_labels:
                key_label.configure(height=key_height)

        keyboard_frame.bind("<Configure>", fit_keyboard_preview, add="+")
        keyboard_frame.after(100, fit_keyboard_preview)

    # ========================================================

    # MODE SELECTION

    # ========================================================

    def select_mode(self, mode):

        if self._engine_action_busy:
            messagebox.showinfo("SoundKeys", "Please wait for the current audio operation to finish.", parent=self)
            return

        if self.running:

            messagebox.showinfo(

                "SoundKeys",

                "Stop SoundKeys before changing modes.",

                parent=self

            )

            return

        self.mode = mode

        if self.active_page == "HOME":

            self.show_page("HOME")

        elif self.active_page == "MODE SETTINGS":

            self.show_page("MODE SETTINGS")

    def _load_mechanical_settings(self):

        try:

            if self.mechanical_settings_file.exists():

                data = json.loads(self.mechanical_settings_file.read_text(encoding="utf-8"))

                profile = str(data.get("profile", self.mechanical_profile)).lower()

                # Older releases stored the only visible volume as "volume".
                # Reuse it when no universal-volume value exists.
                master = float(data.get("master_volume", data.get("volume", self.master_volume)))

                if profile in {"blue", "red", "brown", "black"}:
                    self.mechanical_profile = profile

                self.master_volume = max(0.0, min(1.0, master))

            # Mechanical mode now uses the same universal volume as every mode.
            self.mechanical_volume = 1.0

            config.MECHANICAL_PROFILE = self.mechanical_profile

            config.MECHANICAL_VOLUME = 1.0

        except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:

            print(f"Could not load mechanical settings: {error}")

    def _save_mechanical_settings(self):

        try:

            data = {

                "profile": self.mechanical_profile,

                "volume": self.master_volume,
                "master_volume": self.master_volume

            }

            self.mechanical_settings_file.write_text(

                json.dumps(data, indent=4),

                encoding="utf-8"

            )

        except OSError as error:

            print(f"Could not save mechanical settings: {error}")

    def set_mechanical_profile(self, profile):
        profile = str(profile).strip().lower()
        if profile not in {"blue", "red", "brown", "black"}:
            return

        previous_profile = self.mechanical_profile
        print(
            f"[SoundKeys GUI] Profile selection: {previous_profile!r} -> {profile!r}; "
            f"engine_exists={self.engine is not None}; "
            f"engine_running={getattr(self.engine, 'running', None)}; "
            f"engine_mode={getattr(self.engine, 'mode', None)!r}"
        )
        try:
            # If Mechanical Mode is already running, reload its sound objects
            # immediately while holding the engine lock used by key callbacks.
            if self.engine is not None:
                if self.engine.running and self.engine.mode == "mechanical":
                    # Public engine method loads the new pack before swapping it in.
                    self.engine.set_mechanical_profile(profile)
                    print(f"[SoundKeys GUI] Engine accepted profile: {self.engine.mechanical_profile!r}")
                else:
                    self.engine.mechanical_profile = profile

            self.mechanical_profile = profile
            config.MECHANICAL_PROFILE = profile
            self._save_mechanical_settings()
            print(f"[SoundKeys GUI] Profile selection completed: {self.mechanical_profile!r}")

        except Exception as error:
            print(f"[SoundKeys GUI] Profile switch FAILED: {error!r}")
            # Restore the previous working profile if the requested pack fails.
            if self.engine is not None:
                try:
                    with self.engine._lock:
                        if self.engine.running and self.engine.mode == "mechanical":
                            self.engine.set_mechanical_profile(previous_profile)
                        else:
                            self.engine.mechanical_profile = previous_profile
                except Exception as restore_error:
                    print(f"Could not restore previous mechanical profile: {restore_error}")
            self.mechanical_profile = previous_profile
            if hasattr(self, "mechanical_profile_menu"):
                self.mechanical_profile_menu.set(previous_profile)
            messagebox.showerror(
                "Mechanical Profile Error",
                f"Could not load the '{profile}' profile.\n\n{error}",
                parent=self
            )

    def set_mechanical_volume(self, value):
        """Backward-compatible alias for the universal volume control."""
        self.set_master_volume(value)

    def set_master_volume(self, value):
        self.master_volume = max(0.0, min(1.0, float(value)))
        self._save_mechanical_settings()
        if hasattr(self, "volume_label"):
            self.volume_label.configure(text=f"{round(self.master_volume * 100)}%")
        if self.engine is not None:
            self.engine.set_master_volume(self.master_volume)
        if self.preview_sound is not None:
            try:
                # Preview Sound objects use the master level directly.
                self.preview_sound.set_volume(self.master_volume)
            except Exception:
                pass

    def _startup_command(self):
        if getattr(sys, "frozen", False):
            return f'"{sys.executable}" --startup'
        script = str(Path(__file__).resolve())
        return f'"{sys.executable}" "{script}" --startup'

    def set_startup_enabled(self, enabled):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
            try:
                if enabled:
                    winreg.SetValueEx(key, "SoundKeys", 0, winreg.REG_SZ, self._startup_command())
                else:
                    try: winreg.DeleteValue(key, "SoundKeys")
                    except FileNotFoundError: pass
            finally:
                winreg.CloseKey(key)
            self.startup_enabled = bool(enabled)
        except Exception as error:
            messagebox.showerror("Startup setting", f"Could not update Windows startup:\n\n{error}", parent=self)
            if hasattr(self, "startup_switch"):
                self.startup_switch.deselect() if enabled else self.startup_switch.select()

    def _startup_is_enabled(self):
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
                value, _ = winreg.QueryValueEx(key, "SoundKeys")
            return bool(value)
        except OSError:
            return False

    def export_backup(self):
        destination = filedialog.asksaveasfilename(parent=self, title="Back up SoundKeys",
            defaultextension=".zip", filetypes=[("SoundKeys backup", "*.zip")],
            initialfile="SoundKeys_Backup.zip")
        if not destination: return
        try:
            allowed = [self.user_data_dir / "library.json",
                       self.user_data_dir / "key_mappings.json",
                       self.user_data_dir / "mechanical_settings.json"]
            custom_dir = self.user_data_dir / "sounds" / "custom"
            if custom_dir.is_dir(): allowed.extend(p for p in custom_dir.rglob("*") if p.is_file())
            with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in allowed:
                    if path.is_file():
                        archive.write(path, path.relative_to(self.user_data_dir).as_posix())
            messagebox.showinfo("Backup complete", "Your SoundKeys settings and custom sounds were backed up.", parent=self)
        except Exception as error:
            messagebox.showerror("Backup failed", str(error), parent=self)

    def restore_backup(self):
        source = filedialog.askopenfilename(parent=self, title="Restore SoundKeys backup",
            filetypes=[("SoundKeys backup", "*.zip")])
        if not source:
            return
        if not messagebox.askyesno("Restore backup", "This will replace your current SoundKeys settings and custom sound library. Continue?", parent=self):
            return

        allowed_exact = {"library.json", "key_mappings.json", "mechanical_settings.json"}
        allowed_ext = {".mp3", ".wav", ".ogg", ".flac"}
        stage = Path(tempfile.mkdtemp(prefix="soundkeys_restore_", dir=str(self.user_data_dir)))
        safety = Path(tempfile.mkdtemp(prefix="soundkeys_safety_", dir=str(self.user_data_dir)))
        try:
            with zipfile.ZipFile(source, "r") as archive:
                members = archive.infolist()
                if len(members) > 1000 or sum(i.file_size for i in members) > 500 * 1024 * 1024:
                    raise ValueError("Backup is too large or contains too many files.")
                validated = []
                for info in members:
                    # Normalize both separator styles before validating archive paths.
                    rel = info.filename.replace("\\", "/")
                    parts = rel.split("/")
                    if rel.startswith("/") or any(part in {"", ".", ".."} for part in parts if part):
                        raise ValueError("Backup contains an unsafe file path.")
                    if info.is_dir():
                        continue
                    valid = rel in allowed_exact or (
                        len(parts) >= 3 and parts[0] == "sounds" and parts[1] == "custom"
                        and Path(parts[-1]).suffix.lower() in allowed_ext
                    )
                    if not valid:
                        raise ValueError(f"Unsupported backup entry: {rel}")
                    validated.append((info, rel))
                if not validated:
                    raise ValueError("The selected archive contains no SoundKeys backup files.")
                # Extract only to a staging directory first; the live data is untouched
                # unless every archive member has been read successfully.
                for info, rel in validated:
                    target = stage.joinpath(*rel.split("/"))
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)

            if self.engine is not None:
                self.engine.stop()
                self.engine.close()
                self.engine = None
                self.running = False

            # Snapshot the current restorable files so an unexpected filesystem
            # failure during commit can be rolled back.
            for name in allowed_exact:
                current = self.user_data_dir / name
                if current.is_file():
                    shutil.copy2(current, safety / name)
            current_custom = self.user_data_dir / "sounds" / "custom"
            if current_custom.is_dir():
                shutil.copytree(current_custom, safety / "sounds" / "custom")

            try:
                if current_custom.exists():
                    shutil.rmtree(current_custom)
                staged_custom = stage / "sounds" / "custom"
                if staged_custom.is_dir():
                    current_custom.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(staged_custom, current_custom)
                for name in allowed_exact:
                    staged_file = stage / name
                    if staged_file.is_file():
                        shutil.copy2(staged_file, self.user_data_dir / name)
            except Exception:
                if current_custom.exists():
                    shutil.rmtree(current_custom)
                if (safety / "sounds" / "custom").is_dir():
                    shutil.copytree(safety / "sounds" / "custom", current_custom)
                for name in allowed_exact:
                    old = safety / name
                    live = self.user_data_dir / name
                    if old.is_file():
                        shutil.copy2(old, live)
                    elif live.exists():
                        live.unlink()
                raise

            self.sound_library = SoundLibrary()
            self.key_mapping = KeyMapping(self.sound_library)
            self._load_mechanical_settings()
            self.refresh_library_list()
            self.refresh_mapping_list()
            self.refresh_mapping_sound_menu()
            if hasattr(self, "volume_slider"):
                self.volume_slider.set(self.master_volume)
                self.volume_label.configure(text=f"{round(self.master_volume * 100)}%")
            messagebox.showinfo("Restore complete", "Backup restored. Start SoundKeys again to use the restored settings.", parent=self)
        except Exception as error:
            messagebox.showerror("Restore failed", f"Could not restore this backup:\n\n{error}", parent=self)
        finally:
            shutil.rmtree(stage, ignore_errors=True)
            shutil.rmtree(safety, ignore_errors=True)

    def test_audio_output(self):
        """Play a short generated test tone without adding or changing assets."""
        try:
            from array import array
            import math
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            frequency, sample_format, channels = pygame.mixer.get_init()
            if sample_format not in (-16, 16):
                raise RuntimeError(f"Unsupported mixer sample format for test tone: {sample_format}")
            samples = array("h")
            for index in range(int(frequency * 0.35)):
                envelope = min(1.0, index / max(1, int(frequency * 0.02)))
                sample = int(5000 * envelope * math.sin(2 * math.pi * 440 * index / frequency))
                for _ in range(max(1, channels)):
                    samples.append(sample)
            tone = pygame.mixer.Sound(buffer=samples.tobytes())
            tone.set_volume(self.master_volume)
            tone.play()
        except Exception as error:
            messagebox.showerror("Audio test failed", f"Could not play the test tone:\n\n{error}", parent=self)

    def run_audio_diagnostics(self):
        lines = []
        try:
            init = pygame.mixer.get_init()
            lines.append(f"Mixer initialized: {'Yes' if init else 'No'}")
            if init:
                lines.append(f"Audio format: {init[0]} Hz / format {init[1]} / {init[2]} channel(s)")
                lines.append(f"Mixer channels: {pygame.mixer.get_num_channels()}")
                lines.append(f"Channels busy: {sum(1 for i in range(pygame.mixer.get_num_channels()) if pygame.mixer.Channel(i).get_busy())}")
            try:
                from pygame._sdl2.audio import get_audio_device_names
                devices = get_audio_device_names(False)
                lines.append("Output devices: " + (", ".join(devices) if devices else "None reported"))
            except Exception as device_error:
                lines.append(f"Output devices: unavailable ({device_error})")
            if self.engine is not None:
                lines.append(f"Loaded standard sounds: {len(self.engine.sounds)}")
                lines.append(f"Loaded mechanical sounds: {len(self.engine.mechanical_sounds)}")
                lines.append(f"Engine running: {self.engine.running}")
            else:
                lines.append("Engine: not initialized")
            custom_dir = self.user_data_dir / "sounds" / "custom"
            files = [p for p in custom_dir.iterdir() if p.is_file()] if custom_dir.exists() else []
            lines.append(f"Custom audio files on disk: {len(files)}")
            if pygame.mixer.get_init():
                unreadable = []
                for path in files:
                    try:
                        pygame.mixer.Sound(str(path))
                    except Exception:
                        unreadable.append(path.name)
                lines.append(f"Unreadable custom files: {len(unreadable)}")
                if unreadable:
                    lines.append("Check: " + ", ".join(unreadable[:8]))
            else:
                lines.append("Unreadable-file scan: skipped (audio mixer is not initialized)")
            lines.append(f"Volume: {round(self.master_volume * 100)}%")
        except Exception as error:
            lines.append(f"Diagnostics error: {error}")
        messagebox.showinfo("Audio diagnostics", "\n".join(lines), parent=self)

    # ENGINE CONTROLS

    # ========================================================

    def _finish_engine_action(self, action, error=None):
        """Apply worker results on Tk's thread and run a queued Stop if needed."""
        if self._closing:
            return

        self.running = bool(self.engine and self.engine.running)
        self.muted = bool(self.engine.muted) if self.engine else self.muted
        self._engine_action_busy = False
        self.update_status_widgets()

        if error is not None:
            print(f"SoundKeys {action} error: {error}")
            messagebox.showerror(
                "SoundKeys Error",
                f"Could not {action} SoundKeys:\n\n{error}",
                parent=self,
            )

        if action == "start" and self._pending_stop:
            self._pending_stop = False
            self.after(0, self.stop_soundkeys)

    def start_soundkeys(self):
        """Start/load the engine on a worker so audio loading never freezes Tk."""
        if self._closing:
            return
        if self._engine_action_busy:
            return
        if self.engine is not None and self.engine.running:
            self.running = True
            self.muted = bool(self.engine.muted)
            self.update_status_widgets()
            return

        self._engine_action_busy = True
        self._pending_stop = False
        self.update_status_widgets()
        selected_mode = self.mode

        def worker():
            error = None
            try:
                if self.engine is None:
                    self.engine = SoundEngine(on_exit=self._request_exit)
                else:
                    # Cleanup may wait for the global keyboard hook; keep it off Tk.
                    self.engine.stop()

                self.engine.mechanical_profile = self.mechanical_profile
                self.engine.mechanical_volume = 1.0
                self.engine.set_master_volume(self.master_volume)
                self.engine.start(mode=selected_mode)

                # Preserve the user's mute preference, including a mute click
                # made while the engine was starting.
                if self.muted and not self.engine.muted:
                    self.engine.toggle_mute()
            except Exception as exc:
                error = exc
            try:
                self.after(0, lambda: self._finish_engine_action("start", error))
            except Exception:
                pass

        threading.Thread(target=worker, name="SoundKeys-Start", daemon=True).start()

    def stop_soundkeys(self):
        """Stop immediately from the UI; perform hook/audio cleanup in background."""
        if self._closing:
            return
        if self._engine_action_busy:
            # If Start is still loading, honor Stop as soon as Start completes.
            self._pending_stop = True
            return
        if self.engine is None:
            self.running = False
            self.update_status_widgets()
            return

        self._engine_action_busy = True
        self.running = False
        self.update_status_widgets()
        engine = self.engine

        def worker():
            error = None
            try:
                engine.stop()
            except Exception as exc:
                error = exc
            try:
                self.after(0, lambda: self._finish_engine_action("stop", error))
            except Exception:
                pass

        threading.Thread(target=worker, name="SoundKeys-Stop", daemon=True).start()

    def toggle_mute(self):
        """Toggle mute from either the GUI or the system-tray menu."""
        if self._closing:
            return

        try:
            if self.engine is None:
                self.muted = not self.muted
            else:
                self.muted = bool(self.engine.toggle_mute())
        except Exception as error:
            print(f"Mute error: {error}")
            messagebox.showerror(
                "SoundKeys Error",
                f"Could not change mute state:\n\n{error}",
                parent=self
            )
            return

        self.update_mute_button()

    @staticmethod
    def _widget_exists(widget):
        """Return False for widgets destroyed during page navigation."""
        try:
            return widget is not None and bool(widget.winfo_exists())
        except Exception:
            return False

    def update_mute_button(self):
        if self._widget_exists(getattr(self, "mute_button", None)):
            try:
                self.mute_button.configure(
                    text="🔇   UNMUTE" if self.muted else "🔊   MUTE"
                )
            except Exception as error:
                print(f"Mute button refresh error: {error}")

    def update_status_widgets(self):
        """Refresh only live widgets; page navigation destroys page-local controls."""
        if self._widget_exists(getattr(self, "status_text", None)):
            try:
                self.status_text.configure(
                    text="RUNNING" if self.running else "STOPPED",
                    text_color=GREEN if self.running else RED
                )
            except Exception as error:
                print(f"Status text refresh error: {error}")

        if self._widget_exists(getattr(self, "status_detail", None)):
            try:
                self.status_detail.configure(
                    text=(
                        f"{self.mode} • Keyboard detection active"
                        if self.running else "Keyboard detection stopped"
                    )
                )
            except Exception as error:
                print(f"Status detail refresh error: {error}")

        if self._widget_exists(getattr(self, "sidebar_status", None)):
            self.sidebar_status.configure(
                text="● ONLINE" if self.running else "● OFFLINE",
                text_color=GREEN if self.running else RED
            )

        if self._widget_exists(getattr(self, "header_badge", None)):
            self.header_badge.configure(
                text="● RUNNING" if self.running else "● READY",
                text_color=GREEN if self.running else MUTED
            )

        # Home-page buttons are destroyed when navigating to another page.
        if self._widget_exists(getattr(self, "start_button", None)):
            self.start_button.configure(
                state="disabled"
                if (self.running or self._engine_action_busy) else "normal"
            )

        if self._widget_exists(getattr(self, "stop_button", None)):
            self.stop_button.configure(
                # Keep Stop clickable during Start so the request can be queued.
                state="normal" if (self.running or self._engine_action_busy) else "disabled",
                text_color=WHITE if (self.running or self._engine_action_busy) else MUTED
            )

        self.update_mute_button()

    def _request_exit(self):

        """Signal the GUI thread to shut down safely."""

        self._exit_requested.set()

    def sync_engine_status(self):
        if self._closing:
            return

        try:
            if self._exit_requested.is_set():
                self.close_app()
                return

            if self.engine is not None:
                actual_running = bool(self.engine.running)
                actual_muted = bool(self.engine.muted)

                if actual_running != self.running:
                    self.running = actual_running
                    self.update_status_widgets()

                if actual_muted != self.muted:
                    self.muted = actual_muted
                    self.update_mute_button()
        except Exception as error:
            # A stale/destroyed widget must never kill the recurring status poll.
            print(f"Engine status sync error: {error}")
        finally:
            if not self._closing:
                try:
                    self.after(150, self.sync_engine_status)
                except Exception:
                    pass

    # ========================================================

    # MODE SETTINGS PAGE

    # ========================================================

    def build_mode_settings(self):

        panel = self.make_panel(

            self.page,

            "MODE SETTINGS",

            "Select a mode. Stop the engine before switching modes."

        )

        panel.grid(row=0, column=0, sticky="ew")

        for mode in ["Chaos Mode", "Custom Mode"]:

            ctk.CTkButton(

                panel,

                text=mode,

                height=42,

                fg_color="#10283A" if self.mode == mode else PANEL_ALT,

                hover_color="#1D3C5B",

                command=lambda chosen=mode: self.select_mode(chosen)

            ).pack(fill="x", padx=16, pady=7)

    # ========================================================

    # SOUND LIBRARY

    # ========================================================

    def build_library(self):

        self.page.grid_rowconfigure(0, weight=0)

        self.page.grid_rowconfigure(1, weight=1)

        panel = self.make_panel(

            self.page,

            "SOUND LIBRARY",

            "Import, preview, and manage your personal sound collection."

        )

        panel.grid(

            row=0,

            column=0,

            sticky="ew",

            pady=(0, 12)

        )

        toolbar = ctk.CTkFrame(

            panel,

            fg_color="transparent"

        )

        toolbar.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkButton(

            toolbar,

            text="+ IMPORT SOUNDS",

            height=36,

            fg_color="#075985",

            hover_color="#0369A1",

            command=self.import_sounds

        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(

            toolbar,

            text="↻ REFRESH",

            height=36,

            fg_color=PANEL_ALT,

            hover_color="#203653",

            command=self.refresh_library_list

        ).pack(side="left")

        self.library_list = ctk.CTkScrollableFrame(

            self.page,

            fg_color=PANEL,

            corner_radius=12,

            border_width=1,

            border_color=BORDER

        )

        self.library_list.grid(

            row=1,

            column=0,

            sticky="nsew"

        )

        self.refresh_library_list()

    def refresh_library_list(self):

        if not hasattr(self, "library_list"):

            return

        if not self.library_list.winfo_exists():

            return

        for widget in self.library_list.winfo_children():

            widget.destroy()

        sounds = self.sound_library.list_sounds()

        if not sounds:

            ctk.CTkLabel(

                self.library_list,

                text="Your library is empty.\nImport some sounds to get started!",

                text_color=MUTED,

                font=("Segoe UI", 13),

                justify="center"

            ).pack(pady=45)

            return

        for filename in sounds:

            row = ctk.CTkFrame(

                self.library_list,

                fg_color=PANEL_ALT,

                corner_radius=8

            )

            row.pack(fill="x", padx=8, pady=5)

            ctk.CTkLabel(

                row,

                text=filename,

                text_color=WHITE,

                anchor="w",

                font=("Segoe UI", 11),

                wraplength=350

            ).pack(

                side="left",

                fill="x",

                expand=True,

                padx=12,

                pady=12

            )

            ctk.CTkButton(

                row,

                text="▶",

                width=42,

                fg_color="#075985",

                hover_color="#0369A1",

                command=lambda name=filename: self.preview_library_sound(name)

            ).pack(side="left", padx=4, pady=8)

            ctk.CTkButton(

                row,

                text="REMOVE",

                width=75,

                fg_color="#572038",

                hover_color="#842747",

                command=lambda name=filename: self.remove_library_sound(name)

            ).pack(side="left", padx=(4, 8), pady=8)

    def import_sounds(self):

        paths = filedialog.askopenfilenames(

            parent=self,

            title="Import sound files",

            filetypes=[

                ("Audio files", "*.mp3 *.wav *.ogg *.flac"),

                ("All files", "*.*")

            ]

        )

        if not paths:

            return

        try:

            imported = self.sound_library.import_files(paths)

            self.refresh_library_list()

            if self.active_page == "KEY MAPPING" and hasattr(self, "mapping_sound_menu"):

                self.refresh_mapping_sound_menu(imported[-1] if imported else None)

            if imported:

                messagebox.showinfo(

                    "SoundKeys",

                    f"Imported {len(imported)} sound(s) successfully.",

                    parent=self

                )

            else:

                messagebox.showwarning(

                    "SoundKeys",

                    "No supported audio files were imported.",

                    parent=self

                )

        except Exception as error:

            messagebox.showerror(

                "Import Error",

                f"Could not import the selected files:\n\n{error}",

                parent=self

            )

    def preview_library_sound(self, filename):

        try:

            self.preview_sound = self.sound_library.preview(filename)
            self.preview_sound.set_volume(self.master_volume)

        except Exception as error:

            messagebox.showerror(

                "Preview Error",

                f"Could not play this sound:\n\n{error}",

                parent=self

            )

    def remove_library_sound(self, filename):

        confirmed = messagebox.askyesno(

            "Remove Sound",

            f"Remove '{filename}' from your SoundKeys library?\n\n"

            "The original file you imported will not be deleted.",

            parent=self

        )

        if not confirmed:

            return

        try:

            if self.preview_sound is not None:

                self.preview_sound.stop()

                self.preview_sound = None

            self.sound_library.remove_sound(filename)

            self.refresh_library_list()

        except Exception as error:

            messagebox.showerror(

                "Remove Error",

                f"Could not remove this sound:\n\n{error}",

                parent=self

            )

    def available_mapping_sounds(self):

        """Return built-in Chaos sounds and user-imported sounds."""

        root = Path(__file__).resolve().parent

        folders = [root / "sounds" / "chaos", self.sound_library.library_dir]

        supported = {".mp3", ".wav", ".ogg", ".flac"}

        found = {}

        for folder in folders:

            if folder.exists():

                for path in sorted(folder.iterdir()):

                    if path.is_file() and path.suffix.lower() in supported:

                        # Keep one unambiguous entry per filename.

                        found.setdefault(path.name, path)

        return found

    def refresh_mapping_sound_menu(self, preferred=None):

        if not hasattr(self, "mapping_sound_menu"):

            return

        sounds = sorted(self.available_mapping_sounds())

        self.mapping_sound_menu.configure(

            values=sounds if sounds else ["No sounds available"],

            state="normal" if sounds else "disabled"

        )

        if sounds:

            current = preferred or self.mapping_sound_menu.get()

            self.mapping_sound_menu.set(current if current in sounds else sounds[0])

    # ========================================================

    # KEY MAPPING PAGE - CLICKABLE KEYBOARD

    # ========================================================

    def build_key_mapping(self):

        # Give the editor and soundboard proportional space. The old fixed

        # second column made the lower panels too wide for smaller windows.

        self.page.grid_columnconfigure(0, weight=7, uniform="mapping_columns")

        self.page.grid_columnconfigure(1, weight=3, uniform="mapping_columns")

        self.page.grid_rowconfigure(0, weight=0)

        self.page.grid_rowconfigure(1, weight=1, minsize=0)

        self.selected_mapping_key = getattr(

            self, "selected_mapping_key", "a"

        )

        self.mapping_key_buttons = {}

        keyboard_panel = self.make_panel(

            self.page,

            "01 / CLICK A KEY",

            "Select a key to assign, replace, or remove its sound. "

            "Cyan keys already have a custom sound."

        )

        keyboard_panel.grid(

            row=0, column=0, columnspan=2,

            sticky="ew", pady=(0, 10)

        )

        keyboard_area = ctk.CTkFrame(

            keyboard_panel, fg_color="transparent"

        )

        keyboard_area.pack(fill="x", padx=10, pady=(2, 8))

        key_rows = [

            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "BACKSPACE"],

            ["TAB", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],

            ["A", "S", "D", "F", "G", "H", "J", "K", "L", "ENTER"],

            ["Z", "X", "C", "V", "B", "N", "M", "LEFT", "DOWN", "UP", "RIGHT"],

            ["SPACE", "DELETE", "HOME", "END", "PGUP", "PGDN", "F1", "F2", "F3", "F4", "F5", "F6"],

            ["F7", "F8", "F9", "F10", "F11", "F12"]

        ]

        for row_index, keys in enumerate(key_rows):

            row_frame = ctk.CTkFrame(

                keyboard_area, fg_color="transparent"

            )

            row_frame.pack(fill="x", pady=1)

            for key_label in keys:

                key_value = {

                    "BACKSPACE": "backspace",

                    "TAB": "tab",

                    "SPACE": "space",

                    "DELETE": "delete",

                    "LEFT": "left", "RIGHT": "right",

                    "UP": "up", "DOWN": "down",

                    "HOME": "home", "END": "end",

                    "PGUP": "page up", "PGDN": "page down"

                }.get(key_label, key_label.lower())

                # ENTER is assignable in Custom Mode; Chaos Mode retains its dedicated Enter sound.

                reserved = False

                mappings = self.key_mapping.list_mappings()
                assigned = bool(mappings.get(key_value)) and mappings.get(key_value) in self.available_mapping_sounds()

                selected = key_value == self.selected_mapping_key
                if self.mode == "Custom Mode" and key_value == "enter" and not assigned:
                    selected = False

                width = 82 if key_label == "SPACE" else 58 if len(key_label) > 4 else 34

                display_label = f"• {key_label}" if assigned else key_label

                if selected:

                    # Selection is a solid cyan/blue keycap.

                    fg, hover, border, txt = "#075985", "#0879A8", BLUE, WHITE

                elif assigned:

                    # Saved assignments use a dark keycap with a cyan marker.

                    fg, hover, border, txt = "#102C43", "#17415F", BLUE, BLUE

                else:

                    fg, hover, border, txt = PANEL_ALT, "#1B2D48", BORDER, MUTED

                button = ctk.CTkButton(

                    row_frame,

                    text=display_label,

                    width=width,

                    height=29,

                    corner_radius=7,

                    fg_color=fg,

                    hover_color=hover,

                    border_width=1,

                    border_color=border,

                    text_color=txt,

                    font=("Consolas", 10, "bold"),

                    state="normal",

                    command=lambda k=key_value: self.select_mapping_key(k)

                )

                # A compact keycap row keeps the keyboard from pushing the

                # configuration controls below the visible window.

                button.pack(side="left", padx=2, pady=1, expand=True, fill="x")

                self.mapping_key_buttons[key_value] = button

        # Bottom area: selected-key editor and current assignments.

        editor = self.make_panel(

            self.page,

            "02 / KEY CONFIGURATION",

            "Choose an audio effect for the selected key."

        )

        editor.grid(

            row=1, column=0, sticky="nsew",

            padx=(0, 6), pady=(0, 2)

        )

        self.selected_key_title = ctk.CTkLabel(

            editor,

            text="SELECTED KEY: A",

            text_color=BLUE,

            font=("Segoe UI", 17, "bold")

        )

        self.selected_key_title.pack(anchor="w", padx=16, pady=(12, 8))

        ctk.CTkLabel(

            editor, text="SOUND EFFECT", text_color=MUTED,

            font=("Segoe UI", 10, "bold")

        ).pack(anchor="w", padx=16, pady=(4, 5))

        sounds = sorted(self.available_mapping_sounds())

        self.mapping_sound_menu = ctk.CTkOptionMenu(

            editor,

            values=sounds if sounds else ["No sounds available"],

            height=38,

            fg_color=PANEL_ALT,

            button_color="#075985",

            button_hover_color="#0369A1",

            text_color=WHITE,

            font=("Segoe UI", 10),

            state="normal" if sounds else "disabled"

        )

        self.mapping_sound_menu.pack(fill="x", padx=16, pady=(0, 10))

        actions = ctk.CTkFrame(editor, fg_color="transparent")

        actions.pack(fill="x", padx=12, pady=(0, 8))

        actions.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(

            actions, text="＋ IMPORT SOUNDS", height=36,

            fg_color="#075985", hover_color="#0369A1",

            command=self.import_sounds

        ).grid(row=0, column=0, sticky="ew", padx=4, pady=4)

        ctk.CTkButton(

            actions, text="▶ PREVIEW", height=36,

            fg_color=PANEL_ALT, hover_color="#203653",

            command=self.preview_selected_mapping_sound

        ).grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        ctk.CTkButton(

            actions, text="SAVE ASSIGNMENT", height=38,

            fg_color="#075985", hover_color="#0369A1",

            font=("Segoe UI", 11, "bold"),

            command=self.assign_selected_sound

        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=4)

        ctk.CTkButton(

            actions, text="REMOVE SOUND FROM KEY", height=34,

            fg_color="#572038", hover_color="#842747",

            command=lambda: self.remove_key_mapping(self.selected_mapping_key)

        ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=4)

        self.mapping_hint = ctk.CTkLabel(

            editor,

            text="Stop the engine before changing mappings.",

            text_color=MUTED,

            font=("Segoe UI", 9),

            wraplength=380

        )

        self.mapping_hint.pack(anchor="w", padx=16, pady=(4, 10))

        assignments = self.make_panel(

            self.page,

            "03 / YOUR SOUNDBOARD",

            "Saved key-to-sound assignments."

        )

        assignments.grid(

            row=1, column=1, sticky="nsew",

            padx=(6, 0), pady=(0, 2)

        )

        self.mapping_list = ctk.CTkScrollableFrame(

            assignments, width=270, fg_color="transparent"

        )

        self.mapping_list.pack(

            fill="both", expand=True, padx=8, pady=(2, 10)

        )

        self.refresh_mapping_list()

        self.update_mapping_selection()

    def select_mapping_key(self, key):

        self.selected_mapping_key = key.lower()

        self.update_mapping_selection()

    def update_mapping_selection(self):

        if not hasattr(self, "mapping_key_buttons"):

            return

        mappings = self.key_mapping.list_mappings()

        for key, button in self.mapping_key_buttons.items():

            assigned = bool(mappings.get(key)) and mappings.get(key) in self.available_mapping_sounds()
            selected = key == self.selected_mapping_key
            if self.mode == "Custom Mode" and key == "enter" and not assigned:
                selected = False

            label = key.upper()

            # Assigned keys carry a marker even while selected, so selection

            # and saved state are never confused.

            if assigned:

                label = f"• {label}"

            button.configure(text=label)

            if selected:

                button.configure(

                    fg_color="#075985", hover_color="#0879A8",

                    border_color=WHITE if assigned else BLUE,

                    text_color=WHITE

                )

            elif assigned:

                button.configure(

                    fg_color="#102C43", hover_color="#17415F",

                    border_color=BLUE, text_color=BLUE

                )

            else:

                button.configure(

                    fg_color=PANEL_ALT, hover_color="#1B2D48",

                    border_color=BORDER, text_color=MUTED

                )

        if hasattr(self, "selected_key_title") and self.selected_key_title.winfo_exists():

            self.selected_key_title.configure(

                text=f"SELECTED KEY: {self.selected_mapping_key.upper()}"

            )

    def preview_selected_mapping_sound(self):

        if not hasattr(self, "mapping_sound_menu"):

            return

        filename = self.mapping_sound_menu.get()

        sound_path = self.available_mapping_sounds().get(filename)

        if sound_path is None:

            messagebox.showinfo("SoundKeys", "Choose an available sound first.", parent=self)

            return

        try:

            if not pygame.mixer.get_init():

                pygame.mixer.init()

            if self.preview_sound is not None:

                self.preview_sound.stop()

            self.preview_sound = pygame.mixer.Sound(str(sound_path))
            self.preview_sound.set_volume(self.master_volume)
            self.preview_sound.play()

        except Exception as error:

            messagebox.showerror("Preview Error", f"Could not preview this sound:\n\n{error}", parent=self)

    def refresh_mapping_list(self):

        if not hasattr(self, "mapping_list") or not self.mapping_list.winfo_exists():

            return

        for widget in self.mapping_list.winfo_children():

            widget.destroy()

        mappings = self.key_mapping.list_mappings()

        if not mappings:

            ctk.CTkLabel(

                self.mapping_list,

                text="No custom assignments yet.\nClick a key to get started!",

                text_color=MUTED, font=("Segoe UI", 11), justify="center"

            ).pack(pady=25)

        else:

            for key, filename in sorted(mappings.items()):

                row = ctk.CTkFrame(

                    self.mapping_list, fg_color=PANEL_ALT, corner_radius=7

                )

                row.pack(fill="x", padx=3, pady=3)

                ctk.CTkLabel(

                    row, text=key.upper(), width=48,

                    text_color=BLUE, font=("Consolas", 11, "bold")

                ).pack(side="left", padx=5, pady=9)

                ctk.CTkLabel(

                    row, text=filename, text_color=WHITE,

                    anchor="w", font=("Segoe UI", 9), wraplength=170

                ).pack(side="left", fill="x", expand=True, padx=3, pady=7)

                ctk.CTkButton(

                    row, text="×", width=28, height=27,

                    fg_color="#572038", hover_color="#842747",

                    command=lambda k=key: self.remove_key_mapping(k)

                ).pack(side="right", padx=5, pady=5)

        self.update_mapping_selection()

    def assign_selected_sound(self):

        if self.running:

            messagebox.showwarning(

                "SoundKeys", "Stop the engine before changing key mappings.",

                parent=self

            )

            return

        key = self.selected_mapping_key

        filename = self.mapping_sound_menu.get()

        try:

            self.key_mapping.assign(key, filename)

            self.refresh_mapping_list()

            messagebox.showinfo(

                "SoundKeys",

                f"Assigned '{filename}' to '{key.upper()}'.",

                parent=self

            )

        except Exception as error:

            messagebox.showerror("Mapping Error", str(error), parent=self)

    def remove_key_mapping(self, key):

        if self.running:

            messagebox.showwarning(

                "SoundKeys", "Stop the engine before changing key mappings.",

                parent=self

            )

            return

        try:

            removed = self.key_mapping.remove(key)

            self.refresh_mapping_list()

            if not removed:

                messagebox.showinfo(

                    "SoundKeys", f"No sound is assigned to {key.upper()}.",

                    parent=self

                )

        except Exception as error:

            messagebox.showerror("Mapping Error", str(error), parent=self)

    # ========================================================

    # ABOUT PAGE

    # ========================================================

    def build_about(self):
        # Reset grid settings left behind by Home / Key Mapping.
        # In particular, Key Mapping creates a weighted second column;
        # if it is not reset, the About panel can collapse to a narrow strip.
        self.page.grid_columnconfigure(0, weight=1, minsize=0, uniform="")
        self.page.grid_columnconfigure(1, weight=0, minsize=0, uniform="")
        self.page.grid_columnconfigure(2, weight=0, minsize=0, uniform="")

        self.page.grid_rowconfigure(0, weight=1, minsize=0, uniform="")
        self.page.grid_rowconfigure(1, weight=0, minsize=0, uniform="")
        self.page.grid_rowconfigure(2, weight=0, minsize=0, uniform="")

        panel = self.make_panel(
            self.page,
            "ABOUT SOUNDKEYS",
            "Your keyboard. Your sound. Your experience."
        )
        panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        panel.grid_columnconfigure(0, weight=1)

        # Branding
        ctk.CTkLabel(
            panel,
            text="〰  SOUNDKEYS",
            font=("Segoe UI", 30, "bold"),
            text_color=BLUE
        ).pack(pady=(18, 4))

        ctk.CTkLabel(
            panel,
            text="VERSION 1.0.0  •  CYBERPUNK EDITION",
            font=("Consolas", 11, "bold"),
            text_color=PURPLE
        ).pack(pady=5)

        ctk.CTkFrame(
            panel, height=2, fg_color=BORDER
        ).pack(fill="x", padx=30, pady=14)

        # Project description
        ctk.CTkLabel(
            panel,
            text="ABOUT THE PROJECT",
            font=("Segoe UI", 14, "bold"),
            text_color=BLUE
        ).pack(anchor="w", padx=30, pady=(5, 8))

        description = ctk.CTkLabel(
            panel,
            text=(
                "SoundKeys transforms ordinary keyboard presses into "
                "an interactive sound experience.\n\n"
                "Choose between Chaos Mode, Custom Mode and Mechanical "
                "Mode, import your own sounds, and personalize your "
                "typing experience."
            ),
            font=("Segoe UI", 13),
            text_color=WHITE,
            justify="left",
            anchor="w",
            wraplength=700
        )
        description.pack(fill="x", anchor="w", padx=30, pady=6)

        # Recalculate wrapping on resize, using the real inner panel width.
        def update_about_wrap(event=None):
            available_width = max(220, panel.winfo_width() - 90)
            description.configure(wraplength=available_width)

        panel.bind("<Configure>", update_about_wrap, add="+")
        panel.after(250, update_about_wrap)

        ctk.CTkFrame(
            panel, height=2, fg_color=BORDER
        ).pack(fill="x", padx=30, pady=14)

        # Developer credits
        ctk.CTkLabel(
            panel,
            text="DEVELOPED BY",
            font=("Segoe UI", 12, "bold"),
            text_color=MUTED
        ).pack(pady=(5, 3))

        ctk.CTkLabel(
            panel,
            text="HARSHIT SHARMA",
            font=("Segoe UI", 25, "bold"),
            text_color=PURPLE
        ).pack(pady=5)

        ctk.CTkLabel(
            panel,
            text="Creator & Developer of SoundKeys",
            font=("Segoe UI", 12),
            text_color=WHITE
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            panel,
            text="Built with Python  •  CustomTkinter  •  Pygame",
            font=("Consolas", 11),
            text_color=MUTED
        ).pack(pady=(4, 14))

        ctk.CTkFrame(panel, height=2, fg_color=BORDER).pack(fill="x", padx=30, pady=8)
        ctk.CTkLabel(panel, text="RELEASE TOOLS", font=("Segoe UI", 13, "bold"),
                     text_color=BLUE).pack(pady=(4, 8))
        tools_row = ctk.CTkFrame(panel, fg_color="transparent")
        tools_row.pack(fill="x", padx=30, pady=4)
        ctk.CTkButton(tools_row, text="BACK UP SETTINGS", command=self.export_backup,
                      fg_color=PANEL_ALT, hover_color="#183454", border_width=1,
                      border_color=BORDER).pack(side="left", padx=(0, 8))
        ctk.CTkButton(tools_row, text="RESTORE BACKUP", command=self.restore_backup,
                      fg_color=PANEL_ALT, hover_color="#183454", border_width=1,
                      border_color=BORDER).pack(side="left", padx=8)
        ctk.CTkButton(tools_row, text="AUDIO DIAGNOSTICS", command=self.run_audio_diagnostics,
                      fg_color=PANEL_ALT, hover_color="#183454", border_width=1,
                      border_color=BORDER).pack(side="left", padx=8)
        ctk.CTkButton(tools_row, text="TEST AUDIO", command=self.test_audio_output,
                      fg_color=PANEL_ALT, hover_color="#183454", border_width=1,
                      border_color=BORDER).pack(side="left", padx=8)
        startup_row = ctk.CTkFrame(panel, fg_color="transparent")
        startup_row.pack(fill="x", padx=30, pady=(8, 14))
        ctk.CTkLabel(startup_row, text="Launch SoundKeys when Windows starts",
                     text_color=WHITE, font=("Segoe UI", 12)).pack(side="left")
        self.startup_switch = ctk.CTkSwitch(startup_row, text="", command=lambda: self.set_startup_enabled(self.startup_switch.get()))
        self.startup_switch.pack(side="right")
        if self._startup_is_enabled(): self.startup_switch.select()

    def _make_tray_image(self):
        """Load the SoundKeys icon for the notification area."""
        from PIL import Image, ImageDraw

        icon_path = self._resource_path("SoundKeys.ico")
        if icon_path.exists():
            try:
                with Image.open(icon_path) as icon_image:
                    return icon_image.convert("RGBA").resize((64, 64))
            except Exception as error:
                print(f"Could not load tray icon asset: {error}")

        # Fallback keeps the tray available if the icon asset is missing.
        image = Image.new("RGBA", (64, 64), (7, 11, 22, 255))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle(
            (5, 5, 59, 59), radius=13, fill=(13, 21, 39, 255),
            outline=(0, 200, 255, 255), width=3
        )
        draw.line(
            (15, 34, 24, 34, 29, 19, 36, 46, 42, 29, 49, 29),
            fill=(0, 200, 255, 255), width=4
        )
        return image

    def _ensure_tray_icon(self):
        """Create and start the Windows notification-area icon once."""
        if self.tray_icon is not None:
            return True

        try:
            import pystray
            from pystray import MenuItem as Item

            menu = pystray.Menu(
                Item("Open SoundKeys", self._tray_open, default=True),
                Item("Start", self._tray_start),
                Item("Stop", self._tray_stop),
                Item("Mute / Unmute", self._tray_mute),
                pystray.Menu.SEPARATOR,
                Item("Exit SoundKeys", self._tray_exit),
            )

            self.tray_icon = pystray.Icon(
                "SoundKeys",
                self._make_tray_image(),
                "SoundKeys",
                menu=menu,
            )
            self.tray_icon.run_detached()
            self._tray_available = True
            return True

        except Exception as error:
            self.tray_icon = None
            self._tray_available = False
            messagebox.showerror(
                "SoundKeys - System Tray",
                "Could not start the system tray icon.\n\n"
                "Install the tray dependencies with:\n"
                "py -m pip install pystray Pillow\n\n"
                f"Details: {error}",
                parent=self,
            )
            return False

    def minimize_to_tray(self):
        """Hide the window while keeping the sound engine alive."""
        if self._closing:
            return

        if self._ensure_tray_icon():
            self.withdraw()
        else:
            # Keep the app accessible if tray support could not be initialized.
            self.iconify()

    def _restore_window(self):
        if self._closing:
            return
        self.deiconify()
        self.state("normal")
        self.lift()
        self.focus_force()

    def _run_from_tray(self, callback):
        """Marshal tray callbacks onto Tk's UI thread."""
        if self._closing:
            return
        try:
            self.after(0, callback)
        except Exception:
            pass

    def _tray_open(self, icon=None, item=None):
        self._run_from_tray(self._restore_window)

    def _tray_start(self, icon=None, item=None):
        self._run_from_tray(self.start_soundkeys)

    def _tray_stop(self, icon=None, item=None):
        self._run_from_tray(self.stop_soundkeys)

    def _tray_mute(self, icon=None, item=None):
        self._run_from_tray(self.toggle_mute)

    def _tray_exit(self, icon=None, item=None):
        self._run_from_tray(self.exit_app)

    # ========================================================

    # SHUTDOWN

    # ========================================================

    def close_app(self):
        """Backward-compatible close handler: closing hides the window."""
        self.minimize_to_tray()

    def exit_app(self):
        """Completely stop SoundKeys and release all resources."""
        if self._closing:
            return

        self._closing = True

        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception as error:
                print(f"Tray shutdown error: {error}")
            self.tray_icon = None

        if self.preview_sound is not None:
            try:
                self.preview_sound.stop()
            except Exception:
                pass
            self.preview_sound = None

        if self.engine is not None:
            try:
                self.engine.close()
            except Exception as error:
                print(f"Shutdown error: {error}")
            self.engine = None

        self.destroy()

if __name__ == "__main__":

    app = SoundKeysApp()

    app.mainloop()
