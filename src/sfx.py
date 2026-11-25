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
import random

# ⚠️ `wave` 在 pygbag 的 wasm 标准库里没有（`ModuleNotFoundError`），
# 所以只在真正合成 WAV 的函数里按需 import —— 网页版只读预渲染 ogg，不需要它。

# 采样率 / 位深。44100 是 SDL 混音最稳的档；16-bit 单声道够用。
_RATE = 44100
_CHANNELS = 1
_SAMPLE_WIDTH = 2

# mixer 初始化要用的公开采样率（`Game._Audio` 用它把设备锁到单声道，
# 不跟 sfx 的实际格式对齐的话，单声道 PCM 会被当成双声道交错播放）。
RATE = _RATE

# 网页版（pygbag）不在浏览器里现算音频：构建时导出成 22050Hz 的 wav，运行时直接加载。
# 折一半采样率能把 7 段 12 秒循环从 ~7.4MB 压到 ~3.7MB，听感上没区别。
WEB_RATE = 22050

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
    "sword": 0.46,
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


def _tone(n, f0, f1, wave_kind, env, vib=0.0, rate=_RATE):
    """合成 n 个采样点。wave_kind: 'square'/'sine'/'noise'/'tri'；vib 是颤音深度。

    `rate` 默认 44100（音效用）；音乐先用 11025 合成再升采样，省一半计算量。
    """
    freqs = _fade(f0, f1, n)
    if vib:
        freqs = [f * (1.0 + vib * math.sin(2 * math.pi * 5.0 * i / rate)) for i, f in enumerate(freqs)]
    out = [0.0] * n
    phase = 0.0
    for i, f in enumerate(freqs):
        phase += 2 * math.pi * f / rate
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


def _white_noise(n, seed):
    """固定种子的白噪（-1 ~ 1）。

    比 `_tone(..., "noise")` 真实：后者是**相位的函数**，本质仍是一个带音高的锯齿，
    叠在带通里会露出「电子嗡嗡」的底色 —— 挥剑的刃风必须是平谱噪声，才吹得起来。
    """
    rng = random.Random(seed)
    return [rng.uniform(-1.0, 1.0) for _ in range(n)]


def _swept_band(x, cutoffs, q=1.2):
    """Chamberlin 状态变量带通，截止频率逐采样点变化（做「扫过去」的刃风）。

    `cutoffs[i]` 是第 i 个采样点的中心频率；`q` 越小带宽越宽。
    """
    damp = 1.0 / max(0.5, q)
    low = 0.0
    band = 0.0
    out = [0.0] * len(x)
    for i, v in enumerate(x):
        f = 2.0 * math.sin(math.pi * min(cutoffs[i], _RATE * 0.22) / _RATE)
        high = v - low - damp * band
        band += f * high
        low += f * band
        out[i] = band
    return out


def _sword_swing():
    """挥剑：一声清脆的金属「唰」。

    2026-11-25 第二版（作者反馈「太沙」）：把噪声从主角降成配角 ——
      1. 白噪只留起手约 100ms 的窄带高频「气口」，幅度减半、截止抬高，
         听感是「空气被划开」，不是沙子；
      2. 金属层基频抬到 1400Hz，只留 1 / 2.76 / 5.40 三个分音，衰减压到 50~110ms，
         失谐副本从 +0.6% 收到 +0.3%（拍频更细，不会像沙锤）；
      3. 低频重量砍到 18%，只给一点挥砍的实感。
    时长 0.26s → 0.18s，起音 3ms → 1.5ms：更短、更亮、更干净。
    """
    dur = 0.18
    m = int(dur * _RATE)

    # 1) 刃风：一条很短的窄带高频。截止从 1.2k 冲到 5.2k，然后迅速消失
    noise = _white_noise(m, 20261125)
    cut = []
    for i in range(m):
        u = i / (m - 1)
        cut.append(1200.0 + 4000.0 * min(1.0, u / 0.45))
    air = _swept_band(noise, cut, q=2.2)
    for i in range(m):
        u = i / (m - 1)
        env = min(1.0, u / 0.06) * max(0.0, 1.0 - u / 0.55) ** 1.6
        air[i] *= env * 0.55

    # 2) 金属余振：更亮的基频、更短的分音
    ring = [0.0] * m
    for ratio, amp, tau in ((1.0, 0.34, 0.11), (2.76, 0.22, 0.075), (5.40, 0.10, 0.05)):
        for det in (1.0, 1.003):
            f = 1400.0 * ratio * det
            if f >= _RATE * 0.45:
                continue
            ph = 0.0
            step = 2.0 * math.pi * f / _RATE
            for i in range(m):
                t = i / _RATE
                ring[i] += math.sin(ph) * amp * math.exp(-t / tau) * (1.0 - math.exp(-t / 0.002))
                ph += step

    # 3) 低频重量：只给一点实感，别糊住高频
    m_low = int(0.07 * _RATE)
    weight = _tone(m_low, 120, 62, "sine", _envelope(m_low, 0.005, 0.85))
    weight = [v * 0.18 for v in weight]

    out = _mix(air, ring, weight)

    # 统一收尾包络：1.5ms 起音 + 25ms 淡出，去掉开关爆音
    attack = max(1, int(0.0015 * _RATE))
    fade_out = int(0.025 * _RATE)
    for i in range(m):
        if i < attack:
            out[i] *= i / attack
        elif i >= m - fade_out:
            out[i] *= (m - 1 - i) / fade_out
    return [out]


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
    import wave
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
        # 挥剑：一条扫过的刃风 + 非谐金属余振。不能像打击，得像**空挥**（没砍中也有声音）
        return _to_bytes(_render(_sword_swing(), _GAIN[name]), name)

    if name == "dull":
        # 干活被挡（手占着）：一记闷响，短、低、没有上扬 —— 不是错，是「做不了」
        m = n(0.09)
        tr = _tone(m, 110, 62, "tri", _envelope(m, 0.04, 0.7))
        nz = _tone(m, 300, 300, "noise", _envelope(m, 0.05, 0.8))
        return _to_bytes(_render([tr, [v * 0.18 for v in nz]], _GAIN[name]), name)

    raise KeyError("unknown sfx: %r" % name)


