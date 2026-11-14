# -*- coding: utf-8 -*-
"""探针：第三幕只放紫怪（2 只/分），老者 + 玩家都不动，看格式信息能不能自己补上。"""
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro
from src.config import VALID


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
    g.update_yellows = lambda dt: None
    g.monsters.clear(); g.yellows.clear()
    return g


for label in ("玩家不动", "玩家只补格式格"):
    g = to_act3()
    t = 0.0
    wiped = 0
    while t < 120 and g.state == "BATTLE":
        if label == "玩家只补格式格":
            white = [c for c in g.format_cells if g.board.state[c[0]][c[1]] == 0]
            if white:
                r, c = sorted(white)[0]
                g.player.cell = (r, c); g.player.pos.update(
                    (g.player.cell[1] * 28, g.player.cell[0] * 28))
                g.input.held.add(13)
            else:
                g.input.held.discard(13)
        auto_mono(g)
        g.update(1 / 60)
        t += 1 / 60
    white = len([1 for c in g.format_cells if g.board.state[c[0]][c[1]] == 0])
    print("%s：%.0f 秒后状态 %s / 进度 %d/%d / 格式格还白 %d / 脏格 %d / 紫怪 %d"
          % (label, t, g.state, g.board.progress(), len(g.must), white,
             g.board.stains, len(g.purples)))
