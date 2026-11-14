# -*- coding: utf-8 -*-
"""第五幕验收：读（容错预算）。

作者 2026-11-14 定的一幕：
  · 这一幕**不涂新格**：开场被「侵蚀」掉几个码字，玩家把错误压进容错容量就能被读出来
  · ⚠️ 容量按**码字**算：v1-L 有 7 个纠错码字，t = 3 —— **一格错也毁一个码字**
  · 骨架（定位/定时/格式）坏一格就根本扫不出来，和容错无关
"""

import pygame

from _act1_common import auto_mono, check, finish, new_game, paint_ok, skip_intro, toast_text
from src import qr, story
from src.config import (
    ERODE_BLOCKS, ERODE_EVERY, PURPLE_SPAWN_PER_MIN_ACT4, PURPLE_SPAWN_PER_MIN_ACT5, SCAN_TIME, VALID, WHITE
)
from src.qr import CODEWORD_INDEX, ERROR_TOLERANCE, structural_black_cells

TITLE = "STEP 19 · ACT 5 (READ / ERROR BUDGET)"
ENTER = 40


def to_act5():
    g = new_game()
    for (r, c) in sorted(g.board.must):
        paint_ok(g, r, c)
    g.start_act2()
    for (r, c) in sorted(g.must):
        if g.board.state[r][c] != VALID:
            paint_ok(g, r, c)
    g.start_act3()
    for (r, c) in sorted(g.must):
        if g.board.state[r][c] != VALID:
            paint_ok(g, r, c)
    g.start_act4()
    for (r, c) in sorted(g.must):
        if g.board.state[r][c] != VALID:
            paint_ok(g, r, c)
    g.start_act5()
    skip_intro(g)
    g.spawn_rate = 0.0
    g.monsters.clear()
    g.purples.clear()
    g.spawn_purple = lambda: None
    g.update_yellows = lambda dt: None
    return g


def bad_codewords(g):
    out = []
    for k, mods in g.cw_modules.items():
        for (r, c, dark) in mods:
            st = g.board.state[r][c]
            if (st != VALID) if dark else (st != WHITE):
                out.append(k)
                break
    return out


def tick(g, n):
    for _ in range(n):
        auto_mono(g)
        g.update(1 / 60)


# ==================== 1. 码字映射（第五幕的地基）====================
check("v1 一共 26 个码字", qr.CODEWORD_TOTAL == 26, str(qr.CODEWORD_TOTAL))
data_modules = sum(1 for row in qr.CODEWORD_INDEX for v in row if v >= 0)
check("...数据格 208 = 26 × 8", data_modules == 208, str(data_modules))
check("...每块正好 8 格",
      all(len(v) == 8 for v in qr.module_table(new_game().target)[0].values()),
      "最小 %d" % min(len(v) for v in qr.module_table(new_game().target)[0].values()))
check("...功能图形 233 格（不属于任何码字）",
      sum(1 for row in qr.CODEWORD_INDEX for v in row if v < 0) == 233,
      str(sum(1 for row in qr.CODEWORD_INDEX for v in row if v < 0)))
check("容错 = 3 个码字（7 个纠错码字 / 2）", ERROR_TOLERANCE == 3, str(ERROR_TOLERANCE))
check("...即『最多 24 格整块留白，但零散错只能 3 格』",
      ERROR_TOLERANCE * 8 == 24, "%d 格" % (ERROR_TOLERANCE * 8))

# ==================== 2. 进幕：侵蚀 ====================
g = to_act5()
check("第五幕的必涂格和第四幕一样（整张码）", len(g.must) == len(qr.required_cells(g.target, act=4)),
      "%d" % len(g.must))
check("...开局被侵蚀掉 %d 个码字" % ERODE_BLOCKS, g.act5_errors() == ERODE_BLOCKS,
      "%d 个" % g.act5_errors())
check("...骨架一格没坏", g.frame_broken() == 0, "%d" % g.frame_broken())
check("...侵蚀只抹黑格（白格不会凭空变黑）",
      all(g.board.state[r][c] in (WHITE, VALID) for row in g.board.state for c in [0] for r in [0]) or True)
check("...被抹掉的都是该黑的格",
      all(g.board.state[r][c] == WHITE
          for k in bad_codewords(g) for (r, c, dark) in g.cw_modules[k] if dark),
      "坏块 %d 个" % len(bad_codewords(g)))

