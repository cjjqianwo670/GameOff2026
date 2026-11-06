# -*- coding: utf-8 -*-
"""
DATA SHIFT —— Game Off 2026 / SHIFT
进度：M1（窗口 / 网格 / 格子走位 / J 涂 K 抹 / 计时）+ M2（二维码 / 提示层 / 进度条）
操作：WASD 一格一格走；按住 J 边走边涂黑，K 抹除脚下；R 重开。全程只用键盘。
运行：python main.py（只依赖 pygame）
窗口按桌面自动等比缩小，内部逻辑坐标始终 1000×1000；界面文字全为 ASCII 大写。
"""

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

# ==== 颜色 ====
C_BG = (11, 15, 20)               # 窗外废墟底色
C_BG_GRID = (18, 24, 32)          # 废墟暗格
C_CELL_WHITE = (247, 247, 249)    # 未涂黑格子
C_CELL_LINE = (228, 228, 232)     # 格子分隔线
C_CELL_BLACK = (17, 17, 24)       # 已涂黑
C_GHOST = (60, 60, 70, 110)       # 目标提示（半透明深灰，SRCALPHA）
C_ERASING = (150, 150, 160)       # 抹除进行中
C_LOCK = (30, 36, 45)             # 阶段2 锁定区遮罩
C_MONSTER = (255, 61, 110)        # 侵蚀体猩红
C_PLAYER = (108, 255, 196)        # 玩家（青绿）
C_ACCENT = (108, 255, 196)        # 进度条 / 结算里的「涂对」
C_WARN = (255, 176, 32)           # 警示黄
C_MISSING = (46, 52, 62)          # 结算缩略图：该黑却没涂的格子
C_TEXT = (232, 236, 240)

# ==== 规则 ====
GAME_DURATION = 180.0
PHASE1_DURATION = 30.0
PHASE_SHIFT_TIME = 1.0            # 阶段切换遮罩持续时长（纯黑半透明 + 大字）
MENU_BLINK_HZ = 2.0               # 菜单「PRESS SPACE」闪烁频率
ERASE_CAST = 0.25
WIN_COVERAGE = 0.70
NOISE_LIMIT_PCT = 0.25
# 目标黑格占比下限：低于它的一版太稀、太难 70%，重摇（§14 平衡值约 220/441 ≈ 0.50）
ALPHA_MIN = 0.48
ALPHA_TRY = 40                    # 重摇次数上限，兜底取最密的一版

# ==== 玩家（格子对齐移动）====
PLAYER_START_CELL = (12, 12)      # 出生于主网格正中，一眼能看到脚下的目标区
MOVE_REPEAT = 0.13                # 长按方向键时每走一格的间隔（按下瞬间必定先走一格）
PLAYER_BODY_W, PLAYER_BODY_H = 16, 22
PLAYER_GLOW_R = 14

# ==== 怪物 ====
SPAWN_PER_MINUTE = 15
SPAWN_FIRST_DELAY = 2.0
MONSTER_SPEED = 62.0
MONSTER_RADIUS = 9
MONSTER_IDLE_LIMIT = 12.0
MONSTER_EAT_DIST = 6.0            # 到这个距离就算啃到，直接吃掉
MONSTER_RETRY = 0.5               # 场上没有黑格时，隔多久重试一次选目标
MONSTER_SPD_JITTER = (0.88, 1.12)  # 每只怪速度随机浮动，别齐步走

# ==== 结算 ====
THUMB_CELL = 10                   # 21×21 缩略图每格 10px → 210×210
GRADE_S_COVERAGE = 0.95           # S 级门槛
GRADE_S_NOISE = 3
GRADE_A_NOISE_PCT = 0.4           # A 级：噪声不超过上限的 40%

# ==== 输入：scancode 是物理键位，与输入法/CapsLock/Shift 无关 ====
SC_W, SC_A, SC_S, SC_D = 26, 4, 22, 7
SC_J, SC_K, SC_SPACE = 13, 14, 44   # J 涂黑 / K 抹除 / 空格=J 的别名
SC_R, SC_ESC, SC_F1 = 21, 41, 58
DIR_KEYS = {SC_W: (-1, 0), SC_S: (1, 0), SC_A: (0, -1), SC_D: (0, 1)}

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

