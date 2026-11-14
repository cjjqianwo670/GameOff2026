# -*- coding: utf-8 -*-
"""第二幕 · 必涂格（定时图案）验收。

第二幕的必涂格 = 第一幕 100 格 + 定时图案 6 格 = 106。
这里断言的是**结构与数字**，不是「代码自认为算对了」：
定时图案那 6 格必须逐个对上 QR 的 timing pattern 位置，且必须是真码里的黑格。
"""

import sys


import random  # noqa: E402

from _act1_common import check, finish  # noqa: E402
from src.config import TARGET_OFFSET  # noqa: E402
from src.qr import generate_target, required_cells, timing_cells  # noqa: E402

orr, occ = TARGET_OFFSET

# --- 1) 两幕的格数 ---
target, content = generate_target(random.Random(20261111))
act1 = required_cells(target, act=1)
act2 = required_cells(target, act=2)
check("第一幕必涂 = 100", len(act1) == 100, "%d" % len(act1))
check("第二幕必涂 = 106", len(act2) == 106, "%d" % len(act2))

diff = act2 - act1
check("第二幕只比第一幕多 6 格", len(diff) == 6, "%d" % len(diff))
check("第二幕是第一幕的超集（第一幕的格子一个没少）", act1 <= act2)

# --- 2) 多出来的必须正好是定时图案 ---
expected = {(orr + r, occ + c) for (r, c) in timing_cells()}
check("多出来的 6 格 = 定时图案（主网格坐标）", diff == expected,
      "差集 %s" % sorted(diff ^ expected)[:4])

# --- 3) 定时图案在 QR 坐标里的位置写死（v1 的固有结构） ---
check("定时图案 = (6,8)(6,10)(6,12)(8,6)(10,6)(12,6)",
      timing_cells() == {(6, 8), (6, 10), (6, 12), (8, 6), (10, 6), (12, 6)},
      str(sorted(timing_cells())))
check("定时图案两列（第 6 行 / 第 6 列）各 3 格",
      len([1 for r, c in timing_cells() if r == 6]) == 3
      and len([1 for r, c in timing_cells() if c == 6]) == 3)

# --- 4) 这些格子在真码里必须都是黑的（required_cells 内部也会校验） ---
all_dark = all(target[r - orr][c - occ] for (r, c) in act2)
check("106 格在真码里全是黑的", all_dark)

# --- 5) 不随内容浮动：换 20 个随机码，格数恒为 106 ---
sizes = set()
for i in range(20):
    t2, _ = generate_target(random.Random(i))
    sizes.add(len(required_cells(t2, act=2)))
check("换 20 个随机内容，第二幕恒为 106 格", sizes == {106}, str(sorted(sizes)))

check("第一幕不受影响（还是 100）",
      all(len(required_cells(generate_target(random.Random(i))[0], act=1)) == 100
          for i in range(5)))

finish("第二幕 · 必涂格（定时图案）")
