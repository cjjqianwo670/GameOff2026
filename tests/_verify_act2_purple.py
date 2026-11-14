# -*- coding: utf-8 -*-
"""第二幕 · 紫怪（the purple one）验收。

规则来源：作者 2026-11-11 拍板（见 DATA_SHIFT_第二幕待定清单.md P1~P9）
  P3 只锁圣坛内的有效黑域
  P2 清「黑格更多」的那条（行 vs 列）
  P4 清整条 25 格（含圣坛外平地诱饵）
  P9 脏格不算黑格：不计入比较，也不被清掉
  默认  平局选离玩家远的那条；一生一次；撞完由 game 移除

夹具说明：这里**直接设置 board.state**，不走 paint()。
因为 paint() 对「圣坛内非必涂格」只会产生脏格，用它造不出想要的 VALID 布局。
paint() 的规则已经由 _verify_act1_board.py 覆盖，这里测的是紫怪。
"""

import sys


import random  # noqa: E402

import pygame  # noqa: E402

from _act1_common import check, finish  # noqa: E402
from src.board import Board  # noqa: E402
from src.config import (  # noqa: E402
    DIRTY, PURPLE_EAT_DIST, PURPLE_HIT_DAMAGE, PURPLE_HIT_DIST, PURPLE_RADIUS, PURPLE_SPEED,
    VALID, WHITE
)
from src.entities import PurpleOne  # noqa: E402
from src.grid import cell_center  # noqa: E402
from src.qr import generate_target, required_cells  # noqa: E402


def new_board():
    t, _ = generate_target(random.Random(42))
    return Board(t, required_cells(t, act=2))


def fill(b, cells, state=VALID):
    """夹具：直接把这些格子设成某个状态。"""
    for r, c in cells:
        b.state[r][c] = state


def run_to_target(p, b, player=None, limit=2000):
    """让紫怪一直走到「撞上」，返回第一次的非 alive 返回值。"""
    for _ in range(limit):
        res = p.update(1 / 60, b, player)
        if res != "alive":
            return res
    return "timeout"


# ==================== 1. 只锁圣坛内（P3） ====================
b = new_board()
fill(b, [(0, 0)])                      # 平地（圣坛外）造一格黑，离紫怪最近
fill(b, [(12, 12)])                    # 圣坛内一格
p = PurpleOne(cell_center(0, 1))
p.retarget(b)
check("平地黑格更近，但紫怪只锁圣坛内的格（P3）", p.target == (12, 12), "%s" % (p.target,))

b2 = new_board()
fill(b2, [(0, 0), (0, 1)])             # 只有平地黑格
p2 = PurpleOne(cell_center(0, 1))
check("坛内一格黑都没有 → 锁不到目标", p2.retarget(b2) is False, "%s" % (p2.target,))

before = pygame.Vector2(p2.pos)
p2.update(1 / 60, b2)
check("没有目标时朝圣坛中心漂（不是原地发呆）", p2.pos.distance_to(before) > 0,
      "移动 %.2fpx" % p2.pos.distance_to(before))

# ==================== 2. 锁最近的坛内黑格 ====================
b3 = new_board()
fill(b3, [(8, 8), (18, 18)])
p3 = PurpleOne(cell_center(7, 7))
p3.retarget(b3)
check("锁最近的坛内黑格", p3.target == (8, 8), "%s" % (p3.target,))

# ==================== 3. 行 vs 列：清黑格更多的那条（P2） ====================
b4 = new_board()
fill(b4, [(10, c) for c in range(6, 14)])     # 第 10 行 8 格
fill(b4, [(11, 10), (12, 10)])                # 第 10 列：交点 + 这 2 格 = 3 格
check("构造有效：行 8 格 > 列 3 格",
      b4.line_dark("row", 10) == 8 and b4.line_dark("col", 10) == 3,
      "row=%d col=%d" % (b4.line_dark("row", 10), b4.line_dark("col", 10)))
axis, idx = PurpleOne(cell_center(10, 10)).pick_line(b4, (10, 10))
check("黑格多的那条是行 → 清行（P2）", (axis, idx) == ("row", 10), "%s,%s" % (axis, idx))

