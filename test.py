"""
단어 배열 퍼즐 자동 풀이 스크립트
==================================

동작 원리
---------
1. 화면(또는 지정한 영역)을 캡처한다.
2. OCR(Tesseract)로 화면에 흩어진 단어들의 텍스트와 좌표(bounding box)를 추출한다.
3. 추출된 단어들을 올바른 문장 순서로 정렬한다.
   - 기본: Claude API를 호출해 올바른 어순을 물어봄 (가장 정확)
   - 대안: 규칙 기반(대문자로 시작하는 단어를 문장 시작으로, 마침표 있는 단어를 끝으로 등)
4. 정렬된 순서대로 각 단어의 화면 좌표를 자동으로 클릭한다 (pyautogui).

사전 준비
---------
1. Python 패키지 설치:
   pip install pytesseract pyautogui mss pillow anthropic

2. Tesseract OCR 엔진 설치 (별도 프로그램, pytesseract는 이걸 감싸는 래퍼일 뿐입니다):
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki 에서 설치 후,
     아래 TESSERACT_CMD 경로를 실제 설치 경로로 수정하세요.
   - Mac: brew install tesseract

3. (선택) Claude API를 쓰려면 환경변수 ANTHROPIC_API_KEY를 설정하세요.
   설정하지 않으면 규칙 기반 정렬로 자동 대체됩니다.

주의사항
--------
- 이 스크립트는 여러분의 PC에서 로컬로 실행하는 용도입니다 (이 대화 환경이 아님).
- SCREEN_REGION을 실제 퍼즐이 표시되는 화면 좌표에 맞게 수정해야 인식률이 올라갑니다.
- 앱마다 폰트/배경이 달라 OCR 인식률이 다를 수 있습니다. 필요하면 이미지 전처리
  (흑백 변환, 대비 조절 등)를 추가하세요.
"""

import time
import re
import os

import pyautogui
import pytesseract
from PIL import Image
import mss

# ── 설정 ──────────────────────────────────────────────────────────
# Windows에서 Tesseract 경로를 직접 지정해야 할 수도 있습니다. 예:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 캡처할 화면 영역 (단어들이 표시되는 부분만 지정하면 인식률과 속도가 좋아집니다)
# left, top, width, height. None이면 전체 화면을 캡처합니다.
SCREEN_REGION = None  # 예: {"left": 100, "top": 400, "width": 800, "height": 300}

# 클릭 사이 지연 시간(초). 너무 빠르면 앱이 클릭을 놓칠 수 있습니다.
CLICK_DELAY = 0.4

# 실행 전 대기 시간(초). 이 사이에 퍼즐 화면을 준비하세요.
START_DELAY = 3


# ── 1. 화면 캡처 ──────────────────────────────────────────────────
def capture_screen(region=None):
    with mss.mss() as sct:
        monitor = region if region else sct.monitors[1]
        shot = sct.grab(monitor)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    return img, monitor


# ── 2. OCR로 단어 + 좌표 추출 ─────────────────────────────────────
def extract_words(img, offset=(0, 0), lang="kor+eng"):
    """
    반환: [{"text": 단어, "x": 화면절대x, "y": 화면절대y}, ...]
    x, y는 해당 단어 박스의 중심 좌표(클릭할 지점)입니다.
    """
    data = pytesseract.image_to_data(
        img, lang=lang, output_type=pytesseract.Output.DICT
    )

    words = []
    n = len(data["text"])
    for i in range(n):
        text = data["text"][i].strip()
        conf = int(data["conf"][i]) if data["conf"][i] != "-1" else -1
        if not text or conf < 40:  # 신뢰도 낮은 조각 제외
            continue
        x = data["left"][i] + data["width"][i] // 2 + offset[0]
        y = data["top"][i] + data["height"][i] // 2 + offset[1]
        words.append({"text": text, "x": x, "y": y})
    return words


# ── 3-A. Claude API로 올바른 어순 판단 (권장) ─────────────────────
def order_words_with_claude(words):
    """
    words: [{"text": ..., "x": ..., "y": ...}, ...]
    반환: 올바른 순서로 재배열된 같은 리스트
    """
    try:
        import anthropic
    except ImportError:
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    client = anthropic.Anthropic(api_key=api_key)
    word_list = [w["text"] for w in words]

    prompt = (
        "다음은 뒤섞인 단어 목록입니다. 문법적으로 올바른 하나의 문장이 되도록 "
        "순서를 정렬해서, 정렬된 단어만 쉼표로 구분해 한 줄로 출력하세요. "
        "설명이나 다른 텍스트는 출력하지 마세요.\n\n"
        f"단어 목록: {word_list}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    result_text = response.content[0].text.strip()
    ordered_texts = [t.strip() for t in result_text.split(",")]

    # 텍스트 -> 원본 단어 객체 매핑 (동일 단어가 여러 개일 경우를 대비해 하나씩 소비)
    remaining = list(words)
    ordered = []
    for token in ordered_texts:
        for w in remaining:
            if w["text"] == token:
                ordered.append(w)
                remaining.remove(w)
                break
    # 매칭 안 된 단어가 있으면 실패로 간주
    if len(ordered) != len(words):
        return None
    return ordered


# ── 3-B. 규칙 기반 정렬 (API 키 없을 때 대체용, 정확도 낮음) ──────
def order_words_by_heuristic(words):
    def score(w):
        t = w["text"]
        starts_capital = t[0].isupper() if t and t[0].isalpha() else False
        ends_punct = bool(re.search(r"[.!?]$", t))
        return (not starts_capital, ends_punct)

    return sorted(words, key=score)


# ── 4. 순서대로 클릭 ──────────────────────────────────────────────
def click_words_in_order(ordered_words, delay=CLICK_DELAY):
    for w in ordered_words:
        pyautogui.click(w["x"], w["y"])
        print(f"클릭: '{w['text']}' @ ({w['x']}, {w['y']})")
        time.sleep(delay)


# ── 메인 ──────────────────────────────────────────────────────────
def main():
    print(f"{START_DELAY}초 후 캡처를 시작합니다. 퍼즐 화면을 준비하세요...")
    time.sleep(START_DELAY)

    img, monitor = capture_screen(SCREEN_REGION)
    offset = (monitor["left"], monitor["top"]) if SCREEN_REGION else (0, 0)

    words = extract_words(img, offset=offset)
    if not words:
        print("단어를 인식하지 못했습니다. SCREEN_REGION과 언어 설정을 확인하세요.")
        return

    print("인식된 단어:", [w["text"] for w in words])

    ordered = order_words_with_claude(words)
    if ordered is None:
        print("Claude API 미사용/실패 — 규칙 기반 정렬로 대체합니다.")
        ordered = order_words_by_heuristic(words)

    print("정렬된 순서:", [w["text"] for w in ordered])

    click_words_in_order(ordered)
    print("완료.")


if __name__ == "__main__":
    main()
