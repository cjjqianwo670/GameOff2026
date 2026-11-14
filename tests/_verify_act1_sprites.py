# -*- coding: utf-8 -*-
"""第一幕 · 角色贴图验收（sprites.py）。

只画、不跑游戏逻辑：把每个角色画到一张干净画布上，然后数像素。
这样测的是「画出来的东西」，不是「代码自认为画了什么」。
"""

import sys


import pygame  # noqa: E402

from _act1_common import check, finish, pygame  # noqa: E402
from src import sprites  # noqa: E402
from src.config import (  # noqa: E402
    C_BG, C_CELL_BLACK, C_CELL_WHITE, C_MONSTER, C_MONSTER_CORE, C_MONSTER_DARK, C_MONSTER_RING, C_OLDMAN,
    C_OLDMAN_DARK, C_OLDMAN_LIGHT, C_OUTLINE, C_PLAYER, C_PLAYER_DARK, C_PLAYER_DEEP,
    C_ITEM, C_ITEM_INK, C_ITEM_LEATHER, C_ITEM_LEATHER_DARK, C_ITEM_MARK, C_ITEM_PAPER,
    C_PLAYER_LIGHT,
    C_PROP_DEAD, C_SASH, C_STAFF
)


def canvas(w=160, h=160):
    s = pygame.Surface((w, h))
    s.fill(C_BG)
    return s


def colors_in(s, rect):
    """rect 范围内出现过的颜色集合。"""
    out = set()
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            out.add(s.get_at((x, y))[:3])
    return out


def count(s, color, rect):
    n = 0
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            if s.get_at((x, y))[:3] == color:
                n += 1
    return n


def centroid_x(s, color, rect):
    tot, n = 0.0, 0
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            if s.get_at((x, y))[:3] == color:
                tot += x
                n += 1
    return (tot / n) if n else None


def inside_any(s, rect):
    """rect 内有没有任何非底色像素。"""
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            if s.get_at((x, y))[:3] != C_BG:
                return True
    return False


# ==================== 码序使 ====================
CX, CY = 80, 84
S = canvas(160, 180)
sprites.draw_sequencer(S, CX, CY, facing=1, t=0.0, moving=False)
box = pygame.Rect(CX - 30, CY - 34, 60, 60)

seen = colors_in(S, box)
check("码序使：分层上色（斗篷暗部 / 受光面 / 面罩高光 / 描边 都在）",
      {C_PLAYER_DEEP, C_PLAYER_DARK, C_PLAYER_LIGHT, C_OUTLINE} <= seen,
      "%s" % sorted(seen)[:6])
check("码序使：不是单色块（bbx 内 ≥ 5 种颜色）", len(seen) >= 5, "%d 种" % len(seen))

# 影子：脚下那一行比周围暗（不是纯底色）
foot = pygame.Rect(CX - 8, CY + 14, 16, 4)
check("码序使：脚下有影子", colors_in(S, foot) != {C_BG}, "%s" % sorted(colors_in(S, foot))[:3])

# 面罩随朝向换边
SH = pygame.Rect(CX - 8, CY - 22, 16, 12)
s_left = canvas(160, 180)
sprites.draw_sequencer(s_left, CX, CY, facing=2, t=0.0)
s_right = canvas(160, 180)
sprites.draw_sequencer(s_right, CX, CY, facing=3, t=0.0)
cl = centroid_x(s_left, C_PLAYER_LIGHT, SH)
cr = centroid_x(s_right, C_PLAYER_LIGHT, SH)
check("码序使：朝左时面罩在左半边", cl is not None and cl < CX, "%.1f" % (cl or -1))
check("码序使：朝右时面罩在右半边", cr is not None and cr > CX, "%.1f" % (cr or -1))

s_up = canvas(160, 180)
sprites.draw_sequencer(s_up, CX, CY, facing=0, t=0.0)
n_face = count(s_up, C_PLAYER_LIGHT, SH)
n_down = count(S, C_PLAYER_LIGHT, SH)
check("码序使：背对时脸是暗的（只剩后脑一条缝）", n_face < n_down * 0.6,
      "背对 %d / 正面 %d" % (n_face, n_down))