b5 = new_board()
fill(b5, [(r, 16) for r in range(6, 14)])     # 第 16 列 8 格
fill(b5, [(16, 15), (16, 17)])                # 第 16 行 2 格
check("构造有效：列 8 格 > 行 2 格",
      b5.line_dark("col", 16) == 8 and b5.line_dark("row", 16) == 2,
      "row=%d col=%d" % (b5.line_dark("row", 16), b5.line_dark("col", 16)))
axis, idx = PurpleOne(cell_center(16, 16)).pick_line(b5, (16, 16))
check("黑格多的那条是列 → 清列（P2）", (axis, idx) == ("col", 16), "%s,%s" % (axis, idx))

# ==================== 4. 平局 → 离玩家远的那条 ====================
b6 = new_board()
fill(b6, [(12, c) for c in (10, 11, 13)] + [(r, 12) for r in (10, 11, 13)])
check("构造有效：行 3 = 列 3（平局）",
      b6.line_dark("row", 12) == b6.line_dark("col", 12) == 3,
      "row=%d col=%d" % (b6.line_dark("row", 12), b6.line_dark("col", 12)))

cx, cy = cell_center(12, 12)
axis, _ = PurpleOne(cell_center(12, 12)).pick_line(b6, (12, 12), pygame.Vector2(cx, cy + 200))
check("平局：玩家在正下方 → 清离他更远的「行」", axis == "row", "%s" % (axis,))
axis2, _ = PurpleOne(cell_center(12, 12)).pick_line(b6, (12, 12), pygame.Vector2(cx + 200, cy))
check("平局：玩家在正右方 → 清离他更远的「列」", axis2 == "col", "%s" % (axis2,))

# ==================== 5. 撞到 → 清整条（P4） ====================
b7 = new_board()
row = 10
fill(b7, [(row, c) for c in range(6, 14)])
before = b7.line_dark("row", row)
p7 = PurpleOne(cell_center(row, 10))
res = run_to_target(p7, b7)
check("撞到锁定格 → 返回 ('wipe', axis, index, 清掉格数)",
      isinstance(res, tuple) and res == ("wipe", "row", row, before), "%s" % (res,))
check("整条线的有效黑域被清空", b7.line_dark("row", row) == 0,
      "剩 %d" % b7.line_dark("row", row))

# 整 25 格：圣坛外的平地诱饵也一起被清（P4）
b8 = new_board()
fill(b8, [(3, 0), (3, 1)])                    # 平地（圣坛外）
fill(b8, [(3, c) for c in range(6, 12)])      # 圣坛内
total_before = b8.line_dark("row", 3)
p8 = PurpleOne(cell_center(3, 6))
res8 = run_to_target(p8, b8)
check("先确定它清的是「行」", isinstance(res8, tuple) and res8[1] == "row", "%s" % (res8,))
check("清整条 25 格 → 圣坛外的平地诱饵也被清（P4）",
      b8.state[3][0] == WHITE and b8.state[3][1] == WHITE,
      "平地格状态 %d/%d（0=白）" % (b8.state[3][0], b8.state[3][1]))
check("清掉的数量 = 清之前这条线上的黑格数", res8[3] == total_before,
      "%d vs %d" % (res8[3], total_before))

# ==================== 6. 脏格不算黑格、也不被清（P9） ====================
b9 = new_board()
fill(b9, [(14, 18)], state=DIRTY)
fill(b9, [(14, 20)])
check("构造有效：有一格脏格", b9.state[14][18] == DIRTY, "%d" % b9.state[14][18])
check("脏格不计入「这条线有多少黑格」", b9.line_dark("row", 14) == 1,
      "line_dark=%d" % b9.line_dark("row", 14))

p9 = PurpleOne(cell_center(14, 20))
res9 = run_to_target(p9, b9)
check("撞到了（返回 wipe）", isinstance(res9, tuple) and res9[0] == "wipe", "%s" % (res9,))
check("清行时脏格**不被清掉**（P9）", b9.state[14][18] == DIRTY,
      "脏格状态 %d（2=脏）" % b9.state[14][18])
check("那唯一一格有效黑域被清了", b9.state[14][20] == WHITE, "%d" % b9.state[14][20])

