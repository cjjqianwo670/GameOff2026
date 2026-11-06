# -*- coding: utf-8 -*-
"""
DATA SHIFT —— Game Off 2026 / SHIFT
进度：M1（窗口 / 网格 / 涂抹 / WASD / 计时）+ M2（二维码 / 提示层 / 进度条）
运行：python main.py（只依赖 pygame）
窗口按桌面自动等比缩小，内部逻辑坐标始终 1000×1000；界面文字全为 ASCII 大写。
"""

import math
import random

import pygame

# ==== 1. 常量与颜色 ====

# ==== 画面 ====
WINDOW_W = WINDOW_H = 1000        # 逻辑画布尺寸（所有布局都按它算）
FPS = 60
CELL = 28
GRID_N = 24
GRID_ORIGIN = (164, 164)          # (1000-672)/2
TARGET_N = 21
TARGET_OFFSET = (1, 1)            # 24-21=3 是奇数，只能左/上留 1 格
SPAWN_N = 30
SPAWN_ORIGIN = (80, 80)
SPAWN_PX = SPAWN_N * CELL         # 840

# 窗口自适应：高 DPI 屏逻辑分辨率常只有 1400×900 上下，1000×1000 会溢出屏幕，
# 所以真实窗口按桌面可用空间缩、画面整帧贴进去，逻辑坐标始终是 1000×1000。
FIT_MARGIN_X, FIT_MARGIN_Y = 80, 120   # 预留左右边距 + 标题栏 + 任务栏
MIN_WINDOW = 520                        # 再小就看不清了

GRID_PX = GRID_N * CELL           # 672
TARGET_PX = TARGET_N * CELL       # 588

# ==== 颜色 ====
C_BG = (11, 15, 20)               # 窗外废墟底色
C_BG_GRID = (18, 24, 32)          # 废墟暗格
C_CELL_WHITE = (247, 247, 249)    # 未涂黑格子
C_CELL_LINE = (228, 228, 232)     # 格子分隔线
C_CELL_BLACK = (17, 17, 24)       # 已涂黑
C_GHOST = (60, 60, 70, 110)       # 目标提示（半透明深灰，SRCALPHA）
C_ERASING = (150, 150, 160)       # 抹除进行中
C_LOCK = (30, 36, 45)             # 阶段2 锁定区遮罩
C_MONSTER = (255, 61, 110)        # 侵蚀体猩红（M3 使用）
C_PLAYER = (108, 255, 196)        # 玩家（青绿）
C_ACCENT = (108, 255, 196)        # 进度条
C_WARN = (255, 176, 32)           # 警示黄
C_TEXT = (232, 236, 240)

# ==== 规则 ====
GAME_DURATION = 180.0
PHASE1_DURATION = 30.0
ERASE_CAST = 0.25
WIN_COVERAGE = 0.70
NOISE_LIMIT_PCT = 0.25
# 目标黑格占比下限：低于它的一版太稀、太难 70%，重摇（§14 平衡值约 220/441 ≈ 0.50）
ALPHA_MIN = 0.48
ALPHA_TRY = 40                    # 重摇次数上限，兜底取最密的一版

# ==== 玩家 ====
PLAYER_SPEED = 210.0              # px/s
PLAYER_ACCEL = 18.0               # 速度平滑系数
PLAYER_START = (500, 500)
PAINT_MODE = "global"             # "global" | "radius"
PAINT_RADIUS = 220

PLAYER_BODY_W, PLAYER_BODY_H = 16, 22
PLAYER_GLOW_R = 14
CLAMP_PAD = 8                     # 角色可越出网格 8px

# ==== 怪物（M3 才用，先占位保证常量区完整） ====
SPAWN_PER_MINUTE = 15
SPAWN_FIRST_DELAY = 2.0
MONSTER_SPEED = 62.0
MONSTER_RADIUS = 9
MONSTER_IDLE_LIMIT = 12.0

# ==== 输入：scancode 是物理键位，与输入法/CapsLock/Shift 无关 ====
SC_W, SC_A, SC_S, SC_D = 26, 4, 22, 7
SC_R, SC_ESC, SC_F1 = 21, 41, 58

