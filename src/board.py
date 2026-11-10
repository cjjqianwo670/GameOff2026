# -*- coding: utf-8 -*-
"""棋盘：格子状态、异象灰域、脏格计数、涂改与抹除计时。

只管「数据」，不碰任何绘制。四条状态：
    WHITE   白（没涂）
    VALID   有效黑域（the Dark）—— 必涂格上的黑，或平地上的诱饵黑，都算它
    DIRTY   脏黑（a stain）—— 圣坛内涂在非必涂格上，黑白相间，必须 K 擦掉
    ERASING 抹除中（0.25s 塌陷）
"""

from src.config import (
    DIRTY, ERASE_CAST, ERASING, GRID_N, MIRAGE_FADE, MIRAGE_RADIUS, STAIN_LIMIT, TARGET_N, VALID, WHITE
)
from src.grid import to_target

# ==== 棋盘 ====


class Board:
    def __init__(self, target, must):
        self.target = target                                   # 21×21 的 0/1 真码
        self.must = set(must)                                  # 本轮必涂格（主网格坐标）
        self.state = [[WHITE] * GRID_N for _ in range(GRID_N)]
        self.erase_t = [[0.0] * GRID_N for _ in range(GRID_N)]
        self.reveal = [[0.0] * GRID_N for _ in range(GRID_N)]   # 异象灰域剩余秒
        # 地图道具用：这一格**被异象照过**（灰域退了也还记着）
        self.seen = [[False] * TARGET_N for _ in range(TARGET_N)]
        self.flash = {}                                        # {(r,c): 剩余秒}，被怪啃那一下的红闪
        self.stains = 0                                        # ⚠️ 本幕**累计**涂错格数，擦掉不返还

    # --- 查询 ---
    def in_altar(self, r, c):
        """圣坛 = 中间 21×21；外面叫平地（the plain）。"""
        return to_target(r, c) is not None

    def is_dark(self, r, c):
        return self.state[r][c] == VALID

    def progress(self):
        """已复原本轮必涂格数。"""
        n = 0
        for (r, c) in self.must:
            if self.state[r][c] == VALID:
                n += 1
        return n

    def is_complete(self):
        """完成条件：100 格全为有效黑域。

        脏格**不再**卡通关：超出额度改为每次扣血（见 game.paint_here），
        所以手滑的代价是命，不是「这局废了」。
        """
        return self.progress() >= len(self.must)

    def stains_over(self):
        """超出额度的脏格数（0 表示还在额度内）。"""
        return max(0, self.stains - STAIN_LIMIT)

    def dark_cells(self):
        """场上还有哪些有效黑域（红怪找吃的用）。"""
        return [(r, c) for r in range(GRID_N) for c in range(GRID_N) if self.state[r][c] == VALID]

    def revealed(self, r, c):
        """这一格此刻该不该画灰域。"""
        return self.reveal[r][c] > 0 and self.state[r][c] == WHITE

    # --- 操作 ---
    def paint(self, r, c):
        """涂黑脚下这一格。返回 "valid" / "dirty" / "plain" / None（没变化）。

        圣坛内必涂格 → VALID
        圣坛内其他格 → DIRTY，累计计数 +1（不管有没有被异象照过，蒙涂也算）
        平地（诱饵）  → VALID，不参与判定，也不计数
        """
        if self.state[r][c] != WHITE:
            return None
        if self.in_altar(r, c):
            if (r, c) in self.must:
                self.state[r][c] = VALID
                return "valid"
            self.state[r][c] = DIRTY
            self.stains += 1
            return "dirty"
        self.state[r][c] = VALID
        return "plain"

    def start_erase(self, r, c):
        """K：0.25 秒塌陷。脏格的累计计数**不减**（擦了也不返还）。"""
        if self.state[r][c] not in (VALID, DIRTY):
            return False
        self.state[r][c] = ERASING
        self.erase_t[r][c] = ERASE_CAST
        return True

    def force_white(self, r, c):
        """红怪啃食：无条件变白 + 红闪。"""
        self.state[r][c] = WHITE
        self.erase_t[r][c] = 0.0
        self.flash[(r, c)] = 0.15

    def reveal_around(self, r, c):
        """异象：以 (r,c) 为中心 (2R+1)² 照出灰域，返回新照亮的格数。

        - 只在圣坛内生效；站在平地上按 Shift 一个灰域都没有（叙事设定 + 玩法边界）
        - 只照「该黑且还白」的格子：已经涂黑的、本来就不该黑的，照了也没意义
        - 已经照过的格子会把 5 秒重新充满（再照一次就是再看一眼）
        """
        if not self.in_altar(r, c):
            return 0
        k = MIRAGE_RADIUS
        n = 0
        for rr in range(max(0, r - k), min(GRID_N, r + k + 1)):
            for cc in range(max(0, c - k), min(GRID_N, c + k + 1)):
                t = to_target(rr, cc)
                if t is None:
                    continue
                self.seen[t[0]][t[1]] = True          # 地图记住：这里我看过
                if not self.target[t[0]][t[1]]:
                    continue
                if self.state[rr][cc] != WHITE:
                    continue
                if self.reveal[rr][cc] <= 0:
                    n += 1
                self.reveal[rr][cc] = MIRAGE_FADE
        return n

    def clear_row(self, r):
        """旧紫怪专用：把这一整行的黑域清成白色，返回清掉几格。

        新版不刷紫怪了，这个方法留着备查（见开工单 §5「不要删掉旧关卡代码」）。
        """
        n = 0
        for c in range(GRID_N):
            if self.state[r][c] == VALID:
                self.force_white(r, c)
                n += 1
        return n

    def wipe_stains(self):
        """清屏：把全部脏格抹回白色，返回抹掉几格。累计计数不动（本幕账已经记下了）。"""
        n = 0
        for r in range(GRID_N):
            for c in range(GRID_N):
                if self.state[r][c] == DIRTY:
                    self.state[r][c] = WHITE
                    n += 1
        return n

    def update(self, dt):
        for r in range(GRID_N):
            srow, erow, vrow = self.state[r], self.erase_t[r], self.reveal[r]
            for c in range(GRID_N):
                if srow[c] == ERASING:
                    erow[c] -= dt
                    if erow[c] <= 0:
                        erow[c] = 0.0
                        srow[c] = WHITE
                if vrow[c] > 0:
                    vrow[c] = max(0.0, vrow[c] - dt)
        for k in list(self.flash):
            self.flash[k] -= dt
            if self.flash[k] <= 0:
                del self.flash[k]

    # --- 检查点快照 ---
    def snapshot(self):
        """只存「会变」的东西：格子状态、抹除计时、灰域、累计脏格。"""
        return {
            "state": [row[:] for row in self.state],
            "erase_t": [row[:] for row in self.erase_t],
            "reveal": [row[:] for row in self.reveal],
            "seen": [row[:] for row in self.seen],
            "stains": self.stains,
        }

    def restore(self, snap):
        self.state = [row[:] for row in snap["state"]]
        self.erase_t = [row[:] for row in snap["erase_t"]]
        self.reveal = [row[:] for row in snap["reveal"]]
        self.seen = [row[:] for row in snap.get("seen", self.seen)]
        self.stains = snap["stains"]
        self.flash.clear()
