# -*- coding: utf-8 -*-
"""第三幕 STEP 17 验收：格式信息「难涂」+ 黄怪加快。

作者 2026-11-13 定的两件事：
  · 黄怪刷新加快（`YELLOW_SPAWN_PER_MIN` 5 → 7）
  · 格式信息要难涂：老者每格停 0.9s（原 0.35），玩家补也得**按住 J 满 0.8s**
"""

import pygame

from _act1_common import auto_mono, check, finish, new_game, paint_ok
from src import story
from src.config import (
    FORMAT_HOLD_TIME, SC_J, SC_M, SCRIBE_PAUSE, VALID, WHITE, YELLOW_SPAWN_PER_MIN
)
from src.grid import cell_center

TITLE = "STEP 17 · ACT 3 (FORMAT CELLS NEED A LONG PRESS / YELLOW FASTER)"

ENTER = 40


def to_act3():
    g = new_game()
    for (r, c) in sorted(g.board.must):
        paint_ok(g, r, c)
    g.start_act2()
    for (r, c) in sorted(g.must):
        if g.board.state[r][c] != VALID:
            paint_ok(g, r, c)
    g.start_act3()
    g.has_sword = True
    for _ in range(400):
        auto_mono(g)
        g.update(1 / 60)
        g.dlg_t = 99.0
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
        if g.state != "DIALOG":
            break
    g.spawn_rate = 0.0                            # 红怪会啃格，别让它干扰断言
    g.monsters.clear()
    g.spawn_purple = lambda: None                 # 紫怪会清整行
    g.purples.clear()
    return g


def white_format_cell(g):
    return sorted(c for c in g.format_cells if g.board.state[c[0]][c[1]] == WHITE)


def stand(g, r, c):
    g.player.cell = (r, c)
    g.player.pos.update(cell_center(r, c))


# ==================== 1. 常量 ====================
check("黄怪每分钟 7 只（原 5）", YELLOW_SPAWN_PER_MIN == 7.0, "%.1f" % YELLOW_SPAWN_PER_MIN)
check("...折算 8.6 秒一只", abs(60.0 / YELLOW_SPAWN_PER_MIN - 8.571) < 0.01,
      "%.2fs" % (60.0 / YELLOW_SPAWN_PER_MIN))
check("老者站定后停 0.9s 才落笔（原 0.35）", SCRIBE_PAUSE == 0.9, "%.2f" % SCRIBE_PAUSE)
check("玩家补格式格要按住 0.8s", FORMAT_HOLD_TIME == 0.8, "%.2f" % FORMAT_HOLD_TIME)

# ==================== 2. 黄怪按新速率到场 ====================
g = to_act3()
g.yellows = []
g.yellow_spawned = 1                           # 已过首只延迟，量的是**间隔**
g.yellow_t = 0.0
t = 0.0
while not g.yellows and t < 15:
    auto_mono(g)
    g.update(1 / 60)
    t += 1 / 60
need = 60.0 / YELLOW_SPAWN_PER_MIN
check("下一只黄怪 8.6 秒到场（不是原来的 12 秒）", abs(t - need) < 0.15,
      "%.2fs / 期望 %.2fs" % (t, need))
check("...比原来快（12 → 8.6）", t < 10.0, "%.2fs" % t)
g.yellows.clear()
g.yellow_spawned = 99                          # 后面的测试不要黄怪

# ==================== 3. 老者：一格 0.9 秒 ====================
g = to_act3()
g.yellow_spawned = 99
target = white_format_cell(g)[0]
r, c = target
g.oldman.pos.update(cell_center(r, c))         # 已经站到格子上了
g.scribe_target = (r, c)
g.scribe_writing = True
g.scribe_t = 0.0
g.scribe_said = True                           # 别让他那句心声把世界冻住
t = 0.0
while g.board.state[r][c] != VALID and t < 4:
    auto_mono(g)
    g.update(1 / 60)
    t += 1 / 60