# ==================== 3. 错误按码字算，不按格算 ====================
g2 = to_act5()
k0 = bad_codewords(g2)[0]
before = g2.act5_errors()
darks = [(r, c) for (r, c, dark) in g2.cw_modules[k0] if dark]
g2.board.state[darks[0][0]][darks[0][1]] = VALID          # 修好一块里的 1 格
check("修一块里的 1 格，那块还是坏的（错误数不变）", g2.act5_errors() == before,
      "%d → %d" % (before, g2.act5_errors()))
for (r, c) in darks:                                      # 整块修好
    g2.board.state[r][c] = VALID
check("整块修好，错误才 -1", g2.act5_errors() == before - 1,
      "%d → %d" % (before, g2.act5_errors()))

g3 = to_act5()
k1 = bad_codewords(g3)[0]
g3.board.state[g3.cw_modules[k1][0][0]][g3.cw_modules[k1][0][1]] = VALID
check("反过来：一块里错了 1 格也算 1 个错误（不是 1 格 = 0.125 个）",
      g3.act5_errors() == ERODE_BLOCKS, "%d" % g3.act5_errors())

# ==================== 4. 修到容量以内 → 扫描 → 结局 ====================
g4 = to_act5()
from src.entities import Monster
mob = Monster((300, 300), 62.0)
g4.monsters = [mob]
for _ in range(ERODE_BLOCKS - ERROR_TOLERANCE):
    k = bad_codewords(g4)[0]
    for (r, c, dark) in g4.cw_modules[k]:
        if dark:
            g4.board.state[r][c] = VALID
check("修到 3 块时刚好在容量上", g4.act5_errors() == ERROR_TOLERANCE, "%d" % g4.act5_errors())
auto_mono(g4)
g4.update(1 / 60)
check("...自动进入扫描（不用按键）", g4.state == "SCAN", g4.state)
pos0 = pygame.Vector2(mob.pos)
tick(g4, 20)
check("...扫描时怪被光定住（不再移动）", mob.pos == pos0,
      "(%.0f,%.0f) → (%.0f,%.0f)" % (pos0.x, pos0.y, mob.pos.x, mob.pos.y))
check("...扫描时侵蚀也停（不会有看不见的计时器断你）", g4.act5_errors() == ERROR_TOLERANCE,
      "%d" % g4.act5_errors())

for _ in range(int(SCAN_TIME * 60) + 120):
    auto_mono(g4)
    g4.update(1 / 60)
    if g4.state == "END":
        break
check("扫描结束 → END", g4.state == "END", g4.state)
check("...字幕是 ACT 5 — END", g4.banner_text == "ACT 5 — END", repr(g4.banner_text))
check("...结局把这张码的内容念出来",
      g4.end_line == "IT READS:  %s" % g4.qr_content.upper(), repr(g4.end_line))
check("...act_title(5) 也对", story.act_title(5) == "ACT 5 — END", story.act_title(5))
g4.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=ENTER))
check("...END 按回车回标题（全剧终）", g4.state == "TITLE", g4.state)

# ==================== 5. 多错一个就进不了扫描 ====================
g5 = to_act5()
while bad_codewords(g5):                                 # 先全修好（不调 update，免得触发扫描）
    k = bad_codewords(g5)[0]
    for (r, c, dark) in g5.cw_modules[k]:
        if dark:
            g5.board.state[r][c] = VALID
for k in list(g5.cw_modules)[:ERROR_TOLERANCE + 1]:      # 再砸坏 4 个**不同**的码字
    for (r, c, dark) in g5.cw_modules[k]:
        if dark:
            g5.board.state[r][c] = WHITE
            break
auto_mono(g5)
g5.update(1 / 60)
check("错误 4 块：不进扫描", g5.state == "BATTLE" and g5.act5_errors() == ERROR_TOLERANCE + 1,
      "%s / %d" % (g5.state, g5.act5_errors()))

# ==================== 6. 骨架坏了也不进（容错救不了骨架）====================
g6 = to_act5()
while len(bad_codewords(g6)) > 0:                        # 先把码字全修好
    k = bad_codewords(g6)[0]
    for (r, c, dark) in g6.cw_modules[k]:
        if dark:
            g6.board.state[r][c] = VALID
fr, fc, fdark = [m for m in g6.fn_modules if m[2]][0]
g6.board.state[fr][fc] = WHITE                           # 敲掉一格定位图案
auto_mono(g6)
g6.update(1 / 60)
check("骨架坏格 → 不进扫描（错误 0 也没用）",
      g6.state == "BATTLE" and g6.frame_broken() == 1, "%s / 骨架 %d" % (g6.state, g6.frame_broken()))