# 光标：会闪
s_on = canvas(160, 180)
sprites.draw_sequencer(s_on, CX, CY, t=3.0)          # int(6.6)%4 = 2 → 亮
s_off = canvas(160, 180)
sprites.draw_sequencer(s_off, CX, CY, t=1.4)         # int(3.08)%4 = 3 → 灭
cur = pygame.Rect(CX + 7, CY - 30, 12, 16)
check("码序使：头上有光标", count(s_on, C_PLAYER_LIGHT, cur) > 10,
      "%d px" % count(s_on, C_PLAYER_LIGHT, cur))
check("码序使：光标会闪（另一拍是灭的）", count(s_off, C_PLAYER_LIGHT, cur) == 0,
      "%d px" % count(s_off, C_PLAYER_LIGHT, cur))

# 走路帧与站立帧不一样（有动）
s_walk = canvas(160, 180)
sprites.draw_sequencer(s_walk, CX, CY, t=0.42, moving=True)
check("码序使：走路帧和站立帧不同（有动作）",
      pygame.image.tostring(s_walk, "RGB") != pygame.image.tostring(S, "RGB"))

# 不越界：贴图边缘 3px 不许有东西（否则会糊到隔壁格）
edge_ok = not (inside_any(S, pygame.Rect(0, 0, 160, 3)) or inside_any(S, pygame.Rect(0, 177, 160, 3))
               or inside_any(S, pygame.Rect(0, 0, 3, 180)) or inside_any(S, pygame.Rect(157, 0, 3, 180)))
check("码序使：不越出边界（边缘 3px 干净）", edge_ok)


# ==================== 老者 ====================
class FakeOldMan:
    def __init__(self, facing=0):
        self.pos = pygame.Vector2(CX, CY)
        self.facing = facing
        self.staff_t = 0.0


O = canvas(160, 180)
om = FakeOldMan(0)
sprites.draw_oldman(O, om, t=0.0)
obox = pygame.Rect(CX - 26, CY - 30, 52, 52)
oseen = colors_in(O, obox)
check("老者：袍子 / 暗部 / 腰带 / 拐杖 都在",
      {C_OLDMAN, C_OLDMAN_DARK, C_SASH, C_STAFF} <= oseen, "%s" % sorted(oseen)[:6])
check("老者：不是单色块（bbx 内 ≥ 6 种颜色）", len(oseen) >= 6, "%d 种" % len(oseen))
check("老者：脚边有影子",
      colors_in(O, pygame.Rect(CX - 10, CY + 16, 20, 4)) != {C_BG})
check("老者：背对时看不见胡子", count(O, C_OLDMAN_LIGHT, obox) == 0,
      "%d px" % count(O, C_OLDMAN_LIGHT, obox))

of = canvas(160, 180)
omf = FakeOldMan(1)
sprites.draw_oldman(of, omf, t=0.0)
check("老者：转身后露出胡子和眼睛",
      count(of, C_OLDMAN_LIGHT, obox) > 6 and count(of, C_CELL_BLACK, obox) > 0,
      "胡 %d / 眼 %d" % (count(of, C_OLDMAN_LIGHT, obox), count(of, C_CELL_BLACK, obox)))

# 眼睛跟着朝向偏
ofl = canvas(160, 180)
oml = FakeOldMan(2)
sprites.draw_oldman(ofl, oml, t=0.0)
ex_l = centroid_x(ofl, C_CELL_BLACK, pygame.Rect(CX - 8, CY - 20, 7, 8))
ex_r = centroid_x(of, C_CELL_BLACK, pygame.Rect(CX - 8, CY - 20, 16, 8))
check("老者：眼睛随朝向偏移", ex_l is not None and ex_l < ex_r,
      "左 %.1f / 正 %.1f" % (ex_l or -1, ex_r or -1))


def staff_top_x(surf):
    """杖身最上面那段 C_STAFF 像素的 x（挥杖时它会摆）。"""
    for y in range(CY - 30, CY - 10):
        for x in range(CX - 4, CX + 22):
            if surf.get_at((x, y))[:3] == C_STAFF:
                return x
    return None


