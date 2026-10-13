import math
import os
import random

import arcade
from PIL import Image, ImageDraw

VIRTUAL_WIDTH = 1280
VIRTUAL_HEIGHT = 720
SCREEN_TITLE = "화장실 로비"
START_FULLSCREEN = False

# 이미지 경로: 이 .py 파일이 있는 폴더 기준 (실행 위치와 상관없이 찾도록)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 로비 배경: lobby.png 를 .py 파일과 같은 폴더(또는 assets 폴더)에서 찾음
BG_CANDIDATES = [
    os.path.join(BASE_DIR, "lobby.png"),
    os.path.join(BASE_DIR, "assets", "lobby.png"),
]
POOP_PATHS = [
    os.path.join(BASE_DIR, "assets", "poop_1.png"),
    os.path.join(BASE_DIR, "assets", "poop_2.png"),  # 종류를 늘리려면 여기에 추가
]

POOP_COUNT = 24   # 날아다니는 개수
MARGIN = 100      # 화면 밖 여유 거리 (이만큼 벗어나야 다시 등장시킴)

FONT = ("Malgun Gothic", "Apple SD Gothic Neo", "NanumGothic", "Arial")


# ----------------------------------------------------------------
# 임시 이미지 (그림 파일이 없을 때만 사용)
# ----------------------------------------------------------------
def make_placeholder_bg() -> arcade.Texture:
    """화장실 타일 느낌의 임시 배경"""
    img = Image.new("RGBA", (VIRTUAL_WIDTH, VIRTUAL_HEIGHT), (190, 220, 225, 255))
    draw = ImageDraw.Draw(img)
    tile = 80
    for x in range(0, VIRTUAL_WIDTH + 1, tile):
        draw.line([(x, 0), (x, VIRTUAL_HEIGHT)], fill=(150, 185, 195, 255), width=3)
    for y in range(0, VIRTUAL_HEIGHT + 1, tile):
        draw.line([(0, y), (VIRTUAL_WIDTH, y)], fill=(150, 185, 195, 255), width=3)
    return arcade.Texture(img)


def make_placeholder_poop() -> arcade.Texture:
    """갈색 3단 덩어리 + 눈 (임시)"""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    brown, dark = (120, 78, 40, 255), (80, 50, 25, 255)
    draw.ellipse([6, 38, 58, 60], fill=brown, outline=dark, width=2)
    draw.ellipse([14, 22, 50, 46], fill=brown, outline=dark, width=2)
    draw.ellipse([22, 8, 42, 30], fill=brown, outline=dark, width=2)
    draw.ellipse([25, 34, 31, 40], fill=(255, 255, 255, 255))
    draw.ellipse([35, 34, 41, 40], fill=(255, 255, 255, 255))
    draw.ellipse([27, 36, 30, 39], fill=(0, 0, 0, 255))
    draw.ellipse([37, 36, 40, 39], fill=(0, 0, 0, 255))
    return arcade.Texture(img)


def load_poop_textures() -> list:
    textures = [arcade.load_texture(p) for p in POOP_PATHS if os.path.exists(p)]
    return textures or [make_placeholder_poop()]


# ----------------------------------------------------------------
# 날아다니는 오브젝트
# ----------------------------------------------------------------
class FlyingPoop(arcade.Sprite):
    def __init__(self, texture: arcade.Texture, layer_depth: float):
        """layer_depth: 0.0(멀리) ~ 1.0(가까이)"""
        super().__init__(texture, scale=0.4 + layer_depth * 0.9)
        self.layer_depth = layer_depth
        self.alpha = int(110 + layer_depth * 145)             # 멀수록 흐리게
        self.base_speed = 30 + layer_depth * 150              # 멀수록 느리게
        self.spin = random.uniform(-90, 90) * (0.5 + layer_depth)  # 초당 회전 각도
        self.wobble_amp = random.uniform(20, 60)              # 위아래 출렁이는 폭
        self.wobble_freq = random.uniform(0.5, 1.5)           # 출렁이는 빠르기
        self.time = random.uniform(0, math.tau)
        self.vx = 0.0
        self.vy = 0.0
        self.base_y = 0.0
        self.respawn(first=True)

    def respawn(self, first: bool = False):
        """화면 밖 한쪽 끝에서 다시 등장시킴 (처음에는 화면 전체에 흩뿌림)"""
        direction = random.choice((-1, 1))
        self.vx = direction * self.base_speed
        self.vy = random.uniform(-20, 20)
        self.base_y = random.uniform(0, VIRTUAL_HEIGHT)
        if first:
            self.center_x = random.uniform(0, VIRTUAL_WIDTH)
        else:
            self.center_x = -MARGIN if direction == 1 else VIRTUAL_WIDTH + MARGIN
        self.center_y = self.base_y

    def update_poop(self, dt: float):
        self.time += dt
        self.center_x += self.vx * dt
        self.base_y += self.vy * dt
        # 직선 이동 + 사인파 출렁임 = 둥둥 떠다니는 느낌
        self.center_y = self.base_y + math.sin(self.time * self.wobble_freq * 2) * self.wobble_amp
        self.angle += self.spin * dt

        out_x = (self.vx > 0 and self.center_x > VIRTUAL_WIDTH + MARGIN) or \
                (self.vx < 0 and self.center_x < -MARGIN)
        if out_x:
            self.respawn()
        elif self.base_y > VIRTUAL_HEIGHT + MARGIN:
            self.base_y = -MARGIN
        elif self.base_y < -MARGIN:
            self.base_y = VIRTUAL_HEIGHT + MARGIN