# ==== 格子状态 ====
WHITE, BLACK, ERASING = 0, 1, 2

# ==== 布局：HUD ====
HUD_PAD = 80
BAR_W, BAR_H = 320, 10

# ==== 2. 坐标工具函数（全局只用这三个做换算） ====

def cell_to_rect(r, c):
    return pygame.Rect(GRID_ORIGIN[0] + c * CELL,
                       GRID_ORIGIN[1] + r * CELL, CELL, CELL)

def pos_to_cell(x, y):
    """屏幕坐标 → (row, col)；不在主网格内返回 None。"""
    gx, gy = x - GRID_ORIGIN[0], y - GRID_ORIGIN[1]
    if gx < 0 or gy < 0:
        return None
    c, r = gx // CELL, gy // CELL
    if r >= GRID_N or c >= GRID_N:
        return None
    return int(r), int(c)

def to_target(r, c):
    """主网格坐标 → 目标区坐标 (tr, tc)；不在目标区内返回 None。"""
    tr, tc = r - TARGET_OFFSET[0], c - TARGET_OFFSET[1]
    if 0 <= tr < TARGET_N and 0 <= tc < TARGET_N:
        return tr, tc
    return None

# ==== 3. generate_target() ====

def generate_target(rng, n=TARGET_N):
    """程序化生成 21×21「形似 QR」的 0/1 矩阵：保留定位图案/时序线/暗模块，信息区随机。

    不用真 QR 库（每局都长一样、密度不可控）。密度只做下限保护：信息区按 0.5 填，
    期望约 50%（≈220 格，对上 §14）；太稀就重摇，重摇有上限并取最密兜底，绝不递归。
    """
    floor = n * n * ALPHA_MIN
    best, best_cnt = None, -1
    for _ in range(ALPHA_TRY):
        m = _build_qr_like(rng, n)
        cnt = sum(map(sum, m))
        if cnt > best_cnt:
            best, best_cnt = m, cnt
        if cnt >= floor:
            return m
    return best

def _build_qr_like(rng, n):
    m = [[0] * n for _ in range(n)]
    reserved = [[False] * n for _ in range(n)]

    # (1) 三个 7×7 定位图案，连同外围 1 格白色分隔带一起标记 reserved
    for r0, c0 in ((0, 0), (0, n - 7), (n - 7, 0)):
        for r in range(r0 - 1, r0 + 8):
            for c in range(c0 - 1, c0 + 8):
                if 0 <= r < n and 0 <= c < n:
                    reserved[r][c] = True
        for dr in range(7):
            for dc in range(7):
                ring = dr in (0, 6) or dc in (0, 6)
                core = 2 <= dr <= 4 and 2 <= dc <= 4
                m[r0 + dr][c0 + dc] = 1 if (ring or core) else 0

    # (2) 时序线：第 6 行 / 第 6 列，一黑一白交错
    for i in range(n):
        if not reserved[6][i]:
            m[6][i] = 1 if i % 2 == 0 else 0
            reserved[6][i] = True
        if not reserved[i][6]:
            m[i][6] = 1 if i % 2 == 0 else 0
            reserved[i][6] = True

    # (3) 暗模块（QR 规范里的固定黑点）
    m[n - 8][8] = 1
    reserved[n - 8][8] = True

    # (4) 信息区随机填充
    for r in range(n):
        for c in range(n):
            if not reserved[r][c]:
                m[r][c] = 1 if rng.random() < 0.50 else 0
    return m

# ==== 4. class Board ====

