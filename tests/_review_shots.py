# -*- coding: utf-8 -*-
"""评审用：按真实顺序走一遍，每一幕抓关键画面（不改游戏行为）。"""
import os
import sys
import traceback

import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro
from src.config import SC_ENTER, SC_J, VALID, WHITE
from src.grid import cell_center

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_shots", "review")
os.makedirs(OUT, exist_ok=True)


def tick(g, seconds, stop=None, keys=()):
    n = int(seconds * 60)
    for _ in range(n):
        auto_mono(g)
        for k in keys:
            g.input.held.add(k)
        g.update(1 / 60)
        if stop and g.state == stop:
            return True
    return False


def save(g, name):
    g.draw()
    p = os.path.join(OUT, name)
    pygame.image.save(g.canvas, p)
    print("  shot", p)


def goto(g, r, c):
    g.player.cell = (r, c)
    g.player.pos.update(cell_center(r, c))


def fill(g, limit=None):
    n = 0
    for (r, c) in sorted(list(g.must)):
        if limit is not None and n >= limit:
            return n
        if g.board.state[r][c] != VALID:
            paint_ok(g, r, c)
            n += 1
    return n


def goto_altar(g):
    goto(g, 12, 12)


def end_act(g):
    # 先清场再补格：怪会一边吃一边涂，不散场永远填不满（这也是真实难度的体现）
    g.spawn_rate = 0.0
    g.monsters.clear()
    g.purples.clear()
    g.yellows.clear()
    g.update_yellows = lambda dt: None
    g.board.wipe_stains()          # 脏格（含压在必涂格上的）必须先擦，否则永远补不上
    fill(g)
    goto_altar(g)
    a = tick(g, 7.0, "CLEAR")
    b = tick(g, 16.0, "REWARD")
    g.items = []
    g.reward_phase = "wait2"
    g.reward_t = 0.0
    c = tick(g, 40.0, "END")
    print("   end_act act=%s clear=%s reward=%s end=%s state=%s"
          % (g.act, a, b, c, g.state))
    return g.state


steps = []


def step(fn):
    steps.append(fn)
    return fn


@step
def s_title(g):
    g.state = "TITLE"
    g.menu_t = 1.0
    tick(g, 0.5)
    save(g, "00_title.png")


@step
def s_intro(g):
    g.start_act()
    tick(g, 1.95)
    save(g, "01_intro_falling.png")


@step
def s_wake(g):
    tick(g, 1.5, "TUTORIAL")
    g.draw()
    pygame.image.save(g.canvas, os.path.join(OUT, "02_wake_M1.png"))
    print("  shot 02_wake_M1.png  state=", g.state)
    auto_mono(g, 5)
    tick(g, 0.3)
    save(g, "03_tutorial_hint.png")


@step
def s_shift(g):
    # 走过 5 秒 → 提示 TRY [SHIFT]
    for _ in range(int(5.2 * 60)):
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=225))
        auto_mono(g)
        g.update(1 / 60)
        if g.state != "TUTORIAL":
            break
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=225))
    tick(g, 0.2)
    save(g, "04_first_grey_M2.png")


@step
def s_act1_battle(g):
    skip_intro(g)
    g.enter_free_roam()
    g.start_gap()
    tick(g, 11.0, "BATTLE")
    g.spawn_rate = 60.0
    tick(g, 6.0)
    fill(g, 30)
    goto(g, 10, 9)
    tick(g, 1.0)
    save(g, "05_act1_battle.png")
    print("  act1 use", len(g.must), "painted", g.board.progress())


@step
def s_act1_messy(g):
    # 涂错几格 + 挨咬：看脏格和血量的表达
    for (r, c) in [(6, 6), (7, 6), (8, 6), (9, 6), (10, 6), (11, 6)]:
        goto(g, r, c)
        g.board.paint(r, c)          # 没照过 → 脏格
    g.health = 55
    goto(g, 9, 10)
    tick(g, 1.2)
    save(g, "06_act1_stains_health.png")