check("老者落笔要等满 SCRIBE_PAUSE", t >= SCRIBE_PAUSE - 0.02, "%.2fs" % t)
check("...之前 0.35s 就写了，现在明显慢", t > 0.6, "%.2fs" % t)
check("...最后还是写上了（不是永远写不动）", g.board.state[r][c] == VALID, "state %d" % g.board.state[r][c])
check("...计时用的是 SCRIBE_PAUSE", abs(t - SCRIBE_PAUSE) < 0.1, "%.2fs" % t)

# ==================== 4. 玩家：格式格要按住 J ====================
g = to_act3()
g.yellow_spawned = 99
g.oldman.down = True                           # 让老者停笔，只测玩家
rest = white_format_cell(g)
check("第三幕还有白着的格式格可写", len(rest) > 0, "%d 格" % len(rest))
r, c = rest[0]
stand(g, r, c)
g.board.reveal_around(r, c)                    # 先照出灰域（不然是脏格）

g.input.held.add(SC_J)
for _ in range(int(0.5 * 60)):                 # 按 0.5s
    auto_mono(g)
    g.update(1 / 60)
check("按住 0.5s 还没写上去（普通格早就成了）", g.board.state[r][c] == WHITE,
      "state %d" % g.board.state[r][c])
check("...但进度已经涨了（脚下那圈）", 0 < g.fill_t < FORMAT_HOLD_TIME, "%.2f" % g.fill_t)
check("...第一次碰到格式格会教一句「按住 J」", g.hold_said and g.hint_text == story.HINT_FORMAT_HOLD,
      repr(g.hint_text))

t = 0.5
while g.board.state[r][c] != VALID and t < 3:
    auto_mono(g)
    g.update(1 / 60)
    t += 1 / 60
g.input.held.discard(SC_J)
check("按满 0.8s 才落笔", g.board.state[r][c] == VALID, "%.2fs" % t)
check("...总时长就是 FORMAT_HOLD_TIME", abs(t - FORMAT_HOLD_TIME) < 0.08, "%.2fs" % t)
check("...写完进度归零（不留半截）", g.fill_t == 0.0, "%.2f" % g.fill_t)

# ==================== 5. 松手 / 换格会清进度 ====================
g = to_act3()
g.yellow_spawned = 99
g.oldman.down = True
r, c = white_format_cell(g)[0]
stand(g, r, c)
g.board.reveal_around(r, c)
g.input.held.add(SC_J)
for _ in range(int(0.5 * 60)):
    auto_mono(g)
    g.update(1 / 60)
held = g.fill_t
g.input.held.discard(SC_J)
for _ in range(int(0.1 * 60)):
    auto_mono(g)
    g.update(1 / 60)
check("松手 → 进度直接归零（不是慢慢退）", held > 0.4 and g.fill_t == 0.0,
      "%.2f → %.2f" % (held, g.fill_t))
check("...格子还是白的", g.board.state[r][c] == WHITE, "state %d" % g.board.state[r][c])

# ==================== 5b. 被咬 → 这一笔断掉（作者 2026-11-13）====================
from src.entities import YellowOne          # noqa: E402

g = to_act3()
g.yellow_spawned = 99
g.update_scribe = lambda dt: None           # 老头这一节不写，免得他抢先补掉这一格
r, c = white_format_cell(g)[0]
stand(g, r, c)
g.board.reveal_around(r, c)
g.input.held.add(SC_J)
for _ in range(int(0.3 * 60)):              # 先攒 0.3 秒
    auto_mono(g)
    g.update(1 / 60)
before = g.fill_t

# 贴脸放一只已经盯上玩家的黄怪（挨过剑的才会盯玩家；老头没倒，所以它们默认打老头）
y = YellowOne((g.player.pos.x + 6, g.player.pos.y + 6))
y.aggro_t = 6.0
g.yellows = [y]
hp0 = g.health
t = 0.0
while g.health == hp0 and t < 1.0:          # 咬到就停，别让它咬第二口
    auto_mono(g)
    g.update(1 / 60)
    t += 1 / 60
g.input.held.discard(SC_J)
check("黄怪先咬到了玩家", g.health < hp0, "hp %d → %d" % (hp0, g.health))
check("...正在制造的黑域被打断（进度归零）", before > 0.2 and g.fill_t == 0.0,
      "%.2f → %.2f" % (before, g.fill_t))
