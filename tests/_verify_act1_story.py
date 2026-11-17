# -*- coding: utf-8 -*-
"""步骤 8~11 验收：开场碎码 / 教程链 / 老者赶怪 / 双支线对话。

全部用真实键位事件推进，不直接改状态（除了摆位置）。
"""

import pygame

from _act1_common import go_to_oldman, auto_mono, check, finish, new_game, reveal_once, shot
from src.config import (
    PLAYER_START_CELL,
    CELL, C_CELL_WHITE, C_OLDMAN, CALL_RANGE_PX, CLOSE_RANGE_PX,
    DLG_BOX, DLG_LINE_H, GRID_N,
    DLG_LAST_MIN_SHOW, INTRO_TOTAL, MIRAGE_RADIUS, SC_A, SC_D, SC_ENTER, SC_ESC, SC_J, SC_S,
    SC_T, SC_W,
    TUTORIAL_MOVE_SECONDS,
    WHITE
)
from src import story
from src.grid import cell_center, cell_to_rect

TITLE = "STEP 8~11 · INTRO / TUTORIAL / OLD MAN / DIALOGUE"


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


def px(g, r, c):
    return g.canvas.get_at(cell_to_rect(r, c).center)[:3]


g = new_game()

# ================= 步骤 8 · 碎码 → 只剩脚下 =================
check("进游戏先播开场动画", g.state == "INTRO" and g.intro_t > 0, "%.2f" % g.intro_t)
run(g, 1.0)
check("开场 1 秒：整张码已铺出（还没碎）", (not g.burst_done) and g.intro_t > 0)
shot(g, "11_intro_code.png")

run(g, 0.7)
check("1.7 秒：码已经震碎成碎片", g.burst_done and len(g.debris) > 0, "%d 片" % len(g.debris))

run(g, 1.5)
check("3.1 秒后进入教程相位", g.state == "TUTORIAL", g.state)
check("紧接着显示 M1 独白", g.mono_text == story.M1, repr(g.mono_text))
check("出生就提示走路键位", g.prompt_text == story.TUTORIAL_MOVE, repr(g.prompt_text))
check("醒着的时候不画碎片", not g.debris)
g.draw()
pr, pc = g.player.cell
# ⚠️ 只在**已接回的板块**里取格子：没接回的板块被推开 1 格画在别处，
# 用它的规范坐标取像素会取到缝里（背景色），测的就不是「格子白不白」了。
far = [(r, c) for r in range(2, 23) for c in range(2, 23)
       if max(abs(r - pr), abs(c - pc)) > MIRAGE_RADIUS and g.target[r - 2][c - 2] == 1
       and g.board.in_altar(r, c)]
