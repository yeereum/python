import random
import arcade


class BossDropPattern:
    def __init__(self, game):
        self.game = game

        self.state = "idle"
        self.timer = 0.0

        self.home_x = game.window.width / 2
        self.home_y = 650

        self.target_x = 0.0
        self.target_y = 0.0
        self.start_x = 0.0
        self.start_y = 0.0

        self.hide_speed = 420.0
        self.fall_duration = 0.65
        self.warning_duration = 1.0
        self.impact_duration = 0.45
        self.retreat_speed = 500.0

        self.warning_width = 140
        self.warning_height = 90
        self.warning_fill = (255, 65, 65, 75)
        self.warning_outline = (255, 90, 90, 210)

    def start(self):
        self.state = "hide"
        self.timer = 0.0

        self.game.poop_body.position = (self.home_x, self.home_y)
        self.game.poop_arm.position = (self.home_x, self.home_y)
        self.game.poop_body.alpha = 255
        self.game.poop_arm.alpha = 255

    def set_boss_position(self, x, y):
        self.game.poop_body.position = (x, y)
        self.game.poop_arm.position = (x, y)

    def update(self, delta_time):
        body = self.game.poop_body

        if self.state == "hide":
            self.set_boss_position(
                body.center_x,
                body.center_y + self.hide_speed * delta_time,
            )

            if body.bottom > self.game.window.height:
                self.target_x = self.game.player.center_x
                self.target_y = self.game.player.center_y
                self.state = "warning"
                self.timer = 0.0

        elif self.state == "warning":
            self.timer += delta_time

            if self.timer >= self.warning_duration:
                self.start_x = body.center_x
                self.start_y = body.center_y
                self.state = "fall"
                self.timer = 0.0

        elif self.state == "fall":
            self.timer += delta_time
            progress = min(self.timer / self.fall_duration, 1.0)

            x = self.start_x + (self.target_x - self.start_x) * progress
            y = self.start_y + (self.target_y - self.start_y) * progress
            self.set_boss_position(x, y)

            if progress >= 1.0:
                self.check_hit()
                self.state = "impact"
                self.timer = 0.0

        elif self.state == "impact":
            self.timer += delta_time

            if self.timer >= self.impact_duration:
                self.state = "retreat"

        elif self.state == "retreat":
            self.set_boss_position(
                body.center_x,
                body.center_y + self.retreat_speed * delta_time,
            )

            if body.bottom > self.game.window.height:
                self.game.poop_body.position = (self.home_x, self.home_y)
                self.game.poop_arm.position = (self.home_x, self.home_y)
                self.game.poop_body.alpha = 0
                self.game.poop_arm.alpha = 0
                self.state = "finished"
                return True

        return False

    def check_hit(self):
        player = self.game.player

        target_left = self.target_x - self.warning_width / 2
        target_right = self.target_x + self.warning_width / 2
        target_bottom = self.target_y - self.warning_height / 2
        target_top = self.target_y + self.warning_height / 2

        overlaps = (
            player.right > target_left
            and player.left < target_right
            and player.top > target_bottom
            and player.bottom < target_top
        )

        if overlaps:
            self.game.damage()

    def draw(self):
        if self.state != "warning":
            return

        warning_rect = arcade.XYWH(
            self.target_x,
            self.target_y,
            self.warning_width,
            self.warning_height,
        )

        arcade.draw_rect_filled(
            warning_rect,
            self.warning_fill,
        )
        arcade.draw_rect_outline(
            warning_rect,
            self.warning_outline,
            border_width=3,
        )


class Boss_pattern:
    def __init__(self, game):
        self.game = game
        self.patterns = [
            BossDropPattern(game),
        ]
        self.current_pattern = None
        self.cooldown = 1.0

    def update(self, delta_time):
        if self.current_pattern is None:
            self.cooldown -= delta_time

            if self.cooldown <= 0 and self.patterns:
                self.current_pattern = random.choice(self.patterns)
                self.current_pattern.start()

        if self.current_pattern is not None:
            finished = self.current_pattern.update(delta_time)

            if finished:
                self.current_pattern = None
                self.cooldown = 1.0

    def draw(self):
        if self.current_pattern is not None:
            self.current_pattern.draw()