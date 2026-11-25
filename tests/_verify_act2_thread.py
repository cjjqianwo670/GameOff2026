# -*- coding: utf-8 -*-
"""第二幕 · 界丝（BOUND-THREAD）与跨缝通道验收（2026-11-15 作者定）。

规则：
  界丝是圣坛感应到自身状况后产出的「自我修复物质」，轻薄、一次性。
  · 只在唯一固定黑点（暗模块 DARK_MODULE）上生成，一个点同一时间只能停一根
    —— 玩家不取走，圣坛就停产（防刷的自然抑制）。
  · 拾取进背包，堆叠占 1 格，上限 THREAD_MAX；满则提示放不下。
  · 按 I 朝 facing 方向搭跨缝通道：读条 1 秒，通道持续 5 秒，不可被怪破坏，
    玩家能在通道上来回走（不能拐弯）。
  · 分离板块挡人挡涂，但核心格例外 —— 否则补不了核心会软锁。
"""

import pygame

from _act1_common import auto_mono, check, finish, new_game
from src.config import (
    DARK_MODULE, SC_B, SC_I, THREAD_BRIDGE_CAST, THREAD_BRIDGE_LIFE, THREAD_MAX,
    THREAD_PICK_RANGE, THREAD_SPAWN_INTERVAL, TARGET_OFFSET
)
from src.grid import cell_center
from src.qr import finder_cores

TITLE = "STEP 16.5 · ACT 2 (BOUND-THREAD / BRIDGE)"


def to_act2():
    """真实走完第一幕，再进第二幕（四块全开、棋盘 100 格已涂）。"""
    from _act1_common import all_boards
    g = new_game()
    for _ in range(240):
        auto_mono(g)
        g.update(1 / 60)
    g.state = "FREE_ROAM"
    all_boards(g)
    g.start_act2()
    g.state = "BATTLE"
    g.spawn_rate = 0.0
    g.monsters.clear()
    g.purples.clear()
    return g


def key(sc):
    return pygame.event.Event(pygame.KEYDOWN, key=0, scancode=sc)


# ==================== 1. 黑点位置 ====================
g = to_act2()
cell = g.board.thread_cell()
check("界丝黑点 = 暗模块 DARK_MODULE 的主网格坐标",
      cell == (DARK_MODULE[0] + TARGET_OFFSET[0], DARK_MODULE[1] + TARGET_OFFSET[1]),
      str(cell))
check("黑点属于 BL 板块（左下）", g.board.board_of(*cell) == "BL", str(g.board.board_of(*cell)))

# ==================== 2. 生产：随时间生成，占位停产 ====================
check("第一幕没有界丝（act < 2 不生产）", True)   # 占位，真断言见下
g2 = to_act2()
g2.thread_on_cell = False
g2.thread_spawn_t = THREAD_SPAWN_INTERVAL
for _ in range(int(THREAD_SPAWN_INTERVAL * 60) + 2):
    auto_mono(g2)
    g2.update(1 / 60)
check("第二幕起，THREAD_SPAWN_INTERVAL 秒后黑点长出一根界丝", g2.thread_on_cell,
      "on_cell=%s" % g2.thread_on_cell)

# 不取走就停产：再等一个间隔，黑点上的界丝还是那一根，不会变多
g2.thread_count = 0
g2.thread_spawn_t = THREAD_SPAWN_INTERVAL
for _ in range(int(THREAD_SPAWN_INTERVAL * 60) + 2):
    auto_mono(g2)
    g2.update(1 / 60)
check("不取走 → 停产（黑点只能停一根，不会堆起来）", g2.thread_on_cell and g2.thread_count == 0,
      "on_cell=%s count=%d" % (g2.thread_on_cell, g2.thread_count))

# ==================== 3. 拾取：站近按 B，进背包 ====================
g3 = to_act2()
g3.thread_on_cell = True
g3.thread_count = 0
r, c = g3.board.thread_cell()
g3.player.cell = (r, c)
g3.player.pos.update(cell_center(r, c))
auto_mono(g3)                       # 推掉开场心声，别让 B 键被 mono_hold 吞掉
g3.handle_event(key(SC_B))
check("站在黑点旁按 B → 界丝进背包（count 1）", g3.thread_count == 1, "%d" % g3.thread_count)
check("黑点清空，重新计时下一根", not g3.thread_on_cell and g3.thread_spawn_t > 0,
      "on_cell=%s" % g3.thread_on_cell)

