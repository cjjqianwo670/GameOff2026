# -*- coding: utf-8 -*-
"""叙事文本 —— 全部台词只在这里，改文案只动这个文件。

规矩（提纲 §12）：只给现象不给解释；主角不说话；全大写 ASCII；
同一句只在固定位置出现（重复即伏笔），别加第三次。

注意：`LEVELS` 必须和 `config.LEVELS` 一一对应（顺序、条数都一样）。
"""

TITLE = "YOU WAKE UP MID-SENTENCE."

# key=碎片编号 / name=这一关的真相 / open=开场句 / trigger=局中一次性触发句 / end=结算句
LEVELS = (
    {
        "key": "01", "name": "SHAPE",
        "open": "PAINT WHAT LOOKS RIGHT.",
        "trigger": None,
        "end": "IT LOOKS RIGHT. THAT IS ENOUGH.",
    },
    {
        "key": "02", "name": "ERASURE",
        "open": "SOMETHING IS TAKING ROWS BACK.",
        "trigger": "TOO PRECISE TO BE NOISE.",
        "end": "NOISE DOES NOT COORDINATE. SOMETHING DOES.",
    },
    {
        "key": "03", "name": "GRAMMAR",
        "open": "A CODE IS NOT A PICTURE.",
        "trigger": None,
        "end": "THE GRID REMEMBERS ITS RULES.",
    },
    {
        "key": "04", "name": "REDUNDANCY",
        "open": "DAMAGE IS NOT DEATH.",
        "trigger": None,
        "end": "PREVIOUS SEQUENCER: I ALSO FORGOT. I LEFT THIS FOR YOU.",
    },
    {
        "key": "05", "name": "FORMAT",
        "open": "TWO COPIES. ONE NAME.",
        "trigger": "HALF A NAME.",
        "end": "ONE MODULE LEFT.",
    },
)

FAIL = "NOT YET READABLE."          # 失败页统一一句，不换（重试频繁，别每次砸台词）
UNREADABLE = "FRAGMENT ?? / UNREADABLE"   # 还没解锁 / 还没读懂的那一片


def level(i):
    """取第 i 关（从 1 数）的文案；越界就夹到首尾，绝不抛异常。"""
    return LEVELS[max(0, min(len(LEVELS) - 1, i - 1))]


def label(i):
    """选关页/结算页用的短名：FRAGMENT 01 / SHAPE"""
    it = level(i)
    return "FRAGMENT %s / %s" % (it["key"], it["name"])