@step
def s_act1_clear(g):
    g.spawn_rate = 0.0
    g.monsters.clear()
    g.board.wipe_stains()
    fill(g)
    goto_altar(g)
    tick(g, 2.4, "CLEAR")
    tick(g, 0.55)
    save(g, "07_clear_wave.png")
    tick(g, 6.0, "REWARD")
    tick(g, 1.4)
    save(g, "08_reward_items.png")
    print("   clear/reward state", g.state, "items", len(g.items))
    g.items = []
    g.reward_phase = "wait2"
    g.reward_t = 0.0
    tick(g, 40.0, "END")
    save(g, "09_act1_end.png")


@step
def s_act2(g):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=SC_ENTER))
    tick(g, 0.8)
    save(g, "10_act2_open.png")
    print("  act2 state", g.state, "must", len(g.must))


@step
def s_act2_purple(g):
    tick(g, 12.0, "BATTLE")
    g.spawn_rate = 0.0
    # 让紫怪真去清一条线
    tick(g, 9.0)
    save(g, "11_act2_purple.png")
    print("  act2 purple", len(g.purples), "progress", g.board.progress())
    fill(g)
    end_act(g)


@step
def s_act3(g):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=SC_ENTER))
    tick(g, 1.2)
    save(g, "12_act3_dialog.png")
    print("  act3 state", g.state, "must", len(g.must))


@step
def s_act3_scribe(g):
    # 把对话点完
    for _ in range(40):
        g.dlg_t = 99.0
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=SC_ENTER))
        g.update(1 / 60)
        if g.state == "BATTLE":
            break
    tick(g, 6.0)
    save(g, "13_act3_scribe_yellow.png")
    print("  act3 scribe", len(g.scribe_cells), "done", g.scribe_i, "yellow", len(g.yellows))


@step
def s_act3_down(g):
    g.oldman.hp = 0
    g.on_oldman_down()
    tick(g, 0.6)
    save(g, "14_act3_oldman_down.png")


@step
def s_act4(g):
    fill(g)
    end_act(g)
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=SC_ENTER))
    tick(g, 0.5)
    g.spawn_rate = 0.0
    g.monsters.clear()
    g.purples.clear()
    white = sorted(c for c in g.must if g.board.state[c[0]][c[1]] == WHITE)
    cell = [c for c in white if 8 <= c[0] <= 13 and 8 <= c[1] <= 13][0]
    goto(g, *cell)
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=225))
    tick(g, 0.2)
    save(g, "15_act4_grey7x7.png")
    # 按住 J 向右扫：扫是靠「走」触发的，站着按只会写脚下那一格
    tick(g, 2.4, keys=(SC_J, 7))
    save(g, "16_act4_sweep.png")
    print("  act4 must", len(g.must), "progress", g.board.progress())


@step
def s_act5(g):
    fill(g)
    end_act(g)
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=SC_ENTER))
    tick(g, 0.6)
    g.spawn_rate = 0.0
    g.monsters.clear()
    g.purples.clear()
    tick(g, 0.3)
    save(g, "17_act5_eroded.png")
    print("  act5 errors", g.act5_errors())


@step
def s_scan(g):
    from src.qr import ERROR_TOLERANCE
    for _ in range(max(0, g.act5_errors() - ERROR_TOLERANCE)):
        for k, mods in g.cw_modules.items():
            if any(g.board.state[r][c] != (VALID if dark else 0) for (r, c, dark) in mods):
                for (r, c, dark) in mods:
                    if dark:
                        g.board.state[r][c] = VALID
                break
    goto_altar(g)
    tick(g, 1.2)
    save(g, "18_act5_before_scan.png")
    tick(g, 20.0, "SCAN")
    tick(g, 1.4)
    save(g, "19_scan.png")
    tick(g, 6.0, "END")
    tick(g, 1.0)
    save(g, "20_end.png")
    print("  end", g.state, "|", g.end_line)


g = new_game()
for fn in steps:
    print("==", fn.__name__)
    try:
        fn(g)
    except Exception:
        traceback.print_exc()
print("DONE")
