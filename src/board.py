# -*- coding: utf-8 -*-
"""棋盘：格子状态、统计、涂改与抹除计时。

只管「数据」，不碰任何绘制。
"""

from src.config import BLACK, ERASE_CAST, ERASING, GRID_N, TARGET_N, TARGET_OFFSET, WHITE
from src.grid import to_target

# ==== 棋盘 ====


class Board:
    def __init__(self, target):
        self.target = target                                   # 21×21 的 0/1
        self.target_total = sum(map(sum, target))              # 目标黑格总数
        self.state = [[WHITE] * GRID_N for _ in range(GRID_N)]
        self.erase_t = [[0.0] * GRID_N for _ in range(GRID_N)]
        self.flash = {}                                        # {(r,c): 剩余秒}，M3 啃食红闪
        # M1/M2 恒为 True：全网格可涂。M4 只需在 30s 时把它置 False，外围即锁死
        self.outer_open = True

    # --- 查询 ---
    def cell_ok_for_paint(self, r, c):
        if self.outer_open:
            return True
        return to_target(r, c) is not None

    def cell_ok_for_erase(self, r, c):
        # ERASING 期间既不可再涂也不可再抹，避免计时被重置
        return self.state[r][c] == BLACK and self.cell_ok_for_paint(r, c)

    def stats(self):
        """只统计 21×21 目标区，外围诱饵不加分也不扣分。"""
        correct = noise = missing = 0
        orr, occ = TARGET_OFFSET
        for tr in range(TARGET_N):
            for tc in range(TARGET_N):
                st = self.state[orr + tr][occ + tc]
                if self.target[tr][tc]:
                    if st == BLACK:
                        correct += 1
                    else:
                        missing += 1
                elif st == BLACK:
                    noise += 1
        return correct, noise, missing

    # --- 操作 ---
    def paint(self, r, c):
        """幂等：拖动时每帧都会调用，已是黑/正在抹除就直接返回。"""
        if self.state[r][c] != WHITE:
            return
        if not self.cell_ok_for_paint(r, c):
            return
        self.state[r][c] = BLACK

    def start_erase(self, r, c):
        if not self.cell_ok_for_erase(r, c):
            return
        self.state[r][c] = ERASING
        self.erase_t[r][c] = ERASE_CAST

    def force_white(self, r, c):
        """怪物啃食：无条件变白 + 红闪（M3 调用）。"""
        self.state[r][c] = WHITE
        self.erase_t[r][c] = 0.0
        self.flash[(r, c)] = 0.15

    def update(self, dt):
        for r in range(GRID_N):
            for c in range(GRID_N):
                if self.state[r][c] == ERASING:
                    self.erase_t[r][c] -= dt
                    if self.erase_t[r][c] <= 0:
                        self.state[r][c] = WHITE
        for k in list(self.flash):
            self.flash[k] -= dt
            if self.flash[k] <= 0:
                del self.flash[k]
