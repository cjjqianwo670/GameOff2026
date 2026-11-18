# -*- coding: utf-8 -*-
"""道具验收（2026-11-16 作者定：每幕一个新，固定字母键）。

投放：第二幕时停(E) · 第三幕冲刺(Q) · 第四幕诱饵(F) · 第五幕修复卷轴(G)。
常驻能力进幕自动解锁；一次性消耗品每幕补 1，用完即空。
"""

import pygame

from _act1_common import auto_mono, check, finish, new_game, paint_ok, skip_intro
from src import story
from src.config import (
    DASH_DIST, DECOY_HP, DECOY_LIFE, DECOY_CD, SC_E, SC_F, SC_G, SC_Q, TIME_SLOW_CD, TIME_SLOW_DURATION,
    TIME_SLOW_FACTOR, VALID, WHITE
)
from src.entities import Decoy, Monster
from src.grid import cell_center


def ev(sc):
    return pygame.event.Event(pygame.KEYDOWN, key=0, scancode=sc)


def run(g, secs):
    for _ in range(max(1, int(secs * 60))):
        auto_mono(g)
        g.update(1 / 60)


def put(g, cell):
    g.player.cell = cell
    g.player.pos.update(cell_center(*cell))


# ==================== 1. 每幕解锁一个道具 ====================
g = new_game()
skip_intro(g)
g.start_act2()
check("第二幕：时停解锁、冲刺/诱饵/卷轴未解锁",
      g.has_time_slow and not g.has_dash and not g.has_decoy and g.scroll_count == 0)

g3 = new_game()
for (r, c) in sorted(g3.board.must):
    paint_ok(g3, r, c)
g3.start_act2()
for (r, c) in sorted(g3.must):
    if g3.board.state[r][c] != VALID:
        paint_ok(g3, r, c)
g3.start_act3()
check("第三幕：冲刺解锁", g3.has_dash and g3.has_time_slow)

g4 = new_game()
for (r, c) in sorted(g4.board.must):
    paint_ok(g4, r, c)
g4.start_act2()
for (r, c) in sorted(g4.must):
    if g4.board.state[r][c] != VALID:
        paint_ok(g4, r, c)
g4.start_act3()
for (r, c) in sorted(g4.must):
    if g4.board.state[r][c] != VALID:
        paint_ok(g4, r, c)
g4.start_act4()
check("第四幕：诱饵解锁", g4.has_decoy and g4.scroll_count == 0)

g5 = new_game()
for (r, c) in sorted(g5.board.must):
    paint_ok(g5, r, c)
g5.start_act2()
for (r, c) in sorted(g5.must):
    if g5.board.state[r][c] != VALID:
        paint_ok(g5, r, c)
g5.start_act3()
for (r, c) in sorted(g5.must):
    if g5.board.state[r][c] != VALID:
        paint_ok(g5, r, c)
g5.start_act4()
for (r, c) in sorted(g5.must):
    if g5.board.state[r][c] != VALID:
        paint_ok(g5, r, c)
g5.start_act5()
check("第五幕：修复卷轴补 1 个", g5.scroll_count == 1)

# ==================== 2. 时停 ====================
g2 = new_game()
skip_intro(g2)
g2.start_act2()
g2.state = "BATTLE"
g2.mono_hold = False           # 关掉 A2_M1 独白，别挡按键
g2.time_slow_t = 0.0
g2.time_slow_cd = 0.0
g2.handle_event(ev(SC_E))
check("按 E 触发时停（进入减速）", g2.time_slow_t > 0, "%.2f" % g2.time_slow_t)
check("时停冷却开始走", g2.time_slow_cd == TIME_SLOW_CD, "%.1f" % g2.time_slow_cd)
run(g2, 0.5)
# 时停生效期间，怪物 dt 会被乘 TIME_SLOW_FACTOR —— 验证系数正确
check("时停时长 = 3 秒", TIME_SLOW_DURATION == 3.0)
check("减速系数 = 0.3", TIME_SLOW_FACTOR == 0.3)
# 冷却期不能再触发
g2.time_slow_t = 0.0
g2.time_slow_cd = 5.0
g2.handle_event(ev(SC_E))
check("冷却期内按 E 不生效", g2.time_slow_t == 0.0)

# ==================== 3. 冲刺 ====================
g3b = new_game()
skip_intro(g3b)
g3b.start_act2()
g3b.start_act3()          # 第三幕解锁冲刺（前两幕涂满会清屏，这里直接进）
g3b.state = "BATTLE"
g3b.dash_cd = 0.0
g3b.player.facing = 3       # 朝右
g3b.player.cell = (12, 5)
g3b.player.pos.update(cell_center(12, 5))
before = g3b.player.cell
g3b.handle_event(ev(SC_Q))
check("按 Q 冲刺：向右瞬移 %d 格" % DASH_DIST,
      g3b.player.cell == (12, 5 + DASH_DIST), str(g3b.player.cell))
check("冲刺有冷却", g3b.dash_cd > 0)

# 撞墙/撞缝停在原地
g3c = new_game()
skip_intro(g3c)
g3c.start_act2()
g3c.start_act3()
g3c.state = "BATTLE"
g3c.dash_cd = 0.0
g3c.player.facing = 0       # 朝上
g3c.player.cell = (2, 12)   # 圣坛最上沿，往上就是坛外（不能站）
g3c.player.pos.update(cell_center(2, 12))
g3c.handle_event(ev(SC_Q))
check("冲刺撞到不能站的地方 → 原地不动", g3c.player.cell == (2, 12), str(g3c.player.cell))

