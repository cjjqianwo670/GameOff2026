# -*- coding: utf-8 -*-
"""步骤 7 验收：阵亡 → 重新开始界面 → 回到「老者离开」检查点。"""

from _act1_common import clear_wave1, auto_mono, check, finish, new_game, paint_ok, shot, to_battle
from src.config import HEALTH_MAX, PLAYER_START_CELL, RED_SPAWN_PER_MIN, WHITE
from src.entities import Monster
from src.grid import cell_center

TITLE = "STEP 7 · CHECKPOINT"

g = to_battle(new_game())
b = g.board
check("检查点存下来了", g.checkpoint is not None)
check("检查点开局是满血", g.checkpoint["health"] == HEALTH_MAX, "%d" % g.checkpoint["health"])
check("检查点开局全白",
      all(v == WHITE for row in g.checkpoint["board"]["state"] for v in row))
check("检查点开局脏格 0", g.checkpoint["board"]["stains"] == 0)

# --- 第一波里涂一半（33 格里先涂 20 格）、放几只怪、掉血、让刷怪加速 ---
must = sorted(b.must)                           # 第一幕分两波，第一波只有左上角的 33 格
for (r, c) in must[:20]:
    paint_ok(g, r, c)
b.paint(0, 0)                                   # 平地诱饵
g.health = 55
g.elapsed = 61.0
g.spawn_rate = RED_SPAWN_PER_MIN * 1.05
g.accel_step = 2
cx, cy = cell_center(12, 12)
g.monsters = [Monster((cx + 100, cy), 60.0), Monster((cx - 100, cy + 60), 60.0)]
check("死亡前：进度 20 / 血 55 / 怪 2", b.progress() == 20 and g.health == 55 and len(g.monsters) == 2,
      "%d %d %d" % (b.progress(), g.health, len(g.monsters)))

# --- 死亡：直接扣到 0（20 次命中的最后一击，第 5 步已单独验过）---
g.health = 0
auto_mono(g)
g.update(1 / 60)
check("血量归零 → 进入 DEAD 界面", g.state == "DEAD" and g.health == 0, "%s %d" % (g.state, g.health))
shot(g, "07_dead.png")

# DEAD 期间世界冻结：不再刷怪、不再掉血
dead_monsters = len(g.monsters)
for _ in range(120):
    auto_mono(g)
    g.update(1 / 60)
check("DEAD 期间不刷怪", len(g.monsters) == dead_monsters, "%d -> %d" % (dead_monsters, len(g.monsters)))
check("DEAD 期间血量不动", g.health == 0, "%d" % g.health)

# --- 点击回到检查点 ---
g.on_click(600, 500)
check("点击后回到检查点（GAP 起点）", g.state == "GAP", g.state)
check("血量回满", g.health == HEALTH_MAX, "%d" % g.health)
check("棋盘回到全白", b.progress() == 0 and
      all(v == WHITE for row in b.state for v in row), "progress %d" % b.progress())
check("脏格累计清零", b.stains == 0, "%d" % b.stains)
check("红怪全部清空", len(g.monsters) == 0, "%d" % len(g.monsters))
check("claims 清空", g.claims == {}, str(g.claims))
check("刷怪加速复位（速率回到开局值）", abs(g.spawn_rate - RED_SPAWN_PER_MIN) < 1e-9,
      "%.3f" % g.spawn_rate)
check("战斗计时复位", g.elapsed == 0.0, "%.2f" % g.elapsed)
check("玩家回到出生点", g.player.cell == PLAYER_START_CELL, str(g.player.cell))
check("波的状态复位", g.clear_phase is None and g.wave_r == 0.0)

# --- 回车也能重来 ---
g.health = 0
g.state = "DEAD"
import pygame
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, scancode=40))
check("Enter 也能从 DEAD 回到检查点", g.state == "GAP" and g.health == HEALTH_MAX, g.state)

p = shot(g, "07_after_checkpoint.png")
print("  shot ->", p)

# ================= 第二波的检查点（2026-11-14 双波改造）=================
# 第一波写完会**重打一次检查点**：死在第二波不该被踢回「什么都没写」的开场。
g2 = to_battle(new_game())
b2 = g2.board
ok = clear_wave1(g2)
check("第一波清完 → 进入第二波（must 换成整张码 100 格）",
      ok and g2.act1_wave == 2 and len(g2.must) == 100, "%s %d" % (g2.state, len(g2.must)))
check("第二波开局：第一波那 33 格还在", b2.progress() == 33, "%d" % b2.progress())
for (r, c) in sorted(g2.must)[-10:]:
    paint_ok(g2, r, c)
g2.health = 0
auto_mono(g2)
g2.update(1 / 60)
check("第二波里血归零 → DEAD", g2.state == "DEAD", g2.state)
g2.on_click(600, 500)
check("死在第二波 → 回到第二波起点（不是整幕开头）", g2.state == "BATTLE", g2.state)
check("棋盘保留第一波的 33 格", b2.progress() == 33, "%d" % b2.progress())
check("血量回满、怪清空", g2.health == HEALTH_MAX and not g2.monsters,
      "%d %d" % (g2.health, len(g2.monsters)))
check("第二波的 must 仍是整张码（不会缩回 33）", len(g2.must) == 100 and g2.act1_wave == 2,
      "%d / wave %d" % (len(g2.must), g2.act1_wave))

finish(TITLE)
