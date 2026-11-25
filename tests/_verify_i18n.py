# -*- coding: utf-8 -*-
"""中英双语验收：译文覆盖、字体、折行放得下、切换不污染状态。

规则（2026-11-25 作者定）：
  · 状态里永远存英文，只有渲染时 `lang.T()` 取当前语言 —— 所以这里既验译文，也验「别改状态」；
  · 默认英文；中文只在暂停菜单里切（第 1 项 LANGUAGE）；
  · 中文必须真能画出来（字体文件存在 + 有字形），并且在对话框/心声框里放得下。
"""

import ast
import os
import re
import sys

from _act1_common import check, finish, new_game
from src import lang, story, story_zh, ui  # noqa: E402
from src.config import (  # noqa: E402
    DLG_BOX, DLG_PAD, MONO_MAX_ROWS
)
from src.lang import T  # noqa: E402

TITLE = "I18N · 中英双语"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ==================== 1. 默认与查表 ====================
check("默认英文", lang.LANG == "en", lang.LANG)
check("英文时 T() 原样返回", T("HEALTH") == "HEALTH" and T("PRESS ENTER") == "PRESS ENTER")

lang.set_lang("zh")
check("中文：整句命中", T("HEALTH") == "生命" and T("PRESS ENTER") == "按回车",
      "%s / %s" % (T("HEALTH"), T("PRESS ENTER")))
check("中文：格式化模板（TIME / ACT / 错误数）",
      T("TIME 01:23") == "时间 01:23"
      and T("ACT 3") == "第 3 幕"
      and T("ERRORS 1 / 3 \u2014 IT ONLY NEEDS TO READ") == "错误 1 / 3\u2014\u2014只要读得出来就行",
      "%s / %s" % (T("TIME 01:23"), T("ACT 3")))
check("中文：结局那行（URL 原样保留）",
      T("IT READS:  https://he-r.cn") == "它读出来：https://he-r.cn",
      T("IT READS:  https://he-r.cn"))
check("中文：指令式键帽会翻、真键名不动",
      lang.TK("HOLD J") == "按住 J" and lang.TK("WASD") == "WASD",
      "%s / %s" % (lang.TK("HOLD J"), lang.TK("WASD")))

# ==================== 2. 字体真能画中文 ====================
pf = lang.font_file()
check("中文字体文件存在", pf is not None and os.path.exists(pf), "%s" % (pf,))

g = new_game()


def _nonblank(surf):
    """把一张字图里出现过的颜色数算出来：只有底色 = 没画出来。"""
    return len(set(tuple(surf.get_at((x, y))) for x in range(surf.get_width())
                   for y in range(surf.get_height())))


g.set_language("zh")
img = g.f_dlg.render("码序使圣坛黑域", True, (255, 255, 255))
check("中文渲染有宽度", img.get_width() > 0, "%dpx" % img.get_width())
check("中文渲染不是空白/方块", _nonblank(img) > 3, "%d colors" % _nonblank(img))
check("切中文后字体对象确实换了", g.f_dlg is not g._font_sets["en"]["f_dlg"])

# ==================== 3. 译文覆盖：T() 字面量（AST） ====================
def t_literals(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "T":
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                out.append((node.args[0].value, getattr(node, "lineno", 0)))
    return out


bad = []
for fn in ("ui.py", "game.py"):
    for text, lineno in t_literals(os.path.join(ROOT, "src", fn)):
        if text not in story_zh.ZH and text not in story_zh.TPL:
            bad.append("%s:%d %r" % (fn, lineno, text))
check("所有 T(\"字面量\") 都有译文", not bad, "；".join(bad[:4]))

# ==================== 4. 译文覆盖：story.py 的展示字符串 ====================
KEYCAPS = {"WASD", "SHIFT", "J", "K", "B", "I", "U", "H", "E", "Q", "F", "G", "T",
           "HOLD J", "L"}


def walk_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, (tuple, list)):
        for v in node:
            yield from walk_strings(v)
    elif isinstance(node, dict):
        for v in node.values():
            yield from walk_strings(v)


miss_story = []
for name, value in vars(story).items():
    if name.startswith("_") or callable(value) or isinstance(value, (int, float)):
        continue
    for text in walk_strings(value):
        if not text or text in KEYCAPS or len(text) == 1 and text.isalpha():
            continue
        if re.fullmatch(r"\[[A-Z0-9 ]+\]", text):     # 键帽（[E] / [Q]…）不翻
            continue
        if text not in story_zh.ZH and text not in story_zh.TPL:
            miss_story.append("%s: %r" % (name, text[:40]))
