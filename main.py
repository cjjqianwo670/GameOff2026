# -*- coding: utf-8 -*-
"""
扫雷 · Minesweeper (pygame 复刻版)

运行：python minesweeper.py
依赖：pip install pygame

操作：
    左键 翻开 / 点击已翻开的数字可快速展开
    右键 插旗
    中键 在数字上快速展开
    R    重开      1/2/3 切换难度      ESC 退出
"""

import json
import os
import random

import pygame

# ============================================================
#  基础配置
# ============================================================

LEVELS = {
    "easy":   {"rows": 9,  "cols": 9,  "mines": 10, "label": "初级", "desc": "9 × 9 · 10 雷"},
    "medium": {"rows": 16, "cols": 16, "mines": 40, "label": "中级", "desc": "16 × 16 · 40 雷"},
    "hard":   {"rows": 16, "cols": 30, "mines": 99, "label": "高级", "desc": "16 × 30 · 99 雷"},
}
LEVEL_ORDER = ["easy", "medium", "hard"]

# 配色（和网页版一致）
BG          = (238, 242, 249)
BOARD_BG    = (204, 215, 230)
CELL_FILL   = (205, 219, 236)
CELL_HOVER  = (228, 238, 251)
CELL_EDGE   = (166, 187, 210)
CELL_LIGHT  = (255, 255, 255)
REVEALED    = (237, 242, 249)
REVEALED_BD = (224, 232, 242)
PANEL       = (255, 255, 255)
PANEL_SHADE = (226, 232, 242)
PILL_BG     = (241, 245, 251)
LINE        = (219, 227, 238)
TEXT        = (31, 41, 55)
MUTED       = (107, 114, 128)
ACCENT      = (59, 130, 246)
ACCENT_DARK = (37, 99, 235)
RED         = (239, 68, 68)
FLAG_POLE   = (71, 85, 105)
MINE_DARK   = (43, 52, 64)
BOOM_BG     = (255, 217, 214)
WRONG_BG    = (253, 232, 230)

NUMBER_COLORS = {
    1: (29, 111, 224),
    2: (46, 158, 79),
    3: (224, 69, 58),
    4: (123, 63, 228),
    5: (224, 123, 26),
    6: (15, 154, 168),
    7: (55, 65, 81),
    8: (123, 135, 148),
}

BEST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "minesweeper_best.json")


# ============================================================
#  字体
# ============================================================
# 注意：这里刻意不使用 pygame.font.SysFont()。
# 部分 Windows 的字体注册表里存在数值型键名，pygame 的 initsysfonts_win32()
# 会拿 int 去调 os.path.splitext()，直接抛：
#     TypeError: expected str, bytes or os.PathLike object, not int
# 改成按字体文件路径加载，完全绕开系统字体枚举。

