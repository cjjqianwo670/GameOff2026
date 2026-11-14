# -*- coding: utf-8 -*-
"""截一张第四幕：老者走回来补骨架（定位图案被抹白一块）。"""
import os
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro, SHOT_DIR
from src.config import VALID, WHITE
from src.qr import structural_black_cells

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

# 抹掉左上定位图案的一条边，让他去补
for cell in [(2, 2), (2, 3), (2, 4), (2, 5), (2, 6)]:
    g.board.state[cell[0]][cell[1]] = WHITE

t = 0.0
while t < 3.2:
    auto_mono(g)
    g.update(1 / 60)
    if g.oldman:
        g.oldman.update(1 / 60)
    t += 1 / 60
g.draw()
os.makedirs(SHOT_DIR, exist_ok=True)
p = os.path.join(SHOT_DIR, "act4_help.png")
pygame.image.save(g.canvas, p)
print("oldman", g.oldman.pos, "target", g.repair_target, "repair_i", g.repair_i)
print(p)
