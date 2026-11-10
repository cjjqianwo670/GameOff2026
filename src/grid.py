# -*- coding: utf-8 -*-
"""坐标换算：格子 <-> 像素。

全局只允许用这四个函数换算坐标，别处不许手写 r * CELL 之类的算式。
"""

import pygame

from src.config import CELL, GRID_N, GRID_ORIGIN, TARGET_N, TARGET_OFFSET

# ==== 坐标工具 ====


def cell_to_rect(r, c):
    return pygame.Rect(GRID_ORIGIN[0] + c * CELL,
                       GRID_ORIGIN[1] + r * CELL, CELL, CELL)


def pos_to_cell(x, y):
    """屏幕坐标 → (row, col)；不在主网格内返回 None。"""
    gx, gy = x - GRID_ORIGIN[0], y - GRID_ORIGIN[1]
    if gx < 0 or gy < 0:
        return None
    c, r = gx // CELL, gy // CELL
    if r >= GRID_N or c >= GRID_N:
        return None
    return int(r), int(c)


def cell_center(r, c):
    """格子序号 → 该格中心的屏幕坐标（格子对齐移动后，角色位置直接取格心）。"""
    return (GRID_ORIGIN[0] + c * CELL + CELL // 2,
            GRID_ORIGIN[1] + r * CELL + CELL // 2)


def to_target(r, c):
    """主网格坐标 → 目标区坐标 (tr, tc)；不在目标区内返回 None。"""
    tr, tc = r - TARGET_OFFSET[0], c - TARGET_OFFSET[1]
    if 0 <= tr < TARGET_N and 0 <= tc < TARGET_N:
        return tr, tc
    return None


def target_rect():
    """圣坛（21×21）在屏幕上的矩形。"""
    return pygame.Rect(GRID_ORIGIN[0] + TARGET_OFFSET[1] * CELL,
                       GRID_ORIGIN[1] + TARGET_OFFSET[0] * CELL,
                       TARGET_N * CELL, TARGET_N * CELL)


def altar_center():
    r = target_rect()
    return r.centerx, r.centery

