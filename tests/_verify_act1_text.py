# -*- coding: utf-8 -*-
"""文案一致性验收：story.py 里的每一句都必须能在英文文案文件里**原样找到**。

这条是给「一个字都不要自己改」这条要求兜底的：改台词时先改那份 md，再同步 story.py。
"""

import io
import os
import sys

from _act1_common import check, finish

TITLE = "TEXT · VERBATIM AGAINST THE COPY FILE"

# 2026-11-14：文案搬进仓库 docs/（以前指向工作区里的 游戏设计方案/，仓库外的一个目录）
MD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  "docs", "DATA_SHIFT_第一幕英文文案.md")

from src import story  # noqa: E402

md = io.open(MD, encoding="utf-8").read()


def found(text):
    """台词可能被 md 的表格行切断？这里的 md 一行一句，直接整句找。"""
    return text in md


lines = []
for i, (who, text) in enumerate(story.DIALOG_ONE, 1):
    lines.append(("对话一 #%02d" % i, text))
for i, (who, text) in enumerate(story.DIALOG_TWO, 1):
    lines.append(("对话二 #%02d" % i, text))
lines.append(("5.3 老者最后一句", story.LEAVE_LINE[1].replace("\n", " ")))

bad = [name for name, text in lines if not found(text)]
check("对话 %d 句全部与文案文件逐字一致" % len(lines), not bad, "不一致：%s" % bad)

singles = [
    ("M1 第一行", story.M1.split("\n")[0]),
    ("M1 第二行", story.M1.split("\n")[1]),
    ("M2", story.M2), ("M3", story.M3), ("M4", story.M4), ("M5", story.M5),
    ("红怪狠话", story.THREAT),
    ("学走路提示", story.TUTORIAL_MOVE),
    ("学异象提示", story.TUTORIAL_SHIFT),
    ("呼喊提示", story.PROMPT_CALL),
    ("K 清除教学", story.HINT_CLEAR),
    ("脏格嘀咕", story.MONO_STAIN), ("没照嘀咕", story.MONO_BLIND),
    ("来袭嘀咕", story.MONO_INCOMING), ("被咬嘀咕", story.MONO_HIT),
    ("脏格扣血嘀咕", story.MONO_STAIN_HURT),
    ("拾取提示", story.PROMPT_PICK),
    ("背包说明", story.ITEM_BAG),
    ("地图说明", story.ITEM_MAP),
    ("幕结束", story.ACT_TITLE),
]
bad2 = [name for name, text in singles if not found(text)]
check("独白 / 提示 / 道具说明 / 结尾字幕全部逐字一致",
      not bad2, "不一致：%s" % bad2)

# 说话人只有两个，且不出现玩家的真名
check("说话人只有 OLD MAN / SEQUENCER",
      {w for w, _ in story.DIALOG_ONE} | {w for w, _ in story.DIALOG_TWO} == {"OLD MAN", "SEQUENCER"})

# 分支：坛内 13 句；坛外 8 句 + 汇合 9 句
one = story.branch(True)
two = story.branch(False)
check("坛内支线 = 13 句", len(one) == 13, "%d" % len(one))
check("坛外支线 = 8 + 9 = 17 句", len(two) == 17, "%d" % len(two))
check("坛外前 8 句是对话二", two[:8] == list(story.DIALOG_TWO))
check("坛外第 9 句起 = 对话一第 5 句起（汇合不重复）",
      two[8:] == list(story.DIALOG_ONE[story.MERGE_INDEX:]))
check("汇合点那一句是 I didn't either, at first",
      two[8][1].startswith("I didn't either, at first"))

# 文本里不许出现中文（界面全英文）
all_text = " ".join(t for _, t in one + two) + " ".join(t for _, t in singles)
# 破折号 — 是英文文案里本来就有的（U+2014），只查中日韩字符
cjk = [ch for ch in all_text if "\u4e00" <= ch <= "\u9fff"]
check("文本里没有中文（只允许英文 + 文案里的 — ）", not cjk, "".join(cjk[:10]))

finish(TITLE)