# ==================== 4. 诱饵 ====================
g4b = new_game()
skip_intro(g4b)
g4b.start_act2()
g4b.start_act3()
g4b.start_act4()
g4b.state = "BATTLE"
g4b.mono_hold = False          # 关掉 A4_M1 独白
# 找个坛内白格
cell = next((r, c) for r in range(2, 23) for c in range(2, 23)
            if g4b.board.state[r][c] == WHITE and g4b.board.in_altar(r, c))
put(g4b, cell)
g4b.handle_event(ev(SC_F))
check("按 F 在脚下放假黑域", g4b.board.state[cell[0]][cell[1]] == VALID, "%d" % g4b.board.state[cell[0]][cell[1]])
check("诱饵进入冷却", g4b.decoy_cd > 0, "%.1f" % g4b.decoy_cd)
check("诱饵进了清单", len(g4b.decoys) == 1, "%d" % len(g4b.decoys))
# 到期自动消失
run(g4b, DECOY_LIFE + 0.2)
check("诱饵到期自动消失（变回白）", g4b.board.state[cell[0]][cell[1]] == WHITE,
      "%d" % g4b.board.state[cell[0]][cell[1]])
check("诱饵清单清空", len(g4b.decoys) == 0, "%d" % len(g4b.decoys))

# ==================== 4b. 诱饵血量 + 吸引怪物（2026-11-16 升级）====================
g4d = new_game()
skip_intro(g4d)
g4d.start_act2()
g4d.start_act3()
g4d.start_act4()
g4d.state = "BATTLE"
g4d.mono_hold = False
cell3 = next((r, c) for r in range(2, 23) for c in range(2, 23)
             if g4d.board.state[r][c] == WHITE and g4d.board.in_altar(r, c))
put(g4d, cell3)
g4d.handle_event(ev(SC_F))
dc = g4d.decoys[0]
check("诱饵有血量（DECOY_HP）", dc.hp == DECOY_HP and dc.max_hp == DECOY_HP,
      "%d/%d" % (dc.hp, dc.max_hp))

# 红怪优先锁诱饵：场上放一格更近的黑域，红怪仍锁诱饵（强吸引）
near_dark = (cell3[0], cell3[1] + 2)          # 诱饵旁边一格也放黑域
g4d.board.state[near_dark[0]][near_dark[1]] = VALID
m = Monster((g4d.player.pos.x + 5, g4d.player.pos.y + 5), 62.0)   # 贴玩家站，离诱饵更远
# 把红怪放到诱饵附近，让它 retarget 时能看到诱饵和 near_dark 两个黑域
m.pos.update(cell_center(*near_dark))          # 站到 near_dark 上，离 near_dark 最近
m.retarget(g4d.board, g4d.claims, g4d.decoys)
check("有诱饵时红怪优先锁诱饵（哪怕旁边有更近的黑域）", m.target == cell3, str(m.target))

# 红怪咬诱饵 → 扣血，不把诱饵格清掉
m2 = Monster(cell_center(*cell3), 62.0)        # 直接站到诱饵上
m2.retarget(g4d.board, g4d.claims, g4d.decoys)
res = m2.update(1/60, g4d.board, g4d.claims, g4d.player, g4d.decoys)
check("红怪咬诱饵 → 返回 decoy", isinstance(res, tuple) and res[0] == "decoy", repr(res))
check("诱饵扣 1 血", dc.hp == DECOY_HP - 1, "%d" % dc.hp)
check("诱饵格子还是黑域（没被吃掉）", g4d.board.state[cell3[0]][cell3[1]] == VALID,
      "%d" % g4d.board.state[cell3[0]][cell3[1]])

# 血量耗尽才消失：把 hp 打到 0，update_decoys 清掉
dc.hp = 0
dc.dead = True
g4d.update_decoys(1/60)
check("诱饵血量耗尽 → 格子变白、实体摘掉",
      g4d.board.state[cell3[0]][cell3[1]] == WHITE and len(g4d.decoys) == 0,
      "%d / %d" % (g4d.board.state[cell3[0]][cell3[1]], len(g4d.decoys)))

# 冷却中不能再放
g4c = new_game()
skip_intro(g4c)
g4c.start_act2()
g4c.start_act3()
g4c.start_act4()
g4c.state = "BATTLE"
g4c.mono_hold = False
g4c.decoy_cd = 5.0              # 模拟冷却中
cell2 = next((r, c) for r in range(2, 23) for c in range(2, 23)
             if g4c.board.state[r][c] == WHITE and g4c.board.in_altar(r, c))
put(g4c, cell2)
g4c.handle_event(ev(SC_F))
check("冷却中按 F 不放", g4c.board.state[cell2[0]][cell2[1]] == WHITE)

# ==================== 5. 修复卷轴 ====================
g5b = new_game()
skip_intro(g5b)
g5b.start_act2()
g5b.start_act3()
g5b.start_act4()
g5b.start_act5()
g5b.state = "BATTLE"
g5b.mono_hold = False          # 关掉 A5_M1 独白
g5b.scroll_count = 1
g5b.board.detach_board("TL")
check("（准备）TL 已分离", "TL" in g5b.board.detached)
g5b.handle_event(ev(SC_G))
check("按 G 拉回分离板块", "TL" not in g5b.board.detached, str(g5b.board.detached))
check("卷轴计数 -1", g5b.scroll_count == 0, "%d" % g5b.scroll_count)

# 没分离时按 G 不消耗
g5c = new_game()
skip_intro(g5c)
g5c.start_act2()
g5c.start_act3()
g5c.start_act4()
g5c.start_act5()
g5c.state = "BATTLE"
g5c.mono_hold = False
g5c.scroll_count = 1
g5c.handle_event(ev(SC_G))
check("没分离板块时按 G 不消耗", g5c.scroll_count == 1, "%d" % g5c.scroll_count)

finish("道具")
