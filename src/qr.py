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


def timing_cells():
    """定时图案（timing pattern）：QR 第 6 行 / 第 6 列上黑白交替的黑格。

    v1（21×21）里只有 6 格，正好夹在定位图案之间：
        (6,8) (6,10) (6,12)   +   (8,6) (10,6) (12,6)
    坐标是 **QR 矩阵坐标**（0~20），用的时候要加 TARGET_OFFSET。
    """
    cells = set()
    for i in range(8, 13):
        if i % 2 == 0:
            cells.add((6, i))
            cells.add((i, 6))
    return cells


# 格式信息（format information）在 QR 矩阵里的 30 个位置：**两份，各 15 位，内容完全相同**。
# 抄的是 QR 规范里的位序坐标（v1 专用，别套到别的版本上）：
#   第 1 份贴着左上定位图案（行 8 / 列 8 的「L」）；
#   第 2 份被拆成两段：右上（行 8，列 13~20）+ 左下（列 8，行 14~20）。
# (8,6) 和 (6,8) 是定时图案，(13,8) 是暗模块 —— 它们都不在这里面，别混进来。
FORMAT_COPY_1 = ((8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 7), (8, 8),
                 (7, 8), (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8))
FORMAT_COPY_2 = ((8, 20), (8, 19), (8, 18), (8, 17), (8, 16), (8, 15), (8, 14), (8, 13),
                 (20, 8), (19, 8), (18, 8), (17, 8), (16, 8), (15, 8), (14, 8))


def format_cells():
    """格式信息的 30 个位置（QR 坐标，0~20）。14~16 个是黑的，看这一局的掩码。"""
    return set(FORMAT_COPY_1) | set(FORMAT_COPY_2)


def format_dark_cells(target):
    """格式信息里**该是黑的**那些（主网格坐标）。第三幕老者写的就是这些。

    15 位里黑格只有 4 种可能（5/6/9/10），两份合计 10~20 格 —— 所以第三幕的必涂格
    是 106 + 10~20，**一局之内固定，但不同局不一样**（取决于掩码）。
    """
    orr, occ = TARGET_OFFSET
    return {(orr + r, occ + c) for r, c in format_cells() if target[r][c]}


def required_cells(target=None, act=1):
    """本轮必涂格（主网格坐标）。

    第一幕：三个定位图案各 33 格 + 暗模块 1 格 = **100**
    第二幕：再加定时图案 6 格 = **106**（定时图案是 QR 的固有结构，位置和数量写死不浮动）
    第三幕：再加格式信息里该黑的 10~20 格 = **116~126**（取决于掩码，所以必须传 target）

    target 只用来校验（这些格子在真码里必须是黑的），不传就跳过校验。
    ⚠️ act>=3 必须传 target：格式信息有一半是白的，不传就分不出哪些该算必涂格。
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

    if act >= 2:
        for r, c in timing_cells():
            cells.add((orr + r, occ + c))

    if act >= 3:
        if target is None:
            raise ValueError("act>=3 需要 target：格式信息里哪些格该黑由这一局的掩码决定")
        cells |= format_dark_cells(target)

    if target is not None:
        for r, c in cells:
            if not target[r - orr][c - occ]:
                raise ValueError("required cell %s is white in target" % ((r, c),))
    return cells
