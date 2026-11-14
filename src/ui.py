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
    C_ITEM_PAPER, C_ITEM_PAPER_DARK, C_ITEM_LEATHER_DARK, C_MONSTER, C_MUST,
    C_OUTLINE, C_PLAYER, C_PURPLE, C_MIRAGE,
    C_OLDMAN, C_PANEL, C_PANEL_LINE, C_PROP_TOOL, C_RING,
    C_BOX, C_PAPER, C_TEXT, C_WARN,
    DIRTY, DARK_MODULE, DARK_MODULE_LEAD, DLG_BOTTOM, DLG_BOX, DLG_CPS, DLG_FONT, DLG_LINE_H,
    DLG_MIN_ROWS, DLG_PAD,
    ERASE_CAST, ERASING, FORMAT_HOLD_TIME, GRID_N, SCAN_TIME,
    GRID_ORIGIN, GRID_PX, HEALTH_LOW, HEALTH_MAX, HEALTH_WARN, HINT_Y, HUD_X, HUD_Y,
    INTRO_FALL, INTRO_PRINT, INTRO_SHOW,
    INTRO_TOTAL, MAP_CELL, MAP_SCROLL_H, MAP_SCROLL_W, MAP_Y, MIRAGE_ALPHA_MAX, MIRAGE_FADE, MIRAGE_RADIUS, MONO_CPS,
    MONO_FADE_IN, MONO_FADE_OUT, MONO_FONT, MONO_LINE_H,
    PANEL_H, PANEL_PAD, PANEL_W, PANEL_X, PANEL_Y,
    OLDMAN_HP, OLDMAN_REVIVE_TIME, PROP_DEAD_CELL, PROP_TOOL_CELL, SPAWN_ORIGIN,
    SPAWN_PX, STAIN_LIMIT, SWORD_RANGE, SWORD_SWING_TIME, TARGET_N, TOAST_LIFT,
    TARGET_OFFSET, THREAT_Y, VALID, WHITE, WINDOW_H, WINDOW_W
)
from src.grid import cell_center, cell_to_rect, target_rect
from src.qr import ERROR_TOLERANCE

PLAY_W = PANEL_X             # 左侧世界区域的宽度
PANEL_INNER = PANEL_W - PANEL_PAD * 2


# ==== 开始页 ====
#
# 开始页不放任何「玩法解释」，只做三件事：
#   1. 背景是一张**正在被写出来的真码**（和圣坛同一个生成器），一眼看出这游戏在干什么；
#   2. 标题有一道扫描带慢慢扫过、偶尔错位一帧，像一行被读坏的数据；
#   3. 按键说明做成键帽（[J] DARK 而不是「[J] 制造黑域」一大串字）。
# 所有文字都用已有文案，没有新台词。

TITLE_CELL = 26                                  # 背景水印每格像素（21×26 = 546）
TITLE_CODE_Y = 428                               # 水印中心（下缘 701，正好让开键帽那一行）
TITLE_GROW = 1.7                                 # 「写出来」用多久（秒）
# 标题下那行小字。原来写的是「ACT 1」—— 但这一页是**整局**的封面（五幕、也包含通关后回到这里），
# 标幕号既多余又不对。留空 = 不画；想放一句副标题就改这里。
TITLE_SUB = ""
C_RULE = (72, 104, 140)                          # 标题下那条细线（比面板线亮一档，才看得见）
C_CODE_FAR = (26, 42, 62)                        # 水印墨色：只比底色亮一点，是纹理不是图案
C_CODE_NEAR = (58, 88, 124)                      # 扫描带经过时被点亮的墨色

_TITLE_CACHE = {}


def _title_code():
    """开始页背景那张码：**就是本局要复原的那一张**（作者 2026-11-14 定）。

    以前是「每次启动现抽一张、和这一局的码无关」（2026-11-12 的结论）；
    内容固定成 `config.QR_CONTENT` 之后，封面 / 棋盘 / 终幕那张卡是同一张码 ——
    于是宣传图、预告、截图里那张码，扫出来和玩家结局扫出来的是**同一句话**。

    用真码而不是随机点阵，是因为三个定位图案一眼就能认出「这是个码」，
    和游戏里那座圣坛是同一个东西。进程内缓存是必须的 —— 每帧现算会掉帧。
    """
    mat = _TITLE_CACHE.get("code")
    if mat is None:
        from src import qr                        # 延迟导入：只有开始页需要
        mat, _ = qr.generate_target()             # 内容固定，所以每局每启动都一样
        _TITLE_CACHE["code"] = mat
    return mat


def _title_scanlines():
    """CRT 细横纹：一次性画好再整张贴，逐行现画会掉帧。"""
    surf = _TITLE_CACHE.get("lines")
    if surf is None:
        surf = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        for y in range(0, WINDOW_H, 3):
            pygame.draw.line(surf, (0, 0, 0, 26), (0, y), (WINDOW_W, y))
        _TITLE_CACHE["lines"] = surf
    return surf


