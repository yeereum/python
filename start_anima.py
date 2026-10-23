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

class StartAnima(arcade.View):
    def __init__(self):
        super().__init__()
        
        self.elapsed_time = 0

        self.box_fade = Fadein(duration=1.5)
        self.heart_fade = Fadein(duration=1.0)
        self.poop_fade = Fadein(duration=0.7)

        self.lobby_true = True
        self.box_true = False
        self.heart_true = False

        self.event = [
            {
                "time": 3.0,
                "action": lambda: (
                    arcade.play_sound(self.fire_sounds, speed=3),
                    self.poop_fade.start()
                ),
                "done": False
            },
            {
                "time": 4.5,
                "action": lambda: self.arm_form(3),
                "done": False
            },
            {
                "time": 6.0,
                "action": lambda: (
                    self.arm_form(4),
                    arcade.play_sound(self.finger_snap_sounds),
                ),
                "done": False
            },
            {
                "time": 6.15,
                "action": lambda: self.change_bg(),
                "done": False
            },
            {
                "time": 8.0,
                "action": lambda: (
                    self.arm_form(0),
                    self.box_appear()
                ),
                "done": False,
            },
            {
                "time": 10.5,
                "action": lambda: self.run_game(),
                "done": False,
            }
        ]

        self.lobby_images = arcade.load_texture("assets/images/lobby/lobby.png")

        self.finger_snap_sounds = arcade.load_sound("assets/sounds/finger_snap.mp3")

        self.fire_sounds = arcade.load_sound("assets/sounds/fire.wav")

        self.DdongGo = arcade.Sprite(
            path_or_texture="assets/images/game/DdongGo.png",
            center_x = self.window.width / 2,
            center_y = -100,
            scale = 0.15
        )

        self.heart_sheet = arcade.load_spritesheet("assets/images/game/heart.png")
        self.heart_texture = self.heart_sheet.get_texture_grid(size=(400, 400), columns=2, count=3)

        poop_body_sheet = arcade.load_spritesheet("assets/images/poop/body.png")
        poop_body_frames = poop_body_sheet.get_texture_grid(size=(1120, 720), columns=2, count=8)
        
        poop_arm_sheet = arcade.load_spritesheet("assets/images/poop/arm.png")
        self.poop_arm_frames = poop_arm_sheet.get_texture_grid(size=(1120, 720), columns=2, count=5)

        poop_boss_scale = 0.5

        self.poop_body = Poop_boss(
            poop_body_frames,
            scale=poop_boss_scale
        )
        self.poop_body.position = (
            self.window.width / 2, 650
        )

        self.arm_index = 0

        self.poop_arm = arcade.Sprite(
            self.poop_arm_frames[self.arm_index],
            scale=poop_boss_scale
        )
        self.poop_arm.position = self.poop_body.position

        self.heart_index = 0

        self.heart = arcade.Sprite(
            self.heart_texture[self.heart_index],
        )
        self.heart_position = [
            (100, 400),
            (200, 400),
            (300, 400),
            (100, 300),
            (200, 300)
        ]

        self.DdongGo_list = arcade.SpriteList()
        self.DdongGo_list.append(self.DdongGo)

        self.poop_body.alpha = 0
        self.poop_arm.alpha = 0

        self.poop_boss_list = arcade.SpriteList()
        self.poop_boss_list.append(self.poop_body)
        self.poop_boss_list.append(self.poop_arm)

        self.heart_list = arcade.SpriteList()
        for x, y in self.heart_position:
            heart = arcade.Sprite(
                self.heart_texture[self.heart_index],
                scale=0.3
            )
            heart.position = (x, y)
            self.heart_list.append(heart)

    def change_bg(self):
        self.lobby_true = False

    def arm_form(self, index):
        self.arm_index = index
        self.poop_arm.texture = self.poop_arm_frames[index]

    def box_appear(self):
        self.box_true = True
        self.heart_true = True

        self.box_fade.start()
        self.heart_fade.start()

    def run_game(self):
        from game import Game
        self.window.show_view(Game())


    def on_draw(self):
        self.clear()

        self.background_color = (10, 11, 18)

        if self.lobby_true:
            arcade.draw_texture_rect(
                self.lobby_images,
                arcade.XYWH(
                    self.window.width / 2,
                    self.window.height / 2,
                    self.window.width,
                    self.window.height
                )
            )

        if self.box_true:
            arcade.draw_rect_outline(
                arcade.XYWH(
                    self.window.width / 2,
                    300,
                    width=700,
                    height=400
                ),
                color = (255, 255, 255, self.box_fade.alpha
                ),
                border_width = 5
            )

        if self.heart_true:
            for heart in self.heart_list:
                heart.alpha = self.heart_fade.alpha

            self.heart_list.draw()

        if self.elapsed_time >= 3:
            self.poop_body.alpha = self.poop_fade.alpha
            self.poop_arm.alpha = self.poop_fade.alpha
            self.poop_boss_list.draw()
        
        self.DdongGo_list.draw()

    def on_update(self, delta_time):
        self.elapsed_time += delta_time

        self.box_fade.update(delta_time)
        self.heart_fade.update(delta_time)
        self.poop_fade.update(delta_time)

        for event in self.event:
            if not event["done"] and self.elapsed_time >= event["time"]:
                event["action"]()
                event["done"] = True

        if self.DdongGo.center_y <= 300:
            self.DdongGo.center_y += 180 * delta_time

        self.poop_boss_list.update_animation(delta_time)

if __name__ == "__main__":
    window = arcade.Window(
        1280, 720,
        "poop!",
        fullscreen=True,
        resizable=False
    )
    window.show_view(StartAnima())
    arcade.run()