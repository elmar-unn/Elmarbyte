import json
import os
import shutil
import webbrowser
import tkinter as tk
from configparser import ConfigParser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    # pilditugi
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class AnimatedActionButton(tk.Label):
    # animeeritud ülariba nupp
    def __init__(self, parent, text, command, colors, primary=False, width=10):
        self.colors = colors
        self.primary = primary

        # nuppude värvid
        bg = colors["accent"] if primary else colors["panel"]
        hover = colors["accent_hover"] if primary else colors["card_hover"]

        super().__init__(
            parent,
            text=text,
            bg=bg,
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=10,
            cursor="hand2",
            width=width,
        )

        # callback
        self.command = command
        self.base_bg = bg
        self.hover_bg = hover

        # hiire sündmused
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda e: self.command())

    # heks -> rgb
    def _hex_to_rgb(self, h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    # rgb -> heks
    def _rgb_to_hex(self, rgb):
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    # värvianimatsioon
    def _animate_color(self, start, end, steps=8):
        s = self._hex_to_rgb(start)
        e = self._hex_to_rgb(end)

        def step(i=0):
            t = i / max(steps, 1)
            rgb = tuple(int(s[j] + (e[j] - s[j]) * t) for j in range(3))
            self.configure(bg=self._rgb_to_hex(rgb))
            if i < steps:
                self.after(12, lambda: step(i + 1))

        step()

    # hover sisse
    def _on_enter(self, _event=None):
        self.configure(padx=18, pady=11)
        self._animate_color(self.cget("bg"), self.hover_bg)

    # hover välja
    def _on_leave(self, _event=None):
        self.configure(padx=14, pady=10)
        self._animate_color(self.cget("bg"), self.base_bg)


class HoverCard(tk.Frame):
    # grid kaardi widget
    def __init__(self, parent, colors, selected=False, **kwargs):
        self.colors = colors

        # algvärv
        bg = colors["card_selected"] if selected else colors["panel"]
        border = colors["accent"] if selected else colors["border"]

        super().__init__(
            parent,
            bg=bg,
            highlightbackground=border,
            highlightthickness=2 if selected else 1,
            bd=0,
            padx=12,
            pady=12,
            **kwargs
        )

        self.selected = selected

    # valitud olek
    def set_selected(self, selected: bool):
        self.selected = selected
        self.configure(
            bg=self.colors["card_selected"] if selected else self.colors["panel"],
            highlightbackground=self.colors["accent"] if selected else self.colors["border"],
            highlightthickness=2 if selected else 1,
        )

    # hover sees
    def hover_on(self):
        if self.selected:
            return
        self.configure(
            bg=self.colors["card_hover"],
            highlightbackground=self.colors["accent"],
            highlightthickness=2,
        )

    # hover väljas
    def hover_off(self):
        if self.selected:
            return
        self.configure(
            bg=self.colors["panel"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )


class LibraryView(ttk.Frame):
    # library põhivaade
    def __init__(self, parent, db, colors, on_data_changed=None):
        super().__init__(parent)

        # sõltuvused
        self.db = db
        self.colors = colors
        self.on_data_changed = on_data_changed

        # olekumuutujad
        self.selected_game_id = None
        self.view_mode = tk.StringVar(value="grid")
        self.search_var = tk.StringVar()
        self.platform_var = tk.StringVar(value="All")
        self.genre_var = tk.StringVar(value="All")
        self.status_var = tk.StringVar(value="All")
        self.favorites_only_var = tk.BooleanVar(value=False)

        # layout
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # ehita UI
        self._build_header()
        self._build_filters()
        self._build_main_area()

        # algandmed
        self.refresh()

    # ülariba
    def _build_header(self):
        header = ttk.Frame(self)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(20, 12))
        header.columnconfigure(0, weight=1)

        # vasak pealkiri
        left = ttk.Frame(header)
        left.grid(row=0, column=0, sticky="w")
        ttk.Label(left, text="Library", style="Title.TLabel").pack(anchor="w")
        ttk.Label(left, text="Halda mänge, covereid ja launchereid.", style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

        # parem nupurida
        right = ttk.Frame(header)
        right.grid(row=0, column=1, sticky="e")

        # otsingukast
        search_wrap = tk.Frame(right, bg=self.colors["input"], highlightbackground=self.colors["border"], highlightthickness=1)
        search_wrap.pack(side="left", padx=(0, 12))

        # otsingu ikoon
        search_icon = tk.Label(
            search_wrap,
            text="⌕",
            bg=self.colors["input"],
            fg=self.colors["muted"],
            font=("Segoe UI", 11, "bold"),
            padx=8,
        )
        search_icon.pack(side="left")

        # otsingu väli
        self.top_search_entry = tk.Entry(
            search_wrap,
            textvariable=self.search_var,
            bg=self.colors["input"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            bd=0,
            width=28,
            font=("Segoe UI", 11),
        )
        self.top_search_entry.pack(side="left", padx=(0, 8), pady=8)
        self.top_search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        # view toggle
        ttk.Button(right, text="List", command=lambda: self._set_view("list")).pack(side="left", padx=4)
        ttk.Button(right, text="Grid", command=lambda: self._set_view("grid")).pack(side="left", padx=4)

        # play nupp
        self.launch_button = AnimatedActionButton(
            right,
            "Play",
            self.launch_selected,
            self.colors,
            primary=True,
            width=9
        )
        self.launch_button.pack(side="left", padx=(12, 6))

        # add game nupp
        self.add_button = AnimatedActionButton(
            right,
            "Add Game",
            self.open_add_dialog,
            self.colors,
            primary=False,
            width=10
        )
        self.add_button.pack(side="left", padx=(6, 6))

        # steam import nupp
        self.import_steam_button = AnimatedActionButton(
            right,
            "Import Steam",
            self.import_steam_shortcuts,
            self.colors,
            primary=False,
            width=11
        )
        self.import_steam_button.pack(side="left", padx=(6, 6))

        # epic import nupp
        self.import_epic_button = AnimatedActionButton(
            right,
            "Import Epic",
            self.import_epic_installs,
            self.colors,
            primary=False,
            width=10
        )
        self.import_epic_button.pack(side="left", padx=(6, 0))

    # vasak filterpaneel
    def _build_filters(self):
        side = ttk.Frame(self, style="Card.TFrame", padding=18)
        side.grid(row=1, column=0, sticky="ns", padx=(24, 12), pady=(0, 24))
        side.configure(width=330)

        # filtrite pealkiri
        ttk.Label(side, text="Search & filters", style="Heading.TLabel").pack(anchor="w", pady=(0, 12))

        # otsing
        ttk.Label(side, text="Search").pack(anchor="w")
        entry = ttk.Entry(side, textvariable=self.search_var)
        entry.pack(fill="x", pady=(4, 12))
        entry.bind("<KeyRelease>", lambda e: self.refresh())

        # platvorm
        ttk.Label(side, text="Platform").pack(anchor="w")
        self.platform_combo = ttk.Combobox(side, textvariable=self.platform_var, state="readonly")
        self.platform_combo.pack(fill="x", pady=(4, 12))
        self.platform_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # žanr
        ttk.Label(side, text="Genre").pack(anchor="w")
        self.genre_combo = ttk.Combobox(side, textvariable=self.genre_var, state="readonly")
        self.genre_combo.pack(fill="x", pady=(4, 12))
        self.genre_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # staatus
        ttk.Label(side, text="Status").pack(anchor="w")
        self.status_combo = ttk.Combobox(side, textvariable=self.status_var, state="readonly")
        self.status_combo.pack(fill="x", pady=(4, 12))
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # favoriit checkbox
        ttk.Checkbutton(side, text="Favorites only", variable=self.favorites_only_var, command=self.refresh).pack(anchor="w", pady=(6, 10))

        # reset nupp
        ttk.Button(side, text="Reset filters", command=self.reset_filters).pack(fill="x", pady=(0, 14))

        # eraldaja
        ttk.Separator(side).pack(fill="x", pady=12)

        # detaili pealkiri
        ttk.Label(side, text="Selected game", style="Heading.TLabel").pack(anchor="w", pady=(0, 12))

        # detaili sisu
        self.detail_wrap = tk.Frame(side, bg=self.colors["card"])
        self.detail_wrap.pack(fill="both", expand=True)

        # cover eelvaade
        self.cover_label = tk.Label(
            self.detail_wrap,
            text="No cover",
            bg=self.colors["placeholder"],
            fg=self.colors["muted"],
            width=26,
            height=12,
        )
        self.cover_label.pack(fill="x", pady=(0, 12))

        # mängu nimi
        self.detail_title = tk.Label(
            self.detail_wrap,
            text="Nothing selected",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 15, "bold"),
            wraplength=280,
            justify="left",
        )
        self.detail_title.pack(anchor="w")

        # metainfo
        self.detail_meta = tk.Label(
            self.detail_wrap,
            text="",
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
            justify="left",
            wraplength=280,
        )
        self.detail_meta.pack(anchor="w", pady=(8, 10))

        # launcher info
        self.detail_launcher = tk.Label(
            self.detail_wrap,
            text="",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 9),
            justify="left",
            wraplength=280,
        )
        self.detail_launcher.pack(anchor="w", pady=(0, 10))

        # notes
        self.detail_notes = tk.Label(
            self.detail_wrap,
            text="Select a game to see details.",
            bg=self.colors["card"],
            fg=self.colors["text"],
            justify="left",
            wraplength=280,
        )
        self.detail_notes.pack(anchor="w")

        # edit/delete nupud
        actions = ttk.Frame(side)
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="Edit", command=self.open_edit_dialog).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(actions, text="Delete", style="Danger.TButton", command=self.delete_selected).pack(side="left", expand=True, fill="x", padx=(4, 0))

    # põhipaneeli loomine
    def _build_main_area(self):
        container = ttk.Frame(self, style="Card.TFrame")
        container.grid(row=1, column=1, sticky="nsew", padx=(12, 24), pady=(0, 24))
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # vaadete stack
        self.stack = ttk.Frame(container)
        self.stack.grid(row=0, column=0, sticky="nsew")
        self.stack.rowconfigure(0, weight=1)
        self.stack.columnconfigure(0, weight=1)

        # mõlemad vaated
        self._build_list_view()
        self._build_grid_view()

    # tabelivaade
    def _build_list_view(self):
        frame = ttk.Frame(self.stack)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # veerud
        cols = ("title", "platform", "genre", "rating", "status", "favorite", "launcher")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings")

        # pealkirjad
        headings = {
            "title": "Title",
            "platform": "Platform",
            "genre": "Genre",
            "rating": "Rating",
            "status": "Status",
            "favorite": "★",
            "launcher": "Launcher",
        }

        for col in cols:
            self.tree.heading(col, text=headings[col])

        # laiused
        self.tree.column("title", width=300)
        self.tree.column("platform", width=100)
        self.tree.column("genre", width=130)
        self.tree.column("rating", width=80, anchor="center")
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("favorite", width=50, anchor="center")
        self.tree.column("launcher", width=120, anchor="center")

        # tree + scrollbar
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # select event
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        self.list_frame = frame

    # grid vaade
    def _build_grid_view(self):
        frame = ttk.Frame(self.stack)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # canvas + scrollbar
        self.grid_canvas = tk.Canvas(frame, bg=self.colors["card"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.grid_canvas.yview)
        self.grid_inner = tk.Frame(self.grid_canvas, bg=self.colors["card"])

        # scrollregion uuendus
        self.grid_inner.bind(
            "<Configure>",
            lambda e: self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
        )

        # frame canvas sisse
        self.grid_canvas.create_window((0, 0), window=self.grid_inner, anchor="nw")
        self.grid_canvas.configure(yscrollcommand=scrollbar.set)

        self.grid_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.grid_frame = frame

    # view mode muutus
    def _set_view(self, mode):
        self.view_mode.set(mode)
        self.refresh()

    # filtrite reset
    def reset_filters(self):
        self.search_var.set("")
        self.platform_var.set("All")
        self.genre_var.set("All")
        self.status_var.set("All")
        self.favorites_only_var.set(False)
        self.refresh()

    # kombode täitmine
    def _refresh_filter_values(self):
        platforms = ["All"] + self.db.get_platforms()
        genres = ["All"] + self.db.get_genres()
        statuses = ["All"] + self.db.get_statuses()

        self.platform_combo["values"] = platforms
        self.genre_combo["values"] = genres
        self.status_combo["values"] = statuses

        if self.platform_var.get() not in platforms:
            self.platform_var.set("All")
        if self.genre_var.get() not in genres:
            self.genre_var.set("All")
        if self.status_var.get() not in statuses:
            self.status_var.set("All")

    # launcheri label
    def _launcher_label(self, launcher_type):
        mapping = {
            "local_file": "Local",
            "steam_shortcut": "Steam .url",
            "steam_uri": "Steam URI",
            "epic_uri": "Epic URI",
        }
        return mapping.get(launcher_type, launcher_type)

    # täielik refresh
    def refresh(self):
        self._refresh_filter_values()

        games = self.db.get_games(
            search=self.search_var.get(),
            platform=self.platform_var.get(),
            genre=self.genre_var.get(),
            status=self.status_var.get(),
            favorites_only=self.favorites_only_var.get(),
        )

        if self.view_mode.get() == "list":
            self.grid_frame.grid_remove()
            self.list_frame.grid()
            self._render_list(games)
        else:
            self.list_frame.grid_remove()
            self.grid_frame.grid()
            self._render_grid(games)

        if self.selected_game_id:
            game = self.db.get_game(self.selected_game_id)
            if game:
                self._show_details(game)
            else:
                self.selected_game_id = None
                self._clear_details()

    # tabeli täitmine
    def _render_list(self, games):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for game in games:
            self.tree.insert(
                "",
                "end",
                iid=str(game.id),
                values=(
                    game.title,
                    game.platform,
                    game.genre,
                    game.rating,
                    game.status,
                    "★" if game.favorite else "",
                    self._launcher_label(game.launcher_type),
                )
            )

    # kaardi hover bind
    def _bind_card_hover(self, card, game_id):
        def enter(_e=None):
            card.hover_on()

        def leave(_e=None):
            card.hover_off()

        def click(_e=None):
            self.select_game(game_id)

        # lapse widgetid
        for widget in card.winfo_children():
            widget.bind("<Enter>", enter)
            widget.bind("<Leave>", leave)
            widget.bind("<Button-1>", click)

        # kaardi enda eventid
        card.bind("<Enter>", enter)
        card.bind("<Leave>", leave)
        card.bind("<Button-1>", click)

    # gridi täitmine
    def _render_grid(self, games):
        for w in self.grid_inner.winfo_children():
            w.destroy()

        # veergude arv
        cols = 4
        for i in range(cols):
            self.grid_inner.grid_columnconfigure(i, weight=1)

        for idx, game in enumerate(games):
            row = idx // cols
            col = idx % cols

            # valitud kaart
            selected = game.id == self.selected_game_id
            card = HoverCard(self.grid_inner, self.colors, selected=selected)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # cover
            cover = self._make_cover(card, game.cover_path, 180, 210)
            cover.pack(fill="x")

            bg = card.cget("bg")

            # pealkiri
            title = tk.Label(
                card,
                text=game.title,
                bg=bg,
                fg=self.colors["text"],
                font=("Segoe UI", 12, "bold"),
                wraplength=180,
                justify="left",
            )
            title.pack(anchor="w", pady=(10, 4))

            # meta
            meta = tk.Label(
                card,
                text=f"{game.platform} • {game.genre}",
                bg=bg,
                fg=self.colors["muted"],
                font=("Segoe UI", 9),
                wraplength=180,
                justify="left",
            )
            meta.pack(anchor="w")

            # status
            status = tk.Label(
                card,
                text=f"⭐ {game.rating}/10   •   {game.status}",
                bg=bg,
                fg=self.colors["text"],
                font=("Segoe UI", 10),
                wraplength=180,
                justify="left",
            )
            status.pack(anchor="w", pady=(8, 0))

            # launcher badge
            launcher_text = self._launcher_label(game.launcher_type)
            launcher_color = "#7edc9a" if "Steam" in launcher_text or "Epic" in launcher_text else self.colors["muted"]

            launch_badge = tk.Label(
                card,
                text=f"Launch: {launcher_text}",
                bg=bg,
                fg=launcher_color,
                font=("Segoe UI", 9, "bold"),
            )
            launch_badge.pack(anchor="w", pady=(6, 0))

            # favorite badge
            if game.favorite:
                fav = tk.Label(
                    card,
                    text="★ Favorite",
                    bg=bg,
                    fg="#ffd166",
                    font=("Segoe UI", 10, "bold"),
                )
                fav.pack(anchor="w", pady=(6, 0))

            self._bind_card_hover(card, game.id)

    # cover widget
    def _make_cover(self, parent, path, w, h):
        if PIL_AVAILABLE and path and os.path.exists(path):
            try:
                image = Image.open(path)
                image.thumbnail((w, h))
                photo = ImageTk.PhotoImage(image)

                lbl = tk.Label(parent, image=photo, bg=parent["bg"])
                lbl.image = photo
                return lbl
            except Exception:
                pass

        # placeholder
        return tk.Label(
            parent,
            text="No Cover",
            bg=self.colors["placeholder"],
            fg=self.colors["muted"],
            width=22,
            height=11,
        )

    # tree select
    def _on_tree_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        self.select_game(int(selected[0]))

    # mängu valik
    def select_game(self, game_id):
        self.selected_game_id = game_id
        game = self.db.get_game(game_id)
        if game:
            self._show_details(game)
        self.refresh()

    # detaili kuvamine
    def _show_details(self, game):
        self.detail_title.config(text=game.title)

        self.detail_meta.config(
            text=(
                f"{game.platform}\n"
                f"{game.genre}\n"
                f"Status: {game.status}\n"
                f"Rating: {game.rating}/10\n"
                f"Favorite: {'Yes' if game.favorite else 'No'}"
            )
        )

        launcher_label = self._launcher_label(game.launcher_type)
        launcher_text = f"{launcher_label}:\n{game.launcher_path}" if game.launcher_path else f"{launcher_label}:\nNot set"
        self.detail_launcher.config(text=launcher_text)

        self.detail_notes.config(text=game.notes if game.notes else "No notes yet.")

        if PIL_AVAILABLE and game.cover_path and os.path.exists(game.cover_path):
            try:
                image = Image.open(game.cover_path)
                image.thumbnail((260, 260))
                photo = ImageTk.PhotoImage(image)
                self.cover_label.configure(image=photo, text="")
                self.cover_label.image = photo
                return
            except Exception:
                pass

        self.cover_label.configure(image="", text="No cover")
        self.cover_label.image = None

    # detaili tühjendamine
    def _clear_details(self):
        self.detail_title.config(text="Nothing selected")
        self.detail_meta.config(text="")
        self.detail_launcher.config(text="")
        self.detail_notes.config(text="Select a game to see details.")
        self.cover_label.configure(image="", text="No cover")
        self.cover_label.image = None

    # launch loogika
    def launch_selected(self):
        if self.selected_game_id is None:
            messagebox.showinfo("Launch", "Vali kõigepealt mäng.")
            return

        game = self.db.get_game(self.selected_game_id)
        if not game:
            messagebox.showerror("Launch", "Valitud mängu ei leitud enam.")
            return

        if not game.launcher_path:
            messagebox.showwarning("Launch", "Sellel mängul puudub launcher path või URI.")
            return

        try:
            # kohalik fail
            if game.launcher_type == "local_file":
                if not os.path.exists(game.launcher_path):
                    messagebox.showerror("Launch", f"Faili ei leitud:\n{game.launcher_path}")
                    return
                os.startfile(game.launcher_path)
                return

            # steami shortcut
            if game.launcher_type == "steam_shortcut":
                if not os.path.exists(game.launcher_path):
                    messagebox.showerror("Launch", f"Shortcuti faili ei leitud:\n{game.launcher_path}")
                    return
                os.startfile(game.launcher_path)
                return

            # steam uri
            if game.launcher_type == "steam_uri":
                webbrowser.open(game.launcher_path)
                return

            # epic uri
            if game.launcher_type == "epic_uri":
                webbrowser.open(game.launcher_path)
                return

            # fallback
            webbrowser.open(game.launcher_path)

        except Exception as e:
            messagebox.showerror("Launch error", str(e))

    # mängu lisamise aken
    def open_add_dialog(self):
        self._open_game_dialog("Add Game")

    # mängu muutmise aken
    def open_edit_dialog(self):
        if self.selected_game_id is None:
            messagebox.showinfo("Edit", "Vali kõigepealt mäng.")
            return

        game = self.db.get_game(self.selected_game_id)
        if not game:
            messagebox.showerror("Edit", "Valitud mängu ei leitud enam.")
            return

        self._open_game_dialog("Edit Game", game)

    # mängu lisamise/muutmise dialoog
    def _open_game_dialog(self, title, game=None):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("980x900")
        dialog.minsize(900, 820)
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # dialoogi grid
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)

        # väline raam
        shell = tk.Frame(dialog, bg=self.colors["bg"])
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(0, weight=1)

        # canvas scrollitavaks sisuks
        canvas = tk.Canvas(shell, bg=self.colors["bg"], highlightthickness=0, bd=0)
        canvas.grid(row=0, column=0, sticky="nsew")

        # scrollbar
        scrollbar = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        # sisu frame
        content = ttk.Frame(canvas, padding=24)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)

        # frame canvas sisse
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")

        # scroll region update
        def on_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        content.bind("<Configure>", on_configure)

        # canvas width sünk
        def on_canvas_configure(event):
            canvas.itemconfigure(window_id, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)

        # mousewheel scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # pealkiri
        ttk.Label(content, text=title, style="Title.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 18))

        # väljade muutujad
        title_var = tk.StringVar(value=game.title if game else "")
        platform_var = tk.StringVar(value=game.platform if game else "PC")
        genre_var = tk.StringVar(value=game.genre if game else "RPG")
        rating_var = tk.StringVar(value=str(game.rating) if game else "8")
        status_var = tk.StringVar(value=game.status if game else "Backlog")
        favorite_var = tk.BooleanVar(value=bool(game.favorite) if game else False)
        cover_var = tk.StringVar(value=game.cover_path if game else "")
        launcher_type_var = tk.StringVar(value=game.launcher_type if game else "local_file")
        launcher_var = tk.StringVar(value=game.launcher_path if game else "")

        # title + platform
        ttk.Label(content, text="Title").grid(row=1, column=0, sticky="w", padx=(0, 10))
        ttk.Label(content, text="Platform").grid(row=1, column=1, sticky="w")

        ttk.Entry(content, textvariable=title_var).grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=(4, 12))
        ttk.Combobox(
            content,
            textvariable=platform_var,
            state="readonly",
            values=["PC", "PS5", "PS4", "Xbox", "Switch", "Mobile", "Other"]
        ).grid(row=2, column=1, sticky="ew", pady=(4, 12))

        # genre + rating
        ttk.Label(content, text="Genre").grid(row=3, column=0, sticky="w", padx=(0, 10))
        ttk.Label(content, text="Rating (0-10)").grid(row=3, column=1, sticky="w")

        ttk.Combobox(
            content,
            textvariable=genre_var,
            state="readonly",
            values=["RPG", "Action", "Action RPG", "Adventure", "Shooter", "Racing", "Roguelike", "Indie", "Strategy", "Other"]
        ).grid(row=4, column=0, sticky="ew", padx=(0, 10), pady=(4, 12))

        ttk.Combobox(
            content,
            textvariable=rating_var,
            state="readonly",
            values=[str(i) for i in range(0, 11)]
        ).grid(row=4, column=1, sticky="ew", pady=(4, 12))

        # status + launcher type
        ttk.Label(content, text="Status").grid(row=5, column=0, sticky="w", padx=(0, 10))
        ttk.Label(content, text="Launcher type").grid(row=5, column=1, sticky="w")

        ttk.Combobox(
            content,
            textvariable=status_var,
            state="readonly",
            values=self.db.get_statuses()
        ).grid(row=6, column=0, sticky="ew", padx=(0, 10), pady=(4, 12))

        ttk.Combobox(
            content,
            textvariable=launcher_type_var,
            state="readonly",
            values=["local_file", "steam_shortcut", "steam_uri", "epic_uri"]
        ).grid(row=6, column=1, sticky="ew", pady=(4, 12))

        # favorite checkbox
        fav_row = ttk.Frame(content)
        fav_row.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(2, 12))
        ttk.Checkbutton(fav_row, text="Favorite", variable=favorite_var).pack(anchor="w")

        # cover path
        ttk.Label(content, text="Cover image").grid(row=8, column=0, columnspan=2, sticky="w")

        cover_row = ttk.Frame(content)
        cover_row.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(4, 12))
        cover_row.columnconfigure(0, weight=1)

        ttk.Entry(cover_row, textvariable=cover_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(cover_row, text="Browse", command=lambda: self._browse_cover(cover_var)).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(cover_row, text="Import", command=lambda: self._import_cover(cover_var, title_var.get())).grid(row=0, column=2, padx=(8, 0))

        # launcher path
        ttk.Label(content, text="Launcher / EXE / Shortcut / URI").grid(row=10, column=0, columnspan=2, sticky="w")

        launcher_row = ttk.Frame(content)
        launcher_row.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(4, 12))
        launcher_row.columnconfigure(0, weight=1)

        ttk.Entry(launcher_row, textvariable=launcher_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(launcher_row, text="Browse EXE", command=lambda: self._browse_launcher_file(launcher_type_var, launcher_var)).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(launcher_row, text="Steam .url", command=lambda: self._browse_steam_shortcut(launcher_type_var, launcher_var)).grid(row=0, column=2, padx=(8, 0))
        ttk.Button(launcher_row, text="Steam URI", command=lambda: self._fill_steam_uri(launcher_type_var, launcher_var)).grid(row=0, column=3, padx=(8, 0))
        ttk.Button(launcher_row, text="Epic URI", command=lambda: self._fill_epic_uri(launcher_type_var, launcher_var)).grid(row=0, column=4, padx=(8, 0))

        # abiinfo
        helper = tk.Label(
            content,
            text=(
                "Steam shortcut: vali Steam'i .url shortcut.\n"
                "Steam URI: kasuta kujul steam://rungameid/APPID\n"
                "Epic URI: kasuta kujul com.epicgames.launcher://apps/..."
            ),
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            justify="left",
            anchor="w",
            font=("Segoe UI", 9),
        )
        helper.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        # notes
        ttk.Label(content, text="Notes").grid(row=13, column=0, columnspan=2, sticky="w")

        notes_box = tk.Text(
            content,
            height=12,
            bg=self.colors["input"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            wrap="word",
            font=("Segoe UI", 10),
        )
        notes_box.grid(row=14, column=0, columnspan=2, sticky="nsew", pady=(4, 16))
        if game:
            notes_box.insert("1.0", game.notes)

        # nupurida
        actions = ttk.Frame(content)
        actions.grid(row=15, column=0, columnspan=2, sticky="ew", pady=(6, 10))

        ttk.Button(actions, text="Cancel", command=dialog.destroy).pack(side="right")
        ttk.Button(
            actions,
            text="Save Game",
            style="Accent.TButton",
            command=lambda: self._save_game_dialog(
                dialog=dialog,
                existing_game=game,
                title_var=title_var,
                platform_var=platform_var,
                genre_var=genre_var,
                rating_var=rating_var,
                status_var=status_var,
                favorite_var=favorite_var,
                cover_var=cover_var,
                launcher_type_var=launcher_type_var,
                launcher_var=launcher_var,
                notes_box=notes_box,
            )
        ).pack(side="right", padx=(0, 8))

    # mängu salvestus
    def _save_game_dialog(
        self,
        dialog,
        existing_game,
        title_var,
        platform_var,
        genre_var,
        rating_var,
        status_var,
        favorite_var,
        cover_var,
        launcher_type_var,
        launcher_var,
        notes_box,
    ):
        # pealkirja kontroll
        title_text = title_var.get().strip()
        if not title_text:
            messagebox.showerror("Validation", "Title on kohustuslik.")
            return

        # rating kontroll
        try:
            rating = int(rating_var.get())
        except ValueError:
            messagebox.showerror("Validation", "Rating peab olema 0 kuni 10.")
            return

        launcher_type = launcher_type_var.get().strip() or "local_file"
        launcher_value = launcher_var.get().strip()

        # steam uri kontroll
        if launcher_type == "steam_uri" and launcher_value and not launcher_value.startswith("steam://"):
            messagebox.showerror("Validation", "Steam URI peab algama kujul:\nsteam://")
            return

        # epic uri kontroll
        if launcher_type == "epic_uri" and launcher_value and not launcher_value.startswith("com.epicgames.launcher://"):
            messagebox.showerror("Validation", "Epic URI peab algama kujul:\ncom.epicgames.launcher://")
            return

        # märkmed
        notes = notes_box.get("1.0", "end").strip()

        # update või insert
        if existing_game:
            self.db.update_game(
                existing_game.id,
                title_text,
                platform_var.get().strip(),
                genre_var.get().strip(),
                rating,
                status_var.get().strip(),
                1 if favorite_var.get() else 0,
                cover_var.get().strip(),
                launcher_type,
                launcher_value,
                notes,
            )
        else:
            self.db.add_game(
                title_text,
                platform_var.get().strip(),
                genre_var.get().strip(),
                rating,
                status_var.get().strip(),
                1 if favorite_var.get() else 0,
                cover_var.get().strip(),
                launcher_type,
                launcher_value,
                notes,
            )

        dialog.destroy()
        self.refresh()

        if self.on_data_changed:
            self.on_data_changed()

    # cover browse
    def _browse_cover(self, var):
        path = filedialog.askopenfilename(
            title="Choose cover image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"), ("All files", "*.*")]
        )
        if path:
            var.set(path)

    # cover import
    def _import_cover(self, var, game_title):
        src = filedialog.askopenfilename(
            title="Import cover image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"), ("All files", "*.*")]
        )
        if not src:
            return

        os.makedirs("covers", exist_ok=True)
        ext = os.path.splitext(src)[1]

        # faili nimi puhastatult
        safe_title = "".join(
            c for c in (game_title or "cover")
            if c.isalnum() or c in (" ", "_", "-")
        ).strip().replace(" ", "_")

        if not safe_title:
            safe_title = "cover"

        dest = os.path.join("covers", f"{safe_title}{ext}")

        try:
            shutil.copy(src, dest)
            var.set(dest)
            messagebox.showinfo("Import cover", f"Cover imporditud:\n{dest}")
        except Exception as e:
            messagebox.showerror("Import cover error", str(e))

    # kohaliku faili browse
    def _browse_launcher_file(self, launcher_type_var, launcher_var):
        path = filedialog.askopenfilename(
            title="Choose EXE / BAT / LNK",
            filetypes=[("Executable files", "*.exe *.bat *.lnk"), ("All files", "*.*")]
        )
        if path:
            launcher_type_var.set("local_file")
            launcher_var.set(path)

    # steami shortcut browse
    def _browse_steam_shortcut(self, launcher_type_var, launcher_var):
        path = filedialog.askopenfilename(
            title="Choose Steam Internet Shortcut",
            filetypes=[("Internet shortcuts", "*.url *.lnk"), ("All files", "*.*")]
        )
        if path:
            launcher_type_var.set("steam_shortcut")
            launcher_var.set(path)

    # steam uri näidis
    def _fill_steam_uri(self, launcher_type_var, launcher_var):
        launcher_type_var.set("steam_uri")
        launcher_var.set("steam://rungameid/APPID")

    # epic uri näidis
    def _fill_epic_uri(self, launcher_type_var, launcher_var):
        launcher_type_var.set("epic_uri")
        launcher_var.set("com.epicgames.launcher://apps/YOUR_APP_ID?action=launch&silent=true")

    # launcheri label
    def _launcher_label(self, launcher_type):
        mapping = {
            "local_file": "Local",
            "steam_shortcut": "Steam .url",
            "steam_uri": "Steam URI",
            "epic_uri": "Epic URI",
        }
        return mapping.get(launcher_type, launcher_type)

    # steam .url faili parsimine
    def _parse_steam_url_shortcut(self, path: Path):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

        # lihtne URL rea otsing
        for line in text.splitlines():
            if line.strip().upper().startswith("URL="):
                url_value = line.split("=", 1)[1].strip()
                if url_value.startswith("steam://"):
                    return url_value

        return None

    # mängu olemasolu kontroll title järgi
    def _title_exists(self, title: str):
        title_lower = title.strip().lower()
        for game in self.db.get_games():
            if game.title.strip().lower() == title_lower:
                return True
        return False

    # steam shortcutide import
    def import_steam_shortcuts(self):
        # tüüpilised kaustad
        candidate_dirs = [
            Path.home() / "Desktop",
            Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Steam",
        ]

        imported = 0
        skipped = 0

        for directory in candidate_dirs:
            if not directory.exists():
                continue

            for file in directory.glob("*.url"):
                steam_url = self._parse_steam_url_shortcut(file)
                if not steam_url:
                    continue

                # failinimest title
                title = file.stem.strip()
                if not title:
                    skipped += 1
                    continue

                # duplikaadi vältimine
                if self._title_exists(title):
                    skipped += 1
                    continue

                # lisa andmebaasi
                self.db.add_game(
                    title=title,
                    platform="PC",
                    genre="Unknown",
                    rating=0,
                    status="Backlog",
                    favorite=0,
                    cover_path="",
                    launcher_type="steam_shortcut",
                    launcher_path=str(file),
                    notes="Imporditud Steam shortcutist.",
                )
                imported += 1

        self.refresh()
        messagebox.showinfo("Import Steam", f"Imporditud: {imported}\nVahele jäetud: {skipped}")

    # epic installide import
    def import_epic_installs(self):
        # tüüpiline LauncherInstalled.dat asukoht
        candidate = Path(os.environ.get("ALLUSERSPROFILE", r"C:\ProgramData")) / "Epic" / "UnrealEngineLauncher" / "LauncherInstalled.dat"

        if not candidate.exists():
            messagebox.showwarning("Import Epic", f"Faili ei leitud:\n{candidate}")
            return

        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception as e:
            messagebox.showerror("Import Epic", f"JSON lugemine ebaõnnestus:\n{e}")
            return

        installation_list = data.get("InstallationList", [])
        imported = 0
        skipped = 0

        for item in installation_list:
            # nimi AppName-ist või DisplayName-ist
            title = item.get("DisplayName") or item.get("AppName") or ""
            app_name = item.get("AppName") or ""

            # tühi nimi
            if not title:
                skipped += 1
                continue

            # duplikaat
            if self._title_exists(title):
                skipped += 1
                continue

            # buildi uri
            epic_uri = f"com.epicgames.launcher://apps/{app_name}?action=launch&silent=true" if app_name else ""

            # lisa mäng
            self.db.add_game(
                title=title,
                platform="PC",
                genre="Unknown",
                rating=0,
                status="Backlog",
                favorite=0,
                cover_path="",
                launcher_type="epic_uri",
                launcher_path=epic_uri,
                notes="Imporditud Epic LauncherInstalled.dat failist.",
            )
            imported += 1

        self.refresh()
        messagebox.showinfo("Import Epic", f"Imporditud: {imported}\nVahele jäetud: {skipped}")

    # valitud mängu launch
    def launch_selected(self):
        if self.selected_game_id is None:
            messagebox.showinfo("Launch", "Vali kõigepealt mäng.")
            return

        game = self.db.get_game(self.selected_game_id)
        if not game:
            messagebox.showerror("Launch", "Valitud mängu ei leitud enam.")
            return

        if not game.launcher_path:
            messagebox.showwarning("Launch", "Sellel mängul puudub launcher path või URI.")
            return

        try:
            # tavaline fail
            if game.launcher_type == "local_file":
                if not os.path.exists(game.launcher_path):
                    messagebox.showerror("Launch", f"Faili ei leitud:\n{game.launcher_path}")
                    return
                os.startfile(game.launcher_path)
                return

            # steami .url või shortcut
            if game.launcher_type == "steam_shortcut":
                if not os.path.exists(game.launcher_path):
                    messagebox.showerror("Launch", f"Shortcuti faili ei leitud:\n{game.launcher_path}")
                    return
                os.startfile(game.launcher_path)
                return

            # steam uri
            if game.launcher_type == "steam_uri":
                webbrowser.open(game.launcher_path)
                return

            # epic uri
            if game.launcher_type == "epic_uri":
                webbrowser.open(game.launcher_path)
                return

            # fallback
            webbrowser.open(game.launcher_path)

        except Exception as e:
            messagebox.showerror("Launch error", str(e))

    # mängu valik
    def select_game(self, game_id):
        self.selected_game_id = game_id
        game = self.db.get_game(game_id)
        if game:
            self._show_details(game)
        self.refresh()

    # tabeli valik
    def _on_tree_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        self.select_game(int(selected[0]))

    # detaili täitmine
    def _show_details(self, game):
        self.detail_title.config(text=game.title)

        self.detail_meta.config(
            text=(
                f"{game.platform}\n"
                f"{game.genre}\n"
                f"Status: {game.status}\n"
                f"Rating: {game.rating}/10\n"
                f"Favorite: {'Yes' if game.favorite else 'No'}"
            )
        )

        launcher_label = self._launcher_label(game.launcher_type)
        launcher_text = f"{launcher_label}:\n{game.launcher_path}" if game.launcher_path else f"{launcher_label}:\nNot set"
        self.detail_launcher.config(text=launcher_text)

        self.detail_notes.config(text=game.notes if game.notes else "No notes yet.")

        if PIL_AVAILABLE and game.cover_path and os.path.exists(game.cover_path):
            try:
                image = Image.open(game.cover_path)
                image.thumbnail((260, 260))
                photo = ImageTk.PhotoImage(image)
                self.cover_label.configure(image=photo, text="")
                self.cover_label.image = photo
                return
            except Exception:
                pass

        self.cover_label.configure(image="", text="No cover")
        self.cover_label.image = None

    # detaili puhastus
    def _clear_details(self):
        self.detail_title.config(text="Nothing selected")
        self.detail_meta.config(text="")
        self.detail_launcher.config(text="")
        self.detail_notes.config(text="Select a game to see details.")
        self.cover_label.configure(image="", text="No cover")
        self.cover_label.image = None

    # mängu kustutamine
    def delete_selected(self):
        if self.selected_game_id is None:
            messagebox.showinfo("Delete", "Vali kõigepealt mäng.")
            return

        game = self.db.get_game(self.selected_game_id)
        if not game:
            messagebox.showerror("Delete", "Valitud mängu ei leitud enam.")
            return

        ok = messagebox.askyesno("Delete game", f"Kas kustutada '{game.title}'?")
        if not ok:
            return

        self.db.delete_game(game.id)
        self.selected_game_id = None
        self.refresh()

        if self.on_data_changed:
            self.on_data_changed()