def _draw_title_code(g: "Game", s, t):
    """背景水印：从左上往右下逐格「写」出来，写完之后有一道扫描带反复扫过。"""
    mat = _title_code()
    full = TARGET_N * TITLE_CELL
    x0 = (WINDOW_W - full) // 2
    y0 = TITLE_CODE_Y - full // 2
    grow = min(1.0, t / TITLE_GROW)              # 0 → 1：写出来的进度
    band = (t * 0.16) % 1.0 * full               # 扫描带在纸上自上而下走
    for r in range(TARGET_N):
        row = mat[r]
        y = y0 + r * TITLE_CELL
        near_band = abs(y - y0 - band) < TITLE_CELL * 1.4
        delay = r / (TARGET_N - 1)               # 行延迟：一行一行往下写
        for c in range(TARGET_N):
            if not row[c]:
                continue
            if grow * 1.12 < delay + c * 0.004:  # 同一行里从左往右再拖一点
                continue
            k = 0.5 + 0.5 * math.sin(t * 1.2 - (r + c) * 0.28)   # 呼吸
            col = tuple(int(C_CODE_FAR[i] + (C_CODE_NEAR[i] - C_CODE_FAR[i]) * (0.35 * k)) for i in range(3))
            if near_band:
                col = tuple(min(255, v + 16) for v in col)
            s.fill(col, pygame.Rect(x0 + c * TITLE_CELL, y, TITLE_CELL, TITLE_CELL))


def _title_word(g: "Game"):
    """标题的三张图（主字 / 青色残影 / 暗影），只渲染一次。

    「DATA」白、「SHIFT」青：一个词两种色，从标题就把「数据」和「移位」分开，
    也比整行纯白更像这个世界的字。
    """
    imgs = _TITLE_CACHE.get("word")
    if imgs is None:
        parts = (("DATA", C_TEXT), ("SHIFT", C_ACCENT))
        gap = g.f_big.size(" ")[0]
        widths = [g.f_big.size(w)[0] for w, _ in parts]
        size = (sum(widths) + gap * (len(parts) - 1), g.f_big.get_height())
        main = pygame.Surface(size, pygame.SRCALPHA)
        ghost = pygame.Surface(size, pygame.SRCALPHA)
        shadow = pygame.Surface(size, pygame.SRCALPHA)
        x = 0
        for (word, color), w in zip(parts, widths):
            main.blit(g.f_big.render(word, True, color), (x, 0))
            ghost.blit(g.f_big.render(word, True, C_ACCENT), (x, 0))
            shadow.blit(g.f_big.render(word, True, (6, 10, 18)), (x, 0))
            x += w + gap
        imgs = (main, ghost, shadow)
        _TITLE_CACHE["word"] = imgs
    return imgs


