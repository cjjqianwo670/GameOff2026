# -*- coding: utf-8 -*-
"""角色贴图：全部用 pygame 图元现画，不依赖任何外部资源。

三个角色共用同一套绘制顺序，所以风格是统一的：

    影子 → 剪影（深）→ 体积（暗部 / 亮部）→ 高光（眼 / 面罩 / 核心）→ 描边

坐标一律按「格子中心」给，内部再换成图元坐标 —— 以后改 CELL 不用动这里。
所有贴图都只画在中心附近几十 px 内，不会糊到隔壁格。

t 传 g.anim_t（秒），只用来做呼吸 / 抖动 / 闪烁；同屏的怪各自带 phase，不会齐步走。
"""

import math

import pygame

from src.config import (
    C_CELL_BLACK, C_ITEM, C_ITEM_INK, C_ITEM_LEATHER, C_ITEM_LEATHER_DARK, C_ITEM_MARK,
    C_ITEM_PAPER, C_ITEM_PAPER_DARK, C_MONSTER, C_MONSTER_CORE, C_MONSTER_DARK,
    C_MONSTER_RING, C_OLDMAN, C_OLDMAN_DARK, C_OLDMAN_LIGHT, C_OLDMAN_SKIN, C_OUTLINE,
    C_PLAYER, C_PLAYER_DARK, C_PLAYER_DEEP, C_PLAYER_LIGHT, C_PROP_DEAD, C_PROP_TOOL, C_SASH, C_STAFF
)

# 影子按尺寸缓存：每帧新建 Surface 会掉帧
_SHADOW_CACHE = {}


def _mix(a, b, k):
    """两色线性插值（k=0 取 a，k=1 取 b）。"""
    return (int(a[0] + (b[0] - a[0]) * k),
            int(a[1] + (b[1] - a[1]) * k),
            int(a[2] + (b[2] - a[2]) * k))


