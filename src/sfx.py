# -*- coding: utf-8 -*-
"""音效：全部程序合成（`array` + `math` + `wave`，标准库），不依赖任何音频素材。

为什么要合成而不是找 .wav：
  - 铁律「不引入 numpy」—— 合成用标准库就够了；
  - 零版权、零外部资源，仓库自包含，能直接进 git；
  - 每个音效都是「一段可调参数的波形」，用户听不惯改几个数就重出，不用换素材。

设计意图（电子 / 数据废墟的调子，不拟真）：
  - 码序使涂黑 = 一声短促的「落子」滴答（低频方波，像数据被写下去）
  - 抹除    = 反着来的「收回」，频率往上滑（擦掉）
  - 脏格    = 一下短促的错音（失谐的方波，听得出「错了」）
  - 异象    = 一段带颤音的「扫描」气声（照出去的那种感觉）
  - 受伤    = 一声下坠的粗齿（掉血）
  - 红怪死  = 干巴巴的「啪」+ 下滑（它散了）
  - 拾取    = 两声上扬的小铃（拿到东西）
  - 清屏波  = 一个逐渐放大的咻——到顶点一记低鸣（圣坛发动）
  - 对话翻页 = 极轻的一声「咔」（推进台词，音量压很低，不烦）
  - 老者挥杖 = 一下呼啸（驱赶那两只红怪）

所有音效时长都很短（0.03 ~ 0.6 秒），短促、干、电子，符合「数据世界」而不是「自然世界」。
"""

import array
import io
import math
import wave

# 采样率 / 位深。44100 是 SDL 混音最稳的档；16-bit 单声道够用。
_RATE = 44100
_CHANNELS = 1
_SAMPLE_WIDTH = 2

# 全部音效名字（`Game._Audio` 按这份名单预生成，`_verify_act1_sfx.py` 也用它）
SOUNDS = ("paint", "erase", "stain", "anomaly", "hurt", "red_die",
          "pickup", "clear", "ui", "staff", "purple", "wipe", "dull", "sword")

# 各音效的基准音量（0~1），低于 1 是为了叠起来不炸。
_GAIN = {
    "paint": 0.34,
    "erase": 0.28,
    "stain": 0.32,
    "anomaly": 0.22,
    "hurt": 0.46,
    "red_die": 0.40,
    "pickup": 0.34,
    "clear": 0.52,
    "ui": 0.16,
    "staff": 0.30,
    "purple": 0.34,
    "wipe": 0.46,
    "dull": 0.30,
    "sword": 0.34,
}


def _envelope(n, attack, release):
    """给一段波形套 AD 包络（淡入 + 淡出），去掉爆音。

    返回一个列表，长度 = n：前 attack 段线性升到 1，后 release 段线性降到 0。
    """
    attack = max(1, int(attack * n))
    release = max(1, int(release * n))
    if attack + release > n:
        attack = release = n // 2
    env = []
    for i in range(n):
        if i < attack:
            v = i / attack
        elif i >= n - release:
            v = (n - 1 - i) / release
        else:
            v = 1.0
        env.append(v)
    return env


def _fade(f0, f1, n):
    """频率从 f0 线性滑到 f1（每个采样点一个值），用于上滑/下滑的音效。"""
    return [f0 + (f1 - f0) * (i / max(1, n - 1)) for i in range(n)]


def _tone(n, f0, f1, wave_kind, env, vib=0.0):
    """合成 n 个采样点。wave_kind: 'square'/'sine'/'noise'/'tri'；vib 是颤音深度。"""
    freqs = _fade(f0, f1, n)
    if vib:
        freqs = [f * (1.0 + vib * math.sin(2 * math.pi * 5.0 * i / _RATE)) for i, f in enumerate(freqs)]
    out = [0.0] * n
    phase = 0.0
    for i, f in enumerate(freqs):
        phase += 2 * math.pi * f / _RATE
        if wave_kind == "square":
            v = 1.0 if math.sin(phase) >= 0 else -1.0
        elif wave_kind == "tri":
            x = math.sin(phase)
            v = 2.0 / math.pi * math.asin(x)
        elif wave_kind == "noise":
            # 伪随机：固定种子，同一音效每次一样，不会每次都变
            v = math.sin(phase * 12.9898) * 43758.5453
            v = v - math.floor(v) - 0.5
            v *= 2.0
        else:  # sine
            v = math.sin(phase)
        out[i] = v * env[i]
    return out


def _mix(*tracks):
    """把多段波形按采样点相加（可重叠），用于「两个音叠加」的音效。"""
    n = max((len(t) for t in tracks), default=0)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def _render(tracks, gain, clip=0.9):
    """把 tracks（可单个列表或多个）混成 16-bit PCM 字节，返回 pygame 能吃的 bytes。"""
    n = max((len(t) for t in tracks), default=0)
    if n == 0:
        return b""
    samples = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            samples[i] += v
    # 软限幅：超过 ±clip 就往回收，避免削顶破音
    peak = max(abs(v) for v in samples) or 1.0
    if peak > clip:
        k = clip / peak
        samples = [v * k for v in samples]
    buf = array.array("h")
    for v in samples:
        buf.append(int(max(-1.0, min(1.0, v * gain)) * 32767))
    return buf.tobytes()


def _to_bytes(pcm, name):
    """给纯 PCM bytes 套上 WAV 头，转成 pygame.mixer.Sound 能读的 bytes。"""
    bio = io.BytesIO()
    w = wave.open(bio, "wb")
    w.setnchannels(_CHANNELS)
    w.setsampwidth(_SAMPLE_WIDTH)
    w.setframerate(_RATE)
    w.writeframes(pcm)
    w.close()
    return bio.getvalue()


