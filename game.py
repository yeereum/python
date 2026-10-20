
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

        self.move_speed = 300
        self.moving_keys = set()

        self.box_width = 700
        self.box_height = 400
        self.box_center_y = 300
        self.box_border_width = 5

        self.hp_bar_width = 300
        self.hp_bar_height = 18
        self.hp_bar_x = self.window.width / 2
        self.hp_bar_y = 800

        self.heart_sheet = arcade.load_spritesheet(
            "assets/images/game/heart.png"
        )

        self.heart_textures = self.heart_sheet.get_texture_grid(
            size=(400, 400),
            columns=2,
            count=4,
        )

        self.heart_scale = 0.3
        self.max_hp = 5
        self.player_hp = 5

        self.heart_positions = [
            (100, 350),
            (200, 350),
            (300, 350),
            (100, 250),
            (200, 250),
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
        self.spare_heart_position = (300, 250)

        self.player = arcade.Sprite(
            "assets/images/game/DdongGo.png",
            scale=0.1,
        )
        self.player.position = (
            self.window.width / 2,
            self.box_center_y,
        )

        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)

        body_sheet = arcade.load_spritesheet(
            "assets/images/poop/body.png"
        )

        self.body_frames = body_sheet.get_texture_grid(
            size=(1120, 720),
            columns=2,
            count=8,
        )

        self.boss_scale = 0.5

        self.poop_body = Poop_boss(
            self.body_frames,
            scale=self.boss_scale,
        )
        self.poop_body.position = (
            self.window.width / 2,
            650,
        )

        arm_sheet = arcade.load_spritesheet(
            "assets/images/poop/arm.png"
        )

        self.arm_frames = arm_sheet.get_texture_grid(
            size=(1120, 720),
            columns=2,
            count=5,
        )

        self.arm_index = 0

        self.poop_arm = arcade.Sprite(
            self.arm_frames[self.arm_index],
            scale=self.boss_scale,
        )
        self.poop_arm.position = self.poop_body.position

        self.poop_boss_list = arcade.SpriteList()
        self.poop_boss_list.append(self.poop_body)
        self.poop_boss_list.append(self.poop_arm)

        self.boss_max_hp = 100
        self.boss_hp = 100

    def change_heart_texture(self, index, texture_index):
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

    def remove_spare_heart(self):
        self.spare_heart = None

    def arm_form(self, index):
        if 0 <= index < len(self.arm_frames):
            self.arm_index = index
            self.poop_arm.texture = self.arm_frames[index]

    def attack(self):
        print("공격!")

    def on_draw(self):
        self.clear()

        arcade.draw_rect_outline(
            arcade.XYWH(
                self.window.width / 2,
                self.box_center_y,
                self.box_width,
                self.box_height,
            ),
            color = (255, 255, 255),
            border_width = 5,
        )

        self.heart_list.draw()

        if self.spare_heart is not None:
            self.spare_heart.draw()

        self.poop_boss_list.draw()
        self.player_list.draw()

        arcade.draw_rect_filled(
            arcade.XYWH(
                self.hp_bar_x,
                self.hp_bar_y,
                self.hp_bar_width,
                self.hp_bar_height,
            ),
            (70, 30, 30),
        )

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

    def on_update(self, delta_time):
        self.poop_body.update_animation(delta_time)
        self.poop_arm.position = self.poop_body.position

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

        if move_x != 0 and move_y != 0:
            move_x *= 0.70710678
            move_y *= 0.70710678

        self.player.center_x += move_x * self.move_speed * delta_time
        self.player.center_y += move_y * self.move_speed * delta_time

        left = self.window.width / 2 - self.box_width / 2
        right = self.window.width / 2 + self.box_width / 2
        bottom = self.box_center_y - self.box_height / 2
        top = self.box_center_y + self.box_height / 2

        half_width = self.player.width / 2
        half_height = self.player.height / 2

        self.player.center_x = max(
            left + self.box_border_width + half_width,
            min(
                self.player.center_x,
                right - self.box_border_width - half_width,
            ),
        )

        self.player.center_y = max(
            bottom + self.box_border_width + half_height,
            min(
                self.player.center_y,
                top - self.box_border_width - half_height,
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