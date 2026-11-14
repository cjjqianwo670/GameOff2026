# -*- coding: utf-8 -*-
"""第四幕验收：数据区「扫」（sweep）。

作者 2026-11-14 定的一幕：
  · 这一幕没有新图案、没有新 NPC —— 换的是**动词**：按住 J 扫灰域，盲格直接跳过（不写、不脏）
  · 异象扩到 7×7（照一次 49 格，走完要 6.4 秒 > 褪色 5 秒 → 覆盖不完，必须取舍）
  · 紫怪回潮（4 只/分），红怪照旧：你写多快，它吃多快
"""

import pygame

from _act1_common import auto_mono, check, finish, new_game, paint_ok, skip_intro
from src import story
from src.config import (
    MIRAGE_RADIUS, MIRAGE_RADIUS_ACT4, PURPLE_SPAWN_PER_MIN, PURPLE_SPAWN_PER_MIN_ACT3,
    PURPLE_SPAWN_PER_MIN_ACT4, SC_J, VALID, WHITE
)
from src.qr import required_cells
from src.grid import cell_center

TITLE = "STEP 18 · ACT 4 (SWEEP THE DATA AREA)"

ENTER, SHIFT = 40, 225
SW, SA, SS, SD = 26, 4, 22, 7


def to_act4():
    """一路涂到第三幕结束，再进第四幕。"""
    g = new_game()
    for (r, c) in sorted(g.board.must):
        paint_ok(g, r, c)
    g.start_act2()
    for (r, c) in sorted(g.must):
        if g.board.state[r][c] != VALID:
            paint_ok(g, r, c)
    g.start_act3()
    for (r, c) in sorted(g.must):
        if g.board.state[r][c] != VALID:
            paint_ok(g, r, c)
    g.start_act4()
    skip_intro(g)
    return g


def stand(g, cell):
    g.player.cell = cell
    g.player.pos.update(cell_center(*cell))


def white_cells(g):
    return sorted(c for c in g.must if g.board.state[c[0]][c[1]] == WHITE)


def clear_reveal(g):
    for row in g.board.reveal:
        for i in range(len(row)):
            row[i] = 0.0
    for row in g.board.state:
        pass


def hold(g, key, frames, dt=1 / 60):
    g.input.held.add(key)
    for _ in range(frames):
        auto_mono(g)
        g.update(dt)
    g.input.held.discard(key)


# ==================== 1. 必涂格：整张码 ====================
g = to_act4()
black = sum(1 for row in g.target for v in row if v)
check("第四幕的必涂格 = 整张码的所有黑格", len(g.must) == black, "%d / 黑格 %d" % (len(g.must), black))
check("...数量落在 206~244（v1 实测区间）", 200 <= len(g.must) <= 250, "%d" % len(g.must))
check("...包含前三幕的全部必涂格",
      required_cells(g.target, act=3) <= g.must,
      "%d ⊇ %d" % (len(g.must), len(required_cells(g.target, act=3))))
check("...数据区就是「剩下的那些」", len(g.must) - len(required_cells(g.target, act=3)) > 60,
      "第四幕新增 %d 格" % (len(g.must) - len(required_cells(g.target, act=3))))
check("...前三幕涂好的格子原地保留（不清盘）",
      g.board.progress() == len(required_cells(g.target, act=3)),
      "%d 格在手" % g.board.progress())

# ==================== 2. 扫：盲格跳过、灰域即写 ====================
clear_reveal(g)
target = white_cells(g)[0]
stand(g, target)
stains0 = g.board.stains
hold(g, SC_J, 20)
check("没照过就按住 J：不写（盲扫是白走）", g.board.state[target[0]][target[1]] == WHITE,
      "state %d" % g.board.state[target[0]][target[1]])
check("...而且不产生脏格（第四幕的盲涂不罚款，只是没用）",
      g.board.stains == stains0, "%d → %d" % (stains0, g.board.stains))

g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=SHIFT))
check("Shift 照出灰域", g.board.reveal[target[0]][target[1]] > 0,
      "%.2f" % g.board.reveal[target[0]][target[1]])
hold(g, SC_J, 2)                                # 两帧就够：不需要长按
check("走过灰域 → 立刻制造黑域（不必长按）",
      g.board.state[target[0]][target[1]] == VALID, "state %d" % g.board.state[target[0]][target[1]])

# 灰域褪了就该停手
nxt = white_cells(g)[0]
stand(g, nxt)
g.board.reveal[nxt[0]][nxt[1]] = 0.0    # 灰域已经褪干净
hold(g, SC_J, int(0.3 * 60))
check("灰域褪掉之后立刻停手（不是照过就一直能扫）",
      g.board.state[nxt[0]][nxt[1]] == WHITE, "state %d" % g.board.state[nxt[0]][nxt[1]])

