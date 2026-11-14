# -*- coding: utf-8 -*-
"""探针：第五幕老者是否只补骨架、不碰数据区，以及他补完之后能否进扫描。"""
from _act1_common import auto_mono, new_game, paint_ok, skip_intro, toast_text
from src.config import VALID, WHITE, ERODE_EVERY
from src.qr import CODEWORD_INDEX, structural_black_cells
from src import story

ENTER, SHIFT = 40, 225


def to_act5():
    g = new_game()
    for (r, c) in sorted(g.board.must):
        paint_ok(g, r, c)
    g.start_act2()
    for (r, c) in sorted(g.must):
        if g.board.state[r][c] != VALID:
            paint_ok(g, r, c)
    g.start_act3()
    for (r, c) in sorted(g.must):
        if g.board.state[r][c] != VALID:
            paint_ok(g, r, c)
    g.start_act4()
    for (r, c) in sorted(g.must):
        if g.board.state[r][c] != VALID:
            paint_ok(g, r, c)
    g.start_act5()
    skip_intro(g)
    g.spawn_rate = 0.0
    g.monsters.clear()
    g.purples.clear()
    g.spawn_purple = lambda: None
    return g


def tick(g, n):
    for _ in range(n):
        auto_mono(g)
        g.update(1 / 60)


g = to_act5()
print("他在场:", g.oldman is not None and not g.oldman.gone,
      "| 他管 %d 格" % len(g.repair_cells),
      "| 和数据区重叠:",
      sum(1 for (r, c) in g.repair_cells if CODEWORD_INDEX[r - 2][c - 2] >= 0))
print("骨架格 = structural_black_cells:", g.repair_cells == structural_black_cells(g.target))

# 敲掉一格定位图案
fr, fc, fdark = [m for m in g.fn_modules if m[2]][0]
g.board.state[fr][fc] = WHITE
t = 0.0
while g.board.state[fr][fc] != VALID and t < 15:
    tick(g, 1)
    t += 1 / 60
print("骨架被敲掉一格 → %.1f 秒后修好=%s，repair_i=%d" % (t, g.board.state[fr][fc] == VALID, g.repair_i))

# 数据格被抹白 → 他不该碰
g2 = to_act5()
data_cell = None
for (r, c, dark) in g2.cw_modules[sorted(g2.cw_modules)[0]]:
    if dark:
        data_cell = (r, c)
        break
g2.board.state[data_cell[0]][data_cell[1]] = WHITE
tick(g2, int(10 * 60))
print("数据格被抹白 → 10 秒后仍是白的:", g2.board.state[data_cell[0]][data_cell[1]] == WHITE,
      "| 他的 target:", g2.repair_target, "| repair_i:", g2.repair_i)

# 骨架全修好 + 错误压到 3 → 扫描
g3 = to_act5()
while g3.act5_errors() > 3:
    for k, mods in g3.cw_modules.items():
        if any(g3.board.state[r][c] != (VALID if dark else WHITE) for (r, c, dark) in mods):
            for (r, c, dark) in mods:
                if dark:
                    g3.board.state[r][c] = VALID
            break
tick(g3, 200)
print("压到 3 块 → state:", g3.state, "| end_line:", g3.end_line,
      "| 他在扫描里还在吗:", g3.oldman is not None and not g3.oldman.gone)
