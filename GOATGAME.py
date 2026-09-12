import arcade

window = arcade.Window(
    width=800, height=600, title="GOAT GAME"
)
window.center_window()

class GOATGAME(arcade.View):
    def __init__(self):
        super().__init__()
        self.keypress = {
            "W": False, "S": False, "A": False, "D": False, "F": False
        }

        # ================== 오브젝트 =============================================
        self.object_list = arcade.SpriteList()

        self.DdongGo0101 = arcade.Sprite(
            path_or_texture = "images/DdongGo0101.jpg",
            center_x = 400,
            center_y = 300,
            scale = 0.1
        )
        self.DdongGo0101_speed = 250

        self.state = 0
        self.textures = [
            arcade.load_texture("images/DdongGo0101.jpg"),
            arcade.load_texture("images/H_Tteok03.jpg"),
            arcade.load_texture("images/juni0928.jpg"),
        ]

        self.object_list.append(self.DdongGo0101)
        # ========================================================================

    def on_show_view(self):
        arcade.set_background_color(arcade.color.SKY_BLUE)

    def on_draw(self):
        self.clear()
        arcade.draw_text(
            text=f"Pos X: {int(self.DdongGo0101.center_x)}, Y: {int(self.DdongGo0101.center_y)}",
            x = 30, y = 550,
            color = arcade.color.BLACK, font_size = 30
            )
        self.object_list.draw()

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.W:
            self.keypress["W"] = True
        elif key == arcade.key.S:
            self.keypress["S"] = True
        elif key == arcade.key.A:
            self.keypress["A"] = True
        elif key == arcade.key.D:
            self.keypress["D"] = True
        elif key == arcade.key.F:
            self.state = (self.state + 1) % len(self.textures)
            self.DdongGo0101.texture = self.textures[self.state]

    def on_key_release(self, key: int, modifiers: int):
        if key == arcade.key.W:
            self.keypress["W"] = False
        elif key == arcade.key.S:
            self.keypress["S"] = False
        elif key == arcade.key.A:
            self.keypress["A"] = False
        elif key == arcade.key.D:
            self.keypress["D"] = False

    def on_update(self, delta_time: float):
        if self.keypress["W"]:
            self.DdongGo0101.center_y += self.DdongGo0101_speed * delta_time
        if self.keypress["S"]:
            self.DdongGo0101.center_y -= self.DdongGo0101_speed * delta_time
        if self.keypress["A"]:
            self.DdongGo0101.center_x -= self.DdongGo0101_speed * delta_time
        if self.keypress["D"]:
            self.DdongGo0101.center_x += self.DdongGo0101_speed * delta_time

window.show_view(GOATGAME())
arcade.run()