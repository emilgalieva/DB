import arcade
from pyglet.graphics import Batch


class NewGameView(arcade.View):
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


class LoadGameView(arcade.View):
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


class SettingsView(arcade.View):
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
        self.game_view = GameView(self)
        self.new_game_view = NewGameView(self)
        self.load_game_view = LoadGameView(self)
        self.settings_view = SettingsView(self)
        self.endings_view = EndingsView(self)
        self.cell_size = (self.window.height - 200) // 4
        self.menu_batch = Batch()
        self.buttons_content = ("New Game", "Load Game", "Settings", "Endings")
        self.menu_funcs = (self.new_game, self.load_game, self.settings, self.endings)
        self.menu_buttons = [arcade.LBWH(100, self.window.height - 100 - self.cell_size * (i + 1),
                                         400, self.cell_size * 3 // 4) for i in range(4)]
        self.menu_text = [arcade.Text(el, 150, self.window.height - 100 - self.cell_size * (i + 1)
                                      + self.cell_size // 2,
                                      anchor_x="left", anchor_y="bottom", batch=self.menu_batch)
                          for i, el in enumerate(self.buttons_content)]

    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        self.menu_batch.draw()
        for i in range(len(self.menu_buttons)):
            arcade.draw_rect_outline(self.menu_buttons[i], arcade.color.WHITE)

    def on_mouse_press(self, x, y, button, modifiers):
        for i, el in enumerate(self.menu_buttons):
            if el.left + el.width >= x >= el.left and el.bottom + el.height >= y >= el.bottom:
                self.menu_funcs[i]()

    def new_game(self):
        self.window.show_view(self.new_game_view)

    def load_game(self):
        self.window.show_view(self.load_game_view)

    def settings(self):
        self.window.show_view(self.settings_view)

    def endings(self):
        self.window.show_view(self.endings_view)


class GameView(arcade.View):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent


if __name__ == "__main__":
    window = arcade.Window(1280, 720, "Deadly Bite")
    start_view = StartView()
    window.show_view(start_view)
    arcade.run()