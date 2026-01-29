from io import TextIOWrapper

import arcade.gui
from engine.database import save_volume, load_volume, init_db, save_player, load_in_player
from engine.Player import *
from engine.CampView import *
from engine.BaseLevel import *


class MainWindow(arcade.Window):
    def __init__(self, width, height, title, fullscreen, resizable):
        super().__init__(width, height, title, fullscreen, resizable)

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            self.close()


class GameOverView(arcade.View):
    def __init__(self):
        super().__init__()
        self.gui_manager = arcade.gui.UIManager()
        self.restart_button = None
        self.menu_button = None
        self.title_label = None

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.gui_manager.enable()
        self.gui_manager.clear()

        self.title_label = arcade.gui.UILabel(
            text="GAME OVER",
            font_size=72,
            text_color=arcade.color.RED,
            bold=True
        )
        self.menu_button = arcade.gui.UIFlatButton(
            text="В главное меню",
            width=300,
            height=50
        )
        self.menu_button.on_click = self.return_to_menu
        v_box = arcade.gui.UIBoxLayout(space_between=20)
        v_box.add(self.title_label)
        v_box.add(self.menu_button)
        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(v_box, anchor_x="center_x", anchor_y="center_y")
        self.gui_manager.add(anchor)

    def on_draw(self):
        self.clear()
        overlay_color = (0, 0, 0, 200)
        points = [
            (0, 0),
            (self.window.width, 0),
            (self.window.width, self.window.height),
            (0, self.window.height)
        ]
        arcade.draw_polygon_filled(points, overlay_color)

        self.gui_manager.draw()

    def return_to_menu(self, event):
        self.window.show_view(Game.menu_view)

    def on_hide_view(self):
        self.gui_manager.disable()


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
        Game.volume = event.new_value

    def back(self, event):
        self.window.show_view(Game.menu_view)

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

        self.zombies = arcade.SpriteList()
        for _ in range(6):
            zombie = arcade.Sprite("assets/TileMaps/Zombie.png", scale=3)
            zombie.center_x = random.randint(0, self.window.width)
            zombie.center_y = random.randint(0, self.window.height)
            zombie.change_x = random.uniform(-0.5, 0.5)
            self.zombies.append(zombie)

        title = arcade.gui.UILabel(
            text="Deadly Bite",
            font_size=42
        )

        new_game_btn = arcade.gui.UIFlatButton(text="Новая игра", width=250)
        load_game_btn = arcade.gui.UIFlatButton(
            text="Загрузить последнее сохранение", width=250)
        settings_btn = arcade.gui.UIFlatButton(text="Настройки", width=250)

        new_game_btn.on_click = self.new_game
        settings_btn.on_click = self.open_settings
        load_game_btn.on_click = self.load_game

        box = arcade.gui.UIBoxLayout(space_between=20)
        box.add(title)
        box.add(new_game_btn)
        box.add(load_game_btn)
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
        Game.current_level = 0
        Game.game_on_pause = False
        Game.player = Player(PLAYER_TEXTURE_NO_HANDS, 2,
                             0, 0, PLAYER_HAND_TEXTURE, PLAYER_WALKING_TEXTURE)
        self.window.show_view(Game.camp_level)

    def load_game(self, event):
        try:
            Game.player = Player(PLAYER_TEXTURE_NO_HANDS, 2,
                                 0, 0, PLAYER_HAND_TEXTURE, PLAYER_WALKING_TEXTURE)
            load_in_player(Game.player)
        except Exception:
            self.new_game(None)
        self.window.show_view(Game.camp_level)

    def open_settings(self, event):
        self.window.show_view(Game.settings_view)

    def on_draw(self):
        self.clear()
        self.zombies.draw()
        self.gui_manager.draw()

    def on_hide_view(self):
        self.gui_manager.disable()


class FinishScreen(arcade.View):
    def __init__(self):
        super().__init__(background_color=arcade.color.BLACK)

    def on_show_view(self):
        self.gui_manager = arcade.gui.UIManager()
        self.gui_manager.enable()
        self.strikes_done_label = arcade.gui.UILabel(
            "", x=self.window.width // 2, y=50, font_size=24)
        self.zombies_killed_label = arcade.gui.UILabel(
            "", x=self.window.width // 2, y=150, font_size=24)
        self.total_amount_of_money_label = arcade.gui.UILabel("", x=self.window.width // 2, y=250, font_size=24,
                                                              text_color=arcade.color.YELLOW)
        self.gui_manager.add(self.strikes_done_label)
        self.gui_manager.add(self.zombies_killed_label)
        self.gui_manager.add(self.total_amount_of_money_label)

        self.strikes_done_label.text = str(Game.strikes_done)
        self.zombies_killed_label.text = str(Game.zombies_killed)
        money = Game.player.money
        for el in Game.player.inventory:
            money += ITEM_PRICES[el.item_id]

    def on_draw(self):
        self.clear()
        self.gui_manager.draw()



    def on_hide_view(self):
        self.gui_manager.disable()


def init_game(level_args, camp_level_args):
    Game.current_level = 0
    Game.player = Player(PLAYER_TEXTURE_NO_HANDS, 2,
                         0, 0, PLAYER_HAND_TEXTURE, PLAYER_WALKING_TEXTURE)
    Game.levels = tuple(BaseLevel(*el) for el in level_args)
    Game.camp_level = CampView(*camp_level_args)
    Game.game_over_view = GameOverView()
    Game.menu_view = MenuView()
    Game.settings_view = SettingsView()
    Game.finish_screen = FinishScreen()
    # load_player(Game.player)


if __name__ == "__main__":
    init_db()
    window = MainWindow(SCREEN_WIDTH, SCREEN_HEIGHT,
                        "Deadly Bite", resizable=False, fullscreen=True)
    init_game([(NULL_LEVEL, 255), (
        FIRST_LEVEL, 255), (SECOND_LEVEL, 100)], (CAMP_LEVEL, 200))
    window.show_view(Game.menu_view)
    arcade.run()
