# -*- coding: utf-8 -*-
"""步骤 3.5 验收：两个**原本没人教**的动作 —— Shift 照灰、J 落笔（2026-11-14 补）。

背景：Shift 只在教程里出现过一次（`TRY [SHIFT]`），而 **J 从头到尾没被任何演出教过** ——
屏幕上只有底部一行小字 `[J] DARK` 和 HUD 的 `DARK 0/33`。这份脚本锁住三条新契约：

    1. 还没按过 Shift 时，开场那一小片灰**不褪**（邀请不会自己消失）
    2. 站在亮着的灰域上 → 提示 `PRESS [J] TO WRITE HERE`（走开就收，不是一次性弹窗）
    3. 第一笔涂对 → 一句确认 + 从此不再教
"""

import pygame

from _act1_common import auto_mono, check, finish, new_game, reveal_once, shot
from src import story
from src.config import ANOMALY_MISS_LIMIT, PLAYER_START_CELL, SC_J, SC_T
from src.grid import cell_center

TITLE = "STEP 3.5 · TEACHING: SHIFT / J"


def ev(sc):
    return pygame.event.Event(pygame.KEYDOWN, key=0, scancode=sc)


def run(g, secs):
    for _ in range(max(1, int(secs * 60))):
        auto_mono(g)
        g.update(1 / 60)


def put(g, cell):
    g.player.cell = cell
    g.player.pos.update(cell_center(*cell))


def lit_count(g):
    return sum(1 for r in range(25) for c in range(25) if g.board.reveal[r][c] > 0)


g = new_game()
run(g, 3.4)                                     # 开场动画 + M1（auto_mono 会把 M1 关掉）
check("醒来在教程相位", g.state == "TUTORIAL", g.state)
check("一睁眼脚下就有灰", lit_count(g) > 0, "%d 格" % lit_count(g))

# --- 1) 不按 Shift：那片灰不能自己散掉 ---
run(g, 8.0)                                     # 远超过 MIRAGE_FADE=5 秒
check("还没按过 Shift：开场那片灰一直留着（不褪）", lit_count(g) > 0, "%d 格" % lit_count(g))
check("原地站着也能收到 TRY [SHIFT]（不必走满 5 秒）",
      g.prompt_text == story.TUTORIAL_SHIFT, repr(g.prompt_text))

# --- 2) 第一次照出灰域 ---
g.handle_event(ev(225))
auto_mono(g, 5)
check("第一次照出灰域 → M2", g.mono_last == story.M2 or g.mono_text == story.M2,
      repr((g.mono_last or g.mono_text)[:20]))
check("照出灰域后进入自由探索", g.state == "FREE_ROAM", g.state)

# --- 3) 站在灰上 → 教 J ---
put(g, PLAYER_START_CELL)
g.board.reveal_around(*PLAYER_START_CELL)
run(g, 0.15)
check("站在亮着的灰域上：提示按 J", g.prompt_text == story.PROMPT_WRITE, repr(g.prompt_text))
check("这时候还没教完（taught_write=False）", not g.taught_write)
shot(g, "26_teach_write.png")

# --- 4) 走开 → 提示自己收掉 ---
put(g, (0, 0))
run(g, 0.1)
check("走到没有灰的地方：提示收掉", g.prompt_text != story.PROMPT_WRITE, repr(g.prompt_text))

# --- 5) 回来按下 J：第一笔 ---
put(g, PLAYER_START_CELL)
g.board.reveal_around(*PLAYER_START_CELL)
g.input.held.add(SC_J)
run(g, 0.1)
g.input.held.clear()
check("第一笔落对了", g.board.progress() == 1, "%d" % g.board.progress())
check("第一笔之后标记为「教完」", g.taught_write)
check("第一笔给一句确认", g.toasts and g.toasts[-1][0] == story.MONO_FIRST,
      repr(g.toasts[-1][0] if g.toasts else None))
check("提示随之收掉", g.prompt_text == "", repr(g.prompt_text))

# --- 6) 教完之后不再打扰 ---
put(g, (PLAYER_START_CELL[0], PLAYER_START_CELL[1] + 1))
g.board.reveal_around(PLAYER_START_CELL[0], PLAYER_START_CELL[1] + 1)
run(g, 0.15)
check("教完之后：站在灰上也不再提示", g.prompt_text != story.PROMPT_WRITE, repr(g.prompt_text))