check("story.py 的展示文案全部有译文", not miss_story,
      "缺 %d 条：%s" % (len(miss_story), "；".join(miss_story[:4])))

# ==================== 5. 中文放得下（对话 / 独白） ====================
max_w = DLG_BOX[2] - DLG_PAD * 2
one = g.f_dlg.size("字")[0]
over, rows_bad = [], []
dialog_texts = [t for _, t in story.DIALOG_ONE + story.DIALOG_TWO + story.DIALOG_THREE]
dialog_texts.append(story.LEAVE_LINE[1])
for text in dialog_texts:
    for para in T(text).split("\n"):
        for line in ui.wrap_text(g.f_dlg, para, max_w):
            if g.f_dlg.size(line)[0] > max_w + one:
                over.append(line)
    if len(ui._wrap_paragraphs(g.f_dlg, T(text), max_w)) > ui.dlg_box_lines():
        rows_bad.append(text[:24])
check("中文对话不超框宽", not over, "超宽 %d 行：%s" % (len(over), over[:2]))
check("中文对话不超过对话框行数", not rows_bad, "超行：%s" % rows_bad[:2])

mono_texts = [story.M1, story.M2, story.M3, story.A1_GUIDE, story.A1_WAVE, story.A2_M1,
              story.A4_M1, story.A5_M1, story.ACT6_M1]
mono_bad = []
for text in mono_texts:
    g.mono_text = text
    rows = len(ui.mono_lines(g))
    if rows > MONO_MAX_ROWS:
        mono_bad.append("%s → %d 行" % (text[:16], rows))
check("中文心声不超过框高（%d 行）" % MONO_MAX_ROWS, not mono_bad, "；".join(mono_bad[:3]))

# ==================== 6. 切换不污染状态 ====================
g.mono_text = ""
g.dlg_lines = [(story.OLD_MAN, story.LEAVE_LINE[1])]
g.dlg_i = 0
lines_zh = ui.dialog_lines(g)[0]
check("对话渲染成中文", "如果我能回来。" in T(story.LEAVE_LINE[1]) and lines_zh,
      "%r" % (lines_zh[:1],))
check("状态里仍是英文（对话原文未被改写）",
      g.dlg_lines[0][1] is story.LEAVE_LINE[1], "%r" % (g.dlg_lines[0][1][:20],))

g.prompt_text = story.PROMPT_CALL
check("中文下 prompt 的逻辑比较仍然成立",
      g.prompt_text == story.PROMPT_CALL and T(g.prompt_text) == "按 [T] 呼喊",
      T(g.prompt_text))

g.set_language("en")
check("切回英文：折行与最初一致", ui.dialog_lines(g)[0] == ui._wrap_paragraphs(g.f_dlg, story.LEAVE_LINE[1], max_w))

# ==================== 7. 暂停菜单切换 ====================
g.state = "FREE_ROAM"
g.pause_prev = ""
g._pause_open()
check("ESC 进暂停菜单", g.state == "PAUSE")
check("暂停菜单 4 项（多了 LANGUAGE）", len(ui.PAUSE_OPTIONS) == 4 and ui.PAUSE_OPTIONS[1] == "LANGUAGE")
check("语言项显示当前语言", "ENGLISH" in ui._pause_label(g, 1), ui._pause_label(g, 1))
g.pause_sel = 1
g._pause_confirm()
check("回车切到中文", lang.LANG == "zh" and g.lang == "zh")
check("切完仍停在暂停菜单", g.state == "PAUSE")
check("语言项显示中文", "语言：中文" in ui._pause_label(g, 1), ui._pause_label(g, 1))
g._pause_confirm()
check("再按回车切回英文", lang.LANG == "en" and g.lang == "en")
check("切语言不关闭菜单、不丢 pause_prev", g.state == "PAUSE" and g.pause_sel == 1)

# ==================== 8. 实际绘制一遍：没有漏译 ====================
lang.MISSES.clear()
g.set_language("zh")
g.state = "PAUSE"
g.draw()                                   # 暂停菜单
g._pause_resume()
g.draw()                                   # 战斗/漫游 HUD + 底部键位表
from src.ui import draw_title  # noqa: E402
g.state = "TITLE"
draw_title(g)
g.state = "DEAD"
g.draw()
g.state = "END"
g.act = 5
g.banner_text = story.ACT5_TITLE
g.end_line = story.END_LINE % "https://he-r.cn"
g.draw()
check("绘制过的界面没有漏译（lang.MISSES 为空）",
      not lang.MISSES, "缺：%s" % list(lang.MISSES)[:6])

# 收尾：恢复英文，避免影响后续断言
lang.set_lang("en")

finish(TITLE)
