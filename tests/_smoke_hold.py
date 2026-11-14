# -*- coding: utf-8 -*-
"""冒烟：第三幕正常节奏跑 40 秒（有黄怪有紫怪），玩家一边走一边按 J，不能崩。"""
import random
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro
from src.config import SC_J, SC_K, SC_U, VALID

random.seed(7)
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

t = 0.0
frames = 0
while t < 40 and g.state in ("BATTLE", "CLEAR", "REWARD", "END"):
    if frames % 25 == 0:                      # 每 0.4 秒换个动作
        g.input.held.clear()
        g.input.held.add(random.choice([SC_J, SC_J, SC_K, SC_U]))
    if frames % 7 == 0:
        g.player.update(1 / 60, random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)]))
    auto_mono(g)
    g.update(1 / 60)
    g.draw()
    frames += 1
    t += 1 / 60
print("跑了 %.1f 秒 / %d 帧，状态 %s，血 %d，写格 %d，黄怪 %d，格式格还白 %d 个"
      % (t, frames, g.state, g.health, g.scribe_i, len(g.yellows),
         len([1 for (r, c) in g.format_cells if g.board.state[r][c] == 0])))
print("SMOKE OK")