def build_pcm(name):
    """按名字合成，返回裸 PCM（16-bit 单声道）。

    `pygame.mixer.Sound(buffer=...)` 只认裸 PCM：直接塞 `build()` 的 WAV bytes 时，
    44 字节头会被当成采样播出去，单声道数据还会被当成双声道交错（时长腰斩、音色失真）。
    """
    import wave
    bio = io.BytesIO(build(name))
    w = wave.open(bio, "rb")
    try:
        return w.readframes(w.getnframes())
    finally:
        w.close()


def to_channels(pcm, channels):
    """把单声道 PCM 复制成 `channels` 声道（每声道同一份）。

    少数声卡不接受单声道，mixer 只能开成立体声；这时必须把数据补成双声道，
    否则又会被交错播放（时长腰斩、音色失真）。
    """
    if channels == 1:
        return pcm
    src = array.array("h")
    src.frombytes(pcm)
    out = array.array("h")
    for v in src:
        for _ in range(channels):
            out.append(v)
    return out.tobytes()


# ==== 背景音乐：每幕一段 12 秒无缝循环（2026-11-24）====
# 和音效共用同一套合成器。刻意**不做旋律性 BGM**（5 幕全程有大量叙事字幕，
# 旋律会抢台词），只做四层环境：
#   1) drone：根音 + 五度 + 八度，缓慢呼吸
#   2) 心跳 / 脉冲：低音正弦，按幕调密度
#   3) 稀疏高频点缀：五声音阶的短拨弦
#   4) 第三、四幕加一层噪声「扫描底」
# 无缝循环靠两件事：
#   - 所有声音写进**环形缓冲**，尾巴自动绕回开头；
#   - drone 频率对到 `1 / MUSIC_LOOP` 的整数倍，首尾相位一致，循环点不咔哒。
# 先按 11025Hz 合成，再复制成 mixer 的 44100Hz —— 环境音没有高频内容，
# 听不出差别，但 Python 的计算量减到四分之一。

MUSIC_LOOP = 12.0
MUSIC_RATE = 11025
MUSIC_TRACKS = ("title", "act1", "act2", "act3", "act4", "act5", "end")

_MUSIC_GAIN = 0.7

_MUSIC_SPEC = {
    # root 基音 Hz；scale 是相对 root 的半音；density 是「该出的拍里真出的比例」
    "title": dict(root=55.0, bpm=40, scale=(0, 7, 12, 19), drone=0.42, pulse=0.16,
                  pulse_every=4, blip=0.16, blip_every=2, density=0.55, noise=0.0, seed=11),
    "act1": dict(root=55.0, bpm=50, scale=(0, 3, 5, 7, 10, 12, 15), drone=0.44, pulse=0.20,
                 pulse_every=2, blip=0.20, blip_every=1, density=0.70, noise=0.0, seed=21),
    "act2": dict(root=58.27, bpm=60, scale=(0, 3, 5, 7, 10, 12, 15), drone=0.40, pulse=0.20,
                 pulse_every=1, blip=0.20, blip_every=1, density=0.85, noise=0.0, seed=31),
    "act3": dict(root=49.0, bpm=60, scale=(0, 3, 6, 7, 10, 12), drone=0.44, pulse=0.18,
                 pulse_every=1, blip=0.22, blip_every=2, density=0.60, noise=0.05, seed=41),
    "act4": dict(root=55.0, bpm=60, scale=(0, 2, 5, 7, 9, 12, 14), drone=0.38, pulse=0.20,
                 pulse_every=1, blip=0.22, blip_every=1, density=0.90, noise=0.10, seed=51),
    "act5": dict(root=41.2, bpm=40, scale=(0, 7, 12, 15, 19), drone=0.50, pulse=0.14,
                 pulse_every=4, blip=0.18, blip_every=2, density=0.45, noise=0.0, seed=61),
    "end": dict(root=55.0, bpm=40, scale=(0, 4, 7, 12, 16, 19), drone=0.44, pulse=0.12,
                pulse_every=4, blip=0.18, blip_every=2, density=0.50, noise=0.0, seed=71),
}

