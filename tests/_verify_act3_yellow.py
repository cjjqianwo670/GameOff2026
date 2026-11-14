# -*- coding: utf-8 -*-
"""第三幕 M2 验收：黄怪 / 老者血条 / 倒下与救援 / 剑。

作者 2026-11-12 定的规则：
  · 黄怪优先攻击老者；**玩家砍它一次，它就转火玩家**
  · 老者血条空了会**倒下**（不是死），按 H 救 4 秒
  · 第二幕收尾给的剑，就是用来砍它们的
"""

import pygame

from _act1_common import WIN, auto_mono, check, finish, new_game, paint_ok
from src import story
from src.config import (  # noqa: E402
    OLDMAN_HP, OLDMAN_REVIVE_HP, OLDMAN_REVIVE_RANGE, OLDMAN_REVIVE_TIME, SC_H, SC_U, SWORD_CD,
    PURPLE_SPAWN_PER_MIN, PURPLE_SPAWN_PER_MIN_ACT3, SWORD_RANGE, VALID, YELLOW_AGGRO_TIME,
    YELLOW_BITE_DAMAGE, YELLOW_BITE_DIST, YELLOW_HP, YELLOW_PLAYER_DAMAGE, YELLOW_SPEED
)
from src.entities import Monster, PurpleOne, YellowOne
from src.grid import cell_center

TITLE = "STEP 16 · ACT 3 (THE YELLOW ONES / RESCUE / SWORD)"

ENTER, UKEY, HKEY = 40, SC_U, SC_H                # U = 挥剑（作者指定；Q/F 都已删掉）


def to_act3():
    g = new_game()
    for (r, c) in sorted(g.board.must):
        paint_ok(g, r, c)
    g.start_act2()
    for (r, c) in sorted(g.must):
        if g.board.state[r][c] != VALID:
            paint_ok(g, r, c)
    g.start_act3()
    g.has_sword = True
    for _ in range(400):
        auto_mono(g)
        g.update(1 / 60)
        g.dlg_t = 99.0
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
        if g.state != "DIALOG":
            break
    g.spawn_purple = lambda: None                 # 紫怪会清整行，这里不测它
    g.spawn_rate = 0.0                            # 红怪会啃格，别让它干扰断言
    g.monsters.clear()
    return g


def key(sc):
    return pygame.event.Event(pygame.KEYDOWN, key=0, scancode=sc)


# ==================== 1. 索敌：谁近咬谁（作者 2026-11-14 改）====================
g = to_act3()
g.yellow_spawned = 1                      # 关掉自动生成，手动摆
g.yellow_t = 0.0

# A. 站在老者旁边（玩家离得远）→ 咬老者
y = YellowOne((g.oldman.pos.x - 30, g.oldman.pos.y + 90))
g.yellows = [y]
d_old0 = (y.pos - g.oldman.pos).length()
d_pl0 = (y.pos - g.player.pos).length()
hp0 = g.oldman.hp
t = 0.0
while g.oldman.hp == hp0 and t < 10:
    auto_mono(g)
    g.update(1 / 60)
    t += 1 / 60
check("（准备）它确实离老者更近", d_old0 < d_pl0, "%.0f vs %.0f" % (d_old0, d_pl0))
check("离老者近 → 咬老者，扣 %d%%" % YELLOW_BITE_DAMAGE,
      g.oldman.hp == hp0 - YELLOW_BITE_DAMAGE, "%d → %d（%.1fs）" % (hp0, g.oldman.hp, t))

# B. 站在玩家旁边（老者离得远）→ 咬玩家
g2 = to_act3()
g2.yellow_spawned = 1
g2.yellow_t = 0.0
y2 = YellowOne((g2.player.pos.x + 30, g2.player.pos.y - 40))
g2.yellows = [y2]
d_old = (y2.pos - g2.oldman.pos).length()
d_pl = (y2.pos - g2.player.pos).length()
hp_p = g2.health
t = 0.0
while g2.health == hp_p and t < 8:
    auto_mono(g2)
    g2.update(1 / 60)
    t += 1 / 60
check("（准备）它确实离玩家更近", d_pl < d_old, "%.0f vs %.0f" % (d_pl, d_old))
check("离玩家近 → 咬玩家（不再一律冲老者）", g2.health < hp_p,
      "%d → %d（%.1fs）" % (hp_p, g2.health, t))
check("...它的速度比红怪快（冲着人去，慢了够不着）", YELLOW_SPEED > 62, "%.0f" % YELLOW_SPEED)

