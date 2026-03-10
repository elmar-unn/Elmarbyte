import tkinter as tk
from tkinter import ttk

from database import Database
from ui.dashboard_view import DashboardView
from ui.library_view import LibraryView


class GameVaultApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GameVault Stage 8")
        self.root.geometry("1440x840")
        self.root.minsize(1200, 720)

        self.db = Database()
        self.colors = self._configure_theme()

        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.sidebar = tk.Frame(self.root, bg=self.colors["sidebar"], width=240)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        self.content = tk.Frame(self.root, bg=self.colors["bg"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        self.views = {}
        self.current_view = None
        self.nav_buttons = {}

        self._build_sidebar()
        self._build_views()
        self.show_view("dashboard")

    def _configure_theme(self):
        style = ttk.Style()
        style.theme_use("clam")

        colors = {
            "bg": "#0f141a",
            "sidebar": "#151d26",
            "panel": "#1b2430",
            "card": "#222d3a",
            "card2": "#253244",
            "accent": "#5da9ff",
            "accent_hover": "#7bbbff",
            "text": "#f4f7fb",
            "muted": "#9fb0c3",
            "border": "#324154",
            "danger": "#d96b6b",
            "input": "#18212c",
            "selected": "#2f4563",
            "placeholder": "#121821",
        }

        self.root.configure(bg=colors["bg"])

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

        style.configure("TFrame", background=colors["bg"])
        style.configure("Panel.TFrame", background=colors["panel"])
        style.configure("Card.TFrame", background=colors["card"])
        style.configure("Card2.TFrame", background=colors["card2"])

        style.configure(
            "TLabel",
            background=colors["bg"],
            foreground=colors["text"],
            font=("Segoe UI", 10),
        )
        style.configure("Muted.TLabel", background=colors["bg"], foreground=colors["muted"])
        style.configure("Title.TLabel", background=colors["bg"], foreground=colors["text"], font=("Segoe UI", 22, "bold"))
        style.configure("Heading.TLabel", background=colors["bg"], foreground=colors["text"], font=("Segoe UI", 13, "bold"))
        style.configure("CardTitle.TLabel", background=colors["card"], foreground=colors["muted"], font=("Segoe UI", 10))
        style.configure("CardValue.TLabel", background=colors["card"], foreground=colors["text"], font=("Segoe UI", 24, "bold"))
        style.configure("CardText.TLabel", background=colors["card"], foreground=colors["text"])

        style.configure(
            "TButton",
            background=colors["panel"],
            foreground=colors["text"],
            padding=(10, 8),
            borderwidth=0,
            focusthickness=0,
        )
        style.map(
            "TButton",
            background=[("active", colors["card2"]), ("pressed", colors["selected"])],
            foreground=[("active", colors["text"]), ("pressed", "#ffffff")],
        )

        style.configure(
            "Accent.TButton",
            background=colors["accent"],
            foreground="#ffffff",
            padding=(10, 8),
            borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[("active", colors["accent_hover"]), ("pressed", "#3b8eea")],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
        )

        style.configure(
            "Danger.TButton",
            background=colors["danger"],
            foreground="#ffffff",
            padding=(10, 8),
            borderwidth=0,
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#e47d7d"), ("pressed", "#c85d5d")],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
        )

        style.configure(
            "TEntry",
            fieldbackground=colors["input"],
            foreground=colors["text"],
            insertcolor=colors["text"],
            padding=8,
            bordercolor=colors["border"],
        )

        style.configure(
            "TCombobox",
            fieldbackground=colors["input"],
            foreground=colors["text"],
            padding=8,
            bordercolor=colors["border"],
            arrowsize=14,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", colors["input"])],
            foreground=[("readonly", colors["text"])],
            selectbackground=[("readonly", colors["accent"])],
            selectforeground=[("readonly", "#ffffff")],
        )

        style.configure(
            "Treeview",
            background=colors["panel"],
            fieldbackground=colors["panel"],
            foreground=colors["text"],
            bordercolor=colors["border"],
            rowheight=34,
        )
        style.map(
            "Treeview",
            background=[("selected", colors["accent"])],
            foreground=[("selected", "#ffffff")],
        )

        style.configure(
            "Treeview.Heading",
            background=colors["card"],
            foreground=colors["text"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
            padding=10,
        )
        style.map(
            "Treeview.Heading",
            background=[("active", colors["card2"])],
            foreground=[("active", "#ffffff")],
        )

        return colors

    def _build_sidebar(self):
        tk.Label(
            self.sidebar,
            text="GameVault",
            bg=self.colors["sidebar"],
            fg=self.colors["text"],
            font=("Segoe UI", 24, "bold"),
            pady=22,
        ).pack(fill="x")

        tk.Label(
            self.sidebar,
            text="Library + launcher",
            bg=self.colors["sidebar"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
            pady=4,
        ).pack(fill="x")

        items = [
            ("dashboard", "Dashboard"),
            ("library", "Library"),
        ]

        for key, label in items:
            btn = tk.Button(
                self.sidebar,
                text=label,
                anchor="w",
                relief="flat",
                bd=0,
                padx=22,
                pady=14,
                bg=self.colors["sidebar"],
                fg="#dbe6f2",
                activebackground=self.colors["selected"],
                activeforeground="#ffffff",
                font=("Segoe UI", 11, "bold"),
                command=lambda k=key: self.show_view(k),
            )
            btn.pack(fill="x", padx=10, pady=4)
            self.nav_buttons[key] = btn

        tk.Frame(self.sidebar, bg=self.colors["sidebar"]).pack(fill="both", expand=True)

        tk.Label(
            self.sidebar,
            text="Windows EXE launch supported",
            bg=self.colors["sidebar"],
            fg="#7f95ac",
            font=("Segoe UI", 9),
            pady=16,
        ).pack(fill="x")

    def _build_views(self):
        self.views["dashboard"] = DashboardView(self.content, self.db, self.colors)
        self.views["library"] = LibraryView(self.content, self.db, self.colors, on_data_changed=self.refresh_all)

        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

    def show_view(self, name: str):
        if self.current_view:
            self.views[self.current_view].grid_remove()

        self.current_view = name
        self.views[name].grid()
        self.views[name].refresh()

        for key, btn in self.nav_buttons.items():
            if key == name:
                btn.configure(bg=self.colors["selected"], fg="#ffffff")
            else:
                btn.configure(bg=self.colors["sidebar"], fg="#dbe6f2")

    def refresh_all(self):
        for view in self.views.values():
            view.refresh()


def main():
    root = tk.Tk()
    GameVaultApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()