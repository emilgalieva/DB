import arcade
from pyglet.graphics import Batch

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
class Player(arcade.Sprite):
    def __init__(self, path_or_texture, scale, center_x, center_y):
        super().__init__(path_or_texture, scale, center_x, center_y, 0)


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
    CELL_SIZE = 100
    UP_SPACE = 100

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.settings_batch = Batch()
        lever_funcs = (self.change_volume, self.change_brightness, self.change_hud_size)
        lever_text = ("Brightness", "Volume", "HUD size")
        lever_textures = ("lever_settings.png", "lever_settings.png", "lever_settings.png")
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
        self.button_list.append(Button("button_back_to_menu.png", 1, 300, SCREEN_HEIGHT -
                                              SettingsView.UP_SPACE - len(lever_funcs) * SettingsView.CELL_SIZE,0,
                                       self.to_main_menu))

    def on_show(self):
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
        self.game_view = GameView(self)
        self.new_game_view = NewGameView(self)
        self.load_game_view = LoadGameView(self)
        self.settings_view = SettingsView(self)
        self.endings_view = EndingsView(self)
        self.cell_size = (self.window.height - 150) // 4
        self.menu_batch = Batch()
        self.menu_elements = arcade.SpriteList()
        menu_textures = ("button_new_game.png", "button_load_game.png", "button_settings.png", "button_endings.png")
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


class GameView(arcade.View):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent


if __name__ == "__main__":
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Deadly Bite")
    start_view = StartView()
    window.show_view(start_view)
    arcade.run()
