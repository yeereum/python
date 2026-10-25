import arcade
import random

class Fadein:
    def __init__(self, duration=1):
        self.duration = max(duration, 0.001)
        self.elapsed_time = 0
        self.active = False
        self.started = False

    def start(self):
        self.elapsed_time = 0
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

        progress = min(self.elapsed_time / self.duration, 1)
        return int(255 * progress)

class Fadeout:
    def __init__(self, duration=1):
        self.duration = max(duration, 0.001)
        self.elapsed_time = 0
        self.active = False
        self.started = False

    def start(self):
        self.elapsed_time = 0
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
            return 255

        progress = min(self.elapsed_time / self.duration, 1)
        return int(255 * (1 - progress))

class Normal_pattern:
    class Kwangkwang:
        def __init__(self, game):
            self.game = game

            self.state = "normal"
            self.timer = 0

            self.home_x = self.game.window.width / 2
            self.home_y = 650

            self.target_x = 0
            self.target_y = 0
            self.start_x = 0
            self.start_y = 0

            self.stack = 0

            self.hide_speed = 450
            self.fall_duration = 0.16
            self.warning_duration = 0.4
            self.impact_duration = 0.2
            self.retreat_speed = 800

            self.fadeout = Fadeout(0.3)
            self.fadein = Fadein(0.6)

            self.warning_width = 300
            self.warning_height = 300
            self.warning_fill = (255, 65, 65, 75)
            self.warning_outline = (255, 90, 90, 210)

            self.landing_elapsed = 0
            self.landing_wait_time = 0.4

        def start(self):
            self.state = "hide"
            self.timer = 0
            self.stack = 0
            self.landing_elapsed = 0
            self.set_boss_alpha(255)
            self.set_boss_position(self.home_x, self.home_y)

        def set_boss_position(self, x, y):
            self.game.poop_body.position = (x, y)
            self.game.poop_arm.position = (x, y)

        def set_boss_alpha(self, alpha):
            self.game.poop_body.alpha = alpha
            self.game.poop_arm.alpha = alpha

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

                    self.set_boss_position(
                        self.target_x,
                        body.center_y,
                    )

                    self.state = "warning"
                    self.timer = 0

            elif self.state == "warning":
                self.timer += delta_time

                if self.timer >= self.warning_duration:
                    self.start_x = body.center_x
                    self.start_y = body.center_y
                    self.state = "fall"
                    self.timer = 0

            elif self.state == "fall":
                self.timer += delta_time
                progress = min(self.timer / self.fall_duration, 1)

                x = self.start_x + (
                    self.target_x - self.start_x
                ) * progress

                y = self.start_y + (
                    self.target_y - self.start_y
                ) * progress

                self.set_boss_position(x, y)

                if progress >= 1:
                    self.check_hit()
                    self.stack += 1
                    self.timer = 0

                    if self.stack >= 3:
                        self.stack = 0
                        self.landing_elapsed = 0
                        self.state = "landing_wait"
                        arcade.play_sound(self.game.rock_break_sounds, speed=1.75)
                    else:
                        self.state = "impact"
                        arcade.play_sound(self.game.rock_break_sounds, speed=1.75)

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
                    self.state = "hide"

            elif self.state == "fadeout":
                self.fadeout.update(delta_time)
                self.set_boss_alpha(self.fadeout.alpha)

                if not self.fadeout.active:
                    self.set_boss_position(
                        self.home_x,
                        self.home_y,
                    )

                    self.fadein.start()
                    self.state = "fadein"

            elif self.state == "fadein":
                self.fadein.update(delta_time)
                self.set_boss_alpha(self.fadein.alpha)

                if not self.fadein.active:
                    self.set_boss_alpha(255)
                    self.state = "normal"
                    return True

            if self.state == "landing_wait":
                self.landing_elapsed += delta_time

                if self.landing_elapsed >= self.landing_wait_time:
                    self.fadeout.start()
                    self.state = "fadeout"

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
                self.game.hurt()

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

    class Memory_battle:
        def __init__(self, game):
            self.game = game

            self.state = "normal"
            self.timer = 0

            self.fadeout = Fadeout(0.3)

            self.symbols = ["○", "△", "□", "★"]
            self.sequence = []
            self.sequence_index = 0

            self.box_fadein_duration = 0.5

            self.show_fadein_duration = 0.25
            self.show_gap = 0.2

            self.attack_fadein_duration = 0.5
            self.attack_gap = 0.3
            self.attack_fadeout_duration = 0.2

            self.final_attack_wait_duration = 0.5
            self.final_attack_fadein_duration = 0.5

            self.active_zone = None
            self.hit_checked = False

            self.box_center_x = None
            self.box_center_y = None
            self.box_width = None
            self.box_height = None
            self.box_border_width = None

            self.zones = []
            self.final_zone = None

        def create_zones(self):
            left = (
                self.box_center_x
                - self.box_width / 2
                + self.box_border_width
            )
            right = (
                self.box_center_x
                + self.box_width / 2
                - self.box_border_width
            )
            bottom = (
                self.box_center_y
                - self.box_height / 2
                + self.box_border_width
            )
            top = (
                self.box_center_y
                + self.box_height / 2
                - self.box_border_width
            )

            middle_x = (left + right) / 2
            middle_y = (bottom + top) / 2

            zone_width = (right - left) / 2
            zone_height = (top - bottom) / 2

            self.zones = [
                arcade.XYWH(
                    (left + middle_x) / 2,
                    (middle_y + top) / 2,
                    zone_width,
                    zone_height,
                ),
                arcade.XYWH(
                    (middle_x + right) / 2,
                    (middle_y + top) / 2,
                    zone_width,
                    zone_height,
                ),
                arcade.XYWH(
                    (left + middle_x) / 2,
                    (bottom + middle_y) / 2,
                    zone_width,
                    zone_height,
                ),
                arcade.XYWH(
                    (middle_x + right) / 2,
                    (bottom + middle_y) / 2,
                    zone_width,
                    zone_height,
                ),
            ]

            self.final_zone = arcade.XYWH(
                middle_x,
                middle_y,
                top - bottom + 50,
                top - bottom,
            )

        def start(self):
            self.box_center_x = self.game.box_center_x
            self.box_center_y = self.game.box_center_y
            self.box_width = self.game.box_width
            self.box_height = self.game.box_height
            self.box_border_width = self.game.box_border_width

            self.create_zones()

            self.state = "reveal"
            self.timer = 0

            self.sequence = [0, 1, 2, 3]
            random.shuffle(self.sequence)
            self.sequence.append(self.sequence[0])

            self.sequence_index = 0
            self.active_zone = None
            self.hit_checked = False

        def update(self, delta_time):
            if self.state == "normal":
                return False

            self.timer += delta_time

            if self.state == "reveal":
                if self.timer >= self.box_fadein_duration:
                    self.state = "show"
                    self.timer = 0
                    self.sequence_index = 0
                    self.active_zone = None

            elif self.state == "show":
                if self.sequence_index >= len(self.sequence):
                    self.state = "final_attack_wait"
                    self.timer = 0
                    self.sequence_index = 0
                    self.active_zone = None
                    return False

                cycle_time = self.show_fadein_duration + self.show_gap
                self.active_zone = self.sequence[self.sequence_index]

                if self.timer >= cycle_time:
                    self.timer -= cycle_time
                    self.sequence_index += 1

                    if self.sequence_index >= len(self.sequence):
                        self.active_zone = None

            elif self.state == "final_attack_wait":
                if self.timer >= self.final_attack_wait_duration:
                    self.state = "attack_wait"
                    self.timer = 0
                    self.sequence_index = 0
                    self.active_zone = None

            elif self.state == "attack_wait":
                if self.timer >= 0.5:
                    self.state = "attack"
                    self.timer = 0
                    self.sequence_index = 0
                    self.active_zone = self.sequence[0]
                    self.hit_checked = False

            elif self.state == "attack":
                self.active_zone = self.sequence[self.sequence_index]
                self.game.arm_form(1)

                if not self.hit_checked:
                    arcade.play_sound(self.game.rock_break_sounds, speed=1.75)
                    self.check_hit(self.active_zone)
                    self.hit_checked = True

                if self.timer >= self.attack_fadein_duration:
                    self.timer = 0
                    self.sequence_index += 1
                    self.hit_checked = False

                    if self.sequence_index >= len(self.sequence):
                        self.state = "final_attack"
                        self.timer = 0
                        self.active_zone = None
                    else:
                        self.active_zone = self.sequence[self.sequence_index]

            elif self.state == "final_attack":
                self.game.arm_form(1)

                if not self.hit_checked:
                    arcade.play_sound(self.game.rock_break_sounds, speed=1.75)
                    self.check_final_hit()
                    self.hit_checked = True

                if self.timer >= self.final_attack_fadein_duration:
                    self.timer = 0
                    self.active_zone = None
                    self.fadeout.start()
                    self.state = "fadeout"

            elif self.state == "fadeout":
                self.fadeout.update(delta_time)

                if not self.fadeout.active:
                    self.state = "normal"
                    self.active_zone = None
                    return True

            return False

        def check_hit(self, zone_index):
            player = self.game.player
            zone = self.zones[zone_index]

            overlaps = (
                player.right > zone.left
                and player.left < zone.right
                and player.top > zone.bottom
                and player.bottom < zone.top
            )

            if overlaps:
                self.game.hurt()

        def check_final_hit(self):
            player = self.game.player
            zone = self.final_zone

            overlaps = (
                player.right > zone.left
                and player.left < zone.right
                and player.top > zone.bottom
                and player.bottom < zone.top
            )

            if overlaps:
                self.game.hurt()

        def draw(self):
            if self.state == "normal":
                return

            if self.state == "reveal":
                reveal_alpha = int(
                    255 * min(self.timer / self.box_fadein_duration, 1)
                )
            else:
                reveal_alpha = 255

            left = (
                self.box_center_x
                - self.box_width / 2
                + self.box_border_width
            )
            right = (
                self.box_center_x
                + self.box_width / 2
                - self.box_border_width
            )
            bottom = (
                self.box_center_y
                - self.box_height / 2
                + self.box_border_width
            )
            top = (
                self.box_center_y
                + self.box_height / 2
                - self.box_border_width
            )

            middle_x = (left + right) / 2
            middle_y = (bottom + top) / 2

            line_color = (255, 255, 255, reveal_alpha)

            arcade.draw_line(
                middle_x, bottom,
                middle_x, top,
                line_color, 3,
            )
            arcade.draw_line(
                left, middle_y,
                right, middle_y,
                line_color, 3,
            )

            for i, zone in enumerate(self.zones):
                arcade.draw_text(
                    self.symbols[i],
                    zone.center_x,
                    zone.center_y,
                    (255, 255, 255, reveal_alpha),
                    font_size=30,
                    anchor_x="center",
                    anchor_y="center",
                )

            if self.state == "show" and self.active_zone is not None:
                zone = self.zones[self.active_zone]

                arcade.draw_rect_filled(
                    zone,
                    (255, 230, 100, 100),
                )

            elif self.state == "final_attack_wait":
                arcade.draw_rect_filled(
                    self.final_zone,
                    (255, 230, 100, 100),
                )

            elif self.state == "attack" and self.active_zone is not None:
                if self.timer < self.attack_fadeout_duration:
                    attack_alpha = int(
                        160 * self.timer / self.attack_fadeout_duration
                    )
                elif self.timer > (
                    self.attack_fadein_duration - self.attack_fadeout_duration
                ):
                    attack_alpha = int(
                        160 * max(
                            0,
                            (
                                self.attack_fadein_duration - self.timer
                            ) / self.attack_fadeout_duration,
                        )
                    )
                else:
                    attack_alpha = 160

                zone = self.zones[self.active_zone]

                arcade.draw_rect_filled(
                    zone,
                    (255, 50, 50, attack_alpha),
                )

            elif self.state == "final_attack":
                if self.timer < self.attack_fadeout_duration:
                    attack_alpha = int(
                        160 * self.timer / self.attack_fadeout_duration
                    )
                elif self.timer > (
                    self.final_attack_fadein_duration - self.attack_fadeout_duration
                ):
                    attack_alpha = int(
                        160 * max(
                            0,
                            (
                                self.final_attack_fadein_duration - self.timer
                            ) / self.attack_fadeout_duration,
                        )
                    )
                else:
                    attack_alpha = 160

                arcade.draw_rect_filled(
                    self.final_zone,
                    (255, 50, 50, attack_alpha),
                )

