# -*- coding: utf-8 -*-
"""资源定位：同一份代码要能在三种环境里找到 `src/assets/`。

1. 源码运行：`src/assets/`；
2. PyInstaller（onedir）：`sys._MEIPASS/src/assets/`；
3. pygbag（浏览器）：虚拟文件系统里 cwd 可能是归档根，`__file__` 也可能是相对路径。

`path("assets", "fonts", "...")` 返回第一个**真实存在**的绝对路径；都没有则返回 None。
"""

import os
import sys


def path(*parts):
    here = os.path.dirname(os.path.abspath(__file__))          # .../src
    roots = []
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass:
        roots.extend([os.path.join(meipass, "src"), meipass])
    roots.extend([
        here,
        os.path.dirname(here),
        os.getcwd(),
        os.path.join(os.getcwd(), "src"),
    ])
    for root in roots:
        p = os.path.join(root, *parts)
        if os.path.exists(p):
            return p
    return None
