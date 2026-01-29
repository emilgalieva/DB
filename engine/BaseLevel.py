import arcade.color
import arcade.gui
import random
from engine.HUD import *
from engine.Weapon import Weapon
from engine.Item import *
from engine.Zombie import Zombie
from settings import *
from engine.Game import *

# ITEMS_SIZES = ((60, 25), (60, 25), (75, 32))

ITEMS = ((Weapon, PISTOL_SETUP), (Weapon, AUTO_PISTOL_SETUP), (Weapon, AS_RIFLE_SETUP),
         (TemporaryItem, (Effect(*MEDICINE_SETUP),)),
         (TemporaryItem, (TempEffectWithCancel(*ADRENALINE_SETUP),)),
         (TemporaryItem, (TempEffectWithCancel(*PAIN_KILLER_SETUP),)),
         (EquippableItem, (EquippableItem.FOR_HEAD, Effect(*NIGHT_GOOGLES_SETUP))),
         (EquippableItem, (EquippableItem.FOR_BODY, Effect(
             *ARMOR_SETUP))), (Ammo, PISTOL_AMMO_SETUP),
         (Ammo, AS_RIFLE_AMMO_SETUP), (WeaponModification, (Effect(*ANTI_RECOIL_SETUP),)), (WeaponModification,
                                                                                            (Effect(
                                                                                                *LONG_BARREL_SETUP),)))


def create_items(tiled_objects, sprites, tilemap):
    new_items = arcade.SpriteList()
    height = tilemap.tile_height * tilemap.height
    for obj, spr in zip(tiled_objects, sprites):
        new_items.append(ITEMS[obj.properties["item_id"]][0](spr.texture, spr.scale, obj.coordinates.x + spr.width // 2,
                                                             height - obj.coordinates.y + spr.height // 2, obj.rotation,
                                                             *ITEMS[obj.properties["item_id"]][1],
                                                             obj.properties["item_id"]))
    return new_items


def create_item_from_camp(item_id):
    for el in Game.camp_level.items:
        if el.item_id == item_id:
            return el.copy()
    return None


def setup_weapon_enemies(self):
    for item in Game.player.inventory:
        if isinstance(item, Weapon):
            item.walls = self.walls
            item.enemies = self.zombies
            if item.bullet not in Game.player.draw_list:
                Game.player.draw_list.append(item.bullet)

    for item in self.items:
        if isinstance(item, Weapon):
            item.walls = self.walls
            item.enemies = self.zombies
            if item.bullet not in Game.player.draw_list:
                Game.player.draw_list.append(item.bullet)


