import enum
from zipfile import compressor_names

import arcade
from pyglet.graphics import Batch
from settings import *
from engine.Player import Player

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

class Items(enum.Enum):
    PISTOL = 1
    SUBMACHINE_GUN = 2
    AK_47 = 3
    MEDICINE = 4
    PAIN_KILLER = 5
    PISTOL_AMMO = 6
    AK_47_AMMO = 7


class Button(arcade.Sprite):
    def __init__(self, texture, scale, x, y, angle=0, func=None):
        super().__init__(texture, scale, x, y, angle)
        self.connected_to = func

    def connect(self, func):
        self.connected_to = func

    def press(self):
        if self.connected_to is not None:
            self.connected_to()


class SliderButton(arcade.Sprite):
    LEVER_OUTLINE = 2
    def __init__(self, path_or_texture, scale, center_x, center_y, lever_color, lever_width, func):
        super().__init__(path_or_texture, scale, center_x, center_y)
        self.lever_color = lever_color
        self.lever_width = lever_width
        self.connected_to = func
        self.lever_x = self.center_x - self.width // 2 + SliderButton.LEVER_OUTLINE + (self.lever_width - 1) / 2

    def connect(self, func):
        self.connected_to = func

    def press(self, x):
        self.lever_x = (self.center_x - self.width // 2 + SliderButton.LEVER_OUTLINE + (self.lever_width - 1) / 2
                        if x - self.center_x + self.width // 2 - SliderButton.LEVER_OUTLINE - (
                    self.lever_width - 1) / 2 < 0 else
                        self.center_x + self.width // 2 - SliderButton.LEVER_OUTLINE - (self.lever_width - 1) / 2
                        if x - self.center_x - self.width // 2 + SliderButton.LEVER_OUTLINE + (
                                    self.lever_width - 1) / 2 > 0 else x)
        if self.connected_to is not None:
            self.connected_to(int((x - self.center_x + self.width // 2 - SliderButton.LEVER_OUTLINE -
                                     (self.lever_width - 1) / 2)
                                    / (self.width - SliderButton.LEVER_OUTLINE * 2 - self.lever_width + 1) * 100))

    def draw_lever(self):
        arcade.draw_line(self.lever_x, self.center_y + self.height / 2 - SliderButton.LEVER_OUTLINE, self.lever_x,
                         self.center_y - self.height / 2 + SliderButton.LEVER_OUTLINE, self.lever_color,
                         line_width=self.lever_width)


class NewGameView(arcade.View):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.window.show_view(self.parent.game_view)

    def on_draw(self):
        self.clear()


