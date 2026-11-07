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

    def down(self, sc):
        # 事件集合优先，get_pressed 兜底（索引也用 scancode，最坏只是 False，不会幽灵移动）
        return sc in self.held or pygame.key.get_pressed()[sc]

    def dir4(self):
        """返回 (dr, dc) 或 None。格子移动只能四向，斜向按「最后按下」的那颗键走。"""
        if self.last_dir is not None and self.down(self.last_dir):
            return DIR_KEYS[self.last_dir]
        for sc, d in DIR_KEYS.items():     # 兜底：last_dir 键已松开时按固定顺序取
            if self.down(sc):
                return d
        return None
