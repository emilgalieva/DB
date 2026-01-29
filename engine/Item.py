from collections.abc import Sequence
import arcade
from engine.AdvancedResources import *
# from engine.Weapon import Weapon


class Ammo(arcade.Sprite):
    PISTOL_BULLET = 0
    RIFLE_BULLET = 1

    def __init__(self, path_or_texture, scale, center_x, center_y, angle, bullets, type_of_bullet, item_id):
        super().__init__(path_or_texture, scale, center_x, center_y, angle)
        self.item_id = item_id
        self.bullets = bullets
        self.type_of_bullet = type_of_bullet
        self.right_look = True

    def set_angle(self, angle, right_look, hands):
        self.angle = angle
        if right_look != self.right_look:
            self.texture = self.texture.flip_horizontally()
            self.right_look = right_look

    def load_in(self, weapon):
        if weapon.type_of_bullet == self.type_of_bullet:
            filled = min((weapon.max_ammo - weapon.ammo), self.bullets)
            self.bullets -= filled
            weapon.ammo += filled
            weapon.recharge()
            return True
        return False

    def copy(self):
        return Ammo(self.texture, self.scale, 0, 0, 0, self.bullets, self.type_of_bullet, self.item_id)


class Effect:
    """This class's objects are effects, that can be used and unused on a live creatures"""

    def __init__(self, power: Sequence[int], connected_to: Sequence[str]):
        """self.connected_to arguments must ..., for example check Player.hp"""
        self.power = power
        self.connected_to = connected_to
        self.entity = None

    def use_on(self, entity):
        for param, power in zip(self.connected_to, self.power):
            exec(
                f"entity.{param} = ValueWithSender(entity.{param} + power, self)")
        self.entity = entity

    def unuse(self):
        for param, power in zip(self.connected_to, self.power):
            exec(
                f"self.entity.{param} = ValueWithSender(self.entity.{param} - power, self)")


class TempEffectWithCancel(Effect):
    """Objects of this class are effects, that live 'duration' time, at start they '+' power to owner's attributes,
     at the end of their life they '-' power from owner's attributes"""

    def __init__(self, power: Sequence[int], connected_to: Sequence[str], duration: float):
        super().__init__(power, connected_to)
        self.duration = duration

    def use_on(self, entity):
        """Starts effect's living cycle"""
        super().use_on(entity)
        entity.effects.append(self)
        arcade.schedule(self.unuse, self.duration)

    def unuse(self, delta_time):
        """Ends effect's living cycle"""
        super().unuse()
        self.entity.effects_with_duration.remove(self)
        arcade.unschedule(self.unuse)


class MultipleTempEffect(TempEffectWithCancel):
    """Objects of this class are effects, that live 'duration' time and work with interval_between interval between
        an editing attributes, and don't cancel results"""

    def __init__(self, power: Sequence[int], connected_to: Sequence[str], duration: float, interval_between: float):
        super().__init__(power, connected_to, duration)
        self.interval_between = interval_between

    def use_on(self, delta_time, entity=None):
        """Starts the effect's living cycle"""
        entity = self.entity
        super().use_on(entity)
        arcade.schedule(self.use_on, self.interval_between)

    def unuse(self, delta_time):
        """Ends the effect's living cycle"""
        arcade.unschedule(self.use_on)
        arcade.unschedule(self.unuse)
        self.entity.effects_with_duration.remove(self)


class Item(arcade.Sprite):
    """This item is the base class for other items and is not intended for using in the game"""

    def __init__(self, path_or_texture, scale, center_x, center_y, angle, effect, item_id):
        super().__init__(path_or_texture, scale, center_x, center_y, angle)
        self.item_id = item_id
        self.right_look = True
        self.effect = effect
        self.is_available = True

    def set_angle(self, angle, right_look, hands):
        self.angle = angle
        if right_look != self.right_look:
            self.texture = self.texture.flip_horizontally()
            self.right_look = right_look

    def copy(self):
        return Item(self.texture, self.scale, 0, 0, 0, self.effect, self.item_id)


class TemporaryItem(Item):
    """An item, that are not reusable"""

    def use(self, entity):
        self.effect.use_on(entity)
        entity.draw_list.remove(entity.inventory[entity.curr_item_index])
        entity.inventory[entity.curr_item_index] = None


class EquippableItem(Item):
    """An item, that can be equipped and unequipped"""
    ANY = 0
    FOR_HEAD = 1
    FOR_BODY = 2

    def __init__(self, path_or_texture, scale, center_x, center_y, angle, equip_place, effect, item_id):
        super().__init__(path_or_texture, scale, center_x, center_y, angle, effect, item_id)
        self.equip_place = equip_place

    def use(self, entity):
        """Uses item's effect"""
        self.effect.use_on(entity)
        if not (self is entity.inventory[entity.curr_item_index]):
            entity.draw_list.insert(1, self)

    def unuse(self):
        """Unuses item effect"""
        self.effect.unuse()
        self.effect.entity.draw_list.remove(self)

    def copy(self):
        return EquippableItem(self.texture, self.scale, 0, 0, 0, self.equip_place, self.effect, self.item_id)


class WeaponModification(Item):
    def use(self, entity):
        self.effect.use_on(entity)

    def unuse(self):
        self.effect.unuse()
