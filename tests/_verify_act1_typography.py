# -*- coding: utf-8 -*-
"""字幕呈现验收：字号变大、打字机、Enter 先补完、名牌配色、心声底衬。"""

import pygame

from _act1_common import auto_mono, check, finish, new_game, reveal_once, shot, toast_text
from src import story
from src.config import (
    C_BOX,
    TOAST_MAX, TOAST_TIME,
    C_ACCENT, C_OLDMAN, DLG_BOTTOM, DLG_BOX, DLG_CPS, DLG_FONT, DLG_LINE_H, DLG_NAME_FONT, DLG_PAD,
    C_TEXT, DLG_MIN_ROWS, MONO_FADE_OUT, MONO_FONT, MONO_LINE_H, MONO_REPEAT_GAP, PLAYER_GLOW_R,
    PROMPT_FONT, SC_ENTER, SC_R, WINDOW_W
)
from src.grid import cell_center
from src.ui import dlg_box_lines, dialog_char_total, dialog_lines, mono_box, mono_lines

TITLE = "TYPOGRAPHY · MONOLOGUE + DIALOGUE"


def ev(sc):
    return pygame.event.Event(pygame.KEYDOWN, key=0, scancode=sc)


def run(g, secs):
    """推进时间。心声会冻住世界，所以每帧先替玩家按一下回车（见 `_act1_common.auto_mono`）。"""
    for _ in range(max(1, int(secs * 60))):
        auto_mono(g)
        g.update(1 / 60)
        g.draw()


def put(g, cell):
    g.player.cell = cell
    g.player.pos.update(cell_center(*cell))


# --- 字号 ---
check("对话字号 %d ≥ 30（原来 25）" % DLG_FONT, DLG_FONT >= 30)
check("心声字号 %d ≥ 36（原来 27）" % MONO_FONT, MONO_FONT >= 36)
check("底部提示字号 %d ≥ 32（原来 27）" % PROMPT_FONT, PROMPT_FONT >= 32)
check("名牌字号 %d 比正文小（主次分明）" % DLG_NAME_FONT, DLG_NAME_FONT < DLG_FONT)

# --- 每一句都放得进 4 行框 ---
g = new_game()
run(g, 3.4)
g.enter_free_roam()
run(g, 4.0)
reveal_once(g)                                   # 先照过灰域，才允许喊老者（2026-11-14）
put(g, (4, 12))
run(g, 0.1)
g.handle_event(ev(23))
run(g, 1.9)
check("对话已开始", g.state == "DIALOG" and g.dlg_lines is not None)

over = []
for i in range(len(g.dlg_lines)):
    g.dlg_i = i
    lines, _ = dialog_lines(g)
    if len(lines) > dlg_box_lines():
        over.append((i + 1, len(lines)))
check("全部 %d 句都在 %d 行以内" % (len(g.dlg_lines), dlg_box_lines()), not over, str(over))

# --- 打字机 ---
g.dlg_i = 0
g.dlg_t = 0.05
check("刚开始那一瞬：这一句还没打完", g.dlg_typing())
total = dialog_char_total(g)
check("整句字数算得出来", total > 0, "%d" % total)
g.dlg_t = 0.05 + total / DLG_CPS + 0.1
check("时间够了：这一句打完了", not g.dlg_typing())

# --- Enter：先补完，再翻页 ---
g.dlg_t = 0.05
i0 = g.dlg_i
g.handle_event(ev(40))
check("没打完时按 Enter：不翻页、立刻补完", g.dlg_i == i0 and not g.dlg_typing(),
      "i %d -> %d" % (i0, g.dlg_i))
g.handle_event(ev(40))
check("打完之后再按 Enter：翻到下一句", g.dlg_i == i0 + 1, "%d" % g.dlg_i)
check("新的一句从 0 开始打", g.dlg_t == 0.0, "%.2f" % g.dlg_t)

# --- 名牌：说话人不同，牌子颜色不同 ---
def plate_color(g, idx):
    g.dlg_i, g.dlg_t = idx, 99.0
    g.draw()
    rows = max(2, min(dlg_box_lines(), len(dialog_lines(g)[0])))
    box = pygame.Rect(DLG_BOX[0], DLG_BOTTOM - (rows * DLG_LINE_H + 64), DLG_BOX[2], 44)
    hits = set()
    for x in range(box.left + DLG_PAD, box.left + DLG_PAD + 120, 2):
        for y in range(box.top - 14, box.top + 14, 2):
            hits.add(g.canvas.get_at((x, y))[:3])
    return hits

hits_old = plate_color(g, 0)
check("OLDMAN 名牌是暖米色", C_OLDMAN in hits_old, "%s" % sorted(hits_old)[:4])
shot(g, "36_dlg_oldman.png")
hits_seq = plate_color(g, 1)
check("SEQUENCER 名牌换成强调色", C_ACCENT in hits_seq and C_OLDMAN not in hits_seq,
      "%s" % sorted(hits_seq)[:4])

