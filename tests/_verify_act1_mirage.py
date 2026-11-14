# -*- coding: utf-8 -*-
"""步骤 4 验收：Shift 异象（5×5 / 只在圣坛内 / 5 秒渐变 / 涂了也不消失）+ 像素断言。"""

import pygame

from _act1_common import auto_mono, check, clear_wave1, finish, new_game, shot, to_roam
from src.config import (C_CELL_WHITE, C_MUST, GRID_ORIGIN, MIRAGE_FADE, MIRAGE_RADIUS,
                       PLAYER_START_CELL)
from src.grid import cell_to_rect, cell_center

TITLE = "STEP 4 · THE ANOMALY (SHIFT)"


def px(g, r, c):
    return g.canvas.get_at(cell_to_rect(r, c).center)[:3]


def border_px(g, r, c):
    rect = cell_to_rect(r, c)
    return g.canvas.get_at((rect.x + 1, rect.centery))[:3]


def clear_reveal(g):
    """醒来时脚下自带一片灰（enter_tutorial 照的），测行为前先让它褪干净。"""
    for r in range(25):
        for c in range(25):
            g.board.reveal[r][c] = 0.0

g = to_roam(new_game())
clear_reveal(g)
b = g.board

# --- 1) 圣坛内按 Shift：只有「本幕必涂格」会变灰 ---
# 2026-11-14 设计变更：灰域原来按整张目标码（target）照，于是第一幕圣坛正中能照出 13 格灰，
# 那 13 格却全部不在本幕清单里 —— 照着灰涂就是 13 个脏格。现在灰域只照 must：
# 「它亮着，就是此刻该写的地方」。出生点在左下定位图案的正中（跟着 config 走，别再写死）。
SR, SC = PLAYER_START_CELL
g.player.cell = PLAYER_START_CELL
g.player.pos.update(cell_center(SR, SC))
n = b.reveal_around(SR, SC)
check("圣坛内按 Shift 有灰域出现", n > 0, "新照亮 %d 格" % n)

# 5×5 之外不能有灰域
outside = [(r, c) for r in range(25) for c in range(25)
           if max(abs(r - SR), abs(c - SC)) > MIRAGE_RADIUS and b.reveal[r][c] > 0]
check("灰域严格限制在脚下 5×5（±%d）" % MIRAGE_RADIUS, not outside, str(outside[:3]))
check("灰域只在圣坛内", all(b.in_altar(r, c) for r in range(25) for c in range(25) if b.reveal[r][c] > 0))
check("灰域只出现在「该黑且还白」的格子",
      all(b.target[r - 2][c - 2] == 1 and b.state[r][c] == 0
          for r in range(25) for c in range(25) if b.reveal[r][c] > 0))
check("灰域里每一格都是本幕必涂格（照着涂不会变脏）",
      all((r, c) in b.must for r in range(25) for c in range(25) if b.reveal[r][c] > 0))
check("第一幕圣坛正中（数据区）照不出灰域 —— 那里的活还没轮到",
      b.reveal_around(12, 12) == 0)

target_grey = [(r, c) for r in range(SR - 2, SR + 3) for c in range(SC - 2, SC + 3) if b.revealed(r, c)]
check("照出来的格子数 > 0", len(target_grey) > 0, str(target_grey[:4]))
g.draw()
r0, c0 = target_grey[0]
col_grey = px(g, r0, c0)
check("灰域像素不是纯白", col_grey != C_CELL_WHITE, str(col_grey))

# --- 2) 5 秒渐变回白（不是突然消失）---
for _ in range(int(2.5 * 60)):                 # 2.5 秒
    b.update(1 / 60)
g.draw()
col_mid = px(g, r0, c0)
check("半程（2.5s）像素变淡但不是白也不是最初那档灰",
      col_mid != col_grey and col_mid != C_CELL_WHITE, "%s vs %s" % (col_mid, col_grey))
check("半程像素更接近白（渐变方向正确）",
      col_mid[0] > col_grey[0], "%d > %d" % (col_mid[0], col_grey[0]))