class Board:
    def __init__(self, target):
        self.target = target                                   # 21×21 的 0/1
        self.target_total = sum(map(sum, target))              # 目标黑格总数
        self.state = [[WHITE] * GRID_N for _ in range(GRID_N)]
        self.erase_t = [[0.0] * GRID_N for _ in range(GRID_N)]
        self.flash = {}                                        # {(r,c): 剩余秒}，M3 啃食红闪
        # M1/M2 恒为 True：全网格可涂。M4 只需在 30s 时把它置 False，外围即锁死
        self.outer_open = True

    # --- 查询 ---
    def cell_ok_for_paint(self, r, c):
        if self.outer_open:
            return True
        return to_target(r, c) is not None

    def cell_ok_for_erase(self, r, c):
        # ERASING 期间既不可再涂也不可再抹，避免计时被重置
        return self.state[r][c] == BLACK and self.cell_ok_for_paint(r, c)

    def stats(self):
        """只统计 21×21 目标区，外围诱饵不加分也不扣分。"""
        correct = noise = missing = 0
        orr, occ = TARGET_OFFSET
        for tr in range(TARGET_N):
            for tc in range(TARGET_N):
                st = self.state[orr + tr][occ + tc]
                if self.target[tr][tc]:
                    if st == BLACK:
                        correct += 1
                    else:
                        missing += 1
                elif st == BLACK:
                    noise += 1
        return correct, noise, missing

    # --- 操作 ---
    def paint(self, r, c):
        """幂等：拖动时每帧都会调用，已是黑/正在抹除就直接返回。"""
        if self.state[r][c] != WHITE:
            return
        if not self.cell_ok_for_paint(r, c):
            return
        self.state[r][c] = BLACK

    def start_erase(self, r, c):
        if not self.cell_ok_for_erase(r, c):
            return
        self.state[r][c] = ERASING
        self.erase_t[r][c] = ERASE_CAST

    def force_white(self, r, c):
        """怪物啃食：无条件变白 + 红闪（M3 调用）。"""
        self.state[r][c] = WHITE
        self.erase_t[r][c] = 0.0
        self.flash[(r, c)] = 0.15

    def update(self, dt):
        for r in range(GRID_N):
            for c in range(GRID_N):
                if self.state[r][c] == ERASING:
                    self.erase_t[r][c] -= dt
                    if self.erase_t[r][c] <= 0:
                        self.state[r][c] = WHITE
        for k in list(self.flash):
            self.flash[k] -= dt
            if self.flash[k] <= 0:
                del self.flash[k]

# ==== 5. class InputState ====

class InputState:
    """WASD 三层保险：关文本输入 + scancode 事件 + scancode 索引兜底。

    IME 候选窗会吃掉字母键的 KEYDOWN，keycode 又可能被当物理键号查表（幽灵移动），
    scancode 是 USB-HID 物理键位，与布局/CapsLock/Shift/输入法无关。
    """

    def __init__(self):
        try:
            pygame.key.stop_text_input()   # 本游戏不需要打字，让 IME 退化为英文直通
        except Exception:
            pass
        self.held = set()                  # 存 scancode

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            self.held.add(e.scancode)
        elif e.type == pygame.KEYUP:
            self.held.discard(e.scancode)
        elif e.type == pygame.WINDOWFOCUSLOST:
            self.held.clear()              # 防 Alt+Tab 后按键卡死

    def axis(self):
        v = pygame.Vector2(0, 0)
        p = pygame.key.get_pressed()
        if SC_W in self.held or p[SC_W]:
            v.y -= 1
        if SC_S in self.held or p[SC_S]:
            v.y += 1
        if SC_A in self.held or p[SC_A]:
            v.x -= 1
        if SC_D in self.held or p[SC_D]:
            v.x += 1
        if v.length_squared() > 0:
            v.normalize_ip()               # 斜向不加速
        return v

# ==== 6. class Player ====

class Player:
    def __init__(self):
        self.pos = pygame.Vector2(PLAYER_START)
        self.vel = pygame.Vector2(0, 0)
        self.facing = 1                    # 0上 1下 2左 3右

    def update(self, dt, axis):
        target = axis * PLAYER_SPEED
        # 指数收敛：约 0.06s 到位，松手即停，不做滑冰感
        self.vel += (target - self.vel) * (1.0 - math.exp(-PLAYER_ACCEL * dt))
        self.pos += self.vel * dt

        pad = CLAMP_PAD
        minx = GRID_ORIGIN[0] - pad
        maxx = GRID_ORIGIN[0] + GRID_PX + pad
        miny = GRID_ORIGIN[1] - pad
        maxy = GRID_ORIGIN[1] + GRID_PX + pad
        self.pos.x = min(max(self.pos.x, minx), maxx)
        self.pos.y = min(max(self.pos.y, miny), maxy)

        if axis.x or axis.y:
            if abs(axis.x) >= abs(axis.y):
                self.facing = 3 if axis.x > 0 else 2
            else:
                self.facing = 1 if axis.y > 0 else 0

    def can_reach(self, rect):
        if PAINT_MODE == "global":
            return True
        return (self.pos - pygame.Vector2(rect.center)).length() <= PAINT_RADIUS