# 中文字体（常规 / 粗体），按优先级排列
CJK_REG = [
    r"C:\Windows\Fonts\msyh.ttc",       # 微软雅黑
    r"C:\Windows\Fonts\msyh.ttf",       # 微软雅黑（Win7）
    r"C:\Windows\Fonts\Deng.ttf",       # 等线
    r"C:\Windows\Fonts\simhei.ttf",     # 黑体
    r"C:\Windows\Fonts\simsun.ttc",     # 宋体
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]
CJK_BOLD = [
    r"C:\Windows\Fonts\msyhbd.ttc",     # 微软雅黑 Bold
    r"C:\Windows\Fonts\msyhbd.ttf",
    r"C:\Windows\Fonts\Dengb.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]
MONO_REG = [
    r"C:\Windows\Fonts\consola.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]
MONO_BOLD = [
    r"C:\Windows\Fonts\consolab.ttf",
]

_font_cache = {}


def _first_existing(paths):
    for p in paths:
        try:
            if os.path.exists(p):
                return p
        except Exception:
            pass
    return None


def _safe_font(path, size):
    try:
        return pygame.font.Font(path, size)
    except Exception:
        return None


def F(size, bold=False, mono=False):
    """按文件路径加载字体；实在找不到才退回 pygame 内置字体。"""
    key = (size, bold, mono)
    if key in _font_cache:
        return _font_cache[key]

    fnt = None
    native_bold = False

    if mono:
        path = _first_existing(MONO_BOLD if bold else MONO_REG)
        if path:
            fnt = _safe_font(path, size)
            native_bold = bold and (path in MONO_BOLD)

    if fnt is None and bold:
        path = _first_existing(CJK_BOLD)
        if path:
            fnt = _safe_font(path, size)
            native_bold = fnt is not None

    if fnt is None:
        path = _first_existing(CJK_REG)
        if path:
            fnt = _safe_font(path, size)

    if fnt is None:
        fnt = pygame.font.Font(None, size)
        native_bold = False

    if bold and not native_bold:
        fnt.set_bold(True)

    _font_cache[key] = fnt
    return fnt


def draw_text(surf, s, font, color, pos, anchor="topleft"):
    img = font.render(s, True, color)
    rect = img.get_rect(**{anchor: pos})
    surf.blit(img, rect)
    return rect


def fmt3(n):
    n = int(n)
    return "-%02d" % min(999, -n) if n < 0 else "%03d" % min(999, n)


def disable_ime():
    """
    关闭 SDL 的文本输入，让按键直接送给游戏窗口。
    Windows 上开着中文输入法时，r / 1 / 2 这些字母数字会被输入法
    当成拼音抢走，游戏收不到 KEYDOWN，表现就是「按 R 没反应」。
    """
    try:
        pygame.key.stop_text_input()
    except Exception:
        pass


# ============================================================
#  布局计算
# ============================================================

def compute_layout(key):
    L = LEVELS[key]
    rows, cols = L["rows"], L["cols"]
    gap = 3

    # 自适应格子尺寸：先按最大宽度算，再按屏幕高度收一点
    cell = min(34, (1040 - (cols - 1) * gap - 16) // cols)
    try:
        screen_h = pygame.display.Info().current_h
    except Exception:
        screen_h = 900
    by_h = (screen_h - 300 - (rows - 1) * gap - 16) // rows
    cell = max(18, min(cell, by_h))
    cell = min(cell, 34)

    board_w = cols * cell + (cols - 1) * gap + 16
    board_h = rows * cell + (rows - 1) * gap + 16

    pad = 24
    win_w = max(board_w + pad * 2, 640)

    title_y = 16
    sub_y = 62
    btn_y = 94
    btn_h = 46
    panel_y = btn_y + btn_h + 16
    panel_x = pad
    panel_w = win_w - pad * 2
    inner = 14
    hud_h = 54
    hud_y = panel_y + inner
    board_y = hud_y + hud_h + 10
    board_x = panel_x + (panel_w - board_w) // 2
    panel_bottom = board_y + board_h + inner
    win_h = panel_bottom + 52

    # 难度按钮
    btn_gap = 10
    bw = (panel_w - btn_gap * 2) // 3
    level_rects = {}
    for i, k in enumerate(LEVEL_ORDER):
        level_rects[k] = pygame.Rect(panel_x + i * (bw + btn_gap), btn_y, bw, btn_h)

    face_size = 46
    face_rect = pygame.Rect(0, 0, face_size, face_size)
    face_rect.center = (panel_x + panel_w // 2, hud_y + hud_h // 2)

    # 右上角「重开」按钮（不依赖键盘，鼠标也能重开）
    restart_rect = pygame.Rect(win_w - pad - 96, title_y + 6, 96, 32)

    return {
        "win_w": win_w, "win_h": win_h, "cell": cell, "gap": gap,
        "pad": pad, "title_y": title_y, "sub_y": sub_y,
        "panel": pygame.Rect(panel_x, panel_y, panel_w, panel_bottom - panel_y),
        "hud_y": hud_y, "hud_h": hud_h,
        "board_x": board_x, "board_y": board_y,
        "board_w": board_w, "board_h": board_h,
        "panel_x": panel_x, "panel_w": panel_w, "panel_bottom": panel_bottom,
        "level_rects": level_rects, "face_rect": face_rect,
        "restart_rect": restart_rect,
    }


# ============================================================
#  绘制小工具
# ============================================================

def draw_face(surf, rect, state):
    """用几何图形画笑脸，避免 emoji 字体缺失。"""
    pygame.draw.rect(surf, (243, 247, 253), rect, border_radius=14)
    pygame.draw.rect(surf, LINE, rect, 1, border_radius=14)

    cx, cy = rect.center
    r = int(rect.width * 0.32)
    pygame.draw.circle(surf, (255, 206, 84), (cx, cy), r)
    pygame.draw.circle(surf, (222, 168, 40), (cx, cy), r, 1)

    eye = (60, 50, 40)
    if state == "dead":
        k = max(2, r // 4)
        for dx in (-1, 1):
            ex = cx + dx * int(r * 0.42)
            ey = cy - int(r * 0.20)
            pygame.draw.line(surf, eye, (ex - k, ey - k), (ex + k, ey + k), 2)
            pygame.draw.line(surf, eye, (ex - k, ey + k), (ex + k, ey - k), 2)
        pygame.draw.line(surf, eye, (cx - int(r * 0.38), cy + int(r * 0.5)),
                         (cx + int(r * 0.38), cy + int(r * 0.5)), 2)
    elif state == "cool":
        pygame.draw.rect(surf, (45, 55, 70),
                         (cx - int(r * 0.72), cy - int(r * 0.34),
                          int(r * 1.44), int(r * 0.40)), border_radius=2)
        mouth_smile(surf, cx, cy + int(r * 0.16), int(r * 0.5), eye, 2)
    elif state == "worried":
        for dx in (-1, 1):
            pygame.draw.circle(surf, eye, (cx + dx * int(r * 0.38), cy - int(r * 0.22)), 2)
        pygame.draw.ellipse(surf, eye,
                            (cx - int(r * 0.22), cy + int(r * 0.16),
                             int(r * 0.44), int(r * 0.52)))
    else:  # smile
        for dx in (-1, 1):
            pygame.draw.circle(surf, eye, (cx + dx * int(r * 0.38), cy - int(r * 0.26)), 2)
        mouth_smile(surf, cx, cy + int(r * 0.18), int(r * 0.5), eye, 2)


def mouth_smile(surf, cx, cy, w, color, thick=2):
    pts = []
    for dx in range(-w, w + 1):
        y = cy - (dx * dx) // max(1, int(w * 2.0))
        pts.append((cx + dx, y))
    if len(pts) > 1:
        pygame.draw.lines(surf, color, False, pts, thick)


def draw_flag(surf, rect, cell):
    pole_x = rect.centerx - int(cell * 0.09)
    top = rect.top + int(cell * 0.22)
    bottom = rect.bottom - int(cell * 0.22)
    w = max(2, cell // 14)
    pygame.draw.line(surf, FLAG_POLE, (pole_x, top), (pole_x, bottom), w)
    pygame.draw.line(surf, FLAG_POLE, (pole_x - int(cell * 0.17), bottom),
                     (pole_x + int(cell * 0.08), bottom), w)
    pygame.draw.polygon(surf, RED, [
        (pole_x + 1, top),
        (pole_x + int(cell * 0.30), top + int(cell * 0.14)),
        (pole_x + 1, top + int(cell * 0.29)),
    ])


def draw_mine(surf, rect, cell):
    cx, cy = rect.center
    R = max(3, int(cell * 0.25))
    lw = max(2, cell // 14)
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (0.72, 0.72), (-0.72, 0.72), (0.72, -0.72), (-0.72, -0.72)]
    for dx, dy in dirs:
        p1 = (int(cx + dx * R * 0.95), int(cy + dy * R * 0.95))
        p2 = (int(cx + dx * R * 1.8), int(cy + dy * R * 1.8))
        pygame.draw.line(surf, MINE_DARK, p1, p2, lw)
    pygame.draw.circle(surf, MINE_DARK, (cx, cy), R)
    hl = max(1, R // 3)
    pygame.draw.circle(surf, (232, 238, 246), (cx - R // 3, cy - R // 3), hl)


def draw_cross(surf, rect, color, thick=2):
    pad = max(3, int(rect.w * 0.28))
    pygame.draw.line(surf, color, (rect.x + pad, rect.y + pad),
                     (rect.right - pad, rect.bottom - pad), thick)
    pygame.draw.line(surf, color, (rect.x + pad, rect.bottom - pad),
                     (rect.right - pad, rect.y + pad), thick)


# ============================================================
#  游戏
# ============================================================

class Game:
    def __init__(self, level="easy"):
        self.best = self.load_best()
        self.screen = None
        self.key = level
        self.set_level(level)

    # ---------- 存档 ----------
    def load_best(self):
        try:
            with open(BEST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save_best(self):
        try:
            with open(BEST_FILE, "w", encoding="utf-8") as f:
                json.dump(self.best, f)
        except Exception:
            pass

    # ---------- 关卡 / 初始化 ----------
    def set_level(self, key):
        self.key = key
        L = LEVELS[key]
        self.rows, self.cols, self.mines = L["rows"], L["cols"], L["mines"]
        self.layout = compute_layout(key)
        self.screen = pygame.display.set_mode((self.layout["win_w"], self.layout["win_h"]))
        pygame.display.set_caption("扫雷 · Minesweeper")
        disable_ime()   # 重建窗口后输入法可能被重新打开，这里再关一次

        cell = self.layout["cell"]
        self.num_font = F(max(11, int(cell * 0.58)), True)
        self.num_surfs = {
            n: self.num_font.render(str(n), True, c) for n, c in NUMBER_COLORS.items()
        }
        self.reset()

    def reset(self):
        rows, cols = self.rows, self.cols
        self.mine = [[False] * cols for _ in range(rows)]
        self.adj = [[0] * cols for _ in range(rows)]
        self.revealed = [[False] * cols for _ in range(rows)]
        self.flagged = [[False] * cols for _ in range(rows)]

        self.started = False
        self.over = False
        self.won = False
        self.revealed_count = 0
        self.flag_count = 0
        self.elapsed = 0
        self.t0 = None
        self.boom_cell = None
        self.new_record = False
        self.again_rect = None

    # ---------- 布雷 ----------
    def plant(self, sr, sc):
        rows, cols = self.rows, self.cols
        banned = set()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                r, c = sr + dr, sc + dc
                if 0 <= r < rows and 0 <= c < cols:
                    banned.add((r, c))

        pool = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in banned]
        random.shuffle(pool)
        for r, c in pool[:min(self.mines, len(pool))]:
            self.mine[r][c] = True

        for r in range(rows):
            for c in range(cols):
                if self.mine[r][c]:
                    for nr, nc in self.neighbors(r, c):
                        self.adj[nr][nc] += 1

    def neighbors(self, r, c):
        out = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    out.append((nr, nc))
        return out

    # ---------- 时间 ----------
    def freeze_time(self):
        if self.t0 is not None:
            self.elapsed = min(999, (pygame.time.get_ticks() - self.t0) // 1000)

    def tick_time(self):
        if self.started and not self.over and self.t0 is not None:
            self.elapsed = min(999, (pygame.time.get_ticks() - self.t0) // 1000)

    # ---------- 操作 ----------
    def toggle_flag(self, r, c):
        if self.over or self.revealed[r][c]:
            return
        self.flagged[r][c] = not self.flagged[r][c]
        self.flag_count += 1 if self.flagged[r][c] else -1

    def flood(self, r, c):
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if self.revealed[cr][cc] or self.flagged[cr][cc]:
                continue
            self.revealed[cr][cc] = True
            self.revealed_count += 1
            if self.adj[cr][cc] == 0:
                for nr, nc in self.neighbors(cr, cc):
                    if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                        stack.append((nr, nc))

    def left_click(self, r, c):
        if self.over or self.flagged[r][c]:
            return
        if not self.started:
            self.started = True
            self.t0 = pygame.time.get_ticks()
            self.plant(r, c)
        if self.revealed[r][c]:
            self.chord(r, c)
            return
        if self.mine[r][c]:
            self.boom(r, c)
            return
        self.flood(r, c)
        self.check_win()

    def chord(self, r, c):
        if self.over or not self.revealed[r][c] or self.adj[r][c] == 0:
            return
        nb = self.neighbors(r, c)
        flags = sum(1 for nr, nc in nb if self.flagged[nr][nc])
        if flags != self.adj[r][c]:
            return
        boom = None
        for nr, nc in nb:
            if self.flagged[nr][nc] or self.revealed[nr][nc]:
                continue
            if self.mine[nr][nc]:
                boom = (nr, nc)
                break
            self.flood(nr, nc)
        if boom:
            self.boom(*boom)
        else:
            self.check_win()

    def boom(self, r, c):
        if self.over:
            return
        self.over = True
        self.won = False
        self.boom_cell = (r, c)
        self.freeze_time()
        for rr in range(self.rows):
            for cc in range(self.cols):
                if self.mine[rr][cc] and not self.flagged[rr][cc]:
                    self.revealed[rr][cc] = True

    def check_win(self):
        if self.over:
            return
        if self.revealed_count != self.rows * self.cols - self.mines:
            return
        self.over = True
        self.won = True
        self.freeze_time()
        for rr in range(self.rows):
            for cc in range(self.cols):
                if self.mine[rr][cc] and not self.flagged[rr][cc]:
                    self.flagged[rr][cc] = True
                    self.flag_count += 1
        old = self.best.get(self.key)
        self.new_record = (old is None) or (self.elapsed < old)
        if self.new_record:
            self.best[self.key] = self.elapsed
            self.save_best()

    # ---------- 坐标换算 ----------
    def cell_at(self, pos):
        lay = self.layout
        cell, gap = lay["cell"], lay["gap"]
        bx = lay["board_x"] + 8
        by = lay["board_y"] + 8
        x, y = pos
        if x < bx or y < by:
            return None
        c = (x - bx) // (cell + gap)
        r = (y - by) // (cell + gap)
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return None
        # 落在间隙里就不算
        if (x - bx) - c * (cell + gap) >= cell:
            return None
        if (y - by) - r * (cell + gap) >= cell:
            return None
        return int(r), int(c)

    def cell_rect(self, r, c):
        lay = self.layout
        cell, gap = lay["cell"], lay["gap"]
        x = lay["board_x"] + 8 + c * (cell + gap)
        y = lay["board_y"] + 8 + r * (cell + gap)
        return pygame.Rect(x, y, cell, cell)

    # ---------- 事件 ----------
    def handle_mouse_down(self, pos, button):
        lay = self.layout

        if button == 1:
            for k, rect in lay["level_rects"].items():
                if rect.collidepoint(pos):
                    if k != self.key:
                        self.set_level(k)
                    return
            if lay["face_rect"].collidepoint(pos):
                self.reset()
                return
            if lay["restart_rect"].collidepoint(pos):
                self.reset()
                return
            again = getattr(self, "again_rect", None)
            if self.over and again is not None and again.collidepoint(pos):
                self.reset()
                return

        rc = self.cell_at(pos)
        if rc is None:
            return
        r, c = rc
        if button == 1:
            self.left_click(r, c)
        elif button == 3:
            self.toggle_flag(r, c)
        elif button == 2:
            self.chord(r, c)

    def face_state(self):
        if self.over:
            return "cool" if self.won else "dead"
        return "smile"

    # ---------- 绘制 ----------
    def draw(self):
        s = self.screen
        lay = self.layout
        s.fill(BG)
        mouse = pygame.mouse.get_pos()

        # 顶部标题
        draw_text(s, "扫雷", F(30, True), ACCENT, (lay["pad"], lay["title_y"]))
        draw_text(s, "左键翻开 · 右键插旗 · 点已翻开的数字快速展开",
                  F(13), MUTED, (lay["pad"] + 70, lay["title_y"] + 16))

        # 右上角「重开」按钮
        rr = lay["restart_rect"]
        r_hover = rr.collidepoint(mouse)
        pygame.draw.rect(s, (238, 245, 255) if r_hover else (255, 255, 255), rr, border_radius=9)
        pygame.draw.rect(s, (183, 204, 240) if r_hover else LINE, rr, 1, border_radius=9)
        draw_text(s, "重开  R", F(13, True), ACCENT_DARK, rr.center, "center")

        # 难度按钮
        for k, rect in lay["level_rects"].items():
            active = (k == self.key)
            hover = rect.collidepoint(mouse) and not active
            bg = (240, 246, 255) if active else ((247, 250, 254) if hover else (255, 255, 255))
            border = ACCENT if active else ((183, 204, 240) if hover else LINE)
            pygame.draw.rect(s, bg, rect, border_radius=12)
            pygame.draw.rect(s, border, rect, 1, border_radius=12)
            L = LEVELS[k]
            draw_text(s, L["label"], F(15, True),
                      ACCENT_DARK if active else TEXT, (rect.x + 14, rect.y + 7))
            draw_text(s, L["desc"], F(11), (74, 118, 196) if active else MUTED,
                      (rect.x + 14, rect.y + 27))

        # 面板阴影 + 面板
        panel = lay["panel"]
        pygame.draw.rect(s, PANEL_SHADE, panel.move(0, 4), border_radius=18)
        pygame.draw.rect(s, PANEL, panel, border_radius=18)

        # HUD：剩余雷数
        pill_h = 34
        mine_pill = pygame.Rect(lay["panel_x"] + 14, lay["hud_y"] + (lay["hud_h"] - pill_h) // 2, 92, pill_h)
        draw_text(s, "剩余雷数", F(11), MUTED, (mine_pill.x, mine_pill.y - 17))
        pygame.draw.rect(s, PILL_BG, mine_pill, border_radius=8)
        pygame.draw.rect(s, LINE, mine_pill, 1, border_radius=8)
        draw_text(s, fmt3(self.mines - self.flag_count), F(20, True, mono=True),
                  TEXT, mine_pill.center, "center")

        # HUD：计时
        time_pill = pygame.Rect(lay["panel_x"] + lay["panel_w"] - 14 - 92,
                                lay["hud_y"] + (lay["hud_h"] - pill_h) // 2, 92, pill_h)
        draw_text(s, "用时", F(11), MUTED, (time_pill.right, time_pill.y - 17), "topright")
        pygame.draw.rect(s, PILL_BG, time_pill, border_radius=8)
        pygame.draw.rect(s, LINE, time_pill, 1, border_radius=8)
        draw_text(s, fmt3(self.elapsed), F(20, True, mono=True),
                  TEXT, time_pill.center, "center")

        # HUD：笑脸
        draw_face(s, lay["face_rect"], self.face_state())

        # 棋盘底板
        board_rect = pygame.Rect(lay["board_x"], lay["board_y"], lay["board_w"], lay["board_h"])
        pygame.draw.rect(s, BOARD_BG, board_rect, border_radius=12)

        hover_rc = None if self.over else self.cell_at(mouse)
        cell = lay["cell"]

        for r in range(self.rows):
            for c in range(self.cols):
                rect = self.cell_rect(r, c)
                is_boom = (self.boom_cell == (r, c))

                if self.revealed[r][c]:
                    bg = BOOM_BG if is_boom else REVEALED
                    pygame.draw.rect(s, bg, rect, border_radius=3)
                    pygame.draw.rect(s, (239, 68, 68) if is_boom else REVEALED_BD,
                                     rect, 1 if not is_boom else 2, border_radius=3)
                    if self.mine[r][c]:
                        draw_mine(s, rect, cell)
                    elif self.adj[r][c] > 0:
                        surf = self.num_surfs[self.adj[r][c]]
                        s.blit(surf, surf.get_rect(center=rect.center))
                    continue

                # 未翻开
                pygame.draw.rect(s, CELL_EDGE, rect, border_radius=4)
                inner = rect.inflate(-2, -2)
                body = CELL_HOVER if hover_rc == (r, c) else CELL_FILL
                pygame.draw.rect(s, body, inner, border_radius=3)
                pygame.draw.line(s, CELL_LIGHT, (inner.x + 1, inner.y), (inner.right - 2, inner.y))

                if self.flagged[r][c]:
                    if self.over and not self.won and not self.mine[r][c]:
                        pygame.draw.rect(s, WRONG_BG, inner, border_radius=3)
                        draw_cross(s, rect, RED, max(2, cell // 12))
                    else:
                        draw_flag(s, rect, cell)

        # 结算浮层
        if self.over:
            self.draw_overlay(board_rect)

        # 底部
        best = self.best.get(self.key)
        best_txt = ("最佳成绩：%d 秒" % best) if best is not None else "最佳成绩：—"
        draw_text(s, best_txt, F(13), MUTED,
                  (lay["pad"], lay["panel_bottom"] + 18))
        draw_text(s, "R 重开 · 1/2/3 切换难度 · ESC 退出", F(13), MUTED,
                  (lay["win_w"] - lay["pad"], lay["panel_bottom"] + 18), "topright")

    def draw_overlay(self, board_rect):
        s = self.screen
        ov = pygame.Surface((board_rect.w, board_rect.h), pygame.SRCALPHA)
        ov.fill((255, 255, 255, 216))
        # 用圆角遮罩把浮层四角切圆，避免盖住底板圆角
        mask = pygame.Surface((board_rect.w, board_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=12)
        ov.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        s.blit(ov, board_rect.topleft)

        cx = board_rect.centerx
        cy = board_rect.centery

        if self.won:
            title = "新纪录！" if self.new_record else "通关！"
            sub = "%s · 用时 %d 秒" % (LEVELS[self.key]["desc"], self.elapsed)
            color = (37, 99, 235)
        else:
            title = "踩雷了"
            sub = "坚持了 %d 秒 · 再试一次吧" % self.elapsed
            color = (220, 38, 38)

        if board_rect.h < 300:      # 极窄屏紧凑布局
            face_size, dy_title, dy_sub, dy_btn = 44, -6, 20, 52
        else:
            face_size, dy_title, dy_sub, dy_btn = 68, 4, 38, 92

        face_rect = pygame.Rect(0, 0, face_size, face_size)
        face_rect.center = (cx, cy - 62 if face_size > 50 else cy - 42)
        draw_face(s, face_rect, self.face_state())

        draw_text(s, title, F(24 if face_size > 50 else 20, True), color,
                  (cx, cy + dy_title), "center")
        draw_text(s, sub, F(13 if face_size > 50 else 11), MUTED,
                  (cx, cy + dy_sub), "center")

        # 「再来一局」按钮（鼠标可直接点）
        again = pygame.Rect(0, 0, 128, 40)
        again.center = (cx, cy + dy_btn)
        self.again_rect = again
        a_hover = again.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(s, (14, 165, 233) if a_hover else ACCENT, again, border_radius=11)
        draw_text(s, "再来一局", F(14, True), (255, 255, 255), again.center, "center")
        if face_size > 50:
            draw_text(s, "或按 R / 点笑脸", F(11), (170, 176, 188),
                      (cx, cy + dy_btn + 34), "center")


# ============================================================
#  主循环
# ============================================================

def main():
    pygame.init()
    pygame.display.set_caption("扫雷 · Minesweeper")
    disable_ime()

    # pygame 2.0.1 之前没有 WINDOWFOCUSGAINED，取不到就跳过
    FOCUS_GAINED = getattr(pygame, "WINDOWFOCUSGAINED", None)

    game = Game("easy")
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # event.key 用物理键位，event.unicode 兜底：某些输入法/键盘布局
                # 下 key 可能不是预期的 K_r，用文字也认一次
                key = event.key
                ch = (getattr(event, "unicode", "") or "").lower()

                if key in (pygame.K_ESCAPE, pygame.K_q) or ch == "q":
                    running = False
                elif key == pygame.K_r or key == pygame.K_F2 or ch == "r":
                    game.reset()
                elif key == pygame.K_1 or ch == "1":
                    game.set_level("easy")
                elif key == pygame.K_2 or ch == "2":
                    game.set_level("medium")
                elif key == pygame.K_3 or ch == "3":
                    game.set_level("hard")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_mouse_down(event.pos, event.button)

            elif FOCUS_GAINED is not None and event.type == FOCUS_GAINED:
                # 重新拿回焦点时确保输入法没有抢走键盘
                disable_ime()

        game.tick_time()
        game.draw()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