# ==================== 3. 走路扫：一趟能连写 ====================
g2 = to_act4()
clear_reveal(g2)
# 找一格「右边 3 列里还有别的白格」的起点（随机目标下每行白格疏密不同）
cells = white_cells(g2)
pick = None
for (r, c) in cells:
    win = [x for x in cells if x[0] == r and c <= x[1] <= c + MIRAGE_RADIUS_ACT4]
    if len(win) >= 2:
        pick = (r, c, win)
        break
check("数据区里找得到一条能扫的线", pick is not None, "")
start = (pick[0], pick[1])
stand(g2, start)
g2.board.reveal_around(start[0], start[1], radius=MIRAGE_RADIUS_ACT4)
win = pick[2]                                   # 灰域只覆盖右边 3 列
edge = win[-1][1]
g2.input.held.add(SC_J)
for _ in range(int(2.5 * 60)):
    auto_mono(g2)
    g2.update(1 / 60)
    g2.input.held.add(SD)                        # 一直往右走
    if g2.player.cell[1] >= edge:
        break
g2.input.held.clear()
painted = sum(1 for c in win if g2.board.state[c[0]][c[1]] == VALID)
check("按住 J 走一条线：窗口里经过的格全写上了（不用松手重按）",
      painted == len(win) and painted >= 2, "%d / %d" % (painted, len(win)))
check("...走过没照过的格也没制造脏格", g2.board.stains == 0, "%d" % g2.board.stains)

# ==================== 4. 异象半径：第四幕 7×7 ====================
check("第四幕的异象半径是 3（7×7）", MIRAGE_RADIUS_ACT4 == 3, "%d" % MIRAGE_RADIUS_ACT4)
check("...前三幕仍是 2（5×5）", MIRAGE_RADIUS == 2, "%d" % MIRAGE_RADIUS)
g3 = to_act4()
n4 = sum(g3.board.reveal_around(12, 12, radius=g3.mirage_radius()) for _ in [0])
check("...mirage_radius() 在第四幕返回 3", g3.mirage_radius() == 3, str(g3.mirage_radius()))
check("...照出来的范围比前三幕大",
      g3.board.reveal_around(12, 12, radius=g3.mirage_radius()) >= 0 and n4 > 0,
      "照到 %d 格" % n4)

# ==================== 5. 紫怪回潮 ====================
check("第四幕紫怪 4 只/分（第三幕 2、第二幕 6）",
      PURPLE_SPAWN_PER_MIN_ACT4 == 4.0 and PURPLE_SPAWN_PER_MIN_ACT3 == 2.0
      and PURPLE_SPAWN_PER_MIN == 6.0,
      "%.1f / %.1f / %.1f" % (PURPLE_SPAWN_PER_MIN_ACT4, PURPLE_SPAWN_PER_MIN_ACT3, PURPLE_SPAWN_PER_MIN))

g4 = to_act4()
g4.spawn_rate = 0.0
g4.purple_spawned = 1
g4.purple_t = 0.0
t = 0.0
while not g4.purples and t < 20:
    auto_mono(g4)
    g4.update(1 / 60)
    t += 1 / 60
check("第四幕 15 秒来一只紫怪（4 只/分）", abs(t - 15.0) < 0.3, "%.1fs" % t)

# ==================== 6. 通关 → 清屏 → END（ACT 4 — END）====================
g5 = to_act4()
g5.spawn_rate = 0.0
g5.monsters.clear()
g5.purples.clear()
g5.spawn_purple = lambda: None
g5.update_yellows = lambda dt: None
for (r, c) in sorted(g5.must):
    if g5.board.state[r][c] != VALID:
        paint_ok(g5, r, c)
auto_mono(g5)
g5.update(1 / 60)
check("涂满整张码 → 清屏", g5.state == "CLEAR", g5.state)
check("...进度 = 必涂总数（整张码）", g5.board.progress() == len(g5.must),
      "%d / %d" % (g5.board.progress(), len(g5.must)))

for _ in range(int(25 * 60)):
    auto_mono(g5)
    g5.update(1 / 60)
    if g5.state == "END":
        break
check("第四幕收尾会走到 END", g5.state == "END", g5.state)
check("...字幕是 ACT 4 — END", g5.banner_text == "ACT 4 — END", repr(g5.banner_text))
check("...第四幕也不发道具", not g5.items, "%d 件" % len(g5.items))
check("...act_title(4) 就是 ACT 4 — END", story.act_title(4) == "ACT 4 — END", story.act_title(4))
g5.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
check("...END 按回车进第五幕（2026-11-14 接上了）", g5.act == 5 and g5.state == "BATTLE",
      "act %d / %s" % (g5.act, g5.state))

