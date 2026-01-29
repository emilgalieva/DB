import arcade
import random
import arcade.gui
import engine.Inventory
from engine.Game import *
from engine.BaseLevel import BaseLevel
from engine.database import save_player
from settings import INVENTORY_SLOT_SIZE, INVENTORY_SLOT_TEXTURE, INVENTORY_EQUIPMENT_SLOTS, \
    INVENTORY_SLOT_FORBIDDEN_TEXTURE, INVENTORY_SLOT_ON_CHOICE_TEXTURE, INVENTORY_SLOT_FOR_DROPPING_TEXTURE, \
    ITEM_PRICES, TRADER_INVENTORY_SIZE, TRADER_ITEMS_GEN_TUPLE, DOCTOR_ITEMS_GEN_TUPLE, DOCTOR_INVENTORY_SIZE, \
    ARMORER_INVENTORY_SIZE, ARMORER_ITEMS_GEN_TUPLE, TRADER_TEXTURE, DOCTOR_TEXTURE, ARMORER_TEXTURE, SCREEN_WIDTH, \
    SCREEN_HEIGHT

PLAYER_SPEED = 5.0
PLAYER_SCALE = 0.6


DAY_NIGHT_SPEED = 0.01

PALETTE = {
    "forest_dark": (15, 20, 15),
    "tree_green": (30, 45, 30),
    "mud": (45, 35, 25),
    "water": (40, 60, 65),
    "water_glint": (80, 100, 110),
    "bridge": (70, 50, 30),
}


class CampNPCInventory(engine.Inventory.Inventory):
    def __init__(self, std_inventory_size: int, width: int, slot_size: int,
                 distance_around_slots: int, slot_texture: arcade.Texture,
                 equipment_slots, slot_on_forbidden_texture: arcade.Texture,
                 slot_on_choice_texture: arcade.Texture, slot_for_dropping_texture: arcade.Texture, owner: CampNPC):
        super().__init__(std_inventory_size, width, slot_size,
                         distance_around_slots, slot_texture,
                         equipment_slots, slot_on_forbidden_texture,
                         slot_on_choice_texture, slot_for_dropping_texture, owner)
        self.player_money_label = arcade.gui.UILabel(
            x=self.window.width - 300, y=100)
        self.gui_manager.add(self.player_money_label)

    def append(self, item, by_player=False):
        if self.inventory.count(None) >= 2 or by_player:
            for i in range(self.equipped_size, len(self.inventory)):
                if self.inventory[i] is None:
                    self.inventory[i] = item
                    return True
        return False

    def slot_pressed(self, slot):
        if self.first_pressed_slot is not None:
            self.first_pressed_slot.unchoice()
            temp_list = tuple(el.inventory_index for el in (
                self.first_pressed_slot, slot) if el.inventory_index != -1)
            if ((len(temp_list) == 1 and self.inventory[temp_list[0]] is not None
                    and Game.player.money >= ITEM_PRICES[self.inventory[temp_list[0]].item_id])
                    and Game.player.inventory.append(self.inventory[temp_list[0]])):
                Game.player.money -= ITEM_PRICES[self.inventory[temp_list[0]].item_id]
                self.slots[-1].on_forbidden_doing()
                self.inventory[temp_list[0]] = None
            elif (len(temp_list) == 2 and self.first_pressed_slot.inventory_index == slot.inventory_index
                    and Game.player.inventory[Game.player.curr_item_index] is not None
                    and self.append(Game.player.inventory[Game.player.curr_item_index], by_player=True)):
                Game.player.money \
                    += ITEM_PRICES[Game.player.inventory[Game.player.curr_item_index].item_id]
                Game.player.draw_list.remove(
                    Game.player.inventory[Game.player.curr_item_index])
                Game.player.inventory[Game.player.curr_item_index] = None
            self.first_pressed_slot = None
        else:
            self.first_pressed_slot = slot
            self.first_pressed_slot.choice()

    def on_draw(self):
        self.clear()
        self.player_money_label.text = "Current balance: " + \
            str(Game.player.money)
        super().on_draw()

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        if symbol == arcade.key.I:
            self.window.show_view(self.return_to)