_MUSIC_CACHE = {}


def _loop_freq(f):
    """频率对到 1/MUSIC_LOOP 的整数倍：整段首尾相位一致，循环点不会咔哒。"""
    return max(1, int(round(f * MUSIC_LOOP))) / MUSIC_LOOP


def _decay_env(n, attack=0.004, power=5.0):
    """短音包络：快速起音 + 指数衰减。"""
    a = max(1, int(attack * MUSIC_RATE))
    return [min(1.0, i / a) * math.exp(-power * max(0, i - a) / max(1, n - a))
            for i in range(n)]


def _loop_add(buf, at, wave):
    """把一段波形叠加到环形缓冲的 `at` 处（越过末尾就绕回开头）。"""
    n = len(buf)
    at %= n
    end = at + len(wave)
    if end <= n:
        for i, v in enumerate(wave):
            buf[at + i] += v
    else:
        k = n - at
        for i in range(k):
            buf[at + i] += wave[i]
        for i in range(k, len(wave)):
            buf[i - k] += wave[i]


def _upsample(pcm, factor):
    """把低采样率的 PCM 每个采样复制 `factor` 份，升到 mixer 的采样率。"""
    src = array.array("h")
    src.frombytes(pcm)
    out = array.array("h")
    for v in src:
        for _ in range(factor):
            out.append(v)
    return out.tobytes()


def _build_music(name):
    spec = _MUSIC_SPEC[name]
    n = int(MUSIC_LOOP * MUSIC_RATE)
    root = spec["root"]
    beat = 60.0 / spec["bpm"]
    beats = int(round(MUSIC_LOOP / beat))
    buf = [0.0] * n

    # 1) drone：根音 + 五度 + 八度
    for semi, g in ((0, 1.0), (7, 0.55), (12, 0.30)):
        f = _loop_freq(root * (2.0 ** (semi / 12.0)))
        tr = _tone(n, f, f, "sine", [1.0] * n, rate=MUSIC_RATE)
        for i, v in enumerate(tr):
            buf[i] += v * g * spec["drone"]

    # 2) 呼吸：整段转两圈，首尾相位一致
    lfo_f = _loop_freq(2.0 / MUSIC_LOOP)
    lfo = _tone(n, lfo_f, lfo_f, "sine", [1.0] * n, rate=MUSIC_RATE)
    for i, v in enumerate(lfo):
        buf[i] *= 0.8 + 0.2 * v

    # 3) 心跳 / 脉冲
    if spec["pulse"] > 0:
        m = int(0.36 * MUSIC_RATE)
        pulse = _tone(m, 64, 38, "sine", _decay_env(m, 0.002, 6.0), rate=MUSIC_RATE)
        pulse = [v * spec["pulse"] for v in pulse]
        for b in range(0, beats, spec["pulse_every"]):
            _loop_add(buf, int(b * beat * MUSIC_RATE), pulse)

    # 4) 稀疏点缀
    rng = random.Random(spec["seed"])
    scale = spec["scale"]
    m = int(0.30 * MUSIC_RATE)
    for b in range(beats):
        if b % spec["blip_every"]:
            continue
        if rng.random() > spec["density"]:
            continue
        semi = scale[rng.randrange(len(scale))]
        f = _loop_freq(root * 4.0 * (2.0 ** (semi / 12.0)))
        note = _tone(m, f, f, "tri", _decay_env(m, 0.004, 5.5), rate=MUSIC_RATE)
        _loop_add(buf, int(b * beat * MUSIC_RATE), [v * spec["blip"] for v in note])

    # 5) 噪声扫描底
    if spec["noise"] > 0:
        m = int(0.5 * MUSIC_RATE)
        wash = _tone(m, 900, 300, "noise", _decay_env(m, 0.08, 4.0), rate=MUSIC_RATE)
        wash = [v * spec["noise"] for v in wash]
        for b in range(0, beats, 4):
            _loop_add(buf, int(b * beat * MUSIC_RATE), wash)

    pcm = _render([buf], _MUSIC_GAIN)
    return _upsample(pcm, _RATE // MUSIC_RATE)


def build_music(name):
    """整段循环的裸 PCM（44100 / 16-bit / 单声道）。首次合成后缓存，换幕只付一次。"""
    if name not in _MUSIC_CACHE:
        if name not in _MUSIC_SPEC:
            raise KeyError("unknown music: %r" % name)
        _MUSIC_CACHE[name] = _build_music(name)
    return _MUSIC_CACHE[name]
