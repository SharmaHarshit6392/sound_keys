import threading
import tkinter.messagebox as messagebox
from tkinter import filedialog

import customtkinter as ctk

from sound_engine import SoundEngine
from sound_library import SoundLibrary


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
        self.preview_sound = None

        self._exit_requested = threading.Event()
        self._closing = False

        self.mode = "Chaos Mode"
        self.running = False
        self.muted = False
        self.active_page = "HOME"

        self.nav_buttons = {}

        self.title("SoundKeys | Cyberpunk Edition")
        self.geometry("1100x740")
        self.minsize(900, 650)
        self.configure(fg_color=BG)

        self.build_layout()
        self.show_page("HOME")

        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.after(150, self.sync_engine_status)

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
            ("MODE SETTINGS", "⚙"),
            ("SOUND LIBRARY", "♫"),
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
            "MODE SETTINGS": self.build_mode_settings,
            "SOUND LIBRARY": self.build_library,
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
        modes.grid_columnconfigure((0, 1), weight=1)

        self.mode_buttons = {}

        mode_options = [
            ("Chaos Mode", "Random sounds\non selected keys", PURPLE),
            ("Custom Mode", "Choose a sound\nfor each key", BLUE)
        ]

        for col, (name, desc, accent) in enumerate(mode_options):
            selected = self.mode == name

            button = ctk.CTkButton(
                modes,
                text=(
                    f"{'✦' if name == 'Chaos Mode' else '⌘'}\n\n"
                    f"{name.upper()}\n\n{desc}"
                ),
                height=105,
                corner_radius=12,
                border_width=1,
                border_color=accent if selected else BORDER,
                fg_color=(
                    ("#201638" if name == "Chaos Mode" else "#10283A")
                    if selected else PANEL_ALT
                ),
                hover_color="#202A45",
                text_color=WHITE,
                font=("Segoe UI", 12, "bold"),
                command=lambda chosen=name: self.select_mode(chosen)
            )
            button.grid(row=0, column=col, sticky="ew", padx=5)
            self.mode_buttons[name] = button

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

        keyboard_panel = self.make_panel(
            self.page,
            "04  /  KEYBOARD PREVIEW",
            "Chaos Mode uses A, S, D and SPACE. "
            "ENTER plays the dedicated sound."
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

        rows = [
            ["ESC", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["TAB", "A", "S", "D", "F", "G", "H", "J", "K", "L", "ENTER"],
            ["SHIFT", "Z", "X", "C", "V", "B", "N", "M", "←", "→"],
            ["CTRL", "ALT", "SPACE", "ALT", "CTRL"]
        ]

        active_keys = {"A", "S", "D", "SPACE", "ENTER"}

        for row_keys in rows:
            row_frame = ctk.CTkFrame(
                keyboard_frame,
                fg_color="transparent"
            )
            row_frame.pack(anchor="w", pady=2)

            for key in row_keys:
                active = key in active_keys
                width = (
                    100 if key == "SPACE"
                    else 48 if len(key) > 1
                    else 35
                )

                ctk.CTkLabel(
                    row_frame,
                    text=key,
                    width=width,
                    height=27,
                    corner_radius=5,
                    fg_color="#172A43" if active else "#101827",
                    text_color=BLUE if active else MUTED,
                    font=("Consolas", 9, "bold"),
                    border_width=1,
                    border_color=PURPLE if active else BORDER
                ).pack(side="left", padx=2)

    # ========================================================
    # MODE SELECTION
    # ========================================================

    def select_mode(self, mode):
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

    # ========================================================
    # ENGINE CONTROLS
    # ========================================================

    def start_soundkeys(self):
        if self.running:
            return

        try:
            if self.engine is None:
                self.engine = SoundEngine(
                    on_exit=self._request_exit
                )

            self.engine.start(mode=self.mode)

            # Preserve the user's mute preference when starting.
            if self.muted and not self.engine.muted:
                self.engine.toggle_mute()

            self.running = True
            self.muted = bool(self.engine.muted)

            self.update_status_widgets()

        except Exception as error:
            self.running = False
            self.update_status_widgets()

            print(f"SoundKeys error: {error}")

            messagebox.showerror(
                "SoundKeys Error",
                f"Could not start SoundKeys:\n\n{error}",
                parent=self
            )

    def stop_soundkeys(self):
        if self.engine is not None:
            try:
                self.engine.stop()
            except Exception as error:
                print(f"Stop error: {error}")

        self.running = False
        self.update_status_widgets()

    def toggle_mute(self):
        if self.engine is None:
            self.muted = not self.muted
        else:
            try:
                self.muted = bool(self.engine.toggle_mute())
            except Exception as error:
                print(f"Mute error: {error}")
                return

        self.update_mute_button()

    def update_mute_button(self):
        if hasattr(self, "mute_button"):
            self.mute_button.configure(
                text="🔇   UNMUTE" if self.muted else "🔊   MUTE"
            )

    def update_status_widgets(self):
        if hasattr(self, "status_text"):
            self.status_text.configure(
                text="RUNNING" if self.running else "STOPPED",
                text_color=GREEN if self.running else RED
            )

            self.status_detail.configure(
                text=(
                    f"{self.mode} • Keyboard detection active"
                    if self.running else "Keyboard detection stopped"
                )
            )

        self.sidebar_status.configure(
            text="● ONLINE" if self.running else "● OFFLINE",
            text_color=GREEN if self.running else RED
        )

        self.header_badge.configure(
            text="● RUNNING" if self.running else "● READY",
            text_color=GREEN if self.running else MUTED
        )

        # These widgets exist only while the Home page is displayed.
        if hasattr(self, "start_button") and self.start_button.winfo_exists():
            self.start_button.configure(
                state="disabled" if self.running else "normal"
            )

        if hasattr(self, "stop_button") and self.stop_button.winfo_exists():
            self.stop_button.configure(
                state="normal" if self.running else "disabled",
                text_color=WHITE if self.running else MUTED
            )

        self.update_mute_button()

    def _request_exit(self):
        """Signal the GUI thread to shut down safely."""
        self._exit_requested.set()

    def sync_engine_status(self):
        if self._closing:
            return

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

    # ========================================================
    # KEY MAPPING PAGE
    # ========================================================

    def build_key_mapping(self):
        self.page.grid_rowconfigure(0, weight=0)

        panel = self.make_panel(
            self.page,
            "KEY MAPPING",
            "Custom key assignments are configured in config.py for now."
        )
        panel.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            panel,
            text="Interactive key assignment can be added next.",
            text_color=MUTED,
            font=("Segoe UI", 12)
        ).pack(anchor="w", padx=16, pady=(0, 16))

    # ========================================================
    # ABOUT PAGE
    # ========================================================

    def build_about(self):
        self.page.grid_rowconfigure(0, weight=0)

        panel = self.make_panel(
            self.page,
            "ABOUT SOUNDKEYS",
            "Turn your keyboard into a soundboard."
        )
        panel.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            panel,
            text=(
                "Cyberpunk Edition • Desktop UI\n"
                "Built with Python and CustomTkinter"
            ),
            text_color=MUTED,
            font=("Segoe UI", 12),
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 16))

    # ========================================================
    # SHUTDOWN
    # ========================================================

    def close_app(self):
        if self._closing:
            return

        self._closing = True

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