class Enhance_pattern:
    class Enhance_drop:
        pass

class Boss_pattern:
    def __init__(self, game):
        self.game = game

        self.normal_pattern = [
            Normal_pattern.Kwangkwang(game),
            Normal_pattern.Memory_battle(game)
        ]
        self.enhance_pattern = [
        ]

        self.current_pattern = None
        self.pattern_stack = 0
        self.cooldown = 1

    def update(self, delta_time):
        if self.current_pattern is None:
            self.cooldown -= delta_time

            if self.game.boss_hp / self.game.boss_max_hp > 0.3:
                if self.cooldown <= 0 and self.normal_pattern:
                    self.current_pattern = random.choice(
                        self.normal_pattern
                    )
                    self.current_pattern.start()
                    self.game.no_hurt_true = True


            elif self.game.boss_hp / self.game.boss_max_hp <= 0.3:
                if self.cooldown <= 0 and self.enhance_pattern:
                    self.current_pattern = random.choice(
                        self.enhance_pattern
                    )
                    self.current_pattern.start()
                    self.game.no_hurt_true = True

        if self.current_pattern is not None:
            finished = self.current_pattern.update(delta_time)

            if finished:
                self.current_pattern = None
                self.cooldown = 1
                self.game.arm_form(0)
                self.pattern_stack += 1
                if self.game.spare_heart is None and self.game.no_hurt_true:
                    self.game.no_hurt_combo += 1

    def draw(self):
        if self.current_pattern is not None:
            self.current_pattern.draw()