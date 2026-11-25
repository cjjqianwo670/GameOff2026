# -*- coding: utf-8 -*-
"""步骤 12~13 验收：清屏演出 + 道具奖励 + 光扩散收尾。"""

import pygame

from _act1_common import (all_boards, auto_mono, check, fill_must, finish, new_game,
                          paint_ok, shot, to_battle)
from src import story
from src.config import (
    C_BAG_SLOT, C_CELL_BLACK, C_ITEM_LEATHER, C_ITEM_LEATHER_DARK, C_PANEL_LINE,
    MONOLOGUE_TIME, PANEL_PAD, PANEL_W, PANEL_X,
    TARGET_N, TARGET_OFFSET, SC_B, VALID
)
from src.grid import cell_center, cell_to_rect

TITLE = "STEP 12~13 · OPTIONAL BITS / CLEAR / REWARD"


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


g = new_game()
run(g, 3.4)
g.enter_free_roam()
run(g, 4.2)                       # 等过场（赶怪 + 狠话 + M3）走完

# ================= 步骤 13 · 清屏 + 奖励 =================
# 模拟一个正常玩家：战斗里用异象扫过圣坛大半（地图只记照过的地方）
for rr in range(2, 23, 4):
    for cc in range(2, 23, 4):
        g.board.reveal_around(rr, cc)

put(g, (12, 6))
g.start_gap()
for _ in range(int(10.1 * 60)):
    auto_mono(g)
    g.update(1 / 60)
check("空档结束进战斗", g.state == "BATTLE", g.state)

# 第一幕分两波：先过第一波（33 格 + 迷你清屏），再写第二波
# 第一幕是四块板块：一路写到整幕收尾（最后一并进来那块 0 格，直接进终局清屏）
all_boards(g)
checks_done = g.board.progress()
check("100 格涂满", checks_done == 100, "%d" % checks_done)

check("四块写满 → 收尾清屏 → 进奖励阶段", g.state == "REWARD", g.state)

run(g, 1.8)                       # REWARD_DELAY
kinds = sorted(i.kind for i in g.items)
check("道具浮出来了（BAG + MAP 两件）", kinds == ["bag", "map"], str(kinds))
check("道具落在「已复原的黑格」上",
      all(g.board.state[i.cell[0]][i.cell[1]] == VALID for i in g.items))
shot(g, "16_reward_items.png")

# 面板此时还没有物品栏
panel_x = PANEL_X + PANEL_PAD
check("拾取前右侧没有物品栏", not g.has_bag)

bag_it = next(i for i in g.items if i.kind == "bag")
put(g, bag_it.cell)
run(g, 0.05)
check("站在 BAG 旁边出现 PRESS [B] TO PICK UP", g.prompt_text == story.PROMPT_PICK, repr(g.prompt_text))
g.handle_event(ev(SC_B))
run(g, 0.05)
check("按 B 拾取 BAG", g.has_bag and bag_it not in g.items)
check("拾取后弹出道具说明", g.hint_text == story.ITEM_BAG, repr(g.hint_text))

map_it = next(i for i in g.items if i.kind == "map")
put(g, map_it.cell)
run(g, 0.05)
g.handle_event(ev(SC_B))
run(g, 0.05)
check("按 B 拾取 MAP", g.has_map and map_it not in g.items)
check("地图说明指向第二圣坛", g.hint_text == story.ITEM_MAP, repr(g.hint_text))
shot(g, "17_bag_with_map.png")

g.draw()
# 物品栏：8 个格子（边框色能在面板下半区找到）
bag_zone = pygame.Rect(panel_x, 438, 468, 150)
found = any(g.canvas.get_at((x, y))[:3] == C_PANEL_LINE
            for x in range(bag_zone.left, bag_zone.right, 3)
            for y in range(bag_zone.top, bag_zone.bottom, 3))
check("右侧出现 8 格物品栏（能找到格子边框）", found)

finish(TITLE)