# --- 心声：和对话同一套框（2026-11-12 作者要求「别那么枯燥」）---
g2 = new_game()
run(g2, 3.4)
check("醒来就有心声", g2.mono_t > 0 and g2.mono_text == story.M1)
g2.mono_t = g2.mono_total - 2.0            # 打字阶段（此时 alpha 已满）
g2.draw()
mb = mono_box(g2)
check("心声框和对话框同宽同底边（同一套框）",
      (mb.x, mb.w, mb.bottom) == (DLG_BOX[0], DLG_BOX[2], DLG_BOTTOM),
      str((mb.x, mb.w, mb.bottom)))

plate_px = g2.canvas.get_at((mb.right - 30, mb.bottom - 18))[:3]
check("框内是暗底（白格上也读得清）", max(plate_px) < 80, str(plate_px))
row_y = mb.y + 44 + 12
bright = sum(1 for x in range(mb.x + DLG_PAD, mb.right - 40, 2)
             if g2.canvas.get_at((x, row_y))[:3] == C_TEXT)
check("心声是亮字", bright > 10, "%d 个亮点" % bright)

# 名牌：空心描边（描边是强调色，内部是暗底）—— 一眼和「开口说的话」分开
tab = pygame.Rect(mb.x + DLG_PAD, mb.y - 17, 96, 34)
tab_cols = {g2.canvas.get_at((x, y))[:3]
            for x in range(tab.left, tab.right)
            for y in range(tab.top + 3, tab.bottom - 3, 2)}
check("心声名牌是空心描边（不是对话那种实心块）",
      C_ACCENT in tab_cols and C_BOX in tab_cols, "%s" % sorted(tab_cols)[:5])
check("对话名牌仍然是实心的（对照组）", C_ACCENT in plate_color(g, 0) or C_OLDMAN in plate_color(g, 0))

# 心声要按回车才走（2026-11-12 起），所以字打完之后框里必须给出提示
def accent_px(surf, rect):
    return sum(1 for x in range(rect.left, rect.right, 2)
               for y in range(rect.top, rect.bottom, 2)
               if surf.get_at((x, y))[:3] == C_ACCENT)


enter_zone = pygame.Rect(mb.x + DLG_PAD, mb.bottom - 34, 80, 22)
g2.mono_elapsed = 0.05                             # 字刚开始打：还没有 ENTER
g2.mono_hold = True
g2.draw()
early = accent_px(g2.canvas, enter_zone)
g2.mono_elapsed = g2.mono_type_time                # 字打完了：出现 ENTER
g2.draw()
late = accent_px(g2.canvas, enter_zone)
check("字打完之前框里没有 ENTER / 继续提示", early == 0, "%d px" % early)
check("字打完之后给出 ENTER（世界停着，必须告诉玩家怎么走）", late > 6, "%d px" % late)

# 不会自己消失：等再久也还在（寿命由玩家按回车决定）
for _ in range(int(4 * 60)):
    g2.update(1 / 60)
check("光等不会自己消失（寿命由玩家决定，不是计时器）",
      g2.mono_hold and g2.mono_text == story.M1, "%s / %r" % (g2.mono_hold, g2.mono_text[:12]))

# 每一句心声都必须放得进框（最多 3 行）
fits = {}
for name in ("M1", "M2", "M3", "M4", "M5", "A2_M1", "A2_M2", "A2_M3", "A2_M4"):
    text = getattr(story, name, None)
    if not text:
        continue
    g2.mono_text = text
    fits[name] = len(mono_lines(g2))
g2.mono_text = story.M1
check("9 条心声全部 ≤ 3 行（框装得下）", all(n <= 3 for n in fits.values()), str(fits))

# ==================== 心声会冻住世界（2026-11-12 作者要求）====================
# 作者：「有时候玩家犯错，然后突然出现心声遮住屏幕了，怪还在打你，体验很差。」
# 定稿：全部暂停 + 同句不重复 + 两段式回车（先补完字，再关闭）。


def naked(g, secs):
    """推进时间但**不替玩家按回车** —— 专门用来观察「停住」本身。"""
    for _ in range(max(1, int(secs * 60))):
        g.update(1 / 60)


g3 = new_game()
naked(g3, 3.4)                                     # 开场 M1 会自己冒出来
check("说出一句心声 → 世界进入暂停（mono_hold）", g3.mono_hold, str(g3.mono_hold))

# --- 真停了：玩家、贴图动画、计时全部不动 ---
pos0 = (g3.player.pos.x, g3.player.pos.y)
anim0, move0 = g3.anim_t, g3.move_time
g3.input.handle_event(ev(26))                      # 按 W（按住不放）
naked(g3, 1.0)
check("暂停时按住 W 也走不动", (g3.player.pos.x, g3.player.pos.y) == pos0,
      "%s → %s" % (pos0, (round(g3.player.pos.x), round(g3.player.pos.y))))
