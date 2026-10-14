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


class BUTTON:
    button_scale = 1

    def __init__(self, sprite, on_click):
        self.sprite = sprite
        self.on_click = on_click

        self.hit_width = sprite.texture.width * self.button_scale
        self.hit_height = sprite.texture.height * self.button_scale

        self.set_state(
            hovered=False,
            pressed=False
        )

    def contains(self, x: float, y: float) -> bool:
        return (abs(x - self.sprite.center_x) <= self.hit_width / 2 and
                abs(y - self.sprite.center_y) <= self.hit_height / 2)

    def set_state(self, hovered, pressed):

        if pressed:
            self.sprite.scale = self.button_scale * 0.95
            self.sprite.color = (255, 220, 160)
        elif hovered:
            self.sprite.scale = self.button_scale * 1.1
            self.sprite.color = (255, 220, 160)
        else:
            self.sprite.scale = self.button_scale
            self.sprite.color = (255, 255, 255)


class poop(arcade.View):
    def __init__(self):
        super().__init__()

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

        self.lobby_true = True  # 버튼 떠있는 화면이 True
        button_image = Image.open("assets/images/buttons.png").convert("RGBA")
        image_width, image_height = button_image.size

        start_image = button_image.crop(
            (0, 0, round(image_width / 3), image_height)
        )
        exit_image = button_image.crop(
            (round(image_width / 3), 0, round(image_width * 2 / 3), image_height)
        )
        record_image = button_image.crop(
            (round(image_width * 2 / 3), 0, image_width, image_height)
        )

        start_texture = arcade.Texture(image=start_image)
        exit_texture = arcade.Texture(image=exit_image)
        record_texture = arcade.Texture(image=record_image)

        # ================ 버튼 크기 및 위치 ==================
        button_scale = 1

        start_sprite = arcade.Sprite(
            start_texture, center_x=800, center_y=400, scale=button_scale
        )
        exit_sprite = arcade.Sprite(
            exit_texture, center_x=950, center_y=220, scale=button_scale
        )
        record_sprite = arcade.Sprite(
            record_texture, center_x=1100, center_y=400, scale=button_scale
        )

        self.buttons = [
            BUTTON(start_sprite, self.click_start),
            BUTTON(exit_sprite, self.click_exit),
            BUTTON(record_sprite, self.click_record),
        ]

        # 화면에 그리기 위한 SpriteList
        self.button_list = arcade.SpriteList()
        for button in self.buttons:
            self.button_list.append(button.sprite)

        self.hovered_button = None   # 지금 마우스가 올라가 있는 버튼
        self.pressed_button = None   # 마우스 왼쪽 버튼을 '누른 채'인 버튼

    # ================== 버튼 클릭 시 동작 ==================

    def click_start(self):
        self.lobby_true = False
        self.reset_buttons()

    def click_record(self):
        print("해당 기능(기록)은 준비중 :)")

    def click_exit(self):
        arcade.exit()

    # ================== 버튼 상태 도우미 ==================

    def button_at(self, x, y):
        """(x, y) 위치에 있는 버튼을 돌려준다. 없으면 None"""
        for button in self.buttons:
            if button.contains(x, y):
                return button
        return None

    def reset_buttons(self):
        """모든 버튼을 평소 상태로 되돌린다 (화면 전환할 때 사용)"""
        self.hovered_button = None
        self.pressed_button = None
        for button in self.buttons:
            button.set_state(hovered=False, pressed=False)

    def refresh_buttons(self):
        """hovered_button / pressed_button 값에 맞춰 모든 버튼의 모양을 갱신"""
        for button in self.buttons:
            is_pressed = button is self.pressed_button
            # 누른 채로 다른 곳으로 끌고 가면 눌림 효과는 잠시 풀리고,
            # 다시 원래 버튼 위로 돌아오면 눌림 효과가 돌아온다.
            show_pressed = is_pressed and button is self.hovered_button
            button.set_state(
                hovered=(button is self.hovered_button),
                pressed=show_pressed
            )

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
            self.button_list.draw()
        else:
            self.object_list.draw()

    # ================== 마우스 이벤트 ==================

    def on_mouse_motion(self, x, y, dx, dy):
        """호버: 마우스가 올라간 버튼을 기록하고 모양을 바꾼다."""
        if not self.lobby_true:
            return
        self.hovered_button = self.button_at(x, y)
        self.refresh_buttons()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """버튼을 누른 채로 마우스를 움직일 때도 호버 상태를 갱신한다."""
        self.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, mouse_button, modifiers):
        """누르는 순간에는 '어느 버튼을 눌렀는지'만 기록한다. (아직 클릭 아님)"""
        if not self.lobby_true or mouse_button != arcade.MOUSE_BUTTON_LEFT:
            return
        self.hovered_button = self.button_at(x, y)
        self.pressed_button = self.hovered_button
        self.refresh_buttons()

    def on_mouse_release(self, x, y, mouse_button, modifiers):
        """뗄 때: 누른 버튼과 같은 버튼 위에서 뗐을 때만 클릭으로 인정한다."""
        if not self.lobby_true or mouse_button != arcade.MOUSE_BUTTON_LEFT:
            return

        pressed = self.pressed_button
        released_on = self.button_at(x, y)

        # 상태를 먼저 정리한 뒤에 클릭 동작을 실행한다.
        # (클릭 동작이 화면을 바꾸면서 reset_buttons를 호출할 수 있기 때문)
        self.pressed_button = None
        self.hovered_button = released_on
        self.refresh_buttons()

        if pressed is not None and pressed is released_on:
            pressed.on_click()

    # ================== 키 입력 ==================

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            if not self.lobby_true:
                self.lobby_true = True
                self.reset_buttons()
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

        elif key == arcade.key.SPACE:
            self.keypress["Space"] = True

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