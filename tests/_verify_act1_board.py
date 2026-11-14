# -*- coding: utf-8 -*-
"""步骤 3 验收：棋盘四态 + 100 必涂格 + 脏格累计不返还。"""

import pygame

from _act1_common import auto_mono, check, finish, new_game, shot
from src.config import (
    CELL, C_CELL_BLACK, C_CELL_WHITE, DIRTY, ERASING, GRID_ORIGIN, VALID, WHITE
)
from src.grid import cell_to_rect

TITLE = "STEP 3 · BOARD STATES / MUST-PAINT / STAINS"

g = new_game()
b = g.board
must = sorted(b.must)                           # 当前这一波（第一幕第一波 = 左下角 33 格）
check("必涂格 100 个（整幕合计）", len(g.must_all) == 100, "%d" % len(g.must_all))
check("第一波只发左下角那 33 格", len(b.must) == 33, "%d" % len(b.must))
check("两波拼起来就是整幕的必涂格", set(b.must) <= set(g.must_all))
check("必涂格都是目标黑格",
      all(g.target[r - 2][c - 2] == 1 for (r, c) in b.must))

# --- 0) 新规则（2026-11-12 作者定）：圣坛内**必须先照出来**才写得对 ---
# 「灰域还亮着」才认；没照过 / 灰域已褪 / 被怪清掉后重涂，一律脏格。
gb = new_game()
bb = gb.board
mr0, mc0 = sorted(bb.must)[0]
res = bb.paint(mr0, mc0)
check("没照过就涂必涂格 → 脏格（不是有效黑域）",
      res == "dirty" and bb.state[mr0][mc0] == DIRTY, "%s" % res)
check("...照样记一笔脏格（和涂错同一套代价）", bb.stains == 1, "%d" % bb.stains)
bb.state[mr0][mc0] = WHITE                       # 抹掉重来（走 K 要等 0.25s，这里直接复位）
bb.reveal_around(mr0, mc0)
res = bb.paint(mr0, mc0)
check("照出来（灰域亮着）再涂同一格 → VALID",
      res == "valid" and bb.state[mr0][mc0] == VALID, "%s" % res)

# 灰域 5 秒褪掉之后，那一格又算「没照过」
r2, c2 = sorted(bb.must)[1]
bb.reveal_around(r2, c2)
for _ in range(int(6.0 * 60)):
    bb.update(1 / 60)
check("灰域会褪（6 秒后这一格不再亮着）", bb.reveal[r2][c2] == 0.0, "%.2f" % bb.reveal[r2][c2])
res = bb.paint(r2, c2)
check("灰域褪了再涂 → 脏格（5 秒是硬时限）", res == "dirty", "%s" % res)

# 作者报的那个 bug：紫怪清掉一格后，不重新照就补涂
bb.force_white(mr0, mc0, "purple")
check("（准备）被紫怪清掉的那一格回到白", bb.state[mr0][mc0] == WHITE)
res = bb.paint(mr0, mc0)
check("被清掉后不重新照就补涂 → 脏格（这正是作者报的 bug）", res == "dirty", "%s" % res)
bb.state[mr0][mc0] = WHITE
bb.reveal_around(mr0, mc0)
check("重新照一下再补 → VALID", bb.paint(mr0, mc0) == "valid")

# --- 1) 必涂格：照出来之后上涂 → VALID ---
mr, mc = must[0]
b.reveal_around(mr, mc)
res = b.paint(mr, mc)
check("必涂格上涂 J → VALID", res == "valid" and b.state[mr][mc] == VALID, "%s %s" % (res, b.state[mr][mc]))
check("必涂格涂完不计脏格", b.stains == 0, "%d" % b.stains)
check("进度 +1", b.progress() == 1, "%d" % b.progress())

# --- 2) 圣坛内非必涂格涂 → DIRTY，累计 +1 ---
# 找一个圣坛内、非必涂、真码为白的格子（干净的例子）
free = None
for r in range(2, 23):
    for c in range(2, 23):
        if (r, c) not in b.must:
            free = (r, c)
            break
    if free:
        break
fr, fc = free
res = b.paint(fr, fc)
check("圣坛内非必涂格涂 J → DIRTY", res == "dirty" and b.state[fr][fc] == DIRTY, "%s" % res)
check("脏格累计 +1", b.stains == 1, "%d" % b.stains)

# 蒙涂也算：一个「该黑但不是本轮必涂」的信息区格子，没照过直接涂
blind = None
for r in range(2, 23):
    for c in range(2, 23):
        tr, tc = r - 2, c - 2
        if (r, c) not in b.must and g.target[tr][tc] == 1 and b.state[r][c] == WHITE:
            blind = (r, c)
            break
    if blind:
        break
if blind:
    res = b.paint(*blind)
    check("蒙涂（该黑但非必涂）也算脏格", res == "dirty" and b.stains == 2, "%s stains=%d" % (res, b.stains))
else:
    check("蒙涂（该黑但非必涂）也算脏格", True, "本例没有这种格子，跳过")

# --- 3) 擦掉脏格 → WHITE，累计不减 ---
before = b.stains
b.start_erase(fr, fc)
check("K 进入 ERASING", b.state[fr][fc] == ERASING)
for _ in range(20):
    b.update(1 / 60)
check("0.25s 后变回 WHITE", b.state[fr][fc] == WHITE, "%s" % b.state[fr][fc])
check("擦掉之后累计脏格不返还", b.stains == before, "%d / before %d" % (b.stains, before))

# --- 4) 平地上涂 → VALID，不计数 ---
pr, pc = 0, 0
res = b.paint(pr, pc)
check("平地涂 J → VALID（诱饵）", res == "plain" and b.state[pr][pc] == VALID, "%s" % res)
check("平地涂不计数", b.stains == before, "%d" % b.stains)
check("平地涂不计入进度", b.progress() == 1, "%d" % b.progress())

# --- 5) 脏黑外观：黑白相间，必须和纯黑一眼可分 ---
g2 = new_game()
b2 = g2.board
b2.reveal_around(mr, mc)
b2.paint(mr, mc)          # 一格有效黑域（照过才涂得上）
b2.paint(fr, fc)          # 一格脏黑
g2.draw()
rect = cell_to_rect(fr, fc)
vals = [g2.canvas.get_at((rect.x + dx, rect.y + dy))[:3]
        for dx in range(3, CELL - 3, 3) for dy in range(3, CELL - 3, 3)]
light = sum(1 for v in vals if v[0] > 180)
dark = sum(1 for v in vals if v[0] < 60)
check("脏黑格中心区域同时有亮条和暗条（黑白相间）", light > 0 and dark > 0,
      "light %d / dark %d" % (light, dark))
rect_v = cell_to_rect(mr, mc)
check("有效黑域是纯黑",
      g2.canvas.get_at((rect_v.centerx, rect_v.centery))[:3] == C_CELL_BLACK)

p = shot(g2, "03_valid_vs_stain.png")
print("  shot ->", p)
finish(TITLE)
