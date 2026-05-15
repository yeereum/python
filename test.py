import pygame
import sys
import math
import random
from dataclasses import dataclass, field
from typing import Optional

# ────────────────────────────────────────────
#  상수 정의
# ────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1100, 720
TILE_SIZE = 64
FARM_COLS, FARM_ROWS = 10, 8
FARM_X, FARM_Y = 10, 60         # 농장 그리드 시작 좌표
UI_X = FARM_X + FARM_COLS * TILE_SIZE + 16
PANEL_W = SCREEN_W - UI_X - 8
FPS = 60

# 계절
SEASONS = ["🌸 봄", "☀️ 여름", "🍂 가을", "❄️ 겨울"]
SEASON_COLORS = [
    (180, 230, 180),   # 봄 - 연초록
    (230, 220, 140),   # 여름 - 노란
    (210, 160, 100),   # 가을 - 주황
    (200, 220, 240),   # 겨울 - 하늘
]

# ────────────────────────────────────────────
#  색상 팔레트
# ────────────────────────────────────────────
C = {
    "bg":          (30,  40,  20),
    "tile_empty":  (55,  90,  35),
    "tile_tilled": (100, 65,  30),
    "tile_watered":(60,  50,  20),
    "tile_rock":   (80,  80,  90),
    "tile_tree":   (30,  70,  30),
    "grid_line":   (45,  75,  28),
    "ui_bg":       (25,  30,  40),
    "ui_panel":    (35,  42,  55),
    "ui_border":   (70,  85, 110),
    "text":        (230, 220, 200),
    "text_muted":  (140, 130, 120),
    "text_gold":   (245, 200,  60),
    "text_green":  (100, 220, 110),
    "text_red":    (220, 100, 100),
    "text_blue":   (120, 180, 255),
    "highlight":   (255, 220,  60),
    "btn":         (50,  60,  80),
    "btn_hover":   (70,  85, 110),
    "btn_active":  (60, 100,  60),
    "ready_glow":  (80, 220,  80),
    "energy_bar":  (80, 180, 220),
    "hp_bar":      (80, 220, 100),
}

# ────────────────────────────────────────────
#  작물 데이터
# ────────────────────────────────────────────
@dataclass
class CropData:
    name: str
    emoji: str
    cost: int        # 씨앗 가격
    sell: int        # 수확물 판매가
    days: int        # 성장 일수
    season: int      # 재배 가능 계절 (0=봄,1=여름,2=가을,3=겨울)
    color: tuple     # 성장 중 색상

CROPS = {
    "turnip":  CropData("순무",   "🌿", 15,  40,  4, 0, (120, 200, 80)),
    "potato":  CropData("감자",   "🥔", 25,  70,  6, 0, (160, 180, 60)),
    "melon":   CropData("멜론",   "🍈", 40, 130,  8, 1, (80,  200, 120)),
    "corn":    CropData("옥수수", "🌽", 30,  85,  6, 1, (200, 200, 60)),
    "pumpkin": CropData("호박",   "🎃", 50, 160, 10, 2, (200, 130, 50)),
    "grape":   CropData("포도",   "🍇", 35, 110,  7, 2, (160, 80,  180)),
}

# ────────────────────────────────────────────
#  도구 정의
# ────────────────────────────────────────────
TOOLS = [
    ("hoe",     "괭이",     "⛏",  "빈 땅을 경작합니다",          2),
    ("water",   "물뿌리개", "💧", "심어진 작물에 물을 줍니다",    1),
    ("seed",    "씨앗심기", "🌱", "경작된 땅에 씨앗을 심습니다", 2),
    ("harvest", "수확",     "🧺", "다 자란 작물을 수확합니다",    1),
    ("axe",     "도끼",     "🪓", "나무를 베어 목재를 얻습니다",  3),
    ("pickaxe", "곡괭이",   "⛏", "바위를 캐서 돌을 얻습니다",    3),
]
TOOL_IDS = [t[0] for t in TOOLS]

