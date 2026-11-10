# -*- coding: utf-8 -*-
"""活物：玩家（格子对齐步进）与红怪（the red ones）。

红怪的行为（第一幕）：
  场上有有效黑域（the Dark） → 吃掉最近的一格，然后自毁
  场上没有黑域             → 改为追玩家，追上就 -5% 血量，然后自毁
"""

import pygame

from src.config import (
    C_MONSTER, C_PURPLE, GRID_N, MONSTER_EAT_DIST, MOVE_REPEAT, PLAYER_START_CELL, PURPLE_RADIUS,
    RED_EAT_DIST, RED_HIT_DIST, RED_RADIUS, VALID
)
from src.grid import cell_center

# ==== 玩家 ====


class Player:
    """格子对齐（grid-based）：按一下走一格，位置永远是格心。"""

    def __init__(self):
        self.cell = PLAYER_START_CELL       # (row, col) 才是真身，pos 只是它的投影
        self.pos = pygame.Vector2(cell_center(*self.cell))
        self.facing = 1                     # 0上 1下 2左 3右
        self.repeat = 0.0                   # 长按连走的计时器

    def reset(self):
        self.cell = PLAYER_START_CELL
        self.pos.update(cell_center(*self.cell))
        self.facing = 1
        self.repeat = 0.0

    def update(self, dt, d, frozen=False):
        if frozen or d is None:
            self.repeat = 0.0               # 松手/禁止移动时归零，下次按下瞬间就走一格
            return
        self.repeat -= dt
        if self.repeat > 0:
            return
        self.repeat = MOVE_REPEAT
        nr, nc = self.cell[0] + d[0], self.cell[1] + d[1]
        if not (0 <= nr < GRID_N and 0 <= nc < GRID_N):
            return                          # 撞墙：原地不动
        self.cell = (nr, nc)
        self.pos.update(cell_center(nr, nc))
        self.facing = (1 if d[0] > 0 else 0) if d[0] else (3 if d[1] > 0 else 2)

# ==== 怪物 ====


class Monster:
    """红怪：锁住最近的黑域走过去吃掉；场上没黑域了就转头追你。

    一生只生效 1 次 —— 吃到黑域、或者打中玩家，都然后自毁。
    半径/颜色挂在实例上，画的时候不用判断类型。
    """

    def __init__(self, pos, speed, kind="red"):
        self.kind = kind
        self.pos = pygame.Vector2(pos)
        self.speed = speed
        self.target = None                  # (r, c) 或 None（None = 场上没黑域，追人）
        self.mode = "dark"                  # "dark" 吃黑域 / "hunt" 追玩家
        if kind == "purple":                # 旧紫怪：新版不刷，留着备查（见开工单 §5）
            self.radius = PURPLE_RADIUS
            self.color = C_PURPLE
        else:
            self.radius = RED_RADIUS
            self.color = C_MONSTER

    def claim(self, claims):
        """松开手上锁的那一格，让别的怪可以抢。"""
        if self.target is not None:
            n = claims.get(self.target, 0) - 1
            if n > 0:
                claims[self.target] = n
            else:
                claims.pop(self.target, None)
            self.target = None

    def retarget(self, board, claims):
        """扫全网格找最近的有效黑域：优先没人锁的，全被锁了就允许重复，绝不卡死。

        脏格不吸引怪（它不是 the Dark）。一格黑域都没有时返回 False → 转追玩家。
        """
        self.claim(claims)
        free, free_d = None, None
        any_cell, any_d = None, None
        for r in range(GRID_N):
            row = board.state[r]
            for c in range(GRID_N):
                if row[c] != VALID:
                    continue
                cx, cy = cell_center(r, c)
                d = (cx - self.pos.x) ** 2 + (cy - self.pos.y) ** 2
                if any_d is None or d < any_d:
                    any_cell, any_d = (r, c), d
                if not claims.get((r, c)) and (free_d is None or d < free_d):
                    free, free_d = (r, c), d
        pick = free or any_cell
        if pick is None:
            self.mode = "hunt"
            return False
        claims[pick] = claims.get(pick, 0) + 1
        self.target = pick
        self.mode = "dark"
        return True

    def update(self, dt, board, claims, player):
        """返回 "alive" / "eat" / "hit"。"""
        if self.kind == "purple":               # 旧紫怪保留原行为：撞到就清掉整行
            return self._update_purple(dt, board, claims)

        # 目标黑域被别人吃了/被玩家抹了 → 立刻重选
        if self.target is not None and board.state[self.target[0]][self.target[1]] != VALID:
            self.retarget(board, claims)

        if self.mode == "hunt" or self.target is None:
            if self.retarget(board, claims):
                return self._step_to_dark(dt, board, claims)
            return self._hunt(dt, player)

        return self._step_to_dark(dt, board, claims)

    def _step_to_dark(self, dt, board, claims):
        cx, cy = cell_center(*self.target)
        d = pygame.Vector2(cx - self.pos.x, cy - self.pos.y)
        if d.length() <= RED_EAT_DIST:
            board.force_white(*self.target)     # 吃掉这一格
            self.claim(claims)
            return "eat"
        self.pos += d.normalize() * self.speed * dt
        return "alive"

    def _hunt(self, dt, player):
        d = player.pos - self.pos
        if d.length() <= RED_HIT_DIST:
            return "hit"                        # 追上玩家：扣血，然后自毁
        if d.length_squared() > 1.0:
            self.pos += d.normalize() * self.speed * dt
        return "alive"

    def _update_purple(self, dt, board, claims):
        """旧紫怪：吃掉整行。新版不刷它，留着备查。"""
        if self.mode != "dark" or self.target is None:
            if not self.retarget(board, claims):
                to_c = pygame.Vector2(cell_center(GRID_N // 2, GRID_N // 2)) - self.pos
                if to_c.length_squared() > 1.0:
                    self.pos += to_c.normalize() * self.speed * 0.5 * dt
                return "alive"
        cx, cy = cell_center(*self.target)
        d = pygame.Vector2(cx - self.pos.x, cy - self.pos.y)
        if d.length() <= MONSTER_EAT_DIST:
            board.clear_row(self.target[0])
            self.claim(claims)
            return "eat"
        self.pos += d.normalize() * self.speed * dt
        return "alive"
