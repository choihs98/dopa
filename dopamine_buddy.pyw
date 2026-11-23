#!/usr/bin/env python3
"""도파미 v6 - 작고 통통한 흰 털뭉치 낙서 캐릭터. 화면을 폴짝폴짝 돌아다니며 도파민 썰을 푼다.

실행:  더블클릭 (.pyw 라서 콘솔 창이 뜨지 않음)
조작:  클릭 = 아야! 하고 뒤로 물러남 / 가만히 길게 누르기 = 대화창 열기 / 드래그 = 들어서 옮기기
       (가끔 마우스에 매달림, 알아서 15~35초마다 썰을 풂)
채팅:  같은 폴더에 api_key.txt(Anthropic API 키 한 줄) 또는 환경변수 ANTHROPIC_API_KEY 필요
종료:  빠르게 5번 연타하면 삐져서 집에 감 (또는 작업 관리자에서 pythonw 종료)
썰:    같은 폴더에 stories.txt(한 줄에 하나)를 두면 기본 썰에 추가됨
기준:  Windows (투명 배경은 Windows에서만 동작). 추가 설치 없음, 표준 라이브러리만 사용.
"""
import json
import math
import os
import queue
import random
import sys
import threading
import time
import urllib.error
import urllib.request
import tkinter as tk
import tkinter.font as tkfont

try:  # 고해상도 화면에서 흐려지지 않게
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ---- 크기: SC 를 줄이면 더 작아짐 (그림 코드는 원래 크기로 그리고 SC배로 줄여 표시) ----
SC = 0.62
KEY = "#010203"              # 이 색은 투명 처리됨
WW, HH = 320, 300            # 실제 창 크기 (말풍선 공간 포함, 대부분 투명)
GR = HH - 8                  # 창 안에서 바닥 y (실제 px)
LCX, GROUND = 170, 340       # 그림 코드의 논리 좌표 기준점
BUBBLE_BOTTOM = 190          # 말풍선 아래쪽 (논리 y)
FRAME_MS = 20
RX, RY = 52, 48              # 몸 반지름 (논리)
HOP_H, HOP_DUR, WIND_DUR, HOP_LEN = 40, 0.42, 0.16, 110
HANG_H = 134                 # 매달릴 때 바닥~손 높이 (논리)
EDGE_PAD = WW // 2 - 45      # 화면 가장자리까지 캐릭터가 갈 수 있게

BODY, INK, PAPER = "#ffffff", "#161616", "#fffef8"
TONGUE, DROOL, MOUTH = "#ff7f9c", "#c6e9ff", "#5b1f2f"
BOIL = True                  # 낙서 선이 살짝 일렁이게 (끄려면 False)

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-5-5"   # 빠르고 저렴한 모델. 바꾸려면 여기만 수정
PERSONA = (
    "너는 '도파미'야. 컴퓨터 화면 위를 돌아다니는 둥글통통한 흰 털뭉치 낙서 캐릭터이고, "
    "지금 사용자는 컴퓨터로 그림을 그리는 중이야. 성격은 어리숙하고 멍청한 척하지만 순수하고 다정해. "
    "항상 한국어 반말로, 1~3문장 이내로 아주 짧게 대답해. 가끔 '어...', '헤헤' 같은 말을 섞어. "
    "도파민이나 뇌과학 이야기가 나오면 멍청한 척하면서도 내용은 정확하게 쉽게 설명하고, 모르면 모른다고 해. "
    "이모지와 마크다운은 쓰지 마. 위험하거나 부적절한 요청은 도파미답게 어리둥절해하며 부드럽게 넘겨."
)
TALK_GAP = (15, 35)          # 말하는 간격(초)

GREETING = "어... 안녕? 나 도파미야... 맞나? 그림 그리는 동안 도파민 썰 풀어줄게."
PREFIX = ["", "", "어... ", "음냐, ", "아 맞다! ", "헤헤, ", "어어? "]
SUFFIX = ["", "", "", " 헤헤", "... 맞나?", " (아마도)"]
SILLY = [
    "어... 나 방금 뭐 말하려고 했지?",
    "도파민? 그거 먹는 거 아니었어? ...아니구나.",
    "방금 침 흘렸다... 아니야, 안 흘렸어.",
    "나 오늘 천재인 것 같아. 아니다, 기분 탓이다.",
    "이 선은... 내가 그은 건가? 네가 그은 건가?",
    "그림 잘 그리네... 나는 못 그리는데. 헤헤.",
    "어? 마우스 포인터다. 매달리고 싶다.",
    "배고파... 아, 이게 기대 도파민인가?",
]