# ────────────────────────────────────────────
#  타일 상태
# ────────────────────────────────────────────
@dataclass
class Tile:
    kind: str = "empty"       # empty / tilled / watered / rock / tree / stump
    plant_id: Optional[str] = None
    planted_day: int = 0
    watered: bool = False
    growth: float = 0.0       # 0.0 ~ 1.0

    @property
    def is_ready(self):
        return self.plant_id is not None and self.growth >= 1.0

# ────────────────────────────────────────────
#  게임 상태
# ────────────────────────────────────────────
@dataclass
class GameState:
    day: int = 1
    season: int = 0
    gold: int = 500
    energy: int = 100
    max_energy: int = 100
    level: int = 1
    xp: int = 0
    tool: str = "hoe"
    selected_seed: str = "turnip"
    seeds: dict = field(default_factory=lambda: {"turnip": 5})
    inventory: dict = field(default_factory=dict)   # crop_id -> qty
    resources: dict = field(default_factory=dict)   # "wood","stone" -> qty
    tiles: list = field(default_factory=list)
    log: list = field(default_factory=list)
    total_earned: int = 0
    harvests: int = 0

    def add_log(self, msg: str):
        self.log.insert(0, msg)
        if len(self.log) > 30:
            self.log.pop()

    def spend_energy(self, amount: int) -> bool:
        if self.energy < amount:
            self.add_log("⚡ 에너지가 부족합니다!")
            return False
        self.energy -= amount
        return True

    def gain_xp(self, amount: int):
        self.xp += amount
        needed = self.level * 60
        if self.xp >= needed:
            self.xp -= needed
            self.level += 1
            self.add_log(f"🏆 레벨 업! → 레벨 {self.level}")
            self.max_energy += 10
            self.energy = min(self.energy + 20, self.max_energy)

    def xp_ratio(self) -> float:
        return self.xp / (self.level * 60)

    def available_seeds(self):
        return {k: v for k, v in self.seeds.items()
                if v > 0 and CROPS[k].season == self.season}

# ────────────────────────────────────────────
#  초기 타일 배치
# ────────────────────────────────────────────
def make_tiles() -> list:
    tiles = []
    for r in range(FARM_ROWS):
        for c in range(FARM_COLS):
            t = Tile()
            rng = random.random()
            if (r in (0, FARM_ROWS-1)) or (c in (0, FARM_COLS-1)):
                t.kind = "empty"   # 외곽은 비워둠
            elif rng < 0.06:
                t.kind = "rock"
            elif rng < 0.11:
                t.kind = "tree"
            tiles.append(t)
    return tiles

# ────────────────────────────────────────────
#  하루 경과 처리
# ────────────────────────────────────────────
def advance_day(gs: GameState):
    gs.day += 1
    gs.energy = gs.max_energy

    if gs.day > 28:
        gs.day = 1
        gs.season = (gs.season + 1) % 4
        gs.add_log(f"🌍 계절 변경: {SEASONS[gs.season]}")

    ready_count = 0
    for tile in gs.tiles:
        if tile.kind == "watered":
            tile.kind = "tilled"
        tile.watered = False
        if tile.plant_id:
            crop = CROPS[tile.plant_id]
            # 물을 준 날만 성장
            age = gs.day - tile.planted_day
            tile.growth = min(1.0, age / crop.days)
            if tile.growth >= 1.0:
                ready_count += 1

    if ready_count:
        gs.add_log(f"🌾 {ready_count}개의 작물이 수확 가능합니다!")
    gs.add_log(f"☀️  {gs.day}일차 아침 (에너지 회복)")