def build(name):
    """按名字合成一个音效，返回 WAV bytes。名字不对会抛 KeyError（尽早暴露）。"""
    n = lambda sec: int(sec * _RATE)

    if name == "paint":
        # 落子：低频方波，短促，微微上扬（写下去的感觉）
        m = n(0.05)
        tr = _tone(m, 130, 200, "square", _envelope(m, 0.05, 0.45))
        return _to_bytes(_render([tr], _GAIN[name]), name)

    if name == "erase":
        # 抹除：频率往上滑的短哨（擦掉、收回）
        m = n(0.06)
        tr = _tone(m, 300, 640, "tri", _envelope(m, 0.06, 0.5))
        return _to_bytes(_render([tr], _GAIN[name]), name)

    if name == "stain":
        # 脏格：失谐的两个方波叠一起，短促刺耳（错了）
        m = n(0.07)
        a = _tone(m, 196, 196, "square", _envelope(m, 0.04, 0.5))
        b = _tone(m, 209, 209, "square", _envelope(m, 0.04, 0.5))
        return _to_bytes(_render([a, b], _GAIN[name]), name)

    if name == "anomaly":
        # 异象：一段扫描气声，音量先升后降（照出去）
        m = n(0.28)
        tr = _tone(m, 720, 1280, "sine", _envelope(m, 0.35, 0.55), vib=0.012)
        # 混一点点噪声，让它像「信号」而不是纯音
        nz = _tone(m, 900, 900, "noise", _envelope(m, 0.3, 0.6))
        return _to_bytes(_render([tr, [v * 0.25 for v in nz]], _GAIN[name]), name)

    if name == "hurt":
        # 受伤：下坠的粗方波（掉血、被咬）
        m = n(0.18)
        tr = _tone(m, 320, 90, "square", _envelope(m, 0.02, 0.4))
        return _to_bytes(_render([tr], _GAIN[name]), name)

    if name == "red_die":
        # 红怪死：短促的「啪」+ 下滑，带点噪声（它散了）
        m = n(0.12)
        thump = _tone(m, 160, 55, "square", _envelope(m, 0.02, 0.6))
        nz = _tone(m, 800, 800, "noise", _envelope(m, 0.05, 0.7))
        return _to_bytes(_render([thump, [v * 0.5 for v in nz]], _GAIN[name]), name)

    if name == "pickup":
        # 拾取：两声上扬的小铃（拿到东西）
        m = n(0.07)
        a = _tone(m, 880, 1320, "sine", _envelope(m, 0.06, 0.5))
        b = _tone(m, 1320, 1760, "sine", _envelope(m, 0.06, 0.5))
        return _to_bytes(_render([a, b], _GAIN[name]), name)

    if name == "clear":
        # 清屏：一个逐渐放大的咻，到顶点一记低鸣（圣坛发动）
        m = n(0.55)
        whoosh = _tone(m, 180, 1500, "sine", _envelope(m, 0.2, 0.35))
        boom = _tone(m, 55, 55, "sine", _envelope(m, 0.05, 0.6))
        return _to_bytes(_render([whoosh, [v * 0.7 for v in boom]], _GAIN[name]), name)

    if name == "ui":
        # 对话翻页：极轻一声「咔」（不抢台词）
        m = n(0.025)
        tr = _tone(m, 900, 1200, "square", _envelope(m, 0.2, 0.6))
        return _to_bytes(_render([tr], _GAIN[name]), name)

    if name == "staff":
        # 老者挥杖：一下呼啸（驱赶那两只红怪）
        m = n(0.3)
        tr = _tone(m, 500, 180, "tri", _envelope(m, 0.1, 0.5))
        return _to_bytes(_render([tr], _GAIN[name]), name)

    if name == "purple":
        # 紫怪进场：一记低沉的双音，像什么东西在深呼吸（不刺耳，但要听得见）
        m = n(0.34)
        low = _tone(m, 74, 62, "sine", _envelope(m, 0.25, 0.45))
        up = _tone(m, 148, 124, "tri", _envelope(m, 0.3, 0.5))
        return _to_bytes(_render([low, [v * 0.45 for v in up]], _GAIN[name]), name)

    if name == "wipe":
        # 清行：一整条被抹掉 —— 下坠的低鸣 + 一层噪声冲刷
        m = n(0.45)
        body = _tone(m, 260, 58, "square", _envelope(m, 0.05, 0.55))
        wash = _tone(m, 700, 220, "noise", _envelope(m, 0.15, 0.5))
        return _to_bytes(_render([body, [v * 0.55 for v in wash]], _GAIN[name]), name)

    if name == "sword":
        # 挥剑：一道极短的高频"唰" + 一点金属泛音。不能像打击，得像**空挥**（没砍中也有声音）
        m = n(0.16)
        air = _tone(m, 1900, 700, "noise", _envelope(m, 0.02, 0.75))
        ring = _tone(m, 2400, 2100, "tri", _envelope(m, 0.01, 0.6))
        return _to_bytes(_render([air, [v * 0.45 for v in ring]], _GAIN[name]), name)

    if name == "dull":
        # 干活被挡（手占着）：一记闷响，短、低、没有上扬 —— 不是错，是「做不了」
        m = n(0.09)
        tr = _tone(m, 110, 62, "tri", _envelope(m, 0.04, 0.7))
        nz = _tone(m, 300, 300, "noise", _envelope(m, 0.05, 0.8))
        return _to_bytes(_render([tr, [v * 0.18 for v in nz]], _GAIN[name]), name)

    raise KeyError("unknown sfx: %r" % name)
