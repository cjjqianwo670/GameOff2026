# -*- coding: utf-8 -*-
"""冒烟：从标题一路推到 ACT 4 — END（三幕用「直接涂满」，第四幕用扫）。"""
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro
from src.config import VALID, WHITE

ENTER = 40


def fill_all(g):
    for (r, c) in sorted(list(g.must)):
        if g.board.state[r][c] == WHITE:
            paint_ok(g, r, c)


def finish_wave1(g):
    """第一幕分两波：第一波（33 格）清一次屏，回来再写第二波（100 格）。"""
    fill_all(g)
    for _ in range(900):
        auto_mono(g)
        g.update(1 / 60)
        if getattr(g, "act1_wave", 2) == 2:
            return True
    return False


def in_altar(g):
    from src.grid import cell_center
    g.player.cell = (12, 12)
    g.player.pos.update(cell_center(12, 12))


def finish(g):
    """清屏 → 跳过拾取 → END。"""
    in_altar(g)
    tick(g, 400, "CLEAR")
    tick(g, 900, "REWARD")
    g.items = []
    g.reward_phase = "wait2"
    g.reward_t = 0.0
    tick(g, 2400, "END")
    if g.state != "END":
        print("  !! 卡在", g.state, "phase", g.reward_phase)


def tick(g, n, stop=None):
    for _ in range(n):
        auto_mono(g)
        g.update(1 / 60)
        if stop and g.state == stop:
            return True
    return False


g = new_game()
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))   # TITLE → 开局
skip_intro(g)
g.enter_free_roam()
g.start_gap()
tick(g, 900, "BATTLE")
print("act1", g.act, g.state)
g.spawn_rate = 0.0
print("wave1", finish_wave1(g), "must", len(g.must))
fill_all(g)
finish(g)
print("act1 end", g.state, g.banner_text)
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
print("act2", g.act, g.state)

tick(g, 300, "BATTLE")
g.spawn_rate = 0.0
g.monsters.clear(); g.purples.clear(); g.spawn_purple = lambda: None
fill_all(g)
finish(g)
print("act2 end", g.state, g.banner_text)
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
print("act3", g.act, g.state)
# 第三幕：老者写，玩家补 — 直接涂满，让老头那套逻辑不参与
for _ in range(600):
    auto_mono(g)
    g.dlg_t = 99.0
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
    g.update(1 / 60)
    if g.state == "BATTLE":
        break
g.spawn_rate = 0.0
g.yellow_spawned = 10**6
g.update_yellows = lambda dt: None
g.yellows.clear(); g.monsters.clear(); g.purples.clear(); g.spawn_purple = lambda: None
fill_all(g)
finish(g)
print("act3 end", g.state, g.banner_text)
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
print("act4", g.act, g.state, "must", len(g.must))
g.spawn_rate = 0.0
g.monsters.clear(); g.purples.clear(); g.spawn_purple = lambda: None
g.update_yellows = lambda dt: None
fill_all(g)
finish(g)
print("act4 end", g.state, g.banner_text)
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
print("act5", g.act, g.state, "errors", g.act5_errors())

# 第五幕：把错误修到容量以内 → 扫描 → 结局
from src.qr import ERROR_TOLERANCE
for _ in range(g.act5_errors() - ERROR_TOLERANCE):
    for k, mods in g.cw_modules.items():
        if any(g.board.state[r][c] != (VALID if dark else 0) for (r, c, dark) in mods):
            for (r, c, dark) in mods:
                if dark:
                    g.board.state[r][c] = VALID
            break
in_altar(g)
tick(g, 2400, "END")
print("act5 end", g.state, g.banner_text, "|", g.end_line)
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
print("after end", g.state)
print("FULL RUN OK")
