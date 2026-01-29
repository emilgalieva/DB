import sqlite3

from engine.BaseLevel import create_item_from_camp
# from engine.BaseLevel import create_item_from_camp, BaseLevel
from engine.Game import *
from engine.Item import Ammo, Item
from engine.Weapon import Weapon

DB_NAME = "Saves/game.db"


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


def save_player(player: "Player"):
    with open(DB_NAME, "w"):
        pass
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE player (id, value)""")
        cur.execute(f"""
            INSERT INTO player (id, value) VALUES(1, {Game.current_level})
        """)
        cur.execute(f"""
            INSERT INTO player (id, value) VALUES(2, {player.hp})
        """)
        cur.execute(f"""
            INSERT INTO player (id, value) VALUES(3, {player.energy})
        """)
        cur.execute(f"""
                    INSERT INTO player (id, value) VALUES(4, {Game.strikes_done})
        """)
        cur.execute(f"""
                    INSERT INTO player (id, value) VALUES(5, {Game.zombies_killed})
        """)
        cur.execute(f"""
                            INSERT INTO player (id, value) VALUES(6, {player.money})
                """)
        cur.execute(f"""
                            INSERT INTO player (id, value) VALUES(7, {Game.volume})
        """)
        cur.execute("""CREATE TABLE simple_items (id, value)""")
        cur.execute("""CREATE TABLE ammo (id, value, ammo)""")
        cur.execute("""CREATE TABLE weapons (id, value, ammo, modifier)""")
        simple_items_id = 0
        weapons_id = 0
        ammo_id = 0
        for i, el in enumerate(player.inventory):
            if isinstance(el, Item):
                cur.execute(
                    f"""INSERT INTO simple_items (id, value) VALUES({simple_items_id}, {el.item_id})""")
                simple_items_id += 1
            elif isinstance(el, Weapon):
                cur.execute(f"""INSERT INTO weapons (id, value, ammo, modifier) VALUES({weapons_id}, {el.item_id},
                    {el.ammo}, {el.modifier.item_id})""")
                weapons_id += 1
            elif isinstance(el, Ammo):
                cur.execute(
                    f"""INSERT INTO ammo (id, value, ammo) VALUES({ammo_id}, {el.item_id}, {el.bullets})""")
                ammo_id += 1
            elif i < player.inventory.equipped_size:
                cur.execute(
                    f"""INSERT INTO simple_items (id, value) VALUES({simple_items_id}, -1)""")
                simple_items_id += 1
        conn.commit()


def load_in_player(player: "Player"):
    with (sqlite3.connect(DB_NAME) as conn):
        cur = conn.cursor()
        (Game.current_level, player._hp, player._energy, Game.strikes_done, Game.zombies_killed, player.money,
            Game.volume) = (
            el[0] for el in cur.execute("""SELECT value FROM player""").fetchall())
        for i in range(player.inventory.equipped_size):
            result = cur.execute(f"""SELECT value FROM 
            simple_items WHERE id = {i} AND value != -1""").fetchone()
            if result is not None:
                player.inventory[i] = create_item_from_camp(result)
        for el in cur.execute(f"""SELECT value from simple_items WHERE id >= {player.inventory.equipped_size} 
                AND value != -1""").fetchall():
            player.inventory.append(create_item_from_camp(el))
        for el in cur.execute(f"""SELECT value, ammo from ammo""").fetchall():
            item = create_item_from_camp(el[0])
            item.bullets = el[1]
            player.inventory.append(item)
        for el in cur.execute(f"""SELECT value, ammo, modifier from weapons""").fetchall():
            item = create_item_from_camp(el[0])
            item.bullets = el[1]
            item.modifier = create_item_from_camp(el[2])
            player.inventory.append(item)
