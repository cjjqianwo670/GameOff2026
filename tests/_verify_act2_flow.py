# -*- coding: utf-8 -*-
"""第二幕 · 流程验收（第一幕 → 第二幕 → 紫怪 → 清屏 → 结束 / 阵亡回检查点）。

这一份测的是「串起来之后还对不对」，所以只用 game 的公开动作（start_act2 / update / handle_event），
不直接改内部状态；只有为了跳过长流程才手动摆位（put / fill）。
"""

import sys


import pygame  # noqa: E402

from _act1_common import auto_mono, check, finish, new_game, paint_ok, skip_intro, toast_text  # noqa: E402
from src import story  # noqa: E402
from src.config import (  # noqa: E402
    A2_OPEN_SECONDS, HEALTH_MAX, PURPLE_FIRST_DELAY, PURPLE_HIT_DAMAGE, PURPLE_SPAWN_PER_MIN,
    REWARD_DELAY, SC_ENTER, VALID, WHITE
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
check("第二幕开战：紫怪那句走飘字（不冻世界）", toast_text(g) == story.MONO_PURPLE_IN, repr(toast_text(g)))

# ==================== 3. 首只紫怪 = 8 秒 ====================
run(g, PURPLE_FIRST_DELAY - 1.2)
check("7 秒内没有紫怪（作者定 8 秒）", len(g.purples) == 0, "purple_t=%.1f" % g.purple_t)
run(g, 1.6)
check("8 秒后紫怪到场", len(g.purples) == 1, "purple_t=%.1f" % g.purple_t)
check("紫怪第一次来放 A2_M3", g.mono_last == story.A2_M3, repr(g.mono_last[:20]))

# ==================== 4. 清行：第一次独白 + 之后短嘀咕 ====================
g.purples.clear()
row_idx = 8
for c in range(25):
    g.board.state[row_idx][c] = 1          # 造一条满行，保证「行比列多」
g.wipe_warned = False
g.on_line_wiped("row", row_idx, 25)
check("第一次被清 → 一句嘀咕 A2_M4（飘字）", toast_text(g) == story.A2_M4, repr(toast_text(g)[:24]))
g.mono_text = ""
g.on_line_wiped("col", 4, 3)
check("之后再被清 → 不再弹心声（作者：每次都说会影响体验）",
      g.mono_text == "", repr(g.mono_text[:24]))
check("...但仍然有系统提示吗？没有（连 ROW n WIPED 也去掉了，只靠画面 + 音效）",
      g.hint_text == "", repr(g.hint_text[:24]))

# ==================== 5. 紫怪真的会清线（跑起来） ====================
g2 = new_game()
skip_intro(g2)
g2.start_act2()
run(g2, A2_OPEN_SECONDS + 0.2)
check("（准备）已进战斗", g2.state == "BATTLE", g2.state)
# 涂满 12 格让紫怪有得吃，并把紫怪直接放到那一格旁边
cells = sorted(g2.must)[:12]
for (r, c) in cells:
    g2.board.state[r][c] = 1
from src.entities import PurpleOne  # noqa: E402
target_cell = cells[0]
g2.purples = [PurpleOne(cell_center(*target_cell))]
before_total = sum(1 for r in range(25) for c in range(25) if g2.board.state[r][c] == 1)
run(g2, 2.5)
after_total = sum(1 for r in range(25) for c in range(25) if g2.board.state[r][c] == 1)
check("紫怪撞到后清掉了一整条（总黑格数下降）", after_total < before_total,
      "%d → %d" % (before_total, after_total))
check("紫怪清完自毁（场上没了）", len(g2.purples) == 0, "%d" % len(g2.purples))

# ==================== 6. 第二幕通关：106 格 → 清屏 ====================
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

# ==================== 10. 背包 / 地图：第一幕拿到，之后一直带着 ====================
# 这两件是第一幕的奖励。第二幕**不能再浮出来一次**，也不能在转场或回检查点时被收走。
g7 = new_game()
skip_intro(g7)
g7.has_bag = g7.has_map = True                    # 相当于第一幕已经捡完了
g7.start_act2()
check("进第二幕：背包还在", g7.has_bag)
check("进第二幕：地图还在", g7.has_map)

run(g7, A2_OPEN_SECONDS + 0.3)
check("第二幕战斗中道具仍带着", g7.has_bag and g7.has_map)

# 阵亡回检查点：道具不能丢
g7.health = 0
auto_mono(g7)
g7.update(1 / 60)
g7.handle_event(ev(SC_ENTER))
check("第二幕阵亡回检查点后：背包还在", g7.has_bag, "act=%d" % g7.act)
check("第二幕阵亡回检查点后：地图还在", g7.has_map)

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
check("第一幕照旧浮出 BAG + MAP 两件", len(g8.items) == 2, "%d 件" % len(g8.items))


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


# ==================== 9. 坛内没黑域 → 紫怪扑人，扣 10% 血（2026-11-12）====================
from src.entities import PurpleOne  # noqa: E402

g10 = new_game()
skip_intro(g10)
g10.start_act2()
g10.state = "BATTLE"
run(g10, A2_OPEN_SECONDS + 0.3)
for r in range(25):                                # 清空棋盘：坛内一格黑域都没有
    for c in range(25):
        g10.board.state[r][c] = WHITE
g10.monsters.clear()
g10.purples = [PurpleOne(cell_center(*g10.player.cell))]   # 直接贴到玩家身上
hp0 = g10.health
auto_mono(g10)
g10.update(1 / 60)
check("贴脸的紫怪 → 坛内没黑域时扑人成功", g10.health == hp0 - PURPLE_HIT_DAMAGE,
      "%d → %d" % (hp0, g10.health))
check("...扣的是 10%（不是红怪的 5%）", hp0 - g10.health == 10, "%d" % (hp0 - g10.health))
check("...撞完自己消失（一生一次）", len(g10.purples) == 0, "%d" % len(g10.purples))
check("...并且嘀咕一句（飘字）", toast_text(g10) == story.MONO_PURPLE_HIT, repr(toast_text(g10)))

# 有黑域时不会扑人（仍然清行，血量不动）
g11 = new_game()
skip_intro(g11)
g11.start_act2()
g11.state = "BATTLE"
run(g11, A2_OPEN_SECONDS + 0.3)
g11.monsters.clear()
mr, mc = sorted(g11.board.must)[0]
g11.board.state[mr][mc] = VALID
g11.purples = [PurpleOne(cell_center(mr, mc))]
hp1 = g11.health
run(g11, 1.0)
check("坛内有黑域时紫怪不会扑人（血量不变）", g11.health == hp1, "%d → %d" % (hp1, g11.health))


finish("第二幕 · 流程")