# 离太远捡不到
g3b = to_act2()
g3b.thread_on_cell = True
g3b.thread_count = 0
g3b.player.cell = (5, 5)          # 离黑点 (15,10) 很远
g3b.player.pos.update(cell_center(5, 5))
g3b.handle_event(key(SC_B))
check("离黑点太远按 B 捡不到", g3b.thread_count == 0 and g3b.thread_on_cell, "%d" % g3b.thread_count)

# 上限 99
g3c = to_act2()
g3c.thread_on_cell = True
g3c.thread_count = THREAD_MAX
r, c = g3c.board.thread_cell()
g3c.player.cell = (r, c)
g3c.player.pos.update(cell_center(r, c))
g3c.handle_event(key(SC_B))
check("背包满（THREAD_MAX）→ 放不下，数量不变", g3c.thread_count == THREAD_MAX, "%d" % g3c.thread_count)

# ==================== 4. 搭通道：跨缝判定 + 读条 + 扣界丝 + 持续 ====================
g4 = to_act2()
g4.thread_count = 3
# 玩家站 BL 板块边缘，朝右（facing=3）跨到 BR 板块
# 垂直缝在目标区 col 9/10（主网格 col 11/12）；BL 右边缘主网格 col=11，BR 左边缘 col=12
r, c = 15, 11                      # BL 右边缘，紧贴垂直缝
g4.player.cell = (r, c)
g4.player.pos.update(cell_center(r, c))
g4.player.facing = 3               # 朝右
cells = g4.board.bridge_cells(3, (r, c))
check("站在裂缝相邻格朝缝搭通道 → 得到两端格", cells == [(r, c), (r, c + 1)],
      str(cells))
check("朝向没有缝（朝左）→ 搭不了", g4.board.bridge_cells(2, (r, c)) is None)

# 读条 + 扣界丝 + 通道持续
g4.thread_cast_t = 0.0
g4.input.held.add(SC_I)
for _ in range(int(THREAD_BRIDGE_CAST * 60) + 2):
    auto_mono(g4)
    g4.update(1 / 60)
g4.input.held.discard(SC_I)
check("按住 I 读条满 1 秒 → 通道搭成，扣一根界丝",
      g4.thread_bridge is not None and g4.thread_count == 2,
      "count=%d bridge=%s" % (g4.thread_count, g4.thread_bridge is not None))
check("通道两端格正确", g4.thread_bridge is not None and
      set(g4.thread_bridge["cells"]) == {(r, c), (r, c + 1)}, str(g4.thread_bridge))

# 通道持续 5 秒后消失
for _ in range(int(THREAD_BRIDGE_LIFE * 60) + 2):
    auto_mono(g4)
    g4.update(1 / 60)
check("通道持续 THREAD_BRIDGE_LIFE 秒后消失", g4.thread_bridge is None)

# 没界丝搭不了
g4b = to_act2()
g4b.thread_count = 0
r, c = 15, 11
g4b.player.cell = (r, c)
g4b.player.pos.update(cell_center(r, c))
g4b.player.facing = 3
g4b.handle_event(key(SC_I))
check("没界丝按 I 搭不了通道", g4b.thread_bridge is None)

# ==================== 5. 分离板块内部能走，跨缝才需要通道 ====================
g5 = to_act2()
cores = finder_cores()
# 分离 TL
g5.board.detach_board("TL")
# TL 内部任意格：能站（玩家被困在分离板块里也得能动，否则当场卡死）
tl_inner = next((r, c) for r in range(2, 13) for c in range(2, 11)
                if g5.board.board_of(r, c) == "TL")
check("分离板块内部 → 能站（不被困死）", g5.board.can_stand(*tl_inner), str(tl_inner))
# 分离板块内部 → 能涂（补核心/补格子靠这个）
g5.board.state[tl_inner[0]][tl_inner[1]] = 0   # WHITE
g5.board.reveal_around(*tl_inner)
res = g5.board.paint(*tl_inner)
check("分离板块内部 → 能涂", res in ("valid", "dirty"), str(res))

# 跨缝：TL（分离）↔ BL（未分离，是 TL 的邻居）→ 有缝，不能直接走
tl_edge = (12, 5)                 # TL 下边缘主网格（目标区 row10 → 主网格 12），紧贴 BL 上边缘
bl_edge = (13, 5)                 # BL 上边缘
check("（准备）TL 下边缘与 BL 上边缘确实相邻且分属两板",
      g5.board.board_of(*tl_edge) == "TL" and g5.board.board_of(*bl_edge) == "BL",
      "%s / %s" % (g5.board.board_of(*tl_edge), g5.board.board_of(*bl_edge)))