# ==================== 7. 一生一次 ====================
check("撞完置 done", p9.done is True)
check("last_wipe 记下了这一次", p9.last_wipe is not None and p9.last_wipe[0] == "row",
      "%s" % (p9.last_wipe,))
fill(b9, [(16, 16)])                          # 故意再造一格黑，看它会不会又去吃
snapshot = [r[:] for r in b9.state]           # 快照要在填完之后取
again = p9.update(1 / 60, b9)
check("撞完不再动作（返回 alive，棋盘不变）",
      again == "alive" and [r[:] for r in b9.state] == snapshot)

# ==================== 8. 目标被抹掉 → 立刻改锁 ====================
b10 = new_board()
fill(b10, [(10, 10), (10, 16)])
p10 = PurpleOne(cell_center(10, 11))
p10.retarget(b10)
check("先锁最近的那个", p10.target == (10, 10), "%s" % (p10.target,))
b10.state[10][10] = WHITE                     # 玩家按 K 抹掉
p10.update(1 / 60, b10)
check("目标被抹掉 → 立刻改锁另一个", p10.target == (10, 16), "%s" % (p10.target,))

# ==================== 9. 坛内没黑域 → 转去扑人（P10，2026-11-12）====================
# 作者：圣坛内没有格子了，紫怪就攻击码序使；被打到扣 10% 血。

class _FakePlayer:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)


b12 = new_board()                                  # 全白：坛内一格黑域都没有
p12 = PurpleOne((0, 0))
check("（准备）坛内确实没有有效黑域",
      not any(b12.state[r][c] == VALID and b12.in_altar(r, c)
              for r in range(25) for c in range(25)))
check("坛内没黑域时锁不到目标", p12.retarget(b12) is False)

me = _FakePlayer(cell_center(12, 12))
p12.pos.update(cell_center(0, 0))
dist0 = (me.pos - p12.pos).length()
p12.update(0.5, b12, me)                           # 走半秒
dist1 = (me.pos - p12.pos).length()
check("它会朝玩家移动（不是留在原地）", dist1 < dist0, "%.1f → %.1f" % (dist0, dist1))

res12 = run_to_target(p12, b12, me, limit=3000)    # 一直追到撞上
check("撞到玩家 → 返回 ('hit',)", res12 == ("hit",), str(res12))
check("撞完就置 done（由 game 移除，不会一直追）", p12.done)

# 有黑域时仍然是清行，不会跑去追人
b13 = new_board()
fill(b13, [(12, 12), (12, 13), (12, 14)])
p13 = PurpleOne(cell_center(12, 14))
res13 = run_to_target(p13, b13, _FakePlayer(cell_center(0, 0)), limit=600)
check("坛内有黑域时仍然是清行（不会改去追人）",
      isinstance(res13, tuple) and res13[0] == "wipe", str(res13))

# 数值：10% 血、判定距离比黑格的大（体型大）
check("扑人判定距离 = PURPLE_HIT_DIST 且 > 撞黑格的距离",
      PURPLE_HIT_DIST > PURPLE_EAT_DIST, "%.1f > %.1f" % (PURPLE_HIT_DIST, PURPLE_EAT_DIST))
check("扑人扣血 = 10%", PURPLE_HIT_DAMAGE == 10, "%d" % PURPLE_HIT_DAMAGE)
check("比红怪咬一口（5%%）更疼", PURPLE_HIT_DAMAGE > 5, "%d > 5" % PURPLE_HIT_DAMAGE)

# ==================== 9. 数值与 config 对齐 ====================
p11 = PurpleOne((0, 0))
check("速度/半径取自 config", p11.speed == PURPLE_SPEED and p11.radius == PURPLE_RADIUS,
      "%.1f px/s / r=%d" % (p11.speed, p11.radius))
check("撞到判定距离 > 0", PURPLE_EAT_DIST > 0, "%.1f" % PURPLE_EAT_DIST)
check("比红怪慢（用户 P1 的意图）", PURPLE_SPEED < 62.0, "%.1f < 62" % PURPLE_SPEED)

finish("第二幕 · 紫怪")
