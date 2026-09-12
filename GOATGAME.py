import arcade

window = arcade.Window(width=800, height=600, title="My Arcade Game")
window.center_window()

class GOATGAME(arcade.View):
    def __init__(self):
        super().__init__()
        self.circle_x = 400
        self.circle_y = 300
        self.circle_radius = 50
        self.circle_speed = 250
        self.keypress = {'W': False, 'S': False, 'A': False, 'D': False}
        
    def on_show_view(self):
        arcade.set_background_color(arcade.color.SKY_BLUE)

    def on_draw(self):
        self.clear()
        arcade.draw.draw_circle_filled(
            center_x=self.circle_x, center_y=self.circle_y, radius=self.circle_radius, color=arcade.color.AERO_BLUE
            )
        arcade.draw.draw_circle_outline(
            center_x=self.circle_x, center_y=self.circle_y, radius=self.circle_radius, color=arcade.color.BALL_BLUE, border_width=5
            )
        arcade.draw_text(
            text=f"Pos X: {int(self.circle_x)}, Y: {int(self.circle_y)}", x=50, y=550, color=arcade.color.BLACK, font_size=30
            )

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.W:
            self.keypress['W'] = True
        elif key == arcade.key.S:
            self.keypress['S'] = True
        elif key == arcade.key.A:
            self.keypress['A'] = True
        elif key == arcade.key.D:
            self.keypress['D'] = True

    def on_key_release(self, key: int, modifiers: int):
        if key == arcade.key.W:
            self.keypress['W'] = False
        elif key == arcade.key.S:
            self.keypress['S'] = False
        elif key == arcade.key.A:
            self.keypress['A'] = False
        elif key == arcade.key.D:
            self.keypress['D'] = False

    def on_update(self, delta_time: float):
        if self.keypress['W']:
            self.circle_y += self.circle_speed * delta_time
        if self.keypress['S']:
            self.circle_y -= self.circle_speed * delta_time
        if self.keypress['A']:
            self.circle_x -= self.circle_speed * delta_time
        if self.keypress['D']:
            self.circle_x += self.circle_speed * delta_time

window.show_view(GOATGAME())
arcade.run()