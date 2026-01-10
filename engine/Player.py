from settings import (PLAYER_MAX_HP, PLAYER_JUMP_SPEED, PLAYER_WALK_SPEED, PLAYER_CLIMB_SPEED,
                      PLAYER_JUMP_TIMEOUT, PLAYER_MAX_ENERGY, PLAYER_SPRINT_COST, PLAYER_ENERGY_RECOVERY_SPEED,
                      PLAYER_JUMP_BUFFER, PLAYER_JUMP_COYOTE_TIME, X_SPEED_FALL, PLAYER_JUMP_COST, JUMP_X_BOOST_K,
                      PLAYER_SPRINT_K, SCREEN_HEIGHT, SCREEN_WIDTH)
import arcade
from engine.Weapon import Weapon
from math import asin, degrees, acos, cos, sin, radians
class Player(arcade.Sprite):
    def __init__(self, path_or_texture, scale, center_x, center_y, hands_texture):
        super().__init__(path_or_texture, scale, center_x, center_y, 0)
        self._hp = PLAYER_MAX_HP
        self.walk_speed = PLAYER_WALK_SPEED
        self.jump_speed = PLAYER_JUMP_SPEED
        self.climb_speed = PLAYER_CLIMB_SPEED
        self.buffer_jump_timer = None
        self.coyote_jump_timer = None
        self.can_jump = False
        self.shot = None
        self.jump_timer = PLAYER_JUMP_TIMEOUT
        self.is_on_ladder = False
        self.is_in_aiming = False
        self.shift_pressed = False
        self.right_look = True
        self.jumps = 0
        self._energy = PLAYER_MAX_ENERGY
        self.is_in_sprint = False
        self.physics_engine = None
        self.hands = arcade.Sprite(hands_texture, scale, center_x - 4.5 * scale, center_y + 14.5 * scale, 0)
        self.inventory = []
        self.curr_item = None
        self.equipped_item = None
        self.particle_systems = []
        self.draw_list = arcade.SpriteList()
        self.draw_list.append(self)
        self.draw_list.append(self.hands)

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, hp):
        self._hp = min(hp, PLAYER_MAX_HP)

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, hp):
        self._energy = min(hp, PLAYER_MAX_ENERGY)

    def update(self, keyboard, mouse, delta_time):
        if self.jump_timer < PLAYER_JUMP_TIMEOUT:
            self.jump_timer += delta_time
        if self.is_in_sprint:
            self._energy -= PLAYER_SPRINT_COST * delta_time
        elif self._energy < PLAYER_MAX_ENERGY:
            self._energy = min((PLAYER_MAX_ENERGY, self._energy
                                              + PLAYER_ENERGY_RECOVERY_SPEED * delta_time))
        self.is_in_sprint = False
        is_on_ladder = self.physics_engine.is_on_ladder()
        can_jump = self.physics_engine.can_jump(1)
        if self.buffer_jump_timer is not None:
            self.buffer_jump_timer += delta_time
            if self.buffer_jump_timer > PLAYER_JUMP_BUFFER:
                self.buffer_jump_timer = None
        if can_jump or is_on_ladder:
            self.jumps = 0
            self.change_y = 0
            self.change_x = 0
            if self.coyote_jump_timer is None:
                self.coyote_jump_timer = 0
            elif self.coyote_jump_timer <= PLAYER_JUMP_COYOTE_TIME:
                self.coyote_jump_timer += delta_time
                if self.coyote_jump_timer > PLAYER_JUMP_COYOTE_TIME:
                    self.coyote_jump_timer = None
            if arcade.key.A in keyboard:
                self.change_x -= self.walk_speed
            if arcade.key.D in keyboard:
                self.change_x += self.walk_speed
            if (self.shift_pressed and self.change_x != 0
                    and self._energy >= PLAYER_SPRINT_COST * delta_time):
                self.change_x *= 2
                self.is_in_sprint = True
        elif self.change_x > 0:
            self.change_x = max(self.change_x - X_SPEED_FALL * delta_time, 0)
        elif self.change_x < 0:
            self.change_x = min(self.change_x + X_SPEED_FALL * delta_time, 0)
        if (arcade.key.W in keyboard) or self.buffer_jump_timer is not None:
            if is_on_ladder:
                self.change_y += self.climb_speed
            elif self._energy >= PLAYER_JUMP_COST:
                if can_jump or (self.coyote_jump_timer is not None and self.jumps == 0):
                    self.jump_timer = 0
                    self.change_x *= JUMP_X_BOOST_K
                    self.jumps = 1
                    self.physics_engine.jump(self.jump_speed)
                    self._energy -= PLAYER_JUMP_COST
                elif self.jump_timer > PLAYER_JUMP_TIMEOUT:
                    self.buffer_jump_timer = 0
        if arcade.key.S in keyboard and is_on_ladder:
            self.change_y -= self.climb_speed
        if (self.shift_pressed and self.change_y != 0
                and is_on_ladder and self._energy >= PLAYER_SPRINT_COST * delta_time):
            self.change_y *= PLAYER_SPRINT_K
            self.is_in_sprint = True
        self.change_x *= delta_time
        if is_on_ladder:
            self.change_y *= delta_time
        self.physics_engine.update()
        self.change_x /= delta_time
        if is_on_ladder:
            self.change_y = 0
        if (self.change_x > 0 and not self.right_look) or (self.change_x < 0 and self.right_look):
            self.texture = self.texture.flip_horizontally()
            self.hands.texture = self.hands.texture.flip_horizontally()
            if self.curr_item is not None:
                self.inventory[self.curr_item].texture = self.inventory[self.curr_item].texture.flip_horizontally()
            self.right_look = self.change_x > 0
        self.hands.center_x = self.center_x - 4.5 * self.scale[0] * (1 if self.right_look else -1)
        self.hands.center_y = self.center_y + 14.5 * self.scale[1]
        if mouse[1] is not None:
            self.hands.angle = 0
            gipoten = ((mouse[1][1] - SCREEN_HEIGHT // 2 - self.hands.center_y + self.center_y) ** 2
                       + (mouse[1][0] - SCREEN_WIDTH // 2 - self.hands.center_x + self.center_x) ** 2) ** 0.5
            if gipoten != 0:
                self.hands.angle = ((-90 - degrees(asin((mouse[1][1] - SCREEN_HEIGHT // 2 - self.hands.center_y
                                                         + self.center_y) / gipoten)))) * (1 if self.right_look else -1)
        for el in self.particle_systems:
            el.update(delta_time)
            if el.can_reap():
                self.particle_systems.remove(el)
        if self.curr_item is not None:
            if isinstance(self.inventory[self.curr_item], Weapon):
                if self.inventory[self.curr_item].smoke is not None:
                    self.particle_systems.append(self.inventory[self.curr_item].smoke)
                    self.inventory[self.curr_item].smoke = None
                if (arcade.key.R in keyboard) and self.inventory[self.curr_item].is_available:
                    self.inventory[self.curr_item].recharge()
            self.inventory[self.curr_item].update(delta_time)
            self.inventory[self.curr_item].set_angle(self.hands.angle + 90 * (1 if self.right_look else -1),
                                                    self.right_look)
            self.inventory[self.curr_item].center_x = (self.hands.center_x
                                                + (self.hands.height / 2 + self.inventory[self.curr_item].width / 7)
                                                    * cos(radians(self.inventory[self.curr_item].angle))
                                                    * (1 if self.right_look else -1))
            self.inventory[self.curr_item].center_y = (self.hands.center_y
                                                + (self.hands.height / 2 + self.inventory[self.curr_item].width / 3)
                                                    * sin(radians(-self.inventory[self.curr_item].angle))
                                                    * (1 if self.right_look else -1))


    def change_curr_item(self, new_value):
        if self.curr_item is not None:
            self.draw_list.remove(self.inventory[self.curr_item])
            if isinstance(self.inventory[self.curr_item], Weapon):
                self.draw_list.remove(self.inventory[self.curr_item].bullet)
        self.draw_list.append(self.inventory[new_value])
        self.curr_item = new_value

    def append_to_inventory(self, item):
        self.inventory.append(item)
        if isinstance(item, Weapon):
            self.draw_list.append(item.bullet)

    def shoot(self):
        if self.curr_item is not None and isinstance(self.inventory[self.curr_item], Weapon):
            self.inventory[self.curr_item].shoot(self.right_look)