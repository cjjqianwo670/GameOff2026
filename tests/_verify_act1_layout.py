# -*- coding: utf-8 -*-
"""步骤 1 验收：画布 1360×1000 + 新布局（网格 700×700 / 右侧 520px 面板 / HUD / 底部提示）。"""

import pygame

from _act1_common import WIN, check, finish, new_game, shot
from src.config import (
    C_CELL_WHITE, C_PANEL, CELL, GRID_N, GRID_ORIGIN, GRID_PX, HINT_Y, HUD_Y, PANEL_H, PANEL_W, PANEL_X,
    PANEL_Y,
    SPAWN_ORIGIN, SPAWN_PX, TARGET_OFFSET, WINDOW_H, WINDOW_W
)


TITLE = "STEP 1 · CANVAS 1360x1000"

g = new_game()

check("逻辑画布 1360×1000", (WINDOW_W, WINDOW_H) == (1360, 1000), str((WINDOW_W, WINDOW_H)))
check("Game.canvas 尺寸 = 逻辑画布", g.canvas.get_size() == (1360, 1000), str(g.canvas.get_size()))

grid = pygame.Rect(GRID_ORIGIN, (GRID_PX, GRID_PX))
check("主网格 700×700 完全落在画布内",
      grid.left >= 0 and grid.top >= 0 and grid.right <= PANEL_X and grid.bottom <= WINDOW_H,
      str(grid))

panel = pygame.Rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
check("右侧面板宽 ≥ 500px", PANEL_W >= 500, "%dpx" % PANEL_W)
check("右侧面板不与网格重叠", not panel.colliderect(grid), "%s vs %s" % (panel, grid))
check("顶部 HUD 不压网格", HUD_Y + 44 <= grid.top, "HUD %d / grid top %d" % (HUD_Y, grid.top))
check("底部提示不压网格", HINT_Y >= grid.bottom, "hint %d / grid bottom %d" % (HINT_Y, grid.bottom))

ring = pygame.Rect(SPAWN_ORIGIN, (SPAWN_PX, SPAWN_PX))
check("30×30 生成环包住 25×25 主网格且左对齐世界区",
      ring.contains(grid) and ring.left == 0, str(ring))
check("生成环右沿 = 840 = 面板左沿", ring.right == PANEL_X, "%d" % ring.right)

# 鼠标换算：窗口被等比缩小后，鼠标坐标要 / self.scale 才能点准
# （dummy 视频驱动下 set_pos 不生效，直接替换 get_pos）
_real_get_pos = pygame.mouse.get_pos
pygame.mouse.get_pos = lambda: (408, 300)
g.scale = 0.6
mx, my = g.mouse_xy()
check("鼠标坐标按 /scale 换算（0.6 缩放 → 680,500）", abs(mx - 680) <= 1 and abs(my - 500) <= 1,
      "%s" % ((mx, my),))
pygame.mouse.get_pos = _real_get_pos

p = shot(g, "01_layout.png")
col = g.canvas.get_at((GRID_ORIGIN[0] + CELL // 2, GRID_ORIGIN[1] + CELL // 2))[:3]
check("网格左上格是白底", col == C_CELL_WHITE, str(col))
col_panel = g.canvas.get_at((PANEL_X + PANEL_W // 2, PANEL_Y + PANEL_H - 40))[:3]
check("右侧面板底色是面板色（空着的区域）", col_panel == C_PANEL, str(col_panel))

# 圣坛（21×21）在网格里正居中：偏移 (2,2)
orr, occ = TARGET_OFFSET
check("圣坛偏移 (2,2) → 21×21 正居中", GRID_N - 21 == 2 * occ == 2 * orr, str(TARGET_OFFSET))

print("shot ->", p)
finish(TITLE)
