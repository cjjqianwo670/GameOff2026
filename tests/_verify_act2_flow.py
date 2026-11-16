# -*- coding: utf-8 -*-
"""第二幕 · 流程验收（第一幕 → 第二幕 → 清屏 → 结束 / 阵亡回检查点）。

这一份测的是「串起来之后还对不对」，所以只用 game 的公开动作（start_act2 / update / handle_event），
不直接改内部状态；只有为了跳过长流程才手动摆位（put / fill）。

2026-11-16：紫怪从第二幕延后到第四幕，所以这一幕**不刷紫怪**（只红怪咬核心→分离）。
紫怪的清线行为由 `_verify_act2_purple.py`（纯单元）和 `_verify_act4_flow.py` 覆盖。
"""

import sys


import pygame  # noqa: E402

from _act1_common import auto_mono, check, finish, new_game, paint_ok, skip_intro, toast_text  # noqa: E402
from src import story  # noqa: E402
from src.config import (  # noqa: E402
    A2_OPEN_SECONDS, GREEN_FIRST_DELAY, HEALTH_MAX, PURPLE_FIRST_DELAY, REWARD_DELAY,
    SC_ENTER, VALID, WHITE
)
from src.grid import cell_center  # noqa: E402


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


def paint_all_must(g):
    for (r, c) in sorted(g.must):
        g.board.state[r][c] = 1        # 直接设 VALID，跳过 paint 的必涂判定
    return len(g.must)


# ==================== 1. 第一幕 → 第二幕：棋盘不清空 ====================
g = new_game()
skip_intro(g)
g.enter_tutorial()
g.enter_free_roam()
g.start_gap()
run(g, 10.2)                                  # 空档结束 → 战斗
check("第一幕进入战斗", g.state == "BATTLE" and g.act == 1, "%s act=%d" % (g.state, g.act))

# 涂一部分第一幕必涂格（模拟玩家进度）
first_20 = sorted(g.must)[:20]
for (r, c) in first_20:
    g.board.state[r][c] = 1
board_id = id(g.board)

g.start_act2()
check("切到第二幕", g.act == 2, "act=%d" % g.act)
check("棋盘对象没被换掉（不清空）", id(g.board) == board_id)
check("第二幕必涂 = 106", len(g.must) == 106, "%d" % len(g.must))
check("board.must 也换成了 106", len(g.board.must) == 106, "%d" % len(g.board.must))
check("第一幕涂的 20 格原地保留",
      all(g.board.state[r][c] == 1 for (r, c) in first_20))
check("进度只算已有的 20 格", g.board.progress() == 20, "%d" % g.board.progress())
check("血量回满", g.health == HEALTH_MAX, "%d" % g.health)
check("进了第二幕开场相位", g.state == "A2_OPEN", g.state)
check("开场放 A2_M1", g.mono_text == story.A2_M1, repr(g.mono_text[:24]))
check("第二幕检查点已打", g.checkpoint is not None and g.checkpoint.get("act") == 2)
check("检查点记的相位 = A2_OPEN", g.checkpoint.get("state") == "A2_OPEN")
check("第一幕的怪/紫怪都清空", not g.monsters and not g.purples)

# ==================== 2. 开场 → 战斗 ====================
run(g, A2_OPEN_SECONDS * 0.6)
check("开场没到时不进战斗", g.state == "A2_OPEN", g.state)
run(g, A2_OPEN_SECONDS * 0.6)
check("开场结束自动进战斗", g.state == "BATTLE", g.state)

# ==================== 3. 第二幕不刷紫怪（2026-11-16 延后到第四幕）====================
# 跑满「原首只紫怪 8 秒 + 一个生成间隔」的时间，场上应该一只紫怪都没有。
run(g, PURPLE_FIRST_DELAY + 11.0)
check("第二幕跑满 19 秒也**没有紫怪**（紫怪延后到第四幕）", len(g.purples) == 0, "%d 只" % len(g.purples))
check("第二幕开战不喊紫怪心声（MONO_PURPLE_IN 已撤）",
      toast_text(g) != story.MONO_PURPLE_IN, repr(toast_text(g)[:24]))

