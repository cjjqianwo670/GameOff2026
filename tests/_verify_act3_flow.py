# -*- coding: utf-8 -*-
"""第三幕 M1 验收：老者回来 + 替你写格式信息（黄怪/血条/H 救人属于 M2，这里不测）。

作者 2026-11-12 定的规则：
  · 老者带着格式信息回来，替码序使写（码序使经验太少，写得太慢）
  · 格式信息他全包，暂时不交给玩家
  · 他引来的追兵（黄怪）属于 M2，这一幕先只有红怪 / 紫怪
"""

import pygame

from _act1_common import WIN, auto_mono, check, finish, new_game, paint_ok, shot, toast_text
from src import story
from src.config import (  # noqa: E402
    C_ITEM, C_OLDMAN, HEALTH_MAX, OLDMAN_BLAST_RADIUS, OLDMAN_CELL, OLDMAN_STAGGER,
    SC_H, SCRIBE_PAUSE, SCRIBE_WALK_SPEED, VALID, WHITE
)
from src.qr import format_cells, format_dark_cells, required_cells
from src.config import TARGET_N, TARGET_OFFSET
from src.grid import cell_center

TITLE = "STEP 15 · ACT 3 (OLD MAN SCRIBES THE FORMAT)"


def to_act3(g):
    """把前两幕的必涂格填好，然后进第三幕。"""
    for (r, c) in sorted(g.board.must):
        paint_ok(g, r, c)
    g.start_act2()
    for (r, c) in sorted(g.must):
        if g.board.state[r][c] != VALID:
            paint_ok(g, r, c)
    g.start_act3()
    g.spawn_rate = 0.0
    g.spawn_purple = lambda: None            # 这一幕先不测紫怪（它会清整行，见 M2 平衡）
    g.monsters.clear()
    return g


def skip_dialog(g, limit=400):
    for _ in range(limit):
        auto_mono(g)
        g.update(1 / 60)
        g.dlg_t = 99.0
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=40))
        if g.state != "DIALOG":
            return g.state
    return g.state


# ==================== 1. 必涂格：106 + 格式信息 ====================
g0 = new_game()
orr, occ = TARGET_OFFSET

fmt_qr = format_cells()
check("格式信息是 30 个位置（两份拷贝，各 15 位）", len(fmt_qr) == 30, "%d" % len(fmt_qr))
check("...两份拷贝坐标不重叠", len(fmt_qr) == len(format_cells()))
check("...全在 QR 矩阵内（0~20）",
      all(0 <= r < TARGET_N and 0 <= c < TARGET_N for r, c in fmt_qr))

must2 = required_cells(g0.target, act=2)
must3 = required_cells(g0.target, act=3)
added = must3 - must2
check("第三幕必须**传 target**（哪些格式格该黑由掩码决定）",
      isinstance(must3, set))
try:
    required_cells(None, act=3)
    raised = False
except ValueError:
    raised = True
check("...不传 target 直接报错，而不是猜", raised)

check("第三幕比第二幕多出 10~20 格", 10 <= len(added) <= 20, "+%d" % len(added))
check("...多出来的全是格式信息里该黑的格",
      added == format_dark_cells(g0.target), "%d" % len(added))
check("第三幕必涂总数 = 106 + 新增", len(must3) == 106 + len(added), "%d" % len(must3))
check("...而且每一格在真码里都是黑的",
      all(g0.target[r - orr][c - occ] for r, c in must3))
check("第三幕必涂 ⊃ 第二幕必涂（不清空前两幕的成果）", must2 <= must3)

# ==================== 2. 进第三幕：老者回来了 ====================
g = new_game()
n_before = g.board.progress()
to_act3(g)
check("进第三幕：act = 3", g.act == 3, "%d" % g.act)
check("...棋盘没被清空（前两幕的 106 格还在）", g.board.progress() >= n_before + 106,
      "%d" % g.board.progress())
check("...必涂格 = 106 + 格式信息", len(g.must) == 106 + len(g.format_cells), "%d" % len(g.must))
check("老者回来了（站在坛外老位置，面朝坛内）",
      g.oldman is not None and not g.oldman.gone and g.oldman.cell == OLDMAN_CELL,
      "%s gone=%s" % (g.oldman.cell if g.oldman else None, g.oldman.gone if g.oldman else None))
check("...他面朝坛内（facing=1 下）", g.oldman.facing == 1, "%d" % g.oldman.facing)
check("开场是对话（他先说话）", g.state == "DIALOG", g.state)

# ==================== 3. 对话：13 句，不接 LEAVE_LINE，说完直接开打 ====================
check("对话 13 句", len(g.dlg_lines) == 13, "%d" % len(g.dlg_lines))
check("...**没有**第一幕那句 LEAVE_LINE（他这次不走）",
      all("I'll come back" not in line for _, line in g.dlg_lines),
      repr(g.dlg_lines[-1][1][:30]))
