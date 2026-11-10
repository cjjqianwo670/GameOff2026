# -*- coding: utf-8 -*-
"""界面绘制：所有 draw_* 都在这里，第一个参数是 Game 实例。

改界面不用翻游戏逻辑，改逻辑也不会碰画法。
只读 Game 的属性，不修改任何游戏状态。

布局（逻辑画布 1360×1000）：
    0~840    世界（30×30 生成环，正中 25×25 主网格）
    840~1360 状态面板（血条 / 进度 / 脏格，Phase B 再加 8 格物品栏与 21×21 进度图）
    12~48    顶部 HUD    ·    906~    底部操作提示 / 系统消息
"""

from typing import TYPE_CHECKING

import math

import pygame

if TYPE_CHECKING:            # 只为 IDE 补全与类型检查，运行时不执行，不会造成循环 import
    from src.game import Game

from src import story
from src.config import (
    CELL, C_ACCENT, C_ALTAR, C_BG, C_BG_GRID, C_CELL_BLACK, C_CELL_LINE, C_CELL_WHITE,
    C_DIM, C_ERASING, C_MISSING, C_MONSTER, C_MUST, C_PANEL, C_PANEL_LINE, C_PLAYER, C_TEXT,
    C_WARN, DIRTY, ERASE_CAST, ERASING, GRID_N, GRID_ORIGIN, GRID_PX, HEALTH_LOW, HEALTH_MAX,
    HINT_Y, HUD_X, HUD_Y, MIRAGE_ALPHA_MAX, MIRAGE_FADE, PANEL_H, PANEL_PAD, PANEL_W, PANEL_X,
    PANEL_Y, PLAYER_BODY_H, PLAYER_BODY_W, PLAYER_GLOW_R, SPAWN_ORIGIN, SPAWN_PX, STAIN_LIMIT,
    TARGET_OFFSET, VALID, WINDOW_H, WINDOW_W, CLEAR_WAVE_WIDTH
)
from src.grid import cell_to_rect, target_rect

PLAY_W = PANEL_X             # 左侧世界区域的宽度


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


def draw_world(g: "Game"):
    s = g.screen
    b = g.board
    s.fill(C_BG)

    # 废墟暗格：只铺世界区域，右侧面板自己会盖住
    for x in range(0, PLAY_W, CELL):
        pygame.draw.line(s, C_BG_GRID, (x, 0), (x, WINDOW_H))
    for y in range(0, WINDOW_H, CELL):
        pygame.draw.line(s, C_BG_GRID, (0, y), (PLAY_W, y))

    # 生成环虚线框：提示红怪从这条线外来
    draw_dashed_rect(s, pygame.Rect(SPAWN_ORIGIN, (SPAWN_PX, SPAWN_PX)))

    # 白底一次铺满整个 25×25（不逐格 fill）
    s.fill(C_CELL_WHITE, pygame.Rect(GRID_ORIGIN, (GRID_PX, GRID_PX)))

    # 异象灰域：只画「照出来了、该黑、还是白」的格子，越接近 5 秒越淡
    for r in range(GRID_N):
        for c in range(GRID_N):
            if not b.revealed(r, c):
                continue
            k = b.reveal[r][c] / MIRAGE_FADE
            g.mirage_tile.set_alpha(int(MIRAGE_ALPHA_MAX * k))
            s.blit(g.mirage_tile, cell_to_rect(r, c).topleft)

    # 绿框：本轮必涂格。照出来才看得见 —— 没照过的格子你根本不知道要涂
    for (r, c) in b.must:
        if b.revealed(r, c):
            pygame.draw.rect(s, C_MUST, cell_to_rect(r, c), 2)

    # 网格线：整片画线比每格描边便宜，且不会被提示块吃掉
    for i in range(GRID_N + 1):
        x = GRID_ORIGIN[0] + i * CELL
        y = GRID_ORIGIN[1] + i * CELL
        pygame.draw.line(s, C_CELL_LINE, (x, GRID_ORIGIN[1]), (x, GRID_ORIGIN[1] + GRID_PX))
        pygame.draw.line(s, C_CELL_LINE, (GRID_ORIGIN[0], y), (GRID_ORIGIN[0] + GRID_PX, y))

    # 格子状态：有效黑域 / 脏黑（黑白相间）/ 抹除中
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
        s.blit(g.flash_surf, cell_to_rect(r, c).topleft)

    # 圣坛边框：平时是暗框；清屏阶段跟着光脉动
    frame = target_rect().inflate(6, 6)
    if g.state == "CLEAR":
        k = (math.cos(g.glow_t * 6.0) + 1.0) * 0.5      # 0~1 往返
        col = mix(C_ALTAR, C_ACCENT, k)
        pygame.draw.rect(s, col, frame, 3)
    else:
        pygame.draw.rect(s, C_ALTAR, frame, 2)

    # 清屏的圆形波：一个半径随时间增大的圆环描边（不许做成粒子），裁在世界区域内
    if g.state == "CLEAR" and g.clear_phase in ("wave", "hold") and g.wave_r > 0:
        old = s.get_clip()
        s.set_clip(pygame.Rect(0, 0, PLAY_W, WINDOW_H))
        cx, cy = frame.center
        pygame.draw.circle(s, C_ACCENT, (cx, cy), int(g.wave_r), CLEAR_WAVE_WIDTH)
        s.set_clip(old)

    # 红怪就是一个圆；玩家必须画在它之后，否则怪物路过会把玩家盖住
    for m in g.monsters:
        mx, my = int(m.pos.x), int(m.pos.y)
        pygame.draw.circle(s, m.color, (mx, my), m.radius)
        pygame.draw.circle(s, C_CELL_BLACK, (mx, my), m.radius, 1)

    draw_player(g, s)


