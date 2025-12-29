from settings import (PLAYER_HP, PLAYER_JUMP_SPEED, PLAYER_WALK_SPEED, PLAYER_CLIMB_SPEED,
                      PLAYER_SPRINT_K, X_SPEED_FALL, PLAYER_JUMP_COYOTE_TIME)
import arcade
class Player(arcade.Sprite):
    def __init__(self, path_or_texture, scale, center_x, center_y):
        super().__init__(path_or_texture, scale, center_x, center_y, 0)
        self.hp = PLAYER_HP
        self.walk_speed = PLAYER_WALK_SPEED
        self.jump_speed = PLAYER_JUMP_SPEED
        self.climb_speed = PLAYER_CLIMB_SPEED
        self.buffer_jump_timer = None
        self.coyote_jump_timer = None
        self.can_jump = False
        self.on_ladder = False
        self.is_in_aiming = False
        self.shift_pressed = False
        self.inventory = []
        self.right_look = True
        self.jumps = 0


    def change_direction(self):
        if (self.change_x > 0 and not self.right_look) or (self.change_x < 0 and self.right_look):
            self.texture = self.texture.flip_horizontally()
            self.right_look = self.change_x > 0
