import sqlite3

DB_NAME = "game.db"


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                volume REAL
            )
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO settings (id, volume)
            VALUES (1, 0.5)
        """)
        conn.commit()


def save_volume(volume: float):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "UPDATE settings SET volume=? WHERE id=1",
            (volume,)
        )
        conn.commit()


def load_volume() -> float:
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT volume FROM settings WHERE id=1")
        return cur.fetchone()[0]
