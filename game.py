import arcade

class Game(arcade.View):
    def __init__(self):
        super().__init__()

        self.keypress = {
            "W": False,
            "S": False,
            "A": False,
            "D": False,
        }

        self.character = [
            {
                "name": "DdongGo0101",
                "texture": arcade.load_texture("assets/images/game/DdongGo.png"),
                "speed": 250,
                "scale": 0.2,
            }
        ]

        self.state = 0
        self.player_spin = 200
        self.player_speed = self.character[self.state]["speed"]

        self.player = arcade.Sprite(
            self.character[self.state]["texture"],
            center_x=400,
            center_y=300,
            scale=self.character[self.state]["scale"],
            angle=0
        )
        self.object_list = arcade.SpriteList()
        self.object_list.append(self.player)

    def on_draw(self):
        self.clear(arcade.color.DARK_SLATE_GRAY)
        self.object_list.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            from lobby import Lobby
            self.window.show_view(Lobby())
            return

        if key == arcade.key.W:
            self.keypress["W"] = True
        elif key == arcade.key.S:
            self.keypress["S"] = True
        elif key == arcade.key.A:
            self.keypress["A"] = True
        elif key == arcade.key.D:
            self.keypress["D"] = True

    def on_key_release(self, key, modifiers):
        if key == arcade.key.W:
            self.keypress["W"] = False
        elif key == arcade.key.S:
            self.keypress["S"] = False
        elif key == arcade.key.A:
            self.keypress["A"] = False
        elif key == arcade.key.D:
            self.keypress["D"] = False

    def on_update(self, delta_time):
        if self.keypress["W"]:
            self.player.center_y += self.player_speed * delta_time
        if self.keypress["S"]:
            self.player.center_y -= self.player_speed * delta_time
        if self.keypress["A"]:
            self.player.center_x -= self.player_speed * delta_time
        if self.keypress["D"]:
            self.player.center_x += self.player_speed * delta_time