# ────────────────────────────────────────────
#  타일 클릭 처리
# ────────────────────────────────────────────
def use_tool(gs: GameState, idx: int):
    tile = gs.tiles[idx]
    tool = gs.tool

    if tool == "hoe":
        if tile.kind == "empty":
            if gs.spend_energy(2):
                tile.kind = "tilled"
                gs.gain_xp(2)
                gs.add_log("⛏  밭을 경작했습니다.")
        elif tile.kind in ("tilled", "watered"):
            gs.add_log("이미 경작된 땅입니다.")
        else:
            gs.add_log("여기는 경작할 수 없습니다.")

    elif tool == "water":
        if tile.plant_id and not tile.watered:
            if gs.spend_energy(1):
                tile.watered = True
                if tile.kind == "tilled":
                    tile.kind = "watered"
                gs.add_log("💧 물을 주었습니다.")
        elif tile.kind in ("tilled",) and not tile.plant_id:
            if gs.spend_energy(1):
                tile.kind = "watered"
                tile.watered = True
                gs.add_log("💧 물을 주었습니다.")
        elif tile.watered:
            gs.add_log("이미 물을 주었습니다.")
        else:
            gs.add_log("물을 줄 수 없는 타일입니다.")

    elif tool == "seed":
        if tile.kind not in ("tilled", "watered"):
            gs.add_log("먼저 밭을 경작하세요!")
            return
        sid = gs.selected_seed
        if gs.seeds.get(sid, 0) <= 0:
            gs.add_log("씨앗이 없습니다. 상점에서 구매하세요.")
            return
        crop = CROPS[sid]
        if crop.season != gs.season:
            gs.add_log(f"⚠  {crop.name}는 {SEASONS[crop.season]}에만 심을 수 있습니다.")
            return
        if tile.plant_id:
            gs.add_log("이미 작물이 심어져 있습니다.")
            return
        if gs.spend_energy(2):
            tile.plant_id = sid
            tile.planted_day = gs.day
            tile.growth = 0.0
            gs.seeds[sid] -= 1
            gs.gain_xp(3)
            gs.add_log(f"🌱 {crop.emoji} {crop.name} 씨앗 심기 완료.")

    elif tool == "harvest":
        if tile.is_ready:
            crop = CROPS[tile.plant_id]
            if gs.spend_energy(1):
                gs.inventory[tile.plant_id] = gs.inventory.get(tile.plant_id, 0) + 1
                gs.harvests += 1
                gs.gain_xp(8)
                gs.add_log(f"🧺 {crop.emoji} {crop.name} 수확! (판매가 {crop.sell}G)")
                tile.plant_id = None
                tile.planted_day = 0
                tile.growth = 0.0
                tile.kind = "tilled"
        else:
            gs.add_log("수확할 작물이 없습니다.")

    elif tool == "axe":
        if tile.kind == "tree":
            if gs.spend_energy(3):
                gs.resources["wood"] = gs.resources.get("wood", 0) + random.randint(2, 4)
                tile.kind = "stump"
                gs.gain_xp(5)
                gs.add_log("🪓 나무를 베었습니다. 목재 획득!")
        elif tile.kind == "stump":
            if gs.spend_energy(2):
                tile.kind = "empty"
                gs.add_log("🪓 그루터기를 제거했습니다.")
        else:
            gs.add_log("나무가 없습니다.")

    elif tool == "pickaxe":
        if tile.kind == "rock":
            if gs.spend_energy(3):
                gs.resources["stone"] = gs.resources.get("stone", 0) + random.randint(2, 4)
                tile.kind = "empty"
                gs.gain_xp(5)
                gs.add_log("⛏  바위를 캐었습니다. 돌 획득!")
        else:
            gs.add_log("바위가 없습니다.")


def sell_all(gs: GameState):
    total = 0
    for crop_id, qty in gs.inventory.items():
        if qty > 0:
            price = CROPS[crop_id].sell * qty
            total += price
            gs.add_log(f"💰 {CROPS[crop_id].emoji} {CROPS[crop_id].name} x{qty} → {price}G")
    if total:
        gs.gold += total
        gs.total_earned += total
        gs.inventory.clear()
        gs.add_log(f"💰 총 {total}G 판매 완료!")
    else:
        gs.add_log("판매할 작물이 없습니다.")


def buy_seeds(gs: GameState, crop_id: str, qty: int = 5):
    crop = CROPS[crop_id]
    cost = crop.cost * qty
    if gs.gold < cost:
        gs.add_log(f"💸 골드가 부족합니다! (필요: {cost}G)")
        return
    gs.gold -= cost
    gs.seeds[crop_id] = gs.seeds.get(crop_id, 0) + qty
    gs.add_log(f"🛒 {crop.emoji} {crop.name} 씨앗 {qty}개 구매 ({cost}G)")