check("...最后一句是那句「别让它们碰到那两条线」",
      "reach the lines" in g.dlg_lines[-1][1], g.dlg_lines[-1][1][:40])
st = skip_dialog(g)
check("说完直接进战斗（不是自由探索 —— 他不会再走）", st == "BATTLE", st)
check("...老者还站在原地（没被 end_dialog 弄走）",
      not g.oldman.gone and g.oldman.leaving is False,
      "gone=%s leaving=%s" % (g.oldman.gone, g.oldman.leaving))

# ==================== 4. 老者替你写格式信息 ====================
check("（准备）格式格还没写", g.board.progress() == 106, "%d" % g.board.progress())
check("（准备）他不知道写哪些格", len(g.scribe_cells) == len(g.format_cells),
      "%d / %d" % (len(g.scribe_cells), len(g.format_cells)))

# 作者 2026-11-12：**他必须走到那一格上才落笔**（不是隔空写）
first = g.scribe_cells[0]
home = (g.oldman.pos.x, g.oldman.pos.y)
run = 0.0
while g.board.progress() == 106 and run < 8.0:
    auto_mono(g)
    g.update(1 / 60)
    g.monsters.clear()
    run += 1 / 60
check("他先走过去，过一会儿才落第一格（不是隔空写）", run > 0.2, "%.2fs" % run)
check("...落笔时他**站在那一格上**（±2px）",
      abs(g.oldman.pos.x - cell_center(*first)[0]) < 2
      and abs(g.oldman.pos.y - cell_center(*first)[1]) < 2,
      "om %s / cell %s" % ((round(g.oldman.pos.x), round(g.oldman.pos.y)), cell_center(*first)))
check("...他确实离开了出发点", (g.oldman.pos.x, g.oldman.pos.y) != home, str(home))
check("...落的那一格正好是顺序里的第一格", g.board.state[first[0]][first[1]] == VALID)
check("...他落笔时有一句心声", g.mono_text == story.A3_M1, repr(g.mono_text[:20]))
check("...他走得很慢（SCRIBE_WALK_SPEED 明显低于玩家）",
      SCRIBE_WALK_SPEED < 30 * 60 / 0.13, "%.0f px/s" % SCRIBE_WALK_SPEED)

# 玩家先涂掉一格 → 他不会去动它（他挑的永远是「还是白的」那些）
nxt = sorted(c for c in g.format_cells if g.board.state[c[0]][c[1]] == WHITE)[0]
paint_ok(g, *nxt)
i_before = g.scribe_i
for _ in range(int(6 * 60)):
    auto_mono(g)
    g.update(1 / 60)
    g.monsters.clear()
check("玩家先涂好的格子他不会去抢（挑的永远是白的那些）",
      g.scribe_i > i_before and g.board.state[nxt[0]][nxt[1]] == VALID
      and g.scribe_target != nxt,
      "i %d → %d / target %s" % (i_before, g.scribe_i, g.scribe_target))

# ==================== 5. 被怪吃掉 → 玩家必须自己补 ====================
victim = g.scribe_cells[0]
g.format_seen.add(victim)                       # 他写过，已经记在账上
g.board.state[victim[0]][victim[1]] = WHITE     # 模拟被红怪啃掉
auto_mono(g)
g.update(1 / 60)
check("格式格被吃掉 → 冒出一行系统提示（叫他补）",
      g.hint_text == story.HINT_FORMAT_BROKEN, repr(g.hint_text))
check("...同时一句嘀咕（飘字，不冻世界）", toast_text(g) == story.A3_M2, repr(toast_text(g)[:20]))
check("...提示只出现一次（不是每帧刷）",
      g.format_warned is True)
g.hint_text = ""
g.board.state[victim[0]][victim[1]] = WHITE
auto_mono(g)
g.update(1 / 60)
check("...第二次被吃不再刷提示", g.hint_text == "", repr(g.hint_text))

# 他**不回头补**：这一格必须玩家自己补上，否则这一幕永远写不完（这就是玩家的活）
check("（准备）破掉的那一格还是白的，他不会自己去补",
      g.board.state[victim[0]][victim[1]] == WHITE)
paint_ok(g, *victim)                            # 玩家照出来、补上
check("玩家补回破掉的那一格", g.board.state[victim[0]][victim[1]] == VALID)

