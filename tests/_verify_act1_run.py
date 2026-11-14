# -*- coding: utf-8 -*-
"""机制回归 + 性能：真实键位走一遍战斗段（走 / 照 / 涂 / 擦 / 挨打 / 清屏），单帧耗时。"""

import time

import pygame

from _act1_common import clear_wave1, auto_mono, check, fill_must, finish, new_game, shot, toast_text
from src import story
from src.config import GAP_SECONDS, SC_D, SC_J, SC_K, WHITE
from src.entities import Monster
from src.grid import cell_center

TITLE = "MECHANICS REGRESSION + PERF"


def ev(sc):
    return pygame.event.Event(pygame.KEYDOWN, key=0, scancode=sc)


def run(g, secs):
    """推进时间。心声会冻住世界，所以每帧先替玩家按一下回车（见 `_act1_common.auto_mono`）。"""
    for _ in range(max(1, int(secs * 60))):
        auto_mono(g)
        g.update(1 / 60)
        g.draw()


def put(g, cell):
    g.player.cell = cell
    g.player.pos.update(cell_center(*cell))


g = new_game()
run(g, 3.4)
g.enter_free_roam()
g.start_gap()
for _ in range(int((GAP_SECONDS + 0.1) * 60)):
    auto_mono(g)
    g.update(1 / 60)
check("空档结束进战斗", g.state == "BATTLE", g.state)

# --- 走路 ---
r0, c0 = g.player.cell
g.input.held.add(SC_D)
run(g, 0.45)
g.input.held.clear()
check("按 D 能往右走", g.player.cell[1] > c0 and g.player.cell[0] == r0, str(g.player.cell))

# --- 异象 ---
before = sum(1 for r in range(25) for c in range(25) if g.board.reveal[r][c] > 0)
g.handle_event(ev(225))
after = sum(1 for r in range(25) for c in range(25) if g.board.reveal[r][c] > 0)
check("战斗里按 Shift 照出灰域", after > before, "%d -> %d" % (before, after))

# --- 按着 Shift 时 J 涂不上 ---
g.input.held.add(SC_J)
g.input.held.add(225)
run(g, 0.2)
check("按着 Shift 时 J 涂不上去",
      g.board.state[g.player.cell[0]][g.player.cell[1]] == WHITE)
g.input.held.clear()

# --- 涂错 → 脏格 + 提示；K 擦掉但计数不减 ---
fr, fc = next((r, c) for r in range(2, 23) for c in range(2, 23)
              if (r, c) not in g.board.must)
put(g, (fr, fc))
g.input.held.add(SC_J)
run(g, 0.1)
g.input.held.clear()
check("涂错变脏黑", g.board.state[fr][fc] == 2, "%d" % g.board.state[fr][fc])
check("第一次涂脏格：教 K 的教学提示 + 一句嘀咕（飘字）",
      g.stain_warned and g.hint_text == story.HINT_CLEAR and toast_text(g) == story.MONO_STAIN)
shot(g, "09_stain_warning.png")
stains = g.board.stains
g.input.held.add(SC_K)
run(g, 0.4)
g.input.held.clear()
check("K 擦掉脏格", g.board.state[fr][fc] == WHITE)
check("擦掉后累计脏格不减", g.board.stains == stains, "%d" % g.board.stains)

# --- 被红怪打一下 ---
hp0 = g.health
cx, cy = cell_center(*g.player.cell)
g.monsters.append(Monster((cx + 20, cy), 200.0))
run(g, 0.3)
check("被红怪命中 -5%", g.health == hp0 - 5, "%d" % g.health)

# --- 涂满 → 清屏 → 奖励 ---
clear_wave1(g)                      # 第一幕第一波（33 格 + 迷你清屏）先过掉
fill_must(g)
check("100 格全复原", g.board.progress() == 100, "%d" % g.board.progress())
put(g, (12, 12))
run(g, 0.2)
check("进入清屏", g.state == "CLEAR", "%s/%s" % (g.state, g.clear_phase))
for _ in range(int(6.0 * 60)):                  # 发光 1.2 + 扩散 ~2.4 + 停顿 0.6
    if g.state == "REWARD":
        break
    auto_mono(g)
    g.update(1 / 60)
    g.draw()
check("波扫完 → 奖励阶段", g.state == "REWARD", g.state)
run(g, 1.8)                                     # REWARD_DELAY 之后才浮出
check("两个道具都浮出", len(g.items) == 2, "%d" % len(g.items))

# --- 性能 ---
t0 = time.perf_counter()
for _ in range(120):
    auto_mono(g)
    g.update(1 / 60)
    g.draw()
ms = (time.perf_counter() - t0) / 120 * 1000
check("单帧 update+draw < 8ms", ms < 8.0, "%.2f ms" % ms)

finish(TITLE)
