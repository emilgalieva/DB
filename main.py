import enum
import arcade
from pyglet.graphics import Batch
from settings import *
from engine.Player import Player
from engine.Weapon import Weapon
import arcade
import arcade.gui
from engine.database import save_volume, load_volume, init_db
import random

class HUD(arcade.Sprite):
    def __init__(self, icon, scale, center_x, center_y, hud_width, hud_fill_color, hud_outline_color):
        super().__init__(icon, scale, center_x, center_y)
        self.hud_width = hud_width
        self.hud_fill_color = hud_fill_color
        self.hud_outline_color = hud_outline_color
        self.draw_list = arcade.SpriteList()
        self.draw_list.append(self)

    def show(self, percent):
        percent /= 100
        self.draw_list.draw()
        arcade.draw_lbwh_rectangle_outline(self.center_x + self.width // 2 + 2, self.center_y - self.height // 2,
                                           self.hud_width, self.height, self.hud_outline_color, 2)
        arcade.draw_lbwh_rectangle_filled(self.center_x + self.width // 2 + 3, self.center_y - self.height // 2 + 1,
                                          (self.hud_width - 2) * percent, self.height - 2, self.hud_fill_color)

class Items(enum.Enum):
    PISTOL = 1
    SUBMACHINE_GUN = 2
    AK_47 = 3
    MEDICINE = 4
    PAIN_KILLER = 5
    PISTOL_AMMO = 6
    AK_47_AMMO = 7


class MainWindow(arcade.Window):
    def __init__(self, width, height, title, fullscreen, resizable):
        super().__init__(width, height, title, fullscreen, resizable)
        self.gui_manager = arcade.gui.UIManager(self)
        self.gui_manager.enable()

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
    def __init__(self):
        super().__init__()
        self.ui = arcade.gui.UIManager()
        self.volume = load_volume()

    def on_show_view(self):
        arcade.set_background_color(arcade.color.GRAY)
        self.ui.enable()
        self.ui.clear()

        slider = arcade.gui.UISlider(
            value=self.volume,
            min_value=0,
            max_value=1,
            width=300
        )
        slider.on_change = self.change_volume

        back_btn = arcade.gui.UIFlatButton(text="Назад", width=200)
        back_btn.on_click = self.back

        box = arcade.gui.UIBoxLayout(space_between=20)
        box.add(slider)
        box.add(back_btn)

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(box, anchor_x="center_x", anchor_y="center_y")
        self.ui.add(anchor)

    def change_volume(self, event):
        self.volume = event.new_value
        arcade.sound.set_volume(self.volume)
        save_volume(self.volume)

    def back(self, event):
        # from views.menu_view import MenuView
        self.window.show_view(MenuView())

    def on_draw(self):
        self.clear()
        self.ui.draw()

    def on_hide_view(self):
        self.ui.disable()




class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.ui = arcade.gui.UIManager()
        self.zombies = arcade.SpriteList()

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.ui.enable()
        self.ui.clear()

        # Зомби на фоне
        self.zombies = arcade.SpriteList()
        for _ in range(6):
            zombie = arcade.Sprite("assets/zombie.png", scale=0.5)
            zombie.center_x = random.randint(0, self.window.width)
            zombie.center_y = random.randint(0, self.window.height)
            zombie.change_x = random.uniform(-0.5, 0.5)
            self.zombies.append(zombie)

        title = arcade.gui.UILabel(
            text="ZOMBIE APOCALYPSE",
            font_size=42
        )

        new_game_btn = arcade.gui.UIFlatButton(text="Новая игра", width=250)
        settings_btn = arcade.gui.UIFlatButton(text="Настройки", width=250)

        new_game_btn.on_click = self.new_game
        settings_btn.on_click = self.open_settings

        box = arcade.gui.UIBoxLayout(space_between=20)
        box.add(title)
        box.add(new_game_btn)
        box.add(settings_btn)

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(box, anchor_x="center_x", anchor_y="center_y")
        self.ui.add(anchor)

    def on_update(self, delta_time):
        self.zombies.update()
        for zombie in self.zombies:
            if zombie.right < 0:
                zombie.left = self.window.width

    def new_game(self, event):
        # from views.game_view import GameView
        self.window.show_view(BaseLevel.camp_view)

    def open_settings(self, event):
        # from views.settings_view import SettingsView
        self.window.show_view(SettingsView())

    def on_draw(self):
        self.clear()
        self.zombies.draw()
        self.ui.draw()

    def on_hide_view(self):
        self.ui.disable()


