# -*- coding: utf-8 -*-
"""第二幕 · 「核心」机制验收（2026-11-15 作者定）。

规则：
  定位图案（finder）中心的 3×3 黑块 = 「核心」（共三块：TL / TR / BL，右下角没有）。
  第二幕起，怪物破坏核心（哪怕 1 格），对应板块就分离 —— 视觉上被推开一格、
  进度上那一整块不再计数；玩家补满 9 格核心，板块滑回原位。
"""

import pygame

from _act1_common import (all_boards, auto_mono, check, finish, new_game)
from src.config import BOARD_ADJACENT, BOARD_NUM, VALID
from src.entities import Monster
from src.grid import cell_center
from src.qr import core_board_of, finder_cores

TITLE = "第二幕 · 核心：破坏即分离，补满即合回"


def to_act2():
    """真实走完第一幕，再进第二幕（四块全开、棋盘 100 格已涂）。"""
    g = new_game()
    for _ in range(240):
        auto_mono(g)
        g.update(1 / 60)
    g.state = "FREE_ROAM"
    all_boards(g)
    g.start_act2()
    g.state = "BATTLE"
    g.spawn_rate = 0.0
    g.monsters.clear()
    g.purples.clear()
    return g


cores = finder_cores()
check("核心只有三块（TL / TR / BL，右下角没有）", set(cores) == {"TL", "TR", "BL"}, str(sorted(cores)))
check("每块核心正好 9 格", all(len(v) == 9 for v in cores.values()),
      str({k: len(v) for k, v in cores.items()}))
check("核心都在定位图案中心（QR 局部 2..4）",
      all(all(2 <= (r - 2) % 7 <= 4 and 2 <= (c - 2) % 7 <= 4 for (r, c) in v) for v in cores.values()))

# --- 编号与相邻关系（作者 2026-11-15 定）---
check("编号：BL=1 / TL=2 / TR=3 / BR=4（顺时针）",
      BOARD_NUM == {"BL": 1, "TL": 2, "TR": 3, "BR": 4}, str(BOARD_NUM))
check("板块 1（BL）相邻 2 和 4", set(BOARD_ADJACENT["BL"]) == {"TL", "BR"}, str(BOARD_ADJACENT["BL"]))
check("板块 2（TL）相邻 1 和 3", set(BOARD_ADJACENT["TL"]) == {"BL", "TR"}, str(BOARD_ADJACENT["TL"]))
check("板块 3（TR）相邻 2 和 4", set(BOARD_ADJACENT["TR"]) == {"TL", "BR"}, str(BOARD_ADJACENT["TR"]))
check("板块 4（BR）相邻 1 和 3", set(BOARD_ADJACENT["BR"]) == {"BL", "TR"}, str(BOARD_ADJACENT["BR"]))
check("右下角（板块 4）没有核心 → 是「不动的锚点」", "BR" not in cores)

# --- core_board_of：单格反查 ---
check("core_board_of 认得出 TL 核心", core_board_of((5, 5)) == "TL", str(core_board_of((5, 5))))
check("core_board_of 认得出 TR 核心", core_board_of((5, 19)) == "TR", str(core_board_of((5, 19))))
check("core_board_of 认得出 BL 核心", core_board_of((19, 5)) == "BL", str(core_board_of((19, 5))))
check("非核心格返回 None", core_board_of((12, 12)) is None and core_board_of((1, 1)) is None)

# --- 红怪吃掉核心一格 → 分离 ---
g = to_act2()
base = g.board.progress()
check("（准备）第二幕开局四块全开、无分离", g.board.detached == set()
      and g.board.progress() == 100, "prog %d detached %s" % (g.board.progress(), g.board.detached))

tl = sorted(cores["TL"])
m = Monster(cell_center(*tl[0]), 200.0)
m.target = tl[0]
m.mode = "dark"
g.monsters.append(m)
g.board.state[tl[0][0]][tl[0][1]] = VALID
for _ in range(300):
    auto_mono(g)
    g.update(1 / 60)
    if g.board.detached:
        break
check("红怪吃掉核心一格 → TL 分离", g.board.detached == {"TL"}, str(g.board.detached))
check("分离后 TL 那 33 格不再计入进度", g.board.progress() == base - 33,
      "%d → %d" % (base, g.board.progress()))

# --- 补满核心 → 合回 ---
for (r, c) in tl:
    if g.board.state[r][c] != VALID:
        g.board.reveal_around(r, c)
        g.board.paint(r, c)
for _ in range(30):
    auto_mono(g)
    g.update(1 / 60)
check("补满核心 9 格 → TL 合回", g.board.detached == set(), str(g.board.detached))
check("合回后进度恢复", g.board.progress() == base, "%d" % g.board.progress())

# --- 紫怪清行擦到核心 → 也分离 ---
g2 = to_act2()
bl = sorted(cores["BL"])
# BL 核心在主网格行 18~20（QR 16..18 + 偏移 2），清掉一整行 19 会擦到
g2.board.clear_line("row", 19)
g2.on_line_core_damaged("row", 19)
check("紫怪清行擦到 BL 核心 → BL 分离", g2.board.detached == {"BL"}, str(g2.board.detached))

# --- 擦到非核心的行 → 不分离 ---
g3 = to_act2()
g3.board.clear_line("row", 8)          # 第 8 行不经过任何核心
g3.on_line_core_damaged("row", 8)
check("清行不碰核心 → 不分离", g3.board.detached == set(), str(g3.board.detached))

# --- 第一幕不该有这个机制 ---
g4 = new_game()
for _ in range(240):
    auto_mono(g4)
    g4.update(1 / 60)
g4.on_core_damaged((5, 5))             # 即使给个核心格，act=1 也直接返回
check("第一幕没有「核心分离」", g4.board.detached == set(), str(g4.board.detached))

finish(TITLE)
