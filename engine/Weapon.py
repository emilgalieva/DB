from typing import Any
import arcade
from arcade import particles

from engine.AdvancedResources import ValueWithSender
from settings import (BULLET_STEP, WEAPON_RECOIL_FALL_SPEED, BULLET_SMOKE_PARTICLE_LIFETIME,
                      BULLET_SMOKE_PARTICLE_TEXTURE, BULLET_SMOKE_PARTICLE_SPEED_Y, BULLET_SMOKE_PARTICLE_MAX_SPEED_X,
                      BULLET_SMOKE_PARTICLES_COUNT, BULLET_SMOKE_PARTICLES_INTERVAL)
from math import asin, acos, degrees, radians, cos, sin
from random import randint

def create_smoke_emitter(x, y):
    return particles.Emitter(
        center_xy=(x, y),
        emit_controller=particles.EmitterIntervalWithCount(BULLET_SMOKE_PARTICLES_INTERVAL, BULLET_SMOKE_PARTICLES_COUNT),
        particle_factory=lambda emitter: particles.LifetimeParticle(
            filename_or_texture=arcade.make_soft_circle_texture(10, (150, 150, 150, 255), 100, 0),
            change_xy=(randint(int(-BULLET_SMOKE_PARTICLE_MAX_SPEED_X * 1000),
                               int(BULLET_SMOKE_PARTICLE_MAX_SPEED_X * 1000)) / 1000 / 60,
                       BULLET_SMOKE_PARTICLE_SPEED_Y / 60),
            lifetime=BULLET_SMOKE_PARTICLE_LIFETIME,
            scale=1,
            alpha=255, mutation_callback=smoke_mutation)
    )

def smoke_mutation(particle: particles.Particle, to_sub_per_frame=255 / BULLET_SMOKE_PARTICLE_LIFETIME / 60):
    if particle.alpha > 0:
        particle.alpha -= to_sub_per_frame

class Bullet(arcade.Sprite):
    def __init__(self, path_or_texture, scale, center_x, center_y, angle, damage, fall_speed,
                 max_steps):
        super().__init__(path_or_texture, scale, center_x, center_y, angle)
        self.enemies = None
        self.walls = None
        self.damage = damage
        self.fall_speed = fall_speed
        self.max_steps = max_steps
        self.visible = False
        self.left_texture = self.texture
        self.right_texture = self.texture.flip_horizontally()

    def fly(self, right_look):
        #!
        self.enemies = arcade.SpriteList()
        self.visible = True
        self.texture = (self.right_texture if right_look else self.left_texture)
        self.change_x = cos(radians(self.angle)) * BULLET_STEP
        self.change_y = sin(radians(-self.angle)) * BULLET_STEP
        for i in range(0, self.max_steps):
            self.center_x += self.change_x
            self.center_y += self.change_y
            gipoten = ((self.change_y ** 2 + self.change_x ** 2) ** 0.5)
            self.angle = (degrees(asin(self.change_y / gipoten))
                          * (-1 if self.change_x / gipoten > 0 else 1))
            hitted = arcade.check_for_collision_with_lists(self, (self.enemies, self.walls))
            if len(hitted):
                for el in hitted:
                    if el in self.enemies:
                        el.hp -= ValueWithSender(self.damage, self)
                break
            self.change_y -= self.fall_speed



class Weapon(arcade.Sprite):
    def __init__(self, path_or_texture: "str | arcade.Texture", scale: int | float, center_x: int, center_y: int,
                 angle: int | float, max_ammo: int, shooting_speed: int | float, recharging_speed: int,
                 bullet_start_y: int | float, recoil_per_strike: int | float,
                 type_of_bullet: int, bullet_texture: "str | arcade.Texture", bullet_scale: int | float,
                 bullet_damage: int | float, bullet_fall_speed: int | float, bullet_max_steps: int,
                 max_strikes_per_click: tuple):
        super().__init__(path_or_texture, scale, center_x, center_y, angle)
        self.right_look = True
        self.type_of_bullet = type_of_bullet
        self.recoil_per_strike = recoil_per_strike
        self.recoil = 0
        self.ammo = 0
        self.max_ammo = max_ammo
        self.shooting_period = 1 / shooting_speed
        self.is_available = True
        self.bullet_start_y_from_center = bullet_start_y * self.scale_y
        self.recharging_period = 1 / recharging_speed
        self.bullet = Bullet(bullet_texture, bullet_scale, 0, 0, 0, bullet_damage, bullet_fall_speed,
                             bullet_max_steps)
        self.strikes_per_click = 0
        self.max_strikes_per_click = max_strikes_per_click
        self.curr_max_strikes_per_click_index = 0
        self.smoke = None
        self._modification = None

    @property
    def walls(self):
        return self.bullet.walls

    @walls.setter
    def walls(self, walls):
        self.bullet.walls = walls

    @property
    def enemies(self):
        return self.bullet.enemies

    @enemies.setter
    def enemies(self, enemies):
        self.bullet.enemies = enemies

    @property
    def modification(self):
        return self._modification

    @modification.setter
    def modification(self, new_modification):
        if self._modification is not None:
            self._modification.unuse()
        if new_modification is not None:
            self._modification = new_modification
            self._modification.use(self)

    def set_angle(self, angle, right_look, hands):
        self.angle = angle + self.recoil * (-1 if right_look else 1)
        hands.angle += self.recoil * (-1 if right_look else 1)
        if right_look != self.right_look:
            self.texture = self.texture.flip_horizontally()
            self.right_look = right_look

    def check_shoot(self, right_look, left_mouse_button_pressed):
        if left_mouse_button_pressed:
            if (self.is_available and self.ammo > 0
                    and self.strikes_per_click < self.max_strikes_per_click[self.curr_max_strikes_per_click_index]):
                self.bullet.angle = self.angle - (0 if right_look else 180)
                self.bullet.center_x = ((self.width / 2 + self.bullet.width / 2) * cos(radians(-self.bullet.angle))
                                     - self.bullet_start_y_from_center * sin(radians(-self.bullet.angle))
                                    * (1 if right_look else -1) + self.center_x)
                self.bullet.center_y = ((self.width / 2 + self.bullet.width / 2) * sin(radians(-self.bullet.angle))
                                     + self.bullet_start_y_from_center * cos(radians(-self.bullet.angle))
                                    * (1 if right_look else -1) + self.center_y)
                self.recoil += self.recoil_per_strike
                self.smoke = create_smoke_emitter(*self.position)
                self.bullet.fly(right_look)
                self.is_available = False
                self.ammo -= 1
                self.strikes_per_click += 1
                arcade.schedule(self.on, self.shooting_period)
        else:
            self.strikes_per_click = 0

    def update(self, delta_time):
        if self.recoil > 0:
            self.recoil = max((self.recoil - WEAPON_RECOIL_FALL_SPEED * delta_time, 0))
        # if self._modification is not None:

    def change_shooting_mode(self):
        self.curr_max_strikes_per_click_index = ((self.curr_max_strikes_per_click_index + 1)
                                                 % len(self.max_strikes_per_click))
        self.strikes_per_click = 0
        print(self.curr_max_strikes_per_click_index)


    def recharge(self):
        self.is_available = False
        arcade.schedule(self.on, self.recharging_period)

    def on(self, delta_time):
        self.is_available = True
        arcade.unschedule(self.on)

