import arcade.gui
from settings import SCREEN_HEIGHT, SCREEN_WIDTH
from engine.Item import *


class InventorySlot(arcade.gui.UITextureButton):
    def __init__(self, inventory_index: int, x: float = 0, y: float = 0, width: float | None = None,
                 height: float | None = None,
                 texture=None,
                 texture_on_forbidden_doing=None,
                 texture_on_choice=None,
                 forbidden_texture_duration: float = 1.0,
                 all_textures_outline=1,
                 text: str = "",
                 multiline: bool = False,
                 scale: float | None = None,
                 style=None,
                 size_hint: tuple[float | None, float | None] | None = None,
                 size_hint_min: tuple[float | None,
                                      float | None] | None = None,
                 size_hint_max: tuple[float | None, float | None] | None = None, owner: "Player" = None,
                 connected_to=None):
        super().__init__(x=x, y=y, width=width, height=height, texture=texture, text=text,
                         multiline=multiline, scale=scale, style=style, size_hint=size_hint,
                         size_hint_min=size_hint_min, size_hint_max=size_hint_max)
        self.inventory_index = inventory_index
        self.item_texture = None
        self.texture_on_forbidden_doing = texture_on_forbidden_doing
        self.texture_on_choice = texture_on_choice
        self.forbidden_done = False
        self.forbidden_texture_duration = forbidden_texture_duration
        self.remove_forbidden_texture = lambda delta_time: self.on_forbidden_doing(
            to_disable_forbidden_texture=True)
        self.all_textures_outline = all_textures_outline
        self.std_texture = self.texture
        self.on_click = lambda event: connected_to(self)
        self.owner = owner

    def draw_item(self):
        if self.inventory_index != -1 and self.owner.inventory[self.inventory_index] is not None:
            self.item_texture = arcade.Texture(self.owner.inventory.inventory
                                               [self.inventory_index].texture.image)
            k = (self.width - self.all_textures_outline * 2) / \
                self.item_texture.width
            arcade.draw_texture_rect(self.item_texture, arcade.LBWH(self.center_x - self.width // 2
                                                                    + self.all_textures_outline, self.center_y -
                                                                    self.item_texture.height // 2 * k,
                                                                    self.width - self.all_textures_outline * 2,
                                                                    self.item_texture.height * k))

    def on_forbidden_doing(self, delta_time=None, to_disable_forbidden_texture=False):
        if self.forbidden_done and not to_disable_forbidden_texture:
            arcade.unschedule(self.remove_forbidden_texture)
            arcade.schedule(self.remove_forbidden_texture,
                            self.forbidden_texture_duration)
        elif self.forbidden_done:
            self.texture = self.std_texture
            self.texture_pressed = self.std_texture
            self.texture_hovered = self.std_texture
            self._textures["disabled"] = self.std_texture
            self.forbidden_done = False
            arcade.unschedule(self.remove_forbidden_texture)
        else:
            self.texture = self.texture_on_forbidden_doing
            self.texture_pressed = self.texture_on_forbidden_doing
            self.texture_hovered = self.texture_on_forbidden_doing
            self._textures["disabled"] = self.texture_on_forbidden_doing
            self.forbidden_done = True
            arcade.schedule(self.remove_forbidden_texture,
                            self.forbidden_texture_duration)

    def choice(self):
        self.texture = self.texture_on_choice
        self.texture_pressed = self.texture_on_choice
        self.texture_hovered = self.texture_on_choice
        self._textures["disabled"] = self.texture_on_choice

    def unchoice(self):
        self.texture = self.std_texture
        self.texture_pressed = self.std_texture
        self.texture_hovered = self.std_texture
        self._textures["disabled"] = self.std_texture


