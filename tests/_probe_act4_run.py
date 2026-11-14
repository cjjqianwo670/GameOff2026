# -*- coding: utf-8 -*-
"""探针：第四幕让一个「会扫的玩家」打完，量时长与血量（带怪）。"""
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro
from src.config import SC_J, VALID, WHITE

ENTER, SHIFT = 40, 225
SW, SA, SS, SD = 26, 4, 22, 7      # 走路也用按键，别绕过 MOVE_REPEAT


def to_act4():
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
    return g


def nearest(g):
    cand = [(r, c) for (r, c) in g.must if g.board.state[r][c] == WHITE]
    if not cand:
        return None
    px, py = g.player.pos
    return min(cand, key=lambda rc: (rc[0] * 28 - py) ** 2 + (rc[1] * 28 - px) ** 2)


def run(seed):
    g = to_act4()
    g.rng.seed(seed)
    g.input.held.add(SC_J)                  # 一直按住 J（扫）
    t = 0.0
    shift_cd = 0.0
    while t < 240 and g.state == "BATTLE":
        tgt = nearest(g)
        if tgt is None:
            break
        r, c = g.player.cell
        # 站着的地方没灰域 → 放下 J 照一下（照的时候按 J 是照不出来的）
        if g.board.reveal[r][c] <= 0 and shift_cd <= 0:
            g.input.held.discard(SC_J)
            g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=SHIFT))
            g.input.held.add(SC_J)
            shift_cd = 0.45
        tr, tc = tgt
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
    print("第 %d 局：%.1f 秒 / 状态 %s / 血 %d / 进度 %d/%d / 脏格 %d / 紫怪 %d / 红怪 %d"
          % (seed + 1, t, g.state, g.health, g.board.progress(), len(g.must),
             g.board.stains, len(g.purples), len(g.monsters)))