STORIES = [
    "도파민이 '행복 호르몬'이라고 알고 있지? 사실은 '기대 호르몬'에 가까워. 받을 때보다 기대할 때 더 반응한대.",
    "1954년에 쥐 뇌에 자극 레버를 달아줬더니 밥도 안 먹고 계속 눌렀대. 보상 회로의 힘이 이 정도야.",
    "원숭이 실험에서 보상이 예상보다 크면 도파민 신호가 늘고, 예상대로면 조용했대. 핵심은 '놀람'이야.",
    "숏폼이랑 뽑기가 끊기 어려운 건 언제 터질지 모르는 '가변 보상' 때문이야. 기대감이 계속 유지되거든.",
    "그림 막힐 땐 2분만 낙서해봐. 시작이 어려운 건 보상이 너무 멀어서야. 선 하나가 첫 보상!",
    "작업을 잘게 쪼개서 하나씩 체크하면 작은 보상이 연달아 생겨서 계속하기 쉬워진대. 레이어 하나 = 체크 하나!",
    "'도파민 디톡스'는 이름이 좀 과장이야. 도파민을 끊을 순 없고, 자극적인 습관을 줄이는 쪽에 가까워.",
    "목표에 가까워질수록 도파민이 점점 올라간다는 쥐 실험이 있어. 마감 직전에 집중력 터지는 이유일지도?",
    "운동하면 도파민 쪽이 활발해진다고 알려져 있어. 어깨 돌리면서 스트레칭 한번 어때?",
    "택배는 도착한 순간보다 '오늘 오겠지' 하고 기다리는 시간이 더 설레지? 그게 바로 기대 도파민!",
    "장바구니에 담을 때가 결제할 때보다 더 설렐 때가 있지? 기대가 보상보다 먼저 오는 거야.",
    "새로운 걸 보면 뇌가 반응한다고 해. 같은 브러시만 쓰지 말고 오늘은 새 브러시 하나 써봐!",
    "커피로 각성되는 건 주로 아데노신을 막아서래. 도파민 신호에도 간접적으로 영향을 준다고 해.",
    "완성한 그림을 보여주기 직전에 두근거리는 것도 기대 회로 덕분이야. 올리기 전이 제일 떨리지?",
    "알림이 계속 신경 쓰이는 건 '혹시 뭐 왔나?' 하는 기대 때문이야. 그림 그릴 땐 무음 어때?",
    "'한 판만 더' 하는 마음도 기대 회로 얘기야. 다음엔 더 좋은 게 나올 것 같잖아.",
    "도파민은 '좋다'보다 '원한다'에 더 가깝대. 좋아서 하는 게 아니라 원해서 계속하는 일도 있어!",
    "완벽주의 때문에 못 끝내겠으면 70%에서 한 번 저장하고 쉬어봐. 끝냈다는 작은 보상이 의외로 커.",
    "예상보다 칭찬을 크게 받으면 기분이 확 올라가잖아. 이것도 '예측 오차'로 설명돼. 오늘 그림 기대된다!",
    "도파민이 높다 낮다로 단순하게 설명하는 영상이 많은데 실제 뇌는 훨씬 복잡하대. 썰은 썰로만 들어줘.",
    "진행 막대나 체크표가 잘 먹히는 이유가 있어. 눈에 보이는 진행은 그 자체로 작은 보상이거든.",
    "자기 전에 피드 넘기다 시간 순삭된 적 있지? 끝이 없는 피드는 '멈출 신호'가 없어서 더 빠져들어.",
    "물 한 모금 마시고 와! 손도 눈도 쉬어야 선이 더 예쁘게 나와.",
    "20분마다 20초만 먼 곳 보기! 눈이 편해져야 오래 그릴 수 있어.",
]


BASE_DIR = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))


def load_extra_stories():
    """같은 폴더의 stories.txt (한 줄에 하나, # 로 시작하면 주석)를 기본 썰에 추가"""
    try:
        with open(os.path.join(BASE_DIR, "stories.txt"), encoding="utf-8") as fh:
            return [s.strip() for s in fh if s.strip() and not s.lstrip().startswith("#")]
    except Exception:
        return []


STORIES += load_extra_stories()


def load_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        try:
            with open(os.path.join(BASE_DIR, "api_key.txt"), encoding="utf-8") as fh:
                key = fh.read().strip()
        except Exception:
            key = ""
    return key


