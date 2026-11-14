# -*- coding: utf-8 -*-
"""键位验收：每一个 scancode 都必须对得上 SDL 的 HID 表，且按对的键真的有用。

为什么单独有这一份：T 和 B 曾经写成 20 / 48（PS/2 扫描码），SDL 里 20 是 Q、48 是 ]，
结果「按 T 呼喊老者」永远没反应，而且所有玩法测试都还是绿的 —— 因为测试和实现用了同一个错数字。
这份脚本不查「代码和自己一致」，只查「代码和 SDL 的键表一致」。
"""

import pygame

from _act1_common import clear_wave1, reveal_once, auto_mono, check, fill_must, finish, new_game, to_roam, toast_text
from src import story
from src.config import (
    SC_A, SC_B, SC_D, SC_ENTER, SC_ESC, SC_F1, SC_J, SC_K, SC_KP_ENTER, SC_R, SC_S, SC_SHIFT,
    SC_SPACE, SC_T, SC_U, SC_W,)
from src.grid import cell_center

TITLE = "KEYS · SDL SCANCODE TABLE"

# SDL scancode（HID usage）：字母 A..Z = 4..29，数字 1..9 = 30..38，0 = 39
LETTER = {ch: 4 + i for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}

used = {"W": SC_W, "A": SC_A, "S": SC_S, "D": SC_D, "J": SC_J, "K": SC_K,
        "R": SC_R, "T": SC_T, "B": SC_B}
bad = {k: v for k, v in used.items() if LETTER[k] != v}
check("字母 scancode 全部符合 A=4…Z=29", not bad,
      "错：%s" % {k: (v, LETTER[k]) for k, v in bad.items()})

check("W=26 / A=4 / S=22 / D=7", (SC_W, SC_A, SC_S, SC_D) == (LETTER["W"], LETTER["A"],
                                                             LETTER["S"], LETTER["D"]))
check("J=13 / K=14（涂 / 擦）", (SC_J, SC_K) == (LETTER["J"], LETTER["K"]))
check("T=23（呼喊）", SC_T == 23, "%d" % SC_T)
check("U=24（挥剑，第三幕；作者指定，不是 Q/F）", SC_U == 24, "%d" % SC_U)
check("B=5（拾取，不是 48=]）", SC_B == 5, "%d" % SC_B)
check("Shift 左右 = 225 / 229", tuple(SC_SHIFT) == (225, 229), str(SC_SHIFT))
check("Enter / Esc / Space / F1", (SC_ENTER, SC_ESC, SC_SPACE, SC_F1) == (40, 41, 44, 58))
check("小键盘回车 = 88（旧代码里别名写成 SC_KP_ENTER_ALIAS，已删）", SC_KP_ENTER == 88)


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


# --- 行为：站在老者旁边，按 Q 没反应，按 T 才开口 ---
g = to_roam(new_game())
run(g, 0.2)
reveal_once(g)                                   # 先照过灰域，才允许喊老者（2026-11-14）
put(g, (4, 12))
run(g, 0.1)
check("走到老者旁边会提示 CALL OUT", g.prompt_text == story.PROMPT_CALL, repr(g.prompt_text))

g.handle_event(ev(LETTER["Q"]))
check("按 Q（旧代码里被当成 T）不会开始对话", g.state == "FREE_ROAM", g.state)

g.handle_event(ev(SC_T))
check("按 T 才开始对话", g.state == "DIALOG", g.state)
check("对话内容是坛内支线", len(g.dlg_lines) == 14, str(len(g.dlg_lines) if g.dlg_lines else None))

# --- 行为：站在道具上，按 ] 不捡，按 B 才捡 ---
g2 = to_roam(new_game())
clear_wave1(g2)          # 第一幕分两波：先过第一波，再写第二波
fill_must(g2)
g2.player.cell = (12, 12)
g2.player.pos.update(cell_center(12, 12))
g2.enter_clear()
g2.clear_phase = "wave"
g2.wave_r = 0.0
run(g2, 3.5)
run(g2, 1.8)
check("走到奖励阶段、道具已浮出", g2.state == "REWARD" and len(g2.items) == 2,
      "%s / %d" % (g2.state, len(g2.items)))
if g2.items:
    it = g2.items[0]
    put(g2, it.cell)
    run(g2, 0.05)
    g2.handle_event(ev(48))
    check("按 ]（旧代码里被当成 B）不会拾取", len(g2.items) == 2, "%d" % len(g2.items))
    g2.handle_event(ev(SC_B))
    check("按 B 才拾取", len(g2.items) == 1, "%d" % len(g2.items))

