# -*- coding: utf-8 -*-
"""独立 QA：第四、五幕的边角情况（不是断言套件，是找茬）。"""
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro
from src.config import SC_J, SC_K, SC_M, VALID, WHITE
from src.qr import ERROR_TOLERANCE
from src.grid import cell_center

ENTER, SHIFT = 40, 225
SHIFT = 225


def to(act):
    g = new_game()
    for (r, c) in sorted(g.board.must):
        paint_ok(g, r, c)
    if act >= 2:
        g.start_act2()
        for (r, c) in sorted(g.must):
            if g.board.state[r][c] != VALID:
                paint_ok(g, r, c)
    if act >= 3:
        g.start_act3()
        for (r, c) in sorted(g.must):
            if g.board.state[r][c] != VALID:
                paint_ok(g, r, c)
    if act >= 4:
        g.start_act4()                 # 第四幕：数据区故意不填（真玩法就是从这里开始扫）
    if act >= 5:
        for (r, c) in sorted(g.must):
            if g.board.state[r][c] != VALID:
                paint_ok(g, r, c)
        g.start_act5()
    skip_intro(g)
    g.spawn_rate = 0.0
    g.monsters.clear(); g.purples.clear()
    g.spawn_purple = lambda: None
    g.update_yellows = lambda dt: None
    return g


def tick(g, n):
    for _ in range(n):
        auto_mono(g)
        g.update(1 / 60)


print("=" * 60)
print("A. 第四幕：地图摊开时按住 J")
g = to(4)
g.has_map = True
white = sorted(c for c in g.must if g.board.state[c[0]][c[1]] == WHITE)
g.player.cell = white[0]; g.player.pos.update(cell_center(*white[0]))
g.board.reveal_around(*white[0], radius=3)
auto_mono(g)      # 开场那句心声会冻住世界，得先推过去
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=SC_M))
g.input.held.add(SC_J)
tick(g, 60)
g.input.held.discard(SC_J)
print("  map_open=%s 格子=%d（应为0=白）fill_t=%.2f" % (g.map_open, g.board.state[white[0][0]][white[0][1]], g.fill_t))

print("B. 第四幕：K 擦掉再扫")
g.input.held.add(SC_K)
tick(g, 20)
g.input.held.discard(SC_K)
print("  擦除后状态=%d（3=ERASING 或 0）" % g.board.state[white[0][0]][white[0][1]])

print("C. 第五幕：把 9 块全修好（错误 0）会不会也进扫描")
g = to(5)
for _ in range(20):
    bad = [k for k, mods in g.cw_modules.items()
           if any(g.board.state[r][c] != (VALID if dark else WHITE) for (r, c, dark) in mods)]
    if not bad:
        break
    for (r, c, dark) in g.cw_modules[bad[0]]:
        if dark:
            g.board.state[r][c] = VALID
tick(g, 2)
print("  errors=%d state=%s（应为 SCAN）" % (g.act5_errors(), g.state))

print("D. 第五幕：扫描中按 ESC / R 会不会卡")
g = to(5)
for _ in range(20):
    bad = [k for k, mods in g.cw_modules.items()
           if any(g.board.state[r][c] != (VALID if dark else WHITE) for (r, c, dark) in mods)]
    if not bad:
        break
    for (r, c, dark) in g.cw_modules[bad[0]]:
        if dark:
            g.board.state[r][c] = VALID
tick(g, 2)
before = g.state
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=41))   # ESC
print("  ESC 前 %s → 后 %s" % (before, g.state))
g = to(5)
for _ in range(20):
    bad = [k for k, mods in g.cw_modules.items()
           if any(g.board.state[r][c] != (VALID if dark else WHITE) for (r, c, dark) in mods)]
    if not bad:
        break
    for (r, c, dark) in g.cw_modules[bad[0]]:
        if dark:
            g.board.state[r][c] = VALID
tick(g, 2)
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=21))   # R
tick(g, 5)
print("  R 之后 act=%d state=%s" % (g.act, g.state))

print("E. 第五幕：跑 90 秒（有红怪+紫怪），不崩、不卡死")
g = to(5)
g.spawn_purple = type(g).spawn_purple.__get__(g)
g.spawn_rate = 12.0
t = 0.0
frames = 0
while t < 90 and g.state in ("BATTLE", "SCAN", "DEAD", "END"):
    auto_mono(g)
    g.update(1 / 60)
    g.draw()
    t += 1 / 60
    frames += 1
print("  %.1fs / %d 帧 / state=%s / errors=%d / hp=%d / 怪 %d+%d"
      % (t, frames, g.state, g.act5_errors(), g.health, len(g.monsters), len(g.purples)))

print("F. 第五幕：错误数在死亡检查点后是否回到本幕开头")
g = to(5)
base = g.act5_errors()
g.health = 5
for _ in range(10):
    g.health = max(0, g.health - 5)
    tick(g, 1)
    if g.state == "DEAD":
        break
g.restore_checkpoint()
print("  DEAD→%s act=%d errors=%d（进幕时 %d）" % (g.state, g.act, g.act5_errors(), base))

print("G. 第五幕：骨架被红怪吃掉一格后，玩家能修回来吗")
g = to(5)
fr, fc, fdark = [m for m in g.fn_modules if m[2]][0]
g.board.state[fr][fc] = WHITE
g.board.reveal_around(fr, fc, radius=3)
g.player.cell = (fr, fc); g.player.pos.update(cell_center(fr, fc))
g.input.held.add(SC_J)
tick(g, 3)
g.input.held.discard(SC_J)
print("  骨架格=%d（1=VALID 才算修好）frame_broken=%d" % (g.board.state[fr][fc], g.frame_broken()))
print("=" * 60)