class Inventory(arcade.View):
    """Class, that represents an entity's inventory"""

    def __init__(self, std_inventory_size: int, width: int, slot_size: int,
                 distance_around_slots: int, slot_texture: arcade.Texture,
                 equipment_slots: Sequence[Sequence[int, arcade.Texture, int]], slot_on_forbidden_texture: arcade.Texture,
                 slot_on_choice_texture: arcade.Texture, slot_for_dropping_texture: arcade.Texture, owner):
        super().__init__(background_color=arcade.color.BLACK)
        self.background_color = (40, 40, 40)
        self.equipped_size = len(equipment_slots)
        self.inventory = [None for i in range(
            std_inventory_size + self.equipped_size)]
        self.width_in_slots = width // slot_size
        self.slot_size = slot_size
        self.first_pressed_slot = None
        self.distance_around_slots = distance_around_slots
        self.slots = []
        self.owner = owner
        self.return_to = None
        self.slot_texture = slot_texture
        self.equipment_slots = equipment_slots
        self.slot_on_forbidden_texture = slot_on_forbidden_texture
        self.slot_on_choice_texture = slot_on_choice_texture
        self.slot_for_dropping_texture = slot_for_dropping_texture
        self.gui_manager = arcade.gui.UIManager()
        self.create_inventory()

    def __len__(self):
        return len(self.inventory)

    def __getitem__(self, item):
        return self.inventory[item]

    def __setitem__(self, key, value):
        self.inventory[key] = value

    def create_inventory(self):
        """Initializes and moves slots"""
        to_add_to_x = self.distance_around_slots + self.slot_size
        x = self.distance_around_slots
        to_sub_from_y = self.distance_around_slots + self.slot_size
        y = SCREEN_HEIGHT
        i = -1
        for i in range(self.equipped_size):
            y -= to_sub_from_y
            self.slots.append(InventorySlot(
                i, x, y, self.slot_size, self.slot_size, self.equipment_slots[i][1],
                self.slot_on_forbidden_texture, self.slot_on_choice_texture, 0.5, 5, owner=self.owner,
                connected_to=self.slot_pressed))
        y = SCREEN_HEIGHT - self.distance_around_slots - self.slot_size
        i += 1
        quit_flag = False
        while True:
            x = to_add_to_x - self.slot_size
            for it in range(self.width_in_slots):
                if i == len(self.inventory):
                    quit_flag = True
                    break
                x += to_add_to_x
                self.slots.append(InventorySlot(
                    i, x, y, self.slot_size, self.slot_size, self.slot_texture,
                    self.slot_on_forbidden_texture, self.slot_on_choice_texture, 0.5, 5, owner=self.owner,
                    connected_to=self.slot_pressed))
                i += 1
            if quit_flag:
                break
            y -= to_sub_from_y
        self.slots.append(InventorySlot(-1, SCREEN_WIDTH - self.slot_size - 5, SCREEN_HEIGHT - self.slot_size - 5,
                                        self.slot_size, self.slot_size,
                                        texture=self.slot_for_dropping_texture,
                                        texture_on_choice=self.slot_on_choice_texture,
                                        texture_on_forbidden_doing=self.slot_on_choice_texture,
                                        all_textures_outline=5, connected_to=self.slot_pressed))
        for el in self.slots:
            self.gui_manager.add(el)

    def on_draw(self):
        self.clear()
        self.gui_manager.draw()
        for el in self.slots:
            el.draw_item()

    def on_show_view(self) -> None:
        self.gui_manager.enable()

    def on_hide_view(self) -> None:
        self.gui_manager.disable()

    def slot_pressed(self, slot: InventorySlot):
        """Called when inventory slot is pressed"""
        if self.first_pressed_slot is not None:
            self.first_pressed_slot.unchoice()
            temp_list = tuple(el.inventory_index for el in (
                self.first_pressed_slot, slot) if el.inventory_index != -1)
            if len(temp_list) == 1 and self.inventory[temp_list[0]] is not None:
                self.slots[-1].on_forbidden_doing()
                self.owner.level_items.append(
                    self.inventory[temp_list[0]])
                self.inventory[temp_list[0]].position = (
                    self.owner.center_x, self.owner.center_y)
                self.return_to.drop(self.inventory[temp_list[0]])
                self.inventory[temp_list[0]] = None
                if temp_list[0] < self.equipped_size:
                    self.inventory[temp_list[0]].unuse()
            elif len(temp_list) == 2:
                self.replace_items(
                    (self.first_pressed_slot.inventory_index, slot.inventory_index))
            self.first_pressed_slot = None
        else:
            self.first_pressed_slot = slot
            self.first_pressed_slot.choice()

    def append(self, item):
        """Appends item to inventory, if can"""
        for i in range(self.equipped_size, len(self.inventory)):
            if self.inventory[i] is None:
                self.inventory[i] = item
                return True
        return False

    def replace_items(self, two_items_indexes: tuple[int, int]):
        """Process events, when two slots are pressed"""
        a = None
        for i, el in enumerate(two_items_indexes):
            if el < self.equipped_size:
                if a is None:
                    a = i
                else:
                    a = -1
        if a is not None:
            none_in_chosen = (self.inventory[two_items_indexes[0]] is None,
                              self.inventory[two_items_indexes[1]] is None)
            if two_items_indexes[0] != two_items_indexes[1] and not all(none_in_chosen):
                if (a == -1 and not all(none_in_chosen) and all(none_in_chosen[i]
                   or (self.inventory[el].equip_place in (EquippableItem.ANY,
                                                          self.equipment_slots[two_items_indexes[(i + 1) % 2]][0]))
                        for i, el in enumerate(two_items_indexes))):
                    pass
                elif a != -1 and (none_in_chosen[(a + 1) % 2]
                                  or (((isinstance(self.inventory[two_items_indexes[(a + 1) % 2]], EquippableItem)
                                        and self.inventory[two_items_indexes[(a + 1) % 2]].equip_place
                                        in (self.equipment_slots[two_items_indexes[a]][0], EquippableItem.ANY))))):
                    if not none_in_chosen[(a + 1) % 2]:
                        self.inventory[two_items_indexes[(
                            a + 1) % 2]].use(self.owner)
                        self.inventory[two_items_indexes[(
                            a + 1) % 2]].set_angle(0, self.owner.right_look, None)
                    elif not none_in_chosen[a]:
                        self.inventory[two_items_indexes[a]].unuse()
                elif not all(none_in_chosen):
                    self.slots[two_items_indexes[0]].on_forbidden_doing()
                    self.slots[two_items_indexes[1]].on_forbidden_doing()
                    return
                else:
                    return
            else:
                return
        elif two_items_indexes[0] == two_items_indexes[1]:
            self.owner.curr_item_index = two_items_indexes[0]
            return
        (self.inventory[two_items_indexes[0]],
            self.inventory[two_items_indexes[1]]) = (self.inventory[two_items_indexes[1]],
                                                     self.inventory[two_items_indexes[0]])

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        if symbol == arcade.key.Q:
            self.window.show_view(self.return_to)
