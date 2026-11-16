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


def clear_board(g, limit=1200):
    """把**当前这一块板块**写满，推进到下一块（或整幕收尾）。

    第一幕是四块板块（BL 34 → TL 67 → TR 100 → BR 0 格），所以「写满一次」不再等于整幕完成。
    返回 True 表示确实推进了（`act1_wave` 变大，或者进了 REWARD / END）。
    """
    from src.grid import cell_center

    # 清屏的发光段要求玩家站在坛内。测试常把人挪到坛外（贴道具、贴老者），
    # 那会让清屏**永远卡在 glow**；真实玩法里玩家出不去，所以这里直接把人挪回来。
    if not g.board.in_altar(*g.player.cell):
        r, c = sorted(g.must)[0]
        g.player.cell = (r, c)
        g.player.pos.update(cell_center(r, c))
    wave0 = getattr(g, "act1_wave", 1)
    fill_must(g)
    for _ in range(limit):
        auto_mono(g)
        g.update(1 / 60)
        if getattr(g, "act1_wave", 1) != wave0 or g.state in ("REWARD", "END"):
            return True
    return False


def clear_wave1(g):
    """（旧名，保留）把第一块板块（BL，34 格）写完并推进到 TL。"""
    return clear_board(g)


def all_boards(g, limit=6):
    """把四块板块依次写完，停在 REWARD / END。返回停下来的状态。"""
    for _ in range(limit):
        if g.state in ("REWARD", "END"):
            break
        if not clear_board(g):
            break
    return g.state


def oldman_cell():
    """第一幕老者的站位（在第 3~5 幕是另一个常量）。"""
    from src.config import OLDMAN_CELL_ACT1
    return OLDMAN_CELL_ACT1


def go_to_oldman(g):
    """站到老者旁边（他左边一格，平地/板块上都可以站），返回距离。

    2026-11-14：第一幕他站在玩家板块 BL 的**左侧空地**上（`OLDMAN_CELL_ACT1`），
    不再在 `(1,12)`。测试里凡是「走到老者跟前喊话」的地方统一走这里。
    """
    from src.grid import cell_center
    r, c = oldman_cell()
    cell = (r, max(2, c + 1))                 # 他右边一格：那是 BL 的左沿
    g.player.cell = cell
    g.player.pos.update(cell_center(*cell))
    return g.oldman_dist()


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