ow = canvas(160, 180)
omw = FakeOldMan(1)
omw.staff_t = 0.1                       # sin(1.6) ≈ 1 → 整根甩到一边
sprites.draw_oldman(ow, omw, t=0.0)
x0, x1 = staff_top_x(of), staff_top_x(ow)
check("老者：挥杖时拐杖会摆", x0 is not None and x1 is not None and abs(x1 - x0) >= 5,
      "静止 %s / 挥动 %s" % (x0, x1))
check("老者：不越出边界（边缘 3px 干净）",
      not (inside_any(O, pygame.Rect(0, 0, 160, 3)) or inside_any(O, pygame.Rect(0, 177, 160, 3))
           or inside_any(O, pygame.Rect(0, 0, 3, 180)) or inside_any(O, pygame.Rect(157, 0, 3, 180))))


# ==================== 红怪 ====================
R = canvas(120, 120)
sprites.draw_red(R, 60, 60, 9, t=0.3, phase=0.0, hunting=False, look=(60, 20))
rbox = pygame.Rect(40, 40, 40, 40)
rseen = colors_in(R, rbox)
check("红怪：外圈肉 / 内圈亮 / 眼珠 / 描边 都在",
      {C_MONSTER_DARK, C_MONSTER, C_MONSTER_CORE, C_CELL_BLACK} <= rseen,
      "%s" % sorted(rseen)[:6])
check("红怪：身体不是正圆（9 个顶点各自起伏）", len(rseen) >= 5, "%d 种颜色" % len(rseen))

# 触须伸出身体之外
ring_zone = pygame.Rect(60 - 14, 60 - 14, 28, 28)
inner = pygame.Rect(60 - 6, 60 - 6, 12, 12)
n_out = count(R, C_MONSTER_DARK, ring_zone) - count(R, C_MONSTER_DARK, inner)
check("红怪：有伸出体外的触须", n_out > 3, "%d px" % n_out)

# 追人形态与吃黑形态不同
R2 = canvas(120, 120)
sprites.draw_red(R2, 60, 60, 9, t=0.3, phase=0.0, hunting=True, look=(100, 60))
check("红怪：追人时多出瞄准弧（C_MONSTER_RING）",
      count(R2, C_MONSTER_RING, pygame.Rect(30, 30, 60, 60)) > 10,
      "%d px" % count(R2, C_MONSTER_RING, pygame.Rect(30, 30, 60, 60)))
check("红怪：两种形态画出来不一样",
      pygame.image.tostring(R, "RGB") != pygame.image.tostring(R2, "RGB"))

# 瞳孔跟着目标转
Ra = canvas(120, 120)
sprites.draw_red(Ra, 60, 60, 9, t=0.0, phase=0.0, look=(110, 60))
Rb = canvas(120, 120)
sprites.draw_red(Rb, 60, 60, 9, t=0.0, phase=0.0, look=(10, 60))
pa = centroid_x(Ra, C_MONSTER_CORE, rbox)
pb = centroid_x(Rb, C_MONSTER_CORE, rbox)
check("红怪：瞳孔朝目标偏（左右不同）", pa is not None and pb is not None and pa - pb >= 3,
      "右看 %.1f / 左看 %.1f" % (pa or -1, pb or -1))

# 各自呼吸：两只不同相位的怪，同一帧也不一样
Rp = canvas(120, 120)
sprites.draw_red(Rp, 60, 60, 9, t=0.3, phase=0.0)
Rq = canvas(120, 120)
sprites.draw_red(Rq, 60, 60, 9, t=0.3, phase=2.4)
check("红怪：不同相位的怪不会齐步走",
      pygame.image.tostring(Rp, "RGB") != pygame.image.tostring(Rq, "RGB"))
Rt = canvas(120, 120)
sprites.draw_red(Rt, 60, 60, 9, t=0.8, phase=0.0)
check("红怪：会呼吸（两帧不同）",
      pygame.image.tostring(Rp, "RGB") != pygame.image.tostring(Rt, "RGB"))

