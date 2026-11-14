# -*- coding: utf-8 -*-
"""截一张第四幕：灰域 + 扫过的黑域 + HUD。"""
import os
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro, SHOT_DIR
from src.config import SC_J, VALID
from src.grid import cell_center

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
skip_intro(g)
g.spawn_rate = 0.0
g.monsters.clear(); g.purples.clear()

# 站到数据区中间，照一下，往右扫两格
white = sorted(c for c in g.must if g.board.state[c[0]][c[1]] == 0)
cell = [c for c in white if 8 <= c[0] <= 13 and 8 <= c[1] <= 13][0]
g.player.cell = cell
g.player.pos.update(cell_center(*cell))
for _ in range(10):
    auto_mono(g); g.update(1/60)
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=225))
g.input.held.add(SC_J)
for _ in range(int(0.5 * 60)):
    g.input.held.add(7)
    auto_mono(g); g.update(1/60)
g.input.held.clear()
g.draw()
os.makedirs(SHOT_DIR, exist_ok=True)
p = os.path.join(SHOT_DIR, "act4_sweep.png")
pygame.image.save(g.canvas, p)
print("act", g.act, "progress", g.board.progress(), "/", len(g.must), "cell", g.player.cell)
print(p)
