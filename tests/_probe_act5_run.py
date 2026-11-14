# -*- coding: utf-8 -*-
"""探针：第五幕让一个会修的机器人打（带怪），量时长、错误数、存活。"""
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro
from src.config import SC_J, VALID, WHITE
from src.qr import ERROR_TOLERANCE

SHIFT = 225
SW, SA, SS, SD = 26, 4, 22, 7


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
    return g


def bad_cells(g):
    """所有「该黑却是白」的格（要修的洞）。"""
    out = []
    for mods in g.cw_modules.values():
        for (r, c, dark) in mods:
            if dark and g.board.state[r][c] != VALID:
                out.append((r, c))
    return out


def run(seed):
    g = to_act5()
    g.rng.seed(seed)
    g.input.held.add(SC_J)
    t = 0.0
    shift_cd = 0.0
    while t < 180 and g.state == "BATTLE":
        cells = bad_cells(g)
        if not cells:
            break
        px, py = g.player.pos
        tr, tc = min(cells, key=lambda rc: (rc[0] * 28 - py) ** 2 + (rc[1] * 28 - px) ** 2)
        r, c = g.player.cell
        if g.board.reveal[r][c] <= 0 and shift_cd <= 0:
            g.input.held.discard(SC_J)
            g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=SHIFT))
            g.input.held.add(SC_J)
            shift_cd = 0.4
        for k in (SW, SA, SS, SD):
            g.input.held.discard(k)
        if tr > r:
            g.input.held.add(SS)
        elif tr < r:
            g.input.held.add(SW)
        elif tc > c:
            g.input.held.add(SD)
        elif tc < c:
            g.input.held.add(SA)
        auto_mono(g)
        g.update(1 / 60)
        shift_cd -= 1 / 60
        t += 1 / 60
    return t, g


for seed in range(5):
    t, g = run(seed)
    print("第 %d 局：%.1f 秒 / 状态 %s / 血 %d / 错误 %d / 修到 %d 块内=%s"
          % (seed + 1, t, g.state, g.health, g.act5_errors(),
             ERROR_TOLERANCE, g.act5_errors() <= ERROR_TOLERANCE))
