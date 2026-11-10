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
    C_CELL_BLACK, C_MONSTER, C_MONSTER_CORE, C_MONSTER_DARK, C_MONSTER_RING, C_OLDMAN,
    C_OLDMAN_DARK, C_OLDMAN_LIGHT, C_OUTLINE, C_PLAYER, C_PLAYER_DARK, C_PLAYER_DEEP,
    C_PLAYER_LIGHT, C_PROP_DEAD, C_SASH, C_STAFF
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

def draw_sequencer(s, cx, cy, facing=1, t=0.0, moving=False, glow=None):
    """读码的人：深色斗篷 + 一条发光面罩 + 头上一块闪烁的光标。

    他不是「一个方块」，而是「正在被输入的那一行」—— 光标才是身份标识。
    朝向：0 上（背对）1 下 2 左 3 右。
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
    # 两只手：短袖子 + 一点亮色袖口，看得出他有胳膊
    for ax in (-11, 8):
        s.fill(C_PLAYER_DEEP, pygame.Rect(px + ax, py - 6, 3, 12))
    # 两侧亮边：轮廓在任何底色上都咬得住
    pygame.draw.line(s, C_PLAYER, (px - 8, py - 7), (px - 10, py + 10), 1)
    pygame.draw.line(s, C_PLAYER, (px + 8, py - 7), (px + 10, py + 10), 1)
    pygame.draw.polygon(s, C_OUTLINE, cloak, 1)

    # 兜帽：一个尖顶的罩子，头缩在里面 —— 一眼就是「穿斗篷的人」
    hood = [(px - 8, py - 9), (px - 5, py - 23), (px + 5, py - 23), (px + 8, py - 9)]
    pygame.draw.polygon(s, C_PLAYER_DEEP, hood)
    pygame.draw.polygon(s, C_OUTLINE, hood, 1)

    # 胸口核心：一块会呼吸的方块（那是他的「码」）
    k = (math.sin(t * 3.4) + 1.0) * 0.5
    s.fill(C_PLAYER, pygame.Rect(px - 3, py, 7, 3))
    s.fill(_mix(C_PLAYER, C_PLAYER_LIGHT, 0.30 + 0.55 * k), pygame.Rect(px - 2, py - 1, 5, 4))

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
        pygame.draw.circle(s, C_OLDMAN, (hx, hy + 1), 6)
        pygame.draw.circle(s, C_OLDMAN_DARK, (hx, hy - 5), 6)
        pygame.draw.polygon(s, C_OLDMAN_LIGHT,
                            [(hx - 5, hy + 2), (hx + 5, hy + 2), (hx, hy + 9)])
        ex = hx + (-3 if om.facing == 2 else 2 if om.facing == 3 else 0)
        ey = hy + (0 if om.facing in (2, 3) else 1)
        s.fill(C_CELL_BLACK, pygame.Rect(ex, ey, 2, 2))

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
             base=None, dark=None):
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
            pygame.draw.arc(s, C_MONSTER_RING, box, a0, a0 + math.radians(44), 2)


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
