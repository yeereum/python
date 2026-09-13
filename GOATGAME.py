import arcade

window_width = 960
window_height = 540
window = arcade.Window(
    width=window_width,
    height=window_height,
    title="GOAT GAME",
)
window.center_window()

class GOATGAME(arcade.View):
    def __init__(self):
        super().__init__()
        self.keypress = {
            "W": False, "S": False, "A": False, "D": False, "F": False, "Space": False
        }

        # ================== 오브젝트 =============================================
        self.object_list = arcade.SpriteList()

        self.player = arcade.Sprite(
            path_or_texture = "assets/images/DdongGo0101.jpg",
            center_x = 400,
            center_y = 300,
            scale = 0.1,
            angle = 0
        )

        self.character = [
            {
                "name" : "DdongGo0101",
                "texture" : arcade.load_texture("assets/images/DdongGo0101.jpg"),
                "speed" : 250,
                "scale" : 0.1,
            },
            {
                "name" : "H_Tteok03",
                "texture" : arcade.load_texture("assets/images/H_Tteok03.jpg"),
                "speed" : 100,
                "scale" : 0.2
            },
            {
                "name" : "juni0928",
                "texture" : arcade.load_texture("assets/images/juni0928.jpg"),
                "speed" : 600,
                "scale" : 0.05
            }
        ]    

        self.player_spin = 200
        self.player_speed = 200
        self.state = 0
        self.object_list.append(self.player)
        # ========================================================================

    def on_show_view(self):
        arcade.set_background_color(arcade.color.SKY_BLUE)

    def on_draw(self):
        self.clear()
        arcade.draw_text(
            text=f"Pos X: {int(self.player.center_x)}, Y: {int(self.player.center_y)}",
            x = 10, y = 520,
            color = arcade.color.BLACK,
            font_size = 15,
            )
        self.object_list.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W:
            self.keypress["W"] = True
        elif key == arcade.key.S:
            self.keypress["S"] = True
        elif key == arcade.key.A:
            self.keypress["A"] = True
        elif key == arcade.key.D:
            self.keypress["D"] = True
        elif key == arcade.key.F: # F키 캐릭터 스왑
            self.state = (self.state + 1) % len(self.character)
            self.player.texture = self.character[self.state]["texture"]
            self.player.scale = self.character[self.state]["scale"]
            self.player_speed = self.character[self.state]["speed"]
        elif key == arcade.key.SPACE:
            self.keypress["Space"] = True
        elif key == arcade.key.F11: # 전체화면 전환
            self.window.set_fullscreen(not self.window.fullscreen)

    def on_key_release(self, key, modifiers):
        if key == arcade.key.W:
            self.keypress["W"] = False
        elif key == arcade.key.S:
            self.keypress["S"] = False
        elif key == arcade.key.A:
            self.keypress["A"] = False
        elif key == arcade.key.D:
            self.keypress["D"] = False
        elif key == arcade.key.SPACE:
            self.keypress["Space"] = False

    def on_update(self, delta_time):
        if self.keypress["W"]:
            self.player.center_y += self.player_speed * delta_time
        if self.keypress["S"]:
            self.player.center_y -= self.player_speed * delta_time
        if self.keypress["A"]:
            self.player.center_x -= self.player_speed * delta_time
        if self.keypress["D"]:
            self.player.center_x += self.player_speed * delta_time
        if self.keypress["Space"]:
            self.player.angle += self.player_spin * delta_time

window.show_view(GOATGAME())
arcade.run()