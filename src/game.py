# -*- coding: utf-8 -*-
"""游戏主类：状态机、回合、关卡推进、输入分发、每帧更新。

只管「规则」：画法在 ui.py，数值在 config.py。
"""

import random

import pygame

from src.board import Board
from src.config import (
    BTN_H, BTN_W, CELL, C_BG, C_GHOST, C_MONSTER, C_PLAYER, DEBRIS_GRAVITY, DEBRIS_JITTER,
    DEBRIS_SPEED, DEBRIS_UP, FPS, GRADE_A_NOISE_PCT, GRADE_S_COVERAGE, GRADE_S_NOISE,
    INTRO_FADE, INTRO_FALL, INTRO_SHOW, INTRO_TOTAL, LEVELS, LV_BTN_GAP, LV_BTN_H, LV_BTN_W,
    MONSTER_SPD_JITTER, MONSTER_SPEED, PHASE1_DURATION, PHASE_SHIFT_TIME, PLAYER_GLOW_R,
    PLAYER_START_CELL,
    PURPLE_SPAWN_MARGIN, PURPLE_SPAWN_WINDOW, PURPLE_SPEED, PURPLE_MODE,
    SC_A, SC_D, SC_ENTER, SC_ESC, SC_F1, SC_J, SC_K, SC_KP_ENTER, SC_LEFT, SC_R, SC_RIGHT,
    SC_SPACE, SHAKE_LEAD, SHAKE_SEQ, SHAKE_STEP, SPAWN_ORIGIN, SPAWN_PX, STORY_BANNER_TIME,
    TARGET_N, TARGET_OFFSET,
    WINDOW_H, WINDOW_W
)
from src.entities import Monster, Player
from src.grid import cell_center
from src.input_state import InputState
from src.qr import generate_target
from src import story
from src.ui import draw_banner, draw_hud, draw_result, draw_select, draw_title, draw_world

# ==== 游戏主类 ====


