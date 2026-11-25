# -*- coding: utf-8 -*-
"""中英双语：**状态里永远存英文，绘制时才用 `T()` 取当前语言**。

为什么不直接把状态里的字符串翻译掉：
  · ui.py 有 `g.prompt_text == story.PROMPT_CALL`、`who == story.OLD_MAN` 这类**逻辑比较**；
  · `tests/_verify_act1_text.py` 断言状态与 docs 英文文案逐字一致。
所以只在这一层做「英文 → 当前语言」的映射；默认英文时 `T()` 原样返回，行为与改前完全一致。

译文表在 `story_zh.py`：`ZH` 是整句映射，`TPL` 是含 `%` 的模板（状态里存的是**已经格式化好**的
英文，比如 `TIME 01:23`，所以这里要反向匹配模板再替换）。
"""

import re

from src import assets, story_zh

LANG = "en"                  # "en" / "zh"
LANGS = ("en", "zh")
MISSES = set()               # 查不到的英文（测试断言为空，防止漏译）

_FONT_PARTS = ("assets", "fonts", "NotoSansSC-VF.ttf")


def font_file():
    """中文字体路径：源码 / PyInstaller / pygbag 三种环境都能定位（见 `assets.path`）。"""
    return assets.path(*_FONT_PARTS)


def set_lang(code):
    """切换语言。只改这一层的状态码；字体与重绘由 `Game.set_language` 负责。"""
    global LANG
    if code not in LANGS:
        raise ValueError("unknown language: %r" % (code,))
    LANG = code


def is_zh():
    return LANG == "zh"


# `%d` / `%02d` / `%s` / `%f` / `%x` —— 模板里要替换掉的部分
_FMT = re.compile(r"%[-+ 0#]*[0-9]*(?:\.[0-9]+)?[dsfx]")
_PATTERNS = None


def _split_template(text):
    """把模板拆成「字面段列表」（长度 = 占位符个数 + 1）。"""
    return _FMT.split(text)


def _patterns():
    """(正则, 中文分段, 中文模板) 列表。首次用到才编译。"""
    global _PATTERNS
    if _PATTERNS is None:
        pats = []
        for en, zh in story_zh.TPL.items():
            parts = _split_template(en)
            zh_parts = _split_template(zh)
            if len(parts) != len(zh_parts):
                raise ValueError("模板占位符数量不一致：%r -> %r" % (en, zh))
            rx = re.compile("^" + "(.*?)".join(re.escape(p) for p in parts) + "$")
            pats.append((rx, zh_parts))
        _PATTERNS = pats
    return _PATTERNS


def T(text):
    """把一段英文换成当前语言。查不到就原样返回，并记进 `MISSES`。"""
    if LANG == "en" or not text:
        return text
    hit = story_zh.ZH.get(text)
    if hit is not None:
        return hit
    # 状态里存的是**格式化后**的英文（`TIME 01:23`），所以模板要无条件试一遍
    for rx, zh_parts in _patterns():
        m = rx.match(text)
        if m:
            out = [zh_parts[0]]
            for i, group in enumerate(m.groups()):
                out.append(group)
                out.append(zh_parts[i + 1])
            return "".join(out)
    MISSES.add(text)
    return text


def TK(key):
    """键帽文本：只翻「指令式键帽」（`HOLD J`），真键名（WASD / SHIFT / J…）原样显示。"""
    if LANG == "en":
        return key
    return story_zh.KEYS.get(key, key)
