import arcade
from pytiled_parser.tiled_object import Tile

import arcade.gui
from engine.HUD import *
from engine.Weapon import Weapon
from engine.Item import *
from settings import HP_HUD_ICON_TEXTURE, ENERGY_HUD_ICON_TEXTURE, GRAVITY_CONSTANT, PISTOL_SETUP, NIGHT_GOOGLES_SETUP, \
    PAIN_KILLER_SETUP, ADRENALINE_SETUP, MEDICINE_SETUP, ARMOR_SETUP, SCREEN_WIDTH, AUTO_PISTOL_SETUP, AS_RIFLE_SETUP, \
    PISTOL_AMMO_SETUP, AS_RIFLE_AMMO_SETUP

ITEMS_SIZES = ((60, 25), (60, 25), (75, 32))

ITEMS = ((Weapon, PISTOL_SETUP), (Weapon, AUTO_PISTOL_SETUP), (Weapon, AS_RIFLE_SETUP),
         (TemporaryItem, (Effect(*MEDICINE_SETUP),)),
         (TemporaryItem, (TempEffectWithCancel(*ADRENALINE_SETUP),)),
         (TemporaryItem, (TempEffectWithCancel(*PAIN_KILLER_SETUP),)),
          (EquippableItem, (EquippableItem.FOR_HEAD, Effect(*NIGHT_GOOGLES_SETUP))),
         (EquippableItem, (EquippableItem.FOR_BODY, Effect(*ARMOR_SETUP))), (Ammo, PISTOL_AMMO_SETUP),
         (Ammo, AS_RIFLE_AMMO_SETUP))

def create_items(tiled_objects, sprites, tilemap):
    new_items = arcade.SpriteList()
    height = tilemap.tile_height * tilemap.height
    for obj, spr in zip(tiled_objects, sprites):
        new_items.append(ITEMS[obj.properties["item_id"]][0](spr.texture, spr.scale, obj.coordinates.x + spr.width // 2,
                                                             height - obj.coordinates.y + spr.height // 2, obj.rotation,
                                              *ITEMS[obj.properties["item_id"]][1]))
        if 0 < obj.properties["item_id"] < 3:
            new_items[-1].size = ITEMS_SIZES[obj.properties["item_id"]]
    return new_items

class BaseLevel(arcade.View):
    ALLOWED_KEYBOARD_KEYS = ("W", "A", "S", "D", "E",
                             "T", "Q", "R", "LSHIFT", "RSHIFT")
    levels = []
    current_level = 0
    camp_level = None
    player = None
    game_on_pause = False

    def __init__(self, tilemap_path):
        super().__init__(background_color=(0, 0, 0))
        self.tilemap = tilemap_path
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

    def on_show_view(self):
        if not BaseLevel.game_on_pause:
            if isinstance(self.tilemap, str):
                self.tilemap = arcade.load_tilemap(self.tilemap, layer_options={
                    "walls": {
                        "use_spatial_hash": True
                    },
                    "ladders": {
                        "use_spatial_hash": True
                    },
                })
            self.warning_label = arcade.gui.UILabel(x=self.window.width // 2, y=self.window.height // 2,
                                                    text_color=arcade.color.GRAY, bold=True)
            BaseLevel.player.position = self.tilemap.sprite_lists["player_spawn"][0].position
            self.gui_camera = arcade.Camera2D()
            self.game_camera = arcade.Camera2D()
            self.items = create_items(self.tilemap.get_tilemap_layer("items").tiled_objects,
                                      self.tilemap.sprite_lists["items"], self.tilemap)
            self.exits = self.tilemap.sprite_lists["exits"]
            self.walls = self.tilemap.sprite_lists["walls"]
            self.ladders = self.tilemap.sprite_lists["ladders"]
            self.background = self.tilemap.sprite_lists["background"]
            for el in BaseLevel.player.inventory:
                if isinstance(el, Weapon):
                    el.walls = self.walls
                    # el.enemies = self.enemies
                    BaseLevel.player.draw_list.append(el.bullet)
            for el in self.items:
                if isinstance(el, Weapon):
                    el.walls = self.walls
                    # el.enemies = self.enemies
                    BaseLevel.player.draw_list.append(el.bullet)
            self.gui_manager = arcade.gui.UIManager()
            self.gui_manager.add(self.warning_label)
            self.physics_engine = arcade.PhysicsEnginePlatformer(BaseLevel.player, gravity_constant=GRAVITY_CONSTANT,
                                                                 walls=self.walls, ladders=self.ladders)
            BaseLevel.player.physics_engine = self.physics_engine
            BaseLevel.player.level_items = self.items
        else:
            BaseLevel.game_on_pause = False

    def on_hide_view(self) -> None:
        self.gui_manager.clear()

    def remove_temp_message(self, delta_time):
        self.warning_label.text = ""
        arcade.unschedule(self.remove_temp_message)

    def show_temp_message(self, text="", duration=1):
        arcade.schedule(self.remove_temp_message, duration)
        self.warning_label.text = text


    def drop(self, item: arcade.Sprite):
        while not arcade.check_for_collision_with_list(item, self.walls):
            item.center_y -= 4

    def on_draw(self):
        self.clear((0, 0, 0, 255))
        self.game_camera.use()
        self.background.draw()
        self.exits.draw()
        self.walls.draw()
        self.ladders.draw()
        self.items.draw()
        BaseLevel.player.draw_list.draw()
        for el in BaseLevel.player.particle_systems:
            el.draw()
        self.gui_camera.use()
        self.gui_manager.draw()
        self.stamina_HUD.show(BaseLevel.player.energy)
        self.hp_HUD.show(BaseLevel.player.hp)

    def on_update(self, delta_time):
        BaseLevel.player.update(self.keyboard_pressed,
                                self.mouse_events, delta_time)
        self.game_camera.position = BaseLevel.player.position
        if not self.exit_blocked and arcade.check_for_collision_with_list(BaseLevel.player, self.exits):
            if BaseLevel.current_level < len(BaseLevel.levels) - 1:
                BaseLevel.current_level += 1
                self.window.show_view(BaseLevel.camp_level)
            # else:
            #     self.window.show_view(BaseLevel.finish_screen)

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
        if BaseLevel.player.is_in_aiming:
            self.mouse_events["POS"] = [x, y]

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.mouse_events["RIGHT"] = True
            # BaseLevel.player.is_in_aiming = not BaseLevel.player.is_in_aiming
        elif button == arcade.MOUSE_BUTTON_LEFT:
            self.mouse_events["LEFT"] = True
        elif button == arcade.MOUSE_BUTTON_MIDDLE:
            self.mouse_events["MIDDLE"] = True

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.mouse_events["RIGHT"] = False
            # BaseLevel.player.is_in_aiming = not BaseLevel.player.is_in_aiming
        elif button == arcade.MOUSE_BUTTON_LEFT:
            self.mouse_events["LEFT"] = False
        elif button == arcade.MOUSE_BUTTON_MIDDLE:
            self.mouse_events["MIDDLE"] = False

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> bool | None:
        self.mouse_events["SCROLL"] = scroll_y