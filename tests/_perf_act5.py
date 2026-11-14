import time, pygame
from _act1_common import auto_mono, new_game, paint_ok, skip_intro
from src.config import VALID

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
g.spawn_rate = 12.0

t0 = time.perf_counter()
for _ in range(300):
    auto_mono(g)
    g.update(1/60)
    g.draw()
ms = (time.perf_counter() - t0) / 300 * 1000
print("第五幕 单帧 update+draw = %.2f ms（预算 16.7ms）" % ms)
