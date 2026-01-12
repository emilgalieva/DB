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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player (
                id INTEGER PRIMARY KEY, value INTEGER
            )
        """)
        # cursor.execute("""
        #     CREATE TABLE IF NOT EXISTS  (
        #         id INTEGER PRIMARY KEY, value INTEGER
        #     )
        # """)
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

def save_player(player: "Player"):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            DELETE from player
                    WHERE TRUE
            """)
        cur.execute(f"""
            INSERT INTO player (id, value) VALUES((1, {BaseLevel.current_level}))
        """)
        cur.execute(f"""
            INSERT INTO player (id, value) VALUES((2, {player.hp}))
        """)
        cur.execute(f"""
            INSERT INTO player (id, value) VALUES((3, {player.energy}))
        """)
        for i, el in enumerate(player.inventory):
            cur.execute(f"""
                INSERT INTO player (id, value) VALUES(({i + 4}, {el}))
            """)
        conn.commit()

def load_player(player: "Player"):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        new_current_level = cur.execute("""SELECT value
                                   FROM player
                                   WHERE id = 1""").fetchone()
        if new_current_level is not None:
            BaseLevel.current_level = new_current_level
        #already has check
        player.hp = cur.execute("""SELECT value FROM player WHERE id=2""").fetchone()
        # already has check
        player.energy = cur.execute("""SELECT value
                                       FROM player
                                       WHERE id = 3""").fetchone()
        new_inventory = cur.execute("""
            SELECT value FROM player WHERE id > 3
        """).fetchall()
        player.inventory = [] if new_inventory is None else new_inventory