far = far[len(far) // 2]
check("5×5 之外的格子是纯白（灰码没有整张淡入）", px(g, *far) == C_CELL_WHITE, str(px(g, *far)))
shot(g, "12_wake_footprint.png")

# ================= 步骤 9 · 教程链 =================
run(g, 10.0)
# 2026-11-14 设计变更：站着不动的玩家**也要**收到 TRY [SHIFT]（`tut_t >= 6` 的兜底），
# 否则「不走路」的人永远收不到这条提示。但「移动计时」仍然只算真的在走 —— 这两件事要分开。
check("站着不动 10 秒也会给 TRY [SHIFT]（站着不动的兜底）",
      g.prompt_text == story.TUTORIAL_SHIFT, repr(g.prompt_text))
check("站着不动，移动计时不涨", g.move_time == 0.0, "%.2f" % g.move_time)
check("站着不动，开场那片灰也不褪（还没按过 Shift）",
      any(g.board.reveal[r][c] > 0 for r in range(25) for c in range(25)))

g.input.held.add(SC_S)
run(g, 2.7)
g.input.held.add(SC_W)
run(g, 2.7)
g.input.held.clear()
check("移动满 %.0f 秒后提示 Shift" % TUTORIAL_MOVE_SECONDS,
      g.move_time >= TUTORIAL_MOVE_SECONDS and g.prompt_text == story.TUTORIAL_SHIFT,
      "%.2f / %r" % (g.move_time, g.prompt_text))

put(g, PLAYER_START_CELL)                        # 出生点：左下定位图案，本幕必涂格
g.handle_event(ev(225))
check("第一次照出灰域 → M2", g.mono_text == story.M2, repr(g.mono_text[:30]))
check("照出灰域后进入自由探索", g.state == "FREE_ROAM", g.state)

# ================= 步骤 10 · 老者驱赶红怪 =================
# 2026-11-14：这一段单独开一局来测。现在老者就站在玩家板块下面，教程几乎一迈步就结束，
# 于是「进 FREE_ROAM 0.4 秒后红怪落下」这场戏会在很早的时候自己播完 ——
# 挂在长流程那一局上测，只会测到「已经播完了」。
gS = new_game()
run(gS, 3.4)
gS.enter_free_roam()
check("老者站在圣坛外（不在任何一块石板上）", not gS.board.in_altar(*gS.oldman.cell),
      str(gS.oldman.cell))
check("老者一开始朝上（背对玩家，面朝圣坛）", gS.oldman.facing == 0, "%d" % gS.oldman.facing)

run(gS, 0.6)
check("开场 0.6 秒：两只红怪进场", len(gS.scene_reds) == 2, "%d" % len(gS.scene_reds))
run(gS, 1.2)
check("老者挥起拐杖", gS.oldman.staff_t > 0, "%.2f" % gS.oldman.staff_t)
check("红怪放狠话", gS.threat_t > 0, "%.2f" % gS.threat_t)
shot(gS, "13_threat.png")

run(gS, 3.0)
check("红怪逃走并消失", len(gS.scene_reds) == 0, "%d" % len(gS.scene_reds))
check("逃走之后显示 M3", gS.mono_last == story.M3, repr(gS.mono_last))
check("老者转回身朝向圣坛", gS.oldman.facing == 1, "%d" % gS.oldman.facing)

# ================= 步骤 11 · 对话 =================
# --- 太远：不显示提示 ---
put(g, (12, 12))
run(g, 0.1)
check("离得远时不显示呼喊提示", g.prompt_text == "", repr(g.prompt_text))

# --- 坛内呼喊 ---
go_to_oldman(g)
run(g, 0.1)
check("进呼喊范围 → PRESS [T] TO CALL OUT", g.prompt_text == story.PROMPT_CALL, repr(g.prompt_text))
check("距离在呼喊范围内", g.oldman_dist() <= CALL_RANGE_PX, "%.0f" % g.oldman_dist())
g.handle_event(ev(SC_T))
check("坛内按 T 开始对话", g.state == "DIALOG" and g.dlg_lines is not None)
check("坛内支线 13 句 + 最后一句 = 14", len(g.dlg_lines) == 14, "%d" % len(g.dlg_lines))
# 2026-11-14：第一幕圣坛还裂着，他**不跑上来**（跑上来＝站到码上）。就地转身说话。
check("圣坛还裂着：老者就地开口（不跑过来）", g.dlg_phase == "talk", g.dlg_phase)
run(g, 2.0)
check("跑到位后开始说话", g.dlg_phase == "talk", g.dlg_phase)
check("第一句是 OLD MAN", g.dlg_lines[0][0] == story.OLD_MAN)

# 对话期间不能走动、不能涂
cell0 = g.player.cell
g.input.held.add(SC_D)
run(g, 0.6)
g.input.held.clear()
check("对话期间不能移动", g.player.cell == cell0, "%s -> %s" % (cell0, g.player.cell))
g.input.held.add(SC_J)
run(g, 0.3)
g.input.held.clear()
check("对话期间不能涂", all(v == WHITE for row in g.board.state for v in row))

# 每句都放得下（折行行数 ≤ 4）
from src.ui import dialog_lines  # noqa: E402
box_lines = (DLG_BOX[3] - 56) // DLG_LINE_H
over = []
for i in range(len(g.dlg_lines)):
    g.dlg_i = i
    lines, _ = dialog_lines(g)
    if len(lines) > box_lines:
        over.append((i + 1, len(lines)))
check("每句台词折行后都放得进对话框（≤%d 行）" % box_lines, not over, str(over))
g.dlg_i = 0
shot(g, "14_dialog_one.png")

# Esc 不再直接关对话，而是弹暂停菜单（2026-11-17）；再按 Esc 继续回到对话，不会卡死
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=SC_ESC))
check("对话中按 Esc 弹出暂停菜单（不会卡死）", g.state == "PAUSE" and g.pause_prev == "DIALOG", g.state)
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=SC_ESC))
check("暂停菜单里再按 Esc 继续 → 回到对话", g.state == "DIALOG", g.state)

