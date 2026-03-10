import sqlite3
from typing import Optional

from models import Game


class Database:
    def __init__(self, path: str = "gamevault.db"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.migrate_tables()
        self.seed_if_empty()

    def create_tables(self):
        cur = self.conn.cursor()
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
            launcher_type TEXT DEFAULT 'file',
            launcher_path TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        )
        """)
        self.conn.commit()

    def migrate_tables(self):
        cur = self.conn.cursor()
        cur.execute("PRAGMA table_info(games)")
        cols = [row["name"] for row in cur.fetchall()]

        if "launcher_path" not in cols:
            cur.execute("ALTER TABLE games ADD COLUMN launcher_path TEXT DEFAULT ''")

        if "launcher_type" not in cols:
            cur.execute("ALTER TABLE games ADD COLUMN launcher_type TEXT DEFAULT 'file'")

        if "notes" not in cols:
            cur.execute("ALTER TABLE games ADD COLUMN notes TEXT DEFAULT ''")

        self.conn.commit()

    def seed_if_empty(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) AS count FROM games")
        count = cur.fetchone()["count"]
        if count > 0:
            return

        samples = [
            ("Elden Ring", "PC", "RPG", 10, "Completed", 1, "", "file", "", "Huge open-world action RPG."),
            ("Hades", "PC", "Roguelike", 9, "Playing", 1, "", "file", "", "Fast runs and great voice acting."),
            ("Cyberpunk 2077", "PC", "Action RPG", 8, "Backlog", 0, "", "file", "", "Need to finish Phantom Liberty too."),
            ("Fortnite", "PC", "Shooter", 8, "Playing", 0, "", "epic", "", "Can be launched through Epic."),
        ]

        cur.executemany("""
        INSERT INTO games (
            title, platform, genre, rating, status, favorite,
            cover_path, launcher_type, launcher_path, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, samples)

        self.conn.commit()

    def get_games(self, search="", platform="All", genre="All", status="All", favorites_only=False):
        cur = self.conn.cursor()
        query = "SELECT * FROM games WHERE 1=1"
        params = []

        if search.strip():
            term = f"%{search.strip().lower()}%"
            query += " AND (LOWER(title) LIKE ? OR LOWER(platform) LIKE ? OR LOWER(genre) LIKE ?)"
            params.extend([term, term, term])

        if platform != "All":
            query += " AND platform = ?"
            params.append(platform)

        if genre != "All":
            query += " AND genre = ?"
            params.append(genre)

        if status != "All":
            query += " AND status = ?"
            params.append(status)

        if favorites_only:
            query += " AND favorite = 1"

        query += " ORDER BY title COLLATE NOCASE ASC"

        cur.execute(query, params)
        return [Game.from_row(row) for row in cur.fetchall()]

    def get_game(self, game_id: int) -> Optional[Game]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM games WHERE id = ?", (game_id,))
        row = cur.fetchone()
        return Game.from_row(row) if row else None

    def add_game(
        self,
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
    ):
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO games (
            title, platform, genre, rating, status, favorite,
            cover_path, launcher_type, launcher_path, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, platform, genre, rating, status, favorite,
            cover_path, launcher_type, launcher_path, notes
        ))
        self.conn.commit()

    def update_game(
        self,
        game_id,
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
    ):
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
            title, platform, genre, rating, status, favorite,
            cover_path, launcher_type, launcher_path, notes, game_id
        ))
        self.conn.commit()

    def delete_game(self, game_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM games WHERE id = ?", (game_id,))
        self.conn.commit()

    def get_platforms(self):
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT platform FROM games ORDER BY platform")
        return [row["platform"] for row in cur.fetchall()]

    def get_genres(self):
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT genre FROM games ORDER BY genre")
        return [row["genre"] for row in cur.fetchall()]

    def get_statuses(self):
        return ["Backlog", "Playing", "Completed", "Dropped"]

    def get_stats(self):
        cur = self.conn.cursor()

        cur.execute("SELECT COUNT(*) AS count FROM games")
        total = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) AS count FROM games WHERE status = 'Completed'")
        completed = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) AS count FROM games WHERE status = 'Playing'")
        playing = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) AS count FROM games WHERE favorite = 1")
        favorites = cur.fetchone()["count"]

        cur.execute("SELECT ROUND(AVG(rating), 1) AS avg_rating FROM games")
        avg_rating = cur.fetchone()["avg_rating"] or 0

        cur.execute("""
        SELECT title, rating
        FROM games
        ORDER BY rating DESC, title ASC
        LIMIT 1
        """)
        top = cur.fetchone()
        top_game = f"{top['title']} ({top['rating']}/10)" if top else "-"

        cur.execute("""
        SELECT status, COUNT(*) AS count
        FROM games
        GROUP BY status
        ORDER BY count DESC
        """)
        status_breakdown = [(row["status"], row["count"]) for row in cur.fetchall()]

        return {
            "total": total,
            "completed": completed,
            "playing": playing,
            "favorites": favorites,
            "avg_rating": avg_rating,
            "top_game": top_game,
            "status_breakdown": status_breakdown,
        }