def ask_claude(history, key):
    """(성공 여부, 답변 또는 오류 종류) 반환. 백그라운드 스레드에서 호출됨"""
    body = json.dumps({"model": MODEL, "max_tokens": 200, "system": PERSONA, "messages": history}).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, headers={
        "content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()
        return (True, text) if text else (False, "empty")
    except urllib.error.HTTPError as e:
        return False, {401: "key", 403: "key", 404: "model", 429: "rate"}.get(e.code, f"http {e.code}")
    except Exception as e:  # 네트워크 오류 등
        return False, f"net {type(e).__name__}"


def rrect_pts(x0, y0, x1, y1, r):
    pts = []
    for cx_, cy_, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(5):
            a = math.radians(a0 + 90 * k / 4)
            pts += [cx_ + r * math.cos(a), cy_ + r * math.sin(a)]
    return pts


def wobble(pts, seed, amp, closed):
    rnd = random.Random(seed)
    out = []
    for i in range(0, len(pts), 2):
        out += [pts[i] + rnd.uniform(-amp, amp), pts[i + 1] + rnd.uniform(-amp, amp)]
    if closed:
        out += out[:2]
    return out


def pen(c, pts, seed, width=2.5, amp=1.0, closed=True):
    """검은 펜으로 대충 두 번 덧그린 듯한 선"""
    c.create_line(wobble(pts, seed, amp, closed), fill=INK, width=width, joinstyle="round", capstyle="round")
    c.create_line(wobble(pts, seed + 7, amp * 1.6, closed), fill=INK, width=1.3, capstyle="round")


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class Scaled:
    """논리 좌표(원래 크기)로 그리면 SC배로 줄여서 실제 캔버스에 그려주는 래퍼"""

    def __init__(self, raw):
        self.raw = raw

    @staticmethod
    def _p(vals):
        return [WW / 2 + (v - LCX) * SC if i % 2 == 0 else GR + (v - GROUND) * SC for i, v in enumerate(vals)]

    @staticmethod
    def _kw(kw):
        if "width" in kw:
            kw["width"] = max(1.0, kw["width"] * math.sqrt(SC))   # 선은 덜 얇아지게
        return kw

    def delete(self, *a):
        self.raw.delete(*a)

    def create_polygon(self, *args, **kw):
        pts = list(args[0]) if len(args) == 1 else list(args)
        return self.raw.create_polygon(self._p(pts), **self._kw(kw))

    def create_line(self, *args, **kw):
        pts = list(args[0]) if len(args) == 1 else list(args)
        return self.raw.create_line(self._p(pts), **self._kw(kw))

    def create_oval(self, x0, y0, x1, y1, **kw):
        return self.raw.create_oval(*self._p([x0, y0, x1, y1]), **self._kw(kw))

    def create_arc(self, x0, y0, x1, y1, **kw):
        return self.raw.create_arc(*self._p([x0, y0, x1, y1]), **self._kw(kw))

    def create_text(self, x, y, **kw):
        px, py = self._p([x, y])
        return self.raw.create_text(px, py, **kw)


class Buddy:
    def __init__(self):
        self.root = root = tk.Tk()
        root.title("도파미")
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        try:
            root.attributes("-transparentcolor", KEY)
        except tk.TclError:
            pass  # Windows가 아니면 투명 배경 미지원
        root.config(bg=KEY)

        self.sw, self.sh = root.winfo_screenwidth(), root.winfo_screenheight()
        self.raw = tk.Canvas(root, width=WW, height=HH, bg=KEY, highlightthickness=0)
        self.raw.pack()
        self.cv = Scaled(self.raw)

        families = set(tkfont.families())
        self.face_name = next((f for f in ("맑은 고딕", "Malgun Gothic", "Apple SD Gothic Neo", "NanumGothic")
                               if f in families), "TkDefaultFont")
        self.font = tkfont.Font(family=self.face_name, size=11)

        # 위치/물리 (x, y 는 창의 화면 좌표)
        self.x = float(random.randint(0, max(0, self.sw - WW)))
        self.y = float(max(0, self.sh - GR - 60))
        self.px = self.x
        self.vx_s = 0.0
        self.lift = self.plift = 0.0
        self.sy, self.vsy, self.tsy = 1.0, 0.0, 1.0
        self.tipdx = self.tipv = self.tipdy = 0.0   # 귀가 몸보다 늦게 흔들리는 스프링
        self.parts = []                              # 착지 때 퐁 터지는 먼지방울
        self.lid = self.lid_t = 0.18
        self.blink_end, self.next_blink = 0.0, time.time() + 2
        self.face = 1
        # 상태
        self.state = "idle"
        self.act, self.act_start, self.act_dur, self.act_var = None, 0.0, 0.0, 0
        self.idle_until = time.time() + 1.0
        self.tx, self.ty = self.x, self.y
        self.t0 = self.t_end = 0.0
        self.x0 = self.y0 = self.x1 = self.y1 = 0.0
        self.dragging = False
        self.press_xy, self.press_t = None, 0.0
        self.hang_pending, self.chase_until, self.hang_until = False, 0.0, 0.0
        self.pain_until = self.hit_t = 0.0
        self.clicks, self.leaving = [], False
        self.chatting, self.chat_win, self.chat_entry, self.chat_last = False, None, None, 0.0
        self.history, self.reply_q = [], queue.Queue()
        # 말하기
        self.bag, self.first, self.count = [], True, 0
        self.text, self.typed, self.talk_until, self.box = "", 0.0, None, None
        self.next_talk = time.time() + 3
        self.last_lift = 0.0

        cv = self.raw
        cv.bind("<ButtonPress-1>", self.on_press)
        cv.bind("<B1-Motion>", self.on_drag)
        cv.bind("<ButtonRelease-1>", self.on_release)

        root.geometry(f"{WW}x{HH}+{int(self.x)}+{int(self.y)}")
        self.update()

    # ---------- 입력 ----------
    def pointer(self):
        try:
            px, py = self.root.winfo_pointerxy()
            return int(px), int(py)
        except Exception:
            return int(self.x + WW / 2), int(self.y + GR)

    def on_press(self, e):
        self.press_t = time.time()
        self.press_xy = (e.x_root, e.y_root)
        self.ox, self.oy = e.x_root - self.x, e.y_root - self.y

    def on_drag(self, e):
        if not self.dragging and self.press_xy and \
                math.hypot(e.x_root - self.press_xy[0], e.y_root - self.press_xy[1]) > 5:
            self.dragging = True            # 5px 넘게 움직이면 클릭이 아니라 '들어올리기'
            self.act, self.hang_pending = None, False
            self.ox, self.oy = e.x_root - self.x, e.y_root - self.y
        if self.dragging:
            self.x, self.y = e.x_root - self.ox, e.y_root - self.oy

    def on_release(self, e):
        if self.dragging:
            self.dragging = False
            self.sy, self.vsy = 0.7, 0.0          # 내려놓으면 말랑하게 착지
            if self.state != "talk":
                self.state = "idle"
                self.idle_until = time.time() + 1.2
        elif self.press_xy:
            if time.time() - self.press_t >= 0.6:       # 가만히 길게 누르면 대화창
                self.open_chat()
            else:                                       # 톡 누르면 아야!
                self.ouch(time.time())
        self.press_xy = None

    # ---------- 행동 ----------
    def schedule_next(self):
        gap = (6, 10) if self.count <= 1 else TALK_GAP      # 인사 직후엔 곧바로 첫 썰
        self.next_talk = time.time() + random.uniform(*gap)

    def pick_target(self):
        self.tx = random.uniform(-EDGE_PAD, max(0, self.sw - WW + EDGE_PAD))
        self.ty = random.uniform(0, max(0, self.sh - GR - 50))

    def start_act(self, name, dur, now):
        self.act, self.act_start, self.act_dur = name, now, dur
        self.act_var = random.choice((0, 1))

    def choose_idle(self, now):
        r = random.random()
        if r < 0.42 or r >= 0.94:
            self.pick_target()
            self.begin_wind(now)
        elif r < 0.54:
            self.start_act("derp", 2.6, now)
        elif r < 0.62:
            self.start_act("yawn", 1.6, now)
        elif r < 0.70:
            self.start_act("nap", random.uniform(7, 11), now)
        elif r < 0.78:
            self.start_act("wave", 2.2, now)
        elif r < 0.86:
            self.start_act("tongue", 2.0, now)
        else:
            self.start_chase(now)

    def begin_wind(self, now):
        dx, dy = self.tx - self.x, self.ty - self.y
        if math.hypot(dx, dy) < 6:
            self.state, self.idle_until = "idle", now + 1.0
            return
        if abs(dx) > 3:
            self.face = 1 if dx > 0 else -1
        self.state, self.t_end = "wind", now + WIND_DUR

    def start_air(self, now):
        dx, dy = self.tx - self.x, self.ty - self.y
        dist = max(1.0, math.hypot(dx, dy))
        step = min(HOP_LEN, dist)
        self.x0, self.y0 = self.x, self.y
        self.x1, self.y1 = self.x + dx / dist * step, self.y + dy / dist * step
        self.t0, self.state = now, "air"

    def land(self, now):
        self.x, self.y, self.lift = self.x1, self.y1, 0.0
        self.sy, self.vsy = 0.62, 0.0
        self.state, self.t_end = "land", now + 0.10
        for _ in range(4):                    # 착지하면 먼지방울이 퐁퐁
            self.parts.append([LCX + random.uniform(-40, 40), GROUND - 8, random.uniform(-1.2, 1.2),
                               random.uniform(-2.2, -0.8), 1.0, random.uniform(4.0, 7.0)])

    # --- 마우스에 매달리기 ---
    def retarget_cursor(self):
        mx, my = self.pointer()
        self.tx = clamp(mx - WW / 2, -EDGE_PAD, self.sw - WW + EDGE_PAD)
        self.ty = clamp(my - GR + HANG_H * SC, 0, self.sh - GR - 50)

    def start_chase(self, now):
        self.hang_pending, self.chase_until = True, now + 12
        self.retarget_cursor()
        self.begin_wind(now)

    def start_hang(self, now):
        self.hang_pending, self.act = False, None
        self.state, self.hang_until = "hang", now + random.uniform(4, 7)

    def drop(self, now):
        self.sy, self.vsy = 0.7, 0.0
        self.state, self.t_end = "land", now + 0.2
        self.pick_target()

    # --- 클릭하면 아야! ---
    def ouch(self, now):
        if self.leaving:
            return
        self.clicks = [t for t in self.clicks if now - t < 3.5] + [now]
        self.act, self.hang_pending = None, False
        self.box = None
        self.hit_t, self.pain_until = now, now + 1.8
        self.sy, self.vsy = 0.62, 0.0
        if len(self.clicks) >= 5:             # 연타하면 삐져서 집에 감
            self.leaving = True
            self.pain_until = now + 4
            self.say("아야야야!! 나 집에 갈래...")
            self.root.after(3000, self.root.destroy)
            return
        mx, _ = self.pointer()
        away = 1 if self.x + WW / 2 >= mx else -1          # 커서 반대쪽으로 물러남
        self.tx = clamp(self.x + away * random.uniform(70, HOP_LEN), -EDGE_PAD, self.sw - WW + EDGE_PAD)
        self.ty = self.y
        self.face = -away                                   # 커서를 계속 쳐다보며 뒷걸음질
        self.state, self.t_end = "wind", now + 0.12
        self.next_talk = max(self.next_talk, now + 8)

    # --- 채팅 ---
    def open_chat(self):
        if self.chat_win:
            return
        self.act, self.hang_pending = None, False
        if not load_api_key():
            self.say("열쇠가 없어서 대화를 못 해... 같은 폴더에 api_key.txt 만들어서 API 키를 넣어줘!")
            return
        self.chatting = True
        self.chat_last = time.time()
        top = tk.Toplevel(self.root)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        top.configure(bg=INK)
        ent = tk.Entry(top, font=self.font, width=26, relief="flat", bg=PAPER, fg=INK, insertbackground=INK)
        ent.pack(padx=2, pady=2, ipady=4)
        w_, h_ = 270, 34
        x = clamp(self.x + WW / 2 - w_ / 2, 4, self.sw - w_ - 4)
        y = self.y + GR + 6
        if y > self.sh - h_ - 60:                  # 아래 공간이 없으면 캐릭터 위쪽에
            y = self.y + GR - 150 * SC - h_ - 8
        top.geometry(f"+{int(x)}+{int(y)}")
        ent.bind("<Return>", self.send_chat)
        ent.bind("<Escape>", lambda e: self.close_chat())
        ent.bind("<Key>", lambda e: setattr(self, "chat_last", time.time()))
        self.chat_win, self.chat_entry = top, ent
        top.after(60, lambda: (top.focus_force(), ent.focus_force()))
        self.say("응? 왜? 말해봐~")

    def close_chat(self):
        if self.chat_win:
            try:
                self.chat_win.destroy()
            except Exception:
                pass
        self.chat_win = self.chat_entry = None
        self.chatting = False
        self.next_talk = max(self.next_talk, time.time() + 8)

    def send_chat(self, _event=None):
        msg = self.chat_entry.get().strip() if self.chat_entry else ""
        if not msg:
            return
        self.chat_entry.delete(0, "end")
        self.chat_last = time.time()
        self.history.append({"role": "user", "content": msg})
        self.history = self.history[-12:]
        while self.history and self.history[0]["role"] != "user":
            self.history.pop(0)
        hist = list(self.history)
        self.say("음... 잠깐만...")

        def work(key=load_api_key()):
            self.reply_q.put(ask_claude(hist, key))
        threading.Thread(target=work, daemon=True).start()

    def poll_replies(self):
        while True:
            try:
                ok, text = self.reply_q.get_nowait()
            except queue.Empty:
                return
            if ok:
                if len(text) > 180:
                    text = text[:177] + "..."
                self.history.append({"role": "assistant", "content": text})
            else:
                text = {"key": "열쇠(API 키)가 이상한가 봐... api_key.txt 확인해줘!",
                        "model": "어... 내 머리(모델 이름)가 없대. 코드 위쪽 MODEL 을 확인해줘!",
                        "rate": "으억 너무 빨라... 조금만 이따가 말 걸어줘."}.get(
                    text, "어... 머리가 지끈거려. 인터넷이 이상한가?")
                if self.history and self.history[-1]["role"] == "user":
                    self.history.pop()                  # 실패한 질문은 기록에서 빼서 다음 호출이 꼬이지 않게
            self.say(text)

    # --- 말하기 ---
    def next_story(self):
        self.count += 1
        if self.first:
            self.first = False
            return GREETING
        if self.count % 4 == 0:
            return random.choice(SILLY)
        if not self.bag:
            self.bag = random.sample(STORIES, len(STORIES))
        return random.choice(PREFIX) + self.bag.pop() + random.choice(SUFFIX)

    def say(self, text=None):
        if self.state == "air" and text is None:   # 공중이면 착지 후에 말하기
            self.next_talk = 0
            return
        if self.state == "air":                    # 공중에서 말하게 되면 그 자리에 착지
            self.x, self.y, self.lift = self.x1, self.y1, 0.0
        self.act = None
        self.text = self.wrap(text or self.next_story(), 250)
        lines = self.text.split("\n")
        tw = max(self.font.measure(s) for s in lines)
        th = self.font.metrics("linespace") * len(lines)
        bw, bh = tw + 28, th + 22
        x0 = clamp(WW / 2 - bw / 2, 4 - self.x, self.sw - 4 - self.x - bw)   # 화면 밖으로 안 나가게
        by = GR + (BUBBLE_BOTTOM - GROUND) * SC
        self.box = (x0, by - bh, x0 + bw, by)
        self.typed, self.talk_until, self.state = 0.0, None, "talk"

    def wrap(self, text, maxw):
        lines, cur = [], ""
        for word in text.split(" "):
            trial = word if not cur else cur + " " + word
            if self.font.measure(trial) <= maxw:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return "\n".join(lines)

    # ---------- 루프 ----------
    def logic(self, now):
        if self.dragging:
            self.tsy, self.lid_t, self.lift = 1.12, 0.0, 0.0
            return
        st = self.state
        if st == "hang":
            mx, my = self.pointer()
            self.x += (mx - WW / 2 - self.x) * 0.35
            self.y += (my - (GR - HANG_H * SC) - self.y) * 0.35
            self.tsy, self.lid_t, self.lift = 1.12, 0.05, 0.0
            if now >= self.hang_until:
                self.drop(now)
        elif st == "idle":
            self.tsy = 0.84 if self.act == "nap" else 1.0
            self.lid_t = 1.0 if self.act in ("nap", "yawn") else 0.18
            if self.chatting:
                pass                                    # 대화 중엔 얌전히 서 있기
            elif now >= self.next_talk:
                self.say()
            elif self.act and now >= self.act_start + self.act_dur:
                self.act, self.idle_until = None, now + random.uniform(0.6, 1.8)
            elif not self.act and now >= self.idle_until:
                self.choose_idle(now)
        elif st == "wind":
            self.tsy, self.lid_t = 0.70, 0.18
            if now >= self.t_end:
                self.start_air(now)
        elif st == "air":
            u = (now - self.t0) / HOP_DUR
            if u >= 1:
                self.land(now)
            else:
                self.x = self.x0 + (self.x1 - self.x0) * u
                self.y = self.y0 + (self.y1 - self.y0) * u
                self.lift = 4 * HOP_H * u * (1 - u)
                self.tsy = 1.2
        elif st == "land":
            self.tsy = 1.0
            if now >= self.t_end:
                if self.chatting:
                    self.state = "idle"
                elif self.hang_pending:
                    self.retarget_cursor()
                    if now > self.chase_until:
                        self.hang_pending = False
                        self.state, self.idle_until = "idle", now + 1.0
                    elif math.hypot(self.tx - self.x, self.ty - self.y) < 90:
                        self.start_hang(now)
                    else:
                        self.begin_wind(now)
                elif now >= self.next_talk:
                    self.say()
                elif math.hypot(self.tx - self.x, self.ty - self.y) > 6:
                    self.begin_wind(now)
                else:
                    self.state, self.idle_until = "idle", now + random.uniform(1.0, 3.0)
        elif st == "talk":
            self.lid_t = 0.05
            if self.typed < len(self.text):
                self.typed += 0.8
                self.tsy = 1.0 + 0.03 * math.sin(now * 14)
            else:
                self.tsy = 1.0
                if self.talk_until is None:
                    self.talk_until = now + max(4.0, len(self.text) * 0.08)
                elif now >= self.talk_until and not self.leaving and not self.chatting:
                    self.box, self.state = None, "idle"
                    self.idle_until = now + random.uniform(1.0, 2.5)
                    self.schedule_next()

    def physics(self, now):
        if self.act == "yawn":
            p = clamp((now - self.act_start) / self.act_dur, 0, 1)
            self.tsy = 1.0 + 0.10 * math.sin(math.pi * p)
        # 몸통 스프링 (스쿼시 & 스트레치)
        self.vsy += -0.25 * (self.sy - self.tsy) - 0.30 * self.vsy
        self.sy += self.vsy
        # 귀: 몸이 움직인 방향의 반대로 한 박자 늦게 따라옴
        wvx = self.x - self.px
        self.px = self.x
        self.vx_s += (wvx - self.vx_s) * 0.3
        target = clamp(-self.vx_s * 0.8 / SC, -14, 14)
        self.tipv += -0.22 * (self.tipdx - target) - 0.20 * self.tipv
        self.tipdx += self.tipv
        lv = self.lift - self.plift
        self.plift = self.lift
        self.tipdy += (clamp(lv * 1.2, -8, 8) - self.tipdy) * 0.3
        # 먼지방울
        for p in self.parts:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.07
            p[4] -= 0.035
        self.parts = [p for p in self.parts if p[4] > 0]
        # 눈 깜빡임
        if now >= self.next_blink:
            self.blink_end = now + 0.13
            self.next_blink = now + random.uniform(2.0, 5.5)
        goal = 1.0 if now < self.blink_end else self.lid_t
        self.lid += (goal - self.lid) * 0.5

    def log_error(self):
        """콘솔이 없으니 오류는 dopamine_buddy.log 에 남김 (최대 30번)"""
        self.errors = getattr(self, "errors", 0) + 1
        if self.errors > 30:
            return
        try:
            import traceback
            with open(os.path.join(BASE_DIR, "dopamine_buddy.log"), "a", encoding="utf-8") as fh:
                fh.write(time.strftime("%Y-%m-%d %H:%M:%S ") + traceback.format_exc() + "\n")
        except Exception:
            pass

    def update(self):
        try:
            now = time.time()
            self.poll_replies()
            if self.chatting and now - self.chat_last > 90:        # 90초간 입력 없으면 대화창 닫기
                self.close_chat()
            self.logic(now)
            self.physics(now)
            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
            if now - self.last_lift > 3:
                self.root.attributes("-topmost", True)
                self.root.lift()
                self.last_lift = now
            self.draw(now)
        except Exception:
            self.log_error()
        self.root.after(FRAME_MS, self.update)

    # ---------- 그리기 ----------
    def look_vec(self, cy):
        px, py = self.pointer()
        dx = px - (self.x + WW / 2)
        dy = py - (self.y + GR + (cy - GROUND) * SC)
        d = math.hypot(dx, dy) or 1.0
        k = min(1.0, d / 200.0)
        return dx / d * 3.5 * k, dy / d * 3.0 * k

    def draw(self, now):
        c = self.cv
        c.delete("all")
        cx, f = LCX, self.face
        sy = clamp(self.sy, 0.5, 1.4)
        sx = 1 + (1 - sy) * 0.7
        lift = self.lift
        hanging = self.state == "hang"
        pain = now < self.pain_until
        skew = clamp(self.vx_s * 1.0 / SC, -12, 12)
        if hanging:
            skew = clamp(skew * 1.5, -14, 14) + math.sin(now * 3) * 4          # 대롱대롱 흔들
        if pain and now - self.hit_t < 0.5:
            skew += math.sin(now * 45) * 4                                       # 맞은 직후 부르르
        rx, ry = RX * sx, RY * sy
        cy = GROUND - lift - ry
        asleep = self.act == "nap"
        talking = self.state == "talk" and self.typed < len(self.text)
        bs = int(now * 6) % 3 if BOIL else 0     # 낙서 일렁임 프레임 (초당 6번)

        def at(dx, dyf):
            """몸 위의 특징 좌표 (dyf: -1 위 ~ 1 아래), 기울기 반영"""
            return (cx + dx * sx + f * 3 * sx + skew * (1 - dyf) / 2, cy + ry * dyf)

        def blob(x, y, rw, rh, seed, fill=BODY, n=20, width=2.5):
            pts = []
            for i in range(n):
                a = 2 * math.pi * i / n
                pts += [x + rw * math.cos(a), y + rh * math.sin(a)]
            c.create_polygon(pts, fill=fill, outline="")
            pen(c, pts, seed + bs * 17, width=width, amp=0.9)

        # 그림자 (매달렸을 땐 없음)
        if not hanging:
            sh_w = max(20, 46 - lift * 0.45)
            c.create_oval(cx - sh_w, GROUND - 5, cx + sh_w, GROUND + 5, fill="#444444", outline="", stipple="gray50")

        # 짧은 다리 (매달리면 달랑달랑)
        for s in (-1, 1):
            kick = (6 + math.sin(now * 7 + s * math.pi) * 4) if hanging else 0
            blob(cx + s * 23 * sx + skew * 0.1, GROUND - lift - 8 + kick, 13, 9, 10 + s)

        # 작은 귀 (몸통 뒤)
        top_y = cy - ry
        for s in (-1, 1):
            blob(cx + s * 36 * sx + skew + self.tipdx * 0.4,
                 top_y + 9 + self.tipdy * 0.5 - (sy - 1) * 6, 11, 13, 20 + s)

        # 짧은 팔
        wave = self.act == "wave" and self.state == "idle"
        for s in (-1, 1):
            if hanging:                                 # 두 팔을 위로 뻗어 마우스를 붙잡음
                hx, hy = cx + s * 3 + skew, top_y - 26          # 두 손이 한 점(마우스)에서 만남
                shx, shy = at(s * (RX - 8), 0.0)
                c.create_line(shx, shy, hx, hy, fill=INK, width=11, capstyle="round")
                c.create_line(shx, shy, hx, hy, fill=BODY, width=6.5, capstyle="round")
                blob(hx, hy, 6.5, 6.5, 30 + s, n=12, width=2)
                continue
            ax, ay = at(s * (RX + 3), 0.2)
            ay += math.sin(now * 8 + s) * 1.5
            if s == 1 and wave:
                ay = cy - ry * 0.45 + math.sin(now * 12) * 6
                ax += 4
            elif sy > 1.1:
                ay -= (sy - 1.1) * 40
            if talking and s == 1 and int(now * 2) % 3 == 0:
                ay = cy - ry * 0.2 + math.sin(now * 10) * 4
            if pain:
                ay = cy - ry * 0.1 + math.sin(now * 30) * 2                  # 아파서 팔 파닥
            blob(ax, ay, 9, 12, 30 + s)

        # 몸통: 털이 보송한 울퉁불퉁 낙서 외곽선
        pts = []
        for i in range(56):
            a = 2 * math.pi * i / 56
            s, co = math.sin(a), math.cos(a)
            t = (1 - s) / 2
            fluff = 1 + 0.035 * math.sin(a * 13 + 0.7) + 0.02 * math.sin(a * 7)
            pts += [cx + rx * (1 + 0.08 * s) * fluff * co + skew * t, cy + ry * fluff * s]
        c.create_polygon(pts, fill=BODY, outline="")
        pen(c, pts, 100 + bs * 13, width=3, amp=1.3)
        for dx_, ang in ((-11, -0.4), (0, 0.0), (11, 0.4)):          # 머리 위 털뭉치 삐죽
            x_, y_ = at(dx_, -0.80)
            pen(c, [x_, y_ + 3, x_ + ang * 6, y_ - 5], 200 + dx_ + bs * 5, width=2, amp=0.6, closed=False)

        # 눈
        lx, ly = self.look_vec(cy)
        derp = 0.0
        if self.act == "derp":
            derp = math.sin(math.pi * clamp((now - self.act_start) / self.act_dur, 0, 1))
        for s, rw_, rh_, dyf, pr in ((-1, 11.5, 12.5, -0.16, 3.6), (1, 9.5, 10.5, -0.06, 4.2)):
            ex, ey = at(s * 17, dyf)
            if pain:                                      # > < 로 꽉 감은 눈 + 눈물
                pen(c, [ex - s * 7, ey - 7, ex + s * 5, ey, ex - s * 7, ey + 7], 400 + s + bs * 3,
                    width=3, amp=0.6, closed=False)
                off = (now * 40) % 14
                c.create_oval(ex + s * 5 - 3, ey + 9 + off, ex + s * 5 + 3, ey + 17 + off,
                              fill=DROOL, outline=INK, width=1.3)
            elif self.lid > 0.9:
                pen(c, [ex - 8, ey + 1 + s, ex + 8, ey - 1 - s], 300 + s + bs * 3, width=3, amp=0.7, closed=False)
            else:
                blob(ex, ey, rw_, rh_, 40 + s, fill="white", width=2.2)
                ox = -s * 4.0 + math.sin(now * 1.3 + s * 1.7) * 1.3 + lx * 0.5   # 기본: 안쪽으로 모인 사팔눈
                oy = math.cos(now * 0.9 + s) * 1.3 + ly * 0.5
                if hanging:
                    ox, oy = ox + lx * 0.8, oy - 3                             # 매달린 채 위(손)를 올려다봄
                if self.act_var == 0:
                    ox += s * 9 * derp                       # 눈알이 서로 반대로 도망
                    oy += s * 4 * derp
                else:
                    ox += -s * 3 * derp                      # 눈알이 코 쪽으로 몰림
                    oy += -2 * derp
                d = math.hypot(ox, oy)
                if d > rw_ - 4.5:
                    ox, oy = ox / d * (rw_ - 4.5), oy / d * (rw_ - 4.5)
                c.create_oval(ex + ox - pr, ey + oy - pr, ex + ox + pr, ey + oy + pr, fill=INK, outline="")
                yl = ey - rh_ + 2 * rh_ * self.lid
                if self.lid > 0.05:                           # 반쯤 감긴 멍한 눈꺼풀
                    pen(c, [ex - rw_ + 1, yl, ex + rw_ - 1, yl + s * 0.8], 50 + s + bs * 3, width=2, amp=0.5,
                        closed=False)

        # 눈썹: 평소엔 좌우 비대칭, 아플 땐 팔자로 처짐
        ex, ey = at(-17, -0.16)
        up = 8 if talking else 0
        if pain:
            pen(c, [ex - 8, ey - 14, ex + 8, ey - 22], 60 + bs * 3, width=3, amp=0.7, closed=False)
            ex, ey = at(17, -0.06)
            pen(c, [ex - 8, ey - 20, ex + 8, ey - 12], 70 + bs * 3, width=3, amp=0.7, closed=False)
        else:
            pen(c, [ex - 10, ey - 19 - up * 0.3, ex + 8, ey - 27 - up], 60 + bs * 3, width=3, amp=0.7, closed=False)
            ex, ey = at(17, -0.06)
            pen(c, [ex - 8, ey - 13, ex + 10, ey - 11 + (up * 0.2)], 70 + bs * 3, width=3, amp=0.7, closed=False)

        # 입: 살짝 벌린 채 오른쪽 입꼬리만 어색하게 올라감
        mx, my = at(0, 0.40)
        mo = 0.35
        if pain:
            mo = 2.0 + 0.4 * math.sin(now * 25)                                  # 아야~ 하고 크게 벌림
        elif self.act == "yawn":
            mo = 0.35 + 2.6 * math.sin(math.pi * clamp((now - self.act_start) / self.act_dur, 0, 1))
        elif talking:
            mo = 1.2 if int(now * 9) % 2 == 0 else 0.4
        elif hanging:
            mo = 1.0
        elif asleep:
            mo = 0.3
        bot = my + 8 + 9 * mo
        mpts = [mx - 12, my, mx - 5, my - 3, mx + 5, my - 4, mx + 13, my - 10,
                mx + 9, my + 4 + 7 * mo, mx, bot, mx - 9, my + 4 + 6 * mo]
        c.create_polygon(mpts, fill=MOUTH, outline="")
        pen(c, mpts, 80 + bs * 3, width=2.4, amp=0.8)

        # 혀 (가끔 쏙)
        if self.act == "tongue":
            e = clamp(math.sin(math.pi * clamp((now - self.act_start) / self.act_dur, 0, 1)) * 1.6, 0, 1)
            if e > 0.1:
                th = 10 * e
                blob(mx + 2, bot - 3 + th * 0.6, 6.5, th, 90, fill=TONGUE, n=16, width=2)
                pen(c, [mx + 2, bot, mx + 2, bot + th * 1.0], 95, width=1.5, amp=0.4, closed=False)

        # 침
        if not pain:
            dlen = 5 + 9 * (0.5 + 0.5 * math.sin(now * 0.7)) + (10 if asleep else 0) + (3 if talking else 0)
            dx0, dy0 = mx - 8, my + 4 + 6 * mo
            c.create_line(dx0, dy0, dx0, dy0 + dlen, fill=INK, width=6)
            c.create_line(dx0, dy0, dx0, dy0 + dlen, fill=DROOL, width=3)
            blob(dx0, dy0 + dlen + 3, 4.5, 5.5, 110, fill=DROOL, n=12, width=1.8)

        # 낮잠: 코방울 + z z z
        if asleep:
            r = 5 + 6 * (0.5 + 0.5 * math.sin(now * 1.4))
            bx, by = mx + 17, my - 6
            c.create_oval(bx - r, by - r, bx + r, by + r, fill="#eef8ff", outline=INK, width=1.8)
            c.create_line(bx - r * 0.5, by - r * 0.3, bx - r * 0.2, by - r * 0.6, fill=INK, width=1.3)
            for i in range(3):
                ph = ((now * 0.6) + i / 3) % 1
                c.create_text(cx + 40 + ph * 24, top_y - 8 - ph * 34 + 10, text="z",
                              font=(self.face_name, int((10 + 8 * ph) * 0.8), "bold"), fill=INK)

        # 먼지방울
        for p in self.parts:
            r = p[5] * p[4]
            c.create_oval(p[0] - r, p[1] - r, p[0] + r, p[1] + r, fill=BODY, outline=INK, width=1.5)

        # 아야! 말풍선 (톱니 모양 폭발)
        if pain and not self.leaving and now - self.hit_t < 1.4:
            bx, by = cx + 40, top_y - 26
            spikes = []
            for i in range(16):
                ang = 2 * math.pi * i / 16
                rr = 42 if i % 2 == 0 else 25
                spikes += [bx + rr * math.cos(ang), by + rr * math.sin(ang) * 0.8]
            c.create_polygon(spikes, fill="#fff3a0", outline="")
            pen(c, spikes, 500 + bs * 3, width=2, amp=0.8)
            c.create_text(bx, by, text="아야!", font=(self.face_name, 11, "bold"), fill=INK, anchor="center")

        # 말풍선 (실제 크기로, 종이 + 삐뚤빼뚤 펜 테두리)
        if self.state == "talk" and self.box:
            r_ = self.raw
            x0, y0, x1, y1 = self.box
            tipx = clamp(WW / 2, x0 + 16, x1 - 16)
            bp = rrect_pts(x0, y0, x1, y1, 14)
            r_.create_polygon(bp, fill=PAPER, outline="")
            r_.create_polygon(tipx - 8, y1 - 1, tipx + 8, y1 - 1, tipx, y1 + 13, fill=PAPER, outline="")
            pen(r_, bp, 900 + bs * 3, width=2.5, amp=1.2)
            r_.create_line(tipx - 8, y1, tipx, y1 + 13, tipx + 8, y1, fill=INK, width=2.5)
            r_.create_line(tipx - 7, y1, tipx + 7, y1, fill=PAPER, width=3)
            r_.create_text(x0 + 14, y0 + 11, text=self.text[:int(self.typed)], font=self.font,
                           fill=INK, anchor="nw")


if __name__ == "__main__":
    Buddy().root.mainloop()