# ==== 7. class Monster（M3：生成环取点 / 最近黑格选目标 / 走到就吃 / 吃完自删） ====

# ==== 8. class Game ====

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

        # 28×28 的半透明提示块反复复用（每帧新建 400 个 Surface 会掉帧）
        self.ghost = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.ghost.fill(C_GHOST)

        # 玩家脚下光晕，同样只做一次
        self.glow = pygame.Surface((PLAYER_GLOW_R * 2, PLAYER_GLOW_R * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.glow, (*C_PLAYER, 46), (PLAYER_GLOW_R, PLAYER_GLOW_R), PLAYER_GLOW_R)

        # 被啃格的红闪覆盖层（半透明），M3 复用，同样只做一次
        self.flash_surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.flash_surf.fill((*C_MONSTER, 120))

        self.new_round()

    # ---------- 开局 ----------
    def new_round(self):
        rng = random.Random()                     # 不固定种子：R 重开必出新码
        self.target = generate_target(rng)
        self.board = Board(self.target)
        self.player = Player()
        self.elapsed = 0.0
        self.state = "PLAY"                       # MENU / RESULT 在 M4~M5 接入

    # ---------- 事件 ----------
    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:              # 与 input.handle_event 互不排斥
            if e.scancode == SC_R:
                self.new_round()
            elif e.scancode == SC_ESC:
                self.running = False              # M5 改成回 MENU
            elif e.scancode == SC_F1:
                self.debug = not self.debug

    # ---------- 更新 ----------
    def update(self, dt):
        self._last_dt = dt                        # 仅供 F1 显示
        if self.state != "PLAY":
            return

        # 1) 键盘移动必须在鼠标之前，否则拖涂时会感觉角色慢一帧
        self.player.update(dt, self.input.axis())

        # 2) 鼠标：每帧轮询，不依赖 MOUSEBUTTONDOWN，拖动才连续
        cell = pos_to_cell(*self.mouse_logical())
        if cell:
            lmb, _, rmb = pygame.mouse.get_pressed()
            if lmb:
                if self.player.can_reach(cell_to_rect(*cell)):
                    self.board.paint(*cell)
            elif rmb:
                self.board.start_erase(*cell)

        # 3) 计时（阶段锁定属 M4，这里只跑表）
        self.elapsed += dt

        # 4) 先让抹除收敛，再进 M3 的怪物逻辑
        self.board.update(dt)

        # 5) 时间到 —— M4 在此切 RESULT，现在只把表停住
        if self.elapsed >= GAME_DURATION:
            self.elapsed = GAME_DURATION

    # ---------- 绘制 ----------
    def mouse_logical(self):
        """窗口坐标 → 逻辑坐标（窗口被缩过的时候必须换算，否则涂不准）。"""
        mx, my = pygame.mouse.get_pos()
        return mx / self.scale, my / self.scale

    def present(self):
        if self.needs_scale:
            pygame.transform.smoothscale(self.canvas, self.window.get_size(), self.window)
        else:
            self.window.blit(self.canvas, (0, 0))

    def draw(self):
        self.draw_world()
        self.draw_hud()
        self.present()

    def draw_world(self):
        s = self.screen
        s.fill(C_BG)

        # 废墟暗格：每 28px 一层暗线，主网格盖上去之后只剩网格外的部分可见
        for x in range(0, WINDOW_W, CELL):
            pygame.draw.line(s, C_BG_GRID, (x, 0), (x, WINDOW_H))
        for y in range(0, WINDOW_H, CELL):
            pygame.draw.line(s, C_BG_GRID, (0, y), (WINDOW_W, y))

        # 生成环虚线框：提示怪物从这条线外来
        self.draw_dashed_rect(s, pygame.Rect(SPAWN_ORIGIN, (SPAWN_PX, SPAWN_PX)))

        # 白底：锁定遮罩属 M4，现在全部按可涂状态画
        for r in range(GRID_N):
            for c in range(GRID_N):
                if self.board.state[r][c] == WHITE:
                    s.fill(C_CELL_WHITE, cell_to_rect(r, c))

        # 目标提示层：只有「该黑且还白」的格子才叠，强度低到不盖住网格线
        orr, occ = TARGET_OFFSET
        for tr in range(TARGET_N):
            row = self.target[tr]
            for tc in range(TARGET_N):
                if row[tc] and self.board.state[orr + tr][occ + tc] == WHITE:
                    s.blit(self.ghost, (GRID_ORIGIN[0] + (occ + tc) * CELL,
                                        GRID_ORIGIN[1] + (orr + tr) * CELL))

        # 网格线：整片画线比每格描边便宜，且不会被提示块吃掉
        for i in range(GRID_N + 1):
            x = GRID_ORIGIN[0] + i * CELL
            y = GRID_ORIGIN[1] + i * CELL
            pygame.draw.line(s, C_CELL_LINE, (x, GRID_ORIGIN[1]), (x, GRID_ORIGIN[1] + GRID_PX))
            pygame.draw.line(s, C_CELL_LINE, (GRID_ORIGIN[0], y), (GRID_ORIGIN[0] + GRID_PX, y))

        # 已涂黑 / 抹除中 / 被啃红闪
        for r in range(GRID_N):
            for c in range(GRID_N):
                st = self.board.state[r][c]
                if st == BLACK:
                    s.fill(C_CELL_BLACK, cell_to_rect(r, c))
                elif st == ERASING:
                    rect = cell_to_rect(r, c)
                    s.fill(C_ERASING, rect)
                    # 抹除灰与提示灰明度只差 15，靠颜色分不清，让中心白块从 0 撑到满格
                    k = 1.0 - self.board.erase_t[r][c] / ERASE_CAST
                    inset = int(CELL * 0.5 * (1.0 - k))
                    if inset > 0:
                        s.fill(C_CELL_WHITE, rect.inflate(-2 * inset, -2 * inset))
        for (r, c) in self.board.flash:
            s.blit(self.flash_surf, (GRID_ORIGIN[0] + c * CELL, GRID_ORIGIN[1] + r * CELL))

        # M3：怪物画在这里

        self.draw_player(s)

    def draw_player(self, s):
        px, py = int(self.player.pos.x), int(self.player.pos.y)
        s.blit(self.glow, (px - PLAYER_GLOW_R, py - PLAYER_GLOW_R))

        if PAINT_MODE == "radius":                # 只有切到 radius 才显示射程
            pygame.draw.circle(s, C_ACCENT, (px, py), PAINT_RADIUS, 1)

        body = pygame.Rect(px - PLAYER_BODY_W // 2, py - PLAYER_BODY_H // 2,
                           PLAYER_BODY_W, PLAYER_BODY_H)
        pygame.draw.rect(s, C_PLAYER, body, border_radius=5)

        # 4×4 的「眼」按朝向偏移，让角色在静止时也有方向感
        ex, ey = px - 2, py - 2
        if self.player.facing == 0:
            ey = body.top + 4
        elif self.player.facing == 1:
            ey = body.bottom - 8
        elif self.player.facing == 2:
            ex = body.left + 3
        else:
            ex = body.right - 7
        s.fill(C_CELL_BLACK, pygame.Rect(ex, ey, 4, 4))

    def draw_dashed_rect(self, s, rect, dash=12, color=C_CELL_LINE):
        for x in range(rect.left, rect.right, dash * 2):
            x2 = min(x + dash, rect.right)
            pygame.draw.line(s, color, (x, rect.top), (x2, rect.top))
            pygame.draw.line(s, color, (x, rect.bottom), (x2, rect.bottom))
        for y in range(rect.top, rect.bottom, dash * 2):
            y2 = min(y + dash, rect.bottom)
            pygame.draw.line(s, color, (rect.left, y), (rect.left, y2))
            pygame.draw.line(s, color, (rect.right, y), (rect.right, y2))

    # ---------- HUD ----------
    def txt(self, text, pos, font, color, right=False):
        """right=True 时 pos 是右上角，用来把文字贴住右侧 HUD 边距。"""
        img = font.render(text, True, color)
        self.screen.blit(img, img.get_rect(topright=pos) if right else img.get_rect(topleft=pos))

    def draw_hud(self):
        s = self.screen
        correct, noise, _missing = self.board.stats()
        total = self.board.target_total or 1     # 百分比一律除 target_total，不写死 441
        coverage = correct / total
        noise_cap = round(total * NOISE_LIMIT_PCT)

        top_y, mid_y = 38, 46

        # 计时：剩余 ≤30s 转警示黄
        remain = max(0.0, GAME_DURATION - self.elapsed)
        t_col = C_WARN if remain <= 30.0 else C_TEXT
        self.txt("%02d:%02d" % (int(remain) // 60, int(remain) % 60), (HUD_PAD, top_y),
                 self.f_main, t_col)

        # 进度条 + 70% 胜利线（唯一的目标锚点）
        bar = pygame.Rect(210, mid_y, BAR_W, BAR_H)
        s.fill(C_LOCK, bar)
        s.fill(C_ACCENT, pygame.Rect(bar.x, bar.y, int(BAR_W * min(coverage, 1.0)), bar.h))
        win_x = bar.x + int(BAR_W * WIN_COVERAGE)
        pygame.draw.line(s, C_TEXT, (win_x, bar.y - 4), (win_x, bar.y + BAR_H + 4), 2)

        pct_col = C_ACCENT if coverage >= WIN_COVERAGE else C_TEXT
        self.txt("%d%%" % int(coverage * 100), (bar.right + 20, top_y), self.f_main, pct_col)

        # 噪声：超过上限 80% 变黄，给玩家「快废了」的预警
        n_col = C_WARN if noise > noise_cap * 0.8 else C_TEXT
        self.txt("NOISE %d/%d" % (noise, noise_cap), (WINDOW_W - HUD_PAD, top_y),
                 self.f_main, n_col, right=True)

        # 底部：阶段标签跟 board.outer_open 走（M4 翻掉开关，文案自动变）+ 操作提示
        phase2 = not self.board.outer_open
        self.txt("PHASE 2 // LOCKED" if phase2 else "PHASE 1 // FREEFORM",
                 (HUD_PAD, WINDOW_H - 62), self.f_main,
                 C_ERASING if phase2 else C_ACCENT)
        self.txt("[WASD] MOVE   [LMB] PAINT   [RMB] ERASE   [R] RESTART",
                 (WINDOW_W - HUD_PAD, WINDOW_H - 62), self.f_small, C_TEXT, right=True)

        if self.debug:
            p = self.player.pos
            self.txt("FPS %d  POS %d,%d  TARGETS %d" % (
                int(round(1.0 / max(self._last_dt, 1e-4))), p.x, p.y, total),
                (HUD_PAD, 10), self.f_small, C_WARN)

# ==== 9. main() 主循环 ====

def create_window():
    """按桌面可用空间决定窗口尺寸（正方形），保证不被屏幕/任务栏裁掉。

    例：1920×1080 开 125% 缩放，逻辑桌面约 1460×910，可用高度 910-120=790，
    窗口就是 790×790，画面整体缩到 0.79 贴进去；桌面够大时缩放因子为 1.0。
    """
    info = pygame.display.Info()
    avail = min(info.current_w - FIT_MARGIN_X, info.current_h - FIT_MARGIN_Y)
    size = max(MIN_WINDOW, min(WINDOW_W, avail))
    return pygame.display.set_mode((size, size))

def main():
    pygame.init()
    window = create_window()
    pygame.display.set_caption("DATA SHIFT")
    clock = pygame.time.Clock()
    game = Game(window)

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 1 / 30)   # dt 上限防切窗口后瞬移
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            else:
                game.input.handle_event(e)           # 键盘状态
                game.handle_event(e)                 # R / ESC / F1，两者不互斥
        game.update(dt)
        game.draw()
        pygame.display.flip()
        if not game.running:
            running = False

    pygame.quit()

if __name__ == "__main__":
    main()
