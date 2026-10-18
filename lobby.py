import arcade
from PIL import Image

class Button:
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

    def contains(self, x, y):
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


class Lobby(arcade.View):
    def __init__(self):
        super().__init__()

        # ================== 제목 ==================

        self.title = arcade.Sprite(
            path_or_texture="assets/images/lobby/title.png",
            center_x = self.window.width / 2,
            center_y = 650,
            scale = 0.9
        )

        # ================== 배경 ==================

        self.lobby_images = arcade.load_texture(
            "assets/images/lobby/lobby.png"
        )

        self.title_images = arcade.load_texture(
            "assets/images/lobby/title.png"
        )

        self.title_list = arcade.SpriteList()
        self.title_list.append(self.title)

        # ================== 로비화면 설정 ==================

        self.lobby_true = True
        button_image = Image.open("assets/images/lobby/buttons.png").convert("RGBA")
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
            Button(start_sprite, self.click_start),
            Button(exit_sprite, self.click_exit),
            Button(record_sprite, self.click_record),
        ]

        self.button_list = arcade.SpriteList()
        for button in self.buttons:
            self.button_list.append(button.sprite)

        self.hovered_button = None
        self.pressed_button = None

    # ================== 버튼 클릭 시 동작 ==================

    def click_start(self):
        from start_anima import StartAnima
        self.reset_buttons()
        self.window.show_view(StartAnima())

    def click_record(self):
        print("해당 기능(기록)은 준비중 :)")

    def click_exit(self):
        arcade.exit()

    # ================== 버튼 상태 도우미 ====================

    def button_at(self, x, y):
        for Button in self.buttons:
            if Button.contains(x, y):
                return Button
        return None

    def reset_buttons(self):
        self.hovered_button = None
        self.pressed_button = None
        for Button in self.buttons:
            Button.set_state(hovered=False, pressed=False)

    def refresh_buttons(self):
        for Button in self.buttons:
            is_pressed = Button is self.pressed_button
            show_pressed = is_pressed and Button is self.hovered_button
            Button.set_state(
                hovered=(Button is self.hovered_button),
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

        self.button_list.draw()
        self.title_list.draw()

    # ================== 마우스 이벤트 ==================

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.lobby_true:
            return
        self.hovered_button = self.button_at(x, y)
        self.refresh_buttons()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, mouse_button, modifiers):
        if not self.lobby_true or mouse_button != arcade.MOUSE_BUTTON_LEFT:
            return
        self.hovered_button = self.button_at(x, y)
        self.pressed_button = self.hovered_button
        self.refresh_buttons()

    def on_mouse_release(self, x, y, mouse_button, modifiers):
        if not self.lobby_true or mouse_button != arcade.MOUSE_BUTTON_LEFT:
            return

        pressed = self.pressed_button
        released_on = self.button_at(x, y)

        self.pressed_button = None
        self.hovered_button = released_on
        self.refresh_buttons()

        if pressed is not None and pressed is released_on:
            pressed.on_click()