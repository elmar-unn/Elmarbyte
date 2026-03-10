import tkinter as tk
from tkinter import ttk

from database import Database
from ui.library_view import LibraryView


class AnimatedNavButton(tk.Label):
    # animeeritud vasaku menüü nupp
    def __init__(self, parent, text, command, colors, selected=False):
        super().__init__(
            parent,
            text=text,
            bg=colors["sidebar_selected"] if selected else colors["sidebar"],
            fg=colors["text"],
            font=("Segoe UI", 11, "bold"),
            padx=18,
            pady=12,
            anchor="w",
            cursor="hand2",
        )

        # oleku väljad
        self.colors = colors
        self.command = command
        self.selected = selected
        self._job = None

        # hiire sündmused
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda e: self.command())

    # valitud oleku muutus
    def set_selected(self, value: bool):
        self.selected = value
        self.configure(
            bg=self.colors["sidebar_selected"] if value else self.colors["sidebar"]
        )

    # hover sisse
    def _on_enter(self, _event=None):
        if self.selected:
            return
        self._animate_bg(self.cget("bg"), self.colors["sidebar_hover"], 8)

    # hover välja
    def _on_leave(self, _event=None):
        if self.selected:
            return
        self._animate_bg(self.cget("bg"), self.colors["sidebar"], 8)

    # sujuv taustavärvi animatsioon
    def _animate_bg(self, start_hex: str, end_hex: str, steps: int):
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass

        # heks -> rgb
        def hex_to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

        # rgb -> heks
        def rgb_to_hex(rgb):
            return "#{:02x}{:02x}{:02x}".format(*rgb)

        start = hex_to_rgb(start_hex)
        end = hex_to_rgb(end_hex)

        # üks animatsiooni samm
        def step(i=0):
            t = i / max(steps, 1)
            rgb = tuple(int(start[j] + (end[j] - start[j]) * t) for j in range(3))
            self.configure(bg=rgb_to_hex(rgb))
            if i < steps:
                self._job = self.after(14, lambda: step(i + 1))

        step()