class BaseLevel(arcade.View):
    ALLOWED_KEYBOARD_KEYS = ("W", "A", "S", "D", "E", "M", "I",
                             "T", "Q", "R", "LSHIFT", "RSHIFT")

    def __init__(self, tilemap_path, brightness):
        super().__init__(background_color=arcade.color.SKY_BLUE)
        Game.bright_control_sprite_list[0].alpha = 255 / brightness
        self.tilemap_path = tilemap_path
        self.tilemap = None
        self.walls = None
        self.background = None
        self.ladders = None
        self.physics_engine = None
        self.keyboard_pressed = {
            el: False for el in BaseLevel.ALLOWED_KEYBOARD_KEYS}
        self.mouse_events = {"LEFT": False, "RIGHT": False,
                             "MIDDLE": False, "SCROLL": 0, "POS": (0, 0)}
        self.gui_camera = None
        self.game_camera = None
        self.hp_HUD = HUD(HP_HUD_ICON_TEXTURE, 2, 20, 60, 100, (255, 20, 20),
                          (0, 0, 0))
        self.stamina_HUD = HUD(ENERGY_HUD_ICON_TEXTURE, 1, 20, 20, 100, (255, 255, 255),
                               (0, 0, 0))
        self.exits = None
        self.items = None
        self.warning_label = None
        self.gui_manager = None
        self.exit_blocked = False
        self.zombies = arcade.SpriteList()
        self.enemies = self.zombies
        self.zombie_spawn_timer = 0
        self.max_zombies = 1000
        self.zombie_spawn_interval = 8
        self.spawn_points = []

    def on_show_view(self):
        if not Game.game_on_pause:
            self.load_level()
        else:
            Game.game_on_pause = False
        self.gui_manager.enable()

    def load_level(self):
        try:
            self.tilemap = arcade.load_tilemap(self.tilemap_path, layer_options={
                "walls": {
                    "use_spatial_hash": True
                },
                "ladders": {
                    "use_spatial_hash": True
                },
                "exits": {
                    "use_spatial_hash": True
                },
                "zombie_spawns": {
                    "use_spatial_hash": True
                }
            })
            self.gui_camera = arcade.Camera2D()
            self.game_camera = arcade.Camera2D()
            self.load_map_layers()
            self.load_game_objects()
            self.create_physics_engine()
            self.load_zombies()
            self.init_gui()

        except Exception as e:
            import traceback
            traceback.print_exc()

    def load_map_layers(self):
        self.walls = self.tilemap.sprite_lists.get(
            "walls", arcade.SpriteList())
        self.ladders = self.tilemap.sprite_lists.get(
            "ladders", arcade.SpriteList())
        self.background = self.tilemap.sprite_lists.get(
            "background", arcade.SpriteList())
        self.exits = self.tilemap.sprite_lists.get(
            "exits", arcade.SpriteList())
        if "zombie_spawns" in self.tilemap.sprite_lists:
            self.spawn_points = self.tilemap.sprite_lists["zombie_spawns"]
        if "player_spawn" in self.tilemap.sprite_lists and len(self.tilemap.sprite_lists["player_spawn"]) > 0:
            spawn_sprite = self.tilemap.sprite_lists["player_spawn"][0]
            Game.player.center_x = spawn_sprite.center_x
            Game.player.center_y = spawn_sprite.center_y
            Game.player.change_x = 0
            Game.player.change_y = 0
        else:
            Game.player.center_x = 100
            Game.player.center_y = 100
            Game.player.change_x = 0
            Game.player.change_y = 0

    def load_game_objects(self):
        if "items" in self.tilemap.sprite_lists:
            try:
                items_layer = self.tilemap.get_tilemap_layer("items")
                if items_layer and hasattr(items_layer, 'tiled_objects'):
                    self.items = create_items(items_layer.tiled_objects,
                                              self.tilemap.sprite_lists["items"], self.tilemap)
                else:
                    self.items = arcade.SpriteList()
            except:
                self.items = arcade.SpriteList()
        else:
            self.items = arcade.SpriteList()

    def create_physics_engine(self):
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            Game.player,
            gravity_constant=GRAVITY_CONSTANT,
            walls=self.walls,
            ladders=self.ladders
        )
        Game.player.physics_engine = self.physics_engine
        Game.player.level_items = self.items

    def load_zombies(self):
        self.zombies = arcade.SpriteList()
        if "zombie" in self.tilemap.sprite_lists.keys():
            for zombie_sprite in self.tilemap.sprite_lists["zombie"]:
                zombie = Zombie(zombie_sprite.center_x,
                                zombie_sprite.center_y, self.walls)
                self.zombies.append(zombie)
        self.enemies = self.zombies
        self.setup_weapon_enemies()

    def setup_weapon_enemies(self):
        for item in Game.player.inventory:
            if isinstance(item, Weapon):
                item.walls = self.walls
                item.enemies = self.zombies
                if item.bullet not in Game.player.draw_list:
                    Game.player.draw_list.append(item.bullet)
        for item in self.items:
            if isinstance(item, Weapon):
                item.walls = self.walls
                item.enemies = self.zombies
                if item.bullet not in Game.player.draw_list:
                    Game.player.draw_list.append(item.bullet)

    def init_gui(self):
        self.gui_manager = arcade.gui.UIManager()
        self.warning_label = arcade.gui.UILabel(
            x=self.window.width // 2,
            y=self.window.height // 2,
            text="",
            text_color=arcade.color.GRAY,
            bold=True,
            align="center"
        )
        self.gui_manager.add(self.warning_label)

    def on_hide_view(self) -> None:
        Game.player.change_x = 0
        self.gui_manager.disable()

    def remove_temp_message(self, delta_time):
        self.warning_label.text = ""
        arcade.unschedule(self.remove_temp_message)

    def show_temp_message(self, text="", duration=1):
        arcade.schedule(self.remove_temp_message, duration)
        self.warning_label.text = text

    def drop(self, item: arcade.Sprite):
        if not self.walls:
            return

        while not arcade.check_for_collision_with_list(item, self.walls) and item.center_y > 0:
            item.center_y -= 4


    def on_draw(self):
        self.clear((0, 0, 0, 255))
        if self.game_camera:
            self.game_camera.use()

            if self.background:
                self.background.draw()
            if self.exits:
                self.exits.draw()
            if self.walls:
                self.walls.draw()
            if self.ladders:
                self.ladders.draw()
            if self.items:
                self.items.draw()
            if self.zombies:
                self.zombies.draw()

            if Game.player and Game.player.draw_list:
                Game.player.draw_list.draw()

            for el in Game.player.particle_systems:
                el.draw()

        if self.gui_camera:
            self.gui_camera.use()
            if self.gui_manager:
                self.gui_manager.draw()

        self.stamina_HUD.show(Game.player.energy)
        self.hp_HUD.show(Game.player.hp)

    def on_update(self, delta_time):
        if Game.player:
            Game.player.update(self.keyboard_pressed,
                               self.mouse_events, delta_time)
            self.game_camera.position = arcade.math.lerp_2d(self.game_camera.position,
                                                            Game.player.position, GAME_CAMERA_LERP)
            Game.bright_control_sprite_list[0].position = self.game_camera.position
        self.update_zombies(delta_time)

        if self.game_camera and Game.player:
            self.game_camera.position = Game.player.position

        self.check_exit()

    def update_zombies(self, delta_time):
        if not self.zombies:
            return

        zombies_to_remove = []

        for zombie in self.zombies:
            if zombie.is_alive:
                zombie.update(delta_time, Game.player)
            else:
                zombies_to_remove.append(zombie)

        for zombie in zombies_to_remove:
            self.zombies.remove(zombie)

        if Game.player:
            collided_zombies = arcade.check_for_collision_with_list(
                Game.player, self.zombies)
            for zombie in collided_zombies:
                if zombie.is_alive and zombie.invulnerable_timer <= 0:
                    zombie.attack(Game.player)

    def check_exit(self):
        if (not self.exit_blocked and Game.player and self.exits and
                arcade.check_for_collision_with_list(Game.player, self.exits)):
            if Game.current_level < len(Game.levels) - 1:
                Game.current_level += 1
                self.window.show_view(Game.camp_level)
            else:
                self.window.show_view(Game.finish_screen)

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        for el in BaseLevel.ALLOWED_KEYBOARD_KEYS:
            if symbol == eval(f"arcade.key.{el}"):
                self.keyboard_pressed[el] = True
                return

    def on_key_release(self, symbol: int, modifiers: int) -> bool | None:
        for el in BaseLevel.ALLOWED_KEYBOARD_KEYS:
            if symbol == eval(f"arcade.key.{el}"):
                self.keyboard_pressed[el] = False
                return

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        if Game.player and Game.player.is_in_aiming:
            self.mouse_events["POS"] = [x, y]

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.mouse_events["RIGHT"] = True
        elif button == arcade.MOUSE_BUTTON_LEFT:
            self.mouse_events["LEFT"] = True
        elif button == arcade.MOUSE_BUTTON_MIDDLE:
            self.mouse_events["MIDDLE"] = True

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.mouse_events["RIGHT"] = False
        elif button == arcade.MOUSE_BUTTON_LEFT:
            self.mouse_events["LEFT"] = False
        elif button == arcade.MOUSE_BUTTON_MIDDLE:
            self.mouse_events["MIDDLE"] = False

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> bool | None:
        self.mouse_events["SCROLL"] = scroll_y
