# -*- coding: utf-8 -*-
"""界面绘制：所有 draw_* 都在这里，第一个参数是 Game 实例。

改界面不用翻游戏逻辑，改逻辑也不会碰画法。
只读 Game 的属性，不修改任何游戏状态。
"""

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:            # 只为 IDE 补全与类型检查，运行时不执行，不会造成循环 import
    from src.game import Game

from src import story
from src.config import (
    BAR_H, BAR_W, BLACK, CELL, C_ACCENT, C_BG, C_BG_GRID, C_CELL_BLACK, C_CELL_LINE,
    C_CELL_WHITE, C_DIM, C_ERASING, C_LOCK, C_MISSING, C_MONSTER, C_PANEL, C_PLAYER,
    C_TEXT, C_WARN, ERASE_CAST, ERASING, GRID_N, GRID_ORIGIN, GRID_PX, HUD_PAD,
    DARK_MODULE, DARK_MODULE_LEAD, INTRO_TOTAL, LEVELS, MENU_BLINK_HZ, PLAYER_BODY_H,
    PLAYER_BODY_W, PLAYER_GLOW_R,
    SPAWN_ORIGIN, SPAWN_PX, TARGET_N, TARGET_OFFSET, THUMB_CELL, WHITE, WINDOW_H,
    WINDOW_W
)
from src.grid import cell_to_rect, to_target


def draw_world(g: "Game"):
    s = g.screen
    s.fill(C_BG)

    # 废墟暗格：每 28px 一层暗线，主网格盖上去之后只剩网格外的部分可见
    for x in range(0, WINDOW_W, CELL):
        pygame.draw.line(s, C_BG_GRID, (x, 0), (x, WINDOW_H))
    for y in range(0, WINDOW_H, CELL):
        pygame.draw.line(s, C_BG_GRID, (0, y), (WINDOW_W, y))

    # 生成环虚线框：提示怪物从这条线外来
    draw_dashed_rect(g, s, pygame.Rect(SPAWN_ORIGIN, (SPAWN_PX, SPAWN_PX)))

    # 白底一次铺满整个网格（不用逐格 fill），再给阶段2 的锁定区补暗色。
    # 锁定格保留网格线，和「涂黑的实心块」在质感上区分开
    s.fill(C_CELL_WHITE, pygame.Rect(GRID_ORIGIN, (GRID_PX, GRID_PX)))
    if not g.board.outer_open:
        for r in range(GRID_N):
            for c in range(GRID_N):
                if g.board.state[r][c] == WHITE and to_target(r, c) is None:
                    s.fill(C_LOCK, cell_to_rect(r, c))

    orr, occ = TARGET_OFFSET

    # 开场动画的前半段：完整二维码先用「黑色」铺出来，抖几下再震碎
    # （震碎之后这块不再画，网格恢复全白，只剩到处飞的碎片）
    if g.intro_t > 0 and not g.burst_done:
        if INTRO_TOTAL - g.intro_t < DARK_MODULE_LEAD:
            # 最开始 0.2 秒只有「暗模块」一格是黑的：整张码里唯一永远为黑的格子。
            # 每次开局都从这一格开始 —— 他的手记得，他的脑子不记得。
            dr, dc = DARK_MODULE
            s.fill(C_CELL_BLACK, cell_to_rect(orr + dr, occ + dc))
        else:
            for tr in range(TARGET_N):
                row = g.target[tr]
                for tc in range(TARGET_N):
                    if row[tc]:
                        s.fill(C_CELL_BLACK, cell_to_rect(orr + tr, occ + tc))

    # 目标提示层：只有「该黑且还白」的格子才叠，强度低到不盖住网格线。
    # 开场结束时它从 0 淡入（hint_alpha 由 game 那边推进），平时恒为 255
    if g.hint_alpha > 0:
        g.ghost.set_alpha(g.hint_alpha)
        for tr in range(TARGET_N):
            row = g.target[tr]
            for tc in range(TARGET_N):
                if row[tc] and g.board.state[orr + tr][occ + tc] == WHITE:
                    s.blit(g.ghost, (GRID_ORIGIN[0] + (occ + tc) * CELL,
                                        GRID_ORIGIN[1] + (orr + tr) * CELL))

    # 网格线：整片画线比每格描边便宜，且不会被提示块吃掉
    for i in range(GRID_N + 1):
        x = GRID_ORIGIN[0] + i * CELL
        y = GRID_ORIGIN[1] + i * CELL
        pygame.draw.line(s, C_CELL_LINE, (x, GRID_ORIGIN[1]), (x, GRID_ORIGIN[1] + GRID_PX))
        pygame.draw.line(s, C_CELL_LINE, (GRID_ORIGIN[0], y), (GRID_ORIGIN[0] + GRID_PX, y))

    # 已涂黑 / 抹除中 / 被啃红闪
    for r in range(GRID_N):
        for c in range(GRID_N):
            st = g.board.state[r][c]
            if st == BLACK:
                s.fill(C_CELL_BLACK, cell_to_rect(r, c))
            elif st == ERASING:
                rect = cell_to_rect(r, c)
                s.fill(C_ERASING, rect)
                # 抹除灰与提示灰明度只差 15，靠颜色分不清，让中心白块从 0 撑到满格
                k = 1.0 - g.board.erase_t[r][c] / ERASE_CAST
                inset = int(CELL * 0.5 * (1.0 - k))
                if inset > 0:
                    s.fill(C_CELL_WHITE, rect.inflate(-2 * inset, -2 * inset))
    for (r, c) in g.board.flash:
        s.blit(g.flash_surf, (GRID_ORIGIN[0] + c * CELL, GRID_ORIGIN[1] + r * CELL))

    # 开场碎片：一块碎片就是一个 28px 黑方块，掉出屏幕底部后由 game 那边回收。
    # 描一圈浅边，否则飞到深色背景上就完全看不见了
    for d in g.debris:
        rect = pygame.Rect(int(d[0]), int(d[1]), CELL, CELL)
        s.fill(C_MISSING, rect)                    # 深灰实心：白网格和深背景上都读得出来
        pygame.draw.rect(s, C_CELL_LINE, rect, 1)

    # 阶段2 的锁定区已在白底那一遍画成 C_LOCK（保留网格线），这里不用再盖

    # 怪物就是一个红圆；玩家必须画在它之后，否则怪物路过会把玩家盖住
    for m in g.monsters:
        mx, my = int(m.pos.x), int(m.pos.y)
        # 半径与颜色都挂在怪身上（红怪/紫怪不同），这里不再判断类型
        pygame.draw.circle(s, m.color, (mx, my), m.radius)
        pygame.draw.circle(s, C_CELL_BLACK, (mx, my), m.radius, 1)

    # 角色在开场动画期间先不出现，等灰色二维码浮现完（正式开打）再登场
    if g.intro_t <= 0:
        draw_player(g, s)


