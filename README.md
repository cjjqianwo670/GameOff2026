# DATA SHIFT

A tiny keyboard-only puzzle game: restore a corrupted QR code before the red eroders eat it.

Game Off 2026 entry · theme **SHIFT** · Python + pygame · **no external assets** (no images, no audio).

一个只用键盘的极简解谜小游戏：限时把中心 21×21 的「二维码」复原到关卡要求，同时把噪声压在上限内；
猩红色的「侵蚀体」从外围环不断涌入，每吃掉一个已涂黑的格子就自毁。5 关逐关解锁。

---

## 运行 Run

```bash
pip install pygame-ce     # 或 pygame，两者都能跑
python src/main.py        # 从项目根执行；也可以 python -m src.main
```

- Python 3.10+
- 本仓库在 PyCharm 里的解释器是 `.venv`（Python 3.11.5 + pygame 2.6.1），入口 `src/main.py`
- 代码在 `src/` 包里，模块之间用 `from src.xxx import ...`；`src/main.py` 顶部有路径引导，
  所以 `python src/main.py` 和 `python -m src.main` 两种方式都能启动
- 窗口按桌面可用空间自动等比缩放（内部逻辑画布固定 1000×1000，画完再整帧缩放，判定逻辑不受影响）
- 无存档：关掉游戏，关卡解锁进度归零

## 操作 Controls

| 键 | 作用 |
|---|---|
| `W` `A` `S` `D` | 逐格移动（按下即走一格，长按每 0.13s 走一格） |
| `J`（或空格） | 涂黑脚下格子；**按住 J 移动 = 边走边涂** |
| `K` | 抹除脚下格子（0.25s 灰色塌陷动画） |
| `R` | 局中：重开本关；结算页：失败重试 / 通关进下一关 |
| `Enter`（含小键盘） | 开始页进入选关页；选关页进入所选关卡 |
| `←` `→` / `A` `D` | 选关页切换高亮（移不出已解锁范围） |
| `Esc` | 局中/结算 → 选关页；选关页 → 开始页；开始页 → 退出 |
| `F1` | 调试信息（FPS / 坐标 / 目标格数 / 同屏怪物数） |

**鼠标只允许点菜单按钮**（开始页的 START、选关页的 1~5），游戏进行中没有任何鼠标操作。

## 关卡 Levels

| 关卡 | 需复原 | 时长 | 怪物/分 | 噪声上限 | 首怪延迟 |
|---|---|---|---|---|---|
| 1 | 70% | 180s | 15 | 0.25 | 2.0s |
| 2 | 72% | 170s | 20 | 0.22 | 2.0s |
| 3 | 75% | 160s | 25 | 0.20 | 1.5s |
| 4 | 78% | 150s | 30 | 0.18 | 1.5s |
| 5 | 80% | 140s | 35 | 0.15 | 1.0s |

前 30 秒（`PHASE 1`）可以涂整个 24×24 网格；30 秒后外围锁死（已涂黑的保留，没涂的不能再涂），
只能操作中心 21×21 目标区，同时弹出 1 秒 `PHASE SHIFT` 遮罩。

**进关有 2.1 秒开场动画**：完整的二维码先以纯黑呈现 → 整屏抖三下 → 黑格被震碎、四散后沉出屏幕
（这时网格全白）→ 灰色提示层浮现。这段时间**不计时、不出怪、不能涂**，动画结束才开始跑表。

评级：`S`（复原 ≥95% 且噪声 ≤3）／`A`（噪声 ≤ 上限 40%）／`B`（通关）／`F`（失败）。

## 项目结构 Structure

按职责拆成 9 个模块，统一放在 `src/` 包里，依赖单向，**没有循环 import**：

```
config ──> grid ──> board ──┐
   │          └──> entities ─┼──> game ──> main
   └──> qr ──────────────────┘        ↑
   └──> input_state ──────────────────┘
                        ui ───────────┘（game 调 ui 画，ui 只读 game）
```

| 文件 | 行数 | 职责 |
|---|---|---|
| `src/__init__.py` | 5 | 空包标记，让 `from src.xxx import ...` 成立 |
| `src/config.py` | 122 | 所有常量、颜色、关卡表、开场动画参数（连 pygame 都不 import） |
| `src/grid.py` | 41 | 坐标换算：`cell_to_rect` / `pos_to_cell` / `cell_center` / `to_target` |
| `src/qr.py` | 64 | 程序化生成 21×21「形似 QR」目标矩阵 |
| `src/board.py` | 80 | 棋盘状态、统计、涂改、抹除计时 |
| `src/input_state.py` | 49 | 键盘状态（只认 `scancode`，与输入法无关） |
| `src/entities.py` | 112 | `Player`（格子步进）+ `Monster`（寻路啃食） |
| `src/ui.py` | 349 | 所有 `draw_*`，函数第一个参数是 `Game`，只读不改状态 |
| `src/game.py` | 425 | `Game`：状态机 / 回合 / 关卡推进 / 开场动画 / 每帧更新 |
| `src/main.py` | 67 | 开窗口 + 主循环（含直接运行脚本时的路径引导） |

共 1314 行。**改数值只动 `config.py`，改界面只动 `ui.py`，改规则只动 `game.py`。**

## 状态 Status

M1 网格与涂改 · M2 二维码与提示层 · M3 怪物 · M4 阶段锁定与结算 · M5 菜单与遮罩 · M6 关卡与选关 —— 全部完成。
只剩 M7（PyInstaller 打包 + itch 页面）。

技术交接、踩过的坑、验证方法写在 [HANDOFF.md](HANDOFF.md)；个人开发日记在 [DEVLOG.md](DEVLOG.md)。