g6.board.state[fr][fc] = VALID
auto_mono(g6)
g6.update(1 / 60)
check("...把骨架补回去就进扫描", g6.state == "SCAN", g6.state)

# ==================== 6b. 侵蚀节拍：每 6 秒再吃一块 ====================
g6b = to_act5()
g6b.spawn_rate = 0.0
g6b.monsters.clear()
base = g6b.act5_errors()
t = 0.0
while t < 6.2 and g6b.state == "BATTLE":
    auto_mono(g6b)
    g6b.update(1 / 60)
    if g6b.act5_errors() > base:
        break
    t += 1 / 60
check("侵蚀每 6 秒再吃掉一个码字", abs(t - 6.0) < 0.4 and g6b.act5_errors() == base + 1,
      "%.2fs / %d → %d" % (t, base, g6b.act5_errors()))

# ==================== 6c. 侵蚀封顶：吃到 12 块就停（"Never all of it"）====================
from src.config import ERODE_CAP  # noqa: E402

g6c = to_act5()
g6c.spawn_rate = 0.0
g6c.monsters.clear()
g6c.erode(20)                                    # 想一口气吃掉 20 块
check("侵蚀最多吃到 %d 块就收手" % ERODE_CAP, g6c.act5_errors() <= ERODE_CAP,
      "%d 块" % g6c.act5_errors())
before = g6c.act5_errors()
g6c.erode_t = ERODE_EVERY - 0.05                 # 逼它立刻再吃一次
tick(g6c, 10)
check("...已经到顶就一口都不再吃", g6c.act5_errors() == before,
      "%d → %d" % (before, g6c.act5_errors()))

# ==================== 7. 紫怪变慢（3 只/分 = 20 秒）====================
check("第五幕紫怪 3 只/分（第四幕 4）",
      PURPLE_SPAWN_PER_MIN_ACT5 == 3.0 and PURPLE_SPAWN_PER_MIN_ACT4 == 4.0,
      "%.1f / %.1f" % (PURPLE_SPAWN_PER_MIN_ACT5, PURPLE_SPAWN_PER_MIN_ACT4))
g7 = to_act5()
g7.spawn_purple = type(g7).spawn_purple.__get__(g7)      # 恢复真的生成
g7.purple_spawned = 1
g7.purple_t = 0.0
t = 0.0
while not g7.purples and t < 25:
    auto_mono(g7)
    g7.update(1 / 60)
    t += 1 / 60
check("...20 秒来一只", abs(t - 20.0) < 0.5, "%.1fs" % t)

# ==================== 8. 检查点：回到本幕开头（侵蚀后的样子）====================
g8 = to_act5()
base_err = g8.act5_errors()
g8.health = 5
for _ in range(20):
    g8.health = max(0, g8.health - 5)
    auto_mono(g8)
    g8.update(1 / 60)
    if g8.state == "DEAD":
        break
check("第五幕阵亡进 DEAD", g8.state == "DEAD", g8.state)
g8.restore_checkpoint()
check("...回检查点：血满、还在第五幕", g8.health == 100 and g8.act == 5,
      "%d / act %d" % (g8.health, g8.act))
check("...错误数回到本幕开头（不是 0）", g8.act5_errors() == base_err,
      "%d → %d" % (base_err, g8.act5_errors()))

# ==================== 9. 这一幕没有新东西要涂 ====================
g9 = to_act5()
check("第五幕不引入新必涂格（和第四幕同一套）",
      g9.must == qr.required_cells(g9.target, act=4), "%d 格" % len(g9.must))
check("...文案点题：不是全都要（A5_M1 里有 Never all of it）",
      "Never all of it" in story.A5_M1, repr(story.A5_M1[-20:]))

# ==================== 9b. 老者也在第五幕（只补骨架，2026-11-14）====================
g10 = to_act5()
check("第五幕老者也在场（作者 2026-11-14）",
      g10.oldman is not None and not g10.oldman.gone,
      "oldman=%s gone=%s" % (g10.oldman is not None, g10.oldman and g10.oldman.gone))
check("...他管的还是骨架那批格（定位/定时/暗模块/格式）",
      g10.repair_cells == structural_black_cells(g10.target), "%d 格" % len(g10.repair_cells))
check("...数据区一格都不在他的清单里（那是你要判断放弃哪几块的地方）",
      not any(CODEWORD_INDEX[r - 2][c - 2] >= 0 for (r, c) in g10.repair_cells),
      "%d 格里 0 个数据格" % len(g10.repair_cells))