class CampNPC(arcade.Sprite):
    def __init__(self, path_or_texture, scale, center_x, center_y, inventory_size, item_gen_tuple):
        super().__init__(path_or_texture, scale, center_x, center_y)
        self.is_available = True
        self.inventory = CampNPCInventory(inventory_size, 1000, INVENTORY_SLOT_SIZE, 5,
                                          arcade.load_texture(
                                              INVENTORY_SLOT_TEXTURE),
                                          [],
                                          arcade.load_texture(
                                              INVENTORY_SLOT_FORBIDDEN_TEXTURE),
                                          arcade.load_texture(
                                              INVENTORY_SLOT_ON_CHOICE_TEXTURE),
                                          arcade.load_texture(INVENTORY_SLOT_FOR_DROPPING_TEXTURE), self)
        self.item_gen_tuple = item_gen_tuple

    def generate_item(self):
        rand_gen_event = random.choice(self.item_gen_tuple)
        if rand_gen_event is not None:
            for el in Game.camp_level.items:
                if el.item_id == rand_gen_event:
                    to_append = el.copy()
                    if not self.inventory.append(to_append):
                        for i in range(len(self.inventory)):
                            self.inventory[i] = None
                        self.inventory.append(to_append)


class CampView(BaseLevel):
    def __init__(self, tilemap_path, brightness):
        super().__init__(tilemap_path, brightness)
        self.next_level_button = arcade.gui.UIFlatButton(x=self.window.width - 120, y=50, width=100,
                                                         height=30, text="Next level")
        self.next_level_button.on_click = self.temp
        self.i_pressed = False
        self.can_press_i = True
        self.sun = arcade.Sprite(arcade.make_soft_circle_texture(100, (40, 255, 255, 255), 255, 30), 1,
                                 SCREEN_HEIGHT // 2 - 60, SCREEN_WIDTH - 60, 0)
        self.temp_a = arcade.SpriteList()
        self.temp_a.append(self.sun)
        self.sun = self.temp_a
        self.background_color = arcade.color.SKY_BLUE
        super().on_show_view()
        self.gui_manager.add(self.next_level_button)
        self.setup()

    def temp(self, event):
        self.window.show_view(Game.levels[Game.current_level])
        Game.player.in_camp = False

    def on_show_view(self) -> None:
        if not Game.game_on_pause:
            Game.player.position = self.tilemap.sprite_lists["player_spawn"][0].position
            self.create_physics_engine()
            for el in self.npc:
                if el.is_available:
                    el.generate_item()
            Game.player.in_camp = True
        else:
            Game.game_on_pause = False
        self.gui_manager.enable()

    def on_hide_view(self) -> None:
        self.gui_manager.disable()
        Game.player.change_x = 0
        if not Game.game_on_pause:
            Game.player.in_camp = False
            save_player(Game.player)

    def setup(self):
        self.npc = [CampNPC(TRADER_TEXTURE, 1, 0, 0, TRADER_INVENTORY_SIZE, TRADER_ITEMS_GEN_TUPLE),
                    CampNPC(DOCTOR_TEXTURE, 1, 0, 0,
                            DOCTOR_INVENTORY_SIZE, DOCTOR_ITEMS_GEN_TUPLE),
                    CampNPC(ARMORER_TEXTURE, 1, 0, 0, ARMORER_INVENTORY_SIZE, ARMORER_ITEMS_GEN_TUPLE)]
        self.npc_draw_list = arcade.SpriteList()
        for el in self.npc:
            self.npc_draw_list.append(el)
        for el, ael in zip(self.tilemap.get_tilemap_layer("npc").tiled_objects, self.tilemap.sprite_lists["npc"]):
            self.npc[el.properties["building_id"]].center_y = ((self.tilemap.height
                                                               * self.tilemap.tile_height - el.coordinates.y)
                                                               + ael.height / 2)
            self.npc[el.properties["building_id"]
                     ].center_x = el.coordinates.x + ael.width / 2
            self.npc[el.properties["building_id"]].scale = ael.scale

    def on_draw(self):
        super().on_draw()
        self.game_camera.use()
        self.npc_draw_list.draw()
        self.sun.draw()
        self.gui_camera.use()
        self.next_level_button.visible = True
        self.gui_manager.draw()

    def on_update(self, delta_time):
        super().on_update(delta_time)
        if self.keyboard_pressed["I"]:
            if self.can_press_i:
                for el in arcade.check_for_collision_with_list(Game.player, self.npc_draw_list):
                    el.inventory.return_to = self
                    Game.game_on_pause = True
                    self.can_press_i = False
                    self.window.show_view(el.inventory)
                    break
        else:
            self.can_press_i = True