# ==================== 回车 / J 串键（2026-11-11 修的 bug） ====================
# 现象：站在格子上按回车，脚下被涂黑。
# 根因：InputState.down() 里曾用 pygame.key.get_pressed()[sc] 兜底，那个数组在部分环境下
#       按 keycode 索引，而这里传的是 scancode —— J 的 scancode 13 正好等于 Enter 的 keycode 13。
import src.input_state as _istate

_orig_pressed = pygame.key.get_pressed


class _FakePressed:
    """伪造「按着回车」时的键状态：只让索引 13 为真（模拟 keycode 索引的环境）。"""

    def __getitem__(self, i):
        return i == 13


st = _istate.InputState()
pygame.key.get_pressed = lambda: _FakePressed()
try:
    check("串键环境下 down(J) 不再为真（get_pressed 兜底已移除）", st.down(SC_J) is False,
          "SC_J=%d" % SC_J)
    check("串键环境下 down(回车) 也不为真", st.down(SC_ENTER) is False)
finally:
    pygame.key.get_pressed = _orig_pressed

# 端到端：站在必涂格上按回车，格子不能被涂黑
g3 = to_roam(new_game())
cell = sorted(g3.board.must)[0]
put(g3, cell)
run(g3, 0.1)
before = g3.board.state[cell[0]][cell[1]]
g3.input.handle_event(ev(SC_ENTER))      # main.py 里输入层也是这么收事件的
g3.handle_event(ev(SC_ENTER))
run(g3, 1.0)
check("按回车：held 里只有 40（不是 J 的 13）", g3.input.held == {SC_ENTER},
      str(g3.input.held))
check("按回车不会涂格子（站在必涂格上）",
      g3.board.state[cell[0]][cell[1]] == before,
      "state %d -> %d" % (before, g3.board.state[cell[0]][cell[1]]))
g3.input.handle_event(pygame.event.Event(pygame.KEYUP, key=0, scancode=SC_ENTER))

# 按 J 仍然要能涂（2026-11-12 起必须先把灰域照出来，否则算脏格）
g3.board.reveal_around(*cell)
g3.input.handle_event(ev(SC_J))
run(g3, 0.1)
check("按 J 才涂黑脚下", g3.board.state[cell[0]][cell[1]] == 1,
      "%d" % g3.board.state[cell[0]][cell[1]])

# 失焦 / 回焦点都要清空按键状态（防「回来就一直涂」）
g3.input.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
check("失焦后按键状态清空", not g3.input.held, str(g3.input.held))
g3.input.handle_event(ev(SC_J))
g3.input.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
check("回到焦点也清空（失焦期间可能漏 KEYUP）", not g3.input.held, str(g3.input.held))


def up(sc):
    return pygame.event.Event(pygame.KEYUP, key=0, scancode=sc)


def tap(g, sc, secs=0.2):
    """按一下再松开（涂改是每帧轮询 held 的，所以要真的按住一小会儿）。

    先 auto_mono：心声停住世界时，任何键（包括这个 tap）都会被吃掉，只认回车。
    """
    auto_mono(g)
    g.input.handle_event(ev(sc))
    g.handle_event(ev(sc))
    run(g, secs)
    g.input.handle_event(up(sc))


# ==================== 没照就涂：算脏格 + 两种提示分开（2026-11-12）====================
from src.config import DIRTY, VALID  # noqa: E402

g5 = to_roam(new_game())
cell5 = sorted(g5.board.must)[0]
put(g5, cell5)
tap(g5, SC_J)
check("没照过就涂必涂格 → 脏格", g5.board.state[cell5[0]][cell5[1]] == DIRTY,
      "%d" % g5.board.state[cell5[0]][cell5[1]])
check("...脏格计数 +1", g5.board.stains == 1, "%d" % g5.board.stains)
check("...嘀咕「我还没看清」（飘字，不冻世界）", toast_text(g5) == story.MONO_BLIND, repr(toast_text(g5)))

# 照过之后同一格就能涂对（提示也不该再出现）
g5.board.state[cell5[0]][cell5[1]] = 0                     # 抹白重来
g5.board.reveal_around(*cell5)
g5.hint_text = ""
tap(g5, SC_J)
check("照出来再涂 → 有效黑域", g5.board.state[cell5[0]][cell5[1]] == VALID,
      "%d" % g5.board.state[cell5[0]][cell5[1]])
