"""
단어 배열 퍼즐 자동 클릭기 (오류 검증 + 자동 복구 버전)
========================================================

v2 대비 추가된 부분
--------------------
- 매 클릭 후 ANSWER_REGION(조립되고 있는 문장이 표시되는 영역)을 OCR로 확인해서
  방금 클릭한 단어가 "정답 순서대로 정확히" 들어갔는지 검증한다.
- 틀렸다면(엉뚱한 단어가 들어갔거나, 순서가 어긋났거나, 오타 인식 등):
    1) 조립 영역에서 틀리기 시작한 지점까지 단어를 하나씩 되돌린다(undo).
    2) 그 지점(= 마지막으로 확인된 정답 위치)부터 다시 시도한다.
    3) 같은 지점에서 반복 실패하면(MAX_RETRIES_PER_WORD 초과) 프로그램을 정지한다.
- 매 단어를 클릭하기 전, 버튼 풀(WORD_REGION)을 다시 스캔해서 좌표를 새로
  찾는다. 버튼 위치가 매 클릭마다 재배치되는 앱에도 대응하기 위함이다.

전제 조건 (중요)
-----------------
"되돌리기"는 [조립된 문장에서 단어를 다시 탭하면 풀로 돌아간다]는 동작을
가정하고 구현했습니다. 여러분의 앱이 이렇게 동작하지 않는다면(예: 전체를
한번에 지우는 "지우기" 버튼만 있는 경우) 아래 `undo_last_answer_word()`를
`reset_answer_full()`로 교체하세요. 주석으로 예시를 남겨뒀습니다.

사전 준비
---------
pip install pytesseract pyautogui mss pillow
+ Tesseract OCR 엔진 설치 (kor+eng 언어팩 포함)
"""

import time
import pyautogui
import pytesseract
from PIL import Image
import mss

# ── 설정 ──────────────────────────────────────────────────────────
REFERENCE_REGION = {"left": 100, "top": 100, "width": 800, "height": 100}  # 정답 문장 표시 영역
WORD_REGION      = {"left": 100, "top": 300, "width": 800, "height": 200}  # 뒤섞인 단어 버튼 영역
ANSWER_REGION    = {"left": 100, "top": 220, "width": 800, "height": 80}   # 조립 중인 문장 표시 영역

CLICK_DELAY   = 0.5   # 정상 클릭 사이 간격(초)
VERIFY_DELAY  = 0.25  # 클릭 후 화면 갱신을 기다렸다가 검증하기까지 대기(초)
UNDO_DELAY    = 0.3   # 되돌리기 클릭 사이 간격(초)
POLL_INTERVAL = 0.5   # 버튼/문제가 안 보일 때 재확인 간격(초)
WAIT_TIMEOUT  = 6.0   # 새 문제가 이만큼(초) 안 나타나면 정지
MAX_RETRIES_PER_WORD = 3  # 같은 단어 위치에서 이 횟수 넘게 실패하면 정지

OCR_LANG = "kor+eng"
MIN_CONF = 40


# ── 화면 캡처 + OCR 공통 함수 ─────────────────────────────────────
def capture_region(region):
    with mss.mss() as sct:
        shot = sct.grab(region)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def ocr_plain_text(region):
    img = capture_region(region)
    return pytesseract.image_to_string(img, lang=OCR_LANG).strip()


def ocr_words_with_coords(region):
    """텍스트+좌표+화면상 읽는 순서를 함께 반환 (버튼 풀, 조립 영역 공용)."""
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
    return words  # Tesseract 기본 순서 = 대략 좌->우, 위->아래 (읽는 순서)


# ── 버튼 풀에서 특정 단어 찾기 ─────────────────────────────────────
def find_word_button(target_text, exclude_coords=None):
    """
    WORD_REGION에서 target_text와 일치하는 버튼 좌표를 찾는다.
    같은 텍스트가 여러 개 있을 수 있으므로, 이미 실패했던 좌표(exclude_coords)는
    제외하고 다른 인스턴스를 시도할 수 있게 한다.
    """
    candidates = [w for w in ocr_words_with_coords(WORD_REGION) if w["text"] == target_text]
    if exclude_coords:
        candidates = [w for w in candidates if (w["x"], w["y"]) not in exclude_coords]
    return candidates[0] if candidates else None


# ── 조립 영역 상태 읽기 ────────────────────────────────────────────
def get_answer_words():
    return ocr_words_with_coords(ANSWER_REGION)


# ── 되돌리기 ──────────────────────────────────────────────────────
def undo_last_answer_word():
    """
    조립 영역의 마지막 단어를 클릭해서 풀로 되돌린다.
    (전제: 조립된 단어를 탭하면 되돌아가는 UI)
    """
    current = get_answer_words()
    if not current:
        return
    last = current[-1]
    pyautogui.click(last["x"], last["y"])
    print(f"  되돌리기: '{last['text']}' 제거")
    time.sleep(UNDO_DELAY)


