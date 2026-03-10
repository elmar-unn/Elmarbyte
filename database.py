import sqlite3
from typing import Optional

from models import Game


class Database:
    # sqlite andmebaasi klass
    def __init__(self, path: str = "elmarbyte.db"):
        # loo ühendus
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row

        # loo tabelid
        self.create_tables()

        # uuenda vanu skeeme
        self.migrate_tables()

        # lisa testandmed
        self.seed_if_empty()

    # tabelite loomine
    def create_tables(self):
        cur = self.conn.cursor()

        # mängude tabel
        cur.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            platform TEXT NOT NULL,
            genre TEXT NOT NULL,
            rating INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Backlog',
            favorite INTEGER NOT NULL DEFAULT 0,
            cover_path TEXT DEFAULT '',
            launcher_type TEXT DEFAULT 'local_file',
            launcher_path TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        )
        """)

        self.conn.commit()

    # skeemi migratsioon
    def migrate_tables(self):
        cur = self.conn.cursor()
        cur.execute("PRAGMA table_info(games)")
        cols = [row["name"] for row in cur.fetchall()]

        # puuduva veeru lisamine
        if "cover_path" not in cols:
            cur.execute("ALTER TABLE games ADD COLUMN cover_path TEXT DEFAULT ''")

        # puuduva veeru lisamine
        if "launcher_type" not in cols:
            cur.execute("ALTER TABLE games ADD COLUMN launcher_type TEXT DEFAULT 'local_file'")

        # puuduva veeru lisamine
        if "launcher_path" not in cols:
            cur.execute("ALTER TABLE games ADD COLUMN launcher_path TEXT DEFAULT ''")

        # puuduva veeru lisamine
        if "notes" not in cols:
            cur.execute("ALTER TABLE games ADD COLUMN notes TEXT DEFAULT ''")

        self.conn.commit()

    # demoandmete lisamine
    def seed_if_empty(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) AS count FROM games")

        if cur.fetchone()["count"] > 0:
            return

        # näidisread
        sample_games = [
            ("Dead Cells", "PC", "Roguelike", 9, "Playing", 1, "", "local_file", "", "Hea kiire mäng."),
            ("Gunpoint", "PC", "Strategy", 9, "Completed", 1, "", "steam_shortcut", "", "Väga stiilne indie."),
            ("Fortnite", "PC", "Shooter", 7, "Playing", 0, "", "epic_uri", "", "Epic näide."),
        ]

        cur.executemany("""
        INSERT INTO games
        (title, platform, genre, rating, status, favorite, cover_path, launcher_type, launcher_path, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_games)

        self.conn.commit()

    # mängude lugemine filtritega
    def get_games(self, search="", platform="All", genre="All", status="All", favorites_only=False):
        cur = self.conn.cursor()

        # algne query
        query = "SELECT * FROM games WHERE 1=1"
        params = []

        # otsingu filter
        if search.strip():
            term = f"%{search.strip().lower()}%"
            query += " AND (LOWER(title) LIKE ? OR LOWER(platform) LIKE ? OR LOWER(genre) LIKE ?)"
            params.extend([term, term, term])

        # platvormi filter
        if platform != "All":
            query += " AND platform = ?"
            params.append(platform)

        # žanri filter
        if genre != "All":
            query += " AND genre = ?"
            params.append(genre)

        # staatuse filter
        if status != "All":
            query += " AND status = ?"
            params.append(status)

        # favoriitide filter
        if favorites_only:
            query += " AND favorite = 1"

        # sorteerimine
        query += " ORDER BY title COLLATE NOCASE ASC"

        cur.execute(query, params)
        return [Game.from_row(row) for row in cur.fetchall()]

    # ühe mängu lugemine
    def get_game(self, game_id: int) -> Optional[Game]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM games WHERE id = ?", (game_id,))
        row = cur.fetchone()
        return Game.from_row(row) if row else None

    # mängu lisamine
    def add_game(self, title, platform, genre, rating, status, favorite, cover_path, launcher_type, launcher_path, notes):
        cur = self.conn.cursor()

        cur.execute("""
        INSERT INTO games
        (title, platform, genre, rating, status, favorite, cover_path, launcher_type, launcher_path, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            platform,
            genre,
            rating,
            status,
            favorite,
            cover_path,
            launcher_type,
            launcher_path,
            notes
        ))

        self.conn.commit()

    # mängu muutmine
    def update_game(self, game_id, title, platform, genre, rating, status, favorite, cover_path, launcher_type, launcher_path, notes):
        cur = self.conn.cursor()

        cur.execute("""
        UPDATE games
        SET
            title = ?,
            platform = ?,
            genre = ?,
            rating = ?,
            status = ?,
            favorite = ?,
            cover_path = ?,
            launcher_type = ?,
            launcher_path = ?,
            notes = ?
        WHERE id = ?
        """, (
            title,
            platform,
            genre,
            rating,
            status,
            favorite,
            cover_path,
            launcher_type,
            launcher_path,
            notes,
            game_id
        ))

        self.conn.commit()

    # mängu kustutamine
    def delete_game(self, game_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM games WHERE id = ?", (game_id,))
        self.conn.commit()

    # platvormide loetelu
    def get_platforms(self):
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT platform FROM games ORDER BY platform")
        return [row["platform"] for row in cur.fetchall()]

    # žanrite loetelu
    def get_genres(self):
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT genre FROM games ORDER BY genre")
        return [row["genre"] for row in cur.fetchall()]

    # staatuste loetelu
    def get_statuses(self):
        return ["Backlog", "Playing", "Completed", "Dropped"]