def draw_player(g: "Game", s):
    # 位置就是格心，光晕半径 14 正好铺满一格，等于顺带给"我站在哪一格"画了框
    px, py = int(g.player.pos.x), int(g.player.pos.y)
    s.blit(g.glow, (px - PLAYER_GLOW_R, py - PLAYER_GLOW_R))

    body = pygame.Rect(px - PLAYER_BODY_W // 2, py - PLAYER_BODY_H // 2,
                       PLAYER_BODY_W, PLAYER_BODY_H)
    pygame.draw.rect(s, C_PLAYER, body, border_radius=5)

    # 4×4 的「眼」按朝向偏移，让角色在静止时也有方向感
    ex, ey = px - 2, py - 2
    if g.player.facing == 0:
        ey = body.top + 4
    elif g.player.facing == 1:
        ey = body.bottom - 8
    elif g.player.facing == 2:
        ex = body.left + 3
    else:
        ex = body.right - 7
    s.fill(C_CELL_BLACK, pygame.Rect(ex, ey, 4, 4))


def draw_dashed_rect(g: "Game", s, rect, dash=12, color=C_CELL_LINE):
    for x in range(rect.left, rect.right, dash * 2):
        x2 = min(x + dash, rect.right)
        pygame.draw.line(s, color, (x, rect.top), (x2, rect.top))
        pygame.draw.line(s, color, (x, rect.bottom), (x2, rect.bottom))
    for y in range(rect.top, rect.bottom, dash * 2):
        y2 = min(y + dash, rect.bottom)
        pygame.draw.line(s, color, (rect.left, y), (rect.left, y2))
        pygame.draw.line(s, color, (rect.right, y), (rect.right, y2))