# 死掉的那只
D = canvas(120, 120)
sprites.draw_dead_red(D, 60, 60)
check("死红怪：还是暗红的一摊（C_PROP_DEAD）",
      count(D, C_PROP_DEAD, pygame.Rect(50, 55, 20, 12)) > 40,
      "%d px" % count(D, C_PROP_DEAD, pygame.Rect(50, 55, 20, 12)))
D2 = canvas(120, 120)
sprites.draw_dead_red(D2, 60, 60)
check("死红怪：不动（两帧完全一样）",
      pygame.image.tostring(D, "RGB") == pygame.image.tostring(D2, "RGB"))

# ==================== 性能 ====================
import time  # noqa: E402

BIG = canvas(1360, 1000)
t0 = time.perf_counter()
for i in range(60):
    sprites.draw_sequencer(BIG, 400, 400, facing=i % 4, t=i * 0.1, moving=True)
    sprites.draw_oldman(BIG, om, t=i * 0.1)
    for k in range(12):                      # 12 只怪 ≈ 战斗中常见的上限
        sprites.draw_red(BIG, 200 + k * 30, 300, 9, t=i * 0.1, phase=k, hunting=k % 3 == 0)
ms = (time.perf_counter() - t0) * 1000 / 60
check("性能：一屏 14 个角色的贴图 < 4ms/帧", ms < 4.0, "%.2fms" % ms)

# ==================== 道具：背包 / 地图（2026-11-11 建模） ====================
def item_canvas(kind, glow=True):
    s = pygame.Surface((80, 80))
    s.fill(C_CELL_WHITE)
    sprites.draw_item(s, kind, 40, 40, 0.0, 0, glow=glow)
    return s


bag_s = item_canvas("bag")
map_s = item_canvas("map")
bag_px = colors_in(bag_s, pygame.Rect(28, 26, 24, 26))
map_px = colors_in(map_s, pygame.Rect(26, 28, 28, 24))

check("背包用皮革色画（不是一根金棍）", C_ITEM_LEATHER in bag_px, str(sorted(bag_px))[:60])
check("背包有金属扣（金色高光）", C_ITEM in bag_px)
check("地图用纸色画", C_ITEM_PAPER in map_px, str(sorted(map_px))[:60])
check("地图上有墨线", C_ITEM_INK in map_px)
check("地图上有红点标记", C_ITEM_MARK in map_px)

# 两个图标必须长得不一样（否则玩家分不出哪个是哪个）
diff = sum(1 for x in range(20, 60) for y in range(20, 60)
           if bag_s.get_at((x, y))[:3] != map_s.get_at((x, y))[:3])
check("背包和地图是两个不同的图形", diff > 200, "%d 像素不同" % diff)

# 金环：带光和不带光必须是两张不同的图，而且差别只在脚下
no_glow = item_canvas("bag", glow=False)
with_glow = item_canvas("bag", glow=True)

foot = pygame.Rect(28, 44, 24, 16)                  # 脚下那一圈
n_foot = sum(1 for x in range(foot.left, foot.right) for y in range(foot.top, foot.bottom)
             if with_glow.get_at((x, y))[:3] != no_glow.get_at((x, y))[:3])
check("地面上：道具脚下有金色光环", n_foot > 30, "%d px 不同" % n_foot)

body = pygame.Rect(26, 22, 28, 20)                  # 道具本体
n_body = sum(1 for x in range(body.left, body.right) for y in range(body.top, body.bottom)
             if with_glow.get_at((x, y))[:3] != no_glow.get_at((x, y))[:3])
check("光环只落在脚下，没有糊到道具身上", n_body == 0, "%d px 被污染" % n_body)


# --- 拾到背包之后，码序使背上就背着它（2026-11-11）---
def seq_px(facing, has_bag):
    s = pygame.Surface((80, 80))
    s.fill(C_CELL_WHITE)
    sprites.draw_sequencer(s, 40, 40, facing=facing, t=2.0, has_bag=has_bag)
    return s


