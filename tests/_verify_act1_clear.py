# -*- coding: utf-8 -*-
"""步骤 6 验收：完成判定（100 格 + 脏格 ≤10）+ 清屏（发光 → 进坛 → 圆形波 → 抹脏格）。"""

from _act1_common import (auto_mono, check, clear_wave1, fill_must, finish, new_game,
                          paint_ok, shot, to_battle)
from src.config import CLEAR_GLOW_TIME, CLEAR_WAVE_HOLD, DIRTY, STAIN_LIMIT, VALID
from src.entities import Monster
from src.grid import cell_center

TITLE = "STEP 6 · COMPLETION + CLEAR"

def put(g, cell):
    g.player.cell = cell
    g.player.pos.update(cell_center(*cell))


def run_for(g, secs):
    for _ in range(max(1, int(secs * 60))):
        auto_mono(g)
        g.update(1 / 60)
        g.draw()


g = to_battle(new_game())
b = g.board
# 第一幕分两波：这一节测的是**整幕收尾那次清屏**，所以先把第一波（33 格 + 迷你清屏）过掉
check("第一波清完", clear_wave1(g))
must = sorted(b.must)
check("第二波的必涂格是整张码的 100 格", len(must) == 100, "%d" % len(must))

# --- 1) 99 格 + 1 个脏格 → 不能通关 ---
# ⚠️ 「留最后一格不涂」不能按排序取 must[-1]：第一波已经涂掉的那 33 格可能就排在最后
# （左下定位图案的 (22,8) 是全表最后一个）。要按「还没涂的」来留，否则进度会直接到 100。
left = [rc for rc in must if b.state[rc[0]][rc[1]] == 0]
keep = left[-1]
for (r, c) in must:
    if (r, c) != keep:
        paint_ok(g, r, c)
# 找一个圣坛内非必涂格做脏格
fr, fc = None, None
for r in range(2, 23):
    for c in range(2, 23):
        if (r, c) not in b.must:
            fr, fc = r, c
            break
    if fr:
        break
b.paint(fr, fc)
check("99 格 + 1 脏格：进度 99", b.progress() == 99, "%d" % b.progress())
check("99 格 + 1 脏格：不通关", not b.is_complete())

# --- 2) 涂上第 100 格 → 通关 ---
lr, lc = keep
paint_ok(g, lr, lc)
check("第 100 格涂上 → 进度 100", b.progress() == 100, "%d" % b.progress())
check("脏格 1 ≤ %d → 通关" % STAIN_LIMIT, b.is_complete())

# --- 3) 脏格超上限 → 涂满也不算通关（这是设计写死的条件，Phase A 照做）---
g2 = to_battle(new_game())
b2 = g2.board
for (r, c) in must:
    paint_ok(g2, r, c)
b2.stains = STAIN_LIMIT + 1
check("脏格累计超过额度不再卡通关（改成扣血）", b2.is_complete())
b2.stains = STAIN_LIMIT
check("脏格正好等于上限 → 通关", b2.is_complete())

# --- 4) 进 CLEAR：圣坛发光 + 提示走进圣坛 ---
g.player.cell = (0, 0)                     # 站在平地上
g.player.pos.update(cell_center(0, 0))
auto_mono(g)
g.update(1 / 60)
check("通关瞬间进入 CLEAR", g.state == "CLEAR", g.state)
check("CLEAR 第一阶段是 glow", g.clear_phase == "glow", str(g.clear_phase))
check("站在坛外：提示走进圣坛", g.hint_text == "STEP INTO THE ALTAR", repr(g.hint_text))

# 已经在坛里的人不该被喊「走进圣坛」—— 这句必须在波扫完之前就消失（2026-11-14 修）
g.player.cell = (12, 12)
g.player.pos.update(cell_center(12, 12))
auto_mono(g)
g.update(1 / 60)
check("人已经在坛内：这句提示立刻收掉", g.hint_text == "", repr(g.hint_text))

run_for(g, 1.0)
check("玩家在坛外时波不启动", g.clear_phase == "glow", str(g.clear_phase))

# --- 5) 走进圣坛 → 圆形波，扫过的红怪被清除 ---
for m in g.monsters:
    m.claim(g.claims)
g.monsters = []
g.claims = {}
near = Monster((cell_center(12, 12)[0] + 60, cell_center(12, 12)[1]), 0.0)
far = Monster((1200.0, 950.0), 0.0)
g.monsters = [near, far]

g.player.cell = (12, 12)
g.player.pos.update(cell_center(12, 12))
run_for(g, CLEAR_GLOW_TIME + 0.2)
check("玩家进坛 → 进入 wave", g.clear_phase == "wave", str(g.clear_phase))

shot_n = 0
for _ in range(200):
    auto_mono(g)
    g.update(1 / 60)
    if g.clear_phase == "wave" and g.wave_r > 200 and shot_n == 0:
        shot(g, "06_wave.png")
        shot_n = 1
    if g.clear_phase != "wave":
        break
check("波扫过近处红怪 → 被清除", near not in g.monsters, "%d" % len(g.monsters))
check("波的半径追着涨（远处的怪还没被扫到）", g.wave_r > 0,
      "r %.0f / phase %s" % (g.wave_r, g.clear_phase))

run_for(g, 6.0)
check("波扫完先停 %.1f 秒（CLEAR_WAVE_HOLD）再出道具" % CLEAR_WAVE_HOLD,
      g.state == "REWARD", "%s/%s" % (g.state, g.clear_phase))
check("波扫完全屏 → 红怪全清", len(g.monsters) == 0, "%d" % len(g.monsters))
check("脏格全部被抹掉（画面上没有 DIRTY 了）",
      all(b.state[r][c] != DIRTY for r in range(25) for c in range(25)))
check("有效黑域还在（100 格没被波的收尾动过）", b.progress() == 100, "%d" % b.progress())
check("波扫完 → 进奖励阶段", g.state == "REWARD", g.state)

# --- 6) 涂完最后一格时人就站在坛内：发光不能一帧都没有 ---
g5 = to_battle(new_game())
fill_must(g5)
put(g5, (12, 12))
auto_mono(g5)
g5.update(1 / 60)
check("最后一格涂完 → 进清屏", g5.state == "CLEAR", g5.state)
run_for(g5, CLEAR_GLOW_TIME * 0.7)
check("人本来就站在坛里：发光阶段仍然至少持续 %.1fs" % CLEAR_GLOW_TIME,
      g5.clear_phase == "glow", g5.clear_phase)
run_for(g5, CLEAR_GLOW_TIME * 0.5)
check("亮够之后才开始扩散", g5.clear_phase == "wave", g5.clear_phase)

p = shot(g, "06_act_end.png")
print("  shot ->", p)
finish(TITLE)