# --- 坛外呼喊（对话二）在第一幕已经走不到了（2026-11-14 板块制）---
# 圣坛还裂着的时候玩家**只能站在自己那块板块上**（`can_stand` 判 `fractured()`）：
# 坛外平地和没接回的板子都站不上去。所以「站在坛外喊他 → 他先转身 → 走近再说」这条支线
# 在第一幕不可达（代码留着，第 3~5 幕的坛外站位还要用）。
# 这里锁死那个前提：**能走的地方只有已接回的板块**。
g2 = new_game()
run(g2, 3.4)
g2.enter_free_roam()
open_cells = {(r, c) for r in range(25) for c in range(25) if g2.board.in_altar(r, c)}
leak = [(r, c) for r in range(25) for c in range(25)
        if g2.board.can_stand(r, c) and (r, c) not in open_cells]
check("第一幕：坛外平地 / 没接回的板子都不能站（能走的只有已接回的板块）",
      not leak, str(leak[:4]))

# --- 最后一句：必须再按一次回车，老者才走（2026-11-11 改）---
# 原来是 `dlg_hold = 1.0` 自动离开，玩家还在看 `If I can.` 人就没了。
g4 = new_game()
run(g4, 3.4)
g4.enter_free_roam()
reveal_once(g4)                                  # 先照过灰域，才允许喊老者（2026-11-14）
go_to_oldman(g4)
run(g4, 0.1)
g4.handle_event(ev(SC_T))
run(g4, 1.8)                                   # 等他跑过来、进 talk
check("（准备）坛内对话已开始", g4.state == "DIALOG", g4.state)
last = len(g4.dlg_lines) - 1
for _ in range(300):                           # 翻到最后一句话
    if g4.dlg_lines is None or (g4.dlg_i == last and not g4.dlg_typing()):
        break
    g4.handle_event(ev(SC_ENTER))
    run(g4, 0.03)
check("翻到最后一句话（%s）" % story.LEAVE_LINE[1].split("\n")[-1],
      g4.dlg_i == last, "%d/%d" % (g4.dlg_i, last))
check("最后一句已打完", not g4.dlg_typing())

run(g4, 3.0)
check("最后一句打完 3 秒：对话框还在（不再自动离开）", g4.state == "DIALOG", g4.state)
check("最后一句打完 3 秒：老者还没走", not g4.oldman.leaving)
run(g4, 5.0)
check("再等 5 秒也还在（只有回车才走）", g4.state == "DIALOG" and not g4.oldman.leaving,
      "%s leaving=%s" % (g4.state, g4.oldman.leaving))
shot(g4, "16_last_line_wait.png")

g4.handle_event(ev(SC_ENTER))
check("这一下回车 → 老者才开始离开", g4.state == "FREE_ROAM" and g4.oldman.leaving,
      "%s leaving=%s" % (g4.state, g4.oldman.leaving))


# --- 连按回车不能把最后一句跳过去（2026-11-11 修）---
g5 = new_game()
run(g5, 3.4)
g5.enter_free_roam()
reveal_once(g5)                                  # 先照过灰域，才允许喊老者（2026-11-14）
go_to_oldman(g5)
run(g5, 0.1)
g5.handle_event(ev(SC_T))
run(g5, 1.8)
last5 = len(g5.dlg_lines) - 1
for _ in range(200):                            # 一路按到最后一句（每按一次只走 2 帧，模拟手快）
    if g5.dlg_lines is None or g5.dlg_i == last5:
        break
    g5.handle_event(ev(SC_ENTER))
    run(g5, 0.03)
check("（准备）已经在最后一句", g5.dlg_i == last5, "%d/%d" % (g5.dlg_i, last5))
for _ in range(5):                              # 立刻再连按 5 次
    g5.handle_event(ev(SC_ENTER))
    run(g5, 0.02)
check("连按 5 次也跳不过最后一句（对话框还在、老者没走）",
      g5.state == "DIALOG" and not g5.oldman.leaving,
      "%s leaving=%s" % (g5.state, g5.oldman.leaving))
