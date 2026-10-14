import arcade
from PIL import Image

window_width = 1280
window_height = 720

window = arcade.Window(
    width=window_width,
    height=window_height,
    title="poop!",
    fullscreen=True,
    resizable=False
)
window.center_window()

class button:
    def __init__(self):
        pass


class poop(arcade.View):
    def __init__(self):
        super().__init__()

        # 키 입력 상태
        self.keypress = {
            "W": False,
            "S": False,
            "A": False,
            "D": False,
            "F": False,
            "Space": False,
        }

        # ================== 배경 ==================

        self.lobby_images = arcade.load_texture(
            "assets/images/lobby.png"
        )

        # ================== 캐릭터 ==================

        self.player = arcade.Sprite(
            path_or_texture="assets/images/DdongGo0101.jpg",
            center_x=400,
            center_y=300,
            scale=0.1,
            angle=0
        )

        self.character = [
            {
                "name": "DdongGo0101",
                "texture": arcade.load_texture("assets/images/DdongGo0101.jpg"),
                "speed": 250,
                "scale": 0.1,
            },
            {
                "name": "H_Tteok03",
                "texture": arcade.load_texture("assets/images/H_Tteok03.jpg"),
                "speed": 100,
                "scale": 0.2
            },
            {
                "name": "juni0928",
                "texture": arcade.load_texture("assets/images/juni0928.jpg"),
                "speed": 600,
                "scale": 0.05
            }
        ]

        self.state = 0
        self.player_spin = 200
        self.player_speed = self.character[0]["speed"]

        self.object_list = arcade.SpriteList()
        self.object_list.append(self.player)

        # ================== 로비화면 설정 ==================

        self.lobby_true = True # 버튼 떠있는 화면이 True
        button_image = Image.open("assets/images/buttons.png").convert("RGBA")
        image_width, image_height = button_image.size

        start_button = button_image.crop(
            (0, 0, round(image_width / 3), image_height)
        )

        exit_button = button_image.crop(
            (round(image_width / 3), 0, round(image_width * 2 / 3), image_height)
        )

        record_button = button_image.crop(
            (round(image_width * 2 / 3), 0, image_width, image_height)
        )

        start_texture = arcade.Texture(image=start_button)
        exit_texture = arcade.Texture(image=exit_button)
        record_texture = arcade.Texture(image=record_button)

        # ================ 버튼 크기 및 위치 ==================
        button_scale = 1

        self.start_button = arcade.Sprite(
            start_texture,
            center_x=800,
            center_y=400,
            scale=button_scale
        )

        self.exit_button = arcade.Sprite(
            exit_texture,
            center_x=950,
            center_y=220,
            scale=button_scale
        )

        self.record_button = arcade.Sprite(
            record_texture,
            center_x=1100,
            center_y=400,
            scale=button_scale
        )

        self.buttons = arcade.SpriteList()
        self.buttons.append(self.start_button)
        self.buttons.append(self.exit_button)
        self.buttons.append(self.record_button)

        self.hovered_button = None

    # ================== 화면 그리기 ==================

    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(
            self.lobby_images,
            arcade.XYWH(
                self.window.width / 2,
                self.window.height / 2,
                self.window.width,
                self.window.height
            )
        )

        if self.lobby_true:
            self.buttons.draw()
        else:
            self.object_list.draw()

    # ================== 호버 이벤트 ==================

    def on_mouse_motion(self, x, y, dx, dy):
        self.hovered_button = None

        for button in self.buttons:
            if button.collides_with_point((x, y)):
                self.hovered_button = button
                button.color = (255, 220, 160)
            else:
                button.color = (255, 255, 255)

    # ================== 버튼 클릭 ==================

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.lobby_true:
            return

        if self.start_button.collides_with_point((x, y)):
            self.lobby_true = False

        elif self.record_button.collides_with_point((x, y)):
            print("해당 기능(기록)은 준비중 :)")

        elif self.exit_button.collides_with_point((x, y)):
            arcade.exit()

    # ================== 키 입력 ==================

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            if not self.lobby_true:
                self.lobby_true = True
            return

        if self.lobby_true:
            return

        if key == arcade.key.W:
            self.keypress["W"] = True

        elif key == arcade.key.S:
            self.keypress["S"] = True

        elif key == arcade.key.A:
            self.keypress["A"] = True

        elif key == arcade.key.D:
            self.keypress["D"] = True

        elif key == arcade.key.F:
            self.state = (self.state + 1) % len(self.character)

            self.player.texture = self.character[self.state]["texture"]
            self.player.scale = self.character[self.state]["scale"]
            self.player_speed = self.character[self.state]["speed"]

    # ================== 키 입력 해제 ==================

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

    # ================== 게임 업데이트 ==================

    def on_update(self, delta_time):
        if self.lobby_true:
            return

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


window.show_view(poop())
arcade.run()