import arcade
import arcade.gui
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from engine.BaseLevel import BaseLevel
class CampView(BaseLevel):
    def __init__(self, tilemap_path):
        super().__init__(tilemap_path)
        self.next_level_button = arcade.gui.UIFlatButton(x=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT // 2, width=100,
                                                         height=100, text="Next level")
        self.next_level_button.on_click = self.temp
        self.gui_manager = arcade.gui.UIManager()
        self.gui_manager.add(self.next_level_button)

    def on_show_view(self):
        super().on_show_view()
        self.gui_manager.enable()
        BaseLevel.player.in_camp = True

    def on_hide_view(self) -> None:
        self.gui_manager.disable()
        BaseLevel.player.in_camp = False

    def temp(self, event):
        self.window.show_view(BaseLevel.levels[BaseLevel.current_level])
        BaseLevel.player.in_camp = False
        self.gui_manager.clear()
        self.gui_manager.disable()

    def on_draw(self):
        super().on_draw()
        self.next_level_button.visible = True
        self.gui_manager.draw()