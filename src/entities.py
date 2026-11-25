# -*- coding: utf-8 -*-
"""活物：玩家（格子对齐步进）与红怪（the red ones）。

红怪的行为（第一幕）：
  场上有有效黑域（the Dark） → 吃掉最近的一格，然后自毁
  场上没有黑域             → 改为追玩家，追上就 -5% 血量，然后自毁
"""

import random

import pygame

from src.config import (
    C_GREEN, C_GREEN_DARK, C_GREEN_CORE, C_MONSTER, C_PURPLE, C_YELLOW, GRID_N, MOVE_REPEAT,
    OLDMAN_HP, OLDMAN_STAGGER, PLAYER_START_CELL,
    GREEN_EAT_DIST, GREEN_HIT_DIST, GREEN_RADIUS, GREEN_SPEED,
    PURPLE_EAT_DIST, PURPLE_HIT_DIST, PURPLE_RADIUS, PURPLE_SPEED, RED_EAT_DIST, RED_HIT_DIST,
    RED_RADIUS, SWORD_KNOCKBACK_SPEED, SWORD_KNOCKBACK_TIME, VALID, YELLOW_AGGRO_TIME,
    YELLOW_BITE_CD, YELLOW_BITE_DIST, YELLOW_HP,
    YELLOW_RADIUS, YELLOW_SPEED,
    DECOY_HP, DECOY_LIFE
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

    def update(self, dt, d, frozen=False, can_stand=None, buffered=None):
        if frozen:
            self.repeat = 0.0
            return
        if d is None and buffered is None:
            self.repeat = 0.0               # 松手/禁止移动时归零，下次按下瞬间就走一格
            return
        # 缓冲的新按键优先（输入缓冲/反向急停），否则用持续按住的方向（长按连走）
        move_dir = buffered if buffered is not None else d
        # 朝向先更新：贴墙/贴缝时移动被挡，但面向要跟上（转身朝来怪的方向，作者 2026-11-18）
        self.facing = (1 if move_dir[0] > 0 else 0) if move_dir[0] else (3 if move_dir[1] > 0 else 2)
        if buffered is not None:
            self.repeat = MOVE_REPEAT       # 新按键：立即走一格，再进入正常长按间隔
        else:
            self.repeat -= dt
            if self.repeat > 0:
                return
            self.repeat = MOVE_REPEAT
        nr, nc = self.cell[0] + move_dir[0], self.cell[1] + move_dir[1]
        if not (0 <= nr < GRID_N and 0 <= nc < GRID_N):
            return                          # 撞墙：原地不动
        if can_stand is not None and not can_stand(self.cell, (nr, nc)):
            return                          # 裂缝 / 分离板块 / 还没接回来的板块：过不去
        self.cell = (nr, nc)
        self.pos.update(cell_center(nr, nc))

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

    def retarget(self, board, claims, decoys=None):
        """扫全网格找最近的有效黑域：优先没人锁的，全被锁了就允许重复，绝不卡死。

        脏格不吸引怪（它不是 the Dark）。一格黑域都没有时返回 False → 转追玩家。
        2026-11-16：优先锁诱饵（`decoys` 里的实体）——诱饵是「强吸引」，有它在就先打它。
        """
        self.claim(claims)
        # 1) 优先：找最近的诱饵
        if decoys:
            best_dc, best_d = None, None
            for dc in decoys:
                if dc.dead:
                    continue
                cx, cy = cell_center(*dc.cell)
                d = (cx - self.pos.x) ** 2 + (cy - self.pos.y) ** 2
                if best_d is None or d < best_d:
                    best_dc, best_d = dc, d
            if best_dc is not None:
                self.target = best_dc.cell
                self.mode = "dark"
                claims[self.target] = claims.get(self.target, 0) + 1
                return True
        # 2) 没有诱饵：扫网格找最近黑域
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

    def update(self, dt, board, claims, player, decoys=None):
        """返回 "alive" / "eat" / "hit" / ("decoy", decoy)。"""
        # 目标黑域被别人吃了/被玩家抹了 → 立刻重选
        if self.target is not None and board.state[self.target[0]][self.target[1]] != VALID:
            self.retarget(board, claims, decoys)

        if self.mode == "hunt" or self.target is None:
            if self.retarget(board, claims, decoys):
                return self._step_to_dark(dt, board, claims, decoys)
            return self._hunt(dt, player)

        return self._step_to_dark(dt, board, claims, decoys)

    def _step_to_dark(self, dt, board, claims, decoys=None):
        cx, cy = cell_center(*self.target)
        d = pygame.Vector2(cx - self.pos.x, cy - self.pos.y)
        if d.length() <= RED_EAT_DIST:
            # 先看是不是在咬诱饵：咬诱饵只扣血，不把格子吃掉
            if decoys:
                for dc in decoys:
                    if not dc.dead and dc.cell == self.target:
                        dc.hit()
                        self.claim(claims)
                        return ("decoy", dc)
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

# ==== 绿怪（the green one，第二幕起）====


class GreenOne:
    """绿怪：锁最近的有效黑域走过去，到点后以该格为中心清 3×3（最多 9 格）。

    是红怪的「面扩展版」：破坏从单格升级成一片。规则对齐红怪——
      · 锁最近的有效黑域（脏格不算，也不清）
      · 清 3×3 只清有效黑域，擦到定位图案核心同样触发板块分离（由 game 判定）
      · 一生只生效一次，清完自毁
      · 场上没黑域 → 追玩家，撞到扣血
    """

    def __init__(self, pos, speed=None):
        self.phase = random.random() * 6.283
        self.pos = pygame.Vector2(pos)
        self.speed = GREEN_SPEED if speed is None else speed
        self.radius = GREEN_RADIUS
        self.color = C_GREEN
        self.target = None                  # (r, c) 或 None（None = 追玩家）
        self.mode = "dark"                  # "dark" 吃黑域 / "hunt" 追玩家
        self.done = False

    def claim(self, claims):
        """接口对齐 Monster：绿怪占一格（锁的是目标格）。"""
        if self.target is not None:
            n = claims.get(self.target, 0) - 1
            if n > 0:
                claims[self.target] = n
            else:
                claims.pop(self.target, None)
            self.target = None

    def retarget(self, board, claims, decoys=None):
        """扫全网格找最近的有效黑域（脏格不算）。找不到返回 False → 追玩家。
        2026-11-16：优先锁诱饵（强吸引）。
        """
        self.claim(claims)
        if decoys:
            best_dc, best_d = None, None
            for dc in decoys:
                if dc.dead:
                    continue
                cx, cy = cell_center(*dc.cell)
                d = (cx - self.pos.x) ** 2 + (cy - self.pos.y) ** 2
                if best_d is None or d < best_d:
                    best_dc, best_d = dc, d
            if best_dc is not None:
                self.target = best_dc.cell
                self.mode = "dark"
                claims[self.target] = claims.get(self.target, 0) + 1
                return True
        best, best_d = None, None
        for r in range(GRID_N):
            row = board.state[r]
            for c in range(GRID_N):
                if row[c] != VALID:
                    continue
                cx, cy = cell_center(r, c)
                d = (cx - self.pos.x) ** 2 + (cy - self.pos.y) ** 2
                if best_d is None or d < best_d:
                    best, best_d = (r, c), d
        if best is None:
            self.mode = "hunt"
            self.target = None
            return False
        claims[best] = claims.get(best, 0) + 1
        self.target = best
        self.mode = "dark"
        return True

    def update(self, dt, board, claims, player, decoys=None):
        """返回 "alive" / ("wipe", cells) / ("hit",) / ("decoy", decoy)。"""
        if self.done:
            return "alive"
        if self.target is not None and board.state[self.target[0]][self.target[1]] != VALID:
            self.retarget(board, claims, decoys)
        if self.mode == "hunt" or self.target is None:
            if self.retarget(board, claims, decoys):
                return self._step_to_dark(dt, board, claims, decoys)
            return self._hunt(dt, player)
        return self._step_to_dark(dt, board, claims, decoys)

    def _step_to_dark(self, dt, board, claims, decoys=None):
        cx, cy = cell_center(*self.target)
        d = pygame.Vector2(cx - self.pos.x, cy - self.pos.y)
        if d.length() <= GREEN_EAT_DIST:
            # 咬诱饵：只扣血，不清 3×3
            if decoys:
                for dc in decoys:
                    if not dc.dead and dc.cell == self.target:
                        dc.hit()
                        self.claim(claims)
                        self.done = True
                        return ("decoy", dc)
            wiped = board.clear_area(*self.target)   # 以目标格为中心清 3×3
            self.claim(claims)
            self.done = True
            return ("wipe", wiped)
        self.pos += d.normalize() * self.speed * dt
        return "alive"

    def _hunt(self, dt, player):
        d = player.pos - self.pos
        if d.length() <= GREEN_HIT_DIST:
            self.done = True
            return ("hit",)
        if d.length_squared() > 1.0:
            self.pos += d.normalize() * self.speed * dt
        return "alive"


# ==== 第二幕的紫怪（the purple one）====


class PurpleOne:
    """锁圣坛内的一个黑格，撞到后清掉它所在的那一整条线。

    规则（作者 2026-11-11 拍板；2026-11-25 把「最近」和「黑格更多」改成随机）：
      P3  只锁**圣坛内**的有效黑域；目标从里面**均匀随机**挑一格（原：最近）
      P2  撞到后**随机**清该格所在的行或列（原：比较行/列，清黑格更多的那条）
      P4  清**整条 25 格**（含圣坛外的平地诱饵）
      P9  脏格不算黑格 —— 既不会被选中，也不被清掉
      P10 圣坛内**一格黑域都没有**时，转而扑向码序使，撞到扣 10% 血（作者 2026-11-12）
      默认  诱饵优先；一生只生效一次，撞完由 game 移除

    update() 返回 "alive" / ("wipe", axis, index, cleared) / ("hit",) / ("decoy", decoy)。
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

    def retarget(self, board, decoys=None):
        """诱饵优先；否则在圣坛内的有效黑域里**均匀随机**挑一格。找不到返回 False。

        2026-11-25 作者改：原来是「最近的黑格」，现在是随机 —— 行踪不可预测。
        """
        if decoys:
            best_dc, best_d = None, None
            for dc in decoys:
                if dc.dead or not board.in_altar(*dc.cell):
                    continue
                cx, cy = cell_center(*dc.cell)
                d = (cx - self.pos.x) ** 2 + (cy - self.pos.y) ** 2
                if best_d is None or d < best_d:
                    best_dc, best_d = dc, d
            if best_dc is not None:
                self.target = best_dc.cell
                return True
        cells = [(r, c) for r in range(GRID_N) for c in range(GRID_N)
                 if board.state[r][c] == VALID and board.in_altar(r, c)]
        if not cells:
            self.target = None
            return False
        self.target = random.choice(cells)
        return True

    def pick_line(self, cell):
        """清「行」还是「列」：各 50%，纯随机（作者 2026-11-25 定）。"""
        r, c = cell
        return ("row", r) if random.random() < 0.5 else ("col", c)

    def update(self, dt, board, player=None, decoys=None):
        if self.done:                          # 已经清过一条：等 game 把自己移除
            return "alive"
        if self.target is not None:
            r, c = self.target
            if board.state[r][c] != VALID:      # 被玩家抹了 / 被别的怪吃了 → 重选
                self.target = None
        if self.target is None and not self.retarget(board, decoys):
            # 圣坛内一格黑域都没有：不再干等，转去扑码序使（P10，作者 2026-11-12）
            return self._chase_player(dt, player)

        cx, cy = cell_center(*self.target)
        d = pygame.Vector2(cx - self.pos.x, cy - self.pos.y)
        if d.length() <= PURPLE_EAT_DIST:
            # 咬诱饵：只扣血，不清整条线
            if decoys:
                for dc in decoys:
                    if not dc.dead and dc.cell == self.target:
                        dc.hit()
                        self.target = None
                        self.done = True
                        return ("decoy", dc)
            axis, idx = self.pick_line(self.target)
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


class Decoy:
    """诱饵（第四幕，2026-11-16 升级为独立实体）：一个假黑域方块，**强吸引**所有怪物来攻击。

    有血量（`DECOY_HP`）：怪物攻击一次扣 1，耗尽才消失 —— 所以它能真正「扛火力」几秒，
    而不是像原来那样一口被吃掉。它在 board 上仍占一个 VALID 格（怪物索敌天然能看见它），
    但血量由这个实体自己记，格子被吃只扣血、不立即消失。
    """

    def __init__(self, cell):
        self.cell = cell                      # (r, c)
        self.pos = pygame.Vector2(cell_center(*cell))
        self.hp = DECOY_HP
        self.max_hp = DECOY_HP
        self.t = DECOY_LIFE                   # 存在时长，到期消失
        self.dead = False

    def hit(self, dmg=1):
        """怪物攻击一次：扣血。返回 True = 血量耗尽，该消失了。"""
        self.hp -= dmg
        return self.hp <= 0


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
        self.kb_t = 0.0                 # >0 = 正在被击退（挥剑命中）
        self.kb_dir = pygame.Vector2(0, 0)   # 击退方向（单位向量）

    @property
    def hunting(self):
        """贴图用：像红怪的「追人」状态那样套一圈环。"""
        return self.aggro_t > 0

    def hurt(self, damage=1, knock_dir=None):
        """挨一剑。返回 True = 死了。**挨打必然转火玩家**（作者的规则）。

        `knock_dir`：挥剑传来的击退方向（单位向量），有就进入击退状态。
        """
        self.hp -= damage
        self.flash = 0.12
        self.aggro_t = YELLOW_AGGRO_TIME
        if knock_dir is not None and knock_dir.length_squared() > 0:
            self.kb_t = SWORD_KNOCKBACK_TIME
            self.kb_dir = knock_dir.normalize()
        return self.hp <= 0

    def update(self, dt, oldman, player):
        """索敌：**谁近咬谁**（作者 2026-11-14 改）。

        改动前是「默认冲老者，被打才转火玩家」—— 那让玩家可以一直躲在远处看它咬他。
        改成比距离以后，玩家站得近就是目标，站位本身变成了要判断的事。

        仍然保留的两条：
          · **被砍过就优先玩家**（`aggro_t`）—— 那是「被打之后的反应」，不是索敌；
          · **老者倒下时停手**（`down` 不算目标，且直接 return）—— 2026-11-12 的死循环防线：
            他倒 → 它们转火玩家 → 玩家救不了 → 更救不了。
        """
        self.bite_cd = max(0.0, self.bite_cd - dt)
        self.flash = max(0.0, self.flash - dt)
        if self.aggro_t > 0:
            self.aggro_t = max(0.0, self.aggro_t - dt)

        # 被挥剑击退：整段时间沿击退方向滑出去，不索敌、不咬人。
        if self.kb_t > 0:
            self.kb_t = max(0.0, self.kb_t - dt)
            self.pos += self.kb_dir * SWORD_KNOCKBACK_SPEED * dt
            return "alive"

        if self.aggro_t <= 0 and oldman is not None and not oldman.gone and oldman.down:
            return "alive"          # 他倒了：停手，给玩家时间去扶他起来

        if self.aggro_t > 0 and player is not None:      # 被砍过：先咬砍它的人
            target, go_oldman = player.pos, False
        else:
            cands = []
            if oldman is not None and not oldman.gone and not oldman.down:
                cands.append((oldman.pos, True))
            if player is not None:
                cands.append((player.pos, False))
            if not cands:
                return "alive"
            target, go_oldman = min(
                cands, key=lambda kv: (kv[0] - self.pos).length_squared())

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


# ==== 道具（BAG / SWORD）====


class Item:
    """清屏之后从已复原的黑格上浮出来的道具。t 是浮起进度 0→1。"""

    def __init__(self, kind, cell):
        self.kind = kind                # "bag" / "map" / "sword"
        self.cell = cell
        self.pos = pygame.Vector2(cell_center(*cell))
        self.t = 0.0
        self.picked = False
