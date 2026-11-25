# -*- coding: utf-8 -*-
"""网页版入口（pygbag / WebAssembly）。

和 `src/main.py` 的唯一区别：**每帧必须 `await asyncio.sleep(0)` 把控制权还给浏览器**，
否则 WASM 里会整页卡死。主循环其余逻辑与桌面入口保持一致。

窗口用 1088×800（逻辑画布 1360×1000 的 0.8 倍），`Game.scale` 会自动把鼠标坐标换算回去。
"""

import asyncio
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pygame                                    # noqa: E402

from src.config import FPS                       # noqa: E402
from src.game import Game                        # noqa: E402

WEB_W, WEB_H = 1088, 800


async def main():
    pygame.init()
    window = pygame.display.set_mode((WEB_W, WEB_H))
    pygame.display.set_caption("DATA SHIFT")
    clock = pygame.time.Clock()
    game = Game(window)

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 1 / 30)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            else:
                game.input.handle_event(e)
                game.handle_event(e)
        game.update(dt)
        game.draw()
        pygame.display.flip()
        if not game.running:
            running = False
        await asyncio.sleep(0)                   # 交给浏览器一帧（必须）


asyncio.run(main())
