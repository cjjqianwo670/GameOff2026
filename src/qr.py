# -*- coding: utf-8 -*-
"""目标图案：程序化生成 21×21「形似 QR」的 0/1 矩阵。

想换图案风格（换密度、加新的视觉符号）只改这个文件。
"""

from src.config import ALPHA_MIN, ALPHA_TRY, DARK_MODULE, TARGET_N

# ==== 目标图案 ====


def generate_target(rng, n=TARGET_N):
    """程序化生成 21×21「形似 QR」的 0/1 矩阵：保留定位图案/时序线/暗模块，信息区随机。

    不用真 QR 库（每局都长一样、密度不可控）。密度只做下限保护：信息区按 0.5 填，
    期望约 50%（≈220 格，对上 §14）；太稀就重摇，重摇有上限并取最密兜底，绝不递归。
    """
    floor = n * n * ALPHA_MIN
    best, best_cnt = None, -1
    for _ in range(ALPHA_TRY):
        m = _build_qr_like(rng, n)
        cnt = sum(map(sum, m))
        if cnt > best_cnt:
            best, best_cnt = m, cnt
        if cnt >= floor:
            return m
    return best


def _build_qr_like(rng, n):
    m = [[0] * n for _ in range(n)]
    reserved = [[False] * n for _ in range(n)]

    # (1) 三个 7×7 定位图案，连同外围 1 格白色分隔带一起标记 reserved
    for r0, c0 in ((0, 0), (0, n - 7), (n - 7, 0)):
        for r in range(r0 - 1, r0 + 8):
            for c in range(c0 - 1, c0 + 8):
                if 0 <= r < n and 0 <= c < n:
                    reserved[r][c] = True
        for dr in range(7):
            for dc in range(7):
                ring = dr in (0, 6) or dc in (0, 6)
                core = 2 <= dr <= 4 and 2 <= dc <= 4
                m[r0 + dr][c0 + dc] = 1 if (ring or core) else 0

    # (2) 时序线：第 6 行 / 第 6 列，一黑一白交错
    for i in range(n):
        if not reserved[6][i]:
            m[6][i] = 1 if i % 2 == 0 else 0
            reserved[6][i] = True
        if not reserved[i][6]:
            m[i][6] = 1 if i % 2 == 0 else 0
            reserved[i][6] = True

    # (3) 暗模块（QR 规范里的固定黑点），坐标与 config.DARK_MODULE 同源
    dr, dc = DARK_MODULE
    m[dr][dc] = 1
    reserved[dr][dc] = True

    # (4) 信息区随机填充
    for r in range(n):
        for c in range(n):
            if not reserved[r][c]:
                m[r][c] = 1 if rng.random() < 0.50 else 0
    return m
