import arcade


class Fadein:
    def __init__(self, duration=1.0):
        self.duration = max(duration, 0.001)
        self.elapsed_time = 0.0
        self.active = False
        self.started = False

    def start(self):
        self.elapsed_time = 0.0
        self.active = True
        self.started = True

    def update(self, delta_time):
        if not self.active:
            return

        self.elapsed_time += delta_time

        if self.elapsed_time >= self.duration:
            self.elapsed_time = self.duration
            self.active = False

    @property
    def alpha(self):
        if not self.started:
            return 0

        progress = min(self.elapsed_time / self.duration, 1.0)
        return int(255 * progress)


class Poop_boss(arcade.Sprite):
    def __init__(self, frames, scale):
        super().__init__(frames[0], scale=scale)

        self.frames = frames
        self.frame_index = 0
        self.elapsed_time = 0

    def update_animation(self, delta_time):
        self.elapsed_time += delta_time

        while self.elapsed_time >= 0.1:
            self.elapsed_time -= 0.1
            self.frame_index = (self.frame_index + 1) % len(self.frames)

        self.texture = self.frames[self.frame_index]


class Game(arcade.View):
    def __init__(self):
        super().__init__()

        arcade.load_font("assets/fonts/PressStart2P.ttf")

        self.game_over_true = False

        # 플레이어 이동속도
        self.move_speed = 300
        self.moving_keys = set()

        # 타이머
        self.remain_time = 180

        # 흰 박스 속성
        self.box_width = 700
        self.box_height = 400
        self.box_center_x = self.window.width / 2
        self.box_center_y = 300
        self.box_border_width = 5

        # 체력바
        self.hp_bar_width = 500
        self.hp_bar_height = 20
        self.hp_bar_x = self.window.width / 2
        self.hp_bar_y = 800

        # 플레이어 하트
        self.max_hp = 5
        self.player_hp = 5

        self.heart_sheet = arcade.load_spritesheet(
            "assets/images/game/heart.png"
        )

        self.heart_textures = self.heart_sheet.get_texture_grid(
            size=(400, 400),
            columns=2,
            count=4,
        )

        self.heart_scale = 0.3

        self.heart_positions = [
            (100, 400),
            (200, 400),
            (300, 400),
            (100, 300),
            (200, 300),
        ]

        self.heart_list = arcade.SpriteList()

        for x, y in self.heart_positions:
            heart = arcade.Sprite(
                self.heart_textures[0],
                scale=self.heart_scale,
            )
            heart.position = (x, y)
            self.heart_list.append(heart)

        self.spare_heart = None
        self.max_spare_hearts = 1
        self.spare_heart_position = (300, 300)

        self.spare_heart_list = arcade.SpriteList()

        self.player = arcade.Sprite(
            "assets/images/game/DdongGo.png",
            scale=0.1,
        )
        self.player.position = (
            self.box_center_x,
            self.box_center_y,
        )

        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)

        poop_body_sheet = arcade.load_spritesheet(
            "assets/images/poop/body.png"
        )

        self.poop_body_frames = poop_body_sheet.get_texture_grid(
            size=(1120, 720),
            columns=2,
            count=8,
        )

        self.boss_scale = 0.5

        self.poop_body = Poop_boss(
            self.poop_body_frames,
            scale=self.boss_scale,
        )
        self.poop_body.position = (
            self.window.width / 2,
            650,
        )

        poop_arm_sheet = arcade.load_spritesheet(
            "assets/images/poop/arm.png"
        )

        self.poop_arm_frames = poop_arm_sheet.get_texture_grid(
            size=(1120, 720),
            columns=2,
            count=5,
        )

        self.poop_arm_index = 0

        self.poop_arm = arcade.Sprite(
            self.poop_arm_frames[self.poop_arm_index],
            scale=self.boss_scale,
        )
        self.poop_arm.position = self.poop_body.position

        self.poop_boss_list = arcade.SpriteList()
        self.poop_boss_list.append(self.poop_body)
        self.poop_boss_list.append(self.poop_arm)

        self.boss_max_hp = 1000
        self.boss_hp = 1000

    def change_heart(self, index, texture_index):
        if not 0 <= index < len(self.heart_list):
            return

        if not 0 <= texture_index < len(self.heart_textures):
            return

        self.heart_list[index].texture = self.heart_textures[texture_index]

    def add_spare_heart(self):
        if self.spare_heart is not None:
            return

        self.spare_heart = arcade.Sprite(
            self.heart_textures[1],
            scale=self.heart_scale,
        )
        self.spare_heart.position = self.spare_heart_position
        self.spare_heart_list.append(self.spare_heart)

    def remove_spare_heart(self):
        self.spare_heart_list.clear()
        self.spare_heart = None

    def arm_form(self, index):
        if 0 <= index < len(self.arm_frames):
            self.arm_index = index
            self.poop_arm.texture = self.arm_frames[index]

    def damage(self):
        if self.player_hp <= 0 and self.spare_heart is None:
            return

        if self.spare_heart is None: 
            self.player_hp -= 1

            self.change_heart(
                self.player_hp,
                2,
            )

            self.player.color = (200, 40, 40) # 페이드아웃으로 색 다시 빠지게 할거임

        if self.spare_heart is not None:
            self.remove_spare_heart()

    def attack(self):
        print("공격!")

    def game_over(self):
        if self.game_over_true:
            return

        if self.remain_time <= 0:
            self.game_over_true = True

        elif self.player_hp <= 0:
            self.game_over_true = True

        if self.game_over_true:
            print("게임 종료")

    def on_draw(self):
        self.clear()

        self.background_color = (10, 11, 18)

        arcade.draw_rect_outline(
            arcade.XYWH(
                self.box_center_x,
                self.box_center_y,
                self.box_width,
                self.box_height,
            ),
            color = (255, 255, 255),
            border_width = self.box_border_width,
        )

        self.heart_list.draw()
        self.spare_heart_list.draw()
        self.poop_boss_list.draw()
        self.player_list.draw()

        # 체력바 바탕색
        arcade.draw_rect_filled(
            arcade.XYWH(
                self.hp_bar_x,
                self.hp_bar_y,
                self.hp_bar_width,
                self.hp_bar_height,
            ),
            (70, 30, 30),
        )

        # 체력바 현재 체력
        hp_ratio = self.boss_hp / self.boss_max_hp

        if hp_ratio > 0:
            current_width = self.hp_bar_width * hp_ratio

            arcade.draw_rect_filled(
                arcade.XYWH(
                    self.hp_bar_x - self.hp_bar_width / 2 + current_width / 2,
                    self.hp_bar_y,
                    current_width,
                    self.hp_bar_height,
                ),
                (230, 60, 60),
            )

        timer_min = int(self.remain_time) // 60
        timer_sec = int(self.remain_time) % 60
        timer_color = arcade.color.WHITE

        if self.remain_time < 11:
            timer_color = arcade.color.RED

        arcade.draw_text(
            "TIMER",
            1320,
            400,
            color=timer_color,
            font_size=20,
            font_name="Press Start 2P",
            anchor_x="center",
        )

        arcade.draw_text(
            f"{timer_min:02d}:{timer_sec:02d}",
            1320,
            350,
            color=timer_color,
            font_size=30,
            font_name="Press Start 2P",
            anchor_x="center",
        )

    def on_update(self, delta_time):
        self.poop_body.update_animation(delta_time)
        self.poop_arm.position = self.poop_body.position

        if self.remain_time > 0:
            self.remain_time -= delta_time
            self.remain_time = max(0, self.remain_time)
        
        self.game_over()

        move_x = 0
        move_y = 0

        if arcade.key.A in self.moving_keys:
            move_x -= 1
        if arcade.key.D in self.moving_keys:
            move_x += 1
        if arcade.key.W in self.moving_keys:
            move_y += 1
        if arcade.key.S in self.moving_keys:
            move_y -= 1

        # 대각선 보정
        if move_x != 0 and move_y != 0:
            move_x *= 0.70710678
            move_y *= 0.70710678

        self.player.center_x += move_x * self.move_speed * delta_time
        self.player.center_y += move_y * self.move_speed * delta_time

        box_left = self.box_center_x - self.box_width / 2
        box_right = self.box_center_x + self.box_width / 2
        box_bottom = self.box_center_y - self.box_height / 2
        box_top = self.box_center_y + self.box_height / 2

        self.player.center_x = max(
            box_left + self.box_border_width + self.player.width / 2,
            min(
                self.player.center_x,
                box_right - self.box_border_width - self.player.width / 2,
            ),
        )

        self.player.center_y = max(
            box_bottom + self.box_border_width + self.player.height / 2,
            min(
                self.player.center_y,
                box_top - self.box_border_width - self.player.height / 2,
            ),
        )

    def on_key_press(self, key, modifiers):
        if key in (
            arcade.key.W,
            arcade.key.A,
            arcade.key.S,
            arcade.key.D,
        ):
            self.moving_keys.add(key)

        elif key == arcade.key.SEMICOLON:
            self.attack()

        elif key == arcade.key.ESCAPE:
            arcade.exit()

        elif key == arcade.key.E:
            self.add_spare_heart()

        elif key == arcade.key.Q:
            self.remove_spare_heart()

        elif key == arcade.key.F:
            self.damage()

    def on_key_release(self, key, modifiers):
        self.moving_keys.discard(key)

if __name__ == "__main__":
    window = arcade.Window(
        1280,
        720,
        "poop!",
        fullscreen=True,
        resizable=False,
    )

    window.center_window()
    window.show_view(Game())

    arcade.run()