class LoadGameView(arcade.View):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.temp_batch = Batch()
        self.temp_text = arcade.Text("Under Construction", 100, self.window.height // 2, batch=self.temp_batch)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        self.temp_batch.draw()


class SettingsView(arcade.View):
    CELL_SIZE = 100
    UP_SPACE = 100

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.settings_batch = Batch()
        lever_funcs = (self.change_volume, self.change_brightness, self.change_hud_size)
        lever_text = ("Brightness", "Volume", "HUD size")
        lever_textures = ("assets/Settings/lever_settings.png", "assets/Settings/lever_settings.png",
                          "assets/Settings/lever_settings.png")
        self.lever_list = arcade.SpriteList()
        self.button_list = arcade.SpriteList()
        self.text_list = []
        self.bright = 50
        self.volume = 50
        self.hud_size = 50
        for i in range(len(lever_funcs)):
            self.lever_list.append(SliderButton(lever_textures[i], 1, 740, SCREEN_HEIGHT -
                                                SettingsView.UP_SPACE - i * SettingsView.CELL_SIZE,
                                                (127, 127, 127), 4, lever_funcs[i]))
            self.text_list.append(arcade.Text(lever_text[i], 100, SCREEN_HEIGHT -
                                              SettingsView.UP_SPACE - i * SettingsView.CELL_SIZE,
                                              batch=self.settings_batch))
        self.button_list.append(Button("assets/Settings/button_back_to_menu.png", 1, 300, SCREEN_HEIGHT
                                       - SettingsView.UP_SPACE - len(lever_funcs) * SettingsView.CELL_SIZE,0,
                                       self.to_main_menu))

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        self.lever_list.draw()
        for el in self.lever_list:
            el.draw_lever()
        self.settings_batch.draw()
        self.button_list.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        for el in arcade.get_sprites_at_point((x, y), self.lever_list):
            el.press(x)
        for el in arcade.get_sprites_at_point((x, y), self.button_list):
            el.press()

    def change_volume(self, volume):
        self.volume = volume
        print("volume:", volume)

    def change_brightness(self, brightness):
        self.bright = brightness
        print("brightness: ", brightness)

    def change_hud_size(self, size):
        self.hud_size = size
        print("hud_size:", size)

    def to_main_menu(self):
        self.window.show_view(self.parent)


class EndingsView(arcade.View):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.temp_batch = Batch()
        self.temp_text = arcade.Text("Under Construction", 100, self.window.height // 2, batch=self.temp_batch)

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        self.temp_batch.draw()


class StartView(arcade.View):
    def __init__(self):
        super().__init__()
        self.game_view = BaseLevel("null_level.json")
        self.new_game_view = NewGameView(self)
        self.load_game_view = LoadGameView(self)
        self.settings_view = SettingsView(self)
        self.endings_view = EndingsView(self)
        self.cell_size = (self.window.height - 150) // 4
        self.menu_batch = Batch()
        self.menu_elements = arcade.SpriteList()
        menu_textures = ("assets/MainMenu/button_new_game.png", "assets/MainMenu/button_load_game.png",
                         "assets/MainMenu/button_settings.png", "assets/MainMenu/button_endings.png")
        menu_funcs = (self.new_game, self.load_game, self.settings, self.endings)
        for i in range(4):
            self.menu_elements.append(Button(menu_textures[i], 0.5, 200,
                                             self.window.height - self.cell_size * (i + 1), func=menu_funcs[i]))
    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        self.menu_elements.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        for el in arcade.get_sprites_at_point((x, y), self.menu_elements):
            el.press()

    def new_game(self):
        self.window.show_view(self.new_game_view)

    def load_game(self):
        self.window.show_view(self.load_game_view)

    def settings(self):
        self.window.show_view(self.settings_view)

    def endings(self):
        self.window.show_view(self.endings_view)


class BaseLevel(arcade.View):
    def __init__(self, tilemap_path):
        super().__init__(background_color=(0, 0, 0))
        self.tilemap = tilemap_path
        self.player_list = arcade.SpriteList()
        self.walls = None
        self.background = None
        self.ladders = None
        self.physics_engine = None
        self.keyboard_pressed = set()
        self.scene = None

    def on_show_view(self):
        self.tilemap = arcade.load_tilemap(self.tilemap)
        self.scene = arcade.Scene.from_tilemap(self.tilemap)
        self.player_list.append(Player("assets/Player/idle/default_idle.png", 2,
                                       *(200, 400)))
        # self.items = arcade.SpriteList()
        # self.exits = self.tilemap.sprite_lists["exits"]
        self.walls = self.tilemap.sprite_lists["walls"]
        self.ladders = self.tilemap.sprite_lists["ladders"]
        self.background = self.tilemap.sprite_lists["background"]
        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_list[0], gravity_constant=GRAVITY_CONSTANT,
                                                             walls=self.walls, ladders=self.ladders)

    def on_draw(self):
        self.clear()
        self.background.draw()
        self.walls.draw()
        self.ladders.draw()
        self.player_list.draw()

    def on_update(self, delta_time):
        is_on_ladder = self.physics_engine.is_on_ladder()
        can_jump = self.physics_engine.can_jump(1)
        if self.player_list[0].buffer_jump_timer is not None:
            self.player_list[0].buffer_jump_timer += delta_time
            if self.player_list[0].buffer_jump_timer > PLAYER_JUMP_BUFFER:
                self.player_list[0].buffer_jump_timer = None
        if can_jump or is_on_ladder:
            self.player_list[0].jumps = 0
            self.player_list[0].change_y = 0
            self.player_list[0].change_x = 0
            if self.player_list[0].coyote_jump_timer is None:
                self.player_list[0].coyote_jump_timer = 0
            elif self.player_list[0].coyote_jump_timer <= PLAYER_JUMP_COYOTE_TIME:
                self.player_list[0].coyote_jump_timer += delta_time
                if self.player_list[0].coyote_jump_timer > PLAYER_JUMP_COYOTE_TIME:
                    self.player_list[0].coyote_jump_timer = None
            if arcade.key.A in self.keyboard_pressed:
                self.player_list[0].change_x = (-self.player_list[0].walk_speed *
                                                    (PLAYER_SPRINT_K if self.player_list[0].shift_pressed else 1))
            if arcade.key.D in self.keyboard_pressed:
                self.player_list[0].change_x = (self.player_list[0].walk_speed *
                                                    (PLAYER_SPRINT_K if self.player_list[0].shift_pressed else 1))
        elif self.player_list[0].change_x > 0:
            self.player_list[0].change_x = max(self.player_list[0].change_x - X_SPEED_FALL * delta_time, 0)
        elif self.player_list[0].change_x < 0:
            self.player_list[0].change_x = min(self.player_list[0].change_x + X_SPEED_FALL * delta_time, 0)
        if arcade.key.W in self.keyboard_pressed:
            if is_on_ladder:
                self.player_list[0].change_y = (self.player_list[0].climb_speed *
                                                    (PLAYER_SPRINT_K if self.player_list[0].shift_pressed else 1))
            elif can_jump or ((self.player_list[0].coyote_jump_timer is not None
                               or self.player_list[0].buffer_jump_timer is not None)
                              and self.player_list[0].jumps == 0):
                self.player_list[0].change_x *= JUMP_X_BOOST_K
                self.player_list[0].jumps = 1
                self.physics_engine.jump(self.player_list[0].jump_speed)
            else:
                self.player_list[0].buffer_jump_timer = 0
        if arcade.key.S in self.keyboard_pressed and is_on_ladder:
            self.player_list[0].change_y = (-self.player_list[0].climb_speed *
                                                    (PLAYER_SPRINT_K if self.player_list[0].shift_pressed else 1))
        self.player_list[0].change_x *= delta_time
        if is_on_ladder:
            self.player_list[0].change_y *= delta_time
        self.player_list[0].change_direction()
        self.physics_engine.update()
        self.player_list[0].change_x /= delta_time
        if is_on_ladder:
            self.player_list[0].change_y /= delta_time

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        self.keyboard_pressed.add(symbol)
        if symbol == arcade.key.LSHIFT or symbol == arcade.key.RSHIFT:
            self.player_list[0].shift_pressed = True

    def on_key_release(self, symbol: int, modifiers: int) -> bool | None:
        self.keyboard_pressed.discard(symbol)
        if symbol == arcade.key.LSHIFT or symbol == arcade.key.RSHIFT:
            self.player_list[0].shift_pressed = False

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.player_list[0].is_in_aiming = True

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.player_list[0].is_in_aiming = False


if __name__ == "__main__":
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Deadly Bite")
    start_view = StartView()
    window.show_view(start_view)
    arcade.run()
