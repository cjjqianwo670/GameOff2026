# -*- coding: utf-8 -*-
"""冒烟：从标题一路推到 ACT 5 — END（前四幕「直接涂满」，第五幕修错 + 扫描）。

2026-11-14 改：第一幕现在是**四块板块**（BL → TL → TR → BR），所以「涂满一次就收工」
不成立了 —— 必须一块一块写，每写完一块等它合并。原来的 `finish_wave1()` 只等一次合并，
于是卡在第二块，而脚本末尾无条件打印 `FULL RUN OK` —— 又一次「假绿」。
现在每一步都断言，任何一步不对就 `sys.exit(1)`。
"""
import sys

import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro
from src.config import VALID, WHITE

ENTER = 40
_steps = []          # [(这一步叫什么, 实际状态, 期望状态)]


def check(name, got, want):
    _steps.append((name, got, want))
    return got == want


def fill_all(g):
    for (r, c) in sorted(list(g.must)):
        if g.board.state[r][c] == WHITE:
            paint_ok(g, r, c)


def finish_act1(g):
    """第一幕：四块板块逐块写满，每块写完等它合并（右下那块 0 格，直接进终局清屏）。"""
    for _ in range(6):
        fill_all(g)
        for _ in range(1200):
            auto_mono(g)
            g.update(1 / 60)
            if g.state in ("REWARD", "END"):
                return g.state
        if g.state == "BATTLE" and not [x for x in g.must if g.board.state[x[0]][x[1]] == WHITE]:
            return g.state        # 写满了却没动静：交给下面的断言去报
    return g.state


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
g.spawn_rate = 0.0
check("第一幕进战斗", g.state, "BATTLE")

finish_act1(g)
check("第一幕四块拼完", g.state, "REWARD")
check("第一幕四块全部接回", "".join(sorted(g.board.open_boards)), "BLBRTLTR")
check("第一幕 100/100", g.board.progress(), 100)
finish(g)
check("第一幕收尾", g.state, "END")
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
check("进第二幕", g.act, 2)

tick(g, 300, "BATTLE")
g.spawn_rate = 0.0
g.monsters.clear(); g.purples.clear(); g.spawn_purple = lambda: None
fill_all(g)
finish(g)
check("第二幕收尾", g.state, "END")
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
check("进第三幕", g.act, 3)

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
check("第三幕收尾", g.state, "END")
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
check("进第四幕", g.act, 4)

g.spawn_rate = 0.0
g.monsters.clear(); g.purples.clear(); g.spawn_purple = lambda: None
g.update_yellows = lambda dt: None
fill_all(g)
finish(g)
check("第四幕收尾", g.state, "END")
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
check("进第五幕", g.act, 5)

# 第五幕：把错误修到容量以内 → 扫描 → 结局
from src.qr import ERROR_TOLERANCE
for _ in range(max(0, g.act5_errors() - ERROR_TOLERANCE)):
    for k, mods in g.cw_modules.items():
        if any(g.board.state[r][c] != (VALID if dark else 0) for (r, c, dark) in mods):
            for (r, c, dark) in mods:
                if dark:
                    g.board.state[r][c] = VALID
            break
in_altar(g)
tick(g, 2400, "END")
check("第五幕收尾", g.state, "END")
check("终幕那句话", g.end_line.endswith("YOU WERE HERE"), True)
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
check("回车回标题", g.state, "TITLE")

bad = [s for s in _steps if s[1] != s[2]]
for name, got, want in _steps:
    if got != want:
        print("  FAIL  %s：期望 %r，实际 %r" % (name, want, got))
if bad:
    print("FAILED %d / %d 步" % (len(bad), len(_steps)))
    sys.exit(1)
print("%d / %d 步全过" % (len(_steps), len(_steps)))
print("FULL RUN OK")
