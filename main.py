from settings import *
import arcade.gui
from engine.database import save_volume, load_volume, init_db, save_player, load_player
import random
from engine.Item import *
from engine.Player import *
from engine.BaseLevel import *
from engine.CampView import *


class MainWindow(arcade.Window):
    def __init__(self, width, height, title, fullscreen, resizable):
        super().__init__(width, height, title, fullscreen, resizable)

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            self.close()


class SettingsView(arcade.View):
    def __init__(self):
        super().__init__()
        self.gui_manager = arcade.gui.UIManager()
        self.volume = load_volume()

    def on_show_view(self):
        arcade.set_background_color(arcade.color.GRAY)
        self.gui_manager.enable()
        self.gui_manager.clear()

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
        self.gui_manager.add(anchor)

    def change_volume(self, event):
        self.volume = event.new_value
        # arcade.sound.set_volume(self.volume)
        save_volume(self.volume)

    def back(self, event):
        # from views.menu_view import MenuView
        self.window.show_view(MenuView())

    def on_draw(self):
        self.clear()
        self.gui_manager.draw()

    def on_hide_view(self):
        self.gui_manager.disable()


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.gui_manager = arcade.gui.UIManager()
        self.zombies = arcade.SpriteList()

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.gui_manager.enable()
        self.gui_manager.clear()

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
        self.gui_manager.add(anchor)

    def on_update(self, delta_time):
        self.zombies.update()
        for zombie in self.zombies:
            if zombie.right < 0:
                zombie.left = self.window.width

    def new_game(self, event):
        # from views.game_view import GameView
        self.window.show_view(BaseLevel.camp_level)

    def open_settings(self, event):
        # from views.settings_view import SettingsView
        self.window.show_view(SettingsView())

    def on_draw(self):
        self.clear()
        self.zombies.draw()
        self.gui_manager.draw()

    def on_hide_view(self):
        self.gui_manager.disable()

class FinishScreen(arcade.View):
    pass

def init_game(levels, camp_level):
    BaseLevel.levels = levels
    BaseLevel.camp_level = camp_level
    BaseLevel.current_level = 0
    BaseLevel.player = Player(PLAYER_TEXTURE_NO_HANDS, 2,
                              0, 0, PLAYER_HAND_TEXTURE)
    # load_player(BaseLevel.player)

if __name__ == "__main__":
    init_db()
    window = MainWindow(SCREEN_WIDTH, SCREEN_HEIGHT,
                        "Deadly Bite", resizable=False, fullscreen=True)
    init_game([BaseLevel(NULL_LEVEL), BaseLevel(
        NULL_LEVEL)], CampView(NULL_LEVEL))
    window.show_view(MenuView())
    arcade.run()
