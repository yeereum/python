import math
import arcade

# ===================== 조절 값 =====================
ACCEL_TIME = 0.25   # 키를 누르고 최고 속도에 도달하기까지 걸리는 시간(초) - 작을수록 반응이 빠름
STOP_TIME = 0.30    # 키를 떼고 완전히 멈출 때까지 걸리는 시간(초) - 클수록 많이 미끄러짐
SPEEDS = [250, 100, 600]   # F키로 바꿀 최고 속도들 (캐릭터별 speed 값이라고 생각하면 됨)
# ====================================================


def approach_vector(vx, vy, target_x, target_y, max_delta):
    """현재 속도 (vx, vy)를 목표 속도 (target_x, target_y) 쪽으로 최대 max_delta만큼만 이동시킨다."""
    dx = target_x - vx
    dy = target_y - vy
    dist = math.hypot(dx, dy)
    if dist <= max_delta:
        return target_x, target_y        # 충분히 가까우면 목표에 바로 도달
    return vx + dx / dist * max_delta, vy + dy / dist * max_delta


class Demo(arcade.Window):
    def __init__(self):
        super().__init__(1280, 720, "부드러운 이동 데모")
        self.background_color = arcade.color.DARK_SLATE_GRAY

        self.keypress = {"W": False, "S": False, "A": False, "D": False}

        self.player = arcade.SpriteSolidColor(60, 60, color=arcade.color.BROWN)
        self.player.position = (640, 360)
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)

        self.speed_index = 0
        self.player_speed = SPEEDS[0]   # 최고 속도
        self.vel_x = 0.0                # 현재 속도 (가속/감속으로 서서히 변함)
        self.vel_y = 0.0

        self.info = arcade.Text("", 20, 690, arcade.color.WHITE, 16)

    def on_update(self, delta_time):
        # 1) 입력 방향 (-1, 0, 1)
        dir_x = int(self.keypress["D"]) - int(self.keypress["A"])
        dir_y = int(self.keypress["W"]) - int(self.keypress["S"])

        # 2) 대각선 이동이 더 빨라지지 않도록 길이를 1로 맞춤
        length = math.hypot(dir_x, dir_y)
        has_input = length > 0
        if has_input:
            dir_x /= length
            dir_y /= length

        # 3) 목표 속도 = 방향 x 최고 속도 (입력이 없으면 0)
        target_x = dir_x * self.player_speed
        target_y = dir_y * self.player_speed

        # 4) 속도를 목표 쪽으로 조금씩 이동 (누르는 중엔 가속, 뗀 뒤엔 감속)
        time_needed = ACCEL_TIME if has_input else STOP_TIME
        rate = self.player_speed / time_needed       # 초당 얼마나 바꿀 수 있는지
        self.vel_x, self.vel_y = approach_vector(
            self.vel_x, self.vel_y, target_x, target_y, rate * delta_time
        )

        # 5) 속도만큼 위치 이동
        self.player.center_x += self.vel_x * delta_time
        self.player.center_y += self.vel_y * delta_time

        # 6) 화면 밖으로 못 나가게 하고, 벽에 닿으면 그 방향 속도는 0으로
        half = 30
        if self.player.center_x < half or self.player.center_x > self.width - half:
            self.player.center_x = max(half, min(self.width - half, self.player.center_x))
            self.vel_x = 0.0
        if self.player.center_y < half or self.player.center_y > self.height - half:
            self.player.center_y = max(half, min(self.height - half, self.player.center_y))
            self.vel_y = 0.0

        speed_now = math.hypot(self.vel_x, self.vel_y)
        self.info.text = (f"최고 속도 {self.player_speed} / 현재 속도 {speed_now:.0f}"
                          f"   (F: 최고 속도 변경)")

    def on_draw(self):
        self.clear()
        self.player_list.draw()
        self.info.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W:
            self.keypress["W"] = True
        elif key == arcade.key.S:
            self.keypress["S"] = True
        elif key == arcade.key.A:
            self.keypress["A"] = True
        elif key == arcade.key.D:
            self.keypress["D"] = True
        elif key == arcade.key.F:
            self.speed_index = (self.speed_index + 1) % len(SPEEDS)
            self.player_speed = SPEEDS[self.speed_index]
        elif key == arcade.key.ESCAPE:
            arcade.exit()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.W:
            self.keypress["W"] = False
        elif key == arcade.key.S:
            self.keypress["S"] = False
        elif key == arcade.key.A:
            self.keypress["A"] = False
        elif key == arcade.key.D:
            self.keypress["D"] = False


if __name__ == "__main__":
    Demo()
    arcade.run()