# --- 7) 涂脏格（没照过）不能算「学会」 ---
g2 = new_game()
run(g2, 3.4)
g2.enter_free_roam()
put(g2, (12, 12))                               # 圣坛正中：第一幕这里没有灰
g2.input.held.add(SC_J)
run(g2, 0.1)
g2.input.held.clear()
check("盲涂出脏格不算学会", not g2.taught_write and g2.board.stains > 0,
      "%s / 脏格 %d" % (g2.taught_write, g2.board.stains))

# --- 8) 和老者的对话排在 Shift 之后（2026-11-14）---
# 没照过灰域就走到老者跟前：不许出现 PRESS [T]，而是把缺的那一步（Shift）递给他
g3 = new_game()
run(g3, 3.4)
g3.enter_free_roam()
put(g3, (4, 12))
run(g3, 0.1)
check("还没照过灰域：不提示 PRESS [T]，改提示 TRY [SHIFT]",
      g3.prompt_text == story.TUTORIAL_SHIFT, repr(g3.prompt_text))
g3.handle_event(ev(SC_T))
run(g3, 0.2)
check("还没照过灰域：按 T 也开不了对话", g3.state == "FREE_ROAM", g3.state)
check("按 T 会回一句 TRY [SHIFT]",
      g3.hint_text == story.TUTORIAL_SHIFT and g3.hint_t > 0, repr(g3.hint_text))

put(g3, PLAYER_START_CELL)                       # 回到出生点那片灰上，真的照一次
check("（准备）照一次灰域", reveal_once(g3))
put(g3, (4, 12))
run(g3, 0.1)
check("照过灰域之后：提示变成 PRESS [T] TO CALL OUT",
      g3.prompt_text == story.PROMPT_CALL, repr(g3.prompt_text))
g3.handle_event(ev(SC_T))
run(g3, 0.2)
check("照过灰域之后：按 T 能开对话", g3.state == "DIALOG", g3.state)

# --- 9) 严格模式：照不出灰就是不算，空照三次也不放行（2026-11-14 作者定）---
# 之前的「连照 3 次空就放行」被去掉了：作者要的是**必须先真的照出一次灰域**。
# 代价是玩家站在没有活的地方会一直看到 TRY [SHIFT]，这是有意的 —— 提示不会消失，直到他照到。
g6 = new_game()
run(g6, 3.4)
g6.enter_free_roam()
put(g6, (4, 12))                                 # 这里第一幕没有活，照不出灰
run(g6, 0.1)
for _ in range(ANOMALY_MISS_LIMIT + 2):
    g6.handle_event(ev(225))
    run(g6, 0.1)
check("空照多次也不算「照到过」", not g6.looked)
check("空照之后仍然只有 TRY [SHIFT]，没有 PRESS [T]",
      g6.prompt_text == story.TUTORIAL_SHIFT, repr(g6.prompt_text))
g6.handle_event(ev(SC_T))
run(g6, 0.2)
check("空照之后按 T 依然开不了对话", g6.state == "FREE_ROAM", g6.state)

# --- 10) Shift 的提示是**全局**的：离开老者也一样给 ---
put(g6, (12, 18))                                # 圣坛右下角，离老者很远
run(g6, 0.1)
check("离老者很远也提示 TRY [SHIFT]", g6.prompt_text == story.TUTORIAL_SHIFT, repr(g6.prompt_text))
put(g6, PLAYER_START_CELL)
check("（准备）在出生点真的照一次", reveal_once(g6))
run(g6, 0.1)
check("照到之后：那句 TRY [SHIFT] 立刻退场", g6.prompt_text != story.TUTORIAL_SHIFT, repr(g6.prompt_text))
put(g6, (12, 18))
run(g6, 0.1)
check("照到之后：远处也不会再提示 TRY [SHIFT]", g6.prompt_text != story.TUTORIAL_SHIFT, repr(g6.prompt_text))

# --- 11) 学过的东西不该每一幕重教一遍（2026-11-14 审计）---
g7 = new_game()
run(g7, 3.4)
check("（准备）第一幕照过灰域", reveal_once(g7))
g7.taught_write = True                           # 假装已经写下过第一笔
g7.start_act2()                                  # 进第二幕（会走 _begin_act 的公共复位）
run(g7, 0.2)
check("第二幕：不再重新教 Shift", g7.prompt_text != story.TUTORIAL_SHIFT, repr(g7.prompt_text))
check("第二幕：looked / taught_write 都保留", g7.looked and g7.taught_write,
      "%s / %s" % (g7.looked, g7.taught_write))
check("第二幕：must_all 跟着幕更新（不是停在第一幕的 100）",
      len(g7.must_all) == len(g7.must) == 106, "%d / %d" % (len(g7.must_all), len(g7.must)))

finish(TITLE)