class ElmarbyteApp:
    # põhiäpi klass
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Elmarbyte")
        self.root.geometry("1600x940")
        self.root.minsize(1280, 760)

        # andmebaas
        self.db = Database()

        # teemavärvid
        self.colors = self._configure_theme()

        # root paigutus
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # vasak külgriba
        self.sidebar = tk.Frame(self.root, bg=self.colors["sidebar"], width=240)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        # põhisisu ala
        self.content = tk.Frame(self.root, bg=self.colors["bg"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        # vaadete hoidjad
        self.views = {}
        self.current_view = None
        self.nav_buttons = {}

        # UI loomine
        self._build_sidebar()
        self._build_views()

        # ava kohe library
        self.show_view("library")

    # ttk teema seadistus
    def _configure_theme(self):
        style = ttk.Style()
        style.theme_use("clam")

        # värvipalett
        colors = {
            "bg": "#0b1220",
            "sidebar": "#0f1726",
            "sidebar_hover": "#172338",
            "sidebar_selected": "#1f3150",
            "panel": "#121c2d",
            "card": "#182437",
            "card_hover": "#233552",
            "card_selected": "#2a4166",
            "accent": "#56b7ff",
            "accent_hover": "#79c6ff",
            "text": "#eef4ff",
            "muted": "#8ea2bd",
            "border": "#29405f",
            "danger": "#d96565",
            "input": "#10192a",
            "placeholder": "#0c1522",
        }

        # root taust
        self.root.configure(bg=colors["bg"])

        # üldteema
        style.configure(
            ".",
            background=colors["bg"],
            foreground=colors["text"],
            fieldbackground=colors["input"],
            bordercolor=colors["border"],
            lightcolor=colors["bg"],
            darkcolor=colors["bg"],
            troughcolor=colors["panel"],
            arrowcolor=colors["text"],
        )

        # frame stiilid
        style.configure("TFrame", background=colors["bg"])
        style.configure("Card.TFrame", background=colors["card"])
        style.configure("Panel.TFrame", background=colors["panel"])

        # tekstistiilid
        style.configure("TLabel", background=colors["bg"], foreground=colors["text"], font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=colors["bg"], foreground=colors["muted"])
        style.configure("Title.TLabel", background=colors["bg"], foreground=colors["text"], font=("Segoe UI", 22, "bold"))
        style.configure("Heading.TLabel", background=colors["bg"], foreground=colors["text"], font=("Segoe UI", 13, "bold"))

        # nupud
        style.configure("TButton", background=colors["panel"], foreground=colors["text"], padding=(10, 8), borderwidth=0)
        style.map(
            "TButton",
            background=[("active", colors["card_hover"]), ("pressed", colors["card_selected"])],
            foreground=[("active", colors["text"]), ("pressed", "#ffffff")],
        )

        # primaarne nupp
        style.configure("Accent.TButton", background=colors["accent"], foreground="#ffffff", padding=(10, 8), borderwidth=0)
        style.map(
            "Accent.TButton",
            background=[("active", colors["accent_hover"]), ("pressed", "#3a9ee7")],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
        )

        # danger nupp
        style.configure("Danger.TButton", background=colors["danger"], foreground="#ffffff", padding=(10, 8), borderwidth=0)
        style.map(
            "Danger.TButton",
            background=[("active", "#e57a7a"), ("pressed", "#c45454")],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
        )

        # sisestusväljad
        style.configure("TEntry", fieldbackground=colors["input"], foreground=colors["text"], insertcolor=colors["text"], padding=8)
        style.configure("TCombobox", fieldbackground=colors["input"], foreground=colors["text"], padding=8, arrowsize=14)
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", colors["input"])],
            foreground=[("readonly", colors["text"])],
            selectbackground=[("readonly", colors["accent"])],
            selectforeground=[("readonly", "#ffffff")],
        )

        # tabeli stiil
        style.configure("Treeview", background=colors["panel"], fieldbackground=colors["panel"], foreground=colors["text"], rowheight=34)
        style.map("Treeview", background=[("selected", colors["accent"])], foreground=[("selected", "#ffffff")])
        style.configure("Treeview.Heading", background=colors["card"], foreground=colors["text"], font=("Segoe UI", 10, "bold"), padding=10, relief="flat")
        style.map("Treeview.Heading", background=[("active", colors["card_hover"])])

        return colors

    # vasaku menüü loomine
    def _build_sidebar(self):
        # logo
        tk.Label(
            self.sidebar,
            text="Elmarbyte",
            bg=self.colors["sidebar"],
            fg=self.colors["text"],
            font=("Segoe UI", 24, "bold"),
            pady=22,
        ).pack(fill="x")

        # alatekst
        tk.Label(
            self.sidebar,
            text="launcher + library",
            bg=self.colors["sidebar"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
            pady=4,
        ).pack(fill="x")

        # menüü elemendid
        items = [
            ("library", "Library"),
        ]

        # nuppude loomine
        for key, label in items:
            btn = AnimatedNavButton(
                self.sidebar,
                text=label,
                command=lambda k=key: self.show_view(k),
                colors=self.colors,
            )
            btn.pack(fill="x", padx=12, pady=4)
            self.nav_buttons[key] = btn

        # tühi ruum
        tk.Frame(self.sidebar, bg=self.colors["sidebar"]).pack(fill="both", expand=True)


    # vaadete loomine
    def _build_views(self):
        self.views["library"] = LibraryView(
            self.content,
            self.db,
            self.colors,
            on_data_changed=self.refresh_all,
        )

        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

    # aktiivse vaate vahetus
    def show_view(self, name: str):
        if self.current_view:
            self.views[self.current_view].grid_remove()

        self.current_view = name
        self.views[name].grid()
        self.views[name].refresh()

        for key, btn in self.nav_buttons.items():
            btn.set_selected(key == name)

    # kõigi vaadete refresh
    def refresh_all(self):
        for view in self.views.values():
            view.refresh()


def main():
    # programmi käivitus
    root = tk.Tk()
    ElmarbyteApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()