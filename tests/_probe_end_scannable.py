# -*- coding: utf-8 -*-
"""证明终幕那张卡**真的就是一张这张码**：从截图里把 21×21 逐格采回来，和 segno 的矩阵逐位比。"""
import os
import pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro, SHOT_DIR
from src.config import VALID, WHITE, QR_CONTENT, C_PAPER
from src.qr import ERROR_TOLERANCE, make_qr
from src.grid import cell_center

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
for (r, c) in sorted(g.must):
    if g.board.state[r][c] != VALID:
        paint_ok(g, r, c)
g.start_act5()
skip_intro(g)
g.spawn_rate = 0.0
g.monsters.clear(); g.purples.clear(); g.spawn_purple = lambda: None
g.update_yellows = lambda dt: None
while g.act5_errors() > ERROR_TOLERANCE:
    for k, mods in g.cw_modules.items():
        if any(g.board.state[r][c] != (VALID if dark else WHITE) for (r, c, dark) in mods):
            for (r, c, dark) in mods:
                if dark:
                    g.board.state[r][c] = VALID
            break
g.player.cell = (12, 12)
g.player.pos.update(cell_center(12, 12))
for _ in range(int(4.5 * 60)):
    auto_mono(g)
    g.update(1 / 60)
g.dlg_t = 0.0
g.draw()

from src.ui import PLAY_W, WINDOW_H
module, quiet = 10, 4
n = 21
side = (n + quiet * 2) * module
x0 = PLAY_W // 2 - side // 2
y0 = WINDOW_H // 2 - 80 - side

# 1) 静区必须是纯纸色（一条都没被别的东西压到）
bad_quiet = 0
for d in range(quiet * module):
    for t in range(side):
        for (px, py) in ((x0 + t, y0 + d), (x0 + t, y0 + side - 1 - d),
                         (x0 + d, y0 + t), (x0 + side - 1 - d, y0 + t)):
            if g.screen.get_at((px, py))[:3] != C_PAPER:
                bad_quiet += 1
print("静区被污染像素:", bad_quiet)

# 2) 逐格采样中心像素，重建矩阵
truth = make_qr(QR_CONTENT)
got = [[0] * n for _ in range(n)]
for r in range(n):
    for c in range(n):
        px = x0 + (c + quiet) * module + module // 2
        py = y0 + (r + quiet) * module + module // 2
        col = g.screen.get_at((px, py))[:3]
        got[r][c] = 1 if col[0] < 128 else 0

diff = sum(1 for r in range(n) for c in range(n) if got[r][c] != truth[r][c])
print("逐格比对：%d / 441 个模块不一致" % diff)
print("内容:", QR_CONTENT, "| 尺寸:", side, "px | 每格", module, "px | 静区", quiet, "格")
print("采样重建 == segno 矩阵:", got == truth)
print("SCANNABLE" if diff == 0 and bad_quiet == 0 else "NOT SCANNABLE")