def _draw_title_word(g: "Game", s, t):
    """标题：暗影托底 → 两道错位青色残影（每 2.6 秒抖一下）→ 主字 → 一条扫描线扫过。"""
    main, ghost, shadow = _title_word(g)
    rect = main.get_rect(center=(WINDOW_W // 2, 326))

    shadow.set_alpha(170)                          # 把白字从码纹里「抬」起来
    s.blit(shadow, rect.move(0, 3))

    phase = t % 2.6
    jitter = int(6 * math.sin(phase * 62)) if phase < 0.13 else 0   # 偶尔错位一帧
    for dx, alpha in ((-5 - jitter, 95), (5 + jitter, 65)):
        ghost.set_alpha(alpha)
        s.blit(ghost, rect.move(dx, 0))
    s.blit(main, rect)

    # 扫描线：一条亮线从头往下走，走出标题就从头再来
    span = rect.height + 30
    sy = rect.top - 15 + int((t * 120) % span)
    line = pygame.Surface((rect.width + 60, 3), pygame.SRCALPHA)
    line.fill((*C_ACCENT, 70))
    s.blit(line, (rect.left - 30, sy))


def _draw_title_rule(s):
    """标题下面那条细线：中间一颗小菱形，两边各一段。"""
    cx, y = WINDOW_W // 2, 398
    for left, right in ((cx - 220, cx - 16), (cx + 16, cx + 220)):
        pygame.draw.line(s, C_RULE, (left, y), (right, y))
        pygame.draw.line(s, C_RULE, (left, y + 1), (right, y + 1))
    pygame.draw.polygon(s, C_ACCENT, [(cx, y - 5), (cx + 5, y), (cx, y + 5), (cx - 5, y)])


def _keycap(s, g: "Game", key, x, cy, color=C_ACCENT):
    """一颗键帽：暗底 + 一像素边 + 底沿一道亮边（看着有厚度）。返回右边缘 x。"""
    img = g.f_small.render(key, True, color)
    box = pygame.Rect(x, cy - 14, img.get_width() + 18, 28)
    s.fill(C_CELL_BLACK, box)
    pygame.draw.rect(s, C_PANEL_LINE, box, 1)
    pygame.draw.line(s, C_CODE_NEAR, (box.left + 1, box.bottom - 1), (box.right - 2, box.bottom - 1))
    s.blit(img, img.get_rect(center=box.center))
    return box.right


def _draw_title_enter(g: "Game", s, t):
    """进场提示：一个呼吸的框（不硬闪），右边一颗跟着闪的光标。"""
    label = g.f_main.render("PRESS ENTER", True, C_TEXT)
    box = pygame.Rect(0, 0, label.get_width() + 56, 46)
    box.center = (WINDOW_W // 2, 596)
    k = 0.5 + 0.5 * math.sin(t * 2.4)                    # 0 → 1 呼吸
    s.fill(C_CELL_BLACK, box)
    pygame.draw.rect(s, C_ACCENT if k > 0.45 else C_PANEL_LINE, box, 1)
    s.blit(label, label.get_rect(center=(box.centerx - 7, box.centery)))
    if int(t * 2.2) % 2 == 0:                            # 闪烁光标
        s.fill(C_ACCENT, pygame.Rect(box.right - 27, box.centery - 9, 3, 18))


def _draw_title_controls(g: "Game", s, cy):
    """键位说明：键帽 + 右侧一列短词，一行排开。"""
    items = (("WASD", "MOVE"), ("SHIFT", "ANOMALY"), ("J", "DARK"), ("K", "ERASE"))
    gap_key, gap_group = 12, 38
    spans = [(g.f_small.size(k)[0] + 18, g.f_main.size(v)[0]) for k, v in items]
    total = sum(kw + gap_key + lw for kw, lw in spans) + gap_group * (len(items) - 1)
    x = (WINDOW_W - total) // 2
    for (key, label), (kw, lw) in zip(items, spans):
        right = _keycap(s, g, key, x, cy)
        img = g.f_main.render(label, True, C_TEXT)
        s.blit(img, img.get_rect(midleft=(right + gap_key, cy)))
        x = right + gap_key + lw + gap_group


def draw_title(g: "Game"):
    s = g.screen
    t = g.menu_t                                   # TITLE 里一直在走，回来重开会重播
    s.fill(C_BG)
    for x in range(0, WINDOW_W, CELL):
        pygame.draw.line(s, C_BG_GRID, (x, 0), (x, WINDOW_H))
    for y in range(0, WINDOW_H, CELL):
        pygame.draw.line(s, C_BG_GRID, (0, y), (WINDOW_W, y))

    _draw_title_code(g, s, t)
    s.blit(_title_scanlines(), (0, 0))              # CRT 细横纹：把水印压回背景层

    _draw_title_word(g, s, t)
    _draw_title_rule(s)
    if TITLE_SUB:                                    # 副标题：留空就什么都不画
        center_txt(g, TITLE_SUB, (WINDOW_W // 2, 436), g.f_main, C_ERASING)

    _draw_title_enter(g, s, t)
    _draw_title_controls(g, s, 720)

    center_txt(g, "ESC: QUIT      F1: DEBUG", (WINDOW_W // 2, 838), g.f_small, C_DIM)

    # 四角括号：把整块画面框住，暗示「你现在看到的也是一块被读出来的东西」
    m, L = 34, 46
    for (px, py, dx, dy) in ((m, m, 1, 1), (WINDOW_W - m, m, -1, 1),
                            (m, WINDOW_H - m, 1, -1), (WINDOW_W - m, WINDOW_H - m, -1, -1)):
        pygame.draw.line(s, C_PANEL_LINE, (px, py), (px + L * dx, py), 2)
        pygame.draw.line(s, C_PANEL_LINE, (px, py), (px, py + L * dy), 2)


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

    if g.act >= 5 and g.state in ("BATTLE", "SCAN"):
        _draw_error_blocks(g, s)

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
        kind = b.flash_kind.get((r, c))
        surf = {"purple": g.flash_surf_purple, "scribe": g.flash_surf_scribe}.get(kind, g.flash_surf)
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

    # 第三幕的黄怪：同一套画法，黄色。盯上玩家（挨过打）时才套环
    for y in g.yellows:
        look = g.oldman.pos if (g.oldman is not None and not g.oldman.down) else g.player.pos
        sprites.draw_red(s, y.pos.x, y.pos.y, y.radius, g.anim_t, y.phase,
                         hunting=y.hunting, look=look, glow=g.red_glow, base=y.color,
                         dark=sprites._mix(y.color, C_CELL_BLACK, 0.52),
                         ring=sprites._mix(y.color, (255, 255, 255), 0.45))

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

    if g.state == "SCAN":                            # 第五幕的收尾：一束光把码读出去
        _draw_scan(g, s)

    _draw_toasts(g, s)                               # 嘀咕：飘在头顶，不挡、不冻世界

    # 碎片画在最上层：先炸开、再被吸回脚下（塌完就只剩那一片灰）
    if g.debris:
        _draw_debris(g, s)

    # 威胁台词（红怪的狠话）
    if g.threat_t > 0:
        _draw_threat(g, s)


def _draw_error_blocks(g, s):
    """第五幕：把「坏掉的码字」标出来（红框）。

    没有这个标记，玩家面对一堆随机图案根本不知道哪块坏了、该修哪块 ——
    而这一幕的全部玩法就是「决定放弃哪几块」，所以必须让他看得见。
    """
    for mods in g.cw_modules.values():
        bad = [(r, c, dark) for (r, c, dark) in mods
               if ((g.board.state[r][c] != VALID) if dark else (g.board.state[r][c] != WHITE))]
        if not bad:
            continue
        for (r, c, dark) in bad:
            _damage_cell(s, cell_to_rect(r, c))


_DAMAGE_WASH = None


def _damage_cell(s, rect, size=6):
    """坏格：一层淡红水洗 + 四角 2px 角标。

    只画细边在 1x 下几乎看不见（试过 1px 四角，截图里要盯才找得到）；
    整圈 2px 红框又太吵，会和绿框（必涂格）抢。淡红水洗 + 角标是这两者中间那档：
    一眼扫得到，但不至于像 UI 弹窗。
    """
    global _DAMAGE_WASH
    if _DAMAGE_WASH is None:
        _DAMAGE_WASH = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        _DAMAGE_WASH.fill((*C_MONSTER, 44))
    s.blit(_DAMAGE_WASH, rect.topleft)
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    for (px, py, dx, dy) in ((x, y, 1, 1), (x + w - 2, y, -1, 1),
                             (x, y + h - 2, 1, -1), (x + w - 2, y + h - 2, -1, -1)):
        pygame.draw.line(s, C_MONSTER, (px, py), (px + dx * size, py), 2)
        pygame.draw.line(s, C_MONSTER, (px, py), (px, py + dy * size), 2)


def _draw_toasts(g, s):
    """嘀咕：玩家头顶上方的一行小字，2 秒淡掉。

    为什么不做成框（作者 2026-11-14）：框占半屏，一次涂错就挡住要涂的那片；
    而且它一出现世界就得停。反馈类不需要仪式感，需要的是**看得见、又不碍事**。
    所以：贴着头顶、带 1px 暗描边（白格上也读得清）、不做背景板。
    """
    if not g.toasts:
        return
    px, py = int(g.player.pos.x), int(g.player.pos.y)
    top = GRID_ORIGIN[1] + 12
    for i, (text, t, life, who) in enumerate(g.toasts):
        fade = min(1.0, t / 0.12, max(0.0, (life - t) / 0.5))
        if fade <= 0.02:
            continue
        col = C_OLDMAN if who == story.OLD_MAN else C_ACCENT
        lines = [ln for ln in text.split("\n") if ln.strip()]
        if not lines:
            continue
        block_h = len(lines) * 18
        y0 = py - TOAST_LIFT - i * 22 - block_h
        if y0 < top:                                 # 贴着上边：改画到脚下，别顶进 HUD
            y0 = py + 26 + i * 22
        for k, line in enumerate(lines):
            img = g.f_small.render(line, True, col)
            sh = g.f_small.render(line, True, C_CELL_BLACK)
            rect = img.get_rect(center=(px, y0 + 9 + k * 18))
            rect.x = max(GRID_ORIGIN[0] + 6,
                         min(rect.x, GRID_ORIGIN[0] + GRID_PX - rect.w - 6))
            img.set_alpha(int(255 * fade))
            sh.set_alpha(int(200 * fade))
            s.blit(sh, (rect.x + 1, rect.y + 1))
            s.blit(img, rect)


def _draw_scan(g, s):
    """扫描束：从上往下把整张码读一遍。

    已经扫过的部分压一层冷光（"读过了"），前沿是一道亮线。
    这是全游戏唯一一次「光从上往下走」—— 清屏波是从中心往外扩，两者不会混。
    """
    rect = target_rect()
    k = min(1.0, g.scan_t / float(SCAN_TIME)) if SCAN_TIME > 0 else 1.0
    y = rect.top + int(rect.height * k)
    if k > 0:
        band = pygame.Surface((rect.width, max(1, y - rect.top)), pygame.SRCALPHA)
        band.fill((*C_ACCENT, 26))
        s.blit(band, (rect.left, rect.top))
    pygame.draw.line(s, C_ACCENT, (rect.left, y), (rect.right, y), 3)
    halo = pygame.Surface((rect.width, 10), pygame.SRCALPHA)
    halo.fill((*C_ACCENT, 70))
    s.blit(halo, (rect.left, y - 5))


def _intro_glitch(tr, tc, t, rate=34):
    """颤动阶段的 bit flip：每帧约 3% 的模块闪白。

    用坐标 + 时间的哈希，不存状态 —— 这样抖动是「这一格这一刻该不该闪」，
    而不是一串要维护的随机数；也让同一帧重画（截图 / 测试）结果一致。
    """
    h = (tr * 73856093) ^ (tc * 19349663) ^ (int(t * 40.0) * 83492791)
    return (h & 1023) < rate


def _draw_intro_code(g, s):
    """开场前 1.5 秒：一条扫描线从上往下把整张码印出来，印完开始颤。"""
    t = INTRO_TOTAL - g.intro_t
    orr, occ = TARGET_OFFSET
    if t < DARK_MODULE_LEAD:                     # 第一拍：暗模块先单独亮一下
        dr, dc = DARK_MODULE
        s.fill(C_CELL_BLACK, cell_to_rect(orr + dr, occ + dc))
        return

    span = max(0.01, INTRO_PRINT - DARK_MODULE_LEAD)
    p = min(1.0, (t - DARK_MODULE_LEAD) / span)
    front = p * (TARGET_N + 1.0)                 # 印到第几行（浮点；末尾稍微超扫，保证印满）
    shaking = g.shake_t > 0
    for tr in range(TARGET_N):
        if tr > front:
            break
        row = g.target[tr]
        for tc in range(TARGET_N):
            if not row[tc]:
                continue
            if shaking and _intro_glitch(tr, tc, t):
                continue                         # 颤动：这一格这一帧闪白
            s.fill(C_CELL_BLACK, cell_to_rect(orr + tr, occ + tc))

    if p < 1.0:                                  # 还在印：扫描线 + 上方一层光晕
        rows = min(front, TARGET_N - 1.0)
        y = int(GRID_ORIGIN[1] + (occ + rows + 1.0) * CELL)
        x0 = GRID_ORIGIN[0] + occ * CELL
        w = TARGET_N * CELL
        halo = pygame.Surface((w, 18), pygame.SRCALPHA)
        halo.fill((*C_ACCENT, 46))
        s.blit(halo, (x0, y - 18))
        s.fill(C_ACCENT, pygame.Rect(x0, y - 1, w, 3))


def _debris_col(k):
    """碎片在这一刻的颜色：黑（the Dark）→ 灰（异象那个灰）→ 白（底色）。

    塌陷途中变灰是关键：这样「码碎了」和「异象亮着」是同一种颜色语言，
    碎片收完，脚下那片灰就接上了。
    """
    if k <= 0.55:
        a, b, u = C_CELL_BLACK, C_MIRAGE, k / 0.55
    else:
        a, b, u = C_MIRAGE, C_CELL_WHITE, (k - 0.55) / 0.45
    return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))


def _draw_debris(g, s):
    """塌陷：冲击环 + 白闪 + 缩小的碎片。

    ⚠️ 全部裁在**棋盘矩形**里：碎片和冲击环跑出圣坛边界会糊到右侧面板和褐色背景上，
    看起来像 bug 而不是「炸开」。裁掉之后，这一下就只发生在「地上那张码」的范围里。
    """
    k = min(1.0, max(0.0, (INTRO_TOTAL - g.intro_t - INTRO_SHOW) / INTRO_FALL))
    cx, cy = getattr(g, "burst_center", (WINDOW_W / 2.0, WINDOW_H / 2.0))
    old_clip = s.get_clip()
    s.set_clip(pygame.Rect(GRID_ORIGIN, (GRID_PX, GRID_PX)))

    if k < 0.08:                                  # 炸开那一下的白闪（4 帧）
        a = int(120 * (1.0 - k / 0.08))
        flash = pygame.Surface((TARGET_N * CELL, TARGET_N * CELL), pygame.SRCALPHA)
        flash.fill((255, 255, 255, a))
        s.blit(flash, (GRID_ORIGIN[0] + TARGET_OFFSET[1] * CELL,
                       GRID_ORIGIN[1] + TARGET_OFFSET[0] * CELL))
    if k < 0.45:                                  # 冲击环：从脚下荡出去，前 45% 散完
        u = k / 0.45
        col = tuple(int(C_ACCENT[i] + (C_CELL_WHITE[i] - C_ACCENT[i]) * u) for i in range(3))
        pygame.draw.circle(s, col, (int(cx), int(cy)), int(60 + 620 * u), 2)

    for d in g.debris:
        scale = d[4] if len(d) > 4 else 1.0
        dk = d[5] if len(d) > 5 else 0.0
        size = max(2, int(CELL * scale))
        rect = pygame.Rect(int(d[0] - size / 2.0), int(d[1] - size / 2.0), size, size)
        s.fill(_debris_col(dk), rect)
    s.set_clip(old_clip)


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
    om = g.oldman
    if g.act >= 3 and om.down:                       # 第三幕：他被打倒了
        _draw_revive_ring(g, s, om)                  # 环先画，压在身体底下
        sprites.draw_oldman_down(s, om, g.anim_t)
        _draw_revive_hint(g, s, om)                  # [H] 最后画，盖在最上面
        return
    sprites.draw_oldman(s, om, g.anim_t)
    if g.act == 3:                                   # 只有第三幕他会挨咬；第四幕没人咬他，别画假血条
        _draw_oldman_hp(g, s, om)


def _draw_oldman_hp(g, s, om):
    """他头顶一根细血条。**只有第三幕有** —— 前两幕他打不到，画出来只是噪音。"""
    if om.hurt_t > 0:                                # 被咬那一下整体泛红（加色，不遮住他）
        s.fill((70, 0, 18), pygame.Rect(int(om.pos.x) - 14, int(om.pos.y) - 12, 28, 26),
               special_flags=pygame.BLEND_RGB_ADD)
    w, h = 34, 5
    box = pygame.Rect(int(om.pos.x) - w // 2, int(om.pos.y) - 26, w, h)
    frac = max(0.0, om.hp / float(OLDMAN_HP))
    col = C_MONSTER if frac <= 0.3 else C_OLDMAN
    s.fill(C_CELL_BLACK, box)
    s.fill(col, pygame.Rect(box.x + 1, box.y + 1, max(0, int((w - 2) * frac)), h - 2))
    pygame.draw.rect(s, C_OUTLINE, box, 1)


def _draw_revive_ring(g, s, om):
    """他倒下时脚下那圈：平时是一圈暗环，按住 H 的时候按进度长出青色弧。"""
    r = 20
    cx, cy = int(om.pos.x), int(om.pos.y) + 2
    box = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
    pygame.draw.circle(s, C_PANEL_LINE, (cx, cy), r, 2)
    frac = g.revive_t / float(OLDMAN_REVIVE_TIME) if OLDMAN_REVIVE_TIME > 0 else 0.0
    if frac > 0:
        pygame.draw.arc(s, C_ACCENT, box, math.radians(90), math.radians(90 + 360 * min(frac, 1.0)), 3)


def _draw_revive_hint(g, s, om):
    """头顶的 [H]：闪一下再暗一下，别做成一直亮着的常驻 UI。"""
    cx, cy = int(om.pos.x), int(om.pos.y) - 32
    if cy < GRID_ORIGIN[1] + 12:                     # 他在最上面那一行：提示改画到脚下
        cy = int(om.pos.y) + 44
    k = (math.sin(g.anim_t * 3.4) + 1.0) * 0.5
    img = g.f_main.render("[H]", True, C_TEXT if k > 0.45 else C_OLDMAN)
    s.blit(img, img.get_rect(center=(cx, cy)))


def _draw_item(g, s, it):
    rise = int((1.0 - it.t) * 22)
    sprites.draw_item(s, it.kind, it.pos.x, it.pos.y, g.anim_t, rise)
    # 小标签压在道具上方：图标已经认得出，但第一幕需要玩家一眼知道「这是 BAG / MAP / SWORD」
    label = {"bag": "BAG", "map": "MAP", "sword": "SWORD"}.get(it.kind, "")
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
                           glow=g.glow, has_bag=g.has_bag, holding_map=g.map_open,
                           has_sword=g.has_sword,
                           swing=(g.swing_t / SWORD_SWING_TIME) if g.swing_t > 0 else 0.0)
    if g.swing_t > 0:                                # 挥剑：身前一道弧，很快消失
        _draw_swing(g, s)
    if g.fill_t > 0:                                 # 按住 J 写格式格：脚下长出一圈进度
        _draw_fill_ring(g, s, p.pos)


def _draw_fill_ring(g, s, pos):
    """格式信息要「按住」才写得动 —— 这一圈就是他正在写的那一笔。

    用和救人（`_draw_revive_ring`）同一套语言：暗环打底，青色弧按进度长。
    没有它玩家会以为按键坏了（普通格明明一点就成）。
    """
    r = 16
    cx, cy = int(pos.x), int(pos.y) + 12             # 落在脚下一圈，上半圈压在袍子上
    box = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
    pygame.draw.circle(s, mix(C_ACCENT, C_CELL_BLACK, 0.45), (cx, cy), r, 2)
    frac = min(1.0, g.fill_t / float(FORMAT_HOLD_TIME)) if FORMAT_HOLD_TIME > 0 else 1.0
    # 从**脚底**往两侧对称长：像水位上涨，也避开脸和手
    half = math.pi * frac
    foot = math.pi * 1.5
    pygame.draw.arc(s, C_ACCENT, box, foot - half, foot, 2)
    pygame.draw.arc(s, C_ACCENT, box, foot, foot + half, 2)


def _draw_swing(g: "Game", s):
    """挥砍的弧：朝面向那边甩出去，随 swing_t 变淡。"""
    p = g.player
    k = g.swing_t / SWORD_SWING_TIME if SWORD_SWING_TIME > 0 else 0.0
    ang = {0: -90, 1: 90, 2: 180, 3: 0}[p.facing]
    r = SWORD_RANGE * (0.7 + 0.3 * (1.0 - k))
    cx, cy = p.pos.x, p.pos.y
    a0 = math.radians(ang - 42)
    a1 = math.radians(ang + 42)
    box = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
    col = C_TEXT if k > 0.5 else C_ERASING
    pygame.draw.arc(s, col, box, min(a0, a1), max(a0, a1), 3)


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


def draw_bar(g: "Game", rect, frac, color, back=(12, 20, 32)):
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
    # 三档：正常青绿 / 60% 以下转黄（预警）/ 35% 以下转红（快死了）。
    # 原来只有 30% 一档，玩家在 55% 时看到的还是「一切正常」的青绿 —— 太晚。
    if hp <= HEALTH_LOW:
        hp_col = C_MONSTER
    elif hp <= HEALTH_WARN:
        hp_col = C_WARN
    else:
        hp_col = C_ACCENT
    txt(g, "HEALTH", (x, 96), g.f_small, C_DIM)
    txt(g, "%d%%" % hp, (x + PANEL_INNER, 92), g.f_panel, hp_col, right=True)
    draw_bar(g, pygame.Rect(x, 126, PANEL_INNER, 24), hp / float(HEALTH_MAX), hp_col)

    done = b.progress()
    total = len(b.must) or 1
    if g.act >= 5:                                    # 第五幕：唯一的数字是「错了几块」
        eff = g.act5_errors()
        fr = g.frame_broken()
        col = C_MONSTER if (fr or eff > ERROR_TOLERANCE) else C_ACCENT
        txt(g, "FRAME" if fr else "ERRORS", (x, 196), g.f_small,
            C_MONSTER if fr else C_DIM)
        txt(g, ("%d" % fr) if fr else ("%d / %d" % (eff, ERROR_TOLERANCE)),
            (x + PANEL_INNER, 192), g.f_panel, col, right=True)
        draw_bar(g, pygame.Rect(x, 226, PANEL_INNER, 18),
                 min(1.0, eff / float(ERROR_TOLERANCE + 1)), col)
        if fr:
            # 第五幕他在场：骨架归他，玩家不用管这一头 —— 所以别写「坏了」，
            # 写「他在补」。同一行字承担「现在为什么还不能读」的解释。
            txt(g, "HE'S ON THE FRAME" if (g.oldman is not None and not g.oldman.gone)
                else "THE FRAME IS BROKEN", (x, 252), g.f_small, C_MONSTER)
        else:
            txt(g, "IT READS AT %d OR LESS" % ERROR_TOLERANCE, (x, 252), g.f_small, C_DIM)
        txt(g, "STAINS", (x, 280), g.f_small, C_DIM)
        txt(g, "%d / %d" % (b.stains, STAIN_LIMIT), (x + PANEL_INNER, 276), g.f_panel, C_TEXT, right=True)
        txt(g, "RED ON FIELD", (x, 340), g.f_small, C_DIM)
        txt(g, str(len(g.monsters)), (x + PANEL_INNER, 336), g.f_panel,
            C_MONSTER if g.monsters else C_TEXT, right=True)
        txt(g, "PURPLE ON FIELD", (x, 372), g.f_small, C_DIM)
        txt(g, str(len(g.purples)), (x + PANEL_INNER, 368), g.f_panel,
            C_PURPLE if g.purples else C_TEXT, right=True)
        pygame.draw.line(s, C_PANEL_LINE, (x, 396), (x + PANEL_INNER, 396))
        if g.has_bag:
            _draw_bag(g, s, x, 412)
        if g.has_map:
            _draw_map(g, s, x, MAP_Y)
        _draw_bottom(g, s)
        return
    # 第三幕：老者把格式信息写完之后，剩下的格**全是玩家自己欠的** —— 这时候只报「还差几格」，
    # 报 x/y 玩家看不出该干嘛（HUD 上 121/126 和 10/126 一样没用）。
    owe = max(0, total - done)
    awaiting_fill = g.act == 3 and g.scribe_done_said and owe > 0   # 只有第三幕是他写你欠
    txt(g, "FILL" if awaiting_fill else "DARK", (x, 196), g.f_small,
        C_MONSTER if awaiting_fill else C_DIM)
    txt(g, ("%d" % owe) if awaiting_fill else ("%d / %d" % (done, total)),
        (x + PANEL_INNER, 192), g.f_panel, C_MONSTER if awaiting_fill else C_TEXT, right=True)
    draw_bar(g, pygame.Rect(x, 226, PANEL_INNER, 18), done / float(total),
             C_MONSTER if awaiting_fill else C_TEXT)

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

    _draw_bottom(g, s)


def _draw_bottom(g, s):
    """底部那一层：键位表 / 心声 / 系统提示。第五幕的 HUD 提前 return，所以抽出来复用。"""
    # ---- 底部：键位 + 提示 + 系统消息 ----
    if g.state == "DIALOG":
        pass                                    # 对话框自带 ENTER 提示，底部别再摆键位表
    elif g.state == "TUTORIAL" and g.prompt_text:
        # 教程阶段那句提示本身就是键位表，不用再摆一遍
        center_txt(g, g.prompt_text, (PLAY_W // 2, HINT_Y + 10), g.f_prompt, C_ACCENT)
    elif g.state != "SCAN":                     # 扫描时世界只剩那一束光，别摆键位
        # 常驻键位表（C6：关键键别只弹一次，错过就卡住）
        keys = "[WASD] MOVE   [SHIFT] ANOMALY   [J] DARK   [K] ERASE   [T] CALL"
        if g.act >= 5:                          # 第五幕：只修，不再有"扫"的新东西
            keys = "[WASD] MOVE   [SHIFT] ANOMALY   [J] DARK   [K] ERASE"
        elif g.act >= 4:                        # 第四幕换动词：按住 J 扫灰域
            keys = "[WASD] MOVE   [SHIFT] ANOMALY   HOLD [J] SWEEP   [K] ERASE"
        if g.act >= 3 and g.has_sword:
            keys += "   [U] SWORD"              # 第三幕才有剑，别在前两幕挂着让人按
        txt(g, keys, (HUD_X, HINT_Y), g.f_small, C_ERASING)
        if g.prompt_text:
            txt(g, g.prompt_text, (PLAY_W - 16, HINT_Y - 6), g.f_prompt, C_ACCENT, right=True)

    # 心声：暂停中（mono_hold）时 mono_t 是 0，所以两个条件都要认
    if g.mono_text and (g.mono_hold or g.mono_t > 0):
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
    if g.has_sword:
        inside.append("sword")             # 第二幕收尾拿到的
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
    s.fill(C_BOX, box)                        # 实心：半透明会把底下的白格透出来，显得脏
    pygame.draw.rect(s, C_PANEL_LINE, box, 1)
    _corner_brackets(s, box, 20, who)
    img = g.f_dlg_name.render(name, True, who if not solid_tab else (8, 10, 14))
    tab = pygame.Rect(box.x + DLG_PAD, box.y - 17, img.get_width() + 32, 34)
    if solid_tab:
        s.fill(who, tab)
    else:
        s.fill(C_BOX, tab)
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


def _mono_paint(g, s, box, vis, typing, done=False, blink=True):
    """把「心声框」画到 s 上（box 可以是屏幕坐标，也可以是离屏纸的本地坐标）。

    名牌默认是码序使（青）；老者说话时是暖米色 —— 同一套框区分「我在想」和「他在说」。
    """
    who = getattr(g, "mono_who", "") or story.SEQUENCER
    col = C_OLDMAN if who == story.OLD_MAN else C_ACCENT
    _speech_box(s, g, box, who, col, solid_tab=False)
    top = box.y + 44
    for i, ln in enumerate(vis):
        s.blit(g.f_mono.render(ln, True, C_TEXT), (box.x + DLG_PAD, top + i * MONO_LINE_H))
    if typing and vis:                        # 打字光标（和对话同一个位置算法）
        last = vis[-1]
        cx = box.x + DLG_PAD + g.f_mono.size(last)[0] + 4
        cy = top + (len(vis) - 1) * MONO_LINE_H + 8
        s.fill(C_ACCENT, pygame.Rect(cx, cy, 10, MONO_FONT - 12))
    if not done:
        return
    # 字打完了：底部两角给「按回车继续」——世界是停着的，必须让玩家知道怎么走
    hint = g.f_small.render("ENTER", True, C_ACCENT if blink else C_DIM)
    s.blit(hint, hint.get_rect(bottomleft=(box.x + DLG_PAD, box.bottom - 18)))
    if blink:
        ax, ay = box.right - 52, box.bottom - 34
        pygame.draw.polygon(s, C_ACCENT, [(ax, ay), (ax + 16, ay), (ax + 8, ay + 12)])
    tag = g.f_tiny.render("PAUSED", True, C_DIM)
    s.blit(tag, (box.right - tag.get_width() - DLG_PAD, box.y + 12))


def _draw_monologue(g, s):
    """心声：和老者对话**同一套框**，但**整个世界是停住的**，直到玩家按回车。

    作者 2026-11-12：原来它会自己淡走、而世界照常跑 —— 玩家涂错一格，心声挡住半屏、
    怪还在打他，看不清也躲不掉。现在停下来，读完再走（见 `Game.say`）。

    和对话的三处不同照旧：名牌空心描边、进出淡入淡出、**必须按回车**才继续。
    """
    if not g.mono_text or not (g.mono_hold or g.mono_t > 0):
        return
    lines = mono_lines(g)
    total = sum(len(ln) for ln in lines)
    shown = min(total, int(max(0.0, g.mono_elapsed) * MONO_CPS))
    vis, typing = _reveal(lines, shown)
    box = mono_box(g)
    done = g.mono_elapsed >= g.mono_type_time

    # 淡入用「出现多久」，淡出用「关闭后还剩多久」（暂停期间 mono_t 一直是 0）
    alpha = 1.0
    if g.mono_elapsed < MONO_FADE_IN:
        alpha = g.mono_elapsed / MONO_FADE_IN
    if not g.mono_hold:
        alpha = min(alpha, g.mono_t / MONO_FADE_OUT)
    alpha = max(0, min(255, int(255 * alpha)))
    if alpha >= 255:
        _mono_paint(g, s, box, vis, typing, done, int(g.anim_t * 3) % 2 == 0)
        return
    buf = _mono_buf(box.size)
    _mono_paint(g, buf, pygame.Rect(0, 0, box.w, box.h), vis, typing, done,
                int(g.anim_t * 3) % 2 == 0)
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
    if g.act >= 5:
        # 终幕直接盖成纯底：那张**干净**的码是唯一主角。
        # 试过 188 / 210 / 246 三档遮罩，棋盘和 HUD 总会从底下透出来 ——
        # 屏幕上同时有两张码，视觉上就是在打架（虽然卡上那张照样能扫）。
        # 因为整屏都归它了，排版也改成**整窗居中**（PLAY_W//2 会偏到左边）。
        s.fill(C_BG)
        _draw_clean_code(g, s)
        cx = WINDOW_W // 2
        center_txt(g, g.banner_text, (cx, 604), g.f_big, C_TEXT)
        if getattr(g, "end_line", ""):
            center_txt(g, g.end_line, (cx, 660), g.f_mid, C_ACCENT)
        if int(g.menu_t * 2.0) % 2 == 0:
            center_txt(g, "PRESS ENTER", (cx, 722), g.f_main, C_ERASING)
        return
    # 幕末压暗：**只压世界，不把 HUD 一起黑掉**。
    # 原来是一张盖满整屏的 216 遮罩，右侧面板连数字都看不见 —— 第一眼像游戏卡死了。
    # 现在世界照旧压满（幕结束，舞台暗下来），状态面板只压一档，留得住最后的数字。
    veil = pygame.Surface((PLAY_W, WINDOW_H), pygame.SRCALPHA)
    veil.fill((0, 0, 0, 216))
    s.blit(veil, (0, 0))
    side = pygame.Surface((WINDOW_W - PLAY_W, WINDOW_H), pygame.SRCALPHA)
    side.fill((0, 0, 0, 96))                         # 96 ≈ 留 62% 亮度
    s.blit(side, (PLAY_W, 0))
    center_txt(g, g.banner_text, (PLAY_W // 2, WINDOW_H // 2 - 30), g.f_big, C_TEXT)
    if getattr(g, "end_line", ""):                   # 结局副标题：这张码到底写了什么
        center_txt(g, g.end_line, (PLAY_W // 2, WINDOW_H // 2 + 30), g.f_mid, C_ACCENT)
    if int(g.menu_t * 2.0) % 2 == 0:
        center_txt(g, "PRESS ENTER", (PLAY_W // 2, WINDOW_H // 2 + 90), g.f_main, C_ERASING)


END_CODE_MODULE = 12           # 终幕那张码每格多少像素（≥6 才好扫，12 是整屏的观感上限）
END_CODE_QUIET = 4             # 静区格数（QR 规范下限，别减）


def _end_code_rect(g):
    """终幕那张卡的位置和尺寸。**画和测试都用它** —— 两边各算一遍迟早会走偏。"""
    n = len(g.target)
    side = (n + END_CODE_QUIET * 2) * END_CODE_MODULE
    return WINDOW_W // 2 - side // 2, 200, side


def _draw_clean_code(g, s, module=END_CODE_MODULE, quiet=END_CODE_QUIET):
    """终幕那张「能扫」的码：**没有网格线、有静区、纸是白的**。

    棋盘上的那张码是「你在写的东西」，带格子、带绿框、带光晕 —— 手机扫不出来。
    所以结局另画一张印刷版：21×21 + 四周 4 格静区（QR 规范要求，少了扫不出），
    底色用暖白（和 C_TEXT 同色），模块用近黑。这张是「你写出来的东西在现实里的样子」。

    它也是全游戏唯一一个**出了屏幕还有用**的东西：玩家可以拿手机扫自己的结局。
    """
    mat = g.target
    n = len(mat)
    x0, y0, side = _end_code_rect(g)
    module = side // (n + quiet * 2)                 # 由 rect 反推，别让两个地方各算一遍
    card = pygame.Surface((side, side))
    card.fill(C_PAPER)
    for r in range(n):
        for c in range(n):
            if mat[r][c]:
                card.fill(C_CELL_BLACK, ((c + quiet) * module, (r + quiet) * module,
                                         module, module))
    s.blit(card, (x0, y0))
    pygame.draw.rect(s, C_ACCENT, (x0 - 1, y0 - 1, side + 2, side + 2), 1)


def make_stain_tile():
    """脏黑的样子：黑底 + 白色斜条。必须和「纯黑的有效黑域」一眼可分。"""
    surf = pygame.Surface((CELL, CELL))
    surf.fill(C_CELL_BLACK)
    for i in range(-CELL, CELL * 2, 10):
        pygame.draw.line(surf, (226, 226, 232), (i, 0), (i + CELL, CELL), 4)
    return surf