check("...那一格还是白的（没有被半截写掉）", g.board.state[r][c] == WHITE,
      "state %d" % g.board.state[r][c])

# 断笔之后必须重新按满 0.8 秒
g.yellows = []
g.input.held.add(SC_J)
for _ in range(int(0.6 * 60)):              # 只按 0.6 秒：不够
    auto_mono(g)
    g.update(1 / 60)
check("断笔后按 0.6 秒还写不上（得重新数满 0.8）", g.board.state[r][c] == WHITE,
      "state %d / fill %.2f" % (g.board.state[r][c], g.fill_t))
for _ in range(int(0.3 * 60)):
    auto_mono(g)
    g.update(1 / 60)
g.input.held.discard(SC_J)
check("...再按住到 0.8 秒才写成", g.board.state[r][c] == VALID, "state %d" % g.board.state[r][c])

g.break_pen()
check("断笔的口子只干两件事：清进度 + 清归属格",
      g.fill_t == 0.0 and g.fill_cell is None, "%.2f / %s" % (g.fill_t, g.fill_cell))

# ==================== 6. 进度不会串到下一格 ====================
g = to_act3()
g.yellow_spawned = 99
g.oldman.down = True
pairs = [(a, (a[0], a[1] + 1)) for a in white_format_cell(g) if (a[0], a[1] + 1) in g.format_cells]
check("找得到一对相邻的格式格", len(pairs) > 0, "%d 对" % len(pairs))
a, b = pairs[0]
g.board.reveal_around(*a)
g.board.reveal_around(*b)
stand(g, *a)
g.input.held.add(SC_J)
for _ in range(int(0.5 * 60)):                 # 在 A 上按半秒，不写满
    auto_mono(g)
    g.update(1 / 60)
stand(g, *b)                                   # 挪到 B，继续按 0.3 秒
for _ in range(int(0.3 * 60)):
    auto_mono(g)
    g.update(1 / 60)
g.input.held.discard(SC_J)
check("在 A 攒的进度不会带到 B（B 还是白的）", g.board.state[b[0]][b[1]] == WHITE,
      "state %d" % g.board.state[b[0]][b[1]])
check("...B 的进度从 0 重新数", g.fill_t <= 0.35, "%.2f" % g.fill_t)

# ==================== 6b. 普通格仍然一按就成 ====================
g = to_act3()
g.yellow_spawned = 99
g.oldman.down = True
plain = sorted(cell for cell in g.must if cell not in g.format_cells)
check("还有普通的必涂格", len(plain) > 0, "%d 格" % len(plain))
r, c = plain[0]
g.board.state[r][c] = WHITE                    # 造一格「被怪啃掉」的普通格
stand(g, r, c)
g.board.reveal_around(r, c)
g.input.held.add(SC_J)
for _ in range(2):                             # 两帧
    auto_mono(g)
    g.update(1 / 60)
g.input.held.discard(SC_J)
check("普通格按住两帧就写上了（没有被拖慢）", g.board.state[r][c] == VALID,
      "state %d" % g.board.state[r][c])

# ==================== 7. 地图摊开时不能写（也不留进度）====================
g = to_act3()
g.yellow_spawned = 99
g.oldman.down = True
r, c = white_format_cell(g)[0]
stand(g, r, c)
g.board.reveal_around(r, c)
g.has_map = True                                                      # 没捡到地图按 M 是没反应的
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=SC_M))   # 摊开地图
check("地图确实摊开了", g.map_open, "map_open=%s" % g.map_open)
g.input.held.add(SC_J)
for _ in range(int(1.5 * 60)):
    auto_mono(g)
    g.update(1 / 60)
g.input.held.discard(SC_J)
check("捧着地图时按住 J 也写不了", g.board.state[r][c] == WHITE, "state %d" % g.board.state[r][c])
check("...也不会偷偷攒进度", g.fill_t == 0.0, "%.2f" % g.fill_t)

finish(TITLE)