# ────────────────────────────────────────────
#  렌더링 도우미
# ────────────────────────────────────────────
class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.fonts = {}
        for size in (12, 14, 16, 18, 22, 28):
            try:
                self.fonts[size] = pygame.font.SysFont("malgun gothic", size)
            except:
                self.fonts[size] = pygame.font.SysFont(None, size)
        self.hover_tile = -1
        self.shop_open = False
        self.buttons = {}   # name -> pygame.Rect

    def font(self, size=14):
        return self.fonts.get(size, self.fonts[14])

    def text(self, txt, x, y, color=None, size=14, anchor="topleft"):
        color = color or C["text"]
        surf = self.font(size).render(str(txt), True, color)
        r = surf.get_rect(**{anchor: (x, y)})
        self.screen.blit(surf, r)
        return r

    def rect(self, x, y, w, h, color, border=0, radius=4):
        pygame.draw.rect(self.screen, color, (x, y, w, h), border, border_radius=radius)

    def bar(self, x, y, w, h, ratio, fg, bg=(50, 50, 60), radius=3):
        self.rect(x, y, w, h, bg, radius=radius)
        if ratio > 0:
            self.rect(x, y, max(4, int(w * ratio)), h, fg, radius=radius)

    def button(self, name, x, y, w, h, label, active=False, color=None):
        col = color or (C["btn_active"] if active else C["btn"])
        self.rect(x, y, w, h, col, radius=6)
        pygame.draw.rect(self.screen, C["ui_border"], (x, y, w, h), 1, border_radius=6)
        self.text(label, x + w // 2, y + h // 2, size=13, anchor="center")
        r = pygame.Rect(x, y, w, h)
        self.buttons[name] = r
        return r

    def panel(self, x, y, w, h):
        self.rect(x, y, w, h, C["ui_panel"], radius=8)
        pygame.draw.rect(self.screen, C["ui_border"], (x, y, w, h), 1, border_radius=8)


# ────────────────────────────────────────────
#  타일 그리기
# ────────────────────────────────────────────
def draw_tile(ren: Renderer, tile: Tile, x, y, size, hovered=False):
    s = ren.screen

    # 배경색
    bg = {
        "empty":   C["tile_empty"],
        "tilled":  C["tile_tilled"],
        "watered": C["tile_watered"],
        "rock":    C["tile_rock"],
        "tree":    C["tile_tree"],
        "stump":   (70, 50, 30),
    }.get(tile.kind, C["tile_empty"])

    pygame.draw.rect(s, bg, (x, y, size, size), border_radius=3)

    # 작물 표시
    if tile.plant_id:
        crop = CROPS[tile.plant_id]
        g = tile.growth
        # 성장 단계별 색상 (연두→진초록→작물색)
        stage_col = (
            int(80 + 100 * g),
            int(120 + 80 * g),
            int(40),
        )
        cx, cy = x + size // 2, y + size // 2
        # 줄기
        stem_h = int(10 + g * (size * 0.4))
        pygame.draw.line(s, (60, 120, 40), (cx, cy + size // 4), (cx, cy + size // 4 - stem_h), 2)
        # 잎
        for i in range(min(3, int(g * 3) + 1)):
            lx = cx + (8 if i % 2 == 0 else -8)
            ly = cy + size // 4 - int(stem_h * (0.3 + i * 0.3))
            pygame.draw.ellipse(s, stage_col, (lx - 5, ly - 3, 10, 6))
        # 수확 가능: 과일 원 표시
        if tile.is_ready:
            pygame.draw.circle(s, crop.color, (cx, cy - 4), 8)
            pygame.draw.circle(s, (255, 255, 255), (cx, cy - 4), 8, 1)

        # 성장 게이지
        bar_y = y + size - 6
        pygame.draw.rect(s, (20, 20, 20), (x + 2, bar_y, size - 4, 4), border_radius=2)
        fill_w = int((size - 4) * g)
        bar_col = C["ready_glow"] if tile.is_ready else (80, 180, 80)
        if fill_w > 0:
            pygame.draw.rect(s, bar_col, (x + 2, bar_y, fill_w, 4), border_radius=2)

    # 바위/나무 아이콘 (간단 도형)
    cx, cy = x + size // 2, y + size // 2
    if tile.kind == "rock":
        pygame.draw.ellipse(s, (120, 120, 130), (cx - 14, cy - 8, 28, 18))
        pygame.draw.ellipse(s, (150, 150, 160), (cx - 10, cy - 12, 20, 12))
    elif tile.kind == "tree":
        pygame.draw.rect(s, (100, 60, 20), (cx - 3, cy + 4, 6, 12))
        pygame.draw.circle(s, (40, 120, 40), (cx, cy - 4), 14)
        pygame.draw.circle(s, (60, 160, 60), (cx - 4, cy - 8), 8)
    elif tile.kind == "stump":
        pygame.draw.rect(s, (100, 60, 20), (cx - 8, cy - 4, 16, 10))

    # 물 줬을 때 반짝임
    if tile.watered:
        pygame.draw.rect(s, (60, 120, 200, 60), (x, y, size, size), border_radius=3)

    # 호버 / 테두리
    border_col = C["highlight"] if hovered else C["grid_line"]
    border_w = 2 if hovered else 1
    pygame.draw.rect(s, border_col, (x, y, size, size), border_w, border_radius=3)

    # 수확 가능 글로우
    if tile.is_ready:
        glow = abs(math.sin(pygame.time.get_ticks() * 0.003)) * 80
        pygame.draw.rect(s, (80, 220, 80, int(glow)),
                         (x - 1, y - 1, size + 2, size + 2), 2, border_radius=4)


# ────────────────────────────────────────────
#  UI 패널 그리기
# ────────────────────────────────────────────
def draw_ui(ren: Renderer, gs: GameState):
    s = ren.screen
    x0, pw = UI_X, PANEL_W
    ren.buttons.clear()

    # 배경
    ren.rect(x0 - 4, FARM_Y - 4, pw + 8, FARM_ROWS * TILE_SIZE + 8, C["ui_bg"], radius=8)

    y = FARM_Y

    # ── 상태 ──
    ren.panel(x0, y, pw, 80)
    ren.text("📊 현황", x0 + 8, y + 6, C["text_blue"], 14)

    ren.text(f"💰 {gs.gold}G", x0 + 8,  y + 26, C["text_gold"], 16)
    ren.text(f"🏆 Lv.{gs.level}", x0 + 8, y + 46, C["text_green"], 14)
    ren.text(f"수확 {gs.harvests}회", x0 + 8, y + 62, C["text_muted"], 12)

    # 에너지 바
    ren.text("⚡", x0 + pw - 90, y + 10, size=13)
    ren.bar(x0 + pw - 74, y + 14, 66, 8,
            gs.energy / gs.max_energy, C["energy_bar"])
    ren.text(f"{gs.energy}/{gs.max_energy}", x0 + pw - 74, y + 25, C["text_muted"], 11)

    # XP 바
    ren.text("XP", x0 + pw - 90, y + 40, C["text_muted"], 11)
    ren.bar(x0 + pw - 74, y + 40, 66, 6, gs.xp_ratio(), (180, 120, 240))

    y += 88

    # ── 도구 선택 ──
    ren.panel(x0, y, pw, 160)
    ren.text("🔧 도구", x0 + 8, y + 6, C["text_blue"], 14)
    ty = y + 26
    for i, (tid, tname, ticon, tdesc, tcost) in enumerate(TOOLS):
        active = gs.tool == tid
        col = int(ty + i * 22)
        ren.button(f"tool_{tid}", x0 + 4, col, pw - 8, 20,
                   f"{ticon} {tname}  (⚡{tcost})", active=active)
    y += 168

    # ── 씨앗 선택 ──
    ren.panel(x0, y, pw, 120)
    ren.text("🌱 씨앗", x0 + 8, y + 6, C["text_blue"], 14)
    avail = {k: v for k, v in gs.seeds.items() if v > 0}
    if avail:
        sy = y + 26
        for i, (sid, qty) in enumerate(avail.items()):
            crop = CROPS[sid]
            active = gs.selected_seed == sid and gs.tool == "seed"
            label = f"{crop.emoji} {crop.name} x{qty}"
            ren.button(f"seed_{sid}", x0 + 4, sy + i * 22, pw - 8, 20,
                       label, active=active)
    else:
        ren.text("씨앗 없음 - 상점에서 구매하세요", x0 + 8, y + 30, C["text_muted"], 12)
    y += 128

    # ── 인벤토리 ──
    inv_h = 90
    ren.panel(x0, y, pw, inv_h)
    ren.text("📦 인벤토리", x0 + 8, y + 6, C["text_blue"], 14)
    iy = y + 24
    for crop_id, qty in gs.inventory.items():
        if qty > 0:
            crop = CROPS[crop_id]
            ren.text(f"{crop.emoji} {crop.name}", x0 + 8, iy, size=12)
            ren.text(f"x{qty}  →{crop.sell * qty}G", x0 + pw - 8, iy,
                     C["text_gold"], 12, anchor="topright")
            iy += 16
    for rtype, qty in gs.resources.items():
        icon = "🪵" if rtype == "wood" else "🪨"
        ren.text(f"{icon} {rtype}", x0 + 8, iy, size=12)
        ren.text(f"x{qty}", x0 + pw - 8, iy, C["text_muted"], 12, anchor="topright")
        iy += 16
    y += inv_h + 6

    # ── 액션 버튼 ──
    ren.button("sell_all", x0, y, pw, 26,
               "💰 전부 판매", color=(70, 40, 40))
    y += 32
    ren.button("shop", x0, y, pw, 26,
               "🛒 씨앗 상점", color=(40, 55, 75))
    y += 32
    ren.button("next_day", x0, y, pw, 30,
               "🌙 다음 날로 (N)", color=(40, 40, 80))
    y += 38

    # ── 로그 ──
    log_h = max(60, FARM_Y + FARM_ROWS * TILE_SIZE - y)
    ren.panel(x0, y, pw, log_h)
    ren.text("📋 로그", x0 + 8, y + 4, C["text_blue"], 12)
    ly = y + 20
    for msg in gs.log[:max(1, (log_h - 24) // 14)]:
        ren.text(msg, x0 + 6, ly, C["text_muted"], 11)
        ly += 14


# ────────────────────────────────────────────
#  상점 오버레이
# ────────────────────────────────────────────
def draw_shop(ren: Renderer, gs: GameState, season_crops: list):
    sw, sh = 420, 300
    sx = (SCREEN_W - sw) // 2
    sy = (SCREEN_H - sh) // 2

    # 반투명 오버레이
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    ren.screen.blit(overlay, (0, 0))

    ren.rect(sx, sy, sw, sh, C["ui_panel"], radius=10)
    pygame.draw.rect(ren.screen, C["highlight"], (sx, sy, sw, sh), 2, border_radius=10)
    ren.text(f"🛒 씨앗 상점  ({SEASONS[gs.season]} 판매중)", sx + 12, sy + 10, C["text_gold"], 16)
    ren.text(f"보유 골드: {gs.gold}G", sx + sw - 12, sy + 10, C["text_gold"], 14, anchor="topright")

    y = sy + 38
    for crop_id in season_crops:
        crop = CROPS[crop_id]
        owned = gs.seeds.get(crop_id, 0)
        ren.text(f"{crop.emoji} {crop.name}", sx + 12, y + 2, size=14)
        ren.text(f"씨앗 {crop.cost}G  |  수확 {crop.sell}G  |  {crop.days}일", sx + 100, y + 4, C["text_muted"], 12)
        ren.text(f"보유 x{owned}", sx + 300, y + 4, C["text_blue"], 12)
        ren.button(f"buy_{crop_id}", sx + 340, y, 70, 22, f"구매×5", color=(40, 70, 40))
        y += 32

    ren.button("close_shop", sx + sw // 2 - 40, sy + sh - 36, 80, 26, "닫기", color=(70, 40, 40))


# ────────────────────────────────────────────
#  상단 HUD
# ────────────────────────────────────────────
def draw_hud(ren: Renderer, gs: GameState):
    s = ren.screen
    season_col = SEASON_COLORS[gs.season]
    ren.rect(0, 0, SCREEN_W, FARM_Y - 2, C["ui_bg"])
    pygame.draw.line(s, C["ui_border"], (0, FARM_Y - 2), (SCREEN_W, FARM_Y - 2))

    # 계절/날짜
    ren.text(f"{SEASONS[gs.season]}  {gs.day}일", 12, 14, season_col, 20)
    # 조작 힌트
    hints = "[클릭] 도구 사용   [N] 다음 날   [1-6] 도구 선택   [ESC] 종료"
    ren.text(hints, SCREEN_W // 2, 18, C["text_muted"], 12, anchor="midtop")
    # 총 수익
    ren.text(f"총 수익: {gs.total_earned}G", SCREEN_W - 12, 18, C["text_gold"], 14, anchor="topright")


# ────────────────────────────────────────────
#  메인 루프
# ────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("🌾 농장 경영 게임")
    clock = pygame.time.Clock()

    gs = GameState()
    gs.tiles = make_tiles()
    gs.add_log("🌅 농장에 오신 걸 환영합니다!")
    gs.add_log("💡 괭이로 경작 → 씨앗 심기 → 물주기 → 수확 → 판매!")

    ren = Renderer(screen)
    shop_open = False

    running = True
    while running:
        mx, my = pygame.mouse.get_pos()

        # 호버 타일 계산
        hover_tile = -1
        for i in range(FARM_COLS * FARM_ROWS):
            r, c = divmod(i, FARM_COLS)
            tx = FARM_X + c * TILE_SIZE
            ty = FARM_Y + r * TILE_SIZE
            if tx <= mx < tx + TILE_SIZE and ty <= my < ty + TILE_SIZE:
                hover_tile = i
                break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_n:
                    advance_day(gs)
                    shop_open = False
                # 도구 단축키 1-6
                for i, (tid, *_) in enumerate(TOOLS):
                    if event.key == getattr(pygame, f"K_{i+1}", None):
                        gs.tool = tid

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = mx, my

                if shop_open:
                    # 상점 버튼
                    for name, rect in ren.buttons.items():
                        if rect.collidepoint(clicked):
                            if name.startswith("buy_"):
                                buy_seeds(gs, name[4:], 5)
                            elif name == "close_shop":
                                shop_open = False
                    continue

                # 농장 타일 클릭
                if hover_tile >= 0:
                    use_tool(gs, hover_tile)
                    continue

                # UI 버튼 클릭
                for name, rect in ren.buttons.items():
                    if rect.collidepoint(clicked):
                        if name.startswith("tool_"):
                            gs.tool = name[5:]
                        elif name.startswith("seed_"):
                            gs.selected_seed = name[5:]
                            gs.tool = "seed"
                        elif name == "sell_all":
                            sell_all(gs)
                        elif name == "shop":
                            shop_open = True
                        elif name == "next_day":
                            advance_day(gs)

        # ── 그리기 ──
        screen.fill(C["bg"])
        draw_hud(ren, gs)

        # 농장 배경
        farm_w = FARM_COLS * TILE_SIZE
        farm_h = FARM_ROWS * TILE_SIZE
        pygame.draw.rect(screen, (20, 30, 12), (FARM_X - 2, FARM_Y - 2, farm_w + 4, farm_h + 4),
                         border_radius=6)

        for i, tile in enumerate(gs.tiles):
            r, c = divmod(i, FARM_COLS)
            tx = FARM_X + c * TILE_SIZE
            ty = FARM_Y + r * TILE_SIZE
            draw_tile(ren, tile, tx, ty, TILE_SIZE, hovered=(i == hover_tile))

        draw_ui(ren, gs)

        if shop_open:
            season_crops = [k for k, v in CROPS.items() if v.season == gs.season]
            draw_shop(ren, gs, season_crops)

        # 도구 툴팁
        if hover_tile >= 0 and not shop_open:
            tool_info = next((t for t in TOOLS if t[0] == gs.tool), None)
            if tool_info:
                tip = f"{tool_info[2]} {tool_info[1]}: {tool_info[3]}"
                ren.text(tip, mx + 12, my - 18, C["highlight"], 12)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()