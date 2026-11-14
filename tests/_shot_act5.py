# -*- coding: utf-8 -*-
"""截两张：第五幕开局（侵蚀出的洞 + HUD ERRORS）与扫描中。"""
import os
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro, SHOT_DIR
from src.config import VALID, SCAN_TIME
from src.qr import ERROR_TOLERANCE


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
    g.monsters.clear(); g.purples.clear(); g.spawn_purple = lambda: None
    return g


g = to_act5()
for _ in range(30):                      # 让开场那句独白过去
    auto_mono(g)
    g.update(1/60)
g.draw()
os.makedirs(SHOT_DIR, exist_ok=True)
p1 = os.path.join(SHOT_DIR, "act5_start.png")
pygame.image.save(g.canvas, p1)
print("errors", g.act5_errors(), "frame", g.frame_broken(), p1)

# 修到 3 块
for _ in range(g.act5_errors() - ERROR_TOLERANCE):
    for k, mods in g.cw_modules.items():
        if any(g.board.state[r][c] != (VALID if dark else 0) for (r, c, dark) in mods):
            for (r, c, dark) in mods:
                if dark:
                    g.board.state[r][c] = VALID
            break
auto_mono(g)
g.update(1/60)
for _ in range(int(SCAN_TIME * 0.55 * 60)):   # 扫到一半
    auto_mono(g)
    g.update(1/60)
g.draw()
p2 = os.path.join(SHOT_DIR, "act5_scan.png")
pygame.image.save(g.canvas, p2)
print("state", g.state, p2)

for _ in range(int(SCAN_TIME * 60)):
    auto_mono(g)
    g.update(1/60)
g.draw()
p3 = os.path.join(SHOT_DIR, "act5_end.png")
pygame.image.save(g.canvas, p3)
print("final", g.state, g.banner_text, "|", g.end_line, p3)
