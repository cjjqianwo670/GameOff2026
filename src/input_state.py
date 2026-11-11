# -*- coding: utf-8 -*-
"""键盘状态：只用 scancode，保证输入法 / CapsLock / Shift 下都能走。
"""

import pygame

from src.config import DIR_KEYS

# ==== 键盘状态 ====


class InputState:
    """全部键盘操作，三层保险：关文本输入 + scancode 事件 + scancode 索引兜底。

    IME 候选窗会吃掉字母键的 KEYDOWN，keycode 又可能被当物理键号查表（幽灵移动），
    scancode 是 USB-HID 物理键位，与布局/CapsLock/Shift/输入法无关。
    """

    def __init__(self):
        try:
            pygame.key.stop_text_input()   # 本游戏不需要打字，让 IME 退化为英文直通
        except Exception:
            pass
        self.held = set()                  # 存 scancode
        self.last_dir = None               # 最后按下的方向键，斜向时优先听它的

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            self.held.add(e.scancode)
            if e.scancode in DIR_KEYS:
                self.last_dir = e.scancode
        elif e.type == pygame.KEYUP:
            self.held.discard(e.scancode)
        elif e.type == pygame.WINDOWFOCUSLOST:
            self.held.clear()              # 防 Alt+Tab 后按键卡死
            self.last_dir = None
        elif e.type == pygame.WINDOWFOCUSGAINED:
            # 失焦期间可能漏掉 KEYUP，回来时不要相信旧状态（防「回来就一直走」）
            self.held.clear()
            self.last_dir = None

    def down(self, sc):
        """只看事件集合。

        ⚠️ **不要用 `pygame.key.get_pressed()[sc]` 兜底**（2026-11-11 移除）。
        那个数组在部分环境下是按 **keycode** 索引的，而这里传的是 **scancode**，
        两套号会在数值上撞车：

            按「回车」→ keycode 13 → get_pressed()[13] 为真
            「J」的 scancode  = 13 → down(SC_J) 为真 → **回车被当成 J，站着不动就涂黑脚下**

        （字母键里只有 J 会撞：其余 scancode 在 keycode 空间里对应 Ctrl 组合，玩家不会按到。
        这也正是「只有按回车会误涂」的原因。）

        代价：失去「事件丢失」的兜底。但 SDL 保证 KEYDOWN/KEYUP 成对，
        失焦时下面会清空 held，比串键安全得多。
        """
        return sc in self.held

    def dir4(self):
        """返回 (dr, dc) 或 None。格子移动只能四向，斜向按「最后按下」的那颗键走。"""
        if self.last_dir is not None and self.down(self.last_dir):
            return DIR_KEYS[self.last_dir]
        for sc, d in DIR_KEYS.items():     # 兜底：last_dir 键已松开时按固定顺序取
            if self.down(sc):
                return d
        return None