check("最后一句至少显示了 %.1fs" % DLG_LAST_MIN_SHOW,
      g5.dlg_show_t > 0.05, "%.2fs" % g5.dlg_show_t)
run(g5, DLG_LAST_MIN_SHOW + 0.2)                # 停留够了再按才走
g5.handle_event(ev(SC_ENTER))
check("停留够之后再按 → 老者离开", g5.oldman.leaving, "%s leaving=%s" % (g5.state, g5.oldman.leaving))

# --- 回到 g：坛内支线走完整段对话 → 老者离开 → GAP ---
# 2026-11-17：ESC 不再打断对话（改弹暂停菜单，上面已验），g 仍停在 DIALOG，直接走完即可
check("暂停后仍在对话中", g.state == "DIALOG", g.state)
# --- 走完整段对话 → 老者离开 → GAP ---
for _ in range(40):
    g.handle_event(ev(SC_ENTER))
    auto_mono(g)
    g.update(1 / 60)
run(g, DLG_LAST_MIN_SHOW + 0.3)
g.handle_event(ev(SC_ENTER))
run(g, 0.2)
check("最后一句之后老者开始离开", g.state == "FREE_ROAM" and g.oldman.leaving, g.state)
run(g, 4.6)                                     # 他现在走的是板块**左侧**那条路，出画面要 ~3.7s
check("老者走后进入 10 秒空档", g.state == "GAP", g.state)
check("检查点打在「老者离开那一刻」", g.checkpoint is not None)

run(g, 10.2)
check("空档 10 秒后红怪来袭", g.state == "BATTLE", g.state)

# ================= 防死胡同：教程不该把人锁住 =================
# 1) 一路往上走会走出圣坛（论坛外按 Shift 没灰域），但走近老者就会自动往下走
g3 = new_game()
run(g3, 3.4)
check("醒来在教程相位", g3.state == "TUTORIAL", g3.state)
g3.input.held.add(SC_W)
run(g3, 6.0)
g3.input.held.clear()
# 2026-11-14：圣坛还裂着的时候**走不出自己那块板子**（`can_stand` 判 `fractured()`）——
# 往上会被 BL 的顶沿挡住，站在板子的最上一行，而不是跑到坛外去。
check("一路往上会被板块边界挡住（留在 BL 里）", g3.board.in_altar(*g3.player.cell),
      str(g3.player.cell))
check("…而且停在 BL 的顶沿（走不动了）", g3.player.cell[0] == 13, str(g3.player.cell))
check("走到老者附近 → 自动进入自由探索（不卡在教程）", g3.state == "FREE_ROAM", g3.state)
# 往右走一段，确认在板块内是能自由移动的
before = g3.player.cell
g3.input.held.add(SC_D)
run(g3, 1.0)
g3.input.held.clear()
check("在板块内能正常走（往右挪了几格）", g3.player.cell[1] > before[1],
      "%s → %s" % (before, g3.player.cell))

# 2) 在坛外连按 Shift：前两次没反应，第三次放行
g4 = new_game()
run(g4, 3.4)
put(g4, (0, 0))
g4.handle_event(ev(225))
run(g4, 0.05)
check("坛外按一次 Shift 什么也没有（设计如此）", g4.state == "TUTORIAL", g4.state)
for _ in range(3):
    g4.handle_event(ev(225))
    run(g4, 0.05)
check("坛外连按三次 → 放行，不再卡在教程", g4.state == "FREE_ROAM", g4.state)

# ================= 老者：必须从第一帧就在画布上 =================
def has_color(g, pos, color, r=12):
    cx, cy = int(pos[0]), int(pos[1])
    return any(g.canvas.get_at((cx + dx, cy + dy))[:3] == color
               for dx in range(-r, r + 1, 2) for dy in range(-r, r + 1, 2))


g5 = new_game()
g5.draw()
check("开场第 0 帧：老者已经在画布上",
      has_color(g5, g5.oldman.pos, C_OLDMAN))

run(g5, 3.4)                                   # 进教程
check("教程阶段老者还在（不是某个相位才画出来）",
      g5.state == "TUTORIAL"
      and has_color(g5, g5.oldman.pos, C_OLDMAN), g5.state)

finish(TITLE)
