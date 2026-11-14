# -*- coding: utf-8 -*-
"""跑全量验证脚本，**只有一个判据：每个脚本都打出 `N / N passed` 且退出码 0**。

为什么要有这个文件（2026-11-14 踩过）：
    当时用 `for f in ...; do python "$f" | grep FAIL; done` 判断 —— 只认「有 FAIL 行」。
    可是崩溃的脚本是「打一串 Traceback 然后退出」，它**既没有 FAIL 也没有 passed**，
    于是被算成通过：932 项里有 34 项根本没跑，总数掉到 898 才发现。

    FAIL  = 跑完了但没过
    崩溃  = 根本没跑完        ← 这两个都必须算红

用法：
    python _run_all.py              # 全部
    python _run_all.py act1         # 只跑文件名含 act1 的
    python _run_all.py --quiet      # 只打失败的
退出码：0 = 全绿；1 = 有红。
"""

import glob
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = 300


def parse(line):
    """从脚本输出里取最后一条 `N / M passed`。取不到就返回 None。"""
    best = None
    for ln in line.splitlines():
        ln = ln.strip()
        if ln.endswith("passed") and " / " in ln:
            head = ln.replace("passed", "").strip()
            a, _, b = head.partition(" / ")
            if a.strip().isdigit() and b.strip().isdigit():
                best = (int(a), int(b))
    return best


def run_one(path):
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, os.path.basename(path)],
                           cwd=HERE, capture_output=True, text=True,
                           timeout=TIMEOUT)
        out = (p.stdout or "") + (p.stderr or "")
        code = p.returncode
    except subprocess.TimeoutExpired:
        return False, "超时 %d 秒" % TIMEOUT, None, time.time() - t0
    dt = time.time() - t0

    got = parse(out)
    fails = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("FAIL")]
    crashed = "Traceback (most recent call last)" in out

    # 三条都必须满足：跑完了、全过、退出码 0
    if got is None:
        why = "没有输出 `N / N passed`（多半是崩了）" if crashed else "没有输出结果行"
        tail = [ln for ln in out.splitlines() if ln.strip()][-3:]
        return False, why + "  " + " | ".join(tail), None, dt
    if got[0] != got[1] or code != 0 or fails:
        why = "%d / %d passed" % got
        if fails:
            why += "  失败项: " + " ; ".join(f[4:].strip() for f in fails[:5])
        if crashed:
            why += "  （有 Traceback）"
        return False, why, got, dt
    return True, "%d / %d passed" % got, got, dt


def main(argv):
    quiet = "--quiet" in argv
    words = [a for a in argv if not a.startswith("--")]
    files = sorted(glob.glob(os.path.join(HERE, "_verify_act*.py")))
    if words:
        files = [f for f in files if any(w in os.path.basename(f) for w in words)]
    if not files:
        print("没找到匹配的验证脚本")
        return 1

    bad, total_ok, total_all, t0 = [], 0, 0, time.time()
    for path in files:
        name = os.path.basename(path)
        ok, why, got, dt = run_one(path)
        if got:
            total_ok += got[0]
            total_all += got[1]
        if ok:
            if not quiet:
                print("  OK   %-34s %-18s %5.1fs" % (name, why, dt))
        else:
            bad.append((name, why))
            print("  FAIL %-34s %-18s %5.1fs" % (name, why, dt))

    print("-" * 74)
    print("  %d 个脚本 / %d 项断言   用时 %.1fs" % (len(files), total_all, time.time() - t0))
    if bad:
        print("  !! %d 个脚本是红的：" % len(bad))
        for name, why in bad:
            print("     - %s  →  %s" % (name, why))
        return 1
    print("  全绿：%d / %d" % (total_ok, total_all))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
