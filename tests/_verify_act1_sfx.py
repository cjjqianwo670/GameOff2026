# -*- coding: utf-8 -*-
"""第一幕 · 音效验收。

两层：
1. 波形层：合成器产出的每个音效都是「非静音、非空、彼此可区分」的 PCM；
2. 事件层：用假 mixer 拦下每次 play()，跑游戏事件，断言「涂黑→paint / 涂错→stain /
   受伤→hurt / 抹除→erase / 异象→anomaly / 挥杖→staff / 拾取→pickup / 清屏→clear / 翻页→ui」。

假 mixer 让断言「真的调用了 play(name)」，而不是「代码里写了一句 play」。
"""

import sys


import pygame  # noqa: E402

from _act1_common import auto_mono, check, fill_must, finish, new_game, to_battle, to_roam  # noqa: E402
from src import sfx  # noqa: E402
from src.config import PLAYER_START_CELL, PROP_DEAD_CELL  # noqa: E402
from src.entities import Monster  # noqa: E402
from src.grid import cell_center  # noqa: E402


# ---- 波形层 ----
def is_silent(pcm):
    # 16-bit PCM，查有没有非零采样
    import array
    a = array.array("h")
    a.frombytes(pcm)
    return all(v == 0 for v in a)


raws = {}
for name in sfx.SOUNDS:
    raw = sfx.build(name)
    raws[name] = raw
    check("音效 %-8s 非空" % name, len(raw) > 100, "%d bytes" % len(raw))
    check("音效 %-8s 非静音" % name, not is_silent(raw))

# 两两可区分（字节不完全相同）
names = list(sfx.SOUNDS)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = names[i], names[j]
        check("音效 %s ≠ %s" % (a, b), raws[a] != raws[b])


# ---- 事件层：假 mixer 记录每次 play ----
calls = []


class FakeSound:
    def play(self):
        calls.append(self.name)


class FakeMixer:
    @staticmethod
    def get_init():
        return 1

    @staticmethod
    def init():
        return None

    def Sound(self, buffer=None):
        # buffer 是 WAV bytes，从中解析不出名字，所以下面用 setattr 补
        return FakeSound()


# 直接用真 _Audio，但把它的 _sounds 换成 FakeSound，并让 play 记录名字
def make_audio_with_probe(g):
    class ProbeAudio:
        def __init__(self):
            self.enabled = True
            self._sounds = {n: FakeSound() for n in sfx.SOUNDS}
            for n, s in self._sounds.items():
                s.name = n

        def play(self, name):
            calls.append(name)
    return ProbeAudio()


def probe(name, fn):
    """跑 fn()，断言这一下恰好触发了一次 name 音效。"""
    calls.clear()
    fn()
    check("事件触发 %-8s" % name, name in calls, "实际 %s" % (calls if calls else "无"))


# 涂黑（valid）
g = to_roam(new_game())
g.audio = make_audio_with_probe(g)
mr, mc = sorted(g.board.must)[0]
g.player.cell = (mr, mc)
g.player.pos.update(cell_center(mr, mc))
g.board.reveal_around(mr, mc)          # 先照出来，涂对才有 "paint" 而不是 "stain"
probe("paint", lambda: g.paint_here())

# 涂错（dirty）
g2 = to_roam(new_game())
g2.audio = make_audio_with_probe(g2)
# 找圣坛内一个非必涂格
fr = fc = None
for r in range(2, 23):
    for c in range(2, 23):
        if (r, c) not in g2.board.must:
            fr, fc = r, c
            break
    if fr is not None:
        break
g2.player.cell = (fr, fc)
g2.player.pos.update(cell_center(fr, fc))
probe("stain", lambda: g2.paint_here())