# ==================== 3b. 第二幕低频刷绿怪（首只 12 秒）====================
g_green = new_game()
skip_intro(g_green)
g_green.start_act2()
g_green.state = "BATTLE"
g_green.spawn_rate = 0.0            # 关掉红怪，只看绿怪
g_green.monsters.clear()
run(g_green, GREEN_FIRST_DELAY - 1.0)
check("第二幕 11 秒内没有绿怪（首只 12 秒）", len(g_green.greens) == 0, "%d 只" % len(g_green.greens))
run(g_green, 2.0)
check("12 秒后第一只绿怪到场", len(g_green.greens) == 1, "%d 只" % len(g_green.greens))
check("绿怪第一次进场放 A2_GREEN", g_green.mono_last == story.A2_GREEN,
      repr(g_green.mono_last[:24]) if g_green.mono_last else "None")

# ==================== 4. 第二幕通关：106 格 → 清屏 ====================
g3 = new_game()
skip_intro(g3)
g3.start_act2()
run(g3, A2_OPEN_SECONDS + 0.2)
paint_all_must(g3)
auto_mono(g3)
g3.update(1 / 60)
check("106 格全黑 → 进清屏", g3.state == "CLEAR", "%s/%s" % (g3.state, g3.clear_phase))
check("清屏时紫怪被收掉", not g3.purples)

# ==================== 7. 幕结束字幕 + 转场 ====================
g4 = new_game()
skip_intro(g4)
g4.start_act2()
g4.act = 2
g4.show_banner(story.act_title(g4.act), 999.0)
check("第二幕结束字幕 = ACT 2 — END", g4.banner_text == story.ACT2_TITLE, repr(g4.banner_text))
check("act_title(1) 仍是 ACT 1 — END", story.act_title(1) == story.ACT_TITLE, story.act_title(1))

# 第一幕 END 按回车 → 进第二幕
g5 = new_game()
skip_intro(g5)
g5.state = "END"
g5.act = 1
g5.handle_event(ev(SC_ENTER))
check("第一幕结束按回车 → 第二幕", g5.act == 2 and g5.state == "A2_OPEN",
      "act=%d state=%s" % (g5.act, g5.state))

# 第二幕 END 按回车 → 第三幕（2026-11-12 起有三幕了；回标题要等第三幕之后）
g5.state = "END"
g5.has_sword = True                        # 假装剑已经捡了，别让第三幕的检查点断言受影响
g5.handle_event(ev(SC_ENTER))
check("第二幕结束按回车 → 第三幕（开场就是老者回来那段对话）",
      g5.act == 3 and g5.state == "DIALOG", "act=%d state=%s" % (g5.act, g5.state))

# ==================== 8. 阵亡 → 回第二幕检查点 ====================
g6 = new_game()
skip_intro(g6)
g6.start_act2()
run(g6, A2_OPEN_SECONDS + 0.5)
check("（准备）第二幕战斗中", g6.state == "BATTLE", g6.state)
g6.health = 0
auto_mono(g6)
g6.update(1 / 60)
check("血量归零 → DEAD", g6.state == "DEAD", g6.state)
g6.handle_event(ev(SC_ENTER))
check("阵亡后回第二幕检查点", g6.act == 2 and g6.state == "A2_OPEN",
      "act=%d state=%s" % (g6.act, g6.state))
check("回来时必涂格仍是 106", len(g6.must) == 106, "%d" % len(g6.must))
check("回来时紫怪清空", not g6.purples, "%d" % len(g6.purples))
check("回来时血量满", g6.health == HEALTH_MAX, "%d" % g6.health)

# ==================== 9. 第二幕没有红怪以外的对话（文案层） ====================
check("第二幕没有对话常量（story 里没有 A2_DIALOG）", not hasattr(story, "A2_DIALOG"))
check("紫怪零台词（story 里没有 PURPLE_TALK）", not hasattr(story, "PURPLE_TALK"))

# ==================== 10. 背包：第一幕拿到，之后一直带着（地图已删 2026-11-14）====================
g7 = new_game()
skip_intro(g7)
g7.has_bag = True                                # 相当于第一幕已经捡完了
g7.start_act2()
check("进第二幕：背包还在", g7.has_bag)

