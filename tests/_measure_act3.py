# -*- coding: utf-8 -*-
"""量第三幕节奏：老者独自写完格式信息要多久（完全不放怪）。"""
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro
from src.config import SCRIBE_PAUSE, VALID


def to_act3():
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
    g.spawn_purple = lambda: None
    g.update_yellows = lambda dt: None            # 整幕不放黄怪
    g.monsters.clear(); g.purples.clear(); g.yellows.clear()
    return g


g = to_act3()
n = len(g.format_cells)
t = 0.0
while g.state == "BATTLE" and t < 180:
    auto_mono(g)
    g.update(1 / 60)
    t += 1 / 60
print("格式格 %d 个：老者独自写完 %.1f 秒（SCRIBE_PAUSE=%.2f），平均每格 %.1f 秒"
      % (n, t, SCRIBE_PAUSE, t / n))
print("state", g.state, "scribe_i", g.scribe_i, "剩余白格式格",
      [(r, c) for (r, c) in g.format_cells if g.board.state[r][c] == 0])
