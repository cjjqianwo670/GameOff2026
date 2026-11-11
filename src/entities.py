# -*- coding: utf-8 -*-
"""活物：玩家（格子对齐步进）与红怪（the red ones）。

红怪的行为（第一幕）：
  场上有有效黑域（the Dark） → 吃掉最近的一格，然后自毁
  场上没有黑域             → 改为追玩家，追上就 -5% 血量，然后自毁
"""

import random

import pygame

from src.config import (
    C_MONSTER, C_PURPLE, GRID_N, MONSTER_EAT_DIST, MOVE_REPEAT, PLAYER_START_CELL,
    PURPLE_EAT_DIST, PURPLE_RADIUS, PURPLE_SPEED, RED_EAT_DIST, RED_HIT_DIST, RED_RADIUS, VALID
)
from src.grid import altar_center, cell_center

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
        self.phase = random.random() * 6.283    # 贴图抖动的相位：一群怪别一起呼吸
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

# ==== 第二幕的紫怪（the purple one）====


class PurpleOne:
    """锁圣坛内的一个黑格，撞到后清掉它所在「黑格更多」的那一整条线。

    规则（作者 2026-11-11 拍板）：
      P3  只锁**圣坛内**的有效黑域
      P2  比较锁定格所在的行与列，清**黑格更多**的那条
      P4  清**整条 25 格**（含圣坛外的平地诱饵）
      P9  脏格不算黑格 —— 既不计入「哪条多」，也不被清掉
      默认  平局选离玩家远的那条；一生只生效一次，撞完由 game 移除

    update() 返回 "alive" 或 ("wipe", axis, index, cleared)。
    """

    def __init__(self, pos, speed=None, radius=None):
        self.pos = pygame.Vector2(pos)
        self.speed = PURPLE_SPEED if speed is None else speed
        self.radius = PURPLE_RADIUS if radius is None else radius
        self.color = C_PURPLE
        self.phase = random.random() * 6.283
        self.target = None
        self.last_wipe = None
        self.done = False                      # 撞过一次就置 True，防止同一只连清两条

    def retarget(self, board):
        """最近的有效黑域，**且必须在圣坛内**。找不到返回 False。"""
        best, best_d = None, None
        for r in range(GRID_N):
            row = board.state[r]
            for c in range(GRID_N):
                if row[c] != VALID or not board.in_altar(r, c):
                    continue
                cx, cy = cell_center(r, c)
                d = (cx - self.pos.x) ** 2 + (cy - self.pos.y) ** 2
                if best_d is None or d < best_d:
                    best, best_d = (r, c), d
        self.target = best
        return best is not None

    def pick_line(self, board, cell, player_pos=None):
        """行 vs 列，谁的黑格多清谁；平局清离玩家远的那条。返回 ("row"|"col", index)。"""
        r, c = cell
        n_row = board.line_dark("row", r)
        n_col = board.line_dark("col", c)
        if n_row != n_col:
            return ("row", r) if n_row > n_col else ("col", c)
        if player_pos is None:
            return ("row", r)
        cx, cy = cell_center(r, c)
        # 玩家离线越远越安全：比较「玩家到这条行/列中线的距离」
        return ("row", r) if abs(player_pos.y - cy) >= abs(player_pos.x - cx) else ("col", c)

    def update(self, dt, board, player=None):
        if self.done:                          # 已经清过一条：等 game 把自己移除
            return "alive"
        if self.target is not None:
            r, c = self.target
            if board.state[r][c] != VALID:      # 被玩家抹了 / 被别的怪吃了 → 重选
                self.target = None
        if self.target is None and not self.retarget(board):
            # 场上没有可吃的黑域：朝圣坛中心漂，等玩家涂出来
            to_altar = pygame.Vector2(*altar_center()) - self.pos
            if to_altar.length_squared() > 1.0:
                self.pos += to_altar.normalize() * self.speed * 0.5 * dt
            return "alive"

        cx, cy = cell_center(*self.target)
        d = pygame.Vector2(cx - self.pos.x, cy - self.pos.y)
        if d.length() <= PURPLE_EAT_DIST:
            axis, idx = self.pick_line(board, self.target, player.pos if player else None)
            cleared = board.clear_line(axis, idx)
            self.last_wipe = (axis, idx, cleared)
            self.target = None
            self.done = True                     # 一生一次，由 game 移除
            return ("wipe", axis, idx, cleared)
        self.pos += d.normalize() * self.speed * dt
        return "alive"

    def claim(self, claims):
        """接口对齐 Monster：紫怪不占 claims（它锁的是整条线，不是单格）。"""
        return None


# ==== 老者（the old man）====


class OldMan:
    """老者：一个比玩家大一圈的矩形 + 一根拐杖。不做美术。

    他先是背对玩家（朝世界外），被呼喊后转身；坛内呼喊时他会兴奋地跑过来。
    staff_t > 0 的这段时间里，拐杖在挥 —— 开场驱赶那两只红怪用的就是它。
    """

    def __init__(self, cell, facing=2):
        self.cell = cell
        self.pos = pygame.Vector2(cell_center(*cell))
        self.facing = facing            # 0上 1下 2左 3右
        self.staff_t = 0.0
        self.walk_t = 0.0               # 走路摆动的相位（只在移动时累加）
        self.leaving = False
        self.gone = False

    def wave(self, secs):
        self.staff_t = secs

    def face_to(self, pos):
        dx, dy = pos.x - self.pos.x, pos.y - self.pos.y
        self.facing = (1 if dy > 0 else 0) if abs(dy) > abs(dx) else (3 if dx > 0 else 2)

    def update(self, dt):
        if self.staff_t > 0:
            self.staff_t = max(0.0, self.staff_t - dt)

    def move_toward(self, target, speed, dt):
        """朝目标走一步，返回是否已经到位。"""
        d = pygame.Vector2(target[0] - self.pos.x, target[1] - self.pos.y)
        if d.length() <= speed * dt + 1.0:
            self.pos.update(target)
            return True
        self.pos += d.normalize() * speed * dt
        self.walk_t += dt
        self.face_to(pygame.Vector2(target))
        return False


# ==== 过场里的红怪（不是战斗单位，只是演出）====


class SceneRed:
    """开场被老者赶走的那两只。只沿一条直线进退，逃出画面就回收。"""

    def __init__(self, pos, vel, radius=9):
        self.phase = random.random() * 6.283
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.radius = radius
        self.gone = False

    def update(self, dt, stop_y=None):
        self.pos += self.vel * dt
        if stop_y is not None and self.pos.y >= stop_y:
            self.pos.y = stop_y
            self.vel.update(0, 0)


# ==== 道具（BAG / MAP）====


class Item:
    """清屏之后从已复原的黑格上浮出来的道具。t 是浮起进度 0→1。"""

    def __init__(self, kind, cell):
        self.kind = kind                # "bag" / "map"
        self.cell = cell
        self.pos = pygame.Vector2(cell_center(*cell))
        self.t = 0.0
        self.picked = False
