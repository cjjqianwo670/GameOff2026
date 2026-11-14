# -*- coding: utf-8 -*-
"""探针：长按进度会不会跨格子累计（站在 A 半秒，挪到 B，再按 0.35 秒能不能写 B）。"""
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro
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
g.yellow_spawned = 10**6
g.update_yellows = lambda dt: None
g.oldman.down = True                       # 老头停笔
white = sorted(c for c in g.format_cells if g.board.state[c[0]][c[1]] == WHITE)
# 找一对相邻的格式格
pair = None
ws = set(white)
for (r, c) in white:
    if (r, c + 1) in ws:
        pair = ((r, c), (r, c + 1))
        break
print("相邻一对", pair)
a, b = pair
stand = lambda cell: (setattr(g.player, "cell", cell), g.player.pos.update(cell_center(*cell)))
stand(a)
g.board.reveal_around(*a); g.board.reveal_around(*b)
g.input.held.add(SC_J)
for _ in range(int(0.5 * 60)):
    auto_mono(g); g.update(1 / 60)
print("在 A 按了 0.5s：fill_t=%.2f A=%d B=%d" % (g.fill_t, g.board.state[a[0]][a[1]], g.board.state[b[0]][b[1]]))
stand(b)
for _ in range(int(0.35 * 60)):
    auto_mono(g); g.update(1 / 60)
g.input.held.discard(SC_J)
print("挪到 B 再按 0.35s：fill_t=%.2f B 状态=%s（1=VALID，0=白）"
      % (g.fill_t, g.board.state[b[0]][b[1]]))