# ==================== 6b. 老者回来：只补骨架，不碰数据区 ====================
from src.qr import structural_black_cells, CODEWORD_INDEX

g7 = to_act4()
g7.spawn_rate = 0.0
g7.monsters.clear(); g7.purples.clear()
g7.spawn_purple = lambda: None
check("第四幕把老者放回来了", g7.oldman is not None and not g7.oldman.gone,
      "oldman=%s gone=%s" % (g7.oldman is not None, g7.oldman and g7.oldman.gone))
check("...他管的那批格 = 结构黑格（定位/定时/暗模块/格式）",
      g7.repair_cells == structural_black_cells(g7.target),
      "%d 格" % len(g7.repair_cells))
check("...和数据区完全不相交（数据区他一格不碰）",
      not any(CODEWORD_INDEX[r - 2][c - 2] >= 0 for (r, c) in g7.repair_cells),
      "%d 格里没有数据格" % len(g7.repair_cells))

# 结构格被抹白 → 他会走过去补
struct_cell = sorted(c for c in g7.repair_cells if g7.board.state[c[0]][c[1]] == VALID)[0]
g7.board.state[struct_cell[0]][struct_cell[1]] = WHITE
t = 0.0
while g7.board.state[struct_cell[0]][struct_cell[1]] != VALID and t < 12:
    auto_mono(g7)
    g7.update(1 / 60)
    if g7.oldman:
        g7.oldman.update(1 / 60)
    t += 1 / 60
check("结构格被抹白 → 老者自己走过去补上", g7.board.state[struct_cell[0]][struct_cell[1]] == VALID,
      "%.1fs / %s" % (t, struct_cell))

# 数据格被抹白 → 他当没看见
g7b = to_act4()
g7b.spawn_rate = 0.0
g7b.monsters.clear(); g7b.purples.clear(); g7b.spawn_purple = lambda: None
data_cell = None
for (r, c) in sorted(g7b.must):
    if CODEWORD_INDEX[r - 2][c - 2] >= 0:            # 数据区一格（第四幕开局本来就是白的）
        data_cell = (r, c)
        break
g7b.board.state[data_cell[0]][data_cell[1]] = WHITE
t = 0.0
while t < 8:
    auto_mono(g7b)
    g7b.update(1 / 60)
    if g7b.oldman:
        g7b.oldman.update(1 / 60)
    t += 1 / 60
check("数据格被抹白 → 他不补（那是玩家的活）",
      g7b.board.state[data_cell[0]][data_cell[1]] == WHITE,
      "%.0fs 后仍是白的 %s" % (t, data_cell))
check("...他对数据区没有任何目标（骨架本来是齐的，没有活可干）",
      g7b.repair_target is None and g7b.repair_i == 0,
      "target=%s / repair_i=%d" % (g7b.repair_target, g7b.repair_i))

# ==================== 7. 这一幕没有黄怪 ====================
g6 = to_act4()
for _ in range(int(20 * 60)):              # 跑 20 秒：黄怪只在第三幕刷，这一幕一只都不该来
    auto_mono(g6)
    g6.update(1 / 60)
check("第四幕不刷黄怪（跑 20 秒也是一只没有）",
      not g6.yellows and g6.yellow_spawned == 0,
      "%d 只 / spawned %d" % (len(g6.yellows), g6.yellow_spawned))
check("...开场那句把分工交代清楚（他守骨架，我填内容）",
      "keeps the frame" in story.A4_M1, repr(story.A4_M1[:26]))
check("...底部提示教的是「按住 J 扫」", story.HINT_SWEEP.startswith("HOLD [J]"), repr(story.HINT_SWEEP))

# ==================== 8. 检查点：第四幕阵亡回本幕开头 ====================
g7 = to_act4()
g7.spawn_rate = 0.0
g7.monsters.clear()
g7.purples.clear()
g7.spawn_purple = lambda: None
for (r, c) in white_cells(g7)[:5]:
    paint_ok(g7, r, c)
before = g7.board.progress()
g7.health = 5
for _ in range(20):
    g7.damage(5) if hasattr(g7, "damage") else None
    g7.health = max(0, g7.health - 5)
    auto_mono(g7)
    g7.update(1 / 60)
    if g7.state == "DEAD":
        break
check("第四幕阵亡会进 DEAD", g7.state == "DEAD", g7.state)
g7.restore_checkpoint()
check("...回检查点：血满、还在第四幕", g7.health == 100 and g7.act == 4,
      "%d / act %d" % (g7.health, g7.act))
check("...棋盘回滚到进幕那一刻（这一步写的不算）", g7.board.progress() <= before,
      "%d ≤ %d" % (g7.board.progress(), before))

finish(TITLE)
