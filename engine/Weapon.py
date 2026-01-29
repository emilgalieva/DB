from typing import Any
import arcade
from arcade import particles
from engine.AdvancedResources import ValueWithSender
from engine.Game import *
from settings import (BULLET_STEP, WEAPON_RECOIL_FALL_SPEED, BULLET_SMOKE_PARTICLE_LIFETIME,
                      BULLET_SMOKE_PARTICLE_TEXTURE, BULLET_SMOKE_PARTICLE_SPEED_Y, BULLET_SMOKE_PARTICLE_MAX_SPEED_X,
                      BULLET_SMOKE_PARTICLES_COUNT, BULLET_SMOKE_PARTICLES_INTERVAL,
                      WEAPONS_BARREL_END_POS_X_FROM_CENTER)
from math import asin, acos, degrees, radians, cos, sin
from random import randint


def create_smoke_emitter(x, y):
    return particles.Emitter(
        center_xy=(x, y),
        emit_controller=particles.EmitterIntervalWithCount(
            BULLET_SMOKE_PARTICLES_INTERVAL, BULLET_SMOKE_PARTICLES_COUNT),
        particle_factory=lambda emitter: particles.LifetimeParticle(
            filename_or_texture=arcade.make_soft_circle_texture(
                10, (150, 150, 150, 255), 100, 0),
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


def check_bullet_trajectory(weapon, right_look):
    weapon.bullet.angle, weapon.bullet.center_x, weapon.bullet.center_y = weapon.bullet_start_settings(
        right_look)
    weapon.bullet.change_x = cos(radians(weapon.bullet.angle)) * BULLET_STEP
    weapon.bullet.change_y = sin(radians(-weapon.bullet.angle)) * BULLET_STEP
    for i in range(0, weapon.bullet.max_steps):
        weapon.bullet.center_x += weapon.bullet.change_x
        weapon.bullet.center_y += weapon.bullet.change_y
        gipoten = ((weapon.bullet.change_y ** 2 +
                   weapon.bullet.change_x ** 2) ** 0.5)
        weapon.bullet.angle = (degrees(asin(weapon.bullet.change_y / gipoten))
                               * (-1 if weapon.bullet.change_x / gipoten > 0 else 1))
        hitted = arcade.check_for_collision_with_lists(
            weapon.bullet, (weapon.bullet.enemies, weapon.bullet.walls))
        if len(hitted):
            weapon.bullet.visible = False
            return hitted, (weapon.bullet.center_x, weapon.bullet.center_y)
        weapon.bullet.change_y -= weapon.bullet.fall_speed
    return [], (weapon.bullet.center_x, weapon.bullet.center_y)


class Bullet(arcade.Sprite):
    def __init__(self, path_or_texture, scale, center_x, center_y, angle, damage, fall_speed,
                 max_steps):
        super().__init__(path_or_texture, scale, center_x, center_y, angle)
        self.enemies = None
        self.walls = None
        self._damage = damage
        self.fall_speed = fall_speed
        self.max_steps = max_steps
        self.visible = False
        self.left_texture = self.texture
        self.right_texture = self.texture.flip_horizontally()

    @property
    def damage(self):
        return self._damage

    @damage.setter
    def damage(self, value):
        self._damage = value.v

    def fly(self, weapon, right_look):
        self.texture = (
            self.right_texture if right_look else self.left_texture)
        for el in check_bullet_trajectory(weapon, right_look)[0]:
            if el in self.enemies:
                el.hp = ValueWithSender(el.hp - self.damage, self)
        self.visible = True


class Weapon(arcade.Sprite):
    LASER_MODIFICATION = 0
    MBC_MODIFICATION = 1
    LONG_BARREL_MODIFICATION = 2

    def __init__(self, path_or_texture: "str | arcade.Texture", scale, center_x: int, center_y: int,
                 angle: int | float, max_ammo: int, shooting_speed: int | float, recharging_speed: int | float,
                 bullet_start_y: int | float, recoil_per_strike: int | float,
                 type_of_bullet: int, bullet_texture: "str | arcade.Texture", bullet_scale,
                 bullet_damage: int | float, bullet_fall_speed: int | float, bullet_max_steps: int,
                 max_strikes_per_click: tuple, item_id):
        super().__init__(path_or_texture, scale, center_x, center_y, angle)
        self.item_id = item_id
        self.right_look = True
        self.type_of_bullet = type_of_bullet
        self._recoil_per_strike = recoil_per_strike
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
        self.modification = None
        self.shooting_sound = arcade.Sound("assets/Weapons/shooting_sound.wav")
        self.recharging_sound = arcade.Sound(
            "assets/Weapons/recharging_sound.wav")

    @property
    def recoil_per_strike(self):
        return self._recoil_per_strike

    @recoil_per_strike.setter
    def recoil_per_strike(self, value):
        self._recoil_per_strike = value.v

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

    def copy(self):
        return Weapon(self.texture, self.scale, 0, 0, 0, self.max_ammo, 1 / self.shooting_period,
                      1 / self.recharging_period, self.bullet_start_y_from_center / self.scale_y,
                      self.recoil_per_strike, self.type_of_bullet, self.bullet.texture, self.bullet.scale,
                      self.bullet.damage, self.bullet.fall_speed, self.bullet.max_steps, self.max_strikes_per_click,
                      self.item_id)

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
                self.smoke = create_smoke_emitter(*self.position)
                self.bullet.fly(self, right_look)
                self.recoil += self.recoil_per_strike
                self.is_available = False
                self.ammo -= 1
                self.strikes_per_click += 1
                arcade.play_sound(self.shooting_sound)
                arcade.schedule(self.on, self.shooting_period)
                Game.strikes_done += 1
        else:
            self.strikes_per_click = 0

    def update(self, delta_time):
        if self.recoil > 0:
            self.recoil = max(
                (self.recoil - WEAPON_RECOIL_FALL_SPEED * delta_time, 0))
        if self.modification is not None:
            angle, self.modification.center_x, self.modification.center_y = self.bullet_start_settings(
                self.right_look)
            self.modification.set_angle(angle, self.right_look, None)

    def change_shooting_mode(self):
        self.curr_max_strikes_per_click_index = ((self.curr_max_strikes_per_click_index + 1)
                                                 % len(self.max_strikes_per_click))
        self.strikes_per_click = 0

    def recharge(self):
        self.is_available = False
        arcade.play_sound(
            self.recharging_sound, speed=self.recharging_period / self.recharging_sound.get_length())
        arcade.schedule(self.on, self.recharging_period)

    def on(self, delta_time):
        self.is_available = True
        arcade.unschedule(self.on)

    def bullet_start_settings(self, right_look):
        bullet_angle = self.angle - (0 if right_look else 180)
        return bullet_angle, \
            (WEAPONS_BARREL_END_POS_X_FROM_CENTER[self.item_id] * self.scale_x * cos(radians(-bullet_angle))
             - self.bullet_start_y_from_center * sin(radians(-bullet_angle))
             * (1 if right_look else -1) + self.center_x), \
            (WEAPONS_BARREL_END_POS_X_FROM_CENTER[self.item_id] * self.scale_x * sin(radians(-bullet_angle))
             + self.bullet_start_y_from_center * cos(radians(-bullet_angle))
             * (1 if right_look else -1) + self.center_y)
        # self.bullet.center_x =
        # self.bullet.center_y =