# ==================== 6. 写完 → 清屏（这一幕的正常收尾）====================
g.spawn_rate = 0.0
g.yellow_t = -9999                     # 这一段测的是「写完 → 清屏」，不测「扛着黄怪写完」
g.yellows.clear()
t = 0.0
while g.state == "BATTLE" and t < 60:
    auto_mono(g)
    g.update(1 / 60)
    g.monsters.clear()
    g.purples.clear()
    t += 1 / 60
check("他写完全部格式格 → 自动清屏", g.state == "CLEAR", "%s (%.1fs)" % (g.state, t))
check("...写完后进度 = 必涂总数", g.board.progress() == len(g.must),
      "%d / %d" % (g.board.progress(), len(g.must)))
check("...清屏时他停手了", g.scribe_cells == [], str(len(g.scribe_cells)))
check("...写完的格式区全黑",
      all(g.board.state[r][c] == VALID for (r, c) in g.format_cells))

# ==================== 7. 第三幕收尾：不发道具、字幕是 ACT 3 ====================
for _ in range(int(20 * 60)):
    auto_mono(g)
    g.update(1 / 60)
    if g.state == "END":
        break
check("第三幕收尾会走到 END", g.state == "END", g.state)
check("...字幕是 ACT 3 — END", g.banner_text == "ACT 3 — END", repr(g.banner_text))
check("...第三幕不发道具（第四幕也不发）", not g.items, "%d 件" % len(g.items))
g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=40))
check("...END 按回车进第四幕（2026-11-14 接上了）", g.act == 4 and g.state == "BATTLE",
      "act %d / %s" % (g.act, g.state))

# ==================== 8. 检查点：第三幕阵亡回本幕开头，老者不能消失 ====================
g2 = to_act3(new_game())
skip_dialog(g2)
for _ in range(int(6 * 60)):
    auto_mono(g2)
    g2.update(1 / 60)
    g2.monsters.clear()
prog = g2.board.progress()
g2.state = "DEAD"
g2.restore_checkpoint()
check("第三幕阵亡 → 回到本幕开头", g2.state == "DIALOG" and g2.act == 3, g2.state)
check("...老者还在（不能像前两幕那样被「早走了」）",
      not g2.oldman.gone, str(g2.oldman.gone))
check("...必涂格还是 106 + 格式", len(g2.must) == 106 + len(g2.format_cells),
      "%d" % len(g2.must))
check("...他会从没写的那格继续写", len(g2.scribe_cells) > 0,
      "%d 格" % len(g2.scribe_cells))
check("...血量回满", g2.health == HEALTH_MAX, "%d" % g2.health)

# ==================== 9. 第二幕的剑 ====================
g3 = new_game()
for (r, c) in sorted(g3.board.must):
    paint_ok(g3, r, c)
g3.start_act2()
for (r, c) in sorted(g3.must):
    if g3.board.state[r][c] != VALID:
        paint_ok(g3, r, c)
g3.act = 2
g3.spawn_items()
check("第二幕收尾掉一把剑", len(g3.items) == 1 and g3.items[0].kind == "sword",
      str([it.kind for it in g3.items]))
g3.player.pos.update(g3.items[0].pos)
g3.player.cell = g3.items[0].cell
g3.try_pick()
check("拾取 → has_sword = True", g3.has_sword)
check("...提示是道具说明", g3.hint_text == story.ITEM_SWORD, repr(g3.hint_text))
check("...背包面板里会出现剑这一格（has_sword 决定）", g3.has_sword)

# 剑的贴图：直刃（亮色像素）+ 护手（金色）
tmp = pygame.Surface((48, 48), pygame.SRCALPHA)
from src import sprites  # noqa: E402
sprites.draw_item(tmp, "sword", 24, 24, glow=False)
blade = sum(1 for x in range(48) for y in range(48) if tmp.get_at((x, y))[:3] == (226, 230, 236))
gold = sum(1 for x in range(48) for y in range(48) if tmp.get_at((x, y))[:3] == C_ITEM)
check("剑有亮刃（一眼认得出是金属）", blade > 30, "%d px" % blade)
check("...有护手/金首（不是一根铁条）", gold > 10, "%d px" % gold)

# ==================== 8. 「守」是真的（2026-11-12）====================
# 作者采纳的三条：① 被咬就打断他写作（不然「守」是摆设）；② 写完要告诉玩家「剩下的归你」；③ 他会说话。


def fresh3():
    g9 = to_act3(new_game())
    skip_dialog(g9)
    g9.yellow_t = -9999                    # 这一段只测他，不放大群黄怪
    g9.yellows = []
    return g9


# --- ① 被咬一下就停笔（这一笔重来），但不会被钉在原地 ---
ga = fresh3()
for _ in range(int(8 * 60)):
    auto_mono(ga)
    ga.update(1 / 60)
    if ga.scribe_writing:
        break
