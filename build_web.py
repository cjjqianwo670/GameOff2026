# -*- coding: utf-8 -*-
"""构建网页版（pygbag）到 `web_build/build/web`。

做的事情：
  1. 组装一个干净的 staging 目录（`web_build/`）：`src/` + `web/main.py`；
  2. **预渲染音频**：sfx 与 7 段背景循环导出成 22050Hz 单声道 wav
     （浏览器里现算要慢 5~15 倍，切幕会卡）；
  3. 调用 pygbag 打包成 WebAssembly。

用法（仓库根目录）：
    .venv/Scripts/python.exe build_web.py
产物：
    web_build/build/web/index.html   ← 用任意静态服务器打开
"""

import array
import importlib.util
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.join(ROOT, "web_build")
sys.path.insert(0, ROOT)

from src import sfx                                   # noqa: E402

try:
    import imageio_ffmpeg                             # 构建期依赖：只用来转 OGG
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:                                     # pragma: no cover - 构建机提示
    FFMPEG = None

APP_W, APP_H = 1088, 800


def write_ogg(path, pcm, rate):
    """原始 PCM → OGG(Vorbis)。pygbag 明确拒绝 wav（`--disable-sound-format-error` 只是绕过检查）。"""
    if not FFMPEG:
        raise SystemExit("缺少 imageio-ffmpeg：先运行 pip install imageio-ffmpeg")
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-f", "s16le",
           "-ar", str(rate), "-ac", "1", "-i", "pipe:0",
           "-c:a", "libvorbis", "-q:a", "4", path]
    subprocess.run(cmd, input=pcm, check=True)


def half_rate(pcm):
    """44100 → 22050：隔点取样。体积减半，这批音效/环境音听不出差别。"""
    src = array.array("h")
    src.frombytes(pcm)
    return array.array("h", src[::2]).tobytes()


def build_audio(dst):
    os.makedirs(dst, exist_ok=True)
    rate = sfx.WEB_RATE
    for name in sfx.SOUNDS:
        write_ogg(os.path.join(dst, "sfx_%s.ogg" % name), half_rate(sfx.build_pcm(name)), rate)
    for name in sfx.MUSIC_TRACKS:
        write_ogg(os.path.join(dst, "music_%s.ogg" % name), half_rate(sfx.build_music(name)), rate)
    total = sum(os.path.getsize(os.path.join(dst, f)) for f in os.listdir(dst))
    print("audio: %d files, %.1f MB" % (len(os.listdir(dst)), total / 1048576.0))


def vendor_segno():
    """segno 是纯 Python：放进 `src/` 随包分发，并把 web 包里的 `import segno` 改掉。

    不能保留顶层 `import segno`：pygbag 的导入钩子看到它就去 PyPI 现装
    （还会拉一串构建依赖，既慢又依赖公网）。改成 `from src import segno` 后纯走本地包。
    """
    spec = importlib.util.find_spec("segno")
    if spec is None:
        raise SystemExit("缺少 segno：先在 .venv 里 pip install segno")
    shutil.copytree(os.path.dirname(spec.origin), os.path.join(STAGE, "src", "segno"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # segno/__init__ 会 import writers，而 writers 依赖 xml.sax（pygbag 的 wasm 标准库没有）。
    # 游戏只调 segno.make 拿矩阵，从不写 SVG/PNG，摘掉 writers 不影响。
    init = os.path.join(STAGE, "src", "segno", "__init__.py")
    text = open(init, encoding="utf-8").read()
    if "from . import writers, utils" not in text:
        raise SystemExit("segno/__init__.py 的写法变了，打包脚本需要同步更新")
    open(init, "w", encoding="utf-8").write(
        text.replace("from . import writers, utils", "from . import utils", 1))
    qr = os.path.join(STAGE, "src", "qr.py")
    src_text = open(qr, encoding="utf-8").read()
    if "\nimport segno" not in src_text:
        raise SystemExit("src/qr.py 里没找到 `import segno`，打包脚本需要同步更新")
    open(qr, "w", encoding="utf-8").write(
        src_text.replace("\nimport segno", "\nfrom src import segno", 1))
    print("segno: vendored into src/ (import rewritten)")


def main():
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)

    shutil.copytree(os.path.join(ROOT, "src"), os.path.join(STAGE, "src"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(os.path.join(ROOT, "web", "main.py"), os.path.join(STAGE, "main.py"))
    vendor_segno()
    build_audio(os.path.join(STAGE, "src", "assets", "audio"))

    cmd = [sys.executable, "-m", "pygbag", "--build",
           "--width", str(APP_W), "--height", str(APP_H),
           "--title", "DATA SHIFT", "--ume_block", "0",
           "main.py"]
    print(" ".join(cmd))
    subprocess.run(cmd, cwd=STAGE, check=True)
    print("web build ->", os.path.join(STAGE, "build", "web"))


if __name__ == "__main__":
    main()
