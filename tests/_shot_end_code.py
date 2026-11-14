# -*- coding: utf-8 -*-
"""截一张终幕：那张能扫的码 + IT READS。"""
import os
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro, SHOT_DIR
from src.config import VALID, WHITE, QR_CONTENT
from src.qr import ERROR_TOLERANCE
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
for (r, c) in sorted(g.must):
    if g.board.state[r][c] != VALID:
        paint_ok(g, r, c)
g.start_act5()
skip_intro(g)
g.spawn_rate = 0.0
g.monsters.clear(); g.purples.clear(); g.spawn_purple = lambda: None
g.update_yellows = lambda dt: None

# 把错误压到 3 块以内（留 3 块留白：这也是「不需要完美」的样子）
while g.act5_errors() > ERROR_TOLERANCE:
    for k, mods in g.cw_modules.items():
        if any(g.board.state[r][c] != (VALID if dark else WHITE) for (r, c, dark) in mods):
            for (r, c, dark) in mods:
                if dark:
                    g.board.state[r][c] = VALID
            break

g.player.cell = (12, 12)
g.player.pos.update(cell_center(12, 12))
for _ in range(int(4.5 * 60)):
    auto_mono(g)
    g.update(1 / 60)
g.dlg_t = 0.0
g.draw()
os.makedirs(SHOT_DIR, exist_ok=True)
p = os.path.join(SHOT_DIR, "act5_end_code.png")
pygame.image.save(g.canvas, p)
print("state", g.state, "| content", g.qr_content, "| end_line", g.end_line)
print(p)
