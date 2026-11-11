# -*- coding: utf-8 -*-
"""界面绘制：所有 draw_* 都在这里，第一个参数是 Game 实例。

改界面不用翻游戏逻辑，改逻辑也不会碰画法。只读 Game 的属性，不修改任何游戏状态。

布局（逻辑画布 1360×1000）：
    0~840     世界（30×30 生成环，正中 25×25 主网格，圣坛是中间 21×21）
    840~1360  状态面板（血量 / 进度 / 脏格 / 红怪数；捡到道具后再出 8 格物品栏与 21×21 进度图）
    12~48     顶部 HUD  ·  830~900 内心独白  ·  918 键位与提示  ·  940~ 系统消息
"""

import math
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:            # 只为 IDE 补全与类型检查，运行时不执行，不会造成循环 import
    from src.game import Game

from src import sprites, story
from src.config import (
    BAG_SLOTS, CELL, CLEAR_WAVE_WIDTH, C_ACCENT, C_ALTAR, C_BG, C_BG_GRID, C_CELL_BLACK,
    C_BAG_SLOT, C_CELL_LINE, C_CELL_WHITE, C_DIM, C_ERASING, C_ITEM, C_ITEM_INK,
    C_ITEM_PAPER, C_ITEM_PAPER_DARK, C_ITEM_LEATHER_DARK, C_MISSING, C_MONSTER, C_MUST,
    C_OUTLINE, C_PLAYER, C_PURPLE,
    C_OLDMAN, C_PANEL, C_PANEL_LINE, C_PROP_TOOL, C_RING,
    C_TEXT, C_WARN,
    DIRTY, DARK_MODULE, DARK_MODULE_LEAD, DLG_BOTTOM, DLG_BOX, DLG_CPS, DLG_FONT, DLG_LINE_H,
    DLG_MIN_ROWS, DLG_PAD,
    ERASE_CAST, ERASING, GRID_N,
    GRID_ORIGIN, GRID_PX, HEALTH_LOW, HEALTH_MAX, HINT_Y, HUD_X, HUD_Y, INTRO_FALL, INTRO_SHOW,
    INTRO_TOTAL, MAP_CELL, MAP_SCROLL_H, MAP_SCROLL_W, MAP_Y, MIRAGE_ALPHA_MAX, MIRAGE_FADE, MIRAGE_RADIUS, MONO_CPS,
    MONO_FADE_IN, MONO_FADE_OUT, MONO_FONT, MONO_LINE_H,
    PANEL_H, PANEL_PAD, PANEL_W, PANEL_X, PANEL_Y,
    PLAYER_GLOW_R, PROP_DEAD_CELL, PROP_TOOL_CELL, SPAWN_ORIGIN, SPAWN_PX, STAIN_LIMIT, TARGET_N,
    TARGET_OFFSET, THREAT_Y, VALID, WINDOW_H, WINDOW_W
)
from src.grid import cell_center, cell_to_rect, target_rect

PLAY_W = PANEL_X             # 左侧世界区域的宽度
PANEL_INNER = PANEL_W - PANEL_PAD * 2


# ==== 开始页 ====