check("...涂对时不再弹提示", g5.hint_text == "", repr(g5.hint_text))

# 涂错地方（坛内非必涂格）仍然是另一句提示
g6 = to_roam(new_game())
free6 = None
for r in range(2, 23):
    for c in range(2, 23):
        if (r, c) not in g6.board.must:
            free6 = (r, c)
            break
    if free6:
        break
put(g6, free6)
tap(g6, SC_J)
check("涂错地方 → 嘀咕「好像失败了」（和「没看」分开）",
      toast_text(g6) == story.MONO_STAIN, repr(toast_text(g6)))
check("第一次涂脏格仍教一下 K（按键教学保留）", g6.hint_text == story.HINT_CLEAR, repr(g6.hint_text))


# ==================== 地图摊开 = 双手捧着纸（2026-11-12 作者要求） ====================
# 作者：按 M 看地图时码序使两只手都占着，制造不了黑域；必须再按一次 M 收起来才能涂。
# 定稿范围（作者选）：J / K / Shift 全封；被挡时给一行提示 + 一声闷响。
from src.config import ERASING, MAP_OPEN_TIME, SC_M, VALID, WHITE  # noqa: E402


g4 = to_roam(new_game())
g4.has_bag = g4.has_map = True
cell_j = sorted(g4.board.must)[0]
put(g4, cell_j)
tap(g4, SC_M)                                   # 摊开
run(g4, MAP_OPEN_TIME + 0.1)
check("按 M 摊开地图", g4.map_open)

tap(g4, SC_J)
check("地图摊开时按 J 涂不上（双手捧着纸）",
      g4.board.state[cell_j[0]][cell_j[1]] == WHITE,
      "%d" % g4.board.state[cell_j[0]][cell_j[1]])
check("...被挡时给出一行提示", g4.hint_text == story.MAP_IN_HANDS, repr(g4.hint_text))

# K 也挡：先把脚下这格弄成黑，再按 K
g4.board.state[cell_j[0]][cell_j[1]] = VALID
tap(g4, SC_K)
check("地图摊开时按 K 也擦不掉", g4.board.state[cell_j[0]][cell_j[1]] == VALID,
      "%d" % g4.board.state[cell_j[0]][cell_j[1]])

# Shift 也挡：站着照不出灰域（先把开场自动照出的那 5×5 清掉，免得旧灰域混进来）
g4.board.state[cell_j[0]][cell_j[1]] = WHITE
for _r in range(25):
    for _c in range(25):
        g4.board.reveal[_r][_c] = 0.0
before_reveal = sum(1 for r in range(25) for c in range(25) if g4.board.reveal[r][c] > 0)
tap(g4, SC_SHIFT[0])
after_reveal = sum(1 for r in range(25) for c in range(25) if g4.board.reveal[r][c] > 0)
check("地图摊开时按 Shift 照不出灰域", after_reveal == before_reveal,
      "%d -> %d" % (before_reveal, after_reveal))

# 收起地图：立刻恢复
tap(g4, SC_M)
run(g4, MAP_OPEN_TIME + 0.1)
check("再按一次 M 收起来", not g4.map_open)
g4.board.reveal_around(*cell_j)                 # 先照出来再涂，才是有效黑域
tap(g4, SC_J)
check("收起地图后按 J 立刻能涂（不用等别的）",
      g4.board.state[cell_j[0]][cell_j[1]] == VALID,
      "%d" % g4.board.state[cell_j[0]][cell_j[1]])

# 站着的时候能走：捧图不影响移动（只是不能干活）
tap(g4, SC_M)                                   # 再摊开
run(g4, MAP_OPEN_TIME + 0.1)
check("（准备）地图又摊开了", g4.map_open)
put(g4, (12, 12))
g4.input.handle_event(ev(SC_W))
run(g4, 0.4)
g4.input.handle_event(up(SC_W))
check("捧图时还能走动（只封暗活，不封腿）", g4.player.cell != (12, 12), str(g4.player.cell))

# 按 R 重开一局：手里必须空出来，否则「捧着纸」会把涂改永久封住（而且没地图时按 M 解不开）
g4.input.handle_event(ev(SC_R))
g4.handle_event(ev(SC_R))
g4.input.handle_event(up(SC_R))
run(g4, 0.1)
check("按 R 重开后面板归位（没有地图）", not g4.has_map, str(g4.has_map))
check("按 R 重开时地图自动收起（否则涂改会被永久封住）", not g4.map_open)


finish(TITLE)