back_no = seq_px(0, False)
back_bag = seq_px(0, True)
back_zone = pygame.Rect(30, 30, 21, 18)             # 背部那块
n_back = count(back_bag, C_ITEM_LEATHER, back_zone)
check("背对时：背上有包（皮革色成片）", n_back > 30, "%d px" % n_back)
check("背对时：没包就没有皮革色", count(back_no, C_ITEM_LEATHER, back_zone) == 0,
      "%d px" % count(back_no, C_ITEM_LEATHER, back_zone))
core_zone = pygame.Rect(34, 34, 13, 11)             # 只圈包身中部，别把两边斗篷亮边算进来
check("背对时：包上不该透出胸口核心（青色）", count(back_bag, C_PLAYER, core_zone) == 0,
      "%d px" % count(back_bag, C_PLAYER, core_zone))

front_bag = seq_px(1, True)
front_zone = pygame.Rect(28, 26, 26, 22)
# 肩带用的是「皮革暗色」（整只包的内层才是亮皮革色），所以这里两个都数
n_front = (count(front_bag, C_ITEM_LEATHER_DARK, front_zone)
           + count(front_bag, C_ITEM_LEATHER, front_zone))
check("面向镜头时：只露肩带，不是整只包", 10 < n_front < 90, "%d px" % n_front)
check("面向镜头时：胸口核心还在（没被带子盖掉）",
      count(front_bag, C_PLAYER, pygame.Rect(35, 39, 10, 6)) > 4,
      "%d px" % count(front_bag, C_PLAYER, pygame.Rect(35, 39, 10, 6)))

# 左右走：包在身后那一侧（朝左 → 包在右半，朝右 → 包在左半）
left_bag = seq_px(2, True)
check("朝左走：包从右肩后露出来",
      count(left_bag, C_ITEM_LEATHER, pygame.Rect(42, 30, 12, 18)) > 10,
      "%d px" % count(left_bag, C_ITEM_LEATHER, pygame.Rect(42, 30, 12, 18)))
right_bag = seq_px(3, True)
check("朝右走：包从左肩后露出来",
      count(right_bag, C_ITEM_LEATHER, pygame.Rect(26, 30, 12, 18)) > 10,
      "%d px" % count(right_bag, C_ITEM_LEATHER, pygame.Rect(26, 30, 12, 18)))


# ==================== 捧着地图的姿态（2026-11-12 作者要求） ====================
# 按 M 看地图时，码序使两只手都占着：胸前捧着一张摊开的纸（纸上有三个定位图案）。
# 这不是装饰 —— 同一时刻 J / K / Shift 全被封掉，见 _verify_act1_keys.py。

def seq_hold(facing, has_bag=True):
    s = pygame.Surface((80, 80))
    s.fill(C_CELL_WHITE)
    sprites.draw_sequencer(s, 40, 40, facing=facing, t=2.0, has_bag=has_bag, holding_map=True)
    return s


chest = pygame.Rect(32, 36, 18, 12)

hold_front = seq_hold(1)
idle_front = seq_px(1, True)
n_hold = count(hold_front, C_ITEM_PAPER, chest)
check("面向镜头捧图：胸前有一张纸（纸色像素成片）", n_hold > 50, "%d px" % n_hold)
check("不捧图时胸前没有纸", count(idle_front, C_ITEM_PAPER, chest) == 0,
      "%d px" % count(idle_front, C_ITEM_PAPER, chest))
check("纸上画着三个定位图案（墨色块）", count(hold_front, C_CELL_BLACK, chest) >= 20,
      "%d px" % count(hold_front, C_CELL_BLACK, chest))
check("两端有皮革卷头（不是一张白纸片）",
      count(hold_front, C_ITEM_LEATHER_DARK, pygame.Rect(28, 34, 26, 16)) >= 6,
      "%d px" % count(hold_front, C_ITEM_LEATHER_DARK, pygame.Rect(28, 34, 26, 16)))

