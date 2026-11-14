# -*- coding: utf-8 -*-
"""步骤 12~13 验收：可选互动（M4 / M5）+ 清屏演出 + 道具奖励 + 光扩散收尾。"""

import pygame

from _act1_common import (auto_mono, check, clear_wave1, fill_must, finish, new_game,
                          paint_ok, shot, to_battle)
from src import story
from src.config import (
    C_BAG_SLOT, C_CELL_BLACK, C_ITEM_LEATHER, C_ITEM_LEATHER_DARK, C_ITEM_PAPER, C_PANEL_LINE, MAP_CELL,
    MAP_CELL, MAP_OPEN_TIME, MONOLOGUE_TIME, PANEL_PAD, PANEL_W, PANEL_X, PROP_DEAD_CELL,
    SC_M, TARGET_N, TARGET_OFFSET, VALID,
    PROP_TOOL_CELL, SC_B, VALID
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

# ================= 步骤 12 · 可选互动 =================
run(g, MONOLOGUE_TIME + 0.5)      # 让 M3 自己淡掉（心声时长 5 秒）
check("M3 已经淡掉", g.mono_t == 0.0, "%.2f" % g.mono_t)

put(g, PROP_DEAD_CELL)
run(g, 0.1)
check("靠近死掉的红怪 → M4", g.mono_text == story.M4 and g.mono_t > 0, repr(g.mono_text[:24]))
check("M4 只触发一次（记了标记）", g.prop_done["dead"])

run(g, MONOLOGUE_TIME + 0.5)
put(g, (12, 12))
run(g, 0.5)
back = g.mono_text
put(g, PROP_DEAD_CELL)
run(g, 0.2)
check("走开再回来不重复弹 M4", g.mono_t == 0.0 and g.prop_done["dead"], repr(back[:20]))

put(g, PROP_TOOL_CELL)
run(g, 0.1)
check("靠近用过的道具 → M5", g.mono_text == story.M5 and g.mono_t > 0, repr(g.mono_text[:24]))
run(g, MONOLOGUE_TIME + 0.5)
put(g, (12, 12))
run(g, 0.3)
put(g, PROP_TOOL_CELL)
run(g, 0.2)
check("走开再回来不重复弹 M5", g.mono_t == 0.0 and g.prop_done["tool"])

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
check("第一波清完", clear_wave1(g))
fill_must(g)
checks_done = g.board.progress()
check("100 格涂满", checks_done == 100, "%d" % checks_done)

put(g, (12, 12))
run(g, 0.2)
check("涂满 100 格 → 进入清屏", g.state == "CLEAR", "%s/%s" % (g.state, g.clear_phase))
for _ in range(int(6.0 * 60)):                  # 发光 1.2 + 扩散 ~2.4 + 停顿 0.6
    if g.state == "REWARD":
        break
    auto_mono(g)
    g.update(1 / 60)
    g.draw()
check("走进圣坛 → 波扩散完毕", g.state == "REWARD", g.state)

run(g, 1.8)                       # REWARD_DELAY
check("道具浮出来了（BAG + MAP）", len(g.items) == 2,
      str([i.kind for i in g.items]))
check("道具落在「已复原的黑格」上",
      all(g.board.state[i.cell[0]][i.cell[1]] == VALID for i in g.items))
check("道具种类是 bag 和 map", {i.kind for i in g.items} == {"bag", "map"})
shot(g, "16_reward_items.png")

# 面板此时还没有物品栏 / 地图
panel_x = PANEL_X + PANEL_PAD
check("拾取前右侧没有物品栏", not g.has_bag and not g.has_map)

# 逐个拾取
for kind in ("bag", "map"):
    it = [i for i in g.items if i.kind == kind][0]
    put(g, it.cell)
    run(g, 0.05)
    check("站在 %s 旁边出现 PRESS [B] TO PICK UP" % kind.upper(),
          g.prompt_text == story.PROMPT_PICK, repr(g.prompt_text))
    g.handle_event(ev(SC_B))
    run(g, 0.05)
    check("按 B 拾取 %s" % kind.upper(),
          (g.has_bag if kind == "bag" else g.has_map) and it not in g.items)

check("拾取后弹出道具说明", g.hint_text in (story.ITEM_BAG, story.ITEM_MAP), repr(g.hint_text))
check("两个都到手", g.has_bag and g.has_map)

g.draw()
# 物品栏：8 个格子（边框色能在面板下半区找到）
bag_zone = pygame.Rect(panel_x, 438, 468, 150)
found = any(g.canvas.get_at((x, y))[:3] == C_PANEL_LINE
            for x in range(bag_zone.left, bag_zone.right, 3)
            for y in range(bag_zone.top, bag_zone.bottom, 3))
check("右侧出现 8 格物品栏（能找到格子边框）", found)

# 地图：平时是卷着的卷轴，按 M 才铺开（2026-11-11 改）
CHECK_MAP_CELL = MAP_CELL
from src.ui import map_rect  # noqa: E402

MAP_FULL = map_rect(1.0)                  # 纸面矩形直接问渲染层要，别手算（差一格就测不到真东西）
map_top = MAP_FULL.top
map_left = MAP_FULL.left


def map_pixels(g):
    dark = light = 0
    for tr in range(0, 21, 3):
        for tc in range(0, 21, 3):
            col = g.canvas.get_at((map_left + tc * CHECK_MAP_CELL + 3,
                                   map_top + tr * CHECK_MAP_CELL + 3))[:3]
            if col == C_CELL_BLACK:
                dark += 1
            elif col[0] > 180:
                light += 1
    return dark, light


d0, l0 = map_pixels(g)
check("没按 M 时地图是卷起来的（右侧没有展开的进度图）", d0 == 0 and l0 < 20,
      "dark %d light %d" % (d0, l0))

g.handle_event(ev(SC_M))
run(g, MAP_OPEN_TIME + 0.15)
d1, l1 = map_pixels(g)
check("按 M 之后铺开成 21×21 进度图（黑/浅两色都有）", d1 > 0 and l1 > 0,
      "dark %d light %d" % (d1, l1))
shot(g, "18_panel_bag_map.png")

# 延迟 5 秒 → 光扩散 → 幕结束
run(g, 5.4)
check("两个都捡起后等 5 秒开始扩散", g.reward_phase == "spread", str(g.reward_phase))
run(g, 0.8)
shot(g, "17_spread.png")
run(g, 2.0)
check("光扩散完 → ACT 1 — END", g.state == "END" and g.banner_text == story.ACT_TITLE,
      "%s %r" % (g.state, g.banner_text))
g.menu_t = 0.0                            # 让闪烁提示这一帧是亮的
shot(g, "19_act_end.png")

# ==================== 物品栏里放什么（2026-11-11） ====================
# 背包是容器本身，不占自己的格子；格子里放的是包里的东西（地图）。
def panel_has(g, color, rect):
    g.draw()
    return any(g.canvas.get_at((x, y))[:3] == color
               for x in range(rect.left, rect.right, 2)
               for y in range(rect.top, rect.bottom, 2))


PANEL_INNER = PANEL_W - PANEL_PAD * 2
bag_area = pygame.Rect(PANEL_X + PANEL_PAD, 372, PANEL_INNER, 190)

g_only_bag = to_battle(new_game())
g_only_bag.has_bag, g_only_bag.has_map = True, False
g_only_bag.draw()
check("只有背包时：物品栏格子是空的（背包不占格子）",
      not panel_has(g_only_bag, C_ITEM_LEATHER, bag_area)
      and not panel_has(g_only_bag, C_ITEM_LEATHER_DARK, bag_area),
      "皮革色不该出现在格子里")

# 没有背包就没有「容器」——物品栏整块不画（拾取顺序上也不会出现这种状态）
g_no_bag = to_battle(new_game())
g_no_bag.has_bag, g_no_bag.has_map = False, True
g_no_bag.draw()
check("没有背包时：物品栏整块不画（背包才是容器）",
      not panel_has(g_no_bag, C_BAG_SLOT, bag_area),
      "槽底不该出现在这一区")

g_both = to_battle(new_game())
g_both.has_bag, g_both.has_map = True, True
g_both.draw()
check("两件都有：格子里仍然只有地图（格子数不变）",
      panel_has(g_both, C_ITEM_PAPER, bag_area)
      and not panel_has(g_both, C_ITEM_LEATHER, bag_area))

# ==================== 地图 = 每一幕收尾的定妆照（2026-11-12 作者改规则） ====================
# 作者原话：「这个地图只记录每一幕最后圣坛的样子，这个可以在下一幕提醒玩家之前涂了哪些。」
# 所以它**不是实时镜像**：本幕涂格子、红怪啃掉、紫怪清整行，地图都一动不动；
# 只有一幕真正收尾（清屏波扫完 + 脏格抹掉）才重新拍一张 —— 见 `Game.capture_map()`。
# 它也仍然不是答案纸：只拍「已经发生的事」，永不读 `target`。
from src.config import ERASING  # noqa: E402

orr, occ = TARGET_OFFSET


def map_cell_is_dark(g, tr, tc):
    """这一格在地图上有没有墨（逐像素扫，避免正好取在格边）。"""
    for dx in range(CHECK_MAP_CELL):
        for dy in range(CHECK_MAP_CELL):
            if g.canvas.get_at((map_left + tc * CHECK_MAP_CELL + dx,
                                map_top + tr * CHECK_MAP_CELL + dy))[:3] == C_CELL_BLACK:
                return True
    return False


def map_dark_cells(g):
    return {(tr, tc) for tr in range(TARGET_N) for tc in range(TARGET_N)
            if map_cell_is_dark(g, tr, tc)}


def altar_dark_cells(g):
    return {(tr, tc) for tr in range(TARGET_N) for tc in range(TARGET_N)
            if g.board.state[orr + tr][occ + tc] == VALID}


def target_cells(g):
    return {(r - orr, c - occ) for (r, c) in g.board.must}


def open_map(g):
    g.has_bag = g.has_map = True
    g.map_open = True
    g.map_t = 1.0
    g.draw()


# ---- A. 一幕都还没收尾：地图是一张白纸 ----
g_fresh = to_battle(new_game())
open_map(g_fresh)
check("还没有任何一幕收尾时，地图是整张白纸（没有任何一格墨）",
      map_dark_cells(g_fresh) == set(), str(len(map_dark_cells(g_fresh))))
check("...此时 map_act = 0（一次都没拍过）", g_fresh.map_act == 0, str(g_fresh.map_act))

# 没拿到地图时，按 M 什么都不发生
g_nomap = to_battle(new_game())
g_nomap.has_bag, g_nomap.has_map = True, False
g_nomap.handle_event(ev(SC_M))
check("没有地图时按 M 无效（map_open 不变）", not g_nomap.map_open)

# ---- B. 本幕涂格子：圣坛变了，地图不动（这是这轮的核心） ----
for (r, c) in sorted(g_fresh.board.must)[:12]:     # 当前这一波里随便涂几格
    paint_ok(g_fresh, r, c)
g_fresh.draw()
check("（准备）圣坛上确实涂黑了",
      len(altar_dark_cells(g_fresh)) > 5, str(len(altar_dark_cells(g_fresh))))
check("本幕涂的格子不会立刻出现在地图上（地图不是实时镜像）",
      map_dark_cells(g_fresh) == set(), str(len(map_dark_cells(g_fresh))))

# 地图上仍然没有「该涂但没涂」的格子 —— 不剧透
still_blank = next((tr, tc) for tr in range(TARGET_N) for tc in range(TARGET_N)
                   if g_fresh.target[tr][tc] and (orr + tr, occ + tc) not in g_fresh.board.must)
check("地图上不会提前标出「该涂但没涂」的格子（不剧透）",
      not map_cell_is_dark(g_fresh, *still_blank), str(still_blank))

# 再按一次 M 能卷回去
g_fresh.handle_event(ev(SC_M))
check("再按一次 M → 开始卷回去", not g_fresh.map_open)

# ---- C. 一幕收尾：才拍下这一张，且和那一瞬的圣坛一格不差 ----
clear_wave1(g_fresh)        # 第一波先过掉，下面才是整幕收尾
fill_must(g_fresh)
run(g_fresh, 6.0)          # 涂满 → CLEAR（发光 1.2s → 波扫 → 停 0.6s）→ REWARD，中间拍定格照
check("（准备）这一幕正常收尾了（进 REWARD）且拍了照",
      g_fresh.state == "REWARD" and g_fresh.map_act == 1,
      "%s act %d" % (g_fresh.state, g_fresh.map_act))
check("收尾那一刻：地图 = 圣坛（21×21 逐格一致，不多不少）",
      g_fresh.map_cells == altar_dark_cells(g_fresh) == target_cells(g_fresh),
      "map %d altar %d must %d" % (len(g_fresh.map_cells),
                                   len(altar_dark_cells(g_fresh)), len(target_cells(g_fresh))))
open_map(g_fresh)                                     # 收尾后再打开看一眼（前面按下 M 卷起来了）
check("地图画出来的墨和记录一致", map_dark_cells(g_fresh) == g_fresh.map_cells,
      "pixel %d data %d" % (len(map_dark_cells(g_fresh)), len(g_fresh.map_cells)))
check("100 格 ≠ 真码黑格 222 格 —— 地图仍然不是答案纸",
      len(g_fresh.map_cells) == 100
      and sum(1 for tr in range(TARGET_N) for tc in range(TARGET_N) if g_fresh.target[tr][tc]) > 200,
      "%d" % len(g_fresh.map_cells))
shot(g_fresh, "20_map_record.png")

# ---- D. 进下一幕：地图还是上一幕的，本幕怎么涂 / 怎么被清都不动 ----
act1_record = set(g_fresh.map_cells)
g_fresh.next_act()                                    # → ACT 2
auto_mono(g_fresh)                                    # 第二幕开场那句心声会冻住世界，先推掉
check("第二幕必涂格 = 第一幕 100 + 定时图案 6", len(g_fresh.board.must) == 106,
      str(len(g_fresh.board.must)))
open_map(g_fresh)
check("进第二幕地图仍是一张白纸？不 —— 还是第一幕的记录",
      map_dark_cells(g_fresh) == act1_record and g_fresh.map_act == 1,
      "%d" % len(map_dark_cells(g_fresh)))

new_one = sorted(c for c in g_fresh.board.must
                 if g_fresh.board.state[c[0]][c[1]] != VALID)[0]
paint_ok(g_fresh, *new_one)                            # 第二幕涂一格定时图案（先照再涂）
g_fresh.draw()
check("第二幕涂了新格子，地图仍然只有第一幕的记录（不实时变黑）",
      map_dark_cells(g_fresh) == act1_record, str(len(map_dark_cells(g_fresh))))

wiped_row = max(range(25), key=lambda r: g_fresh.board.line_dark("row", r))
wiped = g_fresh.board.clear_row(wiped_row, kind="purple")   # 紫怪清掉一整行
g_fresh.draw()
check("（准备）紫怪确实清掉了圣坛上的黑格", wiped > 0, "wiped %d at row %d" % (wiped, wiped_row))
check("紫怪清行只掉在圣坛上，地图上的墨不掉（那是上一幕的账）",
      map_dark_cells(g_fresh) == act1_record
      and len(altar_dark_cells(g_fresh)) < len(act1_record),
      "map %d altar %d" % (len(map_dark_cells(g_fresh)), len(altar_dark_cells(g_fresh))))

# 抹除中的格子只影响圣坛，不影响地图（看完还原成 VALID，免得后面填不满必涂格）
g_fresh.board.state[orr + 3][occ + 3] = ERASING
g_fresh.draw()
check("圣坛上抹除中的格子，在地图上仍然是上一幕的黑（互不干扰）",
      (3, 3) in map_dark_cells(g_fresh) and (3, 3) in act1_record)
g_fresh.board.state[orr + 3][occ + 3] = VALID

# ---- E. 第二幕收尾：再拍一张，记录里就多出定时图案那 6 格 ----
g_fresh.state = "BATTLE"                               # 让完成判定生效
fill_must(g_fresh)
run(g_fresh, 6.0)
check("第二幕收尾后重拍：map_act = 2 且地图 = 圣坛（106 格）",
      g_fresh.map_act == 2 and g_fresh.map_cells == altar_dark_cells(g_fresh)
      and len(g_fresh.map_cells) == 106,
      "act %d cells %d" % (g_fresh.map_act, len(g_fresh.map_cells)))
check("上一幕的记录是这张新图的一部分（幕账只增不减）",
      act1_record <= g_fresh.map_cells)
shot(g_fresh, "21_map_act2.png")


finish(TITLE)
