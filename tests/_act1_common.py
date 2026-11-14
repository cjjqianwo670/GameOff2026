# -*- coding: utf-8 -*-
"""第一幕 Phase A 验证脚本的公共部分：无窗口跑、截图、断言小框架。

用法（在任意目录执行）：
    D:/GameOff/GameOff2026/.venv/Scripts/python.exe _verify_act1_board.py
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# 2026-11-14：测试搬进仓库的 tests/。路径不再写死 —— 从本文件位置推两级就是仓库根，
# 换机器 / 换盘符都不用改（以前这里是 "D:/GameOff/GameOff2026"，一处失效就全线红）。
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_shots")
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
WIN = pygame.display.set_mode((1360, 1000))

RESULTS = []


def new_game():
    from src.game import Game
    g = Game(WIN)
    g.start_act()
    return g


def skip_intro(g):
    """把开场动画标记收干净（测试直接跳相位时用，免得还按"开场中"来画）。"""
    g.intro_t = 0.0
    g.hint_alpha = 0
    g.burst_done = True
    g.debris.clear()


def to_battle(g):
    """跳过开场/教程/对话/空档，直接进战斗（检查点也在这时打好）。"""
    from src.config import GAP_SECONDS
    skip_intro(g)
    if g.state == "INTRO":
        g.enter_tutorial()
    g.enter_free_roam()
    g.start_gap()
    for _ in range(int(GAP_SECONDS * 60) + 2):
        auto_mono(g)          # 空档里可能还压着一句心声（开场 M1），不推就永远进不了战斗
        g.update(1 / 60)
    return g


def to_roam(g):
    """跳到自由探索（异象/涂改都能用，但还没有红怪）。"""
    skip_intro(g)
    if g.state == "INTRO":
        g.enter_tutorial()
    g.enter_free_roam()
    return g


def auto_mono(g, limit=3):
    """测试用：替玩家按回车，把「停住世界的心声」推过去。

    2026-11-12 起心声会**冻住整个世界**等回车（作者要求）。推进时间的循环里如果不管它，
    第一帧之后就什么都不动了 —— 测试会莫名其妙全红。

    连按的逻辑和真人一致：字没打完先补完，打完再按就关闭（`Game.advance_monologue`）。
    """
    from src.config import SC_ENTER
    if not hasattr(g, "mono_hold"):
        return                                   # 传进来的不是 Game（Board 之类）：没有心声，跳过
    for _ in range(limit):
        if not g.mono_hold:
            return
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=SC_ENTER))


def toast_text(g):
    """最后一条「嘀咕」（不冻世界的飘字）。反馈类台词现在走这个，不再走 mono_text。"""
    return g.toasts[-1][0] if getattr(g, "toasts", None) else ""


def paint_ok(g, r, c):
    """按真实玩法涂一格：**先按 Shift 照出来**，再落笔。

    2026-11-12 起，圣坛内没照着灰域就写 = 脏格（`Board.paint` 里判），
    所以测试想造「涂对」的局面必须走这个函数，不能直接 `board.paint`。
    """
    g.board.reveal_around(r, c)
    return g.board.paint(r, c)


def fill_must(g):
    """把本轮必涂格全部「照一次、涂一格」地填完，返回涂对了几格。"""
    n = 0
    for (r, c) in sorted(g.board.must):
        if paint_ok(g, r, c) == "valid":
            n += 1
    return n


def reveal_once(g):
    """替玩家真按一次 Shift 并照出灰域 —— 2026-11-14 起这是**与老者对话的前置条件**。

    直接把 `reveal_used` 设成 True 是作弊：那样测的就不是真实链路了。
    这里按真键、走真逻辑，顺手把 M2 关掉。返回是否真的照到了。
    """
    if getattr(g, "reveal_used", False):
        return True
    g.board.reveal_around(*g.player.cell)            # 保证脚下有活，照得出来
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=0, scancode=225))
    auto_mono(g, 5)
    return bool(getattr(g, "reveal_used", False))


def clear_wave1(g):
    """第一幕第一波（左下定位图案 33 格）写完 + 跳过那一次迷你清屏，停在 BATTLE。

    2026-11-14 起第一幕是两波：`g.must` 开局只有 33 格，清一次屏之后才换成整张码的 100 格
    （`g.must_all`）。测试想测「整幕的 100 格」得先过这一道，否则断言会一直看到 33。
    返回 True 表示确实进了第二波。
    """
    fill_must(g)
    if getattr(g, "act1_wave", 2) == 2:
        return True                       # 已经自己触发过了（BATTLE 相位里会自动进 CLEAR）
    if g.state != "CLEAR":
        g.enter_clear()                   # 测试常直接停在 FREE_ROAM：手动发动这一次迷你清屏
        g.clear_phase = "wave"            # 跳过「必须站在坛内发光」那道门，测试不关心它
        g.clear_t = 0.0
        g.wave_r = 0.0
    for _ in range(600):
        auto_mono(g)
        g.update(1 / 60)
        if getattr(g, "act1_wave", 2) == 2:
            return True
    return False


def shot(g, name):
    os.makedirs(SHOT_DIR, exist_ok=True)
    g.draw()
    pygame.image.save(g.canvas, os.path.join(SHOT_DIR, name))
    return os.path.join(SHOT_DIR, name)


def check(name, cond, extra=""):
    RESULTS.append((name, bool(cond), extra))


def report(title):
    ok = 0
    print("=" * 62)
    print(title)
    print("=" * 62)
    for n, c, e in RESULTS:
        print(("  OK   " if c else "  FAIL ") + n + ("   " + e if e else ""))
        ok += 1 if c else 0
    print("-" * 62)
    print("  %d / %d passed" % (ok, len(RESULTS)))
    print("-" * 62)
    return ok == len(RESULTS)


def finish(title):
    sys.exit(0 if report(title) else 1)