# ----------------------------------------------------------------
# 로비 창
# ----------------------------------------------------------------
class LobbyWindow(arcade.Window):
    def __init__(self):
        super().__init__(
            VIRTUAL_WIDTH, VIRTUAL_HEIGHT, SCREEN_TITLE,
            fullscreen=START_FULLSCREEN, resizable=True,
        )
        self.background_color = arcade.color.BLACK
        self.virtual_aspect = VIRTUAL_WIDTH / VIRTUAL_HEIGHT
        self.game_camera = arcade.Camera2D()
        self.viewport_rect = (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT)

        # 배경: 이미지가 있으면 사용, 없으면 임시 배경
        bg_path = next((p for p in BG_CANDIDATES if os.path.exists(p)), None)
        if bg_path:
            bg_texture = arcade.load_texture(bg_path)
        else:
            print("[알림] lobby.png 를 찾지 못해 임시 배경을 사용합니다.")
            print("       찾아본 위치:", *BG_CANDIDATES, sep="\n       ")
            bg_texture = make_placeholder_bg()
        bg_sprite = arcade.Sprite(bg_texture, center_x=VIRTUAL_WIDTH / 2,
                                  center_y=VIRTUAL_HEIGHT / 2)
        bg_sprite.width = VIRTUAL_WIDTH     # 이미지 크기가 달라도 화면에 꽉 채움
        bg_sprite.height = VIRTUAL_HEIGHT
        self.bg_list = arcade.SpriteList()
        self.bg_list.append(bg_sprite)

        # 똥 오브젝트: 멀리 있는 것부터 먼저 그려야 가까운 것이 위에 보임 -> depth 오름차순 정렬
        textures = load_poop_textures()
        poops = [FlyingPoop(random.choice(textures), random.random())
                 for _ in range(POOP_COUNT)]
        poops.sort(key=lambda p: p.layer_depth)
        self.poop_list = arcade.SpriteList()
        for p in poops:
            self.poop_list.append(p)

        self.title_text = arcade.Text(
            "화장실 로비", VIRTUAL_WIDTH / 2, VIRTUAL_HEIGHT / 2 + 60,
            arcade.color.WHITE, 64, font_name=FONT,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.hint_text = arcade.Text(
            "F11: 전체화면 / ESC: 종료", VIRTUAL_WIDTH / 2, VIRTUAL_HEIGHT / 2 - 30,
            arcade.color.LIGHT_GRAY, 24, font_name=FONT,
            anchor_x="center", anchor_y="center",
        )

        self.update_viewport()

    def update_viewport(self):
        ratio = self.get_pixel_ratio()
        win_w, win_h = int(self.width * ratio), int(self.height * ratio)
        if win_w <= 0 or win_h <= 0:
            return
        if win_w / win_h > self.virtual_aspect:
            view_h = win_h
            view_w = int(win_h * self.virtual_aspect)
        else:
            view_w = win_w
            view_h = int(win_w / self.virtual_aspect)
        x, y = (win_w - view_w) // 2, (win_h - view_h) // 2
        self.viewport_rect = (x, y, view_w, view_h)

        self.game_camera.viewport = arcade.LBWH(x, y, view_w, view_h)
        self.game_camera.projection = arcade.LRBT(
            -VIRTUAL_WIDTH / 2, VIRTUAL_WIDTH / 2,
            -VIRTUAL_HEIGHT / 2, VIRTUAL_HEIGHT / 2,
        )
        self.game_camera.position = (VIRTUAL_WIDTH / 2, VIRTUAL_HEIGHT / 2)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.update_viewport()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.F11:
            self.set_fullscreen(not self.fullscreen)
            self.update_viewport()
        elif key == arcade.key.ESCAPE:
            arcade.exit()

    def on_update(self, delta_time: float):
        for poop in self.poop_list:
            poop.update_poop(delta_time)

    def on_draw(self):
        self.default_camera.use()
        self.clear()
        self.game_camera.use()

        self.bg_list.draw()     # 1) 배경
        self.poop_list.draw()   # 2) 날아다니는 오브젝트
        self.title_text.draw()  # 3) 로비 UI는 맨 위
        self.hint_text.draw()


def main():
    LobbyWindow()
    arcade.run()


if __name__ == "__main__":
    main()