# C. 被砍过之后：即使老者更近，也先咬砍它的人
g3b = to_act3()
g3b.yellow_spawned = 1
g3b.yellow_t = 0.0
y3 = YellowOne((g3b.oldman.pos.x - 30, g3b.oldman.pos.y + 60))   # 贴着老者
y3.hurt(1)                                                       # 被砍一剑（没死）
g3b.yellows = [y3]
d_old = (y3.pos - g3b.oldman.pos).length()
d_pl = (y3.pos - g3b.player.pos).length()
hp_o = g3b.oldman.hp
t = 0.0
while t < 2.0:
    auto_mono(g3b)
    g3b.update(1 / 60)
    t += 1 / 60
check("（准备）它离老者更近，但刚刚挨了一剑",
      d_old < d_pl and y3.aggro_t > 0, "%.0f vs %.0f / aggro %.1f" % (d_old, d_pl, y3.aggro_t))
check("...被打之后优先追砍它的人（不咬老者）",
      (y3.pos - g3b.player.pos).length() < d_pl - 30 and g3b.oldman.hp == hp_o,
      "离玩家 %.0f → %.0f，老者 hp %d" % (d_pl, (y3.pos - g3b.player.pos).length(), g3b.oldman.hp))

# ==================== 3. 老者倒下 ====================
g.oldman.hp = YELLOW_BITE_DAMAGE          # 下一口就打倒
g.yellows = [YellowOne((g.oldman.pos.x + 10, g.oldman.pos.y + 10))]
t = 0.0
while not g.oldman.down and t < 6:
    auto_mono(g)
    g.update(1 / 60)
    t += 1 / 60
check("血量归零 → 倒下（不是死）", g.oldman.down and g.oldman.hp == 0, "down=%s hp=%d" % (g.oldman.down, g.oldman.hp))
check("...底部给出 [H] 提示", g.hint_text == story.HINT_HELP_OLDMAN, repr(g.hint_text))
check("...码序使嘀咕一句", g.mono_text == story.A3_DOWN, repr(g.mono_text[:24]))

prog0 = g.board.progress()
for _ in range(int(3 * 60)):              # 他倒下之后
    auto_mono(g)
    g.update(1 / 60)
check("...他写不动了（倒着不落笔）", g.board.progress() == prog0,
      "%d → %d" % (prog0, g.board.progress()))

# 黄怪在老者倒下后改打玩家
g.yellows = [YellowOne((g.player.pos.x + 520, g.player.pos.y))]   # 先放远，别马上咬到
g.yellow_spawned = 1
t = 0.0
hp_pl = g.health
while g.health == hp_pl and t < 20:
    auto_mono(g)
    g.update(1 / 60)
    t += 1 / 60
# 2026-11-12 改：**他倒下之后黄怪停手**（它们要的是格式信息不是命）。
# 不加这条会滚成死循环：他倒 → 黄怪打玩家 → 玩家救不了 → 更救不了。
check("老者倒下 → 黄怪**停手**（给玩家时间去救，不然会滚成死循环）",
      g.health == hp_pl,
      "%d → %d" % (hp_pl, g.health))
check("...咬玩家比红怪疼（%d%% > 5%%）" % YELLOW_PLAYER_DAMAGE, YELLOW_PLAYER_DAMAGE > 5)

# ==================== 4. 救他：站远了 / 没按 H 都不算 ====================
g.yellows.clear()
g.player.pos.update(g.oldman.pos.x + 400, g.oldman.pos.y)
g.input.held.add(HKEY)
for _ in range(int(2 * 60)):
    auto_mono(g)
    g.update(1 / 60)
check("站太远按住 H 没有用", g.oldman.down and g.revive_t == 0,
      "down=%s t=%.2f" % (g.oldman.down, g.revive_t))
g.input.held.discard(HKEY)

g.player.pos.update(g.oldman.pos.x + 4, g.oldman.pos.y + 20)
for _ in range(int(2 * 60)):
    auto_mono(g)
    g.update(1 / 60)
check("站到了但没按 H 也不行", g.oldman.down and g.revive_t == 0, "t=%.2f" % g.revive_t)

# 按住 H：4 秒
g.input.held.add(HKEY)
t = 0.0
while g.oldman.down and t < OLDMAN_REVIVE_TIME + 2:
    auto_mono(g)
    g.update(1 / 60)
    t += 1 / 60
g.input.held.discard(HKEY)
check("按住 H 满 4 秒 → 他站起来", not g.oldman.down and t >= OLDMAN_REVIVE_TIME,
      "%.2fs" % t)
check("...起来时带着一半血", g.oldman.hp == OLDMAN_REVIVE_HP, "%d" % g.oldman.hp)
check("...底部 [H] 提示消失", g.hint_text == "", repr(g.hint_text))
check("...救人距离是 OLDMAN_REVIVE_RANGE", OLDMAN_REVIVE_RANGE >= 40, "%.0f" % OLDMAN_REVIVE_RANGE)

