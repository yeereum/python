"""
단어 배열 퍼즐 자동 클릭기 (연속 감시 버전)
===========================================

동작 흐름
---------
1. REFERENCE_REGION(정답 문장이 표시되는 영역)을 OCR로 읽어 "정답 문장"을 얻는다.
2. WORD_REGION(뒤섞인 단어 버튼들이 있는 영역)을 OCR로 읽어 단어+좌표를 얻는다.
3. 정답 문장의 단어 순서에 맞춰, 인식된 버튼들을 0.5초 간격으로 순서대로 클릭한다.
4. 클릭 도중/이후 WORD_REGION에 단어가 안 보이면:
   - 몇 초간(WAIT_TIMEOUT) 짧은 간격으로 재확인한다.
   - 그 사이 새 단어(다음 문제)가 나타나면 그 문제로 자동 이어서 진행한다.
   - 시간 내에 아무것도 안 나타나면 프로그램을 정지한다.
5. 사용자가 임의로 "다음 문장"으로 넘기는 것도 3~4번 로직으로 자동 감지된다.
   (REFERENCE_REGION의 텍스트가 바뀌면 새 문제로 인식) — 별도로 스크립트를
   다시 실행할 필요가 없다.

사전 준비
---------
pip install pytesseract pyautogui mss pillow
+ Tesseract OCR 엔진 설치 (Windows: UB-Mannheim 빌드, Mac: brew install tesseract)

가장 먼저 할 일
---------------
REFERENCE_REGION과 WORD_REGION 좌표를 실제 앱 화면에 맞게 수정하세요.
좌표를 모르면 스크립트 맨 아래 `print_mouse_position()` 함수로 마우스를
움직여가며 좌표를 확인할 수 있습니다.
"""

import time
import pyautogui
import pytesseract
from PIL import Image
import mss

# ── 설정 ──────────────────────────────────────────────────────────
# 정답 문장이 표시되는 화면 영역 (예: 상단에 "이 문장을 만드세요: ..." 처럼 뜨는 부분)
REFERENCE_REGION = {"left": 100, "top": 100, "width": 800, "height": 100}

# 뒤섞인 단어 버튼들이 표시되는 화면 영역
WORD_REGION = {"left": 100, "top": 300, "width": 800, "height": 300}

CLICK_DELAY = 0.5          # 단어 클릭 사이 간격(초) — 요청하신 0.5초
POLL_INTERVAL = 0.5        # 단어가 안 보일 때 재확인 간격(초)
WAIT_TIMEOUT = 6.0         # 이 시간 동안 단어가 안 나타나면 정지(초)
OCR_LANG = "kor+eng"
MIN_CONF = 40              # OCR 신뢰도 임계값


# ── 화면 캡처 + OCR 공통 함수 ─────────────────────────────────────
def capture_region(region):
    with mss.mss() as sct:
        shot = sct.grab(region)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    return img


def ocr_plain_text(region):
    """REFERENCE_REGION처럼 '문장 하나'를 통으로 읽을 때 사용."""
    img = capture_region(region)
    text = pytesseract.image_to_string(img, lang=OCR_LANG).strip()
    return text


def ocr_words_with_coords(region):
    """WORD_REGION처럼 '흩어진 단어 버튼들'의 텍스트+좌표를 읽을 때 사용."""
    img = capture_region(region)
    data = pytesseract.image_to_data(
        img, lang=OCR_LANG, output_type=pytesseract.Output.DICT
    )
    words = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        conf = int(data["conf"][i]) if data["conf"][i] != "-1" else -1
        if not text or conf < MIN_CONF:
            continue
        x = data["left"][i] + data["width"][i] // 2 + region["left"]
        y = data["top"][i] + data["height"][i] // 2 + region["top"]
        words.append({"text": text, "x": x, "y": y})
    return words


# ── 정답 문장 순서에 맞춰 버튼 매칭 ────────────────────────────────
def match_words_to_reference(reference_sentence, detected_words):
    """
    reference_sentence의 단어 순서대로 detected_words에서 좌표를 찾아 반환.
    detected_words에 정답 단어가 전부 없으면 None (아직 버튼이 다 안 떴다고 판단).
    """
    tokens = reference_sentence.split()
    if not tokens:
        return None

    remaining = list(detected_words)
    ordered = []
    for token in tokens:
        match = next((w for w in remaining if w["text"] == token), None)
        if match is None:
            return None  # 정답 단어 중 하나라도 화면에서 못 찾으면 아직 준비 안 된 것
        ordered.append(match)
        remaining.remove(match)
    return ordered


# ── 한 문제를 클릭으로 완료 ────────────────────────────────────────
def click_sentence(ordered_words):
    for w in ordered_words:
        pyautogui.click(w["x"], w["y"])
        print(f"  클릭: '{w['text']}' @ ({w['x']}, {w['y']})")
        time.sleep(CLICK_DELAY)


# ── 메인 감시 루프 (상태기계) ──────────────────────────────────────
def run():
    print("감시를 시작합니다. Ctrl+C로 언제든 중단할 수 있습니다.")
    last_reference = None
    no_word_elapsed = 0.0

    while True:
        reference_sentence = ocr_plain_text(REFERENCE_REGION)
        detected_words = ocr_words_with_coords(WORD_REGION)

        is_new_reference = bool(reference_sentence) and reference_sentence != last_reference
        ordered = None
        if reference_sentence:
            ordered = match_words_to_reference(reference_sentence, detected_words)

        if ordered is not None and is_new_reference:
            # 새 문제 등장 + 버튼도 다 준비됨 -> 클릭 시작
            print(f"\n새 문제 인식: '{reference_sentence}'")
            click_sentence(ordered)
            last_reference = reference_sentence
            no_word_elapsed = 0.0
            print("이 문제 완료. 다음 문제를 기다립니다...")

        elif ordered is None and (not detected_words):
            # 화면에 단어가 하나도 안 보임 -> 대기하며 재확인
            no_word_elapsed += POLL_INTERVAL
            print(f"단어 버튼이 안 보입니다. 대기 중... ({no_word_elapsed:.1f}s / {WAIT_TIMEOUT}s)")
            if no_word_elapsed >= WAIT_TIMEOUT:
                print("시간 초과: 더 이상 새 문제가 나타나지 않아 프로그램을 정지합니다.")
                break
            time.sleep(POLL_INTERVAL)

        else:
            # 단어는 보이지만 아직 정답 문장과 매칭이 안 됨(버튼이 로딩 중) -> 짧게 재시도
            time.sleep(POLL_INTERVAL)

    print("종료되었습니다.")


# ── 좌표 확인용 보조 도구 ──────────────────────────────────────────
def print_mouse_position(duration=15):
    """
    REFERENCE_REGION / WORD_REGION 좌표를 잡을 때 사용하세요.
    실행 후 duration초 동안 마우스를 원하는 지점으로 움직이면
    현재 좌표가 콘솔에 계속 출력됩니다.
    """
    print(f"{duration}초 동안 마우스 좌표를 출력합니다. 원하는 지점 위로 움직여보세요.")
    end = time.time() + duration
    try:
        while time.time() < end:
            x, y = pyautogui.position()
            print(f"\r현재 좌표: ({x}, {y})   ", end="")
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    print()


if __name__ == "__main__":
    # 좌표를 아직 모른다면 아래 줄의 주석을 풀고 먼저 실행해서 좌표를 확인하세요.
    # print_mouse_position()

    run()
