import arcade


class ValueWithSender:
    def __init__(self, value, sender):
        self.value = value
        self.sender = sender
        self.v = self.value
        self.s = self.sender


class CharacterDrawList(arcade.SpriteList):
    def insert(self, index, to_insert):
        old_sprite_list = self.sprite_list
        self.clear()
        for i, el in enumerate(old_sprite_list):
            if i == index:
                self.append(to_insert)
            self.append(el)
