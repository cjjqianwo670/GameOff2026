# -*- coding: utf-8 -*-
"""探针：第四幕到底会不会刷黄怪（文档说没有，代码是 act>=3）。"""
from _act1_common import auto_mono, new_game, paint_ok, skip_intro
from src.config import VALID

def to(act):
    g = new_game()
    for (r, c) in sorted(g.board.must):
        paint_ok(g, r, c)
    g.start_act2()
    for (r, c) in sorted(g.must):
        if g.board.state[r][c] != VALID: paint_ok(g, r, c)
    g.start_act3()
    for (r, c) in sorted(g.must):
        if g.board.state[r][c] != VALID: paint_ok(g, r, c)
    if act >= 4:
        g.start_act4()
    skip_intro(g)
    g.spawn_rate = 0.0
    g.monsters.clear(); g.purples.clear()
    g.spawn_purple = lambda: None
    return g

for act in (3, 4):
    g = to(act)
    g.oldman.hp = 999 if g.oldman else None
    for _ in range(int(20 * 60)):
        auto_mono(g)
        g.update(1/60)
    print("act %d：20 秒后黄怪 %d 只 / 老者 %s hp %s" %
          (act, len(g.yellows), "在场" if (g.oldman and not g.oldman.gone) else "不在",
           getattr(g.oldman, "hp", None)))
