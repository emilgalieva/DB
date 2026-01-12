import arcade

class Item(arcade.Sprite):
    def __init__(self, path_or_texture, scale, center_x, center_y, angle, power, connected_to: list[property]):
        super().__init__(path_or_texture, scale, center_x, center_y, angle)
        self.power = power
        self.connected_to = connected_to

class TemporaryItem(Item):
    def use(self):
        for i, el in enumerate(self.connected_to):
            el += self.power[i]

class ReusableItem(TemporaryItem):
    def unuse(self):
        for i, el in enumerate(self.connected_to):
            el -= self.power[i]

MEDICINE = TemporaryItem()
ITEMS = ()