def cell_center(r, c):
    """格子序号 → 该格中心的屏幕坐标（格子对齐移动后，角色位置直接取格心）。"""
    return (GRID_ORIGIN[0] + c * CELL + CELL // 2,
            GRID_ORIGIN[1] + r * CELL + CELL // 2)

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
    """全部键盘操作，三层保险：关文本输入 + scancode 事件 + scancode 索引兜底。

    IME 候选窗会吃掉字母键的 KEYDOWN，keycode 又可能被当物理键号查表（幽灵移动），
    scancode 是 USB-HID 物理键位，与布局/CapsLock/Shift/输入法无关。
    """

    def __init__(self):
        try:
            pygame.key.stop_text_input()   # 本游戏不需要打字，让 IME 退化为英文直通
        except Exception:
            pass
        self.held = set()                  # 存 scancode
        self.last_dir = None               # 最后按下的方向键，斜向时优先听它的

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            self.held.add(e.scancode)
            if e.scancode in DIR_KEYS:
                self.last_dir = e.scancode
        elif e.type == pygame.KEYUP:
            self.held.discard(e.scancode)
        elif e.type == pygame.WINDOWFOCUSLOST:
            self.held.clear()              # 防 Alt+Tab 后按键卡死
            self.last_dir = None

    def down(self, sc):
        # 事件集合优先，get_pressed 兜底（索引也用 scancode，最坏只是 False，不会幽灵移动）
        return sc in self.held or pygame.key.get_pressed()[sc]

    def dir4(self):
        """返回 (dr, dc) 或 None。格子移动只能四向，斜向按「最后按下」的那颗键走。"""
        if self.last_dir is not None and self.down(self.last_dir):
            return DIR_KEYS[self.last_dir]
        for sc, d in DIR_KEYS.items():     # 兜底：last_dir 键已松开时按固定顺序取
            if self.down(sc):
                return d
        return None

# ==== 6. class Player ====

class Player:
    """格子对齐（grid-based）：按一下走一格，位置永远是格心，不存在「半个身子在格子里」。"""

    def __init__(self):
        self.cell = PLAYER_START_CELL       # (row, col) 才是真身，pos 只是它的投影
        self.pos = pygame.Vector2(cell_center(*self.cell))
        self.facing = 1                     # 0上 1下 2左 3右
        self.repeat = 0.0                   # 长按连走的计时器

    def update(self, dt, d):
        if d is None:
            self.repeat = 0.0               # 松手归零，保证下次按下瞬间就走一格
            return
        self.repeat -= dt
        if self.repeat > 0:
            return
        self.repeat = MOVE_REPEAT
        nr, nc = self.cell[0] + d[0], self.cell[1] + d[1]
        if not (0 <= nr < GRID_N and 0 <= nc < GRID_N):
            return                          # 撞墙：原地不动，计时器照常重置，不会连环卡顿
        self.cell = (nr, nc)
        self.pos.update(cell_center(nr, nc))
        self.facing = (1 if d[0] > 0 else 0) if d[0] else (3 if d[1] > 0 else 2)

# ==== 7. class Monster ====

class Monster:
    """侵蚀体：从生成环进来，锁住最近的空闲黑格，走过去吃掉它，然后自毁。

    一生只吃 1 格。没有状态机、没有动画阶段——走到就吃，吃完就删。
    「最近黑格」天然就是诱饵机制：外围涂的黑格离生成环最近，怪自然先扑它们。
    """

    def __init__(self, pos, speed):
        self.pos = pygame.Vector2(pos)
        self.speed = speed
        self.target = None                 # (r, c) 或 None
        self.idle = 0.0                    # 无目标存活计时，超时自毁
        self.retry = 0.0                   # 无目标时多久重试一次

    def claim(self, claims):
        """松开手上锁的那一格，让别的怪可以抢。"""
        if self.target is not None:
            claims[self.target] -= 1
            if claims[self.target] <= 0:
                del claims[self.target]
            self.target = None

    def retarget(self, board, claims):
        """扫全网格找最近的黑格：优先没人锁的，全被锁了就允许重复，绝不卡死。"""
        self.claim(claims)
        free, any_cell = None, None
        free_d = any_d = None
        for r in range(GRID_N):
            row = board.state[r]
            for c in range(GRID_N):
                if row[c] != BLACK:        # ERASING 不吸引怪，规则同 §9.3
                    continue
                cx, cy = cell_center(r, c)
                d = (cx - self.pos.x) ** 2 + (cy - self.pos.y) ** 2
                if any_d is None or d < any_d:
                    any_cell, any_d = (r, c), d
                if not claims.get((r, c)) and (free_d is None or d < free_d):
                    free, free_d = (r, c), d
        pick = free or any_cell
        if pick is not None:
            claims[pick] = claims.get(pick, 0) + 1
            self.target = pick

    def update(self, dt, board, claims, center):
        """返回 False 表示这只怪该死（吃到了，或者闲着超时）。"""
        if self.target is not None:
            t = self.target
            if board.state[t[0]][t[1]] != BLACK:
                self.retarget(board, claims)     # 目标被吃了/被玩家抹了，立刻重选

        if self.target is None:
            self.idle += dt                      # 场上没黑格：朝中心漂一会儿，超时自毁
            to_c = center - self.pos
            if to_c.length_squared() > 1.0:
                self.pos += to_c.normalize() * self.speed * 0.5 * dt
            self.retry -= dt
            if self.retry <= 0:
                self.retry = MONSTER_RETRY
                self.retarget(board, claims)
            return self.idle < MONSTER_IDLE_LIMIT

        self.idle = 0.0
        cx, cy = cell_center(*self.target)
        d = pygame.Vector2(cx - self.pos.x, cy - self.pos.y)
        if d.length() <= MONSTER_EAT_DIST:
            board.force_white(*self.target)      # 变白 + 该格红闪
            self.claim(claims)
            return False                         # 吃完必死
        self.pos += d.normalize() * self.speed * dt
        return True

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
        self.f_mid = pygame.font.Font(None, 52)        # 结算页标题
        self.f_big = pygame.font.Font(None, 110)       # 结算页评级

        self.center = pygame.Vector2(WINDOW_W / 2, WINDOW_H / 2)   # 怪物无目标时的漂向点

        # 28×28 的半透明提示块反复复用（每帧新建 400 个 Surface 会掉帧）
        self.ghost = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.ghost.fill(C_GHOST)

        # 玩家脚下光晕，同样只做一次
        self.glow = pygame.Surface((PLAYER_GLOW_R * 2, PLAYER_GLOW_R * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.glow, (*C_PLAYER, 46), (PLAYER_GLOW_R, PLAYER_GLOW_R), PLAYER_GLOW_R)

        # 阶段切换用的整屏遮罩，只建一次，每帧重填内容
        self.overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        self.menu_t = 0.0

        # 被啃格的红闪覆盖层（半透明），M3 复用，同样只做一次
        self.flash_surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.flash_surf.fill((*C_MONSTER, 120))

        self.new_round()
        self.state = "MENU"                       # 开局先落在菜单（此时棋盘已备好一局）

    # ---------- 开局 ----------
    def new_round(self):
        self.rng = random.Random()                # 不固定种子：R 重开必出新码
        self.target = generate_target(self.rng)
        self.board = Board(self.target)
        self.player = Player()
        self.elapsed = 0.0
        self.state = "PLAY"                       # MENU 在 M5 接入

        self.monsters = []
        self.claims = {}                          # {(r,c): 有几只怪锁着这一格}
        self.spawn_acc = 0.0
        self.shifted = False                      # 30s 阶段切换只允许触发一次
        self.shift_timer = 0.0                    # 遮罩剩余时间
        self.result = None

    # ---------- 事件 ----------
    def handle_event(self, e):
        if e.type != pygame.KEYDOWN:              # 与 input.handle_event 互不排斥
            return
        if e.scancode == SC_ESC:
            if self.state == "MENU":
                self.running = False              # 菜单是顶层，这里才真的退出
            else:
                self.to_menu()
        elif e.scancode == SC_SPACE:
            if self.state == "MENU":
                self.start_round()
        elif e.scancode == SC_R:
            if self.state != "MENU":              # 局中/结算都能直接重开
                self.start_round()
        elif e.scancode == SC_F1:
            self.debug = not self.debug

    def start_round(self):
        self.new_round()
        self.input.held.clear()                   # 别让菜单里按着的空格/方向漏进新一局

    def to_menu(self):
        self.new_round()                          # 重置棋盘，菜单背后不挂着一个半死的局
        self.state = "MENU"

    # ---------- 更新 ----------
    def update(self, dt):
        self._last_dt = dt                        # 仅供 F1 显示
        if self.state == "MENU":
            self.menu_t += dt                     # 只用来闪「PRESS SPACE」
            return
        if self.state != "PLAY":
            return
        if self.shift_timer > 0:
            self.shift_timer -= dt

        # 1) 先走格子：移动是离散步进，脚下坐标一帧内就定死
        self.player.update(dt, self.input.dir4())

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
            self.shift_timer = PHASE_SHIFT_TIME   # 1s 遮罩 + 居中大字，只触发这一次

        # 5) 先让抹除收敛，再跑怪物（顺序反了会「吃到空气」）
        self.board.update(dt)

        # 6) 怪物：目标失效会自己改道，吃到就死，闲着超时也死
        for m in self.monsters[:]:
            if not m.update(dt, self.board, self.claims, self.center):
                self.monsters.remove(m)

        # 7) 生成：全程恒定 15/分，用累加器，不用 set_timer
        self.spawn_acc += dt
        interval = 60.0 / SPAWN_PER_MINUTE
        if self.elapsed > SPAWN_FIRST_DELAY and self.spawn_acc >= interval:
            self.spawn_acc -= interval
            self.spawn_monster()

        # 8) 时间到 -> 结算
        if self.elapsed >= GAME_DURATION:
            self.elapsed = GAME_DURATION
            self.finish()

    def spawn_monster(self):
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
        speed = MONSTER_SPEED * self.rng.uniform(*MONSTER_SPD_JITTER)
        self.monsters.append(Monster(pos, speed))

    def finish(self):
        """结算：只统计 21×21 目标区，外围诱饵不加分也不扣分。"""
        for m in self.monsters:            # 结算时松开所有占用，claims 必须归零
            m.claim(self.claims)
        correct, noise, missing = self.board.stats()
        total = self.board.target_total or 1
        cap = round(total * NOISE_LIMIT_PCT)
        coverage = correct / total
        won = coverage >= WIN_COVERAGE and noise <= cap
        if won and coverage >= GRADE_S_COVERAGE and noise <= GRADE_S_NOISE:
            grade = "S"
        elif won and noise <= cap * GRADE_A_NOISE_PCT:
            grade = "A"
        elif won:
            grade = "B"
        else:
            grade = "F"
        self.result = {"coverage": coverage, "noise": noise, "cap": cap,
                       "won": won, "grade": grade}
        self.state = "RESULT"

    # ---------- 绘制 ----------
    def present(self):
        if self.needs_scale:
            pygame.transform.smoothscale(self.canvas, self.window.get_size(), self.window)
        else:
            self.window.blit(self.canvas, (0, 0))

    def draw(self):
        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "RESULT":
            self.draw_result()
        else:
            self.draw_world()
            self.draw_hud()
            self.draw_shift_overlay()
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

        # 白底一次铺满整个网格（不用逐格 fill），再给阶段2 的锁定区补暗色。
        # 锁定格保留网格线，和「涂黑的实心块」在质感上区分开
        s.fill(C_CELL_WHITE, pygame.Rect(GRID_ORIGIN, (GRID_PX, GRID_PX)))
        if not self.board.outer_open:
            for r in range(GRID_N):
                for c in range(GRID_N):
                    if self.board.state[r][c] == WHITE and to_target(r, c) is None:
                        s.fill(C_LOCK, cell_to_rect(r, c))

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

        # 阶段2 的锁定区已在白底那一遍画成 C_LOCK（保留网格线），这里不用再盖

        # 怪物就是一个红圆；玩家必须画在它之后，否则怪物路过会把玩家盖住
        for m in self.monsters:
            mx, my = int(m.pos.x), int(m.pos.y)
            pygame.draw.circle(s, C_MONSTER, (mx, my), MONSTER_RADIUS)
            pygame.draw.circle(s, C_CELL_BLACK, (mx, my), MONSTER_RADIUS, 1)

        self.draw_player(s)

    def draw_player(self, s):
        # 位置就是格心，光晕半径 14 正好铺满一格，等于顺带给"我站在哪一格"画了框
        px, py = int(self.player.pos.x), int(self.player.pos.y)
        s.blit(self.glow, (px - PLAYER_GLOW_R, py - PLAYER_GLOW_R))

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
        self.txt("[WASD] MOVE   [J] PAINT   [K] ERASE   [R] RESTART",
                 (WINDOW_W - HUD_PAD, WINDOW_H - 62), self.f_small, C_TEXT, right=True)
        self.txt("HOLD J WHILE MOVING TO PAINT A TRAIL",
                 (WINDOW_W - HUD_PAD, WINDOW_H - 38), self.f_small, C_ERASING, right=True)

        if self.debug:
            p = self.player.pos
            self.txt("FPS %d  POS %d,%d  TARGETS %d" % (
                int(round(1.0 / max(self._last_dt, 1e-4))), p.x, p.y, total),
                (HUD_PAD, 10), self.f_small, C_WARN)

    # ---------- 菜单 ----------
    def draw_menu(self):
        s = self.screen
        s.fill(C_BG)
        for x in range(0, WINDOW_W, CELL):        # 和局内呼应的废墟暗格
            pygame.draw.line(s, C_BG_GRID, (x, 0), (x, WINDOW_H))
        for y in range(0, WINDOW_H, CELL):
            pygame.draw.line(s, C_BG_GRID, (0, y), (WINDOW_W, y))

        mid = WINDOW_W // 2
        self.center_txt("DATA SHIFT", (mid, 320), self.f_big, C_ACCENT)
        self.center_txt("RESTORE THE CODE. OUTRUN THE SHIFT.", (mid, 404), self.f_main, C_ERASING)
        if int(self.menu_t * MENU_BLINK_HZ) % 2 == 0:      # 闪一下，别像静态图
            self.center_txt("PRESS SPACE TO START", (mid, 540), self.f_mid, C_TEXT)
        self.center_txt("[WASD] MOVE     [J] PAINT     [K] ERASE", (mid, 660), self.f_main, C_TEXT)
        self.center_txt("[R] RESTART     [ESC] MENU     [F1] DEBUG", (mid, 700), self.f_main, C_ERASING)
        self.center_txt("ESC: QUIT", (mid, 900), self.f_small, C_ERASING)

    def draw_shift_overlay(self):
        """阶段切换的 1 秒遮罩：半透明黑 + 居中大字，随计时淡出。"""
        if self.shift_timer <= 0:
            return
        k = min(1.0, self.shift_timer / PHASE_SHIFT_TIME)   # 1 -> 0
        a = int(160 * k)                                    # 只让「幕」淡出
        self.overlay.fill((0, 0, 0, a))
        img = self.f_big.render("PHASE SHIFT", True, C_TEXT)
        # 文字始终全亮：棋盘偏白，白字要靠暗幕托着；幕淡到透明时白字本来也看不见，不突兀
        img.set_alpha(255)
        self.overlay.blit(img, img.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2)))
        self.screen.blit(self.overlay, (0, 0))

    # ---------- 结算页 ----------
    def center_txt(self, text, pos, font, color):
        img = font.render(text, True, color)
        self.screen.blit(img, img.get_rect(center=pos))

    def draw_thumb(self, x, y, is_target):
        """21×21 缩略图。左图纯黑白；右图按「对/错/缺」上色：青绿 / 猩红 / 暗灰。"""
        s = self.screen
        orr, occ = TARGET_OFFSET
        for tr in range(TARGET_N):
            for tc in range(TARGET_N):
                want = self.target[tr][tc]
                if is_target:
                    col = C_CELL_BLACK if want else C_CELL_WHITE
                else:
                    got = self.board.state[orr + tr][occ + tc] == BLACK
                    if want:
                        col = C_ACCENT if got else C_MISSING
                    else:
                        col = C_MONSTER if got else C_CELL_WHITE
                s.fill(col, (x + tc * THUMB_CELL, y + tr * THUMB_CELL,
                             THUMB_CELL, THUMB_CELL))
        pygame.draw.rect(s, C_CELL_LINE,
                         pygame.Rect(x, y, TARGET_N * THUMB_CELL, TARGET_N * THUMB_CELL), 1)

    def draw_result(self):
        s = self.screen
        s.fill(C_BG)                     # 结算页是整屏重画，不清屏会透出上一帧棋盘
        r = self.result
        thumb = TARGET_N * THUMB_CELL
        mid_x = WINDOW_W // 2

        title = "DATA RESTORED" if r["won"] else "DATA CORRUPTED"
        self.center_txt(title, (mid_x, 150), self.f_mid,
                        C_ACCENT if r["won"] else C_MONSTER)

        left_x, right_x, top_y = 120, WINDOW_W - 120 - thumb, 250
        self.draw_thumb(left_x, top_y, True)
        self.draw_thumb(right_x, top_y, False)
        self.txt("TARGET", (left_x, top_y - 32), self.f_small, C_ERASING)
        self.txt("YOURS", (right_x, top_y - 32), self.f_small, C_ERASING)

        cov_col = C_ACCENT if r["coverage"] >= WIN_COVERAGE else C_TEXT
        n_col = C_WARN if r["noise"] > r["cap"] * 0.8 else C_TEXT
        self.center_txt("COVERAGE %d%%" % int(r["coverage"] * 100),
                        (mid_x, 344), self.f_main, cov_col)
        self.center_txt("NOISE %d / %d" % (r["noise"], r["cap"]),
                        (mid_x, 380), self.f_main, n_col)

        g_col = C_MONSTER if r["grade"] == "F" else (C_WARN if r["grade"] == "B" else C_ACCENT)
        self.center_txt("GRADE", (mid_x, 522), self.f_small, C_ERASING)
        self.center_txt(r["grade"], (mid_x, 592), self.f_big, g_col)

        self.center_txt("R: RETRY      ESC: QUIT", (mid_x, 760), self.f_main, C_TEXT)

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
