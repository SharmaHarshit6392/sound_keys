import customtkinter as ctk
import threading
from sound_engine import SoundEngine

# ==========================================
# SOUNDKEYS — CYBERPUNK GAMING DASHBOARD
# ==========================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#070B16"
SIDEBAR = "#0A1020"
PANEL = "#0D1527"
PANEL_ALT = "#111D33"
BORDER = "#20395A"
BLUE = "#00C8FF"
PURPLE = "#A855F7"
PINK = "#F43FCE"
WHITE = "#EAF4FF"
MUTED = "#8295B4"
GREEN = "#31F7A1"
RED = "#FF4778"


class SoundKeysApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.engine = None
        self.engine_thread = None

        self.title("SoundKeys | Cyberpunk Edition")
        self.geometry("1100x740")
        self.minsize(900, 650)
        self.configure(fg_color=BG)

        self.mode = "Chaos Mode"
        self.running = False
        self.muted = False
        self.active_page = "HOME"

        self.build_layout()
        self.show_page("HOME")
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.after(150, self.sync_engine_status)

    # ======================================
    # LAYOUT
    # ======================================

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
            border_color=BORDER,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="〰",
            font=("Segoe UI", 48, "bold"),
            text_color=BLUE,
        ).pack(pady=(25, 0))

        ctk.CTkLabel(
            self.sidebar,
            text="SOUNDKEYS",
            font=("Segoe UI", 21, "bold"),
            text_color=WHITE,
        ).pack(pady=(0, 3))

        ctk.CTkLabel(
            self.sidebar,
            text="YOUR KEYBOARD. YOUR SOUND.",
            font=("Segoe UI", 8, "bold"),
            text_color=MUTED,
        ).pack(pady=(0, 28))

        self.nav_buttons = {}

        navigation = [
            ("HOME", "⌂"),
            ("MODE SETTINGS", "⚙"),
            ("SOUND LIBRARY", "♫"),
            ("KEY MAPPING", "⌨"),
            ("ABOUT", "ⓘ"),
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
                command=lambda page=name: self.show_page(page),
            )
            button.pack(fill="x", padx=12, pady=4)
            self.nav_buttons[name] = button

        ctk.CTkFrame(
            self.sidebar,
            height=2,
            fg_color=BORDER,
        ).pack(fill="x", padx=15, pady=(22, 12))

        ctk.CTkLabel(
            self.sidebar,
            text="SYSTEM STATUS",
            font=("Segoe UI", 10, "bold"),
            text_color=MUTED,
        ).pack(anchor="w", padx=20)

        self.sidebar_status = ctk.CTkLabel(
            self.sidebar,
            text="●  OFFLINE",
            font=("Segoe UI", 12, "bold"),
            text_color=RED,
        )
        self.sidebar_status.pack(anchor="w", padx=20, pady=(8, 0))

        ctk.CTkLabel(
            self.sidebar,
            text="SOUNDKEYS\nCYBERPUNK EDITION",
            justify="left",
            font=("Segoe UI", 10, "bold"),
            text_color=PURPLE,
        ).pack(side="bottom", anchor="w", padx=20, pady=22)

        # Main content area
        self.content = ctk.CTkFrame(
            self,
            fg_color=BG,
            corner_radius=0,
        )
        self.content.grid(row=0, column=1, sticky="nsew", padx=18, pady=15)

        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(
            self.content,
            fg_color="transparent",
        )
        header.grid(row=0, column=0, sticky="ew", pady=(3, 18))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="SOUNDKEYS  /  CONTROL CENTER",
            font=("Segoe UI", 19, "bold"),
            text_color=WHITE,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="DESKTOP EDITION  •  v0.1",
            font=("Consolas", 10),
            text_color=BLUE,
        ).grid(row=1, column=0, sticky="w", pady=(5, 0))

        self.header_badge = ctk.CTkLabel(
            header,
            text="●  READY",
            font=("Segoe UI", 11, "bold"),
            text_color=GREEN,
            fg_color=PANEL,
            corner_radius=8,
        )
        self.header_badge.grid(row=0, column=1, rowspan=2, padx=8, ipadx=12, ipady=8)

        # Swappable page
        self.page = ctk.CTkFrame(
            self.content,
            fg_color="transparent",
        )
        self.page.grid(row=1, column=0, sticky="nsew")
        self.page.grid_columnconfigure(0, weight=1)

