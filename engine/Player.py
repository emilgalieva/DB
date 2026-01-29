import arcade
from arcade.hitbox import HitBoxAlgorithm

from engine.Item import Effect
from settings import (PLAYER_MAX_HP, PLAYER_JUMP_SPEED, PLAYER_WALK_SPEED, PLAYER_CLIMB_SPEED,
                      PLAYER_JUMP_TIMEOUT, PLAYER_MAX_ENERGY, PLAYER_SPRINT_COST, PLAYER_ENERGY_RECOVERY_SPEED,
                      PLAYER_JUMP_BUFFER, PLAYER_JUMP_COYOTE_TIME, X_SPEED_FALL, PLAYER_JUMP_COST, JUMP_X_BOOST_K,
                      PLAYER_SPRINT_K, SCREEN_HEIGHT, SCREEN_WIDTH, PLAYER_INVENTORY_SIZE)
from settings import *
from engine.AdvancedResources import *
from engine.Weapon import Weapon
from engine.Inventory import Inventory
from engine.Game import *
from engine.BaseLevel import *
from math import asin, degrees, cos, sin, radians


class Player(arcade.Sprite):
    def __init__(self, path_or_texture: str, scale, center_x, center_y, hands_texture,
                 walk_texture: str):
        super().__init__(arcade.load_texture(path_or_texture,
                                             hit_box_algorithm=arcade.hitbox.algo_detailed), scale, center_x, center_y, 0)
        self._hp = PLAYER_MAX_HP
        self.walk_speed = PLAYER_WALK_SPEED
        self.jump_speed = PLAYER_JUMP_SPEED
        self.climb_speed = PLAYER_CLIMB_SPEED
        self.inventory_size = PLAYER_INVENTORY_SIZE
        self.buffer_jump_timer = None
        self.coyote_jump_timer = None
        self.can_jump = False
        self.jump_timer = PLAYER_JUMP_TIMEOUT
        self.is_on_ladder = False
        self.is_in_aiming = False
        self._sprint_cost = PLAYER_SPRINT_COST
        self.jump_cost = PLAYER_JUMP_COST
        self.right_look = True
        self.jumps = 0
        self._energy = PLAYER_MAX_ENERGY
        self._energy_recovery_speed = PLAYER_ENERGY_RECOVERY_SPEED
        self.is_in_sprint = False
        self.physics_engine = None
        self.hands = arcade.Sprite(
            hands_texture, scale, center_x - 4.5 * scale, center_y + 14.5 * scale, 0)
        self.hands_held_angle = 0
        self.inventory = Inventory(PLAYER_INVENTORY_SIZE, 1000, INVENTORY_SLOT_SIZE, 5,
                                   arcade.load_texture(INVENTORY_SLOT_TEXTURE),
                                   [(el[0], arcade.load_texture(el[1]), el[2], el[3])
                                    for el in INVENTORY_EQUIPMENT_SLOTS],
                                   arcade.load_texture(
                                       INVENTORY_SLOT_FORBIDDEN_TEXTURE),
                                   arcade.load_texture(
                                       INVENTORY_SLOT_ON_CHOICE_TEXTURE),
                                   arcade.load_texture(INVENTORY_SLOT_FOR_DROPPING_TEXTURE), self)
        self.money = 0
        self._curr_item_index = 0
        self.curr_item_index = 0
        self.particle_systems = []
        self.effects = []
        self.level_items = None
        self.in_camp = False
        self.can_press_q = True
        self.can_press_rmb = True
        self.can_press_mmb = True
        self.can_press_m = True
        self.resistance = 0
        self.temp_draw_list = arcade.SpriteList()
        self.draw_list = CharacterDrawList()
        self.draw_list.append(self)
        self.draw_list.append(self.hands)
        # animations
        self.walk_textures = [self.texture, arcade.load_texture(
            walk_texture, hit_box_algorithm=arcade.hitbox.algo_detailed)]
        self.walked_distance = 0
        self.distance_per_step = self.walk_textures[1].width
        self.curr_texture_index = 0
        self.is_alive = True
        self.death_timer = 0

    @property
    def energy_recovery_speed(self):
        return self._energy_recovery_speed

    @energy_recovery_speed.setter
    def energy_recovery_speed(self, value: ValueWithSender):
        self._energy_recovery_speed = value.v

    @property
    def curr_item_index(self):
        return self._curr_item_index

    @curr_item_index.setter
    def curr_item_index(self, curr_item_index: int):
        scroll_direction_forward = curr_item_index > self._curr_item_index
        curr_item_index = int(curr_item_index) % len(self.inventory)
        if curr_item_index < self.inventory.equipped_size:
            curr_item_index += (self.inventory.equipped_size if scroll_direction_forward
                                else -self.inventory.equipped_size)
        if self.inventory[self._curr_item_index] is not None:
            self.draw_list.remove(self.inventory[self._curr_item_index])
        self._curr_item_index = curr_item_index % len(self.inventory)

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, hp: ValueWithSender):
        if not isinstance(hp.s, Effect) and hp.v < self._hp:
            hp.v += (self._hp - hp.v) * self.resistance
        self._hp = PLAYER_MAX_HP if hp.v > PLAYER_MAX_HP else 0 if hp.v < 0 else hp.v
        if self._hp <= 0:
            self.die()

    @property
    def sprint_cost(self):
        return self._sprint_cost

    @sprint_cost.setter
    def sprint_cost(self, value: ValueWithSender):
        self._sprint_cost = value.v

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, energy: ValueWithSender):
        if isinstance(energy.v, int) or isinstance(energy.v, float):
            self._energy = PLAYER_MAX_ENERGY if energy.v > PLAYER_MAX_ENERGY else 0 if energy.v < 0 else energy.v

    @property
    def brightness(self):
        return Game.bright_control_sprite_list[0].alpha

    @brightness.setter
    def brightness(self, value: ValueWithSender):
        Game.bright_control_sprite_list[0].alpha = 255 / value.v

    def die(self):
        if not self.is_alive:
            return
        self.is_alive = False
        self.death_timer = 0
        self.change_x = 0
        self.change_y = 0
        self.alpha = 200
        arcade.schedule_once(
            lambda x: Game.camp_level.window.show_view(Game.game_over_view), 1.0)

    def update_animation(self, delta_time):
        self.walked_distance += self.change_x * delta_time
        if self.change_x != 0:
            self.curr_texture_index = ((self.curr_texture_index + round(self.walked_distance // self.distance_per_step))
                                       % len(self.walk_textures))
            self.walked_distance = self.walked_distance % self.distance_per_step
            self.texture = self.walk_textures[self.curr_texture_index]
        else:
            self.texture = self.walk_textures[0]
            self.walked_distance = 0

    def update(self, keyboard, mouse, delta_time):
        self.temp_draw_list.clear()
        if not self.is_alive:
            self.death_timer += delta_time
            self.alpha = max(0, 200 - self.death_timer * 100)
            return
        if self.jump_timer < PLAYER_JUMP_TIMEOUT:
            self.jump_timer += delta_time
        if self.is_in_sprint:
            self._energy -= self.sprint_cost * delta_time
        elif self._energy < PLAYER_MAX_ENERGY:
            self._energy = min((PLAYER_MAX_ENERGY, self._energy
                                + self.energy_recovery_speed * delta_time))
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
            if keyboard["A"]:
                self.change_x -= self.walk_speed
            if keyboard["D"]:
                self.change_x += self.walk_speed
            if ((keyboard["LSHIFT"] or keyboard["RSHIFT"]) and self.change_x != 0
                    and self._energy >= self.sprint_cost * delta_time):
                self.change_x *= 2
                self.is_in_sprint = True
        elif self.change_x > 0:
            self.change_x = max(self.change_x - X_SPEED_FALL * delta_time, 0)
        elif self.change_x < 0:
            self.change_x = min(self.change_x + X_SPEED_FALL * delta_time, 0)
        if keyboard["W"] or self.buffer_jump_timer is not None:
            if is_on_ladder:
                self.change_y += self.climb_speed
            elif self._energy >= self.jump_cost:
                if can_jump or (self.coyote_jump_timer is not None and self.jumps == 0):
                    self.jump_timer = 0
                    self.change_x *= JUMP_X_BOOST_K
                    self.jumps = 1
                    self.physics_engine.jump(self.jump_speed)
                    self._energy -= self.jump_cost
                elif self.jump_timer > PLAYER_JUMP_TIMEOUT:
                    self.buffer_jump_timer = 0
        if keyboard["S"] and is_on_ladder:
            self.change_y -= self.climb_speed
        if ((keyboard["LSHIFT"] or keyboard["RSHIFT"]) and self.change_y != 0
                and is_on_ladder and self._energy >= PLAYER_SPRINT_COST * delta_time):
            self.change_y *= PLAYER_SPRINT_K
            self.is_in_sprint = True
        self.update_animation(delta_time)
        self.change_x *= delta_time
        if is_on_ladder:
            self.change_y *= delta_time
        self.physics_engine.update()
        self.change_x /= delta_time
        if is_on_ladder:
            self.change_y = 0
        if (self.change_x > 0 and not self.right_look) or (self.change_x < 0 and self.right_look):
            self.walked_distance = 0
            self.curr_texture_index = 0
            self.walk_textures = [el.flip_horizontally()
                                  for el in self.walk_textures]
            self.hands.texture = self.hands.texture.flip_horizontally()
            old_right_look = self.right_look
            self.right_look = self.change_x > 0
            self.hands_held_angle += (180 + -2 * (self.hands_held_angle + 90 if old_right_look
                                                  else -(self.hands_held_angle + 90))) * (1 if old_right_look else -1)
            for i in range(self.inventory.equipped_size):
                if self.inventory[i] is not None:
                    if self.inventory[i].right_look != self.right_look:
                        self.inventory[i].texture = self.inventory[i].texture.flip_horizontally(
                        )
                        self.inventory[i].right_look = self.right_look
        self.hands.center_x = self.center_x - 4.5 * \
            self.scale[0] * (1 if self.right_look else -1)
        self.hands.center_y = self.center_y + 14.5 * self.scale[1]
        if self.is_in_aiming:
            self.hands.angle = 0
            gipoten = ((mouse["POS"][1] - SCREEN_HEIGHT // 2 - self.hands.center_y + self.center_y) ** 2
                       + (mouse["POS"][0] - SCREEN_WIDTH // 2 - self.hands.center_x + self.center_x) ** 2) ** 0.5
            if gipoten != 0:
                self.hands.angle = ((-90 - degrees(asin((mouse["POS"][1] - SCREEN_HEIGHT // 2 - self.hands.center_y
                                                         + self.center_y) / gipoten)))) * (1 if self.right_look else -1)
                self.hands_held_angle = self.hands.angle
        else:
            self.hands.angle = self.hands_held_angle
        if mouse["RIGHT"]:
            if self.can_press_rmb:
                self.is_in_aiming = not self.is_in_aiming
                self.can_press_rmb = False
        else:
            self.can_press_rmb = True
        self.check_shoot(mouse["LEFT"])
        # particle systems update
        for el in self.particle_systems:
            el.update(delta_time)
            if el.can_reap():
                self.particle_systems.remove(el)
        if self.inventory[self.curr_item_index] is not None:
            if self.inventory[self.curr_item_index] not in self.draw_list:
                self.draw_list.insert(1, self.inventory[self.curr_item_index])
            if isinstance(self.inventory[self.curr_item_index], Weapon):
                if self.inventory[self.curr_item_index].modification is not None:
                    self.temp_draw_list.append(
                        self.inventory[self.curr_item_index].modification)
                if self.inventory[self.curr_item_index].smoke is not None:
                    self.particle_systems.append(
                        self.inventory[self.curr_item_index].smoke)
                    self.inventory[self.curr_item_index].smoke = None
                if mouse["MIDDLE"]:
                    if self.can_press_mmb:
                        self.inventory[self.curr_item_index].change_shooting_mode()
                        (Game.levels[Game.current_level] if not self.in_camp
                         else Game.camp_level).show_temp_message(
                            f"Current strike mode is {self.inventory[self.curr_item_index].
                                                      max_strikes_per_click[self.inventory[self.curr_item_index].
                                                                            curr_max_strikes_per_click_index]} rounds per hold", 1)
                        self.can_press_mmb = False
                else:
                    self.can_press_mmb = True
                if ((keyboard["R"]) and isinstance(self.inventory[self.curr_item_index], Weapon)
                        and self.inventory[self.curr_item_index].is_available):
                    for i, el in enumerate(self.inventory):
                        if isinstance(el, Ammo) \
                           and el.load_in(self.inventory[self.curr_item_index]):
                            (Game.levels[Game.current_level] if not self.in_camp
                             else Game.camp_level).show_temp_message("Recharging is in process",
                                                                     self.inventory[self.curr_item_index].recharging_period)
                            if el.bullets == 0:
                                self.inventory[i] = None
                            break
                    else:
                        (Game.levels[Game.current_level] if not self.in_camp
                            else Game.camp_level).show_temp_message("No ammo in inventory", 2)
                if keyboard["M"]:
                    if self.can_press_m:
                        if self.inventory[self.curr_item_index].modification is not None:
                            self.level_items.append(
                                self.inventory[self.curr_item_index].modification)
                            Game.levels[Game.current_level].drop(
                                self.inventory[self.curr_item_index].modification)
                            self.inventory[self.curr_item_index].modification.unuse(
                            )
                            self.inventory[self.curr_item_index].modification = None
                            (Game.levels[Game.current_level] if not self.in_camp
                             else Game.camp_level).show_temp_message("Modification unused and dropped", 2)
                        else:
                            for i, el in enumerate(arcade.check_for_collision_with_list(self, self.level_items)):
                                if el.item_id in WEAPON_MODIFICATIONS_ID:
                                    self.inventory[self.curr_item_index].modification = el
                                    el.use(
                                        self.inventory[self.curr_item_index])
                                    self.level_items.remove(el)
                                    break
                        self.can_press_m = False
                else:
                    self.can_press_m = True
            self.inventory[self.curr_item_index].update(delta_time)
            self.inventory[self.curr_item_index].set_angle(self.hands.angle + 90 * (1 if self.right_look else -1),
                                                           self.right_look, self.hands)
            self.inventory[self.curr_item_index].center_x = (self.hands.center_x
                                                             + (self.hands.height / 2)
                                                             * cos(radians(self.inventory[self.curr_item_index].angle))
                                                             * (1 if self.right_look else -1))
            self.inventory[self.curr_item_index].center_y = (self.hands.center_y
                                                             + (self.hands.height / 2)
                                                             * sin(radians(-self.inventory[self.curr_item_index].angle))
                                                             * (1 if self.right_look else -1))
        for i, el in enumerate(self.inventory[0:self.inventory.equipped_size]):
            if el is not None:
                el.center_y = self.center_y + \
                    self.inventory.equipment_slots[i][3]
                el.center_x = self.center_x + \
                    self.inventory.equipment_slots[i][2] * \
                    (1 if self.inventory[i].right_look else -1)
        if (keyboard["E"] and self.inventory[self._curr_item_index] is not None
                and isinstance(self.inventory[self._curr_item_index], Item)):
            self.inventory[self._curr_item_index].use(self)
        if mouse["SCROLL"] != 0:
            self.curr_item_index = self.curr_item_index + mouse["SCROLL"]
            mouse["SCROLL"] = 0
        if keyboard["T"]:
            for el in arcade.check_for_collision_with_list(self, self.level_items):
                if self.inventory.append(el):
                    self.level_items.remove(el)
                    break
        if keyboard["Q"]:
            if self.can_press_q:
                self.can_press_q = False
                Game.game_on_pause = True
                for i in keyboard.keys():
                    keyboard[i] = False
                if self.in_camp:
                    self.inventory.return_to = Game.camp_level
                else:
                    self.inventory.return_to = Game.levels[Game.current_level]
                Game.levels[Game.current_level].window.show_view(
                    self.inventory)
        else:
            self.can_press_q = True

    def check_shoot(self, left_mouse_button_pressed):
        if isinstance(self.inventory[self.curr_item_index], Weapon):
            self.inventory[self.curr_item_index].check_shoot(
                self.right_look, left_mouse_button_pressed)