def draw_player(g: "Game", s):
    p = g.player
    px, py = int(p.pos.x), int(p.pos.y)
    s.blit(g.glow, (px - PLAYER_GLOW_R, py - PLAYER_GLOW_R))
    body = pygame.Rect(px - PLAYER_BODY_W // 2, py - PLAYER_BODY_H // 2,
                       PLAYER_BODY_W, PLAYER_BODY_H)
    pygame.draw.rect(s, C_PLAYER, body, border_radius=5)
    ex, ey = px - 2, py - 2
    if p.facing == 0:
        ey = body.top + 4
    elif p.facing == 1:
        ey = body.bottom - 8
    elif p.facing == 2:
        ex = body.left + 3
    else:
        ex = body.right - 7
    s.fill(C_CELL_BLACK, pygame.Rect(ex, ey, 4, 4))


def draw_dashed_rect(s, rect, dash=12, color=C_CELL_LINE):
    for x in range(rect.left, rect.right, dash * 2):
        x2 = min(x + dash, rect.right)
        pygame.draw.line(s, color, (x, rect.top), (x2, rect.top))
        pygame.draw.line(s, color, (x, rect.bottom), (x2, rect.bottom))
    for y in range(rect.top, rect.bottom, dash * 2):
        y2 = min(y + dash, rect.bottom)
        pygame.draw.line(s, color, (rect.left, y), (rect.left, y2))
        pygame.draw.line(s, color, (rect.right, y), (rect.right, y2))

# ---------- HUD 与右侧面板 ----------


def txt(g: "Game", text, pos, font, color, right=False):
    """right=True 时 pos 是右上角，用来把文字贴住右边距。"""
    img = font.render(text, True, color)
    g.screen.blit(img, img.get_rect(topright=pos) if right else img.get_rect(topleft=pos))


def center_txt(g: "Game", text, pos, font, color):
    img = font.render(text, True, color)
    g.screen.blit(img, img.get_rect(center=pos))


def mix(a, b, k):
    return (int(a[0] + (b[0] - a[0]) * k),
            int(a[1] + (b[1] - a[1]) * k),
            int(a[2] + (b[2] - a[2]) * k))


def draw_bar(g: "Game", rect, frac, color, back=(9, 12, 17)):
    s = g.screen
    s.fill(back, rect)
    w = int(rect.w * max(0.0, min(1.0, frac)))
    if w > 0:
        s.fill(color, pygame.Rect(rect.x, rect.y, w, rect.h))
    pygame.draw.rect(s, C_PANEL_LINE, rect, 1)