def sync_engine_status(self):
    """Keep the GUI synchronized with the audio engine."""

    if self.engine is not None:
        actual_running = self.engine.running
        actual_muted = self.engine.muted

        if actual_running != self.running:
            self.running = actual_running

            if actual_running:
                self.status_text.configure(
                    text="RUNNING",
                    text_color=GREEN,
                )
                self.status_detail.configure(
                    text=f"{self.mode} • Keyboard detection active"
                )
                self.sidebar_status.configure(
                    text="● ONLINE",
                    text_color=GREEN,
                )
                self.header_badge.configure(
                    text="● RUNNING",
                    text_color=GREEN,
                )
                self.start_button.configure(state="disabled")
                self.stop_button.configure(
                    state="normal",
                    text_color=WHITE,
                )
            else:
                self.status_text.configure(
                    text="STOPPED",
                    text_color=RED,
                )
                self.status_detail.configure(
                    text="Keyboard detection stopped"
                )
                self.sidebar_status.configure(
                    text="● OFFLINE",
                    text_color=RED,
                )
                self.header_badge.configure(
                    text="● READY",
                    text_color=GREEN,
                )
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")

        if actual_muted != self.muted:
            self.muted = actual_muted
            self.mute_button.configure(
                text="🔇   UNMUTE" if actual_muted else "🔊   MUTE"
            )

    self.after(150, self.sync_engine_status)

    # ======================================
    # REUSABLE PANELS
    # ======================================

    def make_panel(self, parent, title, subtitle=None):
        panel = ctk.CTkFrame(
            parent,
            fg_color=PANEL,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )

        ctk.CTkLabel(
            panel,
            text=title,
            font=("Segoe UI", 12, "bold"),
            text_color=BLUE,
        ).pack(anchor="w", padx=16, pady=(14, 4))

        if subtitle:
            ctk.CTkLabel(
                panel,
                text=subtitle,
                font=("Segoe UI", 10),
                text_color=MUTED,
                wraplength=360,
                justify="left",
            ).pack(anchor="w", padx=16, pady=(0, 12))

        return panel

    def clear_page(self):
        for widget in self.page.winfo_children():
            widget.destroy()

    # ======================================
    # HOME PAGE
    # ======================================

    def show_page(self, page_name):
        self.active_page = page_name

        for name, button in self.nav_buttons.items():
            if name == page_name:
                button.configure(
                    fg_color="#132A46",
                    text_color=BLUE,
                )
            else:
                button.configure(
                    fg_color="transparent",
                    text_color=MUTED,
                )

        self.clear_page()

        if page_name == "HOME":
            self.build_home()
        elif page_name == "MODE SETTINGS":
            self.build_mode_settings()
        elif page_name == "SOUND LIBRARY":
            self.build_library()
        elif page_name == "KEY MAPPING":
            self.build_key_mapping()
        else:
            self.build_about()

    def build_home(self):
        self.page.grid_columnconfigure(0, weight=3)
        self.page.grid_columnconfigure(1, weight=2)

        # Mode selection
        mode_panel = self.make_panel(
            self.page,
            "01  /  SELECT YOUR MODE",
            "Choose how your keyboard triggers sound effects.",
        )
        mode_panel.grid(
            row=0, column=0, columnspan=2,
            sticky="ew", pady=(0, 12),
        )

        self.mode_buttons = {}

        modes = ctk.CTkFrame(mode_panel, fg_color="transparent")
        modes.pack(fill="x", padx=12, pady=(0, 14))
        modes.grid_columnconfigure((0, 1), weight=1)

        for column, (name, description, color) in enumerate([
            ("Chaos Mode", "Random sounds\non selected keys", PURPLE),
            ("Custom Mode", "Choose a sound\nfor each key", BLUE),
        ]):
            selected = self.mode == name

            button = ctk.CTkButton(
                modes,
                text=f"{'✦' if name == 'Chaos Mode' else '⌘'}\n\n"
                     f"{name.upper()}\n\n{description}",
                height=115,
                corner_radius=12,
                border_width=1,
                border_color=color if selected else BORDER,
                fg_color="#201638" if selected and name == "Chaos Mode"
                         else "#10283A" if selected
                         else PANEL_ALT,
                hover_color="#202A45",
                text_color=WHITE,
                font=("Segoe UI", 12, "bold"),
                command=lambda mode=name: self.select_mode(mode),
            )
            button.grid(
                row=0, column=column,
                sticky="ew", padx=5,
            )
            self.mode_buttons[name] = button

        # Status panel
        status_panel = self.make_panel(
            self.page,
            "02  /  ENGINE STATUS",
            "Current application state.",
        )
        status_panel.grid(
            row=1, column=0,
            sticky="nsew", padx=(0, 6), pady=(0, 12),
        )

        self.status_text = ctk.CTkLabel(
            status_panel,
            text="STOPPED",
            font=("Segoe UI", 28, "bold"),
            text_color=RED,
        )
        self.status_text.pack(pady=(12, 0))

        self.status_detail = ctk.CTkLabel(
            status_panel,
            text="Engine not connected yet",
            font=("Consolas", 10),
            text_color=MUTED,
        )
        self.status_detail.pack(pady=(3, 14))

        # Quick controls
        controls = self.make_panel(
            self.page,
            "03  /  QUICK CONTROLS",
            "Interface preview — engine integration comes next.",
        )
        controls.grid(
            row=1, column=1,
            sticky="nsew", padx=(6, 0), pady=(0, 12),
        )

        self.start_button = ctk.CTkButton(
            controls,
            text="▶   START",
            height=38,
            corner_radius=9,
            fg_color="#075985",
            hover_color="#0369A1",
            text_color=WHITE,
            font=("Segoe UI", 12, "bold"),
            command=self.start_soundkeys,
        )
        self.start_button.pack(fill="x", padx=14, pady=(12, 7))

        self.stop_button = ctk.CTkButton(
            controls,
            text="■   STOP",
            height=38,
            corner_radius=9,
            fg_color="#252D40",
            hover_color="#39445C",
            text_color=MUTED,
            font=("Segoe UI", 12, "bold"),
            state="disabled",
            command=self.stop_soundkeys,
        )
        self.stop_button.pack(fill="x", padx=14, pady=7)

        self.mute_button = ctk.CTkButton(
            controls,
            text="🔊   MUTE",
            height=38,
            corner_radius=9,
            fg_color="#24203A",
            hover_color="#3A2D58",
            text_color=WHITE,
            font=("Segoe UI", 12, "bold"),
            command=self.toggle_mute,
        )
        self.mute_button.pack(fill="x", padx=14, pady=(7, 14))

        # Keyboard preview
        keyboard_panel = self.make_panel(
            self.page,
            "04  /  KEYBOARD PREVIEW",
            "Current trigger keys are highlighted below.",
        )
        keyboard_panel.grid(
            row=2, column=0, columnspan=2,
            sticky="ew", pady=(0, 12),
        )

        keyboard_frame = ctk.CTkFrame(
            keyboard_panel,
            fg_color="transparent",
        )
        keyboard_frame.pack(fill="x", padx=12, pady=(0, 14))

        rows = [
            ["ESC", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["TAB", "A", "S", "D", "F", "G", "H", "J", "K", "L", "↵"],
            ["SHIFT", "Z", "X", "C", "V", "B", "N", "M", "←", "→"],
            ["CTRL", "ALT", "SPACE", "ALT", "CTRL"],
        ]

        active_keys = (
            {"A", "S", "D", "SPACE", "ENTER"}
            if self.mode == "Chaos Mode"
            else {"A", "S", "D", "SPACE", "ENTER"}
        )

        for row_index, row in enumerate(rows):
            row_frame = ctk.CTkFrame(
                keyboard_frame,
                fg_color="transparent",
            )
            row_frame.pack(fill="x", pady=3)

            for key in row:
                is_active = key in active_keys
                width = 100 if key == "SPACE" else 35 if len(key) == 1 else 48

                key_button = ctk.CTkLabel(
                    row_frame,
                    text=key,
                    width=width,
                    height=27,
                    corner_radius=5,
                    fg_color="#172A43" if is_active else "#101827",
                    text_color=BLUE if is_active else MUTED,
                    font=("Consolas", 9, "bold"),
                    border_width=1,
                    border_color=PURPLE if is_active else BORDER,
                )
                key_button.pack(side="left", padx=2)

    # ======================================
    # INTERACTION
    # ======================================

    def select_mode(self, mode):
        self.mode = mode
        print(f"Selected mode: {mode}")

        if self.active_page == "HOME":
            self.build_home()

    # ======================================
    # CONNECTED ENGINE CONTROLS
    # ======================================

    def start_soundkeys(self):
        if self.running:
            return

        try:
            if self.engine is None:
                self.engine = SoundEngine()

            self.engine.start(mode=self.mode)

            self.running = True

            self.status_text.configure(
                text="RUNNING",
                text_color=GREEN,
            )
            self.status_detail.configure(
                text=f"{self.mode} • Keyboard detection active"
            )
            self.sidebar_status.configure(
                text="●  ONLINE",
                text_color=GREEN,
            )
            self.header_badge.configure(
                text="●  RUNNING",
                text_color=GREEN,
            )

            self.start_button.configure(state="disabled")
            self.stop_button.configure(
                state="normal",
                text_color=WHITE,
            )

            print(f"{self.mode} activated.")

        except Exception as error:
            self.running = False

            self.status_text.configure(
                text="ERROR",
                text_color=RED,
            )
            self.status_detail.configure(
                text="Could not start the audio engine."
            )

            print(f"SoundKeys error: {error}")

            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "SoundKeys Error",
                f"Could not start SoundKeys:\n\n{error}",
            )

