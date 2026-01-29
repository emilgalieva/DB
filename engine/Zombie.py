import arcade
from engine.AdvancedResources import ValueWithSender
from engine.Game import Game
from settings import GRAVITY_CONSTANT, STANDART_ZOMBIE_HP, ZOMBIE_TEXTURE, SCREEN_WIDTH, SCREEN_HEIGHT
import math
import random


class Zombie(arcade.Sprite):
    def __init__(self, center_x, center_y, walls=None, patrol_range=200):
        super().__init__(ZOMBIE_TEXTURE, 2.0, center_x, center_y)
        self._hp = STANDART_ZOMBIE_HP
        self.max_hp = STANDART_ZOMBIE_HP
        self.walk_speed = 80
        self.damage = 15
        self.attack_range = 50
        self.detection_range = 300
        self.attack_cooldown = 1.5
        self.attack_timer = 0
        self.right_look = random.choice([True, False])
        self.is_alive = True
        self.change_x = 0
        self.change_y = 0
        self.walls = walls
        self.invulnerable_timer = 0
        self.flash_timer = 0
        self.is_flashing = False
        self.flash_alpha = 255
        self.is_on_ground = False

        self.patrol_range = patrol_range
        self.patrol_start_x = center_x
        self.patrol_target_x = center_x + \
            random.randint(-patrol_range, patrol_range)
        self.patrol_change_timer = 0
        self.patrol_change_interval = random.uniform(2.0, 5.0)

        self.max_fall_speed = -300
        self.jump_power = 150
        self.can_jump = False

        self.damage_flash_duration = 0.2
        self.knockback_force = 100

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        damage = self._hp - value.v
        self._hp = value.v
        if damage > 0:
            self.take_damage(damage, getattr(value, 's', None))
        if self._hp <= 0:
            self.die()

    def take_damage(self, damage, damage_source=None):
        self.invulnerable_timer = 0.3
        self.flash_timer = self.damage_flash_duration
        self.is_flashing = True
        if damage_source and hasattr(damage_source, 'center_x'):
            dx = self.center_x - damage_source.center_x
            dy = self.center_y - damage_source.center_y
            dist = max(math.sqrt(dx * dx + dy * dy), 1)
            self.change_x += (dx / dist) * self.knockback_force
            self.change_y += (dy / dist) * self.knockback_force

    def update(self, delta_time, player=None):
        if not self.is_alive:
            return

        self.attack_timer += delta_time
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= delta_time

        if self.is_flashing:
            self.flash_timer -= delta_time
            self.flash_alpha = 100 + 155 * abs(math.sin(self.flash_timer * 30))
            self.alpha = int(self.flash_alpha)
            if self.flash_timer <= 0:
                self.is_flashing = False
                self.alpha = 255

        self.patrol_change_timer += delta_time

        if player and self.can_see_player(player):
            self.chase_player(player, delta_time)
        else:
            self.patrol(delta_time)

        self.update_movement(delta_time)

        if self._hp <= 0 and self.is_alive:
            self.die()

    def can_see_player(self, player):
        if not player:
            return False

        dx = player.center_x - self.center_x
        dy = player.center_y - self.center_y
        distance = math.sqrt(dx * dx + dy * dy)

        return distance <= self.detection_range

    def chase_player(self, player, delta_time):
        dx = player.center_x - self.center_x
        dy = player.center_y - self.center_y
        distance = math.sqrt(dx * dx + dy * dy) if dx != 0 or dy != 0 else 0
        if distance > self.attack_range and distance > 0:
            self.change_x = (dx / distance) * self.walk_speed
        else:
            self.change_x = 0
            if self.attack_timer >= self.attack_cooldown and distance <= self.attack_range:
                self.attack(player)

    def patrol(self, delta_time):
        if self.patrol_change_timer >= self.patrol_change_interval:
            self.patrol_target_x = self.patrol_start_x + \
                random.randint(-self.patrol_range, self.patrol_range)
            self.patrol_change_timer = 0
            self.patrol_change_interval = random.uniform(2.0, 5.0)
        dx = self.patrol_target_x - self.center_x
        if abs(dx) > 10:
            self.change_x = math.copysign(self.walk_speed * 0.5, dx)
            if dx > 0 and not self.right_look:
                self.flip_direction()
            elif dx < 0 and self.right_look:
                self.flip_direction()
        else:
            self.change_x = 0

    def flip_direction(self):
        self.texture = self.texture.flip_horizontally()
        self.right_look = not self.right_look

    def update_movement(self, delta_time):
        self.change_y -= GRAVITY_CONSTANT * delta_time * 60
        self.change_y = max(self.change_y, self.max_fall_speed)
        max_speed = self.walk_speed * 1.5
        self.change_x = max(-max_speed, min(max_speed, self.change_x))
        if abs(self.change_x) < 1:
            self.change_x = 0
        else:
            self.change_x *= 0.9
        old_x = self.center_x
        self.center_x += self.change_x * delta_time
        if self.walls:
            wall_collisions = arcade.check_for_collision_with_list(
                self, self.walls)
            if wall_collisions:
                self.center_x = old_x
                self.change_x = 0
                if self.is_on_ground:
                    self.flip_direction()
                    if random.random() < 0.3:
                        self.change_y = self.jump_power
                        self.is_on_ground = False
        old_y = self.center_y
        self.center_y += self.change_y * delta_time
        if self.walls:
            wall_collisions = arcade.check_for_collision_with_list(
                self, self.walls)
            if wall_collisions:
                for wall in wall_collisions:
                    if self.change_y < 0:
                        self.bottom = wall.top
                        self.is_on_ground = True
                        self.can_jump = True
                    elif self.change_y > 0:
                        self.top = wall.bottom
                    self.change_y = 0
                    break
            else:
                self.is_on_ground = False

    def attack(self, player):
        if self.attack_timer >= self.attack_cooldown:
            dx = player.center_x - self.center_x
            dy = player.center_y - self.center_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance <= self.attack_range:
                damage_value = player.hp - self.damage
                player.hp = ValueWithSender(damage_value, self)
                self.attack_timer = 0

                self.change_x = -self.change_x * 0.5

    def die(self):
        if not self.is_alive:
            return
        Game.zombies_killed += 1
        self.is_alive = False
        self.change_x = 0
        self.change_y = 0
        self.remove_from_sprite_lists()
