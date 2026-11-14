# -*- coding: utf-8 -*-
"""步骤 14 验收：开始页（背景水印 / 双色标题 / 键帽说明 / 三帧不跳动）。

作者 2026-11-12：「开始界面太枯燥了，稍微优化一下。」改法见 HANDOFF §4.19。
这里只管「画出来对不对」，不管玩法。
"""

import pygame

from _act1_common import WIN, check, finish
import src.ui as ui
from src.config import C_ACCENT, C_BG, C_CELL_BLACK, C_TEXT, QR_CONTENT, WINDOW_H, WINDOW_W

TITLE = "STEP 14 · TITLE SCREEN"


def fresh():
    """TITLE 相位的 Game（**不**调 start_act：开始页在开局之前）。"""
    from src.game import Game
    return Game(WIN)


def render(g, t):
    g.menu_t = t
    g.draw()
    return g.canvas


def colors(surf, rect, step=1):
    out = {}
    for x in range(rect.left, rect.right, step):
        for y in range(rect.top, rect.bottom, step):
            out[surf.get_at((x, y))[:3]] = out.get(surf.get_at((x, y))[:3], 0) + 1
    return out


g = fresh()
check("新开一局就停在开始页（不改既有流程）", g.state == "TITLE", g.state)

# ---------- 1. 画面不是一片底色 ----------
cv = render(g, 2.0)
palette = colors(cv, pygame.Rect(0, 0, WINDOW_W, WINDOW_H), 4)
check("开始页有内容（不是纯底色）", len(palette) > 8, "只有 %d 种颜色" % len(palette))

# ---------- 2. 背景是那张码：定位图案在，而且压得很低 ----------
mat = ui._title_code()
full = len(mat) * ui.TITLE_CELL
x0 = (WINDOW_W - full) // 2
y0 = ui.TITLE_CODE_Y - full // 2