# 松手会退一点（不是一键归零）
g.oldman.hp = 5
g.yellows = [YellowOne((g.oldman.pos.x + 8, g.oldman.pos.y + 8))]
for _ in range(int(3 * 60)):
    auto_mono(g)
    g.update(1 / 60)
    if g.oldman.down:
        break
g.yellows.clear()
g.player.pos.update(g.oldman.pos.x + 4, g.oldman.pos.y + 20)
g.input.held.add(HKEY)
for _ in range(int(1.2 * 60)):
    auto_mono(g)
    g.update(1 / 60)
held = g.revive_t
g.input.held.discard(HKEY)
for _ in range(int(0.4 * 60)):
    auto_mono(g)
    g.update(1 / 60)
check("松手之后进度会退，但不归零", 0 < g.revive_t < held,
      "%.2f → %.2f" % (held, g.revive_t))

# ==================== 5. 剑：砍一下就转火玩家，两下砍死 ====================
g2 = to_act3()
g2.yellow_spawned = 1
y2 = YellowOne((g2.player.pos.x + 20, g2.player.pos.y))
g2.yellows = [y2]
check("（准备）黄怪一开始没盯玩家", not y2.hunting)
check("挥剑键是 U=24（作者指定）", SC_U == 24, "%d" % SC_U)
g2.handle_event(key(UKEY))
check("按 Q 挥剑 → 黄怪掉 1 点血", y2.hp == YELLOW_HP - 1, "%d" % y2.hp)
check("...而且**立刻转火玩家**（作者定的规则）", y2.hunting and y2.aggro_t > 0,
      "aggro=%.1f" % y2.aggro_t)
check("...转火是按时间算的（YELLOW_AGGRO_TIME）", YELLOW_AGGRO_TIME > 3, "%.1f" % YELLOW_AGGRO_TIME)
check("...挥砍有 CD（不是按住连点就能秒）", g2.sword_cd > 0, "%.2f" % g2.sword_cd)

g2.yellows = [YellowOne((g2.player.pos.x + 100, g2.player.pos.y))]
far = g2.yellows[0]
g2.sword_cd = 0.0
g2.handle_event(key(UKEY))
check("够不着的黄怪砍不到（有距离判定 SWORD_RANGE）", far.hp == YELLOW_HP, "%d" % far.hp)
check("...挥空也有声音和动作（swing_t 起来了）", g2.swing_t > 0)

g2.yellows = [YellowOne((g2.player.pos.x + 18, g2.player.pos.y))]
y3 = g2.yellows[0]
g2.sword_cd = 0.0
g2.handle_event(key(UKEY))
g2.sword_cd = 0.0
g2.handle_event(key(UKEY))
check("两剑砍死（YELLOW_HP = 2）", YELLOW_HP == 2 and y3 not in g2.yellows, "%d" % YELLOW_HP)

g2.has_sword = False
g2.yellows = [YellowOne((g2.player.pos.x + 18, g2.player.pos.y))]
y4 = g2.yellows[0]
g2.sword_cd = 0.0
g2.handle_event(key(UKEY))
check("没剑时按 Q 什么也不会发生", y4.hp == YELLOW_HP, "%d" % y4.hp)
g2.has_sword = True

# 旧键（Q / F）必须彻底失效 —— 作者 2026-11-12 说挥剑是 U，那两个键已经删了
for stale, name in ((20, "Q"), (9, "F")):
    g2.yellows = [YellowOne((g2.player.pos.x + 18, g2.player.pos.y))]
    y5 = g2.yellows[0]
    g2.sword_cd = 0.0
    g2.swing_t = 0.0
    g2.handle_event(key(stale))
    check("旧键 %s 已经不管用了（只剩 U）" % name, y5.hp == YELLOW_HP and g2.swing_t == 0,
          "hp %d / swing %.2f" % (y5.hp, g2.swing_t))

# 前两幕按 F 不该有剑
g3 = new_game()
g3.has_sword = True
g3.handle_event(key(UKEY))
check("不在第三幕时挥剑无效（剑是第三幕的东西）", g3.swing_t == 0, "%.2f" % g3.swing_t)

# ==================== 6. 检查点 / 清屏 ====================
g4 = to_act3()
g4.oldman.hp = 20
g4.yellows = [YellowOne((g4.oldman.pos.x + 10, g4.oldman.pos.y + 10))]
for _ in range(int(3 * 60)):
    auto_mono(g4)
    g4.update(1 / 60)
    if g4.oldman.down:
        break
g4.state = "DEAD"
g4.restore_checkpoint()
check("第三幕阵亡回本幕 → 老者满血站起来", g4.oldman.hp == OLDMAN_HP and not g4.oldman.down,
      "%d / down=%s" % (g4.oldman.hp, g4.oldman.down))
check("...黄怪清空（不带着上一把的追兵重开）", g4.yellows == [], "%d 只" % len(g4.yellows))