check("（准备）TL 与 BL 之间是分离缝", g5.board.is_seam("TL", "BL"))
# 从 TL 跨到 BL（无通道）→ 挡
g5.player.cell = tl_edge
g5.player.pos.update(cell_center(*tl_edge))
check("跨分离缝（无通道）→ 走不过去", not g5._can_stand(tl_edge, bl_edge))
# 同板块内移动（TL 内部）→ 能走
check("分离板块内部移动 → 能走", g5._can_stand(tl_edge, (12, 4)))

# ==================== 6. 通道落脚格能跨缝走 ====================
g6 = to_act2()
g6.board.detach_board("BR")
# BR 分离后，从 BL（未分离）跨到 BR（分离，BL 的邻居）需要通道
bl_br_edge_from = (15, 11)        # BL 右边缘（主网格 col 11 = 目标区 col 9）
bl_br_edge_to = (15, 12)          # BR 左边缘（主网格 col 12 = 目标区 col 10）
check("（准备）BL 右边缘与 BR 左边缘分属两板且是缝",
      g6.board.board_of(*bl_br_edge_from) == "BL" and g6.board.board_of(*bl_br_edge_to) == "BR"
      and g6.board.is_seam("BL", "BR"))
g6.player.cell = bl_br_edge_from
g6.player.pos.update(cell_center(*bl_br_edge_from))
check("无通道时跨缝走不过去", not g6._can_stand(bl_br_edge_from, bl_br_edge_to))
# 搭了通道 → 能跨
g6.thread_bridge = {"cells": [bl_br_edge_from, bl_br_edge_to], "t": 5.0}
check("搭了通道 → 能跨缝走到对面板块", g6._can_stand(bl_br_edge_from, bl_br_edge_to))
check("通道外的分离缝仍走不过去", not g6._can_stand((16, 11), (16, 12)))

# ============ 7. 来历与作用（2026-11-24：作者「界丝没有讲述来历和作用」）============
# 三个「第一次」各给一句，且一生只给一次 —— 第二幕很静，不能每次都念。
from src import story  # noqa: E402

g7 = to_act2()
g7.mono_hold = False
g7.mono_text = ""
g7.thread_on_cell = False
g7.thread_spawn_t = 0.01
g7.thread_count = 0
g7.update(1 / 60)
check("第一次黑点长出界丝 → 独白说清「圣坛自己长的、一次一根」",
      g7.mono_hold and g7.mono_text == story.A2_THREAD_BORN, repr(g7.mono_text))

# 推掉这句；再把黑点占位/清空各试一次，确认不会第二次弹
for _ in range(240):
    auto_mono(g7)
    g7.update(1 / 60)
g7.mono_text = ""
g7.thread_on_cell = False
g7.thread_spawn_t = 0.01
g7.update(1 / 60)
check("第二次长出 → 不再念（一生一次）", not g7.mono_hold and g7.mono_text == "",
      repr(g7.mono_text))

# 第一次捡起：讲来历 + 用途
g7.mono_hold = False
g7.thread_on_cell = True
g7.thread_count = 0
r, c = g7.board.thread_cell()
g7.player.cell = (r, c)
g7.player.pos.update(cell_center(r, c))
g7.handle_event(key(SC_B))
check("第一次捡起界丝 → 独白说清来历与用途",
      g7.mono_hold and g7.mono_text == story.A2_THREAD_PICK, repr(g7.mono_text))

# 第一次搭成通道：只飘一句（不停世界）
g7.mono_hold = False
g7.thread_count = 1
r, c = 15, 11
g7.player.cell = (r, c)
g7.player.pos.update(cell_center(r, c))
g7.player.facing = 3
g7.toasts.clear()
g7.input.held.add(SC_I)
for _ in range(int(THREAD_BRIDGE_CAST * 60) + 2):
    g7.update(1 / 60)
g7.input.held.discard(SC_I)
texts = [t[0] for t in g7.toasts]
check("第一次搭成通道 → 飘字「撑不久」，且不冻世界",
      story.A2_THREAD_BRIDGE in texts and not g7.mono_hold, str(texts))
check("三句台词都在（来历 + 作用 + 时限）",
      all(getattr(story, n) for n in ("A2_THREAD_BORN", "A2_THREAD_PICK", "A2_THREAD_BRIDGE")))

finish(TITLE)
