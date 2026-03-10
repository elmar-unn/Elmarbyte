import os
import shutil
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class LibraryView(ttk.Frame):
    def __init__(self, parent, db, colors, on_data_changed=None):
        super().__init__(parent)
        self.db = db
        self.colors = colors
        self.on_data_changed = on_data_changed

        self.selected_game_id = None
        self.view_mode = tk.StringVar(value="grid")
        self.search_var = tk.StringVar()
        self.platform_var = tk.StringVar(value="All")
        self.genre_var = tk.StringVar(value="All")
        self.status_var = tk.StringVar(value="All")
        self.favorites_only_var = tk.BooleanVar(value=False)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_header()
        self._build_filters()
        self._build_main_area()
        self.refresh()

    def _build_header(self):
        header = ttk.Frame(self)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(24, 12))
        header.columnconfigure(0, weight=1)

        left = ttk.Frame(header)
        left.grid(row=0, column=0, sticky="w")
        ttk.Label(left, text="Library", style="Title.TLabel").pack(anchor="w")
        ttk.Label(left, text="Manage games, covers and launcher paths.", style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

        right = ttk.Frame(header)
        right.grid(row=0, column=1, sticky="e")

        ttk.Button(right, text="List", command=lambda: self._set_view("list")).pack(side="left", padx=4)
        ttk.Button(right, text="Grid", command=lambda: self._set_view("grid")).pack(side="left", padx=4)
        ttk.Button(right, text="Launch Selected", style="Accent.TButton", command=self.launch_selected).pack(side="left", padx=(12, 0))
        ttk.Button(right, text="Add Game", command=self.open_add_dialog).pack(side="left", padx=(8, 0))

    def _build_filters(self):
        side = ttk.Frame(self, style="Card.TFrame", padding=18)
        side.grid(row=1, column=0, sticky="ns", padx=(24, 12), pady=(0, 24))
        side.configure(width=310)

        ttk.Label(side, text="Search & filters", style="Heading.TLabel").pack(anchor="w", pady=(0, 12))

        ttk.Label(side, text="Search").pack(anchor="w")
        entry = ttk.Entry(side, textvariable=self.search_var)
        entry.pack(fill="x", pady=(4, 12))
        entry.bind("<KeyRelease>", lambda e: self.refresh())

        ttk.Label(side, text="Platform").pack(anchor="w")
        self.platform_combo = ttk.Combobox(side, textvariable=self.platform_var, state="readonly")
        self.platform_combo.pack(fill="x", pady=(4, 12))
        self.platform_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Label(side, text="Genre").pack(anchor="w")
        self.genre_combo = ttk.Combobox(side, textvariable=self.genre_var, state="readonly")
        self.genre_combo.pack(fill="x", pady=(4, 12))
        self.genre_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Label(side, text="Status").pack(anchor="w")
        self.status_combo = ttk.Combobox(side, textvariable=self.status_var, state="readonly")
        self.status_combo.pack(fill="x", pady=(4, 12))
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Checkbutton(side, text="Favorites only", variable=self.favorites_only_var, command=self.refresh).pack(anchor="w", pady=(6, 10))
        ttk.Button(side, text="Reset filters", command=self.reset_filters).pack(fill="x", pady=(0, 14))

        ttk.Separator(side).pack(fill="x", pady=12)

        ttk.Label(side, text="Selected game", style="Heading.TLabel").pack(anchor="w", pady=(0, 12))

        self.detail_wrap = tk.Frame(side, bg=self.colors["card"])
        self.detail_wrap.pack(fill="both", expand=True)

        self.cover_label = tk.Label(
            self.detail_wrap,
            text="No cover",
            bg=self.colors["placeholder"],
            fg=self.colors["muted"],
            width=26,
            height=12,
        )
        self.cover_label.pack(fill="x", pady=(0, 12))

        self.detail_title = tk.Label(
            self.detail_wrap,
            text="Nothing selected",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 15, "bold"),
            wraplength=260,
            justify="left",
        )
        self.detail_title.pack(anchor="w")

        self.detail_meta = tk.Label(
            self.detail_wrap,
            text="",
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
            justify="left",
            wraplength=260,
        )
        self.detail_meta.pack(anchor="w", pady=(8, 10))

        self.detail_launcher = tk.Label(
            self.detail_wrap,
            text="",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 9),
            justify="left",
            wraplength=260,
        )
        self.detail_launcher.pack(anchor="w", pady=(0, 10))

        self.detail_notes = tk.Label(
            self.detail_wrap,
            text="Select a game to see details.",
            bg=self.colors["card"],
            fg=self.colors["text"],
            justify="left",
            wraplength=260,
        )
        self.detail_notes.pack(anchor="w")

        actions = ttk.Frame(side)
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="Edit", command=self.open_edit_dialog).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(actions, text="Delete", style="Danger.TButton", command=self.delete_selected).pack(side="left", expand=True, fill="x", padx=(4, 0))

    def _build_main_area(self):
        container = ttk.Frame(self, style="Card.TFrame")
        container.grid(row=1, column=1, sticky="nsew", padx=(12, 24), pady=(0, 24))
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.stack = ttk.Frame(container)
        self.stack.grid(row=0, column=0, sticky="nsew")
        self.stack.rowconfigure(0, weight=1)
        self.stack.columnconfigure(0, weight=1)

        self._build_list_view()
        self._build_grid_view()

    def _build_list_view(self):
        frame = ttk.Frame(self.stack)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        cols = ("title", "platform", "genre", "rating", "status", "favorite")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings")
        headings = {
            "title": "Title",
            "platform": "Platform",
            "genre": "Genre",
            "rating": "Rating",
            "status": "Status",
            "favorite": "★",
        }
        for col in cols:
            self.tree.heading(col, text=headings[col])

        self.tree.column("title", width=280)
        self.tree.column("platform", width=100)
        self.tree.column("genre", width=120)
        self.tree.column("rating", width=80, anchor="center")
        self.tree.column("status", width=110, anchor="center")
        self.tree.column("favorite", width=50, anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        self.list_frame = frame

    def _build_grid_view(self):
        frame = ttk.Frame(self.stack)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.grid_canvas = tk.Canvas(frame, bg=self.colors["card"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.grid_canvas.yview)
        self.grid_inner = tk.Frame(self.grid_canvas, bg=self.colors["card"])

        self.grid_inner.bind(
            "<Configure>",
            lambda e: self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))
        )

        self.grid_canvas.create_window((0, 0), window=self.grid_inner, anchor="nw")
        self.grid_canvas.configure(yscrollcommand=scrollbar.set)

        self.grid_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.grid_frame = frame

    def _set_view(self, mode):
        self.view_mode.set(mode)
        self.refresh()

    def reset_filters(self):
        self.search_var.set("")
        self.platform_var.set("All")
        self.genre_var.set("All")
        self.status_var.set("All")
        self.favorites_only_var.set(False)
        self.refresh()

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
                )
            )

    def _render_grid(self, games):
        for w in self.grid_inner.winfo_children():
            w.destroy()

        cols = 4
        for i in range(cols):
            self.grid_inner.grid_columnconfigure(i, weight=1)

        for idx, game in enumerate(games):
            row = idx // cols
            col = idx % cols

            selected = game.id == self.selected_game_id
            bg = self.colors["selected"] if selected else self.colors["panel"]
            border = self.colors["accent"] if selected else self.colors["border"]

            card = tk.Frame(
                self.grid_inner,
                bg=bg,
                highlightbackground=border,
                highlightthickness=1,
                bd=0,
                padx=12,
                pady=12,
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            cover = self._make_cover(card, game.cover_path, 160, 200)
            cover.pack(fill="x")

            title = tk.Label(
                card,
                text=game.title,
                bg=bg,
                fg=self.colors["text"],
                font=("Segoe UI", 12, "bold"),
                wraplength=160,
                justify="left",
            )
            title.pack(anchor="w", pady=(10, 4))

            meta = tk.Label(
                card,
                text=f"{game.platform} • {game.genre}",
                bg=bg,
                fg=self.colors["muted"],
                font=("Segoe UI", 9),
                wraplength=160,
                justify="left",
            )
            meta.pack(anchor="w")

            status = tk.Label(
                card,
                text=f"⭐ {game.rating}/10   •   {game.status}",
                bg=bg,
                fg=self.colors["text"],
                font=("Segoe UI", 10),
                wraplength=160,
                justify="left",
            )
            status.pack(anchor="w", pady=(8, 0))

            launch_badge_text = "Epic" if game.launcher_type == "epic" else "Local"
            launch_badge = tk.Label(
                card,
                text=f"Launch: {launch_badge_text}",
                bg=bg,
                fg="#8fd694" if game.launcher_type == "epic" else self.colors["muted"],
                font=("Segoe UI", 9, "bold"),
            )
            launch_badge.pack(anchor="w", pady=(6, 0))

            if game.favorite:
                fav = tk.Label(card, text="★ Favorite", bg=bg, fg="#ffd166", font=("Segoe UI", 10, "bold"))
                fav.pack(anchor="w", pady=(6, 0))
                fav.bind("<Button-1>", lambda e, gid=game.id: self.select_game(gid))

            for widget in (card, cover, title, meta, status, launch_badge):
                widget.bind("<Button-1>", lambda e, gid=game.id: self.select_game(gid))

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

        return tk.Label(
            parent,
            text="No Cover",
            bg=self.colors["placeholder"],
            fg=self.colors["muted"],
            width=20,
            height=11,
        )

    def _on_tree_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        self.select_game(int(selected[0]))

    def select_game(self, game_id):
        self.selected_game_id = game_id
        game = self.db.get_game(game_id)
        if game:
            self._show_details(game)
        self.refresh()

    def _show_details(self, game):
        self.detail_title.config(text=game.title)
        self.detail_meta.config(
            text=f"{game.platform}\n{game.genre}\nStatus: {game.status}\nRating: {game.rating}/10\nFavorite: {'Yes' if game.favorite else 'No'}"
        )

        launcher_label = "Epic URI" if game.launcher_type == "epic" else "Launcher path"
        launcher_text = f"{launcher_label}:\n{game.launcher_path}" if game.launcher_path else f"{launcher_label}:\nNot set"
        self.detail_launcher.config(text=launcher_text)

        self.detail_notes.config(text=game.notes if game.notes else "No notes yet.")

        if PIL_AVAILABLE and game.cover_path and os.path.exists(game.cover_path):
            try:
                image = Image.open(game.cover_path)
                image.thumbnail((240, 240))
                photo = ImageTk.PhotoImage(image)
                self.cover_label.configure(image=photo, text="")
                self.cover_label.image = photo
                return
            except Exception:
                pass

        self.cover_label.configure(image="", text="No cover")
        self.cover_label.image = None

    def _clear_details(self):
        self.detail_title.config(text="Nothing selected")
        self.detail_meta.config(text="")
        self.detail_launcher.config(text="")
        self.detail_notes.config(text="Select a game to see details.")
        self.cover_label.configure(image="", text="No cover")
        self.cover_label.image = None

    def launch_selected(self):
        if self.selected_game_id is None:
            messagebox.showinfo("Launch", "Select a game first.")
            return

        game = self.db.get_game(self.selected_game_id)
        if not game:
            messagebox.showerror("Launch", "Selected game no longer exists.")
            return

        if not game.launcher_path:
            messagebox.showwarning("Launch", "This game has no launcher path or Epic URI yet.")
            return

        try:
            if game.launcher_type == "epic":
                webbrowser.open(game.launcher_path)
                return

            if not os.path.exists(game.launcher_path):
                messagebox.showerror("Launch", f"Launcher not found:\n{game.launcher_path}")
                return

            os.startfile(game.launcher_path)

        except Exception as e:
            messagebox.showerror("Launch error", str(e))

    def open_add_dialog(self):
        self._open_game_dialog("Add Game")

    def open_edit_dialog(self):
        if self.selected_game_id is None:
            messagebox.showinfo("Edit", "Select a game first.")
            return

        game = self.db.get_game(self.selected_game_id)
        if not game:
            messagebox.showerror("Edit", "Selected game no longer exists.")
            return

        self._open_game_dialog("Edit Game", game)

    def _open_game_dialog(self, title, game=None):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("760x760")
        dialog.minsize(760, 760)
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)

        outer = ttk.Frame(dialog, padding=20)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(10, weight=1)

        ttk.Label(outer, text=title, style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 14))

        title_var = tk.StringVar(value=game.title if game else "")
        platform_var = tk.StringVar(value=game.platform if game else "PC")
        genre_var = tk.StringVar(value=game.genre if game else "RPG")
        rating_var = tk.StringVar(value=str(game.rating) if game else "8")
        status_var = tk.StringVar(value=game.status if game else "Backlog")
        favorite_var = tk.BooleanVar(value=bool(game.favorite) if game else False)
        cover_var = tk.StringVar(value=game.cover_path if game else "")
        launcher_type_var = tk.StringVar(value=game.launcher_type if game else "file")
        launcher_var = tk.StringVar(value=game.launcher_path if game else "")

        row = 1
        row = self._field_grid(outer, row, "Title", ttk.Entry(outer, textvariable=title_var))
        row = self._field_grid(
            outer, row, "Platform",
            ttk.Combobox(
                outer, textvariable=platform_var, state="readonly",
                values=["PC", "PS5", "PS4", "Xbox", "Switch", "Mobile", "Other"]
            )
        )
        row = self._field_grid(
            outer, row, "Genre",
            ttk.Combobox(
                outer, textvariable=genre_var, state="readonly",
                values=["RPG", "Action", "Action RPG", "Adventure", "Shooter", "Racing", "Roguelike", "Indie", "Strategy", "Other"]
            )
        )
        row = self._field_grid(
            outer, row, "Rating (0-10)",
            ttk.Combobox(
                outer, textvariable=rating_var, state="readonly",
                values=[str(i) for i in range(0, 11)]
            )
        )
        row = self._field_grid(
            outer, row, "Status",
            ttk.Combobox(
                outer, textvariable=status_var, state="readonly",
                values=self.db.get_statuses()
            )
        )

        ttk.Label(outer, text="Launcher type").grid(row=row, column=0, sticky="w")
        launcher_type_box = ttk.Combobox(
            outer,
            textvariable=launcher_type_var,
            state="readonly",
            values=["file", "epic"],
        )
        launcher_type_box.grid(row=row + 1, column=0, sticky="ew", pady=(4, 10))
        row += 2

        fav_row = ttk.Frame(outer)
        fav_row.grid(row=row, column=0, sticky="ew", pady=(6, 10))
        ttk.Checkbutton(fav_row, text="Favorite", variable=favorite_var).pack(anchor="w")
        row += 1

        ttk.Label(outer, text="Cover image").grid(row=row, column=0, sticky="w")
        row += 1

        cover_row = ttk.Frame(outer)
        cover_row.grid(row=row, column=0, sticky="ew", pady=(4, 10))
        cover_row.columnconfigure(0, weight=1)
        ttk.Entry(cover_row, textvariable=cover_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(cover_row, text="Browse", command=lambda: self._browse_cover(cover_var)).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(cover_row, text="Import", command=lambda: self._import_cover(cover_var, title_var.get())).grid(row=0, column=2, padx=(8, 0))
        row += 1

        ttk.Label(outer, text="Launcher / EXE path or Epic URI").grid(row=row, column=0, sticky="w")
        row += 1

        launcher_row = ttk.Frame(outer)
        launcher_row.grid(row=row, column=0, sticky="ew", pady=(4, 10))
        launcher_row.columnconfigure(0, weight=1)
        ttk.Entry(launcher_row, textvariable=launcher_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(
            launcher_row,
            text="Browse EXE",
            command=lambda: self._browse_launcher(launcher_var)
        ).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(
            launcher_row,
            text="Epic Example",
            command=lambda: self._fill_epic_example(launcher_type_var, launcher_var)
        ).grid(row=0, column=2, padx=(8, 0))
        row += 1

        helper = tk.Label(
            outer,
            text="Epic mode: paste a valid Epic URI like com.epicgames.launcher://apps/... \nFile mode: choose a .exe, .bat or .lnk shortcut.",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            justify="left",
            anchor="w",
            font=("Segoe UI", 9),
        )
        helper.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        ttk.Label(outer, text="Notes").grid(row=row, column=0, sticky="w")
        row += 1

        notes_box = tk.Text(
            outer,
            height=10,
            bg=self.colors["input"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            wrap="word",
            font=("Segoe UI", 10),
        )
        notes_box.grid(row=row, column=0, sticky="nsew", pady=(4, 12))
        if game:
            notes_box.insert("1.0", game.notes)
        row += 1

        actions = ttk.Frame(outer)
        actions.grid(row=row, column=0, sticky="ew", pady=(8, 0))
        actions.columnconfigure(0, weight=1)

        ttk.Button(actions, text="Cancel", command=dialog.destroy).pack(side="right")
        ttk.Button(actions, text="Save Game", style="Accent.TButton", command=lambda: self._save_game_dialog(
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
        )).pack(side="right", padx=(0, 8))

    def _field_grid(self, parent, row, label, widget):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        widget.grid(row=row + 1, column=0, sticky="ew", pady=(4, 10))
        return row + 2

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
        title_text = title_var.get().strip()
        if not title_text:
            messagebox.showerror("Validation", "Title is required.")
            return

        try:
            rating = int(rating_var.get())
        except ValueError:
            messagebox.showerror("Validation", "Rating must be between 0 and 10.")
            return

        launcher_type = launcher_type_var.get().strip() or "file"
        launcher_value = launcher_var.get().strip()

        if launcher_type == "epic" and launcher_value and not launcher_value.startswith("com.epicgames.launcher://"):
            messagebox.showerror(
                "Validation",
                "Epic launcher type expects a URI starting with:\ncom.epicgames.launcher://"
            )
            return

        notes = notes_box.get("1.0", "end").strip()

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

    def _browse_cover(self, var):
        path = filedialog.askopenfilename(
            title="Choose cover image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"), ("All files", "*.*")]
        )
        if path:
            var.set(path)

    def _import_cover(self, var, game_title):
        src = filedialog.askopenfilename(
            title="Import cover image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"), ("All files", "*.*")]
        )
        if not src:
            return

        os.makedirs("covers", exist_ok=True)
        ext = os.path.splitext(src)[1]
        safe_title = "".join(c for c in (game_title or "cover") if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        if not safe_title:
            safe_title = "cover"
        dest = os.path.join("covers", f"{safe_title}{ext}")

        try:
            shutil.copy(src, dest)
            var.set(dest)
            messagebox.showinfo("Import cover", f"Cover imported to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Import cover error", str(e))

    def _browse_launcher(self, var):
        path = filedialog.askopenfilename(
            title="Choose launcher or EXE",
            filetypes=[
                ("Executable files", "*.exe *.bat *.lnk"),
                ("All files", "*.*"),
            ]
        )
        if path:
            var.set(path)

    def _fill_epic_example(self, launcher_type_var, launcher_var):
        launcher_type_var.set("epic")
        launcher_var.set("com.epicgames.launcher://apps/YOUR_APP_ID?action=launch&silent=true")

    def delete_selected(self):
        if self.selected_game_id is None:
            messagebox.showinfo("Delete", "Select a game first.")
            return

        game = self.db.get_game(self.selected_game_id)
        if not game:
            messagebox.showerror("Delete", "Selected game no longer exists.")
            return

        ok = messagebox.askyesno("Delete game", f"Delete '{game.title}'?")
        if not ok:
            return

        self.db.delete_game(game.id)
        self.selected_game_id = None
        self.refresh()
        if self.on_data_changed:
            self.on_data_changed()