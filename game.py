import arcade
import json
from pathlib import Path
from pattern import Boss_pattern

record_file = Path(__file__).resolve().parent / "record.json"

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

        self.boss_pattern = Boss_pattern(self)

        # 게임오버 설정
        self.game_over_true = False
        self.final_score = 0

        # 게임 클리어 설정
        self.game_clear_true = False

        # 커서 깜빡임
        self.cursor_time = 0
        self.cursor_visible = True

        # 플레이어 이동
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

        # 보스 체력바
        self.hp_bar_width = 500
        self.hp_bar_height = 20
        self.hp_bar_x = self.window.width / 2
        self.hp_bar_y = 800

        # 플레이어 체력
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

        # 피격 이펙트
        self.damage_color_time = 0
        self.damage_color_duration = 0.4

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
        self.attack_damage = 100

        self.user_name = ""
        self.player_info = ""
        self.active_input = "user_name"  # 게임오버 창에서 선택되어 있는 입력칸

        self.record_saved = False
        self.save_status = ""            # 게임 피니쉬 상태 메세지
        self.mouse_x = 0
        self.mouse_y = 0
        self.save_button_hovered = False

        # 최대 글자 수
        self.name_max_length = 10
        self.player_info_max_length = 10

        self.name_field = arcade.XYWH(
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
        if self.spare_heart is not None or self.game_over_true or self.game_clear_true:
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
        if self.game_over_true or self.game_clear_true:
            return

        if self.spare_heart is not None:
            self.remove_spare_heart()
            return

        if self.player_hp <= 0:
            self.game_over()
            return
        
        self.player_hp -= 1
        self.change_heart(self.player_hp, 2)
        self.damage_color_time = self.damage_color_duration
        self.player.color = (255, 0, 0)

    def attack(self):
        if self.game_over_true or self.game_clear_true:
            return

        if self.boss_hp <= 0:
            self.game_clear()
            return
        
        if self.boss_hp > 0:
            self.boss_hp = max(
                0,
                self.boss_hp - self.attack_damage,
            )

    def game_over(self):
        if self.game_over_true:
            return

        if self.remain_time <= 0 or self.player_hp <= 0:
            self.game_clear_true = False
            self.game_over_true = True

        if self.game_over_true:
            self.moving_keys.clear()
            self.final_score = (self.boss_max_hp - self.boss_hp) * 10

    def game_clear(self):
        if self.game_clear_true:
            return

        if self.remain_time > 0 and self.player_hp > 0 and self.boss_hp <= 0:
            self.game_over_true = False
            self.game_clear_true = True
        
        if self.game_clear_true:
            self.moving_keys.clear()
            self.final_score = (self.boss_max_hp - self.boss_hp) * 10 + int(self.remain_time) * 50


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

        # 게임오버 or 클리어 텍스트
        if self.game_clear_true:
            self.game_over_text = "GAME CLEAR!"
        else:
            self.game_over_text = "GAME OVER"

        arcade.draw_text(
            self.game_over_text,
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

        # 이름 텍스트
        arcade.draw_text(
            "NAME",
            self.window.width / 2 - 250,
            490,
            arcade.color.WHITE,
            font_size=12,
            font_name="Press Start 2P",
            anchor_x="left",
        )

        # 이름 텍스트 색상
        name_color = (
            (100, 150, 210)
            if self.active_input == "user_name"
            else (70, 75, 95)
        )

        # 이름 칸 배경
        arcade.draw_rect_filled(
            self.name_field,
            (35, 38, 55),
        )
        
        # 이름 칸 테두리
        arcade.draw_rect_outline(
            self.name_field,
            name_color,
            border_width=2,
        )

        name_display = self.user_name or "Enter name"
        if self.active_input == "user_name" and self.user_name and self.cursor_visible:
            name_display += "|"

        # 이름 칸 텍스트
        arcade.draw_text(
            name_display,
            self.window.width / 2 - 235,
            445,
            (255, 255, 255) if self.user_name else (140, 140, 155),
            font_size=12,
            font_name="Press Start 2P",
            anchor_y="center",
        )

        # 학번 텍스트
        arcade.draw_text(
            "STUDENT NUMBER",
            self.window.width / 2 - 250,
            385,
            arcade.color.WHITE,
            font_size=12,
            font_name="Press Start 2P",
            anchor_x="left",
        )

        # 학번 텍스트 컬러
        info_color = (
            (100, 150, 210)
            if self.active_input == "player_info"
            else (70, 75, 95)
        )

        # 학번 칸 배경
        arcade.draw_rect_filled(
            self.player_info_field,
            (35, 38, 55),
        )

        # 학번 칸 테두리
        arcade.draw_rect_outline(
            self.player_info_field,
            info_color,
            border_width=2,
        )

        info_display = self.player_info or "Enter student number"
        if self.active_input == "player_info" and self.player_info and self.cursor_visible:
            info_display += "|"

        # 학번 칸 텍스트
        arcade.draw_text(
            info_display,
            self.window.width / 2 - 235,
            340,
            (255, 255, 255) if self.player_info else (140, 140, 155),
            font_size=12,
            font_name="Press Start 2P",
            anchor_y="center",
        )

        if self.record_saved:               # 기록이 저장되었다면
            button_color = (55, 75, 60)
        elif self.save_button_hovered:      # 버튼 위에 마우스를 올렸다면
            button_color = (120, 175, 125)
        else:
            button_color = (75, 120, 90)

        # 끝내기 버튼 배경
        arcade.draw_rect_filled(
            self.save_button,
            button_color,
        )

        # 끝내기 버튼 테두리
        arcade.draw_rect_outline(
            self.save_button,
            (220, 220, 230),
            border_width=2,
        )

        # 끝내기 버튼 텍스트
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

        # 상태 메세지
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

        user_name = self.user_name.strip()
        player_info = self.player_info.strip()

        if not user_name:
            self.save_status = "Please enter a name"
            self.active_input = "user_name"
            return

        if not player_info:
            self.save_status = "Please enter a student number"
            self.active_input = "player_info"
            return

        if record_file.exists():
            try:
                with record_file.open("r", encoding="utf-8") as file:
                    data = json.load(file)
            except (json.JSONDecodeError, OSError):
                self.save_status = "Could not read records.json"
                return
        else:
            data = {"players": []}

        if not isinstance(data, dict) or not isinstance(data.get("players"), list):
            self.save_status = "Invalid records.json format"
            return

        players = data["players"]
        normalized_name = user_name.casefold()
        normalized_info = player_info.casefold()

        existing_player = next(
            (
                player
                for player in players
                if isinstance(player, dict)
                and str(player.get("user_name", "")).strip().casefold()
                == normalized_name
                and str(
                    player.get(
                        "student number",
                        player.get("student_number", player.get("player_info", "")),
                    )
                ).strip().casefold() == normalized_info
            ),
            None,
        )

        if existing_player is None:
            players.append(
                {
                    "user_name": user_name,
                    "student number": player_info,
                    "best_score": self.final_score,
                }
            )
        else:
            previous_best = int(existing_player.get("best_score", 0))
            existing_player["user_name"] = user_name
            existing_player["student number"] = player_info
            existing_player["best_score"] = max(
                previous_best,
                self.final_score,
            )

        try:
            with record_file.open("w", encoding="utf-8") as file:
                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=4,
                )
        except OSError:
            self.save_status = "Could not save records.json"
            return

        self.record_saved = True
        self.save_status = "Record saved successfully"
        from lobby import Lobby
        self.window.show_view(Lobby())
        return True

    def on_draw(self):
        self.clear(color=(10, 11, 18))

        self.boss_pattern.draw()

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

        if self.game_over_true or self.game_clear_true:
            self.draw_game_over_overlay()

    def on_update(self, delta_time):
        self.boss_pattern.update(delta_time)

        if self.game_over_true or self.game_clear_true:
            self.cursor_time += delta_time
            if self.cursor_time >= 0.5:          # 커서 깜빡임 시간
                self.cursor_time = 0
                self.cursor_visible = not self.cursor_visible
            return

        self.poop_body.update_animation(delta_time)
        self.poop_arm.position = self.poop_body.position

        if self.damage_color_time > 0:
            self.damage_color_time = max(
                0,
                self.damage_color_time - delta_time,
            )

            progress = self.damage_color_time / self.damage_color_duration

            self.player.color = tuple(
                int(original + (red - original) * progress)
                for original, red in zip(
                    (255, 255, 255),
                    (255, 40, 40),
                )
            )
        else:
            self.player.color = (255, 255, 255)

        if self.remain_time > 0:
            self.remain_time = max(
                0,
                self.remain_time - delta_time,
            )

        self.game_over()
        self.game_clear()

        if self.game_over_true or self.game_clear_true:
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
        if (not self.game_over_true and not self.game_clear_true) or self.record_saved:
            return

        if self.name_field.x - self.name_field.width / 2 <= x <= self.name_field.x + self.name_field.width / 2 and self.name_field.y - self.name_field.height / 2 <= y <= self.name_field.y + self.name_field.height / 2:
            self.active_input = "user_name"
            return

        if self.player_info_field.x - self.player_info_field.width / 2 <= x <= self.player_info_field.x + self.player_info_field.width / 2 and self.player_info_field.y - self.player_info_field.height / 2 <= y <= self.player_info_field.y + self.player_info_field.height / 2:
            self.active_input = "player_info"
            return

        if self.save_button.x - self.save_button.width / 2 <= x <= self.save_button.x + self.save_button.width / 2 and self.save_button.y - self.save_button.height / 2 <= y <= self.save_button.y + self.save_button.height / 2:
            self.save_record()

    def on_text(self, text):
        if (not self.game_over_true and not self.game_clear_true) or self.record_saved:
            return

        if not text.isprintable():
            return

        if self.active_input == "user_name":
            if len(self.user_name) < self.name_max_length:
                self.user_name += text
        elif self.active_input == "player_info":
            if len(self.player_info) < self.player_info_max_length:
                self.player_info += text

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            arcade.exit()
            return

        if self.game_over_true or self.game_clear_true:
            if self.record_saved:
                return

            if key == arcade.key.BACKSPACE:
                if self.active_input == "user_name":
                    self.user_name = self.user_name[:-1]
                elif self.active_input == "player_info":
                    self.player_info = self.player_info[:-1]

            elif key in (arcade.key.UP, arcade.key.DOWN, arcade.key.TAB):
                self.active_input = (
                    "player_info"
                    if self.active_input == "user_name"
                    else "user_name"
                )
                self.cursor_visible = True
                self.cursor_time = 0

        if key in (
            arcade.key.W,
            arcade.key.A,
            arcade.key.S,
            arcade.key.D,
        ):
            self.moving_keys.add(key)

        elif key == arcade.key.SEMICOLON:
            self.attack()

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