g5 = to_act3()
g5.yellows = [YellowOne((200, 200)), YellowOne((300, 320))]
g5.enter_clear()
check("清屏时黄怪一起被收掉", g5.yellows == [], "%d 只" % len(g5.yellows))

# ==================== 6.5 剑对每种怪：黄怪两剑，红怪/紫怪一剑 ====================
g8 = to_act3()
g8.yellows = []
g8.purples = []
g8.monsters = [Monster((g8.player.pos.x + 20, g8.player.pos.y + 6), 62.0)]
g8.sword_cd = 0.0
g8.handle_event(key(UKEY))
check("红怪一剑就死（它们没有 hp）", g8.monsters == [], "%d 只" % len(g8.monsters))

g8.purples = [PurpleOne((g8.player.pos.x - 18, g8.player.pos.y + 6))]
g8.sword_cd = 0.0
g8.handle_event(key(UKEY))
check("紫怪也是一剑就死", g8.purples == [], "%d 只" % len(g8.purples))

# 取最近的那一只（不是随机/第一只）
g8.yellows = [YellowOne((g8.player.pos.x + 30, g8.player.pos.y)),
              YellowOne((g8.player.pos.x + 14, g8.player.pos.y))]
near_one = g8.yellows[1]
g8.sword_cd = 0.0
g8.handle_event(key(UKEY))
check("砍的是**最近**那一只", near_one.hp == YELLOW_HP - 1 and g8.yellows[0].hp == YELLOW_HP,
      "%d / %d" % (near_one.hp, g8.yellows[0].hp))

# ==================== 6.6 第三幕的紫怪慢下来了 ====================
check("第三幕的紫怪频率单独配了一个更小的值",
      PURPLE_SPAWN_PER_MIN_ACT3 < PURPLE_SPAWN_PER_MIN,
      "%.1f/分 vs 第二幕 %.1f/分" % (PURPLE_SPAWN_PER_MIN_ACT3, PURPLE_SPAWN_PER_MIN))
# 直接量「再等多久会来下一只」：第三幕 30s，第二幕 10s
def next_purple_gap(act):
    gx = to_act3() if act >= 3 else new_game()
    if act < 3:
        for (r, c) in sorted(gx.board.must):
            paint_ok(gx, r, c)
        gx.start_act2()
        gx.state = "BATTLE"
    gx.purples.clear()
    gx.format_cells = set()               # 别让老者写完就清屏（2026-11-12：他挑格看的是 format_cells）
    gx.yellow_spawned = 1                 # 也别让黄怪来捣乱
    gx.update_yellows = lambda dt: None   # 索敌改成「谁近咬谁」之后，站桩的玩家会被咬死
    gx.spawn_purple = lambda: gx.purples.append(PurpleOne((0, 0)))
    gx.purple_spawned = 1                 # 跳过首只的固定延迟，量「之后」的间隔
    t = 0.0
    gx.purple_t = 0.0
    while not gx.purples and t < 45:
        auto_mono(gx)
        gx.update(1 / 60)
        t += 1 / 60
    return t


gap3 = next_purple_gap(3)
gap2 = next_purple_gap(2)
check("第三幕里紫怪要等 30 秒才来一只", 29.5 <= gap3 <= 30.5, "%.1fs" % gap3)
check("...第二幕还是 10 秒一只（只改了第三幕）", 9.5 <= gap2 <= 10.5, "%.1fs" % gap2)

# ==================== 7. 画面上：他头顶有血条（只有第三幕）====================
g6 = to_act3()
g6.yellow_spawned = 1
g6.yellows = []
g6.mono_t = 0.0
g6.hint_text, g6.hint_t = "", 0.0
ox, oy = int(g6.oldman.pos.x), int(g6.oldman.pos.y)
g6.draw()
box = pygame.Rect(ox - 18, oy - 28, 36, 8)
found = sum(1 for x in range(box.left, box.right)
            for y in range(box.top, box.bottom)
            if g6.canvas.get_at((x, y))[:3] not in ((247, 247, 249), (19, 16, 15)))
check("第三幕他头顶画了血条（不是只有面板上的数字）", found > 20, "%d px" % found)

g7 = new_game()
paint_ok(g7, *sorted(g7.board.must)[0])
g7.draw()
box2 = pygame.Rect(int(g7.oldman.pos.x) - 18, int(g7.oldman.pos.y) - 28, 36, 8)
found2 = sum(1 for x in range(box2.left, box2.right)
             for y in range(box2.top, box2.bottom)
             if g7.canvas.get_at((x, y))[:3] not in ((247, 247, 249), (19, 16, 15)))
check("第一幕他头顶**没有**血条（前两幕打不到他）", g7.act == 1 and found2 <= found,
      "act1 %d px / act3 %d px" % (found2, found))

finish(TITLE)