def stop(self):
    """Disable keyboard detection and stop all active sounds."""

    with self._lock:
        self.running = False

        hook = self._hook
        self._hook = None

        if hook is not None:
            keyboard.unhook(hook)

        pygame.mixer.stop()

    print("SoundKeys stopped.")

    if self._on_status_change:
        self._on_status_change(False)

def toggle_mute(self):
    """Toggle audio mute."""

    with self._lock:
        self.muted = not self.muted

        if self.muted:
            pygame.mixer.stop()

        current_state = self.muted

    print("SoundKeys MUTED" if current_state else "SoundKeys UNMUTED")

    return current_state
    def close_app(self):
        if self.engine is not None:
            self.engine.close()
            self.engine = None

        self.destroy()        

    # ======================================
    # OTHER PAGES
    # ======================================

    def build_mode_settings(self):
        panel = self.make_panel(
            self.page,
            "MODE SETTINGS",
            "Select a mode from the controls below.",
        )
        panel.grid(row=0, column=0, sticky="ew")

        for mode in ["Chaos Mode", "Custom Mode"]:
            ctk.CTkButton(
                panel,
                text=mode,
                height=42,
                fg_color="#10283A" if self.mode == mode else PANEL_ALT,
                hover_color="#1D3C5B",
                command=lambda selected=mode: self.select_mode(selected),
            ).pack(fill="x", padx=16, pady=7)

    def build_library(self):
        panel = self.make_panel(
            self.page,
            "SOUND LIBRARY",
            "Your audio library is stored in sounds/chaos.",
        )
        panel.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            panel,
            text="MP3 library integration is coming next.",
            text_color=MUTED,
            font=("Segoe UI", 12),
        ).pack(anchor="w", padx=16, pady=(0, 16))

    def build_key_mapping(self):
        panel = self.make_panel(
            self.page,
            "KEY MAPPING",
            "Custom key assignments are configured in config.py for now.",
        )
        panel.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            panel,
            text="Interactive key assignment is coming next.",
            text_color=MUTED,
            font=("Segoe UI", 12),
        ).pack(anchor="w", padx=16, pady=(0, 16))

    def build_about(self):
        panel = self.make_panel(
            self.page,
            "ABOUT SOUNDKEYS",
            "Turn your keyboard into a soundboard.",
        )
        panel.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            panel,
            text="Cyberpunk Edition • Desktop UI Preview\n"
                 "Built with Python and CustomTkinter",
            text_color=MUTED,
            font=("Segoe UI", 12),
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 16))


if __name__ == "__main__":
    app = SoundKeysApp()
    app.mainloop()