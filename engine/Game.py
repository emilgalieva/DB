import arcade

from settings import BRIGHT_CONTROL_TEXTURE, SCREEN_WIDTH, SCREEN_HEIGHT


class Game:
    levels = []
    current_level = 0
    camp_level = None
    player = None
    game_on_pause = False
    zombies_killed = 0
    strikes_done = 0
    bright_control_sprite_list = arcade.SpriteList()
    bright_control_sprite_list.append(arcade.Sprite(BRIGHT_CONTROL_TEXTURE, (SCREEN_WIDTH, SCREEN_HEIGHT),
                                                    0, 0))
    settings_view = None
    menu_view = None
    game_over_view = None
    volume = 1.0