for _ in range(int(2.6 * 60)):                 # 累计 5.1 秒
    b.update(1 / 60)
g.draw()
check("5 秒后灰域计时归零", b.reveal[r0][c0] == 0.0, "%.3f" % b.reveal[r0][c0])
check("5 秒后像素回到纯白", px(g, r0, c0) == C_CELL_WHITE, str(px(g, r0, c0)))

# --- 3) 平地上按 Shift：一个灰域都没有 ---
g2 = to_roam(new_game()); clear_reveal(g2)
g2.player.cell = (0, 0)
n2 = g2.board.reveal_around(0, 0)
check("平地按 Shift 返回 0", n2 == 0, "%d" % n2)
check("平地按 Shift 全盘无灰域",
      all(g2.board.reveal[r][c] == 0 for r in range(25) for c in range(25)))

# --- 4) 照过之后涂黑：异象不消失（只是那格变黑了）---
g3 = to_roam(new_game()); clear_reveal(g3)
b3 = g3.board
# 暗模块在第二波才轮得到（第一幕分两波），先补完第一波那 33 格
g3.player.cell = (15, 12)
g3.player.pos.update(cell_center(15, 12))
b3.reveal_around(15, 12)
check("第一波：暗模块还不在清单里，照不出来", not b3.revealed(15, 10))
clear_wave1(g3)
clear_reveal(g3)
g3.state = "FREE_ROAM"
g3.player.cell = (15, 12)                      # 暗模块 (15,10) 落在 5×5 里
g3.player.pos.update(cell_center(15, 12))
b3.reveal_around(15, 12)
check("暗模块被照出来（本轮必涂格）", b3.revealed(15, 10))
b3.paint(15, 10)
check("涂黑之后那格是有效黑域", b3.state[15][10] == 1)
check("涂黑不会清掉异象计时（灰域还在，只是格子黑了）", b3.reveal[15][10] > 0,
      "%.2f" % b3.reveal[15][10])
check("绿框只画在「照出来了的必涂格」上", (15, 10) in b3.must)

# --- 5) Shift 按键走通 handle_event（scancode）---
g4 = to_roam(new_game()); clear_reveal(g4)
auto_mono(g4)                                   # 开场那句 M1 会把世界冻住，任何键都按不出来
g4.player.cell = PLAYER_START_CELL
g4.player.pos.update(cell_center(*PLAYER_START_CELL))
ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LSHIFT, scancode=225, mod=1)
g4.handle_event(ev)
clicked = any(g4.board.reveal[r][c] > 0 for r in range(25) for c in range(25))
check("Shift 的 KEYDOWN（scancode 225）能触发异象", clicked)
ev_r = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RSHIFT, scancode=229, mod=1)
g4.handle_event(ev_r)
check("右 Shift（scancode 229）也能触发", any(g4.board.reveal[r][c] > 0 for r in range(25) for c in range(25)))

# --- 6) 出图：照出来的灰域 + 绿框 ---
g5 = to_roam(new_game()); clear_reveal(g5)
b5 = g5.board
clear_wave1(g5)                        # 暗模块的第二波，绿框才在它上面
clear_reveal(g5)
g5.state = "FREE_ROAM"
g5.player.cell = (15, 12)
g5.player.pos.update(cell_center(15, 12))
b5.reveal_around(15, 12)
# 顺手涂几格、留一格脏黑，给用户看「灰域 / 绿框 / 有效黑域 / 脏黑」四种样子
b5.paint(16, 2)           # 左下定位图案的一格 → 有效黑域（纯黑）
b5.paint(14, 12)          # 圣坛内非必涂 → 脏黑
for _ in range(int(1.2 * 60)):
    b5.update(1 / 60)
g5.draw()
col_green = border_px(g5, 15, 10)      # 暗模块：照出来了、还是白、且是必涂格
check("必涂格的绿框颜色正确", col_green == C_MUST, str(col_green))

p = shot(g5, "04_anomaly_grey.png")
print("  shot ->", p)
finish(TITLE)
