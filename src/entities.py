# -*- coding: utf-8 -*-
"""活物：玩家（格子对齐步进）与红怪（the red ones）。

红怪的行为（第一幕）：
  场上有有效黑域（the Dark） → 吃掉最近的一格，然后自毁
  场上没有黑域             → 改为追玩家，追上就 -5% 血量，然后自毁
"""

import random

import pygame

from src.config import (
    C_MONSTER, C_PURPLE, C_YELLOW, GRID_N, MOVE_REPEAT, OLDMAN_HP, OLDMAN_STAGGER, PLAYER_START_CELL,
    PURPLE_EAT_DIST, PURPLE_HIT_DIST, PURPLE_RADIUS, PURPLE_SPEED, RED_EAT_DIST, RED_HIT_DIST,
    RED_RADIUS, VALID, YELLOW_AGGRO_TIME, YELLOW_BITE_CD, YELLOW_BITE_DIST, YELLOW_HP,
    YELLOW_RADIUS, YELLOW_SPEED
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

    def __init__(self, pos, speed):
        self.phase = random.random() * 6.283    # 贴图抖动的相位：一群怪别一起呼吸
        self.pos = pygame.Vector2(pos)
        self.speed = speed
        self.target = None                  # (r, c) 或 None（None = 场上没黑域，追人）
        self.mode = "dark"                  # "dark" 吃黑域 / "hunt" 追玩家
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

# ==== 第二幕的紫怪（the purple one）====


class PurpleOne:
    """锁圣坛内的一个黑格，撞到后清掉它所在「黑格更多」的那一整条线。

    规则（作者 2026-11-11 拍板）：
      P3  只锁**圣坛内**的有效黑域
      P2  比较锁定格所在的行与列，清**黑格更多**的那条
      P4  清**整条 25 格**（含圣坛外的平地诱饵）
      P9  脏格不算黑格 —— 既不计入「哪条多」，也不被清掉
      P10 圣坛内**一格黑域都没有**时，转而扑向码序使，撞到扣 10% 血（作者 2026-11-12）
      默认  平局选离玩家远的那条；一生只生效一次，撞完由 game 移除

    update() 返回 "alive" / ("wipe", axis, index, cleared) / ("hit",)。
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
            # 圣坛内一格黑域都没有：不再干等，转去扑码序使（P10，作者 2026-11-12）
            return self._chase_player(dt, player)

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

    def _chase_player(self, dt, player):
        """坛内没黑域时扑人：撞到返回 ("hit",)，由 game 扣血并把自己移除。

        没有 player（理论上不会）就退回原来的「朝圣坛中心漂」，不会崩。
        """
        if player is None:
            to_altar = pygame.Vector2(*altar_center()) - self.pos
            if to_altar.length_squared() > 1.0:
                self.pos += to_altar.normalize() * self.speed * 0.5 * dt
            return "alive"
        d = player.pos - self.pos
        if d.length() <= PURPLE_HIT_DIST:
            self.done = True                     # 一生一次，由 game 移除
            return ("hit",)
        if d.length_squared() > 1.0:
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
        # 第三幕：他也会被打。hp 归零不是死，是**倒下**（作者 2026-11-12：倒下会呼救，玩家按 H 救）
        self.hp = OLDMAN_HP
        self.down = False
        self.hurt_t = 0.0               # 被咬那一下的红闪
        self.stagger_t = 0.0            # 被咬之后笔停住多久（`OLDMAN_STAGGER`）

    def wave(self, secs):
        self.staff_t = secs

    def face_to(self, pos):
        dx, dy = pos.x - self.pos.x, pos.y - self.pos.y
        self.facing = (1 if dy > 0 else 0) if abs(dy) > abs(dx) else (3 if dx > 0 else 2)

    def update(self, dt):
        if self.staff_t > 0:
            self.staff_t = max(0.0, self.staff_t - dt)
        if self.hurt_t > 0:
            self.hurt_t = max(0.0, self.hurt_t - dt)
        if self.stagger_t > 0:
            self.stagger_t = max(0.0, self.stagger_t - dt)

    def bitten(self, damage):
        """被咬一口。返回 True = 这一下把他打倒了。"""
        if self.down:
            return False
        self.hp = max(0, self.hp - damage)
        self.hurt_t = 0.22
        self.stagger_t = OLDMAN_STAGGER  # 咬一口就打断他 —— 「守」靠这个才成立
        if self.hp <= 0:
            self.down = True
            return True
        return False

    def revive(self, hp):
        """被救起来：站起来，带着一点血。硬直也清掉。"""
        self.hp = hp
        self.down = False
        self.hurt_t = 0.0
        self.stagger_t = 0.0

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


# ==== 第三幕的黄怪（the yellow ones）====


class YellowOne:
    """黄怪：一路冲老者 —— 它认为格式信息是被偷的。

    行为（作者 2026-11-12 定）：
      · **默认目标 = 老者**；老者倒下 / 不在场，就转火玩家
      · **被砍一次就愤怒**：转火玩家 `YELLOW_AGGRO_TIME` 秒，然后回去找老者
      · 咬人只报事件（`bite_oldman` / `bite_player`），扣血由 game 做 —— 和红怪、紫怪一致

    `update()` 返回 `"alive"` / `"bite_oldman"` / `"bite_player"`。
    """

    def __init__(self, pos, speed=None):
        self.pos = pygame.Vector2(pos)
        self.speed = speed if speed else YELLOW_SPEED
        self.phase = random.random() * 6.283
        self.hp = YELLOW_HP
        self.radius = YELLOW_RADIUS
        self.color = C_YELLOW
        self.aggro_t = 0.0              # >0 = 正在盯玩家（被打之后）
        self.bite_cd = 0.0
        self.flash = 0.0                # 被打中那一下的白闪

    @property
    def hunting(self):
        """贴图用：像红怪的「追人」状态那样套一圈环。"""
        return self.aggro_t > 0

    def hurt(self, damage=1):
        """挨一剑。返回 True = 死了。**挨打必然转火玩家**（作者的规则）。"""
        self.hp -= damage
        self.flash = 0.12
        self.aggro_t = YELLOW_AGGRO_TIME
        return self.hp <= 0

    def update(self, dt, oldman, player):
        self.bite_cd = max(0.0, self.bite_cd - dt)
        self.flash = max(0.0, self.flash - dt)
        if self.aggro_t > 0:
            self.aggro_t = max(0.0, self.aggro_t - dt)

        if self.aggro_t <= 0 and oldman is not None and not oldman.gone and oldman.down:
            # 他倒了：它们要的是格式信息，不是命 —— **停手**，给玩家时间去扶他起来。
            # 不加这条会滚成死循环：他倒 → 黄怪转火玩家 → 玩家救不了 → 更救不了（2026-11-12）
            return "alive"

        go_oldman = (self.aggro_t <= 0 and oldman is not None
                     and not oldman.gone and not oldman.down)
        target = oldman.pos if go_oldman else (player.pos if player is not None else None)
        if target is None:
            return "alive"
        d = target - self.pos
        reach = YELLOW_BITE_DIST if go_oldman else RED_HIT_DIST + 3
        if d.length() <= reach:
            if self.bite_cd > 0:
                return "alive"
            self.bite_cd = YELLOW_BITE_CD
            return "bite_oldman" if go_oldman else "bite_player"
        if d.length_squared() > 1.0:
            self.pos += d.normalize() * self.speed * dt
        return "alive"


# ==== 道具（BAG / MAP / SWORD）====


class Item:
    """清屏之后从已复原的黑格上浮出来的道具。t 是浮起进度 0→1。"""

    def __init__(self, kind, cell):
        self.kind = kind                # "bag" / "map"
        self.cell = cell
        self.pos = pygame.Vector2(cell_center(*cell))
        self.t = 0.0
        self.picked = False
