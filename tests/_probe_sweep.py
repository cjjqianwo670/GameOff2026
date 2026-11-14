# -*- coding: utf-8 -*-
"""探针：按住 J 边走边涂，现在会发生什么？（决定第四幕「自动写入」值不值几天）"""
from _act1_common import auto_mono, new_game, to_battle, skip_intro
from src.config import SC_J, VALID, DIRTY, WHITE

g = new_game()
to_battle(g)
skip_intro(g)
g.spawn_rate = 0.0
g.monsters.clear()

# 先照一片 5x5，然后按住 J 向右走 5 格
r0, c0 = g.player.cell
g.board.reveal_around(r0, c0 + 2)
before = (g.board.progress(), g.board.stains)
g.input.held.add(SC_J)
for _ in range(int(1.2 * 60)):
    auto_mono(g)
    g.update(1 / 60)
    g.player.update(1 / 60, (0, 1))          # 一边按 J 一边往右走
g.input.held.discard(SC_J)
print("起点 (r,c)=", (r0, c0), "终点", g.player.cell)
print("进度 %d → %d，脏格 %d → %d" % (before[0], g.board.progress(), before[1], g.board.stains))
print("按住 J 走过 5 格：干净的 %d 格，脏的 %d 格"
      % (g.board.progress() - before[0], g.board.stains - before[1]))