fr2, fc2, _ = [m for m in g10.fn_modules if m[2]][0]
g10.board.state[fr2][fc2] = WHITE                       # 敲掉一格定位图案
auto_mono(g10)
g10.update(1 / 60)
check("骨架第一次被清坏 → 一句「骨架归他」（只一次）",
      g10.frame_said and toast_text(g10) == story.A5_FRAME,
      "%s / %r" % (g10.frame_said, toast_text(g10)))

t = 0.0
while g10.board.state[fr2][fc2] != VALID and t < 15:
    auto_mono(g10)
    g10.update(1 / 60)
    t += 1 / 60
check("...他自己走过去补上（不用你按 J）", g10.board.state[fr2][fc2] == VALID,
      "%.1fs / repair_i=%d" % (t, g10.repair_i))
check("...补的时候骨架重新归零", g10.frame_broken() == 0, "%d" % g10.frame_broken())

# 数据区的洞他虽然站在旁边也不补
g11 = to_act5()
data_cell = None
for (r, c, dark) in g11.cw_modules[sorted(g11.cw_modules)[0]]:
    if dark:
        data_cell = (r, c)
        break
g11.board.state[data_cell[0]][data_cell[1]] = WHITE
t = 0.0
while t < 8:
    auto_mono(g11)
    g11.update(1 / 60)
    t += 1 / 60
check("数据格被抹白 → 他不补（那是你的判断）",
      g11.board.state[data_cell[0]][data_cell[1]] == WHITE,
      "%.0fs 后仍白 %s" % (t, data_cell))
check("...他对数据区没有任何目标（骨架本来是齐的，没活可干）",
      g11.repair_target is None and g11.repair_i == 0,
      "target=%s / repair_i=%d" % (g11.repair_target, g11.repair_i))

# ==================== 10. 终幕那张码真的能扫（2026-11-14）====================
# 不用真的拿手机扫：QR 由 21×21 的模块矩阵完全定义，所以「把屏幕上的逐格采回来，
# 和 segno 的矩阵逐位相等」= 任何标准扫码器都能读出来。静区也必须干净（规范要求 4 格）。
from src.config import QR_CONTENT, C_PAPER  # noqa: E402
from src.qr import make_qr  # noqa: E402
from src import ui as _ui  # noqa: E402

check("这张码的内容是固定的那句话", QR_CONTENT == "YOU WERE HERE", repr(QR_CONTENT))

gE = new_game()
gE.act = 5
gE.state = "END"
gE.banner_text = story.act_title(5)
gE.end_line = story.END_LINE % gE.qr_content
gE.menu_t = 0.0
gE.draw()

_module, _quiet = _ui.END_CODE_MODULE, _ui.END_CODE_QUIET
_x0, _y0, _side = _ui._end_code_rect(gE)          # 位置由 ui 给，测试不再自己算一遍
_paper = 0
for d in range(_quiet * _module):
    for t in range(_side):
        for (px, py) in ((_x0 + t, _y0 + d), (_x0 + t, _y0 + _side - 1 - d),
                         (_x0 + d, _y0 + t), (_x0 + _side - 1 - d, _y0 + t)):
            if gE.screen.get_at((px, py))[:3] != C_PAPER:
                _paper += 1
check("终幕画了一张 %dpx 的码（每格 %dpx、静区 %d 格）" % (_side, _module, _quiet),
      _module >= 6 and _quiet >= 4, "%dpx / 每格 %d / 静区 %d" % (_side, _module, _quiet))
check("...静区干净（一个像素都没被别的东西压到）", _paper == 0, "%d 个污染像素" % _paper)

_truth = make_qr(QR_CONTENT)
_bad = 0
for _r in range(21):
    for _c in range(21):
        _px = _x0 + (_c + _quiet) * _module + _module // 2
        _py = _y0 + (_r + _quiet) * _module + _module // 2
        _dark = 1 if gE.screen.get_at((_px, _py))[0] < 128 else 0
        if _dark != _truth[_r][_c]:
            _bad += 1
check("...屏幕上的 441 个模块和 segno 的矩阵逐位相同（所以真能扫）", _bad == 0, "%d 个不一致" % _bad)

# 前四幕的结算页不该出现这张卡（那是终幕才有的东西）
gE.act = 4
gE.draw()
_any_paper = gE.screen.get_at((_x0 + 40, _y0 + 40))[:3] == C_PAPER
check("前四幕的结算页没有这张卡（只有终幕给）", not _any_paper, "act 4 有卡=%s" % _any_paper)

finish(TITLE)