def draw_title(g: "Game"):
    s = g.screen
    s.fill(C_BG)
    for x in range(0, WINDOW_W, CELL):
        pygame.draw.line(s, C_BG_GRID, (x, 0), (x, WINDOW_H))
    for y in range(0, WINDOW_H, CELL):
        pygame.draw.line(s, C_BG_GRID, (0, y), (WINDOW_W, y))

    center_txt(g, "DATA SHIFT", (WINDOW_W // 2, 330), g.f_big, C_ACCENT)
    center_txt(g, "ACT 1", (WINDOW_W // 2, 410), g.f_mid, C_TEXT)
    if int(g.menu_t * 2.0) % 2 == 0:
        center_txt(g, "PRESS ENTER", (WINDOW_W // 2, 560), g.f_main, C_ERASING)
    center_txt(g, "[WASD] MOVE     [SHIFT] ANOMALY     [J] DARK     [K] ERASE",
               (WINDOW_W // 2, 700), g.f_main, C_TEXT)
    center_txt(g, "ESC: QUIT      F1: DEBUG", (WINDOW_W // 2, 750), g.f_small, C_DIM)


# ==== 世界 ====

def draw_world(g: "Game"):
    s = g.screen
    b = g.board
    s.fill(C_BG)

    for x in range(0, PLAY_W, CELL):
        pygame.draw.line(s, C_BG_GRID, (x, 0), (x, WINDOW_H))
    for y in range(0, WINDOW_H, CELL):
        pygame.draw.line(s, C_BG_GRID, (0, y), (PLAY_W, y))

    draw_dashed_rect(s, pygame.Rect(SPAWN_ORIGIN, (SPAWN_PX, SPAWN_PX)), color=C_RING)
    s.fill(C_CELL_WHITE, pygame.Rect(GRID_ORIGIN, (GRID_PX, GRID_PX)))

    # ---- 开场：完整码铺出 → 碎 → 只剩脚下一小片 ----
    in_intro = g.intro_t > 0
    if in_intro:
        if not g.burst_done:
            _draw_intro_code(g, s)
        elif g.hint_alpha > 0:
            _draw_ghost(g, s)                 # 只剩脚下 5×5 那一小片
    else:
        _draw_mirage(g, s)

    # 绿框：本轮必涂格。照出来才看得见
    for (r, c) in b.must:
        if b.revealed(r, c):
            pygame.draw.rect(s, C_MUST, cell_to_rect(r, c), 2)

    # 网格线
    for i in range(GRID_N + 1):
        x = GRID_ORIGIN[0] + i * CELL
        y = GRID_ORIGIN[1] + i * CELL
        pygame.draw.line(s, C_CELL_LINE, (x, GRID_ORIGIN[1]), (x, GRID_ORIGIN[1] + GRID_PX))
        pygame.draw.line(s, C_CELL_LINE, (GRID_ORIGIN[0], y), (GRID_ORIGIN[0] + GRID_PX, y))

    # 格子状态
    for r in range(GRID_N):
        srow = b.state[r]
        for c in range(GRID_N):
            st = srow[c]
            if st == VALID:
                s.fill(C_CELL_BLACK, cell_to_rect(r, c))
            elif st == DIRTY:
                s.blit(g.stain_tile, cell_to_rect(r, c).topleft)
            elif st == ERASING:
                rect = cell_to_rect(r, c)
                s.fill(C_ERASING, rect)
                k = 1.0 - b.erase_t[r][c] / ERASE_CAST
                inset = int(CELL * 0.5 * (1.0 - k))
                if inset > 0:
                    s.fill(C_CELL_WHITE, rect.inflate(-2 * inset, -2 * inset))
    for (r, c) in b.flash:
        surf = g.flash_surf_purple if b.flash_kind.get((r, c)) == "purple" else g.flash_surf
        s.blit(surf, cell_to_rect(r, c).topleft)

    # 地上的死红怪 / 用过的道具：**一直在世界上**，不要等某个相位才画出来
    _draw_props(g, s)

    # 圣坛边框：平时暗框；清屏阶段跟着光脉动
    frame = target_rect().inflate(6, 6)
    if g.state in ("CLEAR", "REWARD"):
        k = (math.cos(g.glow_t * 6.0) + 1.0) * 0.5
        pygame.draw.rect(s, mix(C_ALTAR, C_ACCENT, k), frame, 3)
    else:
        pygame.draw.rect(s, C_ALTAR, frame, 2)

    # 清屏的圆形波 / 奖励阶段的光扩散（都裁在世界区域内）
    if g.wave_r > 0 and g.state == "CLEAR":
        old = s.get_clip()
        s.set_clip(pygame.Rect(0, 0, PLAY_W, WINDOW_H))
        pygame.draw.circle(s, C_ACCENT, frame.center, int(g.wave_r), CLEAR_WAVE_WIDTH)
        s.set_clip(old)
    if g.state == "REWARD" and g.reward_phase == "spread":
        _draw_spread(g, s)

    # 道具
    for it in g.items:
        _draw_item(g, s, it)

    # 红怪（战斗单位 + 过场里的两只）
    for r in g.scene_reds:
        sprites.draw_red(s, r.pos.x, r.pos.y, r.radius, g.anim_t, r.phase,
                         look=g.player.pos if g.player else None)
    for m in g.monsters:
        look = cell_center(*m.target) if m.target is not None else (
            g.player.pos if g.player is not None else None)
        sprites.draw_red(s, m.pos.x, m.pos.y, m.radius, g.anim_t, m.phase,
                         hunting=(m.mode == "hunt"), look=look,
                         glow=g.red_glow, base=m.color,
                         dark=sprites._mix(m.color, C_CELL_BLACK, 0.52))

    # 第二幕的紫怪：同样的画法，换一套色（它不追人，只盯着线）
    for pu in g.purples:
        look = cell_center(*pu.target) if pu.target is not None else (
            g.player.pos if g.player is not None else None)
        sprites.draw_red(s, pu.pos.x, pu.pos.y, pu.radius, g.anim_t, pu.phase,
                         hunting=False, look=look, glow=g.red_glow, base=pu.color,
                         dark=sprites._mix(pu.color, C_CELL_BLACK, 0.50))

    # 老者同理：他从第一帧就站在那儿（只有走了以后才不画）
    if g.oldman is not None and not g.oldman.gone:
        _draw_oldman(g, s)

    # 开场动画期间不画玩家（角色会浮在碎码中间）
    if not in_intro:
        draw_player(g, s)

    # 碎片画在最上层
    for d in g.debris:
        rect = pygame.Rect(int(d[0]), int(d[1]), CELL, CELL)
        s.fill(C_MISSING, rect)
        pygame.draw.rect(s, C_CELL_LINE, rect, 1)

    # 威胁台词（红怪的狠话）
    if g.threat_t > 0:
        _draw_threat(g, s)


def _draw_intro_code(g, s):
    """开场前 1.5 秒：整张码用黑色铺出来（先单独亮一下暗模块）。"""
    t = INTRO_TOTAL - g.intro_t
    if t < DARK_MODULE_LEAD:
        dr, dc = DARK_MODULE
        s.fill(C_CELL_BLACK, cell_to_rect(TARGET_OFFSET[0] + dr, TARGET_OFFSET[1] + dc))
        return
    orr, occ = TARGET_OFFSET
    for tr in range(TARGET_N):
        row = g.target[tr]
        for tc in range(TARGET_N):
            if row[tc]:
                s.fill(C_CELL_BLACK, cell_to_rect(orr + tr, occ + tc))


def _draw_ghost(g, s):
    """灰码淡入：**只画脚下 5×5**（醒来时只剩这一小片）。"""
    b = g.board
    g.ghost.set_alpha(g.hint_alpha)
    orr, occ = TARGET_OFFSET
    pr, pc = g.player.cell
    for tr in range(TARGET_N):
        row = g.target[tr]
        for tc in range(TARGET_N):
            if not row[tc]:
                continue
            r, c = orr + tr, occ + tc
            if b.state[r][c] != 0:
                continue
            if max(abs(r - pr), abs(c - pc)) > MIRAGE_RADIUS:
                continue
            s.blit(g.ghost, cell_to_rect(r, c).topleft)


def _draw_mirage(g, s):
    """异象灰域：只画「照出来了、该黑、还是白」的格子，越接近 5 秒越淡。"""
    b = g.board
    for r in range(GRID_N):
        for c in range(GRID_N):
            if not b.revealed(r, c):
                continue
            k = b.reveal[r][c] / MIRAGE_FADE
            g.mirage_tile.set_alpha(int(MIRAGE_ALPHA_MAX * k))
            s.blit(g.mirage_tile, cell_to_rect(r, c).topleft)


def _draw_props(g, s):
    """圣坛外的两件背景物：一只死掉的红怪、几件用过的道具。"""
    sprites.draw_dead_red(s, *cell_center(*PROP_DEAD_CELL))

    # 用过的道具：一块歪掉的板 + 一根探针，都蒙着灰
    x, y = cell_center(*PROP_TOOL_CELL)
    plate = pygame.Rect(x - 12, y - 7, 10, 15)
    pygame.draw.rect(s, C_OUTLINE, plate.inflate(2, 2), border_radius=3)
    pygame.draw.rect(s, C_PROP_TOOL, plate, border_radius=2)
    s.fill(C_OUTLINE, pygame.Rect(plate.x + 2, plate.y + 3, 6, 1))
    s.fill(C_OUTLINE, pygame.Rect(plate.x + 2, plate.y + 6, 4, 1))
    pygame.draw.line(s, C_OUTLINE, (x + 3, y + 6), (x + 11, y - 4), 4)
    pygame.draw.line(s, C_PROP_TOOL, (x + 3, y + 6), (x + 11, y - 4), 2)
    pygame.draw.circle(s, C_OUTLINE, (x + 11, y - 5), 3)


def _draw_oldman(g, s):
    sprites.draw_oldman(s, g.oldman, g.anim_t)


def _draw_item(g, s, it):
    rise = int((1.0 - it.t) * 22)
    sprites.draw_item(s, it.kind, it.pos.x, it.pos.y, g.anim_t, rise)
    # 小标签压在道具上方：图标已经认得出，但第一幕需要玩家一眼知道「这是 BAG / MAP」
    label = "BAG" if it.kind == "bag" else "MAP"
    img = g.f_tiny.render(label, True, C_ITEM)
    s.blit(img, img.get_rect(center=(int(it.pos.x), int(it.pos.y) + rise - 23)))


def _draw_threat(g, s):
    """红怪的狠话：屏幕中央偏上，全大写、猩红。"""
    img = g.f_mid.render(story.THREAT, True, C_MONSTER)
    rect = img.get_rect(center=(PLAY_W // 2, THREAT_Y)).inflate(56, 24)
    plate = pygame.Surface(rect.size, pygame.SRCALPHA)
    plate.fill((0, 0, 0, 150))
    s.blit(plate, rect.topleft)
    s.blit(img, img.get_rect(center=rect.center))


def _draw_spread(g, s):
    """奖励收尾：圣坛的光扩散到整个世界。"""
    old = s.get_clip()
    s.set_clip(pygame.Rect(0, 0, PLAY_W, WINDOW_H))
    cx, cy = target_rect().center
    r = int(g.spread_r)
    g.spread_surf.fill((0, 0, 0, 0))
    pygame.draw.circle(g.spread_surf, (*C_ACCENT, 54), (cx, cy), r)
    pygame.draw.circle(g.spread_surf, (*C_ACCENT, 220), (cx, cy), r, 4)
    s.blit(g.spread_surf, (0, 0))
    s.set_clip(old)


def draw_player(g: "Game", s):
    p = g.player
    moving = g.input.dir4() is not None
    sprites.draw_sequencer(s, p.pos.x, p.pos.y, p.facing, g.anim_t, moving,
                           glow=g.glow, has_bag=g.has_bag, holding_map=g.map_open)


def draw_dashed_rect(s, rect, dash=12, color=C_CELL_LINE):
    for x in range(rect.left, rect.right, dash * 2):
        x2 = min(x + dash, rect.right)
        pygame.draw.line(s, color, (x, rect.top), (x2, rect.top))
        pygame.draw.line(s, color, (x, rect.bottom), (x2, rect.bottom))
    for y in range(rect.top, rect.bottom, dash * 2):
        y2 = min(y + dash, rect.bottom)
        pygame.draw.line(s, color, (rect.left, y), (rect.left, y2))
        pygame.draw.line(s, color, (rect.right, y), (rect.right, y2))

# ==== HUD / 右侧面板 ====


def txt(g: "Game", text, pos, font, color, right=False):
    img = font.render(text, True, color)
    g.screen.blit(img, img.get_rect(topright=pos) if right else img.get_rect(topleft=pos))


def center_txt(g: "Game", text, pos, font, color):
    img = font.render(text, True, color)
    g.screen.blit(img, img.get_rect(center=pos))


def mix(a, b, k):
    return (int(a[0] + (b[0] - a[0]) * k),
            int(a[1] + (b[1] - a[1]) * k),
            int(a[2] + (b[2] - a[2]) * k))


def draw_bar(g: "Game", rect, frac, color, back=(19, 14, 11)):
    s = g.screen
    s.fill(back, rect)
    w = int(rect.w * max(0.0, min(1.0, frac)))
    if w > 0:
        s.fill(color, pygame.Rect(rect.x, rect.y, w, rect.h))
    pygame.draw.rect(s, C_PANEL_LINE, rect, 1)


def draw_hud(g: "Game"):
    s = g.screen
    b = g.board

    # ---- 顶部 ----
    txt(g, "ACT %d" % g.act, (HUD_X, HUD_Y + 2), g.f_main, C_TEXT)
    if g.state in ("BATTLE", "CLEAR", "REWARD", "DEAD"):
        txt(g, "TIME %02d:%02d" % (int(g.elapsed) // 60, int(g.elapsed) % 60),
            (PLAY_W - 24, HUD_Y + 6), g.f_small, C_DIM, right=True)
    txt(g, "[ESC] TITLE", (WINDOW_W - 24, HUD_Y + 6), g.f_small, C_DIM, right=True)

    # ---- 右侧面板 ----
    panel = pygame.Rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
    s.fill(C_PANEL, panel)
    pygame.draw.rect(s, C_PANEL_LINE, panel, 1)
    x = PANEL_X + PANEL_PAD

    hp = g.health
    hp_col = C_MONSTER if hp <= HEALTH_LOW else C_ACCENT
    txt(g, "HEALTH", (x, 96), g.f_small, C_DIM)
    txt(g, "%d%%" % hp, (x + PANEL_INNER, 92), g.f_panel, hp_col, right=True)
    draw_bar(g, pygame.Rect(x, 126, PANEL_INNER, 24), hp / float(HEALTH_MAX), hp_col)

    done = b.progress()
    total = len(b.must) or 1
    txt(g, "DARK", (x, 196), g.f_small, C_DIM)
    txt(g, "%d / %d" % (done, total), (x + PANEL_INNER, 192), g.f_panel, C_TEXT, right=True)
    draw_bar(g, pygame.Rect(x, 226, PANEL_INNER, 18), done / float(total), C_TEXT)

    # 脏格：本幕**累计**涂错格数，擦掉不减；超过额度就转红（那时每次扣血）
    stains = b.stains
    st_col = C_MONSTER if stains > STAIN_LIMIT else (C_WARN if stains > STAIN_LIMIT * 0.7 else C_TEXT)
    txt(g, "STAINS", (x, 280), g.f_small, C_DIM)
    txt(g, "%d / %d" % (stains, STAIN_LIMIT), (x + PANEL_INNER, 276), g.f_panel, st_col, right=True)

    txt(g, "RED ON FIELD", (x, 340), g.f_small, C_DIM)
    txt(g, str(len(g.monsters)), (x + PANEL_INNER, 336), g.f_panel,
        C_MONSTER if g.monsters else C_TEXT, right=True)

    if g.act >= 2:                                   # 第二幕才有紫怪
        txt(g, "PURPLE ON FIELD", (x, 372), g.f_small, C_DIM)
        txt(g, str(len(g.purples)), (x + PANEL_INNER, 368), g.f_panel,
            C_PURPLE if g.purples else C_TEXT, right=True)

    pygame.draw.line(s, C_PANEL_LINE, (x, 396), (x + PANEL_INNER, 396))

    if g.has_bag:
        _draw_bag(g, s, x, 412)
    if g.has_map:
        _draw_map(g, s, x, MAP_Y)

    # ---- 底部：键位 + 提示 + 系统消息 ----
    if g.state == "DIALOG":
        pass                                    # 对话框自带 ENTER 提示，底部别再摆键位表
    elif g.state == "TUTORIAL" and g.prompt_text:
        # 教程阶段那句提示本身就是键位表，不用再摆一遍
        center_txt(g, g.prompt_text, (PLAY_W // 2, HINT_Y + 10), g.f_prompt, C_ACCENT)
    else:
        # 常驻键位表（C6：关键键别只弹一次，错过就卡住）
        txt(g, "[WASD] MOVE   [SHIFT] ANOMALY   [J] DARK   [K] ERASE   [T] CALL",
            (HUD_X, HINT_Y), g.f_small, C_ERASING)
        if g.prompt_text:
            txt(g, g.prompt_text, (PLAY_W - 16, HINT_Y - 6), g.f_prompt, C_ACCENT, right=True)

    if g.mono_t > 0 and g.mono_text:
        _draw_monologue(g, s)

    if g.hint_t > 0 and g.hint_text:
        _draw_hint(g, s)

    if g.debug:
        txt(g, "FPS %d  CELL %d,%d  QR %s  STATE %s  WAVE %.0f  LAST SC %d" % (
            int(round(1.0 / max(g._last_dt, 1e-4))), g.player.cell[0], g.player.cell[1],
            g.qr_content, g.state, g.wave_r, g.last_sc),
            (HUD_X, HUD_Y + 30), g.f_small, C_DIM)


_BAG_ICON_CACHE = {}


def _bag_icon(kind):
    """物品栏格子里的图标：预生成 2 倍（最近邻，保持像素感），别每帧现画。"""
    surf = _BAG_ICON_CACHE.get(kind)
    if surf is None:
        tmp = pygame.Surface((48, 48), pygame.SRCALPHA)
        sprites.draw_item(tmp, kind, 24, 24, glow=False)
        surf = pygame.transform.scale(tmp, (96, 96))
        _BAG_ICON_CACHE[kind] = surf
    return surf


def _draw_bag(g, s, x, y):
    txt(g, "BAG", (x, y), g.f_small, C_DIM)
    cols, rows = 4, 2
    gap = 12
    w = (PANEL_INNER - gap * (cols - 1)) // cols
    h = 62
    # 背包是「容器」，它本身不占格子；格子里放的是包里的东西
    inside = []
    if g.has_map:
        inside.append("map")
    for i in range(min(BAG_SLOTS, cols * rows)):
        r, c = divmod(i, cols)
        rect = pygame.Rect(x + c * (w + gap), y + 26 + r * (h + 10), w, h)
        s.fill(C_BAG_SLOT, rect)
        pygame.draw.rect(s, C_PANEL_LINE, rect, 1, border_radius=4)
        if i < len(inside):                       # 2 倍图标（预生成），格子才不显得空
            icon = _bag_icon(inside[i])
            s.blit(icon, icon.get_rect(center=rect.center))


def _draw_scroll_closed(g, s, cx, cy):
    """卷起来的地图：横躺的一卷纸，中间一道捆带，两端是卷头。"""
    w, h = MAP_SCROLL_W, MAP_SCROLL_H
    x, y = cx - w // 2, cy - h // 2
    center_txt(g, "MAP", (cx, y - 20), g.f_small, C_DIM)
    sprites.shadow(s, cx, y + h + 4, w - 10, 9, 70)

    body = pygame.Rect(x, y, w, h)
    pygame.draw.rect(s, C_OUTLINE, body.inflate(2, 2), border_radius=9)
    pygame.draw.rect(s, C_ITEM_PAPER_DARK, body, border_radius=8)
    pygame.draw.rect(s, C_ITEM_PAPER, body.inflate(-6, -8), border_radius=6)
    for dy in (-5, 4):                              # 卷了几层的纹路
        pygame.draw.line(s, C_ITEM_INK, (x + 14, cy + dy), (x + w - 14, cy + dy), 1)

    for ex in (x - 4, x + w - 8):                   # 两端卷头
        cap = pygame.Rect(ex, y - 3, 12, h + 6)
        pygame.draw.rect(s, C_ITEM_PAPER_DARK, cap, border_radius=5)
        pygame.draw.rect(s, C_OUTLINE, cap, 1, border_radius=5)

    tie = pygame.Rect(cx - 6, y - 4, 12, h + 8)     # 中间那道捆带
    pygame.draw.rect(s, C_ITEM_LEATHER_DARK, tie, border_radius=3)
    pygame.draw.rect(s, C_OUTLINE, tie, 1, border_radius=3)
    s.fill(C_ITEM, pygame.Rect(cx - 2, cy - 2, 4, 4))

    center_txt(g, "M", (cx, y + h + 18), g.f_small, C_DIM)


def _draw_roll_bar(s, left, y, w, above=True):
    """展开时上下那两根卷轴轴。**画在纸的外侧**，不然会盖掉第一行 / 最后一行的格子。"""
    bar = pygame.Rect(left - 10, y - 13 if above else y, w + 20, 13)
    pygame.draw.rect(s, C_ITEM_PAPER_DARK, bar, border_radius=6)
    pygame.draw.rect(s, C_OUTLINE, bar, 1, border_radius=6)
    for ex in (bar.left - 2, bar.right - 10):
        cap = pygame.Rect(ex, bar.top - 3, 12, bar.height + 6)
        pygame.draw.rect(s, C_ITEM_LEATHER_DARK, cap, border_radius=4)
        pygame.draw.rect(s, C_OUTLINE, cap, 1, border_radius=4)


_MAP_TILE_CACHE = {}


def _map_tile():
    """地图像素格：一块纯墨。预生成一张，别每帧现画（铺开时最多 441 格）。"""
    surf = _MAP_TILE_CACHE.get("ink")
    if surf is None:
        surf = pygame.Surface((MAP_CELL, MAP_CELL))
        surf.fill(C_CELL_BLACK)
        _MAP_TILE_CACHE["ink"] = surf
    return surf


def map_rect(open_t=1.0):
    """地图铺开后纸面的矩形（`open_t` = 铺开进度）。

    单独拎出来是因为**验收脚本要按格子逐像素取样**：手算坐标差一格，
    断言就会取到隔壁格子上，测过了也是假过。
    """
    full = TARGET_N * MAP_CELL
    cx = PANEL_X + PANEL_PAD + PANEL_INNER // 2
    cy = MAP_Y + 30 + full // 2
    h = max(8, int(round(full * open_t)))
    return pygame.Rect(cx - full // 2, cy - h // 2, full, h)


def _draw_map(g, s, x, y):
    """右下角的地图：卷着是一个卷轴，按 M 铺开成「上一幕收尾时圣坛的样子」。

    画的是 `g.map_cells`（每一幕收尾那一刻拍下来的定格照），**不读棋盘**：
      · 这一幕涂的格子，地图不会立刻变黑；
      · 紫怪清掉的整行，地图上的墨也不会跟着掉。
    只有一幕真正收尾（清屏波扫完、脏格抹掉）才重新拍一张 —— 见 `Game.capture_map()`。
    也正因为拍的是「已经发生的事」，它永远不会剧透「下一步该涂哪」。
    """
    if not g.has_map:
        return
    full = TARGET_N * MAP_CELL
    cx = x + PANEL_INNER // 2
    top = y + 30
    cy = top + full // 2
    t = g.map_t

    if t <= 0.01:                                   # 完全卷起来
        _draw_scroll_closed(g, s, cx, cy)
        return

    box = map_rect(t)
    s.fill(C_ITEM_PAPER, box)

    old = s.get_clip()
    s.set_clip(box)
    ink = _map_tile()
    for (tr, tc) in g.map_cells:                    # 定格照：本幕怎么涂都不会动它
        s.blit(ink, (box.left + tc * MAP_CELL, box.top + tr * MAP_CELL))
    # 自己在哪（这个是实时的 —— 位置又不是「幕账」）
    pr, pc = g.player.cell
    ptr, ptc = pr - TARGET_OFFSET[0], pc - TARGET_OFFSET[1]
    if 0 <= ptr < TARGET_N and 0 <= ptc < TARGET_N:
        px = box.left + ptc * MAP_CELL + MAP_CELL // 2
        py = box.top + ptr * MAP_CELL + MAP_CELL // 2
        pygame.draw.circle(s, C_OUTLINE, (px, py), 5)
        pygame.draw.circle(s, C_PLAYER, (px, py), 3)
    s.set_clip(old)

    # 这张图是哪一幕收尾时拍的（不然玩家会以为地图坏了：怎么涂都不动）
    if g.map_act:
        txt(g, "AS OF ACT %d" % g.map_act, (box.left, box.top - 36), g.f_small, C_DIM)

    # 上下两根卷轴跟着展开的边缘走 —— 读起来才是「纸从轴里滚出来」，
    # 而不是「一张图被裁掉了下半截」
    _draw_roll_bar(s, box.left, box.top, full, above=True)
    _draw_roll_bar(s, box.left, box.bottom, full, above=False)


def _reveal(lines, n):
    """打字机：按字符数截断折好的行，返回 (可见行, 是否还在打)。"""
    out = []
    for ln in lines:
        if n <= 0:
            break
        out.append(ln[:n])
        n -= len(ln)
    return out, n > 0


def _wrap_paragraphs(font, text, max_w):
    """按 \\n 分段折行：`If I can.` 这种要单独成行的得保住。"""
    out = []
    for para in text.split("\n"):
        out.extend(wrap_text(font, para, max_w))
    return out


_MONO_BUF = {}


def _mono_buf(size):
    """心声淡入淡出用的离屏纸（按尺寸复用，别每帧新建 Surface）。"""
    surf = _MONO_BUF.get(size)
    if surf is None:
        surf = pygame.Surface(size, pygame.SRCALPHA)
        _MONO_BUF[size] = surf
    else:
        surf.fill((0, 0, 0, 0))
    return surf


def _speech_box(s, g, box, name, who, solid_tab=True):
    """对话与心声共用的骨架：实心底 + 一像素边 + 四角括号 + 骑在上沿的名牌。

    `solid_tab=False` 时名牌改成空心描边（字用强调色）—— 心声用它：
    同一个框、同一个名牌位置，但一眼看得出「这是心里说的，不是开口说的」。
    """
    s.fill((20, 14, 11), box)                 # 实心：半透明会把底下的白格透出来，显得脏
    pygame.draw.rect(s, C_PANEL_LINE, box, 1)
    _corner_brackets(s, box, 20, who)
    img = g.f_dlg_name.render(name, True, who if not solid_tab else (8, 10, 14))
    tab = pygame.Rect(box.x + DLG_PAD, box.y - 17, img.get_width() + 32, 34)
    if solid_tab:
        s.fill(who, tab)
    else:
        s.fill((20, 14, 11), tab)
        pygame.draw.rect(s, who, tab, 1)
    s.blit(img, img.get_rect(center=tab.center))


def mono_lines(g):
    """折好的心声行（字号比对话大一号，折行宽度按对话框内宽算）。"""
    return _wrap_paragraphs(g.f_mono, g.mono_text, DLG_BOX[2] - DLG_PAD * 2)


def mono_box(g):
    """心声明框的矩形：和对话框同宽同底边，高度按这句的行数缩（最少 2 行，最多 3 行）。

    测试也用它取样 —— 手写坐标迟早和渲染错开一格。
    """
    rows = max(DLG_MIN_ROWS, min(3, len(mono_lines(g))))
    h = min(DLG_BOX[3], rows * MONO_LINE_H + 64)
    return pygame.Rect(DLG_BOX[0], DLG_BOTTOM - h, DLG_BOX[2], h)


def _mono_paint(g, s, box, vis, typing):
    """把「心声框」画到 s 上（box 可以是屏幕坐标，也可以是离屏纸的本地坐标）。"""
    _speech_box(s, g, box, story.SEQUENCER, C_ACCENT, solid_tab=False)
    top = box.y + 44
    for i, ln in enumerate(vis):
        s.blit(g.f_mono.render(ln, True, C_TEXT), (box.x + DLG_PAD, top + i * MONO_LINE_H))
    if typing and vis:                        # 打字光标（和对话同一个位置算法）
        last = vis[-1]
        cx = box.x + DLG_PAD + g.f_mono.size(last)[0] + 4
        cy = top + (len(vis) - 1) * MONO_LINE_H + 8
        s.fill(C_ACCENT, pygame.Rect(cx, cy, 10, MONO_FONT - 12))


def _draw_monologue(g, s):
    """心声：用和老者对话**同一套框**（实心底、四角括号、骑在上沿的名牌、打字机），
    只有三处不同 —— 名牌空心描边、没有 ENTER 与「继续」箭头、进出淡入淡出。

    这三处不同是故意的：心声是自动走的（不需要玩家按回车），
    而且必须一眼和「开口说的话」分开，否则玩家会以为角色在自言自语。
    """
    if g.mono_t <= 0 or not g.mono_text:
        return
    lines = mono_lines(g)
    total = sum(len(ln) for ln in lines)
    shown = min(total, int(max(0.0, g.mono_total - g.mono_t) * MONO_CPS))
    vis, typing = _reveal(lines, shown)
    box = mono_box(g)

    # 淡入淡出：只有边缘那几百毫秒要离屏纸，中间大段时间直接画到屏幕上
    alpha = 255
    if g.mono_total - g.mono_t < MONO_FADE_IN:
        alpha = int(255 * (g.mono_total - g.mono_t) / MONO_FADE_IN)
    if g.mono_t < MONO_FADE_OUT:
        alpha = int(255 * g.mono_t / MONO_FADE_OUT)
    alpha = max(0, min(255, alpha))
    if alpha >= 255:
        _mono_paint(g, s, box, vis, typing)
        return
    buf = _mono_buf(box.size)
    _mono_paint(g, buf, pygame.Rect(0, 0, box.w, box.h), vis, typing)
    buf.set_alpha(alpha)
    s.blit(buf, box.topleft)


def _draw_hint(g, s):
    lines = g.hint_text.split("\n")
    imgs = [g.f_main.render(ln, True, C_WARN) for ln in lines]
    bw = max(im.get_width() for im in imgs) + 48
    bh = 16 + 30 * len(imgs)
    plate = pygame.Rect(0, 0, bw, bh)
    plate.center = (PLAY_W // 2, HINT_Y + 56)
    s.fill(C_BG, plate)
    pygame.draw.rect(s, C_WARN, plate, 1)
    for i, im in enumerate(imgs):
        s.blit(im, im.get_rect(center=(plate.centerx, plate.top + 15 + 30 * i)))

# ==== 对话框 ====

def wrap_text(font, text, max_w):
    """按空格断行。单词本身超宽也不硬切，宁可溢出一点。"""
    lines, cur = [], ""
    for word in text.split(" "):
        t = (cur + " " + word).strip()
        if cur and font.size(t)[0] > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def dialog_lines(g):
    """当前这句台词折行之后的结果（测试也用它，保证「放得下」是算出来的）。"""
    if not g.dlg_lines:
        return [], ""
    speaker, text = g.dlg_lines[g.dlg_i]
    x, y, w, h = DLG_BOX
    return _wrap_paragraphs(g.f_dlg, text, w - DLG_PAD * 2), speaker


def dialog_char_total(g):
    lines, _ = dialog_lines(g)
    return sum(len(ln) for ln in lines)


def dlg_box_lines():
    """对话框里能吃几行字（测试用它断言「都放得下」）。"""
    return (DLG_BOX[3] - 64) // DLG_LINE_H


def _corner_brackets(s, rect, size, color, width=2):
    """四角括号：比一整圈边框轻，像被「标出来」而不是「装起来」。"""
    x, y, w, h = rect
    for cx, cy, dx, dy in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        pygame.draw.line(s, color, (cx, cy), (cx + dx * size, cy), width)
        pygame.draw.line(s, color, (cx, cy), (cx, cy + dy * size), width)


def draw_dialog(g):
    if not g.dlg_lines or g.dlg_phase == "run":
        return
    s = g.screen
    lines, speaker = dialog_lines(g)
    x, _, w, hmax = DLG_BOX
    # 框底不动，高度跟着这一句的行数缩：短句不留一大片空，长句最多 4 行
    rows = max(DLG_MIN_ROWS, min(dlg_box_lines(), len(lines)))
    h = min(hmax, rows * DLG_LINE_H + 64)
    box = pygame.Rect(x, DLG_BOTTOM - h, w, h)
    who = C_OLDMAN if speaker == story.OLD_MAN else C_ACCENT

    _speech_box(s, g, box, speaker, who)    # 和心声共用的那套框（这里实心名牌）

    # 正文：按**整句**的行数做垂直居中，打字过程中版面不跳
    total = sum(len(ln) for ln in lines)
    shown = min(total, int(g.dlg_t * DLG_CPS))
    vis, typing = _reveal(lines, shown)
    top = box.y + 44
    for i, ln in enumerate(vis):
        s.blit(g.f_dlg.render(ln, True, C_TEXT), (box.x + DLG_PAD, top + i * DLG_LINE_H))
    if typing and vis:
        last = vis[-1]
        cx = box.x + DLG_PAD + g.f_dlg.size(last)[0] + 4
        cy = top + (len(vis) - 1) * DLG_LINE_H + 8
        s.fill(who, pygame.Rect(cx, cy, 10, DLG_FONT - 10))
    elif int(g.dlg_t * 3) % 2 == 0:
        # 打完了：右下角闪一个「继续」
        ax, ay = box.right - 52, box.bottom - 34
        pygame.draw.polygon(s, who, [(ax, ay), (ax + 16, ay), (ax + 8, ay + 12)])

    hint = g.f_small.render("ENTER", True, C_DIM)
    s.blit(hint, hint.get_rect(bottomleft=(box.x + DLG_PAD, box.bottom - 18)))


# ==== 覆盖层 ====

def draw_dead(g: "Game"):
    s = g.screen
    veil = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    veil.fill((0, 0, 0, 200))
    s.blit(veil, (0, 0))
    center_txt(g, "SEQUENCER DOWN", (WINDOW_W // 2, 430), g.f_mid, C_MONSTER)
    center_txt(g, "THE ALTAR WILL TAKE YOU BACK", (WINDOW_W // 2, 500), g.f_main, C_TEXT)
    if int(g.menu_t * 2.0) % 2 == 0:
        center_txt(g, "CLICK OR PRESS ENTER", (WINDOW_W // 2, 580), g.f_main, C_ERASING)


def draw_end(g: "Game"):
    s = g.screen
    veil = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    veil.fill((0, 0, 0, 216))
    s.blit(veil, (0, 0))
    center_txt(g, g.banner_text, (PLAY_W // 2, WINDOW_H // 2 - 30), g.f_big, C_TEXT)
    if int(g.menu_t * 2.0) % 2 == 0:
        center_txt(g, "PRESS ENTER", (PLAY_W // 2, WINDOW_H // 2 + 90), g.f_main, C_ERASING)


def make_stain_tile():
    """脏黑的样子：黑底 + 白色斜条。必须和「纯黑的有效黑域」一眼可分。"""
    surf = pygame.Surface((CELL, CELL))
    surf.fill(C_CELL_BLACK)
    for i in range(-CELL, CELL * 2, 10):
        pygame.draw.line(surf, (226, 226, 232), (i, 0), (i + CELL, CELL), 4)
    return surf


# ==== 旧五关版界面（新版不进入这些状态，留着备查）====

def draw_thumb(g: "Game", x, y, is_target):
    s = g.screen
    orr, occ = TARGET_OFFSET
    for tr in range(TARGET_N):
        for tc in range(TARGET_N):
            want = g.target[tr][tc]
            if is_target:
                col = C_CELL_BLACK if want else C_CELL_WHITE
            else:
                got = g.board.state[orr + tr][occ + tc] == VALID
                if want:
                    col = C_ACCENT if got else C_MISSING
                else:
                    col = C_MONSTER if got else C_CELL_WHITE
            s.fill(col, (x + tc * 10, y + tr * 10, 10, 10))
    pygame.draw.rect(s, C_CELL_LINE, pygame.Rect(x, y, 210, 210), 1)


def draw_result(g: "Game"):
    """旧五关版的结算页。新版不再进入 RESULT，留着备查。"""
    s = g.screen
    s.fill(C_BG)
    r = g.result or {}
    mid_x = WINDOW_W // 2
    line = story.level(g.level)["end"] if r.get("won") else story.FAIL
    for i, ln in enumerate(wrap_text(g.f_mid, line, 860)):
        center_txt(g, ln, (mid_x, 128 + i * 58), g.f_mid, C_ACCENT if r.get("won") else C_MONSTER)
    draw_thumb(g, 120, 250, True)
    draw_thumb(g, WINDOW_W - 330, 250, False)
    center_txt(g, "ESC: TITLE", (mid_x, 760), g.f_main, C_TEXT)
