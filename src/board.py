# -*- coding: utf-8 -*-
"""棋盘：格子状态、统计、涂改与抹除计时。

只管「数据」，不碰任何绘制。
"""

from src.config import (
    BLACK, ERASE_CAST, ERASING, GRID_N, SEEN_FLASH_TIME, SEEN_RADIUS, TARGET_N, TARGET_OFFSET, WHITE
)
from src.grid import to_target

# ==== 棋盘 ====


class Board:
    def __init__(self, target, seen_on=False):
        self.target = target                                   # 21×21 的 0/1
        self.target_total = sum(map(sum, target))              # 目标黑格总数
        self.state = [[WHITE] * GRID_N for _ in range(GRID_N)]
        self.erase_t = [[0.0] * GRID_N for _ in range(GRID_N)]
        self.flash = {}                                        # {(r,c): 剩余秒}，M3 啃食红闪
        # M1/M2 恒为 True：全网格可涂。M4 只需在 30s 时把它置 False，外围即锁死
        self.outer_open = True

        # ---- 记忆层 ----
        # seen[r][c] = 这一格的灰影亮没亮过。只照亮过的地方，其余一片白。
        # 关掉时全部预置 True，等于老行为：整张目标随时可见（is_seen 永远为真）
        self.seen_on = seen_on
        self.seen = [[not seen_on] * GRID_N for _ in range(GRID_N)]
        self.seen_flash = {}                                   # {(r,c): 剩余秒}，刚点亮那一下的细边

    # --- 查询 ---
    def is_seen(self, r, c):
        """这一格的灰影该不该显示。关掉记忆层时恒为 True。"""
        return self.seen[r][c]

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

    def mark_seen(self, r, c, flash=True):
        """玩家站在 (r,c)：以他为中心的 (2R+1)² 一片灰影永久亮起。

        这是「记忆」变成机制的地方 —— 走过才知道，没走过就是白的。
        返回新点亮了几格（供测试断言用）。关掉记忆层时什么都不做。
        """
        if not self.seen_on:
            return 0
        k = SEEN_RADIUS
        n = 0
        for rr in range(max(0, r - k), min(GRID_N, r + k + 1)):
            srow = self.seen[rr]
            for cc in range(max(0, c - k), min(GRID_N, c + k + 1)):
                if not srow[cc]:
                    srow[cc] = True
                    n += 1
                    if flash:
                        self.seen_flash[(rr, cc)] = SEEN_FLASH_TIME
        return n

    def best_row(self):
        """紫怪专用：已涂对的目标黑格数最多的一行，返回整张网格的行号。

        全 0（还没开始涂）时返回 None，让怪退回"最近黑格"的老行为。
        这条规则就是这只怪的全部意义：它不挑随机一行，它挑你干得最好的那一行。
        整行清完该行自然归零，下一次就轮到别的行，不会死循环。
        """
        orr, occ = TARGET_OFFSET
        best, best_n = None, 0
        for tr in range(TARGET_N):
            row = self.target[tr]
            n = 0
            for tc in range(TARGET_N):
                if row[tc] and self.state[orr + tr][occ + tc] == BLACK:
                    n += 1
            if n > best_n:
                best, best_n = orr + tr, n
        return best

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

    def clear_row(self, r):
        """紫怪：把这一整行的黑格全部变白，返回清掉几格（供调试/测试看）。

        只动 BLACK 格：白格本来就是白的；灰色提示是从 target 推出来的，
        这些格子清完又变回「该黑且还白」，提示会自动重新出现，
        所以玩家的这一行等于白涂了，必须重来 —— 这就是这只怪的意义。
        """
        n = 0
        for c in range(GRID_N):
            if self.state[r][c] == BLACK:
                self.force_white(r, c)       # 复用：变白 + 该格红闪
                n += 1
        return n

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
        for k in list(self.seen_flash):
            self.seen_flash[k] -= dt
            if self.seen_flash[k] <= 0:
                del self.seen_flash[k]