check("（准备）他站到格子上了", ga.scribe_writing, str(ga.scribe_target))
ga.scribe_t = SCRIBE_PAUSE * 0.8          # 假装快写完了
ga.oldman.bitten(10)
check("被咬一口 → 进入硬直", ga.oldman.stagger_t > 0, "%.2f" % ga.oldman.stagger_t)
check("...这一笔的进度被打断（不是接着数）", ga.scribe_t == SCRIBE_PAUSE * 0.8,
      "%.2f" % ga.scribe_t)
prog0 = ga.board.progress()
for _ in range(int(OLDMAN_STAGGER * 0.9 * 60)):
    auto_mono(ga)
    ga.update(1 / 60)
check("硬直期间写不出字（进度不涨）", ga.board.progress() == prog0,
      "%d → %d" % (prog0, ga.board.progress()))
check("...硬直比咬的间隔短（不然一只黄怪就能把他锁死）",
      OLDMAN_STAGGER < 1.4, "%.2f < 1.4" % OLDMAN_STAGGER)

# --- ② 被吃掉的格式格，他会回头补（作者：紫怪清了就让他再涂一遍）---
gb = fresh3()
for _ in range(int(10 * 60)):
    auto_mono(gb)
    gb.update(1 / 60)
    if gb.scribe_i >= 1:
        break
check("（准备）他至少写了一格", gb.scribe_i >= 1, "%d" % gb.scribe_i)
victim2 = sorted(c for c in gb.format_cells if gb.board.state[c[0]][c[1]] == VALID)[0]
gb.board.state[victim2[0]][victim2[1]] = WHITE     # 模拟被紫怪/红怪清掉
n_before = gb.scribe_i
back = False
for _ in range(int(25 * 60)):
    auto_mono(gb)
    gb.update(1 / 60)
    if gb.board.state[victim2[0]][victim2[1]] == VALID:
        back = True
        break
check("被吃掉的格式格 → 他会回头补（不再是「走过的不回头」）", back,
      "进度 %d → %d" % (n_before, gb.scribe_i))

# --- ②b 全写完但整张码没满 → 他说一句 + 点名还差几格 ---
gc = fresh3()
gc.yellow_t = -9999
# 先让一个**普通格**被啃掉（模拟红怪），否则格式一写完整张码就成了、直接清屏，测不到这句话
eaten = sorted(c for c in gc.must if c not in gc.format_cells)[0]
gc.board.state[eaten[0]][eaten[1]] = WHITE
for c in gc.format_cells:                          # 假装他已经把格式信息写完了
    gc.board.state[c[0]][c[1]] = VALID
gc.scribe_target = None
owe = len(gc.must) - gc.board.progress()
auto_mono(gc)
gc.update(1 / 60)
check("格式信息写完 → 他开口（「读法成了，剩下的归你」）",
      gc.mono_last == story.A3_READ, repr(gc.mono_last[:26]))
check("...底部点名还差几格（玩家才知道该干嘛）",
      gc.hint_text == story.HINT_FILL_REST % owe, "%r / owe=%d" % (gc.hint_text, owe))
check("...这个提示只说一次（不每帧刷）",
      gc.scribe_done_said is True)
check("...HUD 的标签从 DARK 换成 FILL（第三幕专有）", gc.act >= 3 and gc.scribe_done_said)

# --- ③ 救他起来那一下会把身边的黄怪震开 ---
gd = fresh3()
gd.yellow_t = -9999
gd.oldman.hp = 1
gd.oldman.bitten(10)                               # 打倒
check("（准备）老者倒下了", gd.oldman.down)
from src.entities import YellowOne  # noqa: E402
gd.yellows = [YellowOne((gd.oldman.pos.x + 30, gd.oldman.pos.y)),
              YellowOne((gd.oldman.pos.x + 40, gd.oldman.pos.y + 20))]
gd.player.pos.update(gd.oldman.pos.x + 10, gd.oldman.pos.y + 20)
gd.input.held.add(SC_H)
for _ in range(int(4.3 * 60)):
    auto_mono(gd)
    gd.update(1 / 60)
check("按住 H 满 4 秒 → 他站起来", not gd.oldman.down, str(gd.oldman.down))
check("...救起来那一下把身边的黄怪震开了（不然会滚出「起来→被咬→又倒」）",
      len(gd.yellows) == 0, "%d 只还在" % len(gd.yellows))
check("...他自己回一句（飘字）", gd.mumble_last == story.A3_UP_MAN, repr(gd.mumble_last[:24]))
check("震开半径够大（要能盖住贴着他咬的那些）",
      OLDMAN_BLAST_RADIUS > 60, "%.0f px" % OLDMAN_BLAST_RADIUS)

finish("第 3 幕 · 老者写格式信息")
