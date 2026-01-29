import arcade


class HUD(arcade.Sprite):
    def __init__(self, icon, scale, center_x, center_y, hud_width, hud_fill_color, hud_outline_color):
        super().__init__(icon, scale, center_x, center_y)
        self.hud_width = hud_width
        self.hud_fill_color = hud_fill_color
        self.hud_outline_color = hud_outline_color
        self.draw_list = arcade.SpriteList()
        self.draw_list.append(self)

    def show(self, percent):
        percent /= 100
        self.draw_list.draw()
        arcade.draw_lbwh_rectangle_outline(self.center_x + self.width // 2 + 2, self.center_y - self.height // 2,
                                           self.hud_width, self.height, self.hud_outline_color, 2)
        arcade.draw_lbwh_rectangle_filled(self.center_x + self.width // 2 + 3, self.center_y - self.height // 2 + 1,
                                          (self.hud_width - 2) * percent, self.height - 2, self.hud_fill_color)
