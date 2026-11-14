# -*- coding: utf-8 -*-
"""步骤 2 验收：qr.py 换成 segno 真码（v1 / 纠错 L / 21×21）。"""

import os
import random

import pygame

from _act1_common import SHOT_DIR, check, finish, new_game, shot
from src.config import DARK_MODULE, QR_CONTENT, TARGET_N
from src.qr import generate_target, make_qr, required_cells

TITLE = "STEP 2 · SEGNO REAL QR"

rng = random.Random(20261110)
sizes, counts, contents = set(), [], set()
dark_mod_ok = True
roundtrip_ok = True
for i in range(100):
    m, content = generate_target(rng)
    sizes.add((len(m), len(m[0])))
    counts.append(sum(map(sum, m)))
    contents.add(content)
    if m[DARK_MODULE[0]][DARK_MODULE[1]] != 1:
        dark_mod_ok = False
    if make_qr(content) != m:
        roundtrip_ok = False

check("连生成 100 次都是 21×21", sizes == {(21, 21)}, str(sizes))
check("黑格数都在 190~260 之间", min(counts) >= 190 and max(counts) <= 260,
      "min %d / max %d / avg %.1f" % (min(counts), max(counts), sum(counts) / len(counts)))
check("暗模块 (13,8) 恒为黑（v1 规范位置）", dark_mod_ok)
check("同一内容重生成得到同一张码（segno 确定性）", roundtrip_ok)
check("内容是固定的（%r）" % QR_CONTENT, contents == {QR_CONTENT},
      "%d 种：%s" % (len(contents), sorted(contents)[:3]))
check("...全大写 + 空格（走字母数字模式，v1-L 能放 25 个）",
      QR_CONTENT.isupper() and QR_CONTENT.replace(" ", "").isalnum(),
      "%d 字符" % len(QR_CONTENT))
check("...所以每一局的棋盘都一模一样（确定性）",
      all(m == make_qr(QR_CONTENT) for m in [generate_target(rng)[0] for _ in range(3)]), "")

# segno 默认会给短内容**偷偷升纠错等级**（L → Q），那样「7 个纠错码字 / 只能废 3 块」就不成立了
import segno
q_boost = segno.make(QR_CONTENT, version=1, error="l")
q_plain = segno.make(QR_CONTENT, version=1, error="l", boost_error=False)
check("纠错等级恒为 L（boost_error=False 真的关掉了）", q_plain.error == "l".upper() or q_plain.error == "L",
      "boost 开=%s / 关=%s" % (q_boost.error, q_plain.error))
check("...而默认行为确实会升到 L 以上（这个坑是真的）", q_boost.error != q_plain.error,
      "%s vs %s" % (q_boost.error, q_plain.error))

# 容量：v1-L 字母数字 25 字符；一旦有小写就掉到字节模式（17）
n = len(QR_CONTENT)
check("...内容没超过 v1-L 的字母数字上限（25）", n <= 25, "%d 字符" % n)
import segno as _s
try:
    _s.make("A" * 25, version=1, error="l", boost_error=False)
    cap_ok = True
except Exception:
    cap_ok = False
try:
    _s.make("A" * 26, version=1, error="l", boost_error=False)
    over_ok = False
except Exception:
    over_ok = True
check("...实测上限正好是 25（26 个就溢出版本 1）", cap_ok and over_ok,
      "25 通过=%s / 26 溢出=%s" % (cap_ok, over_ok))

# 必涂格集合：三个定位图案 + 暗模块 = 100，且全在真码的黑格上
g = new_game()
must = g.must_all                       # 整幕合计（第一幕分两波，g.must 开局只有 33）
orr, occ = 2, 2
check("必涂格正好 100 个且无重复", len(must) == 100 and len(set(must)) == 100, "%d" % len(must))
check("必涂格全是目标矩阵里的黑格",
      all(g.target[r - orr][c - occ] == 1 for (r, c) in must))
check("required_cells() 与 must_all 一致", required_cells(g.target) == must)
check("第一波 = 左下定位图案的 33 格", len(g.must) == 33 and g.must <= must, "%d" % len(g.must))

# 出图：给手机扫的样张（每格 20px + 4 格静区，纯黑白）
q, content = generate_target(random.Random(7))
quiet, cell = 4, 20
side = (TARGET_N + quiet * 2) * cell
surf = pygame.Surface((side, side))
surf.fill((255, 255, 255))
for r in range(TARGET_N):
    for c in range(TARGET_N):
        if q[r][c]:
            surf.fill((0, 0, 0), pygame.Rect((c + quiet) * cell, (r + quiet) * cell, cell, cell))
os.makedirs(SHOT_DIR, exist_ok=True)
out = os.path.join(SHOT_DIR, "02_qr_scan_me.png")
pygame.image.save(surf, out)
print("  扫码样张 ->", out, "| content =", content)

p = shot(g, "02_board_with_qr.png")
print("  棋盘截图 ->", p)
finish(TITLE)