def shadow(s, cx, cy, w, h, alpha=72):
    """脚下的一摊影子：贴地感全靠它，不然角色像贴在画面上。"""
    key = (w, h, alpha)
    surf = _SHADOW_CACHE.get(key)
    if surf is None:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (10, 6, 4, alpha), surf.get_rect())
        _SHADOW_CACHE[key] = surf
    s.blit(surf, (cx - w // 2, cy - h // 2))


def _blob(cx, cy, r, n, t, phase, wob):
    """会呼吸的烂肉块：正多边形 + 每点各自起伏。"""
    pts = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        rr = r + math.sin(t + i * 1.9 + phase) * wob
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return pts


# ==== 码序使（玩家）====

def draw_sequencer(s, cx, cy, facing=1, t=0.0, moving=False, glow=None, has_bag=False,
                   holding_map=False, has_sword=False, swing=0.0):
    """读码的人：深色斗篷 + 一条发光面罩 + 头上一块闪烁的光标。

    他不是「一个方块」，而是「正在被输入的那一行」—— 光标才是身份标识。
    朝向：0 上（背对）1 下 2 左 3 右。

    `holding_map`：按 M 看地图时的姿态 —— 两只手往胸前收，捧着一张摊开的纸。
    这不是纯装饰：手占着了就不能写（`Game` 在地图摊开时封掉 J / K / Shift）。

    `has_sword` / `swing`：第三幕的剑。`swing` 是**挥砍剩余比例**（1 → 0，0 = 没在挥），
    刃会从一侧扫到另一侧 —— 只看一道弧线是不够的，人要跟着动。
    """
    # 呼吸（站着轻轻浮）/ 走路（上下颠得更快）
    bob = math.sin(t * 9.5) * 0.6 if moving else math.sin(t * 2.1) * 0.8
    px, py = int(round(cx)), int(round(cy + bob))

    shadow(s, px, py + 14, 24, 8, 84)
    if glow is not None:
        s.blit(glow, (px - glow.get_width() // 2, py + 2 - glow.get_height() // 2))

    # 脚：走路时左右交替抬 1px
    phase = math.sin(t * 12.0)
    lift_l = 1 if (moving and phase > 0) else 0
    lift_r = 1 if (moving and phase <= 0) else 0
    s.fill(C_PLAYER_DEEP, pygame.Rect(px - 7, py + 11 - lift_l, 6, 3))
    s.fill(C_PLAYER_DEEP, pygame.Rect(px + 1, py + 11 - lift_r, 6, 3))

    # 斗篷：肩窄、下摆宽 —— 光是这个梯形剪影就够认人了
    cloak = [(px - 8, py - 9), (px + 8, py - 9), (px + 6, py + 1), (px + 11, py + 12),
             (px - 11, py + 12), (px - 6, py + 1)]
    pygame.draw.polygon(s, C_PLAYER_DEEP, cloak)
    # 左侧亮面（光从左上来）
    pygame.draw.polygon(s, C_PLAYER_DARK,
                        [(px - 8, py - 9), (px - 1, py - 9), (px - 1, py + 1), (px - 2, py + 12),
                         (px - 11, py + 12), (px - 6, py + 1)])
    # 下摆一道暗边 + 中缝（不然就是一个桶）
    s.fill(C_PLAYER_DEEP, pygame.Rect(px - 10, py + 10, 20, 2))
    pygame.draw.line(s, C_OUTLINE, (px, py + 12), (px, py + 6), 1)
    # 两只手：平时是短袖子 + 一点亮色袖口，看得出他有胳膊；
    # 捧着地图时改成「往胸前收」的两条，胳膊一弯，姿态就不一样了
    if not holding_map:
        for ax in (-11, 8):
            s.fill(C_PLAYER_DEEP, pygame.Rect(px + ax, py - 6, 3, 12))
    else:
        _draw_held_arms(s, px, py, facing)
    # 两侧亮边：轮廓在任何底色上都咬得住
    pygame.draw.line(s, C_PLAYER, (px - 8, py - 7), (px - 10, py + 10), 1)
    pygame.draw.line(s, C_PLAYER, (px + 8, py - 7), (px + 10, py + 10), 1)
    pygame.draw.polygon(s, C_OUTLINE, cloak, 1)

    # 背上那只包（第一幕捡到之后一直背着）
    if has_bag:
        _draw_worn_bag(s, px, py, facing)

    # 兜帽：一个尖顶的罩子，头缩在里面 —— 一眼就是「穿斗篷的人」
    hood = [(px - 8, py - 9), (px - 5, py - 23), (px + 5, py - 23), (px + 8, py - 9)]
    pygame.draw.polygon(s, C_PLAYER_DEEP, hood)
    pygame.draw.polygon(s, C_OUTLINE, hood, 1)

    # 第三幕的剑：平时斜垂在身侧，挥砍时整条刃扫过去
    if has_sword and not holding_map:
        _draw_sword_arm(s, px, py, facing, swing)

    # 胸口核心：一块会呼吸的方块（那是他的「码」）
    # 背对时看不见正面 —— 否则它会从背包上透出来；捧着地图时被纸挡住，也不用画
    if facing != 0 and not holding_map:
        k = (math.sin(t * 3.4) + 1.0) * 0.5
        s.fill(C_PLAYER, pygame.Rect(px - 3, py, 7, 3))
        s.fill(_mix(C_PLAYER, C_PLAYER_LIGHT, 0.30 + 0.55 * k), pygame.Rect(px - 2, py - 1, 5, 4))

    # 摊开的地图：只在按 M 时出现，压在胸口
    if holding_map:
        _draw_held_map(s, px, py, facing)

    # 头：方的，像一小块终端，缩在兜帽里
    head = pygame.Rect(px - 5, py - 21, 10, 10)
    pygame.draw.rect(s, C_PLAYER_DARK, head, border_radius=2)
    pygame.draw.rect(s, C_OUTLINE, head, 1, border_radius=2)

    # 面罩：一整条亮屏（朝向决定贴哪边；背对时只剩后脑的一条缝）
    if facing == 0:
        s.fill(C_PLAYER_DEEP, pygame.Rect(px - 4, py - 18, 9, 3))
    elif facing == 1:
        s.fill(C_PLAYER_LIGHT, pygame.Rect(px - 4, py - 18, 9, 4))
        s.fill(C_PLAYER_DEEP, pygame.Rect(px - 5, py - 14, 10, 1))   # 屏幕下沿一条暗边
    elif facing == 2:
        s.fill(C_PLAYER_LIGHT, pygame.Rect(px - 5, py - 18, 6, 4))
        s.fill(C_PLAYER_DEEP, pygame.Rect(px - 5, py - 14, 10, 1))
    else:
        s.fill(C_PLAYER_LIGHT, pygame.Rect(px - 1, py - 18, 6, 4))
        s.fill(C_PLAYER_DEEP, pygame.Rect(px - 5, py - 14, 10, 1))

    # 头上浮着的光标：I 型文本光标，外圈描黑（白格上也不会消失）；每 4 拍灭 1 拍
    if int(t * 2.2) % 4 != 3:
        gx = px + 9
        gy = py - 28 + int(math.sin(t * 1.7))
        s.fill(C_OUTLINE, pygame.Rect(gx, gy, 5, 11))           # 描边：白格上也看得见
        s.fill(C_PLAYER_LIGHT, pygame.Rect(gx + 1, gy + 1, 3, 9))


def _held_map_rect(px, py, facing):
    """捧在胸前那张小纸的矩形。背对时返回 None —— 纸在身体前面，被自己挡住。

    单独拿出来是因为手臂和纸要落在同一个位置上，两边各写一套迟早错开。
    """
    if facing == 0:
        return None
    if facing == 1:
        return pygame.Rect(px - 7, py - 2, 15, 9)
    if facing == 2:                                  # 朝左：纸偏左，露出侧面
        return pygame.Rect(px - 9, py - 2, 11, 9)
    return pygame.Rect(px - 1, py - 2, 11, 9)        # 朝右


def _draw_held_arms(s, px, py, facing):
    """捧图时的手臂：从肩膀往胸前收，袖口落在纸的两端（平时是两条垂直的短袖子）。"""
    r = _held_map_rect(px, py, facing)
    if r is None:                                    # 背对：胳膊在身前，看不见
        return
    for sx, hx in ((px - 8, r.left + 1), (px + 8, r.right - 1)):
        pygame.draw.line(s, C_PLAYER_DEEP, (sx, py - 6), (hx, r.centery), 3)


def _draw_held_map(s, px, py, facing):
    """摊开的地图（缩小版）：纸 + 两端卷头 + 三个定位图案的墨点 + 两只手。

    一眼就认得出来「他在看地图」，而不是「他站着不动」。
    """
    r = _held_map_rect(px, py, facing)
    if r is None:
        # 背对镜头：纸被自己挡住，只让纸边从剪影两侧露出来
        for sx in (-12, 10):
            s.fill(C_OUTLINE, pygame.Rect(px + sx, py, 2, 7))
            s.fill(C_ITEM_PAPER, pygame.Rect(px + sx, py + 1, 2, 5))
        return

    pygame.draw.rect(s, C_OUTLINE, r.inflate(2, 2))
    pygame.draw.rect(s, C_ITEM_PAPER, r)
    for ex in (r.left - 1, r.right):                 # 两端卷头
        s.fill(C_ITEM_LEATHER_DARK, pygame.Rect(ex, r.top - 1, 2, r.height + 2))
        s.fill(C_OUTLINE, pygame.Rect(ex, r.top - 1, 2, 1))
    for ox, oy in ((1, 1), (r.w - 4, 1), (1, r.h - 4)):   # 三个定位图案：这是那张码
        s.fill(C_CELL_BLACK, pygame.Rect(r.left + ox, r.top + oy, 3, 3))
        s.fill(C_ITEM_PAPER, pygame.Rect(r.left + ox + 1, r.top + oy + 1, 1, 1))
    for hx in (r.left - 2, r.right):                 # 双手：袖口压在纸的两个下角
        s.fill(C_OUTLINE, pygame.Rect(hx, r.bottom - 4, 4, 4))
        s.fill(C_PLAYER_LIGHT, pygame.Rect(hx + 1, r.bottom - 3, 2, 2))


def _draw_sword_arm(s, px, py, facing, swing=0.0):
    """手里的剑。`swing` = 挥砍剩余比例（0 = 没在挥）。

    只有 28px 一格，靠**一条亮刃 + 一道金色护手**认；挥砍时刃从 -80° 扫到 +80°，
    外加一道更亮的高光段，读起来才像"抡过去"，而不是剑突然变长了。
    """
    hand = (px + 6, py - 1) if facing != 2 else (px - 6, py - 1)
    base = {0: -90, 1: 90, 2: 180, 3: 0}[facing]
    if swing > 0:
        ang = base - 80 + 160 * (1.0 - swing)        # 从一侧扫到另一侧
        blade = (252, 253, 255)
    else:
        ang = 145 if facing == 2 else 35             # 平时：斜垂在握剑那只手的一侧
        blade = (198, 205, 214)
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    tip = (hand[0] + dx * 17, hand[1] + dy * 17)
    mid = (hand[0] + dx * 9, hand[1] + dy * 9)
    # 护手：垂直于刃的一小段金条
    gx, gy = -dy * 3.2, dx * 3.2
    pygame.draw.line(s, C_OUTLINE, (hand[0] - gx, hand[1] - gy), (hand[0] + gx, hand[1] + gy), 3)
    pygame.draw.line(s, C_ITEM, (hand[0] - gx, hand[1] - gy), (hand[0] + gx, hand[1] + gy), 1)
    # 刃：先描边再压亮面，暗底上才站得住
    pygame.draw.line(s, C_OUTLINE, hand, tip, 4)
    pygame.draw.line(s, blade, mid, tip, 2)
    pygame.draw.circle(s, C_ITEM, (int(hand[0]), int(hand[1])), 2)


def _draw_worn_bag(s, px, py, facing):
    """背在身上的包。

    四种朝向给四种读法：
      0 背对（朝上走）→ 包完整露在背上，这是玩家最常看到的一帧
      1 面向镜头     → 包被自己挡住，只看得见两条肩带和扣（不然像挂在胸前）
      2 / 3 左右走   → 包从肩膀后面探出来半个，压在斗篷边上
    """
    if facing == 1:
        # 只看得见肩带：两条窄带压在肩上，**避开胸口核心**（核心在 px-3…px+4 / py-1…py+3）
        for sx in (-8, 6):
            s.fill(C_OUTLINE, pygame.Rect(px + sx, py - 8, 2, 6))
            s.fill(C_ITEM_LEATHER_DARK, pygame.Rect(px + sx, py - 7, 1, 5))
            s.fill(C_ITEM, pygame.Rect(px + sx, py - 5, 1, 1))
        # 肩带在肩上连成一条：不然只剩两根悬空的竖线
        s.fill(C_ITEM_LEATHER_DARK, pygame.Rect(px - 8, py - 9, 16, 2))
        s.fill(C_OUTLINE, pygame.Rect(px - 8, py - 10, 16, 1))
        return

    if facing == 0:
        bx, by = px, py - 4                   # 背对：包背在肩胛位置，不是腰上
    elif facing == 2:                        # 朝左 → 包在右肩后
        bx, by = px + 5, py - 3
    else:                                    # 朝右 → 包在左肩后
        bx, by = px - 5, py - 3

    body = pygame.Rect(bx - 7, by - 6, 15, 14)
    pygame.draw.rect(s, C_OUTLINE, body.inflate(2, 2), border_radius=4)
    pygame.draw.rect(s, C_ITEM_LEATHER_DARK, body, border_radius=3)
    pygame.draw.rect(s, C_ITEM_LEATHER, body.inflate(-2, -2), border_radius=3)

    # 翻盖：压在上沿，右半暗一档
    flap = pygame.Rect(body.x, body.y, body.w, 5)
    pygame.draw.rect(s, _mix(C_ITEM_LEATHER, C_ITEM_LEATHER_DARK, 0.30), flap, border_radius=3)
    s.fill(C_OUTLINE, pygame.Rect(body.x, body.y + 5, body.w, 1))

    # 金属扣
    s.fill(C_OUTLINE, pygame.Rect(bx - 1, by - 2, 4, 4))
    s.fill(C_ITEM, pygame.Rect(bx, by - 1, 2, 2))

    # 两个侧袋：贴在包身两侧
    s.fill(C_ITEM_LEATHER_DARK, pygame.Rect(body.x - 2, by + 1, 2, 4))
    s.fill(C_ITEM_LEATHER_DARK, pygame.Rect(body.right, by + 1, 2, 4))

    # 肩带：从包顶往肩膀方向伸两条（背面看就是背带）
    if facing == 0:
        for sx in (-5, 4):
            pygame.draw.line(s, C_ITEM_LEATHER_DARK, (bx + sx, by - 6), (bx + sx, by - 11), 2)


# ==== 老者 ====

def draw_oldman(s, om, t=0.0):
    """老者：长袍 + 腰带 + 拐杖 + 胡子。背对时看不见脸（只看见一头灰发和兜帽）。"""
    px = int(round(om.pos.x))
    py = int(round(om.pos.y + math.sin(t * 1.7 + 1.0) * 0.9))

    shadow(s, px, py + 15, 28, 8, 74)

    # 长袍：肩窄下摆宽，人往上一站就有体积
    robe = [(px - 8, py - 11), (px + 8, py - 11), (px + 13, py + 15), (px - 13, py + 15)]
    pygame.draw.polygon(s, C_OLDMAN, robe)
    # 右半压暗（光从左上来）
    pygame.draw.polygon(s, C_OLDMAN_DARK,
                        [(px + 2, py - 11), (px + 8, py - 11), (px + 13, py + 15), (px + 4, py + 15)])
    # 褶子
    pygame.draw.line(s, C_OLDMAN_DARK, (px - 4, py - 5), (px - 7, py + 14), 1)
    pygame.draw.line(s, C_OLDMAN_DARK, (px - 1, py - 5), (px - 1, py + 14), 1)
    # 下摆一道厚边
    s.fill(C_OLDMAN_DARK, pygame.Rect(px - 12, py + 13, 24, 2))

    # 腰带 + 结
    s.fill(C_SASH, pygame.Rect(px - 10, py + 1, 20, 3))
    s.fill(C_OLDMAN_DARK, pygame.Rect(px + 4, py + 1, 3, 3))
    pygame.draw.polygon(s, C_OUTLINE, robe, 1)

    # 兜帽：整个头的轮廓（背对时它就是全部）
    hood = [(px - 8, py - 10), (px - 8, py - 16), (px - 4, py - 23),
            (px + 4, py - 23), (px + 8, py - 16), (px + 8, py - 10)]
    pygame.draw.polygon(s, C_OLDMAN_DARK, hood)
    pygame.draw.polygon(s, C_OUTLINE, hood, 1)

    hx, hy = px, py - 17
    if om.facing == 0:
        # 背对：兜帽里什么也看不见，只有后颈露出一点袍色 + 左侧一道亮边
        pygame.draw.circle(s, C_OLDMAN, (hx, hy + 5), 4)
        pygame.draw.line(s, C_OLDMAN, (hx - 6, hy - 5), (hx - 7, hy + 2), 1)
    else:
        # 正面/侧面：脸 + 头发 + 胡子 + 眼
        pygame.draw.circle(s, C_OLDMAN_SKIN, (hx, hy + 1), 6)
        pygame.draw.circle(s, C_OLDMAN_DARK, (hx, hy - 5), 6)
        pygame.draw.polygon(s, C_OLDMAN_LIGHT,
                            [(hx - 5, hy + 2), (hx + 5, hy + 2), (hx, hy + 9)])
        if om.facing == 1:                       # 正面：两只眼
            s.fill(C_CELL_BLACK, pygame.Rect(hx - 4, hy + 1, 2, 2))
            s.fill(C_CELL_BLACK, pygame.Rect(hx + 2, hy + 1, 2, 2))
        else:                                     # 侧面：一只，贴着朝向那边
            ex = hx + (-3 if om.facing == 2 else 2)
            s.fill(C_CELL_BLACK, pygame.Rect(ex, hy, 2, 2))

    # 手臂：从肩到拐杖上一只手
    pygame.draw.line(s, C_OUTLINE, (px + 5, py - 5), (px + 10, py + 1), 5)
    pygame.draw.line(s, C_OLDMAN_DARK, (px + 5, py - 5), (px + 10, py + 1), 3)
    pygame.draw.circle(s, C_OLDMAN, (px + 10, py + 1), 2)

    # 拐杖：先粗描一道再画杖身，就有边了；顶端一个木球；挥动时整根摆
    swing = math.sin(om.staff_t * 16.0) * 9.0 if om.staff_t > 0 else 0.0
    sx = px + 11
    top = (sx + swing, py - 21)
    bot = (sx + 2, py + 16)
    pygame.draw.line(s, C_OUTLINE, bot, top, 5)
    pygame.draw.line(s, C_STAFF, bot, top, 3)
    s.fill(C_SASH, pygame.Rect(int(top[0]) - 2, py + 6, 5, 2))
    knob = (int(top[0]), py - 22)
    pygame.draw.circle(s, C_STAFF, knob, 3)
    pygame.draw.circle(s, C_OUTLINE, knob, 3, 1)
    if om.staff_t > 0:
        # 挥杖时杖头亮一下：他在驱赶那两只
        k = 0.55 + 0.45 * abs(math.sin(om.staff_t * 16.0))
        pygame.draw.circle(s, _mix(C_STAFF, C_PLAYER, k), knob, 5, 1)


# ==== 红怪 ====

def draw_red(s, cx, cy, radius=9, t=0.0, phase=0.0, hunting=False, look=None, glow=None,
             base=None, dark=None, ring=None):
    """红怪：一块会呼吸的烂肉 + 一只盯着目标的眼 + 三根触须。

    hunting（场上没有黑域、它转来追你）时会多一圈红环 —— 不看面板也知道它盯上你了。
    look 是它「在看哪儿」的世界坐标。
    """
    base = base or C_MONSTER
    dark = dark or C_MONSTER_DARK
    px, py = int(round(cx)), int(round(cy))

    if glow is not None:
        s.blit(glow, (px - glow.get_width() // 2, py - glow.get_height() // 2))

    # 触须先画，压在身体底下
    for i in range(3):
        a = math.radians(-150 + i * 120) + math.sin(t * 6.0 + i * 2.0 + phase) * 0.35
        r0 = radius * 0.7
        r1 = radius + 5 + math.sin(t * 9.0 + i + phase) * 1.8
        tip = (px + math.cos(a) * r1, py + math.sin(a) * r1)
        pygame.draw.line(s, dark, (px + math.cos(a) * r0, py + math.sin(a) * r0), tip, 2)
        s.fill(dark, pygame.Rect(int(tip[0]) - 1, int(tip[1]) - 1, 2, 2))

    # 身体：外圈暗、内圈亮，两层都在扭
    body = _blob(px, py, radius, 9, t * 5.2, phase, 2.0)
    pygame.draw.polygon(s, dark, body)
    pygame.draw.polygon(s, base, _blob(px, py, radius - 3.5, 9, -t * 4.0, phase + 1.0, 1.2))
    pygame.draw.polygon(s, C_CELL_BLACK, body, 1)

    # 湿的那点亮斑（左上）
    s.fill(_mix(base, (255, 255, 255), 0.55), pygame.Rect(px - 5, py - 5, 2, 2))

    # 眼：一只，瞳孔朝目标偏 —— 眼睛要小，周围得留出肉
    ex, ey = float(px), float(py)
    if look is not None:
        dx, dy = look[0] - cx, look[1] - cy
        d = math.hypot(dx, dy) or 1.0
        ex, ey = px + dx / d * 2.2, py + dy / d * 2.2
    pygame.draw.ellipse(s, (34, 3, 12), pygame.Rect(px - 4, py - 3, 8, 6))
    pygame.draw.circle(s, C_MONSTER_CORE, (int(ex), int(ey)), 3 if hunting else 2)

    if hunting:
        # 追人：四段短弧套在外面，像瞄准框（整圈会像个气泡）
        r = int(radius + 5 + math.sin(t * 8.0 + phase) * 1.2)
        box = pygame.Rect(px - r, py - r, r * 2, r * 2)
        for i in range(4):
            a0 = math.radians(45 + i * 90 - 22)
            pygame.draw.arc(s, ring or C_MONSTER_RING, box, a0, a0 + math.radians(44), 2)


def draw_oldman_down(s, om, t=0.0):
    """倒下的老者：侧躺在地上的一团袍子 + 掉在手边的拐杖。

    只有 28px 一格，画不出「倒下的姿势」，只能靠**横向的一坨 + 头在一端** + 掉落的拐杖认出来。
    """
    px, py = int(round(om.pos.x)), int(round(om.pos.y))
    shadow(s, px, py + 9, 38, 9, 88)

    body = pygame.Rect(px - 16, py - 5, 32, 13)
    pygame.draw.ellipse(s, C_OLDMAN, body)
    pygame.draw.ellipse(s, C_OLDMAN_DARK, body.inflate(-10, -5))
    pygame.draw.ellipse(s, C_CELL_BLACK, body, 1)
    # 头在一端（白胡子那撮）
    pygame.draw.circle(s, C_OLDMAN_LIGHT, (px - 15, py + 1), 4)
    pygame.draw.circle(s, C_CELL_BLACK, (px - 15, py + 1), 4, 1)
    # 拐杖脱手，倒在旁边
    pygame.draw.line(s, C_OUTLINE, (px + 9, py + 9), (px + 24, py + 3), 3)
    pygame.draw.line(s, C_PROP_TOOL, (px + 9, py + 9), (px + 24, py + 3), 1)


def draw_dead_red(s, cx, cy):
    """地上那只已经死掉的红怪：瘪下去、X 眼、渗出来的一小道。"""
    px, py = int(round(cx)), int(round(cy))
    shadow(s, px, py + 3, 22, 6, 66)
    body = pygame.Rect(px - 9, py - 3, 18, 9)
    pygame.draw.ellipse(s, C_PROP_DEAD, body)
    pygame.draw.ellipse(s, C_CELL_BLACK, body, 1)
    for dx in (-5, 1):
        pygame.draw.line(s, C_CELL_BLACK, (px + dx, py - 1), (px + dx + 3, py + 2), 1)
        pygame.draw.line(s, C_CELL_BLACK, (px + dx, py + 2), (px + dx + 3, py - 1), 1)
    pygame.draw.line(s, C_PROP_DEAD, (px + 7, py + 4), (px + 11, py + 7), 2)


# ==== 道具（清屏后浮出的 BAG / MAP）====
# 28px 的格子，所以只画「一眼能认出来」的特征：
#   背包 = 翻盖 + 金属扣 + 两条肩带；地图 = 斜放的纸 + 折痕 + 路线 + 红点。
# 都垫一圈 C_OUTLINE，白格和褐底上都咬得住。

ITEM_W, ITEM_H = 22, 24

_GLOW_CACHE = {}


def _item_glow(s, cx, cy, w=30, h=12, alpha=150):
    """道具脚下一圈金色椭圆：像掉落物被一束光罩着。
    弥散光在 28px 的格子里根本看不出来，一圈亮边才认得出来。"""
    key = (w, h, alpha)
    surf = _GLOW_CACHE.get(key)
    if surf is None:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (*C_ITEM, int(alpha * 0.45)), surf.get_rect(), 4)
        pygame.draw.ellipse(surf, (*C_ITEM, alpha), surf.get_rect().inflate(-6, -4), 1)
        _GLOW_CACHE[key] = surf
    s.blit(surf, (cx - w // 2, cy - h // 2))


def draw_item(s, kind, cx, cy, t=0.0, rise=0, glow=True):
    """道具。cx/cy 是中心，rise 是浮起动画的像素偏移（越大越靠下）。

    glow=True 是「掉在地上」的样子（脚下一圈金光 + 影子）；放进物品栏时传 False ——
    面板里光和影子都显得脏。
    """
    px, py = int(round(cx)), int(round(cy + rise))
    if glow:
        _item_glow(s, px, py + 9)
    if kind == "map":
        _draw_map_item(s, px, py, t, glow)
    elif kind == "sword":
        _draw_sword_item(s, px, py, t, glow)
    else:
        _draw_bag_item(s, px, py, t, glow)


def _draw_sword_item(s, px, py, t, ground=True):
    """剑：直刃 + 一侧开锋 + 护手 + 缠皮柄 + 金首。

    只有 22px 宽的地方，画不出「造型」，只能靠**一条亮刃 + 一道暗脊**认出来。
    刃尖略微上抬（`-2`），不然和一根铁条没区别。
    """
    py = int(py + math.sin(t * 2.2) * 0.8)
    if ground:
        shadow(s, px, py + 13, 20, 6, 72)

    tip = py - 15
    # 刃：暗底一层（描边）+ 亮面一层 + 高光一条
    pygame.draw.polygon(s, C_OUTLINE, [(px - 3, py + 1), (px - 3, tip + 3),
                                       (px, tip - 2), (px + 3, tip + 3), (px + 3, py + 1)])
    pygame.draw.polygon(s, (226, 230, 236), [(px - 2, py), (px - 2, tip + 4),
                                             (px, tip), (px + 2, tip + 4), (px + 2, py)])
    s.fill((252, 253, 255), pygame.Rect(px - 1, tip + 5, 1, py - tip - 7))    # 高光
    s.fill((150, 158, 170), pygame.Rect(px + 1, tip + 5, 1, py - tip - 7))    # 暗脊
    # 护手：一条横档，两端各一颗金钉
    s.fill(C_OUTLINE, pygame.Rect(px - 7, py + 1, 14, 4))
    s.fill(C_ITEM, pygame.Rect(px - 6, py + 2, 12, 2))
    s.fill(C_ITEM, pygame.Rect(px - 7, py + 2, 2, 2))
    s.fill(C_ITEM, pygame.Rect(px + 5, py + 2, 2, 2))
    # 柄 + 金首
    s.fill(C_OUTLINE, pygame.Rect(px - 2, py + 5, 4, 8))
    s.fill(C_ITEM_LEATHER_DARK, pygame.Rect(px - 1, py + 5, 2, 8))
    s.fill(C_ITEM, pygame.Rect(px - 2, py + 13, 4, 2))


def _draw_bag_item(s, px, py, t, ground=True):
    """背包：**上窄下宽**的包身 + 提手 + 翻盖 + 金属扣 + 两个侧袋。"""
    py = int(py + math.sin(t * 2.6) * 0.8)
    if ground:
        shadow(s, px, py + 11, 22, 6, 72)

    # 提带：包顶一条横带 + 两端金属环（22px 宽里画拱形会糊成一团黑，横带才认得出来）
    s.fill(C_OUTLINE, pygame.Rect(px - 8, py - 12, 16, 4))
    s.fill(C_ITEM_LEATHER_DARK, pygame.Rect(px - 7, py - 11, 14, 2))
    s.fill(C_ITEM, pygame.Rect(px - 7, py - 12, 2, 2))
    s.fill(C_ITEM, pygame.Rect(px + 5, py - 12, 2, 2))

    # 包身：上窄下宽（背包鼓在下面）
    body = [(px - 7, py - 7), (px + 7, py - 7), (px + 10, py + 9), (px - 10, py + 9)]
    pygame.draw.polygon(s, C_ITEM_LEATHER_DARK, body)
    pygame.draw.polygon(s, C_ITEM_LEATHER,
                        [(px - 6, py - 6), (px + 6, py - 6), (px + 8, py + 8), (px - 8, py + 8)])

    # 两个侧袋：左右各嵌一小块，包就不只是个梯形
    for sx in (-10, 7):
        s.fill(C_ITEM_LEATHER_DARK, pygame.Rect(px + sx, py, 3, 6))
        s.fill(_mix(C_ITEM_LEATHER, C_ITEM_LEATHER_DARK, 0.45), pygame.Rect(px + sx, py, 2, 5))

    # 翻盖：盖住上半，右半边压暗
    flap = [(px - 7, py - 9), (px + 7, py - 9), (px + 8, py + 1), (px - 8, py + 1)]
    pygame.draw.polygon(s, C_ITEM_LEATHER, flap)
    pygame.draw.polygon(s, _mix(C_ITEM_LEATHER, C_ITEM_LEATHER_DARK, 0.55),
                        [(px + 1, py - 9), (px + 7, py - 9), (px + 8, py + 1), (px + 1, py + 1)])
    s.fill(C_OUTLINE, pygame.Rect(px - 8, py + 1, 16, 1))                        # 盖沿的厚边
    pygame.draw.line(s, C_ITEM_LEATHER_DARK, (px - 7, py + 3), (px + 7, py + 3), 1)   # 缝线

    # 金属扣：整个道具唯一的高光点
    s.fill(C_OUTLINE, pygame.Rect(px - 2, py + 1, 5, 5))
    s.fill(C_ITEM, pygame.Rect(px - 1, py + 2, 3, 3))

    pygame.draw.polygon(s, C_OUTLINE, flap, 1)
    pygame.draw.polygon(s, C_OUTLINE, body, 1)


def _draw_map_item(s, px, py, t, ground=True):
    """地图：**左边卷成筒、右边展开**的纸 —— 半卷的才像地图，平摊的像便签。"""
    py = int(py + math.sin(t * 2.6 + 1.0) * 0.8)
    if ground:
        shadow(s, px, py + 10, 24, 6, 72)

    # 展开的纸：右半，右上角微微掀起
    paper = [(px - 5, py - 6), (px + 8, py - 8), (px + 10, py + 5),
             (px + 7, py + 8), (px - 5, py + 8)]
    pygame.draw.polygon(s, C_ITEM_PAPER, paper)
    pygame.draw.polygon(s, C_ITEM_PAPER_DARK, [(px + 7, py + 8), (px + 10, py + 5), (px + 8, py + 1)])

    # 折痕一道（只有一道，多了解不出是折痕，只是脏）
    pygame.draw.line(s, C_ITEM_PAPER_DARK, (px + 2, py - 7), (px + 2, py + 8), 1)

    # 路线 + 红点：地图的读法全靠这条折线和那一点红
    pygame.draw.line(s, C_ITEM_INK, (px - 3, py + 5), (px + 1, py - 2), 1)
    pygame.draw.line(s, C_ITEM_INK, (px + 1, py - 2), (px + 7, py + 2), 1)
    s.fill(C_ITEM_MARK, pygame.Rect(px + 6, py, 3, 3))   # 纸色底上够清楚，不用描边

    pygame.draw.polygon(s, C_OUTLINE, paper, 1)

    # 左边的卷筒：压在纸边上，两道横纹表示卷了几层
    tube = pygame.Rect(px - 11, py - 7, 7, 16)
    pygame.draw.rect(s, C_ITEM_PAPER_DARK, tube, border_radius=3)
    s.fill(C_ITEM_PAPER, pygame.Rect(tube.x + 2, tube.y + 1, 2, tube.h - 2))
    for dy in (4, 11):
        pygame.draw.line(s, C_ITEM_INK, (tube.x + 1, tube.y + dy), (tube.right - 2, tube.y + dy), 1)
    pygame.draw.rect(s, C_OUTLINE, tube, 1, border_radius=3)
