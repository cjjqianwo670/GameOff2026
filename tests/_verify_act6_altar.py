# -*- coding: utf-8 -*-
"""第二圣坛验收（2026-11-25）：第五幕之后把老者的码补完。

这一幕没有怪、没有侵蚀、没有脏格：
    骨架 124 格预先写黑（他记得结构），玩家只补数据区 106 格（他记不住的「字」）。
"""

import pygame

from _act1_common import auto_mono, check, finish, new_game, paint_ok, shot, skip_intro
from src import qr, story
from src.config import OLD_MAN_CODE, SC_K, SCAN_TIME, VALID, WHITE
from src.grid import cell_center

TITLE = "ACT 6 · THE SECOND ALTAR"
ENTER = 40


def ev(sc):
    return pygame.event.Event(pygame.KEYDOWN, key=0, scancode=sc)


def run(g, secs):
    for _ in range(max(1, int(secs * 60))):
        auto_mono(g)
        g.update(1 / 60)


def put(g, cell):
    g.player.cell = cell
    g.player.pos.update(cell_center(*cell))


def drive_to(g, state, limit=4000):
    for _ in range(limit):
        auto_mono(g)
        g.update(1 / 60)
        if g.state == state:
            return True
    return False


# ==================== 1. 从第五幕结局页进第二圣坛 ====================
g = new_game()
skip_intro(g)
g.act = 5
g.state = "END"
g.handle_event(ev(ENTER))
check("第五幕结局页回车 → 第二圣坛", g.state == "ALTAR2" and g.act == 6,
      "%s / %d" % (g.state, g.act))
check("目标码 = 老者的码（HE REMEMBERS YOU）", g.target == qr.make_qr(OLD_MAN_CODE),
      repr(g.qr_content))
check("结局字幕用的内容换成老者的码", g.qr_content == OLD_MAN_CODE, repr(g.qr_content))

skel = qr.structural_black_cells(g.target)
check("骨架 124 格已经预先写黑", len(skel) == 124
      and all(g.board.state[r][c] == VALID for (r, c) in skel), "%d" % len(skel))
check("本幕只补数据区 106 格", len(g.must) == 106, "%d" % len(g.must))
check("开场进度 0 / 106", g.board.progress() == 0, "%d" % g.board.progress())

# ==================== 2. 没有威胁 ====================
run(g, 3.0)
check("第二圣坛没有怪", not g.monsters and not g.purples and not g.greens,
      "%d / %d / %d" % (len(g.monsters), len(g.purples), len(g.greens)))
check("不掉血", g.health == 100, "%d" % g.health)
check("不产界丝", not g.thread_on_cell)
shot(g, "60_altar2_arrival.png")

# 骨架是这张码的锚：第二圣坛的 K 不许碰它（擦掉就扫不出来）
skel_cell = sorted(skel)[0]
put(g, skel_cell)
g.input.held.add(SC_K)
g.update(1 / 60)
g.input.held.discard(SC_K)
check("骨架不能被 K 擦掉", g.board.state[skel_cell[0]][skel_cell[1]] == VALID,
      "%d" % g.board.state[skel_cell[0]][skel_cell[1]])

# ==================== 3. 扫的规则：没照不写、也不脏 ====================
r, c = sorted(g.must)[0]
put(g, (r, c))
g.hold_paint(1 / 60)
check("没照就按 J：不写、不脏", g.board.state[r][c] == WHITE and g.board.stains == 0,
      "%d / %d" % (g.board.state[r][c], g.board.stains))
g.board.reveal_around(r, c, radius=3)
g.hold_paint(1 / 60)
check("照了再按 J：写成一格", g.board.state[r][c] == VALID, "%d" % g.board.state[r][c])

# ==================== 4. 写满 → 扫描 → 老者回来 ====================
for (rr, cc) in sorted(g.must):
    paint_ok(g, rr, cc)
check("数据区 106 格填满", g.board.progress() == 106, "%d" % g.board.progress())
g.update(1 / 60)
check("写满 → 开始扫描", g.state == "ALTAR2_SCAN", g.state)

for _ in range(int(SCAN_TIME * 60) + 60):
    g.update(1 / 60)
    if g.state == "ALTAR2_BACK":
        break
check("扫描完 → 老者回来", g.state == "ALTAR2_BACK"
      and g.oldman is not None and not g.oldman.gone, str(g.state))
check("...他说的是那句告别", g.mono_text == story.ACT6_BACK, repr(g.mono_text))
check("...此时血还是满的", g.health == 100, "%d" % g.health)

for _ in range(20):
    auto_mono(g)
    g.update(1 / 60)
    if g.state == "END":
        break
check("说完 → 结局页", g.state == "END", g.state)
check("...标题是 THE END", g.banner_text == story.ACT6_END_TITLE, repr(g.banner_text))
check("...读出来的是他的码", g.end_line == story.END_LINE % OLD_MAN_CODE, repr(g.end_line))
shot(g, "62_altar2_end.png")
g.handle_event(ev(ENTER))
check("...回车回标题", g.state == "TITLE", g.state)
g.handle_event(ev(ENTER))
check("重新开局：上一局的结局字幕清空", g.end_line == "", repr(g.end_line))

finish(TITLE)
