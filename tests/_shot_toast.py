# -*- coding: utf-8 -*-
"""截一张「嘀咕」：涂错一格，头顶飘一行字，世界照跑。"""
import os
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro, SHOT_DIR
from src.config import SC_J, VALID
from src.grid import cell_center

from _act1_common import to_battle

g = new_game()
to_battle(g)
skip_intro(g)
g.spawn_rate = 0.0
g.monsters.clear()

# 站到一格没照过的格上，按 J → 脏格 → 嘀咕
white = sorted(c for c in g.must if g.board.state[c[0]][c[1]] == 0)
cell = [c for c in white if c[0] >= 3][0]
g.player.cell = cell
g.player.pos.update(cell_center(*cell))
for rr in g.board.reveal:
    for i in range(len(rr)):
        rr[i] = 0.0
auto_mono(g)
g.input.held.add(SC_J)
for _ in range(12):
    auto_mono(g)
    g.update(1/60)
g.input.held.discard(SC_J)
for _ in range(6):                       # 让字淡入一点
    g.update(1/60)
g.draw()
os.makedirs(SHOT_DIR, exist_ok=True)
p = os.path.join(SHOT_DIR, "toast.png")
pygame.image.save(g.canvas, p)
print("toasts", g.toasts, "hold", g.mono_hold)
zoom_cell = cell
cx, cy = cell_center(*zoom_cell)
w = 220
sub = g.canvas.subsurface(pygame.Rect(int(cx - w/2), int(cy - 90), w, w)).copy()
big = pygame.transform.scale(sub, (w*3, w*3))
p2 = os.path.join(SHOT_DIR, "toast_zoom.png")
pygame.image.save(big, p2)
print(p); print(p2)
