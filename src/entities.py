# -*- coding: utf-8 -*-
"""活物：玩家（格子对齐步进）与侵蚀体（走向最近黑格，撞到就生效然后自毁）。

侵蚀体有两种，行为只差「撞到黑格那一刻」：
  红怪（kind="red"）  —— 吃掉那一个黑格
  紫怪（kind="purple"）—— 把那一整行的黑格全清成白色，逼玩家重涂这一行
"""

import pygame

from src.config import (
    BLACK, C_MONSTER, C_PURPLE, GRID_N, MONSTER_EAT_DIST, MONSTER_IDLE_LIMIT, MONSTER_RADIUS,
    MONSTER_RETRY, MOVE_REPEAT, PLAYER_START_CELL, PURPLE_IDLE_LIMIT, PURPLE_RADIUS
)
from src.grid import cell_center

# ==== 玩家 ====


class Player:
    """格子对齐（grid-based）：按一下走一格，位置永远是格心，不存在「半个身子在格子里」。"""

    def __init__(self):
        self.cell = PLAYER_START_CELL       # (row, col) 才是真身，pos 只是它的投影
        self.pos = pygame.Vector2(cell_center(*self.cell))
        self.facing = 1                     # 0上 1下 2左 3右
        self.repeat = 0.0                   # 长按连走的计时器

    def update(self, dt, d):
        if d is None:
            self.repeat = 0.0               # 松手归零，保证下次按下瞬间就走一格
            return
        self.repeat -= dt
        if self.repeat > 0:
            return
        self.repeat = MOVE_REPEAT
        nr, nc = self.cell[0] + d[0], self.cell[1] + d[1]
        if not (0 <= nr < GRID_N and 0 <= nc < GRID_N):
            return                          # 撞墙：原地不动，计时器照常重置，不会连环卡顿
        self.cell = (nr, nc)
        self.pos.update(cell_center(nr, nc))
        self.facing = (1 if d[0] > 0 else 0) if d[0] else (3 if d[1] > 0 else 2)

# ==== 怪物 ====


class Monster:
    """侵蚀体：从生成环进来，锁住最近的空闲黑格，走过去撞上它，然后自毁。

    一生只生效 1 次。没有状态机、没有动画阶段——走到就生效，完事就删。
    「最近黑格」天然就是诱饵机制：外围涂的黑格离生成环最近，怪自然先扑它们。

    kind 决定撞上黑格后的效果：
      "red"    吃一格（默认）
      "purple" 清掉那一整行的黑格（第二关起的紫怪）
    半径、颜色、闲置超时都从 config 按 kind 取，画的时候不用再判断类型。
    """

    def __init__(self, pos, speed, kind="red", mode="nearest"):
        self.kind = kind
        self.mode = mode                   # "nearest" 撞最近的 / "best_row" 专挑完成度最高的行
        self.pos = pygame.Vector2(pos)
        self.speed = speed
        self.target = None                 # (r, c) 或 None
        self.idle = 0.0                    # 无目标存活计时，超时自毁
        self.retry = 0.0                   # 无目标时多久重试一次
        if kind == "purple":
            self.radius = PURPLE_RADIUS
            self.color = C_PURPLE
            self.idle_limit = PURPLE_IDLE_LIMIT   # 紫怪要等玩家涂出东西，能撑更久
        else:
            self.radius = MONSTER_RADIUS
            self.color = C_MONSTER
            self.idle_limit = MONSTER_IDLE_LIMIT

    def claim(self, claims):
        """松开手上锁的那一格，让别的怪可以抢。"""
        if self.target is not None:
            claims[self.target] -= 1
            if claims[self.target] <= 0:
                del claims[self.target]
            self.target = None

    def _pick_best_row(self, board, claims):
        """只盯「完成度最高的那一行」，在那行里挑最近的黑格。选到了返回 True。"""
        row = board.best_row()
        if row is None:
            return False                   # 一行都没涂对：退回老行为
        best, best_d = None, None
        for c in range(GRID_N):
            if board.state[row][c] != BLACK:
                continue
            if claims.get((row, c)):       # 这一格别人锁着了，让给它
                continue
            cx, cy = cell_center(row, c)
            d = (cx - self.pos.x) ** 2 + (cy - self.pos.y) ** 2
            if best_d is None or d < best_d:
                best, best_d = (row, c), d
        if best is None:
            return False                   # 该行已经没黑格，或全被别人锁着
        claims[best] = claims.get(best, 0) + 1
        self.target = best
        return True

    def retarget(self, board, claims):
        """扫全网格找最近的黑格：优先没人锁的，全被锁了就允许重复，绝不卡死。

        mode="best_row" 的紫怪先试「完成度最高的那一行」；那一行没得选时，
        退回最近黑格 —— 保证它永远有事干，不会站着不动。
        """
        self.claim(claims)
        if self.mode == "best_row" and self._pick_best_row(board, claims):
            return
        free, any_cell = None, None
        free_d = any_d = None
        for r in range(GRID_N):
            row = board.state[r]
            for c in range(GRID_N):
                if row[c] != BLACK:        # ERASING 不吸引怪，规则同 §9.3
                    continue
                cx, cy = cell_center(r, c)
                d = (cx - self.pos.x) ** 2 + (cy - self.pos.y) ** 2
                if any_d is None or d < any_d:
                    any_cell, any_d = (r, c), d
                if not claims.get((r, c)) and (free_d is None or d < free_d):
                    free, free_d = (r, c), d
        pick = free or any_cell
        if pick is not None:
            claims[pick] = claims.get(pick, 0) + 1
            self.target = pick

    def update(self, dt, board, claims, center):
        """返回 False 表示这只怪该死（吃到了，或者闲着超时）。"""
        if self.target is not None:
            t = self.target
            if board.state[t[0]][t[1]] != BLACK:
                self.retarget(board, claims)     # 目标被吃了/被玩家抹了，立刻重选

        if self.target is None:
            self.idle += dt                      # 场上没黑格：朝中心漂一会儿，超时自毁
            to_c = center - self.pos
            if to_c.length_squared() > 1.0:
                self.pos += to_c.normalize() * self.speed * 0.5 * dt
            self.retry -= dt
            if self.retry <= 0:
                self.retry = MONSTER_RETRY
                self.retarget(board, claims)
            return self.idle < self.idle_limit

        self.idle = 0.0
        cx, cy = cell_center(*self.target)
        d = pygame.Vector2(cx - self.pos.x, cy - self.pos.y)
        if d.length() <= MONSTER_EAT_DIST:
            if self.kind == "purple":
                board.clear_row(self.target[0])   # 整行的黑格一起变白
            else:
                board.force_white(*self.target)   # 只吃掉这一格，变白 + 红闪
            self.claim(claims)
            return False                          # 试完必死
        self.pos += d.normalize() * self.speed * dt
        return True
