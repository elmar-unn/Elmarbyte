import tkinter as tk
from tkinter import ttk


class DashboardView(ttk.Frame):
    def __init__(self, parent, db, colors):
        super().__init__(parent)
        self.db = db
        self.colors = colors

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 12))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Dashboard", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Overview of your game library.", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.cards = ttk.Frame(self)
        self.cards.grid(row=1, column=0, sticky="ew", padx=24, pady=12)

        for i in range(5):
            self.cards.columnconfigure(i, weight=1)

        self.total = self._card(self.cards, 0, "Total")
        self.completed = self._card(self.cards, 1, "Completed")
        self.playing = self._card(self.cards, 2, "Playing")
        self.favorites = self._card(self.cards, 3, "Favorites")
        self.avg = self._card(self.cards, 4, "Avg rating")

        bottom = ttk.Frame(self)
        bottom.grid(row=2, column=0, sticky="nsew", padx=24, pady=(10, 24))
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)
        bottom.rowconfigure(0, weight=1)

        self.top_frame = ttk.Frame(bottom, style="Card.TFrame", padding=18)
        self.top_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ttk.Label(self.top_frame, text="Top rated game", style="Heading.TLabel").pack(anchor="w")
        self.top_label = tk.Label(self.top_frame, text="-", bg=colors["card"], fg=colors["text"], font=("Segoe UI", 18, "bold"))
        self.top_label.pack(anchor="w", pady=(16, 8))

        self.breakdown_frame = ttk.Frame(bottom, style="Card.TFrame", padding=18)
        self.breakdown_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ttk.Label(self.breakdown_frame, text="Status breakdown", style="Heading.TLabel").pack(anchor="w")
        self.breakdown_rows = tk.Frame(self.breakdown_frame, bg=colors["card"])
        self.breakdown_rows.pack(fill="both", expand=True, pady=(12, 0))

        self.refresh()

    def _card(self, parent, col, title):
        frame = ttk.Frame(parent, style="Card.TFrame", padding=16)
        frame.grid(row=0, column=col, sticky="nsew", padx=8)
        ttk.Label(frame, text=title, style="CardTitle.TLabel").pack(anchor="w")
        value = ttk.Label(frame, text="0", style="CardValue.TLabel")
        value.pack(anchor="w", pady=(8, 0))
        return value

    def refresh(self):
        stats = self.db.get_stats()
        self.total.config(text=str(stats["total"]))
        self.completed.config(text=str(stats["completed"]))
        self.playing.config(text=str(stats["playing"]))
        self.favorites.config(text=str(stats["favorites"]))
        self.avg.config(text=str(stats["avg_rating"]))
        self.top_label.config(text=stats["top_game"])

        for w in self.breakdown_rows.winfo_children():
            w.destroy()

        for status, count in stats["status_breakdown"]:
            row = tk.Frame(self.breakdown_rows, bg=self.colors["card"])
            row.pack(fill="x", pady=6)
            tk.Label(row, text=status, bg=self.colors["card"], fg=self.colors["text"], font=("Segoe UI", 11, "bold")).pack(side="left")
            tk.Label(row, text=str(count), bg=self.colors["card"], fg=self.colors["muted"], font=("Segoe UI", 11)).pack(side="right")