def draw_hud(g: "Game"):
    s = g.screen
    b = g.board

    # ---- 顶部一行 ----
    txt(g, "ACT 1", (HUD_X, HUD_Y + 2), g.f_main, C_TEXT)
    txt(g, "TIME %02d:%02d" % (int(g.elapsed) // 60, int(g.elapsed) % 60),
        (PLAY_W - 24, HUD_Y + 6), g.f_small, C_DIM, right=True)
    txt(g, "[ESC] TITLE", (WINDOW_W - 24, HUD_Y + 6), g.f_small, C_DIM, right=True)

    # ---- 右侧状态面板 ----
    panel = pygame.Rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
    s.fill(C_PANEL, panel)
    pygame.draw.rect(s, C_PANEL_LINE, panel, 1)
    x = PANEL_X + PANEL_PAD
    w = PANEL_W - PANEL_PAD * 2

    # 血量
    hp = g.health
    hp_col = C_MONSTER if hp <= HEALTH_LOW else C_ACCENT
    txt(g, "HEALTH", (x, 96), g.f_small, C_DIM)
    txt(g, "%d%%" % hp, (x + w, 92), g.f_panel, hp_col, right=True)
    draw_bar(g, pygame.Rect(x, 126, w, 24), hp / float(HEALTH_MAX), hp_col)

    # 圣坛复原进度
    done = b.progress()
    total = len(b.must) or 1
    txt(g, "DARK", (x, 196), g.f_small, C_DIM)
    txt(g, "%d / %d" % (done, total), (x + w, 192), g.f_panel, C_TEXT, right=True)
    draw_bar(g, pygame.Rect(x, 226, w, 18), done / float(total), C_TEXT)

    # 脏格：显示的是**本幕累计**涂错格数，擦掉不减
    stains = b.stains
    st_col = C_MONSTER if stains > STAIN_LIMIT else (C_WARN if stains > STAIN_LIMIT * 0.7 else C_TEXT)
    txt(g, "STAINS", (x, 280), g.f_small, C_DIM)
    txt(g, "%d / %d" % (stains, STAIN_LIMIT), (x + w, 276), g.f_panel, st_col, right=True)

    # 场上红怪
    txt(g, "RED ON FIELD", (x, 340), g.f_small, C_DIM)
    txt(g, str(len(g.monsters)), (x + w, 336), g.f_panel,
        C_MONSTER if g.monsters else C_TEXT, right=True)

    pygame.draw.line(s, C_PANEL_LINE, (x, 396), (x + w, 396))
    # 396 以下是给 Phase B 的 8 格物品栏与 21×21 进度图留的位置

    # ---- 底部操作提示 ----
    txt(g, "[WASD] MOVE    [SHIFT] ANOMALY    [J] DARK    [K] ERASE    [R] RESTART",
        (HUD_X, HINT_Y), g.f_small, C_ERASING)

    # ---- 底部系统消息（全大写，一次一句）----
    if g.hint_t > 0 and g.hint_text:
        lines = g.hint_text.split("\n")
        imgs = [g.f_main.render(ln, True, C_WARN) for ln in lines]
        bw = max(im.get_width() for im in imgs) + 48
        bh = 16 + 30 * len(imgs)
        plate = pygame.Rect(0, 0, bw, bh)
        plate.center = (PLAY_W // 2, HINT_Y + 52)
        s.fill(C_BG, plate)
        pygame.draw.rect(s, C_WARN, plate, 1)
        for i, im in enumerate(imgs):
            s.blit(im, im.get_rect(center=(plate.centerx, plate.top + 15 + 30 * i)))

    if g.debug:
        txt(g, "FPS %d  CELL %d,%d  QR %s  WAVE %.0f" % (
            int(round(1.0 / max(g._last_dt, 1e-4))), g.player.cell[0], g.player.cell[1],
            g.qr_content, g.wave_r),
            (HUD_X, HUD_Y + 30), g.f_small, C_DIM)

# ---------- 覆盖层 ----------


def draw_end(g: "Game"):
    """第一幕收尾：整屏压暗 + ACT 1 — END。"""
    s = g.screen
    veil = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    veil.fill((0, 0, 0, 195))
    s.blit(veil, (0, 0))
    center_txt(g, g.banner_text, (PLAY_W // 2, WINDOW_H // 2 - 30), g.f_big, C_TEXT)
    if int(g.menu_t * 2.0) % 2 == 0:
        center_txt(g, "PRESS ENTER", (PLAY_W // 2, WINDOW_H // 2 + 90), g.f_main, C_ERASING)


def draw_dead(g: "Game"):
    s = g.screen
    veil = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    veil.fill((0, 0, 0, 200))
    s.blit(veil, (0, 0))
    center_txt(g, "SEQUENCER DOWN", (WINDOW_W // 2, 430), g.f_mid, C_MONSTER)
    center_txt(g, "THE ALTAR WILL TAKE YOU BACK", (WINDOW_W // 2, 500), g.f_main, C_TEXT)
    if int(g.menu_t * 2.0) % 2 == 0:
        center_txt(g, "CLICK OR PRESS ENTER", (WINDOW_W // 2, 580), g.f_main, C_ERASING)


# ---------- 旧五关版界面（新版不进入这些状态，留着备查）----------


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


def draw_thumb(g: "Game", x, y, is_target):
    s = g.screen
    orr, occ = TARGET_OFFSET
    for tr in range(21):
        for tc in range(21):
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
