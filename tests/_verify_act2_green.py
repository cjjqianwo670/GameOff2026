# -*- coding: utf-8 -*-
"""第二幕 · 绿怪（the green one）验收。

规则（作者 2026-11-16 定）：
  · 绿怪是红怪的「面扩展版」：锁最近的有效黑域，走到后以该格为中心清 3×3（最多 9 格）
  · 只清有效黑域，脏格不碰（和红怪/紫怪一致）
  · 擦到定位图案核心（哪怕 1 格）→ 触发板块分离（和红怪吃核心一致）
  · 一生一次，清完自毁
  · 场上没黑域 → 追玩家，撞到扣血

夹具：直接设置 board.state，不走 paint()（paint 对非必涂格只会产生脏格）。
"""

import random

import pygame

from _act1_common import check, finish
from src.board import Board
from src.config import (
    DIRTY, GREEN_EAT_DIST, GREEN_HIT_DAMAGE, GREEN_RADIUS, VALID, WHITE
)
from src.entities import GreenOne
from src.grid import cell_center
from src.qr import generate_target, required_cells


def new_board():
    t, _ = generate_target(random.Random(42))
    return Board(t, required_cells(t, act=2))


def fill(b, cells, state=VALID):
    for r, c in cells:
        b.state[r][c] = state


# ==================== 1. 锁最近的有效黑域 ====================
b = new_board()
fill(b, [(15, 5)])                 # 一格有效黑域
g = GreenOne(cell_center(15, 8))   # 放在它右边 3 格
assert g.retarget(b, {})
check("绿怪锁最近的有效黑域", g.target == (15, 5), str(g.target))

# 脏格不算
b2 = new_board()
fill(b2, [(15, 5)], state=DIRTY)   # 只有脏格
g2 = GreenOne(cell_center(10, 10))
check("场上只有脏格 → 锁不到（追玩家）", g2.retarget(b2, {}) is False and g2.mode == "hunt")

# ==================== 2. 走到后清 3×3 ====================
b3 = new_board()
center = (12, 12)
# 以 (12,12) 为中心的 3×3：行 11-13、列 11-13，铺满 9 格黑域
for r in range(11, 14):
    for c in range(11, 14):
        b3.state[r][c] = VALID
g3 = GreenOne(cell_center(*center))   # 直接站在中心
res = g3.update(1 / 60, b3, {}, None)
wiped = res[1] if isinstance(res, tuple) and res[0] == "wipe" else []
check("撞到目标后清 3×3（返回 9 格）", res[0] == "wipe" and len(wiped) == 9, "%s / %d 格" % (res[0] if isinstance(res, tuple) else res, len(wiped)))
check("9 格全变白", all(b3.state[r][c] == WHITE for r in range(11, 14) for c in range(11, 14)))

# 3×3 边界外的不动
b4 = new_board()
fill(b4, [(12, 12)])               # 中心黑域（绿怪锁它）
fill(b4, [(10, 10), (14, 14)])     # 3×3 边界外两格黑域
g4 = GreenOne(cell_center(12, 12))
g4.retarget(b4, {})                # 锁 (12,12)（最近）
res4 = g4.update(1 / 60, b4, {}, None)
wiped4 = res4[1] if isinstance(res4, tuple) else []
check("只清以目标为中心的 3×3（边界外的 (10,10)/(14,14) 不动）",
      set(wiped4) == {(12, 12)} and b4.state[10][10] == VALID and b4.state[14][14] == VALID,
      str(wiped4))

# 脏格不碰
b5 = new_board()
fill(b5, [(12, 12)], state=VALID)
fill(b5, [(11, 11)], state=DIRTY)   # 3×3 内的脏格
g5 = GreenOne(cell_center(12, 12))
res5 = g5.update(1 / 60, b5, {}, None)
check("3×3 内的脏格不被清（脏格不是 the Dark）", b5.state[11][11] == DIRTY,
      "state=%d" % b5.state[11][11])

# ==================== 3. 一生一次 ====================
b6 = new_board()
fill(b6, [(12, 12)])
g6 = GreenOne(cell_center(12, 12))
g6.update(1 / 60, b6, {}, None)
check("清完 3×3 自毁（done=True）", g6.done)

# ==================== 4. 没黑域追玩家 ====================
b7 = new_board()
p7 = GreenOne(cell_center(5, 5))
from src.entities import Player
pl = Player()
pl.cell = (10, 10)
pl.pos.update(cell_center(10, 10))
p7.retarget(b7, {})                # 没黑域 → hunt
# 直接把绿怪贴到玩家身上
p7.pos.update(pl.pos)
res7 = p7.update(1 / 60, b7, {}, pl)
check("没黑域时扑人 → 返回 hit", res7 == ("hit",), str(res7))

finish("第二幕 · 绿怪")
