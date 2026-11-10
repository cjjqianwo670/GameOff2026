# -*- coding: utf-8 -*-
"""DATA SHIFT —— 入口

两种启动方式都行：

    python -m src.main        # 从项目根目录
    python src/main.py        # 直接跑脚本

只有「开窗口 + 主循环」两件事，其余都在各模块里：
  config 数值 | grid 坐标 | qr 图案 | board 棋盘 | entities 玩家/怪
  input_state 键盘 | game 规则 | ui 界面
"""

import os
import sys

# 直接 `python src/main.py` 时，sys.path 里只有 src/，
# 而模块之间用的是 `from src.xxx import ...`，所以要让项目根也进 sys.path。
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from src.config import FIT_MARGIN_X, FIT_MARGIN_Y, FPS, MIN_SCALE, WINDOW_H, WINDOW_W
from src.game import Game

# ==== 入口 ====


def create_window():
    """按桌面可用空间等比决定窗口尺寸，保证不被屏幕/任务栏裁掉。

    逻辑画布是 1360×1000（非正方形），窗口按同一个比例缩，
    所以 Game.scale = 窗口宽 / WINDOW_W 这一个因子就能把鼠标坐标换算回逻辑坐标。
    """
    info = pygame.display.Info()
    avail_w = info.current_w - FIT_MARGIN_X
    avail_h = info.current_h - FIT_MARGIN_Y
    scale = min(1.0, avail_w / float(WINDOW_W), avail_h / float(WINDOW_H))
    scale = max(MIN_SCALE, scale)
    return pygame.display.set_mode((int(WINDOW_W * scale), int(WINDOW_H * scale)))


def main():
    pygame.init()
    window = create_window()
    pygame.display.set_caption("DATA SHIFT")
    clock = pygame.time.Clock()
    game = Game(window)

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 1 / 30)   # dt 上限防切窗口后瞬移
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            else:
                game.input.handle_event(e)           # 键盘状态
                game.handle_event(e)                 # R / ESC / F1，两者不互斥
        game.update(dt)
        game.draw()
        pygame.display.flip()
        if not game.running:
            running = False

    pygame.quit()

if __name__ == "__main__":
    main()