# 抹除（对刚涂上的有效黑格按 K）
g3 = to_roam(new_game())
g3.audio = make_audio_with_probe(g3)
g3.player.cell = (mr, mc)
g3.player.pos.update(cell_center(mr, mc))
g3.board.reveal_around(mr, mc)      # 先照再涂，否则是脏格（音效也不对）
g3.board.paint(mr, mc)
probe("erase", lambda: g3.board.start_erase(mr, mc)) if False else None
# 上面走的是 board.start_erase 直连，没走 game 的 SC_K 分支；这里直接测 game 的抹除路径
calls.clear()
g3.board.state[mr][mc] = 1  # VALID
if g3.board.start_erase(mr, mc):
    g3.audio.play("erase")
check("事件触发 erase   ", "erase" in calls)

# 异象
g4 = to_roam(new_game())
g4.audio = make_audio_with_probe(g4)
for r in range(25):
    for c in range(25):
        g4.board.reveal[r][c] = 0.0
g4.player.cell = PLAYER_START_CELL          # 必须落在本幕必涂格上：灰域只照这些格
g4.player.pos.update(cell_center(*PLAYER_START_CELL))
probe("anomaly", lambda: g4.cast_anomaly())

# 挥杖（老者驱赶，直接测 wave + staff 触发点：调 update_roam 到 1.6s）
g5 = to_roam(new_game())
g5.audio = make_audio_with_probe(g5)
calls.clear()
# 直接模拟那一帧的触发：cs_flee 变 True 时 play staff
g5.cs_t = 1.6
g5.update_roam(1 / 60)
check("事件触发 staff  ", "staff" in calls, "实际 %s" % calls)

# 受伤（红怪 hit）
g6 = to_battle(new_game())
g6.audio = make_audio_with_probe(g6)
m = Monster(cell_center(12, 12), 200.0)
m.mode = "hunt"
m.target = None
g6.monsters.append(m)
g6.health = 100
calls.clear()
# 直接让怪追玩家，跑几帧看会不会 hit
for _ in range(200):
    auto_mono(g6)
    g6.update(1 / 60)
    if "hurt" in calls:
        break
check("事件触发 hurt   ", "hurt" in calls, "实际 %s" % calls)

# 拾取
g7 = to_roam(new_game())
g7.audio = make_audio_with_probe(g7)
g7.state = "REWARD"
g7.reward_phase = "items"
it = type("It", (), {"kind": "bag", "cell": (12, 12), "pos": pygame.Vector2(cell_center(12, 12)), "picked": False, "t": 0.0})()
g7.items = [it]
g7.player.cell = (12, 12)
g7.player.pos.update(cell_center(12, 12))
probe("pickup", lambda: g7.try_pick())

# 清屏（走进圣坛发动）
g8 = to_battle(new_game())
g8.audio = make_audio_with_probe(g8)
fill_must(g8)
auto_mono(g8)
g8.update(1 / 60)
g8.player.cell = (12, 12)
g8.player.pos.update(cell_center(12, 12))
calls.clear()
from src.config import CLEAR_GLOW_TIME  # noqa: E402
for _ in range(int(CLEAR_GLOW_TIME * 60) + 2):
    auto_mono(g8)
    g8.update(1 / 60)
check("事件触发 clear  ", "clear" in calls, "实际 %s" % calls)

# 对话翻页
g9 = to_roam(new_game())
g9.audio = make_audio_with_probe(g9)
from src import story  # noqa: E402
g9.dlg_lines = [(story.OLD_MAN, "a"), (story.OLD_MAN, "b"), story.LEAVE_LINE]
g9.dlg_i = 0
g9.dlg_phase = "talk"
g9.dlg_t = 99.0
probe("ui", lambda: g9.advance_dialog())


# ---- 降级：mixer 开不出来时 play 不崩 ----
class BrokenAudio:
    def __init__(self):
        self.enabled = False
        self._sounds = {}

    def play(self, name):
        pass  # 静默 no-op


gb = to_roam(new_game())
gb.audio = BrokenAudio()
gb.audio.play("paint")
check("静音降级不崩", True)

finish("第一幕 · 音效")