# 대안: 전체 지우기 버튼이 따로 있는 앱이라면 이걸 대신 쓰세요.
# RESET_BUTTON_COORD = (500, 250)  # "지우기" 버튼 좌표로 수정
# def reset_answer_full():
#     pyautogui.click(*RESET_BUTTON_COORD)
#     time.sleep(UNDO_DELAY)


def undo_to_length(target_length):
    """조립 영역의 단어 개수가 target_length가 될 때까지 마지막 단어를 계속 제거."""
    while True:
        current = get_answer_words()
        if len(current) <= target_length:
            break
        undo_last_answer_word()


# ── 한 문장을 검증하며 클릭 (핵심 로직) ────────────────────────────
def solve_sentence(reference_tokens):
    """
    reference_tokens 순서대로 버튼을 클릭하되, 매 클릭 후 조립 영역을 검증한다.
    틀리면 해당 지점까지 되돌리고 같은 지점부터 재시도한다.
    반환값: True(완료) / False(복구 실패로 중단)
    """
    index = 0
    retries_at_index = 0
    failed_coords_at_index = []  # 같은 지점에서 잘못 클릭했던 좌표 기록 (동일 텍스트 중복 버튼 대비)
    button_wait_elapsed = 0.0

    while index < len(reference_tokens):
        target = reference_tokens[index]
        btn = find_word_button(target, exclude_coords=failed_coords_at_index)

        if btn is None:
            # 아직 해당 단어 버튼이 화면에 안 떴을 수 있음 -> 짧게 대기 후 재시도
            button_wait_elapsed += POLL_INTERVAL
            if button_wait_elapsed >= WAIT_TIMEOUT:
                print(f"'{target}' 버튼을 끝내 찾지 못했습니다. 중단합니다.")
                return False
            time.sleep(POLL_INTERVAL)
            continue
        button_wait_elapsed = 0.0

        pyautogui.click(btn["x"], btn["y"])
        time.sleep(VERIFY_DELAY)

        answer_words = get_answer_words()
        answer_texts = [w["text"] for w in answer_words]
        expected_prefix = reference_tokens[: index + 1]

        if answer_texts == expected_prefix:
            print(f"[{index + 1}/{len(reference_tokens)}] '{target}' 정상 배치 확인")
            index += 1
            retries_at_index = 0
            failed_coords_at_index = []
            time.sleep(max(0.0, CLICK_DELAY - VERIFY_DELAY))
        else:
            print(f"오류 감지! 기대: {expected_prefix} / 실제: {answer_texts}")
            retries_at_index += 1
            failed_coords_at_index.append((btn["x"], btn["y"]))

            if retries_at_index > MAX_RETRIES_PER_WORD:
                print(f"'{target}' 위치에서 {MAX_RETRIES_PER_WORD}회 넘게 실패 — 프로그램을 정지합니다.")
                return False

            print(f"  복구 중: {index}개까지만 남기고 되돌립니다...")
            undo_to_length(index)  # 마지막으로 확인됐던 정답 지점까지 되돌림
            # index는 그대로 유지 -> 같은 단어부터 재시도 (while 루프 처음으로)

    print("문장 조립 완료.")
    return True


# ── 메인 감시 루프 ─────────────────────────────────────────────────
def run():
    print("감시를 시작합니다. Ctrl+C로 언제든 중단할 수 있습니다.")
    last_reference = None
    no_ref_elapsed = 0.0

    while True:
        reference_sentence = ocr_plain_text(REFERENCE_REGION)

        if reference_sentence and reference_sentence != last_reference:
            print(f"\n새 문제 인식: '{reference_sentence}'")
            tokens = reference_sentence.split()
            success = solve_sentence(tokens)
            if not success:
                break
            last_reference = reference_sentence
            no_ref_elapsed = 0.0
            print("다음 문제를 기다립니다...")
        else:
            no_ref_elapsed += POLL_INTERVAL
            if no_ref_elapsed >= WAIT_TIMEOUT and not reference_sentence:
                print("시간 초과: 더 이상 새 문제가 나타나지 않아 프로그램을 정지합니다.")
                break
            time.sleep(POLL_INTERVAL)

    print("종료되었습니다.")


# ── 좌표 확인용 보조 도구 ──────────────────────────────────────────
def print_mouse_position(duration=15):
    print(f"{duration}초 동안 마우스 좌표를 출력합니다.")
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
    # 좌표(REFERENCE_REGION / WORD_REGION / ANSWER_REGION)를 모르면
    # 아래 줄 주석을 풀고 먼저 실행해서 확인하세요.
    # print_mouse_position()

    run()