# ---------- HUD ----------


def txt(g: "Game", text, pos, font, color, right=False):
    """right=True 时 pos 是右上角，用来把文字贴住右侧 HUD 边距。"""
    img = font.render(text, True, color)
    g.screen.blit(img, img.get_rect(topright=pos) if right else img.get_rect(topleft=pos))


def draw_hud(g: "Game"):
    s = g.screen
    correct, noise, _missing = g.board.stats()
    total = g.board.target_total or 1     # 百分比一律除 target_total，不写死 441
    coverage = correct / total
    noise_cap = round(total * g.goal_noise)

    top_y, mid_y = 38, 46

    # 关卡号放最上面一行；计时留在下面，两行不打架
    txt(g, "LEVEL %d/%d" % (g.level, len(LEVELS)), (HUD_PAD, 10),
             g.f_small, C_ERASING)

    # 计时：剩余 ≤30s 转警示黄
    remain = max(0.0, g.duration - g.elapsed)
    t_col = C_WARN if remain <= 30.0 else C_TEXT
    txt(g, "%02d:%02d" % (int(remain) // 60, int(remain) % 60), (HUD_PAD, top_y),
             g.f_main, t_col)

    # 进度条 + 70% 胜利线（唯一的目标锚点）
    bar = pygame.Rect(210, mid_y, BAR_W, BAR_H)
    s.fill(C_LOCK, bar)
    s.fill(C_ACCENT, pygame.Rect(bar.x, bar.y, int(BAR_W * min(coverage, 1.0)), bar.h))
    win_x = bar.x + int(BAR_W * g.goal_cover)
    pygame.draw.line(s, C_TEXT, (win_x, bar.y - 4), (win_x, bar.y + BAR_H + 4), 2)

    pct_col = C_ACCENT if coverage >= g.goal_cover else C_TEXT
    txt(g, "%d%%" % int(coverage * 100), (bar.right + 20, top_y), g.f_main, pct_col)

    # 噪声：超过上限 80% 变黄，给玩家「快废了」的预警
    n_col = C_WARN if noise > noise_cap * 0.8 else C_TEXT
    txt(g, "NOISE %d/%d" % (noise, noise_cap), (WINDOW_W - HUD_PAD, top_y),
             g.f_main, n_col, right=True)

    # 底部：阶段标签跟 board.outer_open 走（M4 翻掉开关，文案自动变）+ 操作提示
    phase2 = not g.board.outer_open
    txt(g, "PHASE 2 // LOCKED" if phase2 else "PHASE 1 // FREEFORM",
             (HUD_PAD, WINDOW_H - 62), g.f_main,
             C_ERASING if phase2 else C_ACCENT)
    txt(g, "[WASD] MOVE   [J] PAINT   [K] ERASE   [R] RESTART",
             (WINDOW_W - HUD_PAD, WINDOW_H - 62), g.f_small, C_TEXT, right=True)
    txt(g, "HOLD J WHILE MOVING TO PAINT A TRAIL",
             (WINDOW_W - HUD_PAD, WINDOW_H - 38), g.f_small, C_ERASING, right=True)

    if g.debug:
        txt(g, "FPS %d  CELL %d,%d  TARGETS %d  MON %d" % (
            int(round(1.0 / max(g._last_dt, 1e-4))),
            g.player.cell[0], g.player.cell[1], total, len(g.monsters)),
            (HUD_PAD, WINDOW_H - 38), g.f_small, C_WARN)

# ---------- 菜单 ----------


def draw_backdrop(g: "Game", s):
    """菜单统一背景：底色 + 废墟暗格，和局内呼应。"""
    s.fill(C_BG)
    for x in range(0, WINDOW_W, CELL):
        pygame.draw.line(s, C_BG_GRID, (x, 0), (x, WINDOW_H))
    for y in range(0, WINDOW_H, CELL):
        pygame.draw.line(s, C_BG_GRID, (0, y), (WINDOW_W, y))


def draw_button(g: "Game", rect, label, sub, hot, locked=False):
    """一个按钮：悬停亮青边，锁定变暗并显示 LOCKED。"""
    fill = C_LOCK if locked else C_PANEL
    edge = C_DIM if locked else (C_ACCENT if hot else C_ERASING)
    pygame.draw.rect(g.screen, fill, rect, border_radius=8)
    pygame.draw.rect(g.screen, edge, rect, 2, border_radius=8)
    col = C_DIM if locked else (C_ACCENT if hot else C_TEXT)
    img = g.f_mid.render(label, True, col)
    cy = rect.centery - 12 if sub else rect.centery
    g.screen.blit(img, img.get_rect(center=(rect.centerx, cy)))
    if sub:
        sub_img = g.f_small.render(sub, True, C_DIM if locked else C_ERASING)
        g.screen.blit(sub_img, sub_img.get_rect(center=(rect.centerx, rect.bottom - 30)))


def draw_title(g: "Game"):
    s = g.screen
    draw_backdrop(g, s)
    mid = WINDOW_W // 2
    center_txt(g, "DATA SHIFT", (mid, 300), g.f_big, C_ACCENT)
    center_txt(g, story.TITLE, (mid, 384), g.f_main, C_ERASING)
    draw_button(g, g.start_btn(), "START", "", g.hover == 0)
    if int(g.menu_t * MENU_BLINK_HZ) % 2 == 0:      # 闪一下，别像静态图
        center_txt(g, "CLICK START  OR  PRESS ENTER", (mid, 610), g.f_small, C_ERASING)
    center_txt(g, "[WASD] MOVE     [J] PAINT     [K] ERASE", (mid, 760), g.f_main, C_TEXT)
    center_txt(g, "[R] RESTART     [ESC] BACK     [F1] DEBUG", (mid, 800),
                    g.f_small, C_ERASING)
    center_txt(g, "ESC: QUIT", (mid, 930), g.f_small, C_ERASING)


def draw_select(g: "Game"):
    s = g.screen
    draw_backdrop(g, s)
    mid = WINDOW_W // 2
    center_txt(g, "SELECT FRAGMENT", (mid, 220), g.f_mid, C_ACCENT)
    center_txt(g, story.UNREADABLE, (mid, 268), g.f_small, C_DIM)

    for i, rect in enumerate(g.level_btns()):
        n = i + 1
        locked = n > g.unlocked
        it = story.level(n)
        sub = "LOCKED" if locked else it["name"]
        # 同一时刻只亮一个：鼠标在某个按钮上就只听鼠标，鼠标不在按钮上才用键盘选中项
        hot = (g.hover == i) if g.hover is not None else (g.sel == n and not locked)
        draw_button(g, rect, it["key"], sub, hot, locked)

    # 选中那一关的难度（按钮上只放叙事，数字挪到这里，别让按钮变成仪表盘）
    cfg = LEVELS[max(0, min(len(LEVELS) - 1, g.sel - 1))]
    center_txt(g, "COVER %d%%    NOISE %d%%    LIMIT %dS" % (
        int(cfg["cover"] * 100), int(cfg["noise"] * 100), int(cfg["time"])),
        (mid, 578), g.f_small, C_ERASING)

    center_txt(g, "CLICK A FRAGMENT   -   A/D OR ARROWS   -   ENTER TO PLAY   -   ESC: BACK",
                    (mid, 620), g.f_small, C_ERASING)


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


def draw_banner(g: "Game"):
    """两种横幅：
    big   —— 整屏暗幕 + 居中大字（PHASE SHIFT 这类"事件"）
    story —— 底部一条窄字幕（剧情句），不挡棋盘，玩家能一边读一边看码
    """
    if g.banner_t <= 0:
        return
    k = min(1.0, g.banner_t / g.banner_total)     # 1 -> 0

    if g.banner_kind == "story":
        lines = wrap_text(g.f_main, g.banner_text, 900)
        w = max(g.f_main.size(ln)[0] for ln in lines) + 72
        h = 18 + 30 * len(lines)
        top = 924 - h                              # 贴着棋盘下方往上长，不压网格也不碰 HUD
        left = (WINDOW_W - w) // 2
        g.band.fill((0, 0, 0, 0))
        pygame.draw.rect(g.band, (0, 0, 0, int(160 * k)),
                         pygame.Rect(0, 0, w, h), border_radius=5)
        for i, ln in enumerate(lines):
            img = g.f_main.render(ln, True, C_TEXT)
            g.band.blit(img, img.get_rect(center=(w // 2, 9 + 30 * i + 15)))
        g.screen.blit(g.band, (left, top))
        return

    a = int(160 * k)                                    # 只让「幕」淡出
    g.overlay.fill((0, 0, 0, a))
    img = g.f_big.render(g.banner_text, True, C_TEXT)
    # 文字始终全亮：棋盘偏白，白字要靠暗幕托着；幕淡到透明时白字本来也看不见，不突兀
    img.set_alpha(255)
    g.overlay.blit(img, img.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2)))
    g.screen.blit(g.overlay, (0, 0))

# ---------- 结算页 ----------


def center_txt(g: "Game", text, pos, font, color):
    img = font.render(text, True, color)
    g.screen.blit(img, img.get_rect(center=pos))


def draw_thumb(g: "Game", x, y, is_target):
    """21×21 缩略图。左图纯黑白；右图按「对/错/缺」上色：青绿 / 猩红 / 暗灰。"""
    s = g.screen
    orr, occ = TARGET_OFFSET
    for tr in range(TARGET_N):
        for tc in range(TARGET_N):
            want = g.target[tr][tc]
            if is_target:
                col = C_CELL_BLACK if want else C_CELL_WHITE
            else:
                got = g.board.state[orr + tr][occ + tc] == BLACK
                if want:
                    col = C_ACCENT if got else C_MISSING
                else:
                    col = C_MONSTER if got else C_CELL_WHITE
            s.fill(col, (x + tc * THUMB_CELL, y + tr * THUMB_CELL,
                         THUMB_CELL, THUMB_CELL))
    pygame.draw.rect(s, C_CELL_LINE,
                     pygame.Rect(x, y, TARGET_N * THUMB_CELL, TARGET_N * THUMB_CELL), 1)


def draw_result(g: "Game"):
    s = g.screen
    s.fill(C_BG)                     # 结算页是整屏重画，不清屏会透出上一帧棋盘
    r = g.result
    thumb = TARGET_N * THUMB_CELL
    mid_x = WINDOW_W // 2

    last = g.level >= len(LEVELS)
    # 结算只讲一句话：赢了说这一关的真相，输了统一 NOT YET READABLE.
    line = story.level(g.level)["end"] if r["won"] else story.FAIL
    col = C_ACCENT if r["won"] else C_MONSTER
    lines = wrap_text(g.f_mid, line, 860)
    for i, ln in enumerate(lines):
        center_txt(g, ln, (mid_x, 128 + i * 58), g.f_mid, col)

    left_x, right_x, top_y = 120, WINDOW_W - 120 - thumb, 250
    draw_thumb(g, left_x, top_y, True)
    draw_thumb(g, right_x, top_y, False)
    txt(g, "TARGET", (left_x, top_y - 32), g.f_small, C_ERASING)
    txt(g, "YOURS", (right_x, top_y - 32), g.f_small, C_ERASING)

    cov_col = C_ACCENT if r["won"] else C_TEXT
    n_col = C_WARN if r["noise"] > r["cap"] * 0.8 else C_TEXT
    center_txt(g, "COVERAGE %d%%" % int(r["coverage"] * 100),
                    (mid_x, 344), g.f_main, cov_col)
    center_txt(g, "NOISE %d / %d" % (r["noise"], r["cap"]),
                    (mid_x, 380), g.f_main, n_col)

    g_col = C_MONSTER if r["grade"] == "F" else (C_WARN if r["grade"] == "B" else C_ACCENT)
    center_txt(g, "GRADE", (mid_x, 522), g.f_small, C_ERASING)
    center_txt(g, r["grade"], (mid_x, 592), g.f_big, g_col)

    if not r["won"]:
        nxt = "R: RETRY"
    elif last:
        nxt = "R: LEVELS"
    else:
        nxt = "R: NEXT LEVEL"
    center_txt(g, story.label(g.level), (mid_x, 690), g.f_small, C_ERASING)
    center_txt(g, "%s      ESC: LEVELS" % nxt, (mid_x, 760), g.f_main, C_TEXT)