class Game:
    def __init__(self, window):
        self.window = window
        # 绘制都打到逻辑画布，最后一次性缩放进窗口，布局常量与判定逻辑都不用改
        self.canvas = pygame.Surface((WINDOW_W, WINDOW_H))
        self.screen = self.canvas
        self.scale = window.get_width() / float(WINDOW_W)
        self.needs_scale = window.get_width() != WINDOW_W
        self.input = InputState()
        self.running = True
        self.debug = False
        self._last_dt = 1.0 / FPS              # 给 F1 调试显示用

        # 字体只在初始化时创建一次，绝不在 draw 里新建
        self.f_main = pygame.font.Font(None, 28)
        self.f_small = pygame.font.Font(None, 22)
        self.f_mid = pygame.font.Font(None, 52)        # 结算页标题
        self.f_big = pygame.font.Font(None, 110)       # 结算页评级
        self.f_story = pygame.font.Font(None, 40)      # 剧情大字（结算页那句）

        self.center = pygame.Vector2(WINDOW_W / 2, WINDOW_H / 2)   # 怪物无目标时的漂向点

        # 28×28 的半透明提示块反复复用（每帧新建 400 个 Surface 会掉帧）
        self.ghost = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.ghost.fill(C_GHOST)

        # 玩家脚下光晕，同样只做一次
        self.glow = pygame.Surface((PLAYER_GLOW_R * 2, PLAYER_GLOW_R * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.glow, (*C_PLAYER, 46), (PLAYER_GLOW_R, PLAYER_GLOW_R), PLAYER_GLOW_R)

        # 横幅（关卡开场 / 阶段切换）用的整屏遮罩，只建一次，每帧重填内容
        self.overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        self.menu_t = 0.0
        self.banner_text = ""
        self.banner_t = 0.0
        self.banner_total = 1.0
        self.banner_kind = "big"        # "big"=整屏大字 / "story"=底部字幕条
        self.band = pygame.Surface((WINDOW_W, 100), pygame.SRCALPHA)   # 字幕条底，只建一次
        self.level = 1
        self.unlocked = 1            # 已解锁到第几关（内存里，退出游戏就归 1）
        self.sel = 1                 # 选关页当前高亮哪一关
        self.hover = None            # 鼠标悬停的按钮下标

        # 被啃格的红闪覆盖层（半透明），M3 复用，同样只做一次
        self.flash_surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.flash_surf.fill((*C_MONSTER, 120))

        # 开场动画：抖动是把画好的整帧挪一下，所以留一块缓冲区做中转
        self.shake_buf = pygame.Surface((WINDOW_W, WINDOW_H))

        # 下面这些真正在 new_round() 里赋值；这里先给默认值，
        # 一是让 IDE 能静态识别属性（不报 defined outside __init__），二是断言它们永远存在
        self.goal_cover = LEVELS[0]["cover"]
        self.goal_noise = LEVELS[0]["noise"]
        self.duration = LEVELS[0]["time"]
        self.spawn_rate = LEVELS[0]["spawn"]
        self.spawn_delay = LEVELS[0]["delay"]
        self.rng = random.Random()
        self.target = []
        self.board = None
        self.player = None
        self.elapsed = 0.0
        self.monsters = []
        self.claims = {}
        self.spawn_acc = 0.0
        self.shifted = False
        self.result = None
        self.triggered = False      # 本关的一次性剧情句是否已触发
        self.intro_t = 0.0          # >0 表示开场动画还没放完
        self.debris = []            # 震碎的黑色格子：[[x, y, vx, vy], ...]
        self.shake_t = 0.0          # 抖动剩余时间
        self.shake_started = False  # 抖动是否已开始（比震碎早几下）
        self.shake_off = (0, 0)     # 当前这一帧的抖动偏移
        self.burst_done = False     # 是否已经炸开
        self.hint_alpha = 255       # 灰色提示层不透明度（开场从 0 淡入）

        self.new_round()
        self.state = "TITLE"                      # 开局落在开始页（此时棋盘已备好一局）

    # ---------- 开局 ----------
    def new_round(self):
        cfg = LEVELS[self.level - 1]              # 关卡参数只在这里读一次
        self.goal_cover = cfg["cover"]
        self.goal_noise = cfg["noise"]
        self.duration = cfg["time"]
        self.spawn_rate = cfg["spawn"]
        self.spawn_delay = cfg["delay"]
        self.purple_count = cfg.get("purple", 0)   # 这一关有几只紫怪（0=没有）
        self.seen_on = cfg.get("seen", False)      # 这一关是否只照亮走过的地方

        self.rng = random.Random()                # 不固定种子：重开必出新码
        self.target = generate_target(self.rng)
        self.board = Board(self.target, self.seen_on)
        # 开局手上唯一确定的东西：脚下这一小片。其余地方一片白，得自己走过去看
        self.board.mark_seen(*PLAYER_START_CELL, flash=False)
        self.player = Player()
        self.elapsed = 0.0
        self.state = "PLAY"

        self.monsters = []
        self.claims = {}                          # {(r,c): 有几只怪锁着这一格}
        self.spawn_acc = 0.0
        # 紫怪的刷新时刻：开局就把「前 2 分半内的 N 个随机时刻」排好，到点各刷一只
        span = max(1.0, min(PURPLE_SPAWN_WINDOW, self.duration - PURPLE_SPAWN_MARGIN))
        self.purple_times = sorted(self.rng.uniform(1.0, span) for _ in range(self.purple_count))
        self.purple_i = 0                         # 已经刷到第几只
        self.shifted = False                      # 30s 阶段切换只允许触发一次
        self.result = None

        # 开场动画：完整黑码 → 抖两下震碎 → 碎片下沉 → 灰色提示浮现
        # 这 2 秒里不计时、不出怪、不响应涂改，动画放完才显示 LEVEL n 横幅
        self.intro_t = INTRO_TOTAL
        self.debris = []
        self.shake_t = 0.0
        self.shake_started = False
        self.shake_off = (0, 0)
        self.burst_done = False
        self.hint_alpha = 0
        self.triggered = False
        # 开场句在动画期间用底部字幕条显示：动画有 3 秒，刚好够读完，且不挡棋盘
        self.show_banner(story.level(self.level)["open"], INTRO_TOTAL, "story")

    def show_banner(self, text, secs, kind="big"):
        """kind="big" 是整屏大字（PHASE SHIFT）；"story" 是底部字幕条（剧情句，不挡棋盘）。"""
        self.banner_text = text
        self.banner_t = secs
        self.banner_total = secs
        self.banner_kind = kind

    # ---------- 开场动画 ----------
    def update_intro(self, dt):
        """完整黑码 → 抖动震碎 → 碎片下沉 → 灰色提示浮现。期间不计时。"""
        t = INTRO_TOTAL - self.intro_t            # 动画已经过去的时长
        self.intro_t -= dt

        # 1) 先抖三下，抖到中段才震碎：抖动起点比震碎点提前 SHAKE_LEAD 下
        if not self.shake_started and t >= INTRO_SHOW - SHAKE_STEP * SHAKE_LEAD:
            self.shake_t = SHAKE_STEP * len(SHAKE_SEQ)
            self.shake_started = True
        if not self.burst_done and t >= INTRO_SHOW:
            self.burst()                          # 每个黑格变成一块碎片
            self.burst_done = True

        # 2) 抖动：按固定序列取偏移，抖 6 下、幅度递减（比 sin 更可控）
        if self.shake_t > 0:
            self.shake_t = max(0.0, self.shake_t - dt)
            total = SHAKE_STEP * len(SHAKE_SEQ)
            idx = int((total - self.shake_t) / SHAKE_STEP)
            self.shake_off = SHAKE_SEQ[min(idx, len(SHAKE_SEQ) - 1)]
        else:
            self.shake_off = (0, 0)

        # 3) 碎片物理：初速向外炸，重力把它们一路拽到屏幕下方
        alive = []
        for d in self.debris:
            d[3] += DEBRIS_GRAVITY * dt
            d[0] += d[2] * dt
            d[1] += d[3] * dt
            if d[1] < WINDOW_H + CELL:            # 掉出屏幕底部就回收
                alive.append(d)
        self.debris = alive

        # 4) 灰色提示层淡入（碎片基本落完之后才开始浮现）
        fade_start = INTRO_SHOW + INTRO_FALL
        if t >= fade_start:
            self.hint_alpha = int(255 * min(1.0, (t - fade_start) / INTRO_FADE))

        # 5) 结束：恢复正常玩法，计时从这里才开始跑
        if self.intro_t <= 0:
            self.intro_t = 0.0
            self.debris.clear()
            self.shake_off = (0, 0)
            self.hint_alpha = 255

    def burst(self):
        """把完整二维码的每个黑格变成一块碎片，从网格中心向外炸开。"""
        orr, occ = TARGET_OFFSET
        cx, cy = WINDOW_W / 2.0, WINDOW_H / 2.0
        self.debris = []
        for tr in range(TARGET_N):
            row = self.target[tr]
            for tc in range(TARGET_N):
                if not row[tc]:
                    continue
                x, y = cell_center(orr + tr, occ + tc)
                dx, dy = x - cx, y - cy
                dist = (dx * dx + dy * dy) ** 0.5 or 1.0
                speed = random.uniform(*DEBRIS_SPEED)
                vx = dx / dist * speed + random.uniform(-DEBRIS_JITTER, DEBRIS_JITTER)
                vy = dy / dist * speed - random.uniform(0, DEBRIS_UP)
                self.debris.append([x - CELL / 2.0, y - CELL / 2.0, vx, vy])

    # ---------- 事件 ----------
    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.on_click(*self.mouse_xy())        # 鼠标只用于菜单，不参与涂色
            return
        if e.type != pygame.KEYDOWN:               # 与 input.handle_event 互不排斥
            return
        if e.scancode == SC_F1:
            self.debug = not self.debug
            return

        st = self.state
        if e.scancode == SC_ESC:
            if st == "TITLE":
                self.running = False               # 开始页是顶层，这里才真的退出
            elif st == "SELECT":
                self.state = "TITLE"
            else:
                self.goto_select()                 # 局中/结算都回选关页
        elif st == "TITLE":
            if e.scancode in (SC_ENTER, SC_KP_ENTER, SC_SPACE):
                self.state = "SELECT"
        elif st == "SELECT":
            self.on_select_key(e.scancode)
        elif st == "PLAY":
            if e.scancode == SC_R:
                self.start_level(self.level)       # 局中 R：重开本关
        elif st == "RESULT":
            if e.scancode == SC_R:
                self.next_level()

    # ---------- 按钮与选关 ----------
    def mouse_xy(self):
        """窗口坐标 → 逻辑坐标（画布被缩放过，鼠标也得换算）。"""
        mx, my = pygame.mouse.get_pos()
        return int(mx / self.scale), int(my / self.scale)

    def start_btn(self):
        return pygame.Rect((WINDOW_W - BTN_W) // 2, 470, BTN_W, BTN_H)

    def level_btns(self):
        n = len(LEVELS)
        total = n * LV_BTN_W + (n - 1) * LV_BTN_GAP
        x0 = (WINDOW_W - total) // 2
        return [pygame.Rect(x0 + i * (LV_BTN_W + LV_BTN_GAP), 392, LV_BTN_W, LV_BTN_H)
                for i in range(n)]

    def on_click(self, x, y):
        if self.state == "TITLE":
            if self.start_btn().collidepoint(x, y):
                self.state = "SELECT"
        elif self.state == "SELECT":
            for i, rect in enumerate(self.level_btns()):
                if rect.collidepoint(x, y) and i + 1 <= self.unlocked:
                    self.sel = i + 1
                    self.start_level(i + 1)        # 锁着的关点了没反应

    def on_select_key(self, sc):
        if sc in (SC_A, SC_LEFT):
            self.sel = max(1, self.sel - 1)
        elif sc in (SC_D, SC_RIGHT):
            self.sel = min(self.unlocked, self.sel + 1)   # 只能移到已解锁的关
        elif sc in (SC_ENTER, SC_KP_ENTER, SC_SPACE):
            self.start_level(self.sel)

    def goto_select(self):
        self.sel = max(1, min(self.unlocked, self.level))
        self.state = "SELECT"

    def start_level(self, n):
        self.level = max(1, min(len(LEVELS), n))
        self.new_round()
        self.input.held.clear()                    # 别让菜单里按着的键漏进新一局

    def next_level(self):
        """结算页按 R：赢了进下一关，最后一关通关回选关页，输了重试本关。"""
        if not self.result["won"]:
            self.start_level(self.level)
        elif self.level < len(LEVELS):
            self.start_level(self.level + 1)
        else:
            self.goto_select()                     # 全部通关：回选关页，五关都开着

    def update_hover(self):
        """每帧轮询鼠标位置做悬停高亮（点击走事件，悬停只能轮询）。"""
        mx, my = self.mouse_xy()
        self.hover = None
        if self.state == "TITLE":
            if self.start_btn().collidepoint(mx, my):
                self.hover = 0
        else:
            for i, rect in enumerate(self.level_btns()):
                if rect.collidepoint(mx, my):
                    self.hover = i
                    break

    # ---------- 更新 ----------
    def update(self, dt):
        self._last_dt = dt                        # 仅供 F1 显示
        if self.state in ("TITLE", "SELECT"):
            self.menu_t += dt                     # 只用来闪字
            self.update_hover()
            return
        if self.state != "PLAY":
            return
        if self.intro_t > 0:                      # 开场动画期间：不计时、不出怪、不能涂
            self.update_intro(dt)
            return
        if self.banner_t > 0:
            self.banner_t -= dt

        # 1) 先走格子：移动是离散步进，脚下坐标一帧内就定死
        self.player.update(dt, self.input.dir4())
        # 走过的地方就记住了（重复调用无副作用，所以每帧标一次最省事）
        self.board.mark_seen(*self.player.cell)

        # 2) 再处理脚下：按住 J（或空格）边走边涂，按住 K 边走边抹
        #    放在移动之后，所以走进新格子的那一帧它就变黑，不会「走过一格还得补一下」
        if self.input.down(SC_J) or self.input.down(SC_SPACE):
            self.board.paint(*self.player.cell)
        elif self.input.down(SC_K):
            self.board.start_erase(*self.player.cell)

        # 3) 计时
        self.elapsed += dt

        # 4) 阶段切换：只触发一次，靠布尔守卫（不能用 abs(elapsed-30) < dt）
        if not self.shifted and self.elapsed >= PHASE1_DURATION:
            self.shifted = True
            self.board.outer_open = False         # 外围锁死：已黑保留，未黑不可涂
            self.show_banner("PHASE SHIFT", PHASE_SHIFT_TIME, "big")   # 只触发这一次

        # 5) 先让抹除收敛，再跑怪物（顺序反了会「吃到空气」）
        self.board.update(dt)

        # 6) 怪物：目标失效会自己改道，吃到就死，闲着超时也死
        for m in self.monsters[:]:
            if not m.update(dt, self.board, self.claims, self.center):
                self.monsters.remove(m)

        # 7) 生成：全程恒定 15/分，用累加器，不用 set_timer
        self.spawn_acc += dt
        interval = 60.0 / self.spawn_rate
        if self.elapsed > self.spawn_delay and self.spawn_acc >= interval:
            self.spawn_acc -= interval
            self.spawn_monster()

        # 7.5) 紫怪：数量和时间点都在 new_round 里定好，到点各刷一只
        if self.purple_i < len(self.purple_times) and self.elapsed >= self.purple_times[self.purple_i]:
            self.purple_i += 1
            self.spawn_monster("purple")
            self.fire_trigger()                   # 第一只紫怪登场 → 本关那句现象描述

        # 8) 时间到 -> 结算
        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.finish()

    def fire_trigger(self):
        """本关的「局中一次性」剧情句：只在第一次该事件发生时弹，之后不再打扰。"""
        if self.triggered:
            return
        line = story.level(self.level)["trigger"]
        if not line:
            return
        self.triggered = True
        self.show_banner(line, STORY_BANNER_TIME, "story")

    def spawn_monster(self, kind="red"):
        """在 30×30 生成环的四条边上等概率取点：先选边再选 t，长边不会被多算。"""
        side = self.rng.randrange(4)
        t = self.rng.random() * SPAWN_PX
        x0, y0 = SPAWN_ORIGIN
        if side == 0:
            pos = (x0 + t, y0)
        elif side == 1:
            pos = (x0 + SPAWN_PX, y0 + t)
        elif side == 2:
            pos = (x0 + t, y0 + SPAWN_PX)
        else:
            pos = (x0, y0 + t)
        base = PURPLE_SPEED if kind == "purple" else MONSTER_SPEED
        speed = base * self.rng.uniform(*MONSTER_SPD_JITTER)
        # 紫怪专挑「完成度最高的那一行」（config.PURPLE_MODE 可切回 nearest）
        mode = PURPLE_MODE if kind == "purple" else "nearest"
        self.monsters.append(Monster(pos, speed, kind, mode))

    def finish(self):
        """结算：只统计 21×21 目标区，外围诱饵不加分也不扣分。"""
        for m in self.monsters:            # 结算时松开所有占用，claims 必须归零
            m.claim(self.claims)
        correct, noise, missing = self.board.stats()
        total = self.board.target_total or 1
        cap = round(total * self.goal_noise)
        coverage = correct / total
        won = coverage >= self.goal_cover and noise <= cap
        if won and coverage >= GRADE_S_COVERAGE and noise <= GRADE_S_NOISE:
            grade = "S"
        elif won and noise <= cap * GRADE_A_NOISE_PCT:
            grade = "A"
        elif won:
            grade = "B"
        else:
            grade = "F"
        self.result = {"coverage": coverage, "noise": noise, "cap": cap,
                       "won": won, "grade": grade, "level": self.level}
        if won:                                    # 过关就解锁下一关（末关解锁到头为止）
            self.unlocked = max(self.unlocked, min(len(LEVELS), self.level + 1))
        self.state = "RESULT"

    # ---------- 绘制（具体画法都在 ui.py） ----------
    def present(self):
        """把逻辑画布整帧缩放进真实窗口。"""
        if self.needs_scale:
            pygame.transform.smoothscale(self.canvas, self.window.get_size(), self.window)
        else:
            self.window.blit(self.canvas, (0, 0))

    def apply_shake(self):
        """整屏抖动：把已经画好的画面按偏移量重新贴一次（只在开场那几帧发生）。"""
        dx, dy = self.shake_off
        if dx == 0 and dy == 0:
            return
        self.shake_buf.blit(self.canvas, (0, 0))
        self.canvas.fill(C_BG)
        self.canvas.blit(self.shake_buf, (dx, dy))

    def draw(self):
        if self.state == "TITLE":
            draw_title(self)
        elif self.state == "SELECT":
            draw_select(self)
        elif self.state == "RESULT":
            draw_result(self)
        else:
            draw_world(self)
            draw_hud(self)
            draw_banner(self)
            self.apply_shake()
        self.present()