class BaseLevel(arcade.View):
    ALLOWED_KEYBOARD_KEYS = (arcade.key.W, arcade.key.A, arcade.key.S, arcade.key.D, arcade.key.R, arcade.key.E)
    levels = []
    current_level = 0
    camp_view = None

    def __init__(self, tilemap_path):
        super().__init__(background_color=(0, 0, 0))
        self.tilemap = tilemap_path
        self.player = None
        self.walls = None
        self.background = None
        self.ladders = None
        self.physics_engine = None
        self.keyboard_pressed = set()
        self.mouse_pressed = [None, None, None, None]
        self.scene = None
        self.hp_HUD = HUD("assets/HUD/hp_icon.png", 2, 20, 60, 100, (255, 20, 20),
                          (0, 0, 0))
        self.stamina_HUD = HUD("assets/HUD/energy_icon.png", 1, 20, 20, 100, (255, 255, 255),
                               (0, 0, 0))
        self.exits = None

    def on_show_view(self):
        self.tilemap = arcade.load_tilemap(self.tilemap, layer_options = {
            "walls": {
            "use_spatial_hash": True
            },
            "ladders": {
            "use_spatial_hash": True
            }
        })
        self.scene = arcade.Scene.from_tilemap(self.tilemap)
        self.player = Player("assets/Player/idle/default_idle_no_hands.png", 2,
                                       *self.tilemap.sprite_lists["player_spawn"][0].position,
                                       "assets/Player/player_hand.png")
        self.gui_camera = arcade.Camera2D()
        self.game_camera = arcade.Camera2D()
        # self.items = arcade.SpriteList()
        self.exits = self.tilemap.sprite_lists["exits"]
        self.walls = self.tilemap.sprite_lists["walls"]
        self.ladders = self.tilemap.sprite_lists["ladders"]
        self.background = self.tilemap.sprite_lists["background"]
        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player, gravity_constant=GRAVITY_CONSTANT,
                                                             walls=self.walls, ladders=self.ladders)
        self.player.physics_engine = self.physics_engine
        self.player.append_to_inventory(Weapon(*self.player.hands.position, self.player.hands.angle + 90, *PISTOL_SETUP,
                                               self.walls, arcade.SpriteList()))
        self.player.change_curr_item(0)
        # self.player.item_list = self.items
        self.player.exit = self.exits[0]


    def on_draw(self):
        self.game_camera.use()
        self.clear()
        self.background.draw()
        self.exits.draw()
        self.walls.draw()
        self.ladders.draw()
        self.player.draw_list.draw()
        for el in self.player.particle_systems:
            el.draw()
        self.gui_camera.use()
        self.stamina_HUD.show(max(self.player.energy, 0))
        self.hp_HUD.show(self.player.hp)

    def on_update(self, delta_time):
        self.player.update(self.keyboard_pressed, self.mouse_pressed, delta_time)
        self.game_camera.position = self.player.position
        if arcade.check_for_collision(self.player, self.exits[0]):
            BaseLevel.current_level += 1
            self.window.show_view(BaseLevel.camp_view)


    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        if symbol in BaseLevel.ALLOWED_KEYBOARD_KEYS:
            self.keyboard_pressed.add(symbol)
        elif symbol == arcade.key.LSHIFT or symbol == arcade.key.RSHIFT:
            self.player.shift_pressed = True

    def on_key_release(self, symbol: int, modifiers: int) -> bool | None:
        self.keyboard_pressed.discard(symbol)
        if symbol == arcade.key.LSHIFT or symbol == arcade.key.RSHIFT:
            self.player.shift_pressed = False

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        if self.player.is_in_aiming:
            self.mouse_pressed[1] = [x, y]

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.player.is_in_aiming = not self.player.is_in_aiming
        elif button == arcade.MOUSE_BUTTON_LEFT:
            self.player.shoot()


    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.mouse_pressed[1] = None



class CampView(BaseLevel):
    def __init__(self, tilemap_path):
        super().__init__(tilemap_path)
        self.next_level_button = arcade.gui.UIFlatButton(x=SCREEN_WIDTH - 100, y=SCREEN_HEIGHT - 100, width=100,
                                                         height=100, text="Next level")
        self.next_level_button.on_click = self.temp

    def on_show_view(self):
        super().on_show_view()
        self.window.gui_manager.enable()
        self.window.gui_manager.add(self.next_level_button)

    def temp(self, event):
        self.window.show_view(BaseLevel.levels[BaseLevel.current_level])
        self.window.gui_manager.clear()
        self.window.gui_manager.disable()


    def on_draw(self):
        super().on_draw()
        self.next_level_button.visible = True
        self.window.gui_manager.draw()



if __name__ == "__main__":
    init_db()
    window = MainWindow(SCREEN_WIDTH, SCREEN_HEIGHT, "Deadly Bite", resizable=True, fullscreen=False)
    BaseLevel.levels.append(BaseLevel("null_level.json"))
    BaseLevel.current_level = 0
    BaseLevel.camp_view = CampView("null_level.json")
    window.show_view(MenuView())
    arcade.run()