run(g7, A2_OPEN_SECONDS + 0.3)
check("第二幕战斗中道具仍带着", g7.has_bag)

# 阵亡回检查点：道具不能丢
g7.health = 0
auto_mono(g7)
g7.update(1 / 60)
g7.handle_event(ev(SC_ENTER))
check("第二幕阵亡回检查点后：背包还在", g7.has_bag, "act=%d" % g7.act)

# 清屏 → 奖励阶段：第二幕不该浮出 BAG / MAP（回检查点后在 A2_OPEN，先走完开场）
run(g7, A2_OPEN_SECONDS + 0.3)
check("（准备）回到第二幕战斗", g7.state == "BATTLE", g7.state)
for (r, c) in sorted(g7.must):
    g7.board.state[r][c] = 1
auto_mono(g7)
g7.update(1 / 60)
check("（准备）第二幕涂满 → 进清屏", g7.state == "CLEAR", g7.state)
run(g7, 6.0)                                       # 发光 + 圆波 + 停顿
check("涂满后走到奖励阶段", g7.state == "REWARD", "%s/%s" % (g7.state, g7.reward_phase))
run(g7, REWARD_DELAY + 0.3)
check("第二幕收尾浮出**一件**道具", len(g7.items) == 1, "%d 件" % len(g7.items))
check("...而且掉的是剑（第三幕打黄怪用）", g7.items[0].kind == "sword",
      g7.items[0].kind if g7.items else "无")
check("第二幕的道具阶段等玩家来捡（不再直接跳过）", g7.reward_phase == "items", g7.reward_phase)

# 第一幕仍然发（别把第一幕也一起关了）
g8 = new_game()
skip_intro(g8)
g8.start_act2()
g8.act = 1                                         # 只借它的棋盘，按第一幕处理
for (r, c) in sorted(g8.must)[:12]:                # 道具要落在已复原的黑格上，先造几格
    g8.board.state[r][c] = 1
g8.enter_reward()
run(g8, REWARD_DELAY + 0.3)
check("第一幕照旧浮出 BAG 一件（地图已删）", len(g8.items) == 1 and g8.items[0].kind == "bag",
      "%d 件 / %s" % (len(g8.items), [i.kind for i in g8.items]))


# ==================== 8. 作者报的 bug：紫怪清掉定位图案后，不照就能补涂 ====================
# 2026-11-12 定稿规则：圣坛内**灰域还亮着**才写得对；被紫怪清掉的格子记忆作废，必须重新 Shift。
g9 = new_game()
skip_intro(g9)
g9.start_act2()
g9.state = "BATTLE"
mr, mc = sorted(g9.board.must)[0]
paint_ok(g9, mr, mc)                              # 第一幕就涂好的一格（先照再涂）
check("（准备）这一格是有效黑域", g9.board.state[mr][mc] == VALID, "%d" % g9.board.state[mr][mc])

# 定位图案是「早就涂好的」，那时候的灰域早就褪了（5 秒）—— 玩家遇到的就是这个状态
for _r in range(25):
    for _c in range(25):
        g9.board.reveal[_r][_c] = 0.0

wiped = g9.board.clear_row(mr, kind="purple")     # 紫怪把整行抹白（这就是作者遇到的场景）
check("紫怪把这一行清回白（含刚涂的那格）", g9.board.state[mr][mc] == WHITE and wiped >= 1,
      "wiped %d / state %d" % (wiped, g9.board.state[mr][mc]))

res = g9.board.paint(mr, mc)                      # 不按 Shift，直接补
check("不重新照就补涂 → 脏格（bug 已修）", res == "dirty", "%s" % res)
g9.board.state[mr][mc] = WHITE
g9.board.stains -= 1                              # 把这次试探的账抹掉，别影响后面的断言

paint_ok(g9, mr, mc)                              # 重新照一下再补
check("重新照之后补回来 → 有效黑域", g9.board.state[mr][mc] == VALID, "%d" % g9.board.state[mr][mc])
check("进度跟着回来", g9.board.progress() >= 1, "%d" % g9.board.progress())


finish("第二幕 · 流程")
