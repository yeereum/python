import arcade
import json
from pathlib import Path

RECORD_FILE = Path(__file__).resolve().parent / "records.json"

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
        self.game_over_reason = ""
        self.final_score = 0

        self.cursor_elapsed = 0.0
        self.cursor_visible = True
        self.ignore_next_text = False

        self.move_speed = 300
        self.moving_keys = set()

        self.remain_time = 20

        self.box_width = 700
        self.box_height = 400
        self.box_center_x = self.window.width / 2
        self.box_center_y = 300
        self.box_border_width = 5

        self.hp_bar_width = 500
        self.hp_bar_height = 20
        self.hp_bar_x = self.window.width / 2
        self.hp_bar_y = 800

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
        self.attack_damage = 10

        self.nickname = ""
        self.player_info = ""
        self.active_input = "nickname"

        self.record_saved = False
        self.save_status = ""
        self.mouse_x = 0
        self.mouse_y = 0
        self.save_button_hovered = False

        self.nickname_max_length = 24
        self.player_info_max_length = 48

        self.nickname_field = arcade.XYWH(
            self.window.width / 2, 455, 500, 48
        )
        self.player_info_field = arcade.XYWH(
            self.window.width / 2, 350, 500, 48
        )
        self.save_button = arcade.XYWH(
            self.window.width / 2, 235, 300, 60
        )

    def change_heart(self, index, texture_index):
        if not 0 <= index < len(self.heart_list):
            return

        if not 0 <= texture_index < len(self.heart_textures):
            return

        self.heart_list[index].texture = self.heart_textures[texture_index]

    def add_spare_heart(self):
        if self.spare_heart is not None or self.game_over_true:
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
        if 0 <= index < len(self.poop_arm_frames):
            self.poop_arm_index = index
            self.poop_arm.texture = self.poop_arm_frames[index]

    def damage(self):
        if self.game_over_true:
            return

        if self.spare_heart is not None:
            self.remove_spare_heart()
            return

        if self.player_hp <= 0:
            self.game_over()
            return

        self.player_hp -= 1
        self.change_heart(self.player_hp, 2)
        self.player.color = (200, 40, 40)

        self.game_over()

    def attack(self):
        if self.game_over_true:
            return

        if self.boss_hp > 0:
            self.boss_hp = max(
                0,
                self.boss_hp - self.attack_damage,
            )

        print("공격!")

    def game_over(self):
        if self.game_over_true:
            return

        if self.remain_time <= 0:
            self.game_over_true = True
            self.game_over_reason = "TIME UP"

        elif self.player_hp <= 0:
            self.game_over_true = True
            self.game_over_reason = "GAME OVER"

        if self.game_over_true:
            self.moving_keys.clear()
            self.final_score = max(
                0,
                self.boss_max_hp - self.boss_hp,
            )

    def draw_game_over_overlay(self):
        # 화면 전체 반투명 배경
        arcade.draw_rect_filled(
            arcade.XYWH(
                self.window.width / 2,
                self.window.height / 2,
                self.window.width,
                self.window.height,
            ),
            (0, 0, 0, 190),
        )

        # 중앙 어두운 패널
        arcade.draw_rect_filled(
            arcade.XYWH(
                self.window.width / 2,
                self.window.height / 2,
                720,
                570,
            ),
            (18, 20, 32, 250),
        )

        # 패널 테두리
        arcade.draw_rect_outline(
            arcade.XYWH(
                self.window.width / 2,
                self.window.height / 2,
                720,
                570,
            ),
            (210, 210, 230),
            border_width=3,
        )

        # 사망메세지
        arcade.draw_text(
            self.game_over_reason,
            self.window.width / 2,
            590,
            arcade.color.WHITE,
            font_size=26,
            font_name="Press Start 2P",
            anchor_x="center",
        )

        # 스코어
        arcade.draw_text(
            f"SCORE: {self.final_score}",
            self.window.width / 2,
            535,
            (255, 220, 120),
            font_size=18,
            font_name="Press Start 2P",
            anchor_x="center",
        )

        # 닉네임 글자
        arcade.draw_text(
            "NICKNAME",
            self.window.width / 2 - 250,
            490,
            arcade.color.WHITE,
            font_size=12,
            font_name="Press Start 2P",
            anchor_x="left",
        )

        nickname_color = (
            (100, 150, 210)
            if self.active_input == "nickname"
            else (70, 75, 95)
        )

        # 닉네임 칸 배경
        arcade.draw_rect_filled(
            self.nickname_field,
            (35, 38, 55),
        )
        
        # 닉네임 칸 테두리
        arcade.draw_rect_outline(
            self.nickname_field,
            nickname_color,
            border_width=2,
        )

        nickname_display = self.nickname or "Enter nickname"
        if self.active_input == "nickname" and self.cursor_visible:
            nickname_display += "|"

        arcade.draw_text(
            nickname_display,
            self.window.width / 2 - 235,
            445,
            (255, 255, 255) if self.nickname else (140, 140, 155),
            font_size=12,
            font_name="Press Start 2P",
            anchor_y="center",
        )

        arcade.draw_text(
            "PLAYER ID / INFO",
            self.window.width / 2 - 250,
            385,
            arcade.color.WHITE,
            font_size=12,
            font_name="Press Start 2P",
            anchor_x="left",
        )

        info_color = (
            (100, 150, 210)
            if self.active_input == "player_info"
            else (70, 75, 95)
        )

        arcade.draw_rect_filled(
            self.player_info_field,
            (35, 38, 55),
        )
        arcade.draw_rect_outline(
            self.player_info_field,
            info_color,
            border_width=2,
        )

        info_display = self.player_info or "Enter player ID"
        if self.active_input == "player_info" and self.cursor_visible:
            info_display += "|"

        arcade.draw_text(
            info_display,
            self.window.width / 2 - 235,
            340,
            (255, 255, 255) if self.player_info else (140, 140, 155),
            font_size=12,
            font_name="Press Start 2P",
            anchor_y="center",
        )

        if self.record_saved:
            button_color = (55, 75, 60)
        elif self.save_button_hovered:
            button_color = (120, 175, 125)
        else:
            button_color = (75, 120, 90)

        arcade.draw_rect_filled(
            self.save_button,
            button_color,
        )
        arcade.draw_rect_outline(
            self.save_button,
            (220, 220, 230),
            border_width=2,
        )

        arcade.draw_text(
            "FINISH",
            self.window.width / 2,
            235,
            arcade.color.WHITE,
            font_size=16,
            font_name="Press Start 2P",
            anchor_x="center",
            anchor_y="center",
        )

        if self.save_status:
            arcade.draw_text(
                self.save_status,
                self.window.width / 2,
                175,
                (255, 180, 150) if not self.record_saved else (150, 230, 160),
                font_size=10,
                font_name="Press Start 2P",
                anchor_x="center",
            )

    def save_record(self):
        if self.record_saved:
            return

        nickname = self.nickname.strip()
        player_info = self.player_info.strip()

        if not nickname:
            self.save_status = "Please enter a nickname."
            self.active_input = "nickname"
            return

        if not player_info:
            self.save_status = "Please enter a player ID / info."
            self.active_input = "player_info"
            return

        if RECORD_FILE.exists():
            try:
                with RECORD_FILE.open("r", encoding="utf-8") as file:
                    data = json.load(file)
            except (json.JSONDecodeError, OSError):
                self.save_status = "Could not read records.json."
                return
        else:
            data = {"players": []}

        if not isinstance(data, dict) or not isinstance(data.get("players"), list):
            self.save_status = "Invalid records.json format."
            return

        players = data["players"]
        normalized_info = player_info.casefold()

        existing_player = next(
            (
                player
                for player in players
                if isinstance(player, dict)
                and str(player.get("player_info", "")).strip().casefold()
                == normalized_info
            ),
            None,
        )

        if existing_player is None:
            players.append(
                {
                    "nickname": nickname,
                    "player_info": player_info,
                    "best_score": self.final_score,
                }
            )
        else:
            previous_best = int(existing_player.get("best_score", 0))
            existing_player["nickname"] = nickname
            existing_player["player_info"] = player_info
            existing_player["best_score"] = max(
                previous_best,
                self.final_score,
            )

        try:
            with RECORD_FILE.open("w", encoding="utf-8") as file:
                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=4,
                )
        except OSError:
            self.save_status = "Could not save records.json."
            return

        self.record_saved = True
        self.save_status = "Record saved successfully."
        from lobby import Lobby
        self.window.show_view(Lobby())
        return True

    def on_draw(self):
        self.clear(color=(10, 11, 18))

        arcade.draw_rect_outline(
            arcade.XYWH(
                self.box_center_x,
                self.box_center_y,
                self.box_width,
                self.box_height,
            ),
            color=(255, 255, 255),
            border_width=self.box_border_width,
        )

        self.heart_list.draw()
        self.spare_heart_list.draw()
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

        timer_min = int(self.remain_time) // 60
        timer_sec = int(self.remain_time) % 60
        timer_color = (
            arcade.color.RED
            if self.remain_time < 11
            else arcade.color.WHITE
        )

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

        if self.game_over_true:
            self.draw_game_over_overlay()

    def on_update(self, delta_time):
        if self.game_over_true:
            self.cursor_elapsed += delta_time
            if self.cursor_elapsed >= 0.5:
                self.cursor_elapsed = 0.0
                self.cursor_visible = not self.cursor_visible
            return

        self.poop_body.update_animation(delta_time)
        self.poop_arm.position = self.poop_body.position

        if self.remain_time > 0:
            self.remain_time = max(
                0,
                self.remain_time - delta_time,
            )

        self.game_over()

        if self.game_over_true:
            return

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

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
        self.save_button_hovered = (
            self.save_button.x - self.save_button.width / 2 <= x
            <= self.save_button.x + self.save_button.width / 2
            and self.save_button.y - self.save_button.height / 2 <= y
            <= self.save_button.y + self.save_button.height / 2
        )

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.game_over_true or self.record_saved:
            return

        if self.nickname_field.x - self.nickname_field.width / 2 <= x <= self.nickname_field.x + self.nickname_field.width / 2 and self.nickname_field.y - self.nickname_field.height / 2 <= y <= self.nickname_field.y + self.nickname_field.height / 2:
            self.active_input = "nickname"
            return

        if self.player_info_field.x - self.player_info_field.width / 2 <= x <= self.player_info_field.x + self.player_info_field.width / 2 and self.player_info_field.y - self.player_info_field.height / 2 <= y <= self.player_info_field.y + self.player_info_field.height / 2:
            self.active_input = "player_info"
            return

        if self.save_button.x - self.save_button.width / 2 <= x <= self.save_button.x + self.save_button.width / 2 and self.save_button.y - self.save_button.height / 2 <= y <= self.save_button.y + self.save_button.height / 2:
            self.save_record()

    def on_text(self, text):
        if self.ignore_next_text:
            self.ignore_next_text = False
            return

        if not self.game_over_true or self.record_saved:
            return

        if not text.isprintable():
            return

        if self.active_input == "nickname":
            if len(self.nickname) < self.nickname_max_length:
                self.nickname += text
        elif self.active_input == "player_info":
            if len(self.player_info) < self.player_info_max_length:
                self.player_info += text

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            arcade.exit()
            return

        if self.game_over_true:
            if self.record_saved:
                return

            if key == arcade.key.BACKSPACE:
                if self.active_input == "nickname":
                    self.nickname = self.nickname[:-1]
                elif self.active_input == "player_info":
                    self.player_info = self.player_info[:-1]

            elif key in (arcade.key.UP, arcade.key.DOWN, arcade.key.TAB):
                self.active_input = (
                    "player_info"
                    if self.active_input == "nickname"
                    else "nickname"
                )
                self.cursor_visible = True
                self.cursor_elapsed = 0.0

            elif key == arcade.key.ENTER:
                if self.save_button_hovered:
                    self.save_record()
                elif self.active_input == "nickname":
                    self.active_input = "player_info"
                    self.cursor_visible = True
                    self.cursor_elapsed = 0.0
                else:
                    self.save_status = "Hover over COMPLETE and press ENTER."

            return

        if key in (
            arcade.key.W,
            arcade.key.A,
            arcade.key.S,
            arcade.key.D,
        ):
            self.moving_keys.add(key)

        elif key == arcade.key.SEMICOLON:
            self.attack()

        elif key == arcade.key.E:
            self.add_spare_heart()

        elif key == arcade.key.Q:
            self.remove_spare_heart()

        elif key == arcade.key.F:
            was_game_over = self.game_over_true
            self.damage()
            if not was_game_over and self.game_over_true:
                self.ignore_next_text = True

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