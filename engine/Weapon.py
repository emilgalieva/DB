from typing import Any
import arcade
from arcade import particles
from settings import (BULLET_STEP, WEAPON_RECOIL_FALL_SPEED, BULLET_SMOKE_PARTICLE_LIFETIME,
                      BULLET_SMOKE_PARTICLE_TEXTURE, BULLET_SMOKE_PARTICLE_SPEED_Y, BULLET_SMOKE_PARTICLE_MAX_SPEED_X,
                      BULLET_SMOKE_PARTICLES_COUNT)
from math import asin, acos, degrees, radians, cos, sin
from random import randint

def create_smoke_emitter(x, y):
    return particles.Emitter(
        center_xy=(x, y),
        emit_controller=particles.EmitBurst(BULLET_SMOKE_PARTICLES_COUNT),
        particle_factory=lambda emitter: particles.LifetimeParticle(
            filename_or_texture=BULLET_SMOKE_PARTICLE_TEXTURE,
            change_xy=(randint(int(-BULLET_SMOKE_PARTICLE_MAX_SPEED_X * 1000),
                               int(BULLET_SMOKE_PARTICLE_MAX_SPEED_X * 1000)) / 1000 / 60,
                       BULLET_SMOKE_PARTICLE_SPEED_Y / 60),
            lifetime=BULLET_SMOKE_PARTICLE_LIFETIME,
            scale=1,
            alpha=255)
        )

class Bullet(arcade.Sprite):
    def __init__(self, path_or_texture, scale, center_x, center_y, angle, walls, enemies, damage, fall_speed,
                 max_steps):
        super().__init__(path_or_texture, scale, center_x, center_y, angle)
        self.enemies = enemies
        self.walls = walls
        self.damage = damage
        self.fall_speed = fall_speed
        self.max_steps = max_steps
        self.visible = False
        self.left_texture = self.texture
        self.right_texture = self.texture.flip_horizontally()

    def fly(self, right_look):
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
                        el.hp -= self.damage
                break
            self.change_y -= self.fall_speed



class Weapon(arcade.Sprite):
    def __init__(self, center_x, center_y, angle, path_or_texture, scale, max_ammo, shooting_speed,
                 recharging_speed, bullet_start_y, recoil_per_strike, bullet_texture, bullet_scale, bullet_damage,
                 bullet_fall_speed, bullet_max_steps, walls, enemies):
        super().__init__(path_or_texture, scale, center_x, center_y, angle)
        self.recoil_per_strike = recoil_per_strike
        self.recoil = 0
        self.ammo = 0
        self.max_ammo = max_ammo
        self.shooting_period = 1 / shooting_speed
        self.is_available = True
        self.bullet_start_y_from_center = bullet_start_y * self.scale_y - self.height / 2
        self.recharging_period = 1 / recharging_speed
        self.bullet = Bullet(bullet_texture, bullet_scale, 0, 0, 0, walls, enemies, bullet_damage, bullet_fall_speed,
                             bullet_max_steps)
        self.smoke = None

    def set_angle(self, angle, right_look):
        self.angle = angle + self.recoil * (-1 if right_look else 1)


    def shoot(self, right_look):
        if self.is_available and self.ammo > 0:
            self.bullet.angle = self.angle - (0 if right_look else 180)
            self.bullet.center_x = ((self.width / 2 + self.bullet.width / 2) * cos(radians(-self.bullet.angle))
                                     - self.bullet_start_y_from_center * sin(radians(-self.bullet.angle))
                                    * (1 if right_look else -1) + self.center_x)
            self.bullet.center_y = ((self.width / 2 + self.bullet.width / 2) * sin(radians(-self.bullet.angle))
                                     + self.bullet_start_y_from_center * cos(radians(-self.bullet.angle))
                                    * (1 if right_look else -1) + self.center_y)
            self.recoil += self.recoil_per_strike
            self.smoke = create_smoke_emitter(*self.bullet.position)
            self.bullet.fly(right_look)
            self.is_available = False
            self.ammo -= 1
            arcade.schedule(self.on, self.shooting_period)

    def update(self, delta_time):
        if self.recoil > 0:
            self.recoil = max((self.recoil - WEAPON_RECOIL_FALL_SPEED * delta_time, 0))

    def recharge(self):
        self.ammo = self.max_ammo
        self.is_available = False
        arcade.schedule(self.on, self.recharging_period)

    def on(self, delta_time):
        self.is_available = True
        arcade.unschedule(self.on)

