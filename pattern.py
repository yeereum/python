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

class Boss_attack:
    def __init__(self, game):
        self.game = game

        self.state = "normal"
        self.timer = 0
        self.duration = 5.0
        self.move_speed = 500
        self.scale = 0.65

        self.fadein = Fadein(0.6)

        self.home_x = game.window.width / 2
        self.home_y = 650

        self.target_x = 0
        self.target_y = 0

        self.game.boss_attack_active = False

    def set_boss_position(self, x, y):
        self.game.poop_body.position = (x, y)
        self.game.poop_arm.position = (x, y)

    def set_boss_alpha(self, alpha):
        self.game.poop_body.alpha = alpha
        self.game.poop_arm.alpha = alpha

    def set_boss_scale(self, ratio):
        body_scale = self.original_body_scale
        arm_scale = self.original_arm_scale

        if isinstance(body_scale, tuple):
            self.game.poop_body.scale = tuple(
                value * ratio for value in body_scale
            )
        else:
            self.game.poop_body.scale = body_scale * ratio

        if isinstance(arm_scale, tuple):
            self.game.poop_arm.scale = tuple(
                value * ratio for value in arm_scale
            )
        else:
            self.game.poop_arm.scale = arm_scale * ratio

    def choose_target(self):
        body = self.game.poop_body

        left = (
            self.game.box_center_x
            - self.game.box_width / 2
            + body.width / 2
        )
        right = (
            self.game.box_center_x
            + self.game.box_width / 2
            - body.width / 2
        )
        bottom = (
            self.game.box_center_y
            - self.game.box_height / 2
            + body.height / 2
        )
        top = (
            self.game.box_center_y
            + self.game.box_height / 2
            - body.height / 2
        )

        self.target_x = random.uniform(left, right)
        self.target_y = random.uniform(bottom, top)

    def start(self):
        self.original_body_scale = self.game.poop_body.scale
        self.original_arm_scale = self.game.poop_arm.scale
        self.state = "enter"
        self.timer = 0
        self.game.boss_attack_active = False

        self.set_boss_scale(self.scale)
        self.set_boss_position(
            self.game.box_center_x,
            self.game.box_center_y,
        )
        self.set_boss_alpha(0)

        self.fadein.start()

    def update(self, delta_time):
        body = self.game.poop_body

        if self.state == "enter":
            self.fadein.update(delta_time)
            self.set_boss_alpha(self.fadein.alpha)

            if not self.fadein.active:
                self.set_boss_alpha(255)
                self.game.boss_attack_active = True
                self.state = "run"
                self.timer = 0
                self.choose_target()

        elif self.state == "run":
            self.timer += delta_time

            dx = self.target_x - body.center_x
            dy = self.target_y - body.center_y
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance <= self.move_speed * delta_time or distance == 0:
                self.set_boss_position(
                    self.target_x,
                    self.target_y,
                )
                self.choose_target()
            else:
                move_x = dx / distance * self.move_speed * delta_time
                move_y = dy / distance * self.move_speed * delta_time

                self.set_boss_position(
                    body.center_x + move_x,
                    body.center_y + move_y,
                )

            if self.timer >= self.duration:
                self.game.boss_attack_active = False

                self.set_boss_position(
                    self.home_x,
                    self.home_y,
                )
                self.set_boss_scale(1.0)
                self.set_boss_alpha(0)

                self.fadein.start()
                self.state = "return"

        elif self.state == "return":
            self.fadein.update(delta_time)
            self.set_boss_alpha(self.fadein.alpha)

            if not self.fadein.active:
                self.set_boss_alpha(255)
                self.state = "normal"
                return True

        return False

    def draw(self):
        pass

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

            self.attack_wait_duration = 0.5
            self.attack_fadein_duration = 0.5
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

            self.final_zone = [
                arcade.XYWH(
                    middle_x,
                    middle_y,
                    top - bottom + 70,
                    top - bottom,
                ),
                arcade.XYWH(
                    right - (self.box_width - (top - bottom + 70)) / 4 + self.box_border_width,
                    middle_y,
                    (self.box_width - (top - bottom + 70)) / 2,
                    top - bottom - 200
                ),
                arcade.XYWH(
                    left + (self.box_width - (top - bottom + 70)) / 4 - self.box_border_width,
                    middle_y,
                    (self.box_width - (top - bottom + 70)) / 2,
                    top - bottom - 200
                )
            ]

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
                if self.timer >= self.attack_wait_duration:
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

            for zone in self.final_zone:
                overlaps = (
                    player.right > zone.left
                    and player.left < zone.right
                    and player.top > zone.bottom
                    and player.bottom < zone.top
                )

                if overlaps:
                    self.game.hurt()
                    return

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
                for zone in self.final_zone:
                    arcade.draw_rect_filled(
                        zone,
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

                for zone in self.final_zone:
                    arcade.draw_rect_filled(
                        zone,
                        (255, 50, 50, attack_alpha),
                    )

    class Field_attack:
        def __init__(self, game):
            self.game = game

            self.state = "normal"
            self.timer = 0

            self.minipoop_hp = 20
            self.minipoop = []
            self.protected = False

            self.warning_duration = 5.5
            self.warning_fadein_duration = 1
            self.minipoop_appear_time = 2
            self.attack_duration = 0.8
            self.end_duration = 1

            self.warning_fill = (255, 65, 65, 75)
            self.warning_outline = (255, 90, 90, 210)

            self.minipoop_created = False
            self.attack_done = False

        def start(self):
            self.state = "warning"
            self.timer = 0
            self.protected = False
            self.minipoop = []
            self.minipoop_created = False
            self.attack_done = False
            self.game.arm_form(1)

        def create_minipoop(self):
            left = (
                self.game.box_center_x
                - self.game.box_width / 2
                + 70
            )
            right = (
                self.game.box_center_x
                + self.game.box_width / 2
                - 70
            )
            bottom = (
                self.game.box_center_y
                - self.game.box_height / 2
                + 70
            )
            top = (
                self.game.box_center_y
                + self.game.box_height / 2
                - 70
            )

            corners = [
                (left, bottom),
                (left, top),
                (right, bottom),
                (right, top),
            ]
            random.shuffle(corners)

            for x, y in corners[:3]:
                sprite = arcade.Sprite(
                    self.game.minipoop.texture,
                    scale=self.game.minipoop.scale,
                )
                sprite.position = (x, y)

                self.minipoop.append({
                    "sprite": sprite,
                    "hp": self.minipoop_hp,
                })

            self.minipoop_created = True

        def hit_object(self):
            if self.state != "warning":
                return False

            if not self.minipoop_created:
                return False

            punch = self.game.punch

            for minipoop in self.minipoop:
                if minipoop["hp"] <= 0:
                    continue

                sprite = minipoop["sprite"]

                overlaps = (
                    punch.right > sprite.left
                    and punch.left < sprite.right
                    and punch.top > sprite.bottom
                    and punch.bottom < sprite.top
                )

                if overlaps:
                    minipoop["hp"] = max(
                        0,
                        minipoop["hp"] - self.game.attack_damage,
                    )
                    arcade.play_sound(self.game.attack_sounds)
                    return True

            return False

        def update(self, delta_time):
            if self.state == "normal":
                return False

            self.timer += delta_time

            if self.state == "warning":
                if (
                    not self.minipoop_created
                    and self.timer >= self.minipoop_appear_time
                ):
                    self.create_minipoop()

                if (
                    self.minipoop_created
                    and all(minipoop["hp"] <= 0 for minipoop in self.minipoop)
                ):
                    self.protected = True

                if self.timer >= self.warning_duration:
                    self.protected = (
                        self.minipoop_created
                        and all(minipoop["hp"] <= 0 for minipoop in self.minipoop)
                    )
                    arcade.play_sound(self.game.rock_break_sounds, speed=1.75)
                    self.state = "attack"
                    self.timer = 0

                    if not self.protected:
                        self.game.hurt()

            elif self.state == "attack":
                if self.timer >= self.attack_duration:
                    self.state = "end"
                    self.timer = 0

            elif self.state == "end":
                if self.timer >= self.end_duration:
                    self.minipoop.clear()
                    self.protected = False
                    self.state = "normal"
                    return True

            return False

        def draw(self):
            if self.state == "normal":
                return

            if self.state == "warning":
                alpha = int(
                    255 * min(
                        self.timer / self.warning_fadein_duration,
                        1,
                    )
                )

                arcade.draw_rect_filled(
                    arcade.XYWH(
                        self.game.box_center_x,
                        self.game.box_center_y,
                        self.game.box_width,
                        self.game.box_height,
                    ),
                    (255, 65, 65, int(75 * alpha / 255)),
                )

                arcade.draw_rect_outline(
                    arcade.XYWH(
                        self.game.box_center_x,
                        self.game.box_center_y,
                        self.game.box_width,
                        self.game.box_height,
                    ),
                    (
                        self.warning_outline[0],
                        self.warning_outline[1],
                        self.warning_outline[2],
                        int(self.warning_outline[3] * alpha / 255),
                    ),
                    border_width=3,
                )

            elif self.state == "attack":
                arcade.draw_rect_filled(
                    arcade.XYWH(
                        self.game.box_center_x,
                        self.game.box_center_y,
                        self.game.box_width,
                        self.game.box_height,
                    ),
                    (255, 40, 40, 150),
                )

            if self.protected:
                arcade.draw_circle_filled(
                    self.game.player.center_x,
                    self.game.player.center_y,
                    max(self.game.player.width, self.game.player.height) * 0.8,
                    (80, 170, 255, 90),
                )

            fade_alpha = 255

            if self.state == "end":
                fade_alpha = int(
                    255 * max(
                        0,
                        1 - self.timer / self.end_duration,
                    )
                )

            for minipoop in self.minipoop:
                if minipoop["hp"] <= 0:
                    continue

                sprite_list = arcade.SpriteList()
                sprite_list.append(minipoop["sprite"])
                sprite_list.draw()

                sprite = minipoop["sprite"]
                sprite.alpha = fade_alpha

                hp_ratio = minipoop["hp"] / self.minipoop_hp

                arcade.draw_rect_filled(
                    arcade.XYWH(
                        minipoop["sprite"].center_x,
                        minipoop["sprite"].bottom - 8,
                        self.game.minipoop.width,
                        5,
                    ),
                    (70, 30, 30, fade_alpha),
                )

                arcade.draw_rect_filled(
                    arcade.XYWH(
                        minipoop["sprite"].left + self.game.minipoop.width * (hp_ratio / 2),
                        minipoop["sprite"].bottom - 8,
                        self.game.minipoop.width * hp_ratio,
                        5,
                    ),
                    (80, 230, 130, fade_alpha),
                )

class Enhance_pattern:
    class Enhance_kwangkwang:
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

            self.boss_size = 0.7

            self.hide_speed = 450
            self.fall_duration = 0.16
            self.warning_duration = 0.4
            self.impact_duration = 0.2
            self.retreat_speed = 800

            self.dash_warning_duration = 0.35
            self.dash_distance = 500
            self.dash_duration = 0.2
            self.dash_start_x = 0
            self.dash_start_y = 0
            self.dash_target_x = 0
            self.dash_target_y = 0
            self.dash_hit = False

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
            self.dash_hit = False
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
                        body.center_y
                    )

                    self.game.poop_body.scale = self.game.boss_scale * self.boss_size
                    self.game.poop_arm.scale = self.game.boss_scale * self.boss_size
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

                    arcade.play_sound(self.game.rock_break_sounds, speed=1.75)
                    self.state = "impact"

            elif self.state == "impact":
                self.timer += delta_time

                if self.timer >= self.impact_duration:
                    player = self.game.player

                    self.dash_start_x = body.center_x
                    self.dash_start_y = body.center_y

                    dx = player.center_x - body.center_x
                    dy = player.center_y - body.center_y
                    distance = max((dx ** 2 + dy ** 2) ** 0.5, 1)

                    self.dash_target_x = (
                        body.center_x
                        + dx / distance * self.dash_distance
                    )
                    self.dash_target_y = (
                        body.center_y
                        + dy / distance * self.dash_distance
                    )

                    self.dash_hit = False
                    self.timer = 0
                    self.state = "dash_warning"

            elif self.state == "dash_warning":
                self.timer += delta_time

                if self.timer >= self.dash_warning_duration:
                    self.timer = 0
                    self.state = "dash"

                    arcade.play_sound(self.game.rock_break_sounds, speed=1.75)

            elif self.state == "dash":
                self.timer += delta_time
                progress = min(self.timer / self.dash_duration, 1)

                x = self.dash_start_x + (
                    self.dash_target_x - self.dash_start_x
                ) * progress

                y = self.dash_start_y + (
                    self.dash_target_y - self.dash_start_y
                ) * progress

                self.set_boss_position(x, y)

                if not self.dash_hit:
                    if arcade.check_for_collision(
                        self.game.poop_body,
                        self.game.player,
                    ):
                        self.game.hurt()
                        self.dash_hit = True

                if progress >= 1:
                    self.timer = 0

                    if self.stack >= 3:
                        self.landing_elapsed = 0
                        self.state = "landing_wait"
                    else:
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
            if self.state == "warning":
                warning_rect = arcade.XYWH(
                    self.target_x,
                    self.target_y,
                    self.warning_width,
                    self.warning_height
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

            elif self.state == "dash_warning":
                dx = self.dash_target_x - self.dash_start_x
                dy = self.dash_target_y - self.dash_start_y
                distance = (dx ** 2 + dy ** 2) ** 0.5

                center_x = (self.dash_start_x + self.dash_target_x) / 2
                center_y = (self.dash_start_y + self.dash_target_y) / 2

                angle = arcade.math.get_angle_degrees(
                    self.dash_start_x,
                    self.dash_start_y,
                    self.dash_target_x,
                    self.dash_target_y,
                )

                warning_rect = arcade.XYWH(
                    center_x,
                    center_y,
                    distance,
                    self.game.poop_body.width * self.game.boss_scale
                )

                arcade.draw_rect_filled(
                    warning_rect,
                    self.warning_fill,
                    tilt_angle=angle,
                )

                arcade.draw_rect_outline(
                    warning_rect,
                    self.warning_outline,
                    border_width=3,
                    tilt_angle=angle,
                )

    class Enhance_memory_battle:
        def __init__(self, game):
            self.game = game

            self.state = "normal"
            self.timer = 0

            self.fadeout = Fadeout(0.3)

            self.symbols = ["○", "△", "□", "★"]
            self.steps = []
            self.sequence_index = 0

            self.box_fadein_duration = 0.5

            self.show_fadein_duration = 0.35
            self.show_gap = 0.5

            self.attack_wait_duration = 0.5
            self.attack_fadein_duration = 0.5
            self.attack_gap = 0.25
            self.attack_fadeout_duration = 0.2

            self.active_step = None
            self.hit_checked = False

            self.box_center_x = None
            self.box_center_y = None
            self.box_width = None
            self.box_height = None
            self.box_border_width = None

            self.left = None
            self.right = None
            self.bottom = None
            self.top = None

            self.zones = []
            self.final_zone = []
            self.outer_zone = []

        def create_zones(self):
            self.left = (
                self.box_center_x
                - self.box_width / 2
                + self.box_border_width
            )
            self.right = (
                self.box_center_x
                + self.box_width / 2
                - self.box_border_width
            )
            self.bottom = (
                self.box_center_y
                - self.box_height / 2
                + self.box_border_width
            )
            self.top = (
                self.box_center_y
                + self.box_height / 2
                - self.box_border_width
            )

            middle_x = (self.left + self.right) / 2
            middle_y = (self.bottom + self.top) / 2

            zone_width = (self.right - self.left) / 2
            zone_height = (self.top - self.bottom) / 2

            self.zones = [
                arcade.XYWH(
                    (self.left + middle_x) / 2,
                    (middle_y + self.top) / 2,
                    zone_width,
                    zone_height,
                ),
                arcade.XYWH(
                    (middle_x + self.right) / 2,
                    (middle_y + self.top) / 2,
                    zone_width,
                    zone_height,
                ),
                arcade.XYWH(
                    (self.left + middle_x) / 2,
                    (self.bottom + middle_y) / 2,
                    zone_width,
                    zone_height,
                ),
                arcade.XYWH(
                    (middle_x + self.right) / 2,
                    (self.bottom + middle_y) / 2,
                    zone_width,
                    zone_height,
                ),
            ]

            full_height = self.top - self.bottom
            center_width = full_height + 70
            side_width = (self.box_width - center_width) / 2
            right_x = (
                self.right
                - side_width / 2
                + self.box_border_width
            )
            left_x = (
                self.left
                + side_width / 2
                - self.box_border_width
            )

            self.final_zone = [
                arcade.XYWH(
                    middle_x,
                    middle_y,
                    center_width,
                    full_height,
                ),
                arcade.XYWH(
                    right_x,
                    middle_y,
                    side_width,
                    full_height - 200,
                ),
                arcade.XYWH(
                    left_x,
                    middle_y,
                    side_width,
                    full_height - 200,
                ),
            ]

            self.outer_zone = [
                arcade.XYWH(
                    right_x,
                    middle_y,
                    side_width,
                    full_height,
                ),
                arcade.XYWH(
                    left_x,
                    middle_y,
                    side_width,
                    full_height,
                ),
            ]

        def create_steps(self):
            zone_indexes = [0, 1, 2, 3]

            excluded = [random.choice(zone_indexes)]

            for _ in range(2):
                excluded.append(
                    random.choice(
                        [i for i in zone_indexes if i != excluded[-1]]
                    )
                )

            self.steps = [[self.zones[excluded[0]]]]

            for excluded_zone in excluded:
                self.steps.append(
                    [
                        self.zones[i]
                        for i in zone_indexes
                        if i != excluded_zone
                    ]
                )

            self.steps.append(list(self.final_zone))
            self.steps.append(list(self.outer_zone))

        def start(self):
            self.box_center_x = self.game.box_center_x
            self.box_center_y = self.game.box_center_y
            self.box_width = self.game.box_width
            self.box_height = self.game.box_height
            self.box_border_width = self.game.box_border_width

            self.create_zones()
            self.create_steps()

            self.state = "reveal"
            self.timer = 0

            self.sequence_index = 0
            self.active_step = None
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
                    self.active_step = None

            elif self.state == "show":
                if self.sequence_index >= len(self.steps):
                    self.state = "attack_wait"
                    self.timer = 0
                    self.sequence_index = 0
                    self.active_step = None
                    return False

                cycle_time = self.show_fadein_duration + self.show_gap

                if self.timer < self.show_fadein_duration:
                    self.active_step = self.sequence_index
                else:
                    self.active_step = None

                if self.timer >= cycle_time:
                    self.timer -= cycle_time
                    self.sequence_index += 1
                    self.active_step = None

            elif self.state == "attack_wait":
                if self.timer >= self.attack_wait_duration:
                    self.state = "attack"
                    self.timer = 0
                    self.sequence_index = 0
                    self.active_step = None
                    self.hit_checked = False

            elif self.state == "attack":
                self.game.arm_form(1)

                if not self.hit_checked:
                    arcade.play_sound(self.game.rock_break_sounds, speed=1.75)
                    self.check_hit(self.steps[self.sequence_index])
                    self.hit_checked = True

                if self.timer < self.attack_fadein_duration:
                    self.active_step = self.sequence_index
                else:
                    self.active_step = None

                cycle_time = (
                    self.attack_fadein_duration
                    + self.attack_gap
                )

                if self.timer >= cycle_time:
                    self.timer -= cycle_time
                    self.sequence_index += 1
                    self.hit_checked = False
                    self.active_step = None

                    if self.sequence_index >= len(self.steps):
                        self.timer = 0
                        self.fadeout.start()
                        self.state = "fadeout"

            elif self.state == "fadeout":
                self.fadeout.update(delta_time)

                if not self.fadeout.active:
                    self.state = "normal"
                    self.active_step = None
                    return True

            return False

        def check_hit(self, zones):
            player = self.game.player

            for zone in zones:
                overlaps = (
                    player.right > zone.left
                    and player.left < zone.right
                    and player.top > zone.bottom
                    and player.bottom < zone.top
                )

                if overlaps:
                    self.game.hurt()
                    return

        def get_attack_alpha(self):
            if self.timer < self.attack_fadeout_duration:
                return int(
                    160 * self.timer / self.attack_fadeout_duration
                )

            if self.timer > (
                self.attack_fadein_duration
                - self.attack_fadeout_duration
            ):
                return int(
                    160 * max(
                        0,
                        (
                            self.attack_fadein_duration - self.timer
                        ) / self.attack_fadeout_duration,
                    )
                )

            return 160

        def draw(self):
            if self.state == "normal":
                return

            if self.state == "reveal":
                reveal_alpha = int(
                    255 * min(
                        self.timer / self.box_fadein_duration,
                        1,
                    )
                )
            elif self.state == "fadeout":
                reveal_alpha = self.fadeout.alpha
            else:
                reveal_alpha = 255

            middle_x = (self.left + self.right) / 2
            middle_y = (self.bottom + self.top) / 2

            line_color = (255, 255, 255, reveal_alpha)

            arcade.draw_line(
                middle_x, self.bottom,
                middle_x, self.top,
                line_color, 3,
            )
            arcade.draw_line(
                self.left, middle_y,
                self.right, middle_y,
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

            if self.active_step is None:
                return

            if self.state == "show":
                for zone in self.steps[self.active_step]:
                    arcade.draw_rect_filled(
                        zone,
                        (255, 230, 100, 100),
                    )

            elif self.state == "attack":
                attack_alpha = self.get_attack_alpha()

                for zone in self.steps[self.active_step]:
                    arcade.draw_rect_filled(
                        zone,
                        (255, 50, 50, attack_alpha),
                    )

    class Enhance_field_attack:
        def __init__(self, game):
            self.game = game

            self.state = "normal"
            self.timer = 0

            self.minipoop_hp = 40
            self.minipoop = []
            self.protected = False

            self.warning_duration = 6.5
            self.warning_fadein_duration = 1
            self.minipoop_appear_time = 2
            self.attack_duration = 0.8
            self.end_duration = 1

            self.warning_fill = (255, 65, 65, 75)
            self.warning_outline = (255, 90, 90, 210)

            self.minipoop_created = False
            self.attack_done = False

        def start(self):
            self.state = "warning"
            self.timer = 0
            self.protected = False
            self.minipoop = []
            self.minipoop_created = False
            self.attack_done = False
            self.game.arm_form(1)

        def create_minipoop(self):
            left = (
                self.game.box_center_x
                - self.game.box_width / 2
                + 70
            )
            right = (
                self.game.box_center_x
                + self.game.box_width / 2
                - 70
            )
            bottom = (
                self.game.box_center_y
                - self.game.box_height / 2
                + 70
            )
            top = (
                self.game.box_center_y
                + self.game.box_height / 2
                - 70
            )

            corners = [
                (left, bottom),
                (left, top),
                (right, bottom),
                (right, top),
            ]
            random.shuffle(corners)

            for x, y in corners[:3]:
                sprite = arcade.Sprite(
                    self.game.minipoop.texture,
                    scale=self.game.minipoop.scale,
                )
                sprite.position = (x, y)

                self.minipoop.append({
                    "sprite": sprite,
                    "hp": self.minipoop_hp,
                })

            self.minipoop_created = True

        def hit_object(self):
            if self.state != "warning":
                return False

            if not self.minipoop_created:
                return False

            punch = self.game.punch

            for minipoop in self.minipoop:
                if minipoop["hp"] <= 0:
                    continue

                sprite = minipoop["sprite"]

                overlaps = (
                    punch.right > sprite.left
                    and punch.left < sprite.right
                    and punch.top > sprite.bottom
                    and punch.bottom < sprite.top
                )

                if overlaps:
                    minipoop["hp"] = max(
                        0,
                        minipoop["hp"] - self.game.attack_damage,
                    )
                    arcade.play_sound(self.game.attack_sounds)
                    return True

            return False

        def update(self, delta_time):
            if self.state == "normal":
                return False

            self.timer += delta_time

            if self.state == "warning":
                if (
                    not self.minipoop_created
                    and self.timer >= self.minipoop_appear_time
                ):
                    self.create_minipoop()

                if (
                    self.minipoop_created
                    and all(minipoop["hp"] <= 0 for minipoop in self.minipoop)
                ):
                    self.protected = True

                if self.timer >= self.warning_duration:
                    self.protected = (
                        self.minipoop_created
                        and all(minipoop["hp"] <= 0 for minipoop in self.minipoop)
                    )
                    arcade.play_sound(self.game.rock_break_sounds, speed=1.75)
                    self.state = "attack"
                    self.timer = 0

                    if not self.protected:
                        self.game.hurt()

            elif self.state == "attack":
                if self.timer >= self.attack_duration:
                    self.state = "end"
                    self.timer = 0

            elif self.state == "end":
                if self.timer >= self.end_duration:
                    self.minipoop.clear()
                    self.protected = False
                    self.state = "normal"
                    return True

            return False

        def draw(self):
            if self.state == "normal":
                return

            if self.state == "warning":
                alpha = int(
                    255 * min(
                        self.timer / self.warning_fadein_duration,
                        1,
                    )
                )

                arcade.draw_rect_filled(
                    arcade.XYWH(
                        self.game.box_center_x,
                        self.game.box_center_y,
                        self.game.box_width,
                        self.game.box_height,
                    ),
                    (255, 65, 65, int(75 * alpha / 255)),
                )

                arcade.draw_rect_outline(
                    arcade.XYWH(
                        self.game.box_center_x,
                        self.game.box_center_y,
                        self.game.box_width,
                        self.game.box_height,
                    ),
                    (
                        self.warning_outline[0],
                        self.warning_outline[1],
                        self.warning_outline[2],
                        int(self.warning_outline[3] * alpha / 255),
                    ),
                    border_width=3,
                )

            elif self.state == "attack":
                arcade.draw_rect_filled(
                    arcade.XYWH(
                        self.game.box_center_x,
                        self.game.box_center_y,
                        self.game.box_width,
                        self.game.box_height,
                    ),
                    (255, 40, 40, 150),
                )

            if self.protected:
                arcade.draw_circle_filled(
                    self.game.player.center_x,
                    self.game.player.center_y,
                    max(self.game.player.width, self.game.player.height) * 0.8,
                    (80, 170, 255, 90),
                )

            fade_alpha = 255

            if self.state == "end":
                fade_alpha = int(
                    255 * max(
                        0,
                        1 - self.timer / self.end_duration,
                    )
                )

            for minipoop in self.minipoop:
                if minipoop["hp"] <= 0:
                    continue

                sprite_list = arcade.SpriteList()
                sprite_list.append(minipoop["sprite"])
                sprite_list.draw()

                sprite = minipoop["sprite"]
                sprite.alpha = fade_alpha

                hp_ratio = minipoop["hp"] / self.minipoop_hp

                arcade.draw_rect_filled(
                    arcade.XYWH(
                        minipoop["sprite"].center_x,
                        minipoop["sprite"].bottom - 8,
                        self.game.minipoop.width,
                        5,
                    ),
                    (70, 30, 30, fade_alpha),
                )

                arcade.draw_rect_filled(
                    arcade.XYWH(
                        minipoop["sprite"].left + self.game.minipoop.width * (hp_ratio / 2),
                        minipoop["sprite"].bottom - 8,
                        self.game.minipoop.width * hp_ratio,
                        5,
                    ),
                    (80, 230, 130, fade_alpha),
                )

class Boss_pattern:
    def __init__(self, game):
        self.game = game

        self.normal_pattern_index = 0
        self.enhance_pattern_index = 0

        self.boss_attack = Boss_attack(game)
        self.boss_attack_delay = 1
        self.boss_attack_timer = 0
        self.boss_attack_due = False

        self.normal_pattern = [
            Normal_pattern.Kwangkwang(game),
            Normal_pattern.Memory_battle(game),
            Normal_pattern.Field_attack(game)
        ]
        self.enhance_pattern = [
            # Enhance_pattern.Enhance_kwangkwang(game),
            # Enhance_pattern.Enhance_memory_battle(game),
            Enhance_pattern.Enhance_field_attack(game)
        ]

        self.current_pattern = None
        self.pattern_stack = 0
        self.cooltime = 1

    def update(self, delta_time):
        if self.current_pattern is None:
            if self.boss_attack_due:
                self.boss_attack_timer += delta_time

                if self.boss_attack_timer >= self.boss_attack_delay:
                    self.current_pattern = self.boss_attack
                    self.current_pattern.start()

            else:
                self.cooltime -= delta_time

                if self.cooltime <= 0:
                    boss_hp_ratio = (
                        self.game.boss_hp / self.game.boss_max_hp
                    )

                    if boss_hp_ratio > 0.4:
                        available_patterns = self.normal_pattern
                        pattern_index = self.normal_pattern_index
                    else:
                        available_patterns = self.enhance_pattern
                        pattern_index = self.enhance_pattern_index

                    if available_patterns:
                        self.current_pattern = available_patterns[pattern_index]
                        self.current_pattern.start()
                        self.game.no_hurt_true = True

        if self.current_pattern is not None:
            finished = self.current_pattern.update(delta_time)

            if finished:
                is_boss_attack = (
                    self.current_pattern is self.boss_attack
                )

                self.current_pattern = None
                self.game.arm_form(0)
                self.game.poop_body.scale = self.game.boss_scale
                self.game.poop_arm.scale = self.game.boss_scale

                if is_boss_attack:
                    self.boss_attack_due = False
                    self.boss_attack_timer = 0.0
                    self.cooltime = 1

                else:
                    self.pattern_stack += 1
                    self.cooltime = 1

                    if self.game.boss_hp / self.game.boss_max_hp > 0.4:
                        self.normal_pattern_index = (
                            self.normal_pattern_index + 1
                        ) % len(self.normal_pattern)
                    else:
                        self.enhance_pattern_index = (
                            self.enhance_pattern_index + 1
                        ) % len(self.enhance_pattern)

                    if self.pattern_stack % 2 == 0:
                        self.boss_attack_due = True
                        self.boss_attack_timer = 0.0

                    if self.game.spare_heart is None and self.game.no_hurt_true:
                        self.game.no_hurt_combo += 1
                        self.cooltime = 1.5

    def draw(self):
        if self.current_pattern is not None:
            self.current_pattern.draw()