import arcade

class Information(arcade.View):
    def __init__(self, lobby):
        super().__init__()
        self.lobby = lobby

        self.background = arcade.load_texture(
            "assets/images/lobby/information.png"
        )

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(
            self.background,
            arcade.XYWH(
                self.window.width / 2,
                self.window.height / 2,
                self.window.width,
                self.window.height,
            ),
        )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(self.lobby)