def module_px(tr, tc):
    return (x0 + tc * ui.TITLE_CELL + ui.TITLE_CELL // 2,
            y0 + tr * ui.TITLE_CELL + ui.TITLE_CELL // 2)


check("（准备）水印用的是一张 21×21 真码（有定位图案）",
      len(mat) == 21 and mat[0][0] and mat[0][1] and not mat[1][1], str(len(mat)))
check("同一进程内只抽一次（每帧现抽的话水印会闪）", ui._title_code() is ui._title_code())

col_code = cv.get_at(module_px(0, 0))[:3]
check("水印墨块确实画出来了（和底色不同）", col_code != C_BG, str(col_code))
check("水印压得很低（比正文暗得多，是纹理不是字）", max(col_code) < 110, str(col_code))
col_blank = cv.get_at((x0 + 5, y0 + 5))[:3]
check("水印的白格留空（不填色，只有底色与暗格）", col_blank != col_code, str(col_blank))

# ---------- 3. 「写出来」：越到后面墨块越多 ----------
def ink_count(surf):
    n = 0
    for r in range(21):
        for c in range(21):
            if mat[r][c] and surf.get_at(module_px(r, c))[:3] != C_BG:
                n += 1
    return n


early = ink_count(render(g, 0.15))
late = ink_count(render(g, 3.0))
check("水印是逐格「写出来」的（早帧明显少于写完之后）", 0 < early < late,
      "0.15s %d 格 → 3.0s %d 格" % (early, late))

# ---------- 4. 标题：「DATA」白、「SHIFT」青，位置不跳 ----------
def word_box(surf, color):
    """标题字的外接框。**只看 270~380 这一带** —— 再往下 398 那颗菱形也是青色，
    会把 SHIFT 那个框拉长到那条线上（第一版就是被它骗了）。"""
    xs, ys = [], []
    for x in range(300, 1060, 2):
        for y in range(270, 380, 2):
            if surf.get_at((x, y))[:3] == color:
                xs.append(x); ys.append(y)
    if not xs:
        return None
    return pygame.Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


cv2 = render(g, 3.0)
box_white = word_box(cv2, C_TEXT)
box_accent = word_box(cv2, C_ACCENT)
check("标题左半是白字（DATA）", box_white is not None, str(box_white))
check("标题右半是青字（SHIFT）", box_accent is not None, str(box_accent))
if box_white and box_accent:
    check("两半在同一行、左白右青（不是一个词拆两行）",
          abs(box_white.centery - box_accent.centery) <= 6 and box_white.left < box_accent.left,
          "%s / %s" % (box_white, box_accent))
    check("整个标题水平居中（左右余量差 < 40px）",
          abs((box_white.left + box_accent.right) / 2 - WINDOW_W // 2) < 40,
          "中心 %.0f" % ((box_white.left + box_accent.right) / 2))

boxes = []
for t in (0.4, 1.9, 4.2):
    cvx = render(g, t)
    bw = word_box(cvx, C_TEXT)
    boxes.append(None if bw is None else (bw.x, bw.y, bw.w, bw.h))
check("三帧标题位置一致（只有扫描线在动，字不跳）", len(set(boxes)) == 1, str(set(boxes)))

# ---------- 5. 键帽行：四颗键帽 + 右侧说明 ----------
row_cy = 720
probe_y = row_cy - 11            # 键帽上沿内侧、字还没开始的地方；也避开 CRT 横纹那一行
dark_runs, run = [], 0
for x in range(200, 1160):
    if cv2.get_at((x, probe_y))[:3] == C_CELL_BLACK:
        run += 1
    elif run:
        dark_runs.append((x - run, run)); run = 0
if run:
    dark_runs.append((1160 - run, run))
dark_runs = [(x, w) for x, w in dark_runs if w >= 24]
check("键帽行有四颗键帽（暗底块）", len(dark_runs) == 4, str(dark_runs))

x0k, wk = dark_runs[0]
check("键帽是 28px 高的块（不是一行细线）",
      cv2.get_at((x0k + 3, row_cy - 13))[:3] == C_CELL_BLACK
      and cv2.get_at((x0k + 3, row_cy + 16))[:3] != C_CELL_BLACK,
      str(dark_runs[0]))
check("键帽底沿有一道亮边（看着有厚度）",
      cv2.get_at((x0k + 3, row_cy + 13))[:3] != C_CELL_BLACK,
      str(cv2.get_at((x0k + 3, row_cy + 13))[:3]))

# 键名是强调色：在四颗键帽的范围里找青绿像素
for i, (kx, kw) in enumerate(dark_runs):
    acc = colors(cv2, pygame.Rect(kx, row_cy - 12, kw, 24))
    check("第 %d 颗键帽上的键名是强调色" % (i + 1), C_ACCENT in acc, str(list(acc)[:4]))

# 键帽右侧确实有说明文字（正文色像素），不是空着一块
for i, ((kx, kw), label) in enumerate(zip(dark_runs, ("MOVE", "ANOMALY", "DARK", "ERASE"))):
    zone = pygame.Rect(kx + kw + 4, row_cy - 12, 120, 24)
    lit = sum(1 for x in range(zone.left, zone.right, 2)
              for y in range(zone.top, zone.bottom, 2)
              if cv2.get_at((x, y))[:3] == C_TEXT)
    check("第 %d 颗键帽右边写着「%s」" % (i + 1, label), lit > 20, "%d px" % lit)

# ---------- 6. 版面关系：三块东西不打架 ----------
check("水印下缘让开键帽行（不压在键帽上）", y0 + full <= row_cy - 14,
      "水印底 %d / 键帽顶 %d" % (y0 + full, row_cy - 14))
enter_top = 596 - 23
check("水印下缘也让开 PRESS ENTER 框", y0 + full > enter_top + 46,
      "水印底 %d / 按钮底 %d" % (y0 + full, enter_top + 46))

# 四角括号：屏幕四角各有一段短线
corner = cv2.get_at((34, 34))[:3]
check("四角括号画了（左上角不是纯底色）", corner != C_BG, str(corner))

# ---------- 7. 封面那张码 = 你要复原的那张（2026-11-14 改）----------
# 以前是「封面另抽一张、和本局无关」（作者 2026-11-12 定）；内容固定成 "YOU WERE HERE" 之后，
# 封面、棋盘、终幕那张卡是**同一张码** —— 扫封面和扫结局，手机上是同一句话。
g7 = fresh()
g7.start_act()
diff = sum(1 for r in range(21) for c in range(21) if g7.target[r][c] != mat[r][c])
check("封面码就是本局要复原的那张（同一张码）", g7.target == mat, "441 格里差了 %d 格" % diff)
check("...它扫出来就是那句话", g7.qr_content == QR_CONTENT, repr(g7.qr_content))

ui._TITLE_CACHE.pop("code", None)          # 清掉缓存 = 模拟「下一次启动」
second = ui._title_code()
check("每次启动都是同一张（内容固定，不再随机）", second == mat,
      "%d / %d 格" % (sum(map(sum, mat)), sum(map(sum, second))))
check("...仍然是一张合格的真码（三个定位图案）",
      second[0][0] and second[0][1] and not second[1][1])

# ---------- 8. 性能与流程 ----------
import time
t0 = time.perf_counter()
for i in range(60):
    g.menu_t = 2.0 + i / 60
    g.draw()
ms = (time.perf_counter() - t0) / 60 * 1000
check("开始页单帧 < 8ms（60fps 预算的一半）", ms < 8.0, "%.2fms" % ms)

g2 = fresh()
g2.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=40))     # ENTER
check("ENTER 开局（开始页没有别的入口）", g2.state != "TITLE", g2.state)
g3 = fresh()
g3.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=41))     # ESC
check("ESC 退出", not g3.running)

finish(TITLE)
