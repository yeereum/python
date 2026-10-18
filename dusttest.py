"""
Python Arcade - 오브젝트 기준 원형으로 퍼지는 먼지가루 데모

핵심 아이디어
- 먼지 한 알 = 작은 스프라이트 하나 (부드러운 원 모양 텍스처)
- 터뜨릴 때: 360도를 개수만큼 균등하게 나눈 각도로 속도를 줘서 '원형'으로 퍼지게 함
            (각도에 조금씩 흔들림, 속도에 무작위 값을 주면 자연스러워짐)
- 매 프레임: 마찰로 속도가 줄고(퍼지다가 멈춤) / 점점 커지고 / 점점 투명해지다가 / 수명이 끝나면 삭제

조작: WASD 이동 / SPACE: 내 위치에서 먼지 터뜨리기 / 마우스 클릭: 클릭한 곳에서 터뜨리기 / ESC 종료
Arcade 3.x 기준
"""

import math
import random

import arcade
from PIL import Image

# ===================== 조절 값 =====================
DUST_COUNT = 28                 # 한 번에 터지는 먼지 개수
DUST_SPEED = (120, 360)         # 처음 속도 범위 (px/초). 범위가 넓을수록 두께감 있는 고리가 됨
DUST_LIFETIME = (0.5, 0.9)      # 살아있는 시간 범위 (초)
DUST_START_SCALE = 0.35         # 처음 크기 배율
DUST_END_SCALE = 1.1            # 사라질 때 크기 배율 (퍼지면서 커짐)
DUST_START_ALPHA = 170          # 처음 투명도 (0~255)
DUST_DRAG = 3.0                 # 마찰 (클수록 빨리 멈춤). 퍼지는 거리는 대략 '처음 속도 / 마찰'
DUST_COLOR = (200, 180, 150)    # 먼지 색
# ====================================================


def make_dust_texture(size: int = 64) -> arcade.Texture:
    """가운데가 진하고 가장자리로 갈수록 투명해지는 부드러운 원 텍스처를 코드로 만든다."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = img.load()
    center = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - center, y - center) / center   # 0(중심) ~ 1(가장자리)
            if d < 1:
                pixels[x, y] = (255, 255, 255, int(255 * (1 - d) ** 1.5))
    return arcade.Texture(img)


class DustParticle(arcade.Sprite):
    def __init__(self, texture, x, y, direction, speed, lifetime):
        super().__init__(texture, scale=DUST_START_SCALE, center_x=x, center_y=y)
        self.color = DUST_COLOR
        self.vx = math.cos(direction) * speed
        self.vy = math.sin(direction) * speed
        self.life = 0.0
        self.max_life = lifetime

    def update_particle(self, delta_time: float):
        self.life += delta_time
        t = self.life / self.max_life            # 0(태어남) ~ 1(수명 끝)
        if t >= 1:
            self.remove_from_sprite_lists()
            return

        # 마찰: 프레임 속도와 상관없이 같은 느낌이 나도록 지수 감쇠를 사용
        drag = math.exp(-DUST_DRAG * delta_time)
        self.vx *= drag
        self.vy *= drag
        self.center_x += self.vx * delta_time
        self.center_y += self.vy * delta_time

        # 시간이 지날수록 커지고 투명해짐
        self.scale = DUST_START_SCALE + (DUST_END_SCALE - DUST_START_SCALE) * t
        self.alpha = int(DUST_START_ALPHA * (1 - t))


class Demo(arcade.Window):
    def __init__(self):
        super().__init__(1280, 720, "먼지 파티클 데모")
        self.background_color = arcade.color.DARK_SLATE_GRAY

        self.dust_texture = make_dust_texture()
        self.dust_list = arcade.SpriteList()

        # 먼지의 기준이 되는 오브젝트 (실제 게임에서는 self.player 같은 스프라이트)
        self.player = arcade.SpriteSolidColor(60, 60, color=arcade.color.BROWN)
        self.player.position = (640, 360)
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)

        self.keys = set()
        self.hint = arcade.Text(
            "WASD: 이동 / SPACE: 먼지 / 마우스 클릭: 클릭한 곳에서 먼지 / ESC: 종료",
            20, 690, arcade.color.WHITE, 16,
        )

    def spawn_dust(self, x: float, y: float, count: int = DUST_COUNT):
        """(x, y)를 중심으로 먼지를 원형으로 터뜨린다."""
        for i in range(count):
            # 360도를 count개로 균등 분할 + 약간의 흔들림 -> 원형이지만 자연스러움
            direction = math.tau * i / count + random.uniform(-0.12, 0.12)
            speed = random.uniform(*DUST_SPEED)
            lifetime = random.uniform(*DUST_LIFETIME)
            # 중심에서 살짝 떨어진 곳에서 시작하면 한 점에서 뭉쳐 나오는 느낌이 줄어듦
            start_r = random.uniform(0, 12)
            sx = x + math.cos(direction) * start_r
            sy = y + math.sin(direction) * start_r
            self.dust_list.append(
                DustParticle(self.dust_texture, sx, sy, direction, speed, lifetime)
            )

    def on_update(self, delta_time):
        # 간단한 이동 (데모용)
        speed = 300
        if arcade.key.W in self.keys:
            self.player.center_y += speed * delta_time
        if arcade.key.S in self.keys:
            self.player.center_y -= speed * delta_time
        if arcade.key.A in self.keys:
            self.player.center_x -= speed * delta_time
        if arcade.key.D in self.keys:
            self.player.center_x += speed * delta_time

        # 삭제가 일어나므로 복사본(list)을 돌린다
        for particle in list(self.dust_list):
            particle.update_particle(delta_time)

    def on_draw(self):
        self.clear()
        self.player_list.draw()
        self.dust_list.draw()      # 먼지는 오브젝트 위에 그림 (뒤에 깔고 싶으면 순서를 바꾸면 됨)
        self.hint.draw()

    def on_key_press(self, key, modifiers):
        self.keys.add(key)
        if key == arcade.key.SPACE:
            self.spawn_dust(self.player.center_x, self.player.center_y)
        elif key == arcade.key.ESCAPE:
            arcade.exit()

    def on_key_release(self, key, modifiers):
        self.keys.discard(key)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.spawn_dust(x, y)


if __name__ == "__main__":
    Demo()
    arcade.run()