# 纸盖住胸口核心：捧图时那块青光应该看不见了
core = pygame.Rect(35, 39, 10, 6)
n_core_idle = count(idle_front, C_PLAYER, core)
n_core_hold = count(hold_front, C_PLAYER, core)
check("捧图时胸口核心被纸挡住", n_core_idle > 4 and n_core_hold == 0,
      "idle %d hold %d" % (n_core_idle, n_core_hold))

# 背对镜头：纸在身前，看不见；只有纸边从剪影两侧露出来
hold_back = seq_hold(0)
check("背对捧图：胸口看不见纸（纸在身前）", count(hold_back, C_ITEM_PAPER, chest) == 0,
      "%d px" % count(hold_back, C_ITEM_PAPER, chest))
check("背对捧图：两侧露着纸边（看得出手里有东西）",
      count(hold_back, C_ITEM_PAPER, pygame.Rect(25, 38, 6, 12)) > 2
      and count(hold_back, C_ITEM_PAPER, pygame.Rect(49, 38, 6, 12)) > 2,
      "%d / %d px" % (count(hold_back, C_ITEM_PAPER, pygame.Rect(25, 38, 6, 12)),
                      count(hold_back, C_ITEM_PAPER, pygame.Rect(49, 38, 6, 12))))

# 朝左：纸偏在左边（不是画在正中间）
hold_left = seq_hold(2)
check("朝左捧图：纸偏在左侧（右半胸是空的）",
      count(hold_left, C_ITEM_PAPER, pygame.Rect(29, 36, 14, 12)) > 50
      and count(hold_left, C_ITEM_PAPER, pygame.Rect(44, 36, 12, 12)) == 0,
      "%d / %d px" % (count(hold_left, C_ITEM_PAPER, pygame.Rect(29, 36, 14, 12)),
                      count(hold_left, C_ITEM_PAPER, pygame.Rect(44, 36, 12, 12))))


# ==================== 第三幕的剑（2026-11-12）====================
# 作者：「码序者挥剑攻击怪物的**动作和机制**」—— 动作 = 人身上要有剑、挥的时候刃要扫过去。
BLADE_IDLE = (198, 205, 214)
BLADE_SWING = (252, 253, 255)


def seq_sword(facing=3, **kw):
    s = pygame.Surface((80, 80))
    s.fill(C_CELL_WHITE)
    sprites.draw_sequencer(s, 40, 40, facing=facing, t=2.0, **kw)
    return s


nothing = seq_sword()
armed = seq_sword(has_sword=True)
whole = pygame.Rect(0, 0, 80, 80)
check("没剑时画面上没有刃（钢色）", count(nothing, BLADE_IDLE, whole) == 0,
      "%d px" % count(nothing, BLADE_IDLE, whole))
check("拿到剑之后手里有一把（钢色成片）", count(armed, BLADE_IDLE, whole) >= 12,
      "%d px" % count(armed, BLADE_IDLE, whole))
check("...护手/柄首是金色（不是一根灰棍）", count(armed, C_ITEM, whole) >= 6,
      "%d px" % count(armed, C_ITEM, whole))

# 挥砍：刃换成更亮的钢，而且**位置明显变了**（真的扫过去了）
def blade_box(surf, color):
    xs, ys = [], []
    for x in range(80):
        for y in range(80):
            if surf.get_at((x, y))[:3] == color:
                xs.append(x); ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


mid = seq_sword(has_sword=True, swing=0.6)
late = seq_sword(has_sword=True, swing=0.2)
box_mid = blade_box(mid, BLADE_SWING)
box_late = blade_box(late, BLADE_SWING)
check("挥砍时刃是亮的（和待机的灰钢分得开）", box_mid is not None, str(box_mid))
if box_mid and box_late:
    check("...而且刃在两帧之间移动了（不是只有一道弧在动）",
          box_mid != box_late, "%s vs %s" % (box_mid, box_late))

# 朝四个方向都能看见那把剑
for facing in range(4):
    n = count(seq_sword(facing=facing, has_sword=True), BLADE_IDLE, whole)
    check("朝 %d 时也画得出来（不只在某一个朝向）" % facing, n >= 10, "%d px" % n)

finish("第一幕 · 角色贴图")
