# -*- coding: utf-8 -*-
"""截一张第五幕：紫怪把定时图案那一行清空，老者正走过去补。"""
import os
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro, SHOT_DIR
from src.config import VALID, WHITE

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

# 模拟紫怪清掉第 6 行（定时图案那一整行）：主网格坐标 +2
for c in range(2, 23):
    g.board.state[8][c] = WHITE

t = 0.0
while t < 4.6:
    auto_mono(g)
    g.update(1 / 60)
    t += 1 / 60
g.draw()
os.makedirs(SHOT_DIR, exist_ok=True)
p = os.path.join(SHOT_DIR, "act5_help.png")
pygame.image.save(g.canvas, p)
print("oldman", (round(g.oldman.pos.x), round(g.oldman.pos.y)),
      "target", g.repair_target, "repair_i", g.repair_i,
      "frame_broken", g.frame_broken())
print(p)
