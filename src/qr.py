# -*- coding: utf-8 -*-
"""圣坛的目标图案：一张**真**二维码（segno 生成，v1 / 纠错 L / 21×21）。

这张码开局生成一次，贯穿整局；玩家要一格一格把它复刻出来，最后是能扫的。
这里同时提供「本轮必涂格集合」——第一幕就是三个定位图案 + 暗模块，共 100 格。
"""

import random
import string

import segno

from src.config import DARK_MODULE, QR_CONTENT_LEN, QR_ERROR, QR_VERSION, TARGET_N, TARGET_OFFSET

# 去掉容易看错的 0/O/1/l/I，剩下的都是能一眼读出来的 ASCII
ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"


def random_content(rng):
    """8 位 ASCII 内容。以后换成用户给的短网址（上限 17 字符，见 config.QR_CONTENT_LEN）。"""
    return "".join(rng.choice(ALPHABET) for _ in range(QR_CONTENT_LEN))


def make_qr(content):
    """内容 → 21×21 的 0/1 矩阵。

    version 和 error **必须写死**：不写会自动选版本，选到 v2 就不是 21×21 了。
    """
    qr = segno.make(content, version=QR_VERSION, error=QR_ERROR)
    matrix = [[1 if cell else 0 for cell in row] for row in qr.matrix]
    if len(matrix) != TARGET_N:
        raise ValueError("QR size %d != %d" % (len(matrix), TARGET_N))
    return matrix


def generate_target(rng, content=None):
    """生成这一局的目标码，返回 (matrix, content)。"""
    content = content or random_content(rng)
    return make_qr(content), content


def required_cells(target=None):
    """本轮必涂格（主网格坐标）：三个定位图案各 33 格 + 暗模块 1 格 = 100 格。

    定位图案 = 7×7 外框（24 格）+ 中心 3×3（9 格）；中间那圈白不算。
    target 只用来校验（这些格子在真码里必须是黑的），不传就跳过校验。
    """
    orr, occ = TARGET_OFFSET
    cells = set()
    for r0, c0 in ((0, 0), (0, 14), (14, 0)):
        for dr in range(7):
            for dc in range(7):
                ring = dr in (0, 6) or dc in (0, 6)
                core = 2 <= dr <= 4 and 2 <= dc <= 4
                if ring or core:
                    cells.add((orr + r0 + dr, occ + c0 + dc))
    dr, dc = DARK_MODULE
    cells.add((orr + dr, occ + dc))

    if target is not None:
        for r, c in cells:
            if not target[r - orr][c - occ]:
                raise ValueError("required cell %s is white in target" % ((r, c),))
    return cells
