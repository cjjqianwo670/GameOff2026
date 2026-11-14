# -*- coding: utf-8 -*-
"""步骤 5 验收：血量（-5%/次、不回复、20 次死）+ 红怪改行为（有黑域吃黑域，没黑域追人）。"""

from _act1_common import auto_mono, check, finish, new_game, paint_ok, shot, to_battle
from src.config import (
    HIT_DAMAGE, HEALTH_MAX, RED_SPAWN_ACCEL, RED_SPAWN_ACCEL_PERIOD, RED_SPAWN_PER_MIN
)
from src.entities import Monster
from src.grid import cell_center

TITLE = "STEP 5 · HEALTH + RED ONES"


def run(g, secs, keep_monsters=False):
    for _ in range(int(secs * 60)):
        auto_mono(g)
        g.update(1 / 60)
        if not keep_monsters:
            for m in g.monsters:
                m.claim(g.claims)
            g.monsters.clear()


# --- 1) 场上有黑域 → 红怪吃黑域，不碰玩家 ---
g = to_battle(new_game())
b = g.board
mr, mc = sorted(b.must)[0]                       # 必涂格（暗模块）
paint_ok(g, mr, mc)                              # 先照再涂 → 有效黑域
g.monsters.append(Monster(cell_center(mr, mc + 3), 200.0))
run(g, 1.0, keep_monsters=True)
check("有黑域时红怪吃掉了那一格", b.state[mr][mc] == 0, "%d" % b.state[mr][mc])
check("吃掉后红怪自毁", len(g.monsters) == 0, "%d" % len(g.monsters))
check("有黑域时玩家没掉血", g.health == HEALTH_MAX, "%d" % g.health)
check("空盘后 claims 回收干净", g.claims == {}, str(g.claims))

# --- 2) 脏格不吸引红怪（脏格不是 the Dark）---
g = to_battle(new_game())
b = g.board
b.paint(12, 13)
b.state[12][13] = 2                              # 手动做成脏黑
b.stains = 1
m = Monster(cell_center(12, 13), 0.0)            # 原地不动，只看它选什么目标
m.retarget(b, g.claims)
check("脏格不当食物，红怪转为追人", m.mode == "hunt", m.mode)
m.claim(g.claims)

# --- 3) 场上没有黑域 → 追玩家，命中 -5%，自毁 ---
g = to_battle(new_game())
hp0 = g.health
g.monsters.append(Monster((cell_center(*g.player.cell)[0] + 20, cell_center(*g.player.cell)[1]), 120.0))
run(g, 0.5, keep_monsters=True)
check("没黑域时红怪追上玩家", hp0 - g.health == HIT_DAMAGE, "%d -> %d" % (hp0, g.health))
check("命中后红怪自毁", len(g.monsters) == 0, "%d" % len(g.monsters))

# --- 4) 血量不自然回复 ---
hp1 = g.health
run(g, 3.0)
check("血量不自然回复", g.health == hp1, "%d -> %d" % (hp1, g.health))

# --- 5) 连扣 20 次 → 阵亡 ---
g = to_battle(new_game())
hits = 0
for _ in range(20):
    if g.state != "BATTLE":
        break
    cx, cy = cell_center(*g.player.cell)
    g.monsters.append(Monster((cx + 20, cy), 200.0))
    for _ in range(30):
        auto_mono(g)
        g.update(1 / 60)
        if not g.monsters:
            break
    hits += 1
check("每次命中固定 -5%", HEALTH_MAX - hits * HIT_DAMAGE == g.health, "hits %d hp %d" % (hits, g.health))
check("连扣 20 次触发阵亡", hits == 20 and g.health == 0 and g.state == "DEAD",
      "hits %d hp %d state %s" % (hits, g.health, g.state))

# --- 6) 每 30 秒刷怪提速 5% ---
g = to_battle(new_game())
rate0 = g.spawn_rate
check("开局生成速率 = %.1f/分" % RED_SPAWN_PER_MIN, abs(rate0 - RED_SPAWN_PER_MIN) < 1e-9, "%.3f" % rate0)
g.elapsed = RED_SPAWN_ACCEL_PERIOD - 0.05
for _ in range(20):
    auto_mono(g)
    g.update(1 / 60)
    g.monsters.clear()
g.claims.clear()
expect = rate0 * RED_SPAWN_ACCEL
check("过 30 秒速率 ×%.2f" % RED_SPAWN_ACCEL, abs(g.spawn_rate - expect) < 1e-6,
      "%.4f / 期望 %.4f" % (g.spawn_rate, expect))

# --- 7) 出图：红怪在场 + 掉血 ---
g = to_battle(new_game())
b = g.board
for (r, c) in [(3, 4), (5, 6), (19, 17)]:
    paint_ok(g, r, c)
g.health = 65
cx, cy = cell_center(*g.player.cell)
g.monsters += [Monster((cx + 120, cy - 60), 60.0), Monster((cx - 150, cy + 90), 60.0),
               Monster((cx, cy + 200), 60.0)]
p = shot(g, "05_red_and_health.png")
print("  shot ->", p)
finish(TITLE)