check("...连贴图动画都冻住（anim_t 不涨）", g3.anim_t == anim0, "%.3f" % g3.anim_t)
check("...各种计时器也停（move_time 不涨）", g3.move_time == move0, "%.3f" % g3.move_time)

# --- 两段式回车（必须拿一句「字还没打完」的测，不然第一次按就直接关了）---
g4 = new_game()
g4.intro_t = 0.0
g4.reset_mono()
g4.say(story.MONO_STAIN)
g4.update(1 / 60)                                       # 只推进一帧：字远远没打完
g4.handle_event(ev(SC_ENTER))
check("字没打完时按回车：先补完，**不关闭**",
      g4.mono_hold and g4.mono_elapsed >= g4.mono_type_time,
      "hold=%s elapsed=%.2f/%.2f" % (g4.mono_hold, g4.mono_elapsed, g4.mono_type_time))
g4.handle_event(ev(SC_ENTER))
check("再按一次：关闭，世界恢复", not g4.mono_hold, str(g4.mono_hold))

# --- 世界真的重新跑（用刚关掉的那个 g3）---
g3.handle_event(ev(SC_ENTER))                      # M1 早就打完了，一下就该关
check("（准备）关掉开场那句", not g3.mono_hold, str(g3.mono_hold))

anim1 = g3.anim_t
naked(g3, 0.2)
check("恢复之后世界继续跑（anim_t 又涨了）", g3.anim_t > anim1, "%.2f → %.2f" % (anim1, g3.anim_t))

# --- 淡出之后文字才清空 ---
naked(g3, MONO_FADE_OUT + 0.2)
check("淡出结束后文字清空、框消失", g3.mono_text == "" and g3.mono_t == 0.0,
      "%r / %.2f" % (g3.mono_text[:10], g3.mono_t))

# --- 同句冷却：连续涂错只冻一次 ---
g3.reset_mono()
g3.say(story.MONO_STAIN)
check("（准备）同一句能冻住世界", g3.mono_hold)
g3.advance_monologue(); g3.advance_monologue()     # 补完 → 关闭
check("关闭后进入冷却（mono_gap > 0）", g3.mono_gap > 0, "%.1f" % g3.mono_gap)
g3.say(story.MONO_STAIN)
check("冷却期内**同一句**不再冻屏（连续涂错只停一次）", not g3.mono_hold, str(g3.mono_hold))
check("...而且那次 say 被整个吞掉了（没有残留半句）", g3.mono_text == story.MONO_STAIN)
g3.say(story.MONO_BLIND)
check("换一句立刻冻住（冷却只管同一句）", g3.mono_hold and g3.mono_text == story.MONO_BLIND)
check("冷却常量合理（足够盖住连续涂错，又不至于让玩家以为坏了）",
      1.0 <= MONO_REPEAT_GAP <= 8.0, "%.1fs" % MONO_REPEAT_GAP)

# --- 暂停时按 R 能重开，不会卡死 ---
g3.handle_event(ev(SC_R))
check("暂停中按 R 能重开一局（不会卡在暂停里出不来）",
      g3.act == 1 and not g3.mono_hold, "act=%d hold=%s" % (g3.act, g3.mono_hold))

# ==================== 嘀咕（飘字）：反馈类不冻世界 ====================
# 作者 2026-11-14：一天要出现十几次的东西不能每次都停车读。
g4.reset_mono()
g4.toasts.clear()
g4.mumble(story.MONO_STAIN)
check("嘀咕不冻世界（mono_hold 仍是 False）", not g4.mono_hold, str(g4.mono_hold))
check("...但它确实出现在头顶（toasts 里有）", toast_text(g4) == story.MONO_STAIN,
      repr(toast_text(g4)))
t0 = g4.anim_t
auto_mono(g4)
g4.update(1 / 30)
check("...世界照常走（贴图时基 anim_t 在涨）", g4.anim_t > t0, "%.2f → %.2f" % (t0, g4.anim_t))

# 同句冷却
g4.mumble(story.MONO_STAIN)
check("...同一句在冷却里不重复弹（不会刷屏）", len(g4.toasts) == 1, "%d 条" % len(g4.toasts))
g4.mumble(story.MONO_BLIND)
check("...换一句立刻出现", len(g4.toasts) == 2 and toast_text(g4) == story.MONO_BLIND,
      "%d 条 / %r" % (len(g4.toasts), toast_text(g4)))
for i in range(5):
    g4.mumble("line %d" % i)
check("...最多同时 %d 条（新的顶掉最老的）" % TOAST_MAX, len(g4.toasts) == TOAST_MAX,
      "%d 条" % len(g4.toasts))

# 到时间自动消失
for _ in range(int((TOAST_TIME + 0.3) * 30)):
    auto_mono(g4)
    g4.update(1 / 30)
check("...%0.1f 秒后自己消失（不用按回车）" % TOAST_TIME, not g4.toasts,
      "%d 条" % len(g4.toasts))

finish(TITLE)
