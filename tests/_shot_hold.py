# -*- coding: utf-8 -*-
"""截一张「按住 J 写格式格」的图，看脚下那圈进度。"""
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro, SHOT_DIR
from src.config import SC_J, VALID, WHITE
from src.grid import cell_center

g = new_game()
for (r, c) in sorted(g.board.must):
    paint_ok(g, r, c)
g.start_act2()
for (r, c) in sorted(g.must):
    if g.board.state[r][c] != VALID:
        paint_ok(g, r, c)
g.start_act3()
g.has_sword = True
for _ in range(400):
    auto_mono(g)
    g.update(1 / 60)
    g.dlg_t = 99.0
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=40))
    if g.state != "DIALOG":
        break
skip_intro(g)
g.spawn_rate = 0.0
g.yellow_spawned = 99
g.monsters.clear()
g.purples.clear()
g.spawn_purple = lambda: None

cell = sorted(c for c in g.format_cells if g.board.state[c[0]][c[1]] == WHITE)[0]
g.player.cell = cell
g.player.pos.update(cell_center(*cell))
g.board.reveal_around(*cell)
g.input.held.add(SC_J)
for _ in range(int(0.45 * 60)):
    auto_mono(g)
    g.update(1 / 60)
g.draw()
import os
os.makedirs(SHOT_DIR, exist_ok=True)
p = os.path.join(SHOT_DIR, "act3_hold.png")
pygame.image.save(g.canvas, p)
print("fill_t=%.2f hint=%r" % (g.fill_t, g.hint_text))
print(p)

zoom = 4
cx, cy = cell_center(*cell)
w = 90
sub = g.canvas.subsurface(pygame.Rect(int(cx - w / 2), int(cy - w / 2), w, w)).copy()
big = pygame.transform.scale(sub, (w * zoom, w * zoom))
p2 = os.path.join(SHOT_DIR, "act3_hold_zoom.png")
pygame.image.save(big, p2)
print("cell", cell, "center", (cx, cy))
print(p2)
