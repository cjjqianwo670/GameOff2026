# -*- coding: utf-8 -*-
"""脏格新规则验收：累计超过额度 **不判负**，改成每次 -5% 血量；血量归零 → 检查点。"""

from _act1_common import auto_mono, check, fill_must, finish, new_game, to_battle, to_roam, toast_text
from src import story
from src.config import HEALTH_MAX, STAIN_DAMAGE, STAIN_LIMIT
from src.grid import cell_center

TITLE = "STAIN RULE · OVER BUDGET = BLEED, NOT LOSE"


def dump_stain_cells(g, n):
    """在圣坛内涂出 n 格脏格（返回用掉的位置）。"""
    used = []
    for r in range(2, 23):
        for c in range(2, 23):
            if len(used) >= n:
                return used
            if (r, c) in g.board.must or g.board.state[r][c] != 0:
                continue
            g.player.cell = (r, c)
            g.player.pos.update(cell_center(r, c))
            g.paint_here()
            used.append((r, c))
    return used


g = to_roam(new_game())
b = g.board

# --- 额度内：不掉血 ---
dump_stain_cells(g, STAIN_LIMIT)
check("第 %d 格脏格：血量不变" % STAIN_LIMIT, g.health == HEALTH_MAX, "%d" % g.health)
check("额度内 stains = %d" % STAIN_LIMIT, b.stains == STAIN_LIMIT, "%d" % b.stains)
check("额度内 没超额（stains ≤ STAIN_LIMIT）", b.stains <= STAIN_LIMIT, "%d" % b.stains)

# --- 第 11 格：不判负，扣 5% ---
dump_stain_cells(g, 1)
check("第 11 格脏格：不算失败（没进 DEAD）", g.state != "DEAD", g.state)
check("第 11 格脏格：血量 -%d%%" % STAIN_DAMAGE, g.health == HEALTH_MAX - STAIN_DAMAGE, "%d" % g.health)
check("第 11 格脏格：计数是 11", b.stains == 11, "%d" % b.stains)
check("脏格超标扣血 → 一句嘀咕（飘字，不再是 STAIN -x% 数字提示）",  toast_text(g) == story.MONO_STAIN_HURT, repr(toast_text(g)))

# --- 再涂两格：继续掉血 ---
dump_stain_cells(g, 2)
check("第 13 格脏格：血量累计 -15%", g.health == HEALTH_MAX - 3 * STAIN_DAMAGE, "%d" % g.health)

# --- 20 格时的血量（记录实际数字，别只写注释）---
dump_stain_cells(g, 7)
check("第 20 格脏格：血量 = %d" % (HEALTH_MAX - 10 * STAIN_DAMAGE),
      g.health == HEALTH_MAX - 10 * STAIN_DAMAGE, "%d" % g.health)

# --- 100 格涂满 + 脏格超额度，仍然可以通关（不再被脏格卡住）---
g2 = to_roam(new_game())
fill_must(g2)
g2.board.stains = STAIN_LIMIT + 5
check("脏格超额度依然算通关", g2.board.is_complete(), "stains %d" % g2.board.stains)

# --- 涂到血量归零：进 DEAD，再回检查点 ---
g3 = to_battle(new_game())
made = dump_stain_cells(g3, STAIN_LIMIT + int(HEALTH_MAX / STAIN_DAMAGE))
check("一直涂脏格会把血涂光", g3.health == 0, "health %d / stains %d" % (g3.health, g3.board.stains))
auto_mono(g3)
g3.update(1 / 60)
check("血量归零 → DEAD", g3.state == "DEAD", g3.state)
g3.on_click(600, 500)
check("回检查点：血满、棋盘全白、计数清零",
      g3.state == "GAP" and g3.health == HEALTH_MAX and g3.board.stains == 0
      and all(v == 0 for row in g3.board.state for v in row),
      "%s %d %d" % (g3.state, g3.health, g3.board.stains))

finish(TITLE)
