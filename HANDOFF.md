# HANDOFF —— 技术交接与工作日志

> 给「下一个接手的 AI」和「未来的自己」看。只写**与当前代码一致**的事实；改了代码请顺手改这里。
> 最后更新：2026-11-07 17:20 · 代码在 `src/` 下，9 个模块 + `__init__.py`，共 1372 行

---

## 0. 三条最快的上手信息

- 代码在 **`src/`** 包里（`from src.xxx import ...`）；解释器 `.venv`（Python 3.11.5 + pygame 2.6.1），入口 `src/main.py`
- 跑起来（都在**项目根目录**执行）：`python src/main.py` 或 `python -m src.main`；**改数值只改 `src/config.py`**
- 中文技术规格书（1253 行，规则、数值、设计理由最全）在仓库**之外**：
  `D:/Al_WorkPlace/WorrkBuddy_WorkPlace/game尝试/GameOff2026_SHIFT_TechSpec_v2.1.md`

## 1. 进度

M1 网格与涂改 · M2 二维码与提示层 · M3 怪物 · M4 阶段锁定与结算 · M5 菜单与遮罩 · M6 关卡与选关：**全部完成**。
只剩 **M7**（PyInstaller 打包 + itch 页面）。

## 2. 结构与边界（最重要）

按职责拆成 9 个模块，**统一放在 `src/` 包内**，模块之间一律 `from src.xxx import ...`：

```
config ──> grid ──> board ──┐
   │          └──> entities ─┼──> game ──> main
   └──> qr ──────────────────┘        ↑
   └──> input_state ──────────────────┘
                        ui ───────────┘（game 调 ui 画，ui 只读 game）
```

| 文件 | 行数 | 职责 | 允许 import |
|---|---|---|---|
| `src/__init__.py` | 5 | 空包标记，让 `from src.xxx import ...` 成立 | 无 |
| `src/config.py` | 132 | 常量 / 颜色 / `LEVELS` / 开场动画参数 | 无（连 pygame 都不用） |
| `src/grid.py` | 41 | 坐标换算 4 个函数 | pygame, src.config |
| `src/qr.py` | 64 | 生成 21×21 目标矩阵 | src.config |
| `src/board.py` | 94 | 棋盘状态、`stats()`、涂改、抹除计时 | src.config, src.grid |
| `src/input_state.py` | 49 | 键盘状态（只认 scancode） | pygame, src.config |
| `src/entities.py` | 133 | `Player` + `Monster`（红怪吃一格 / 紫怪清一行） | pygame, src.config, src.grid |
| `src/ui.py` | 350 | 所有 `draw_*`（首参 `Game`，只读） | pygame, src.config, src.grid（`Game` 仅 `TYPE_CHECKING`） |
| `src/game.py` | 437 | `Game`：状态机 / 回合 / 关卡 / 开场动画 / 每帧更新 | 全部业务模块 + ui |
| `src/main.py` | 67 | 开窗口 + 主循环（顶部有直接运行脚本的路径引导） | pygame, src.config, src.game |

三条不许破的边界：

1. **数值只进 `config.py`**，别处不写魔法数字
2. **画法只进 `ui.py`**：`game.py` 里不许出现 `pygame.draw`；`ui.py` 不许改 `g.xxx` 状态
3. **依赖单向**，不许循环 import（`ui.py` 那句 `from src.game import Game` 在 `if TYPE_CHECKING:` 里，运行时不执行）

> `src/main.py` 顶部有 3 行引导：`if __package__ in (None, ""): sys.path.insert(0, 项目根)`。
> 没有它，`python src/main.py` 会因为 `sys.path` 里只有 `src/` 而报 `No module named 'src'`。**别删。**

## 3. 状态机与键位

```
TITLE ──(Enter / 点 START)──> SELECT ──(Enter / 点关卡)──> PLAY ──(时间到)──> RESULT
  │                             ↑  ↓                          │                 │
  │(Esc 退出)                   │  └──(Esc)──> TITLE           │(Esc)            │(Esc)
  │                             └────────── SELECT <───────────┘                 │
  └──────────────────────────── SELECT <──────────(Esc / 末关通关 R)─────────────┘
```

- `PLAY` + `R` = 重开本关；`RESULT` + `R` = 失败重试 / 通关进下一关 / 末关回选关页
- **`PLAY` 内部还有一段开场动画**：`intro_t > 0` 时不走正常更新（不计时 / 不出怪 / 不能涂 / 不响应移动），
  只跑 `update_intro()`；动画放完才 `show_banner("LEVEL n")` 并开始计时
- 解锁：`unlocked` 初始 1，通关时 `unlocked = max(unlocked, min(5, level + 1))`，**只存内存**
- 鼠标只用于 `TITLE` / `SELECT` 的按钮点击与悬停；`PLAY` 里没有任何鼠标逻辑
- 窗口可能被等比缩小，鼠标坐标必须 `/ self.scale` 换算回逻辑坐标

## 4. 数值（想调难度只看这里）

`config.py` 的 `LEVELS`：`cover`（需复原比例）/ `time`（秒）/ `spawn`（红怪每分钟）/ `noise`（噪声上限比例）/ `delay`（首怪延迟秒）/ `purple`（紫怪数量，0 = 这一关没有）。

| 关卡 | cover | time | spawn | purple | noise | delay |
|---|---|---|---|---|---|---|
| 1 | 70% | 180s | 15 | 0 | 0.25 | 2.0s |
| 2 | 72% | 170s | 20 | **3** | 0.22 | 2.0s |
| 3 | 75% | 160s | 25 | 0 | 0.20 | 1.5s |
| 4 | 78% | 150s | 30 | 0 | 0.18 | 1.5s |
| 5 | 80% | 140s | 35 | 0 | 0.15 | 1.0s |

**紫怪（第二关起）**：跟红怪共用寻路与选目标，只有「撞上黑格那一刻」不同 —— 红怪 `force_white` 吃一格，
紫怪调 `Board.clear_row(r)` 把整行黑格清成白色（灰提示是 target 推出来的，会自动重新出现，玩家必须重涂）。
数量由 `LEVELS[i]["purple"]` 决定，刷新时刻在 `new_round()` 里排好（前 `PURPLE_SPAWN_WINDOW`=150s 内的随机时刻），
出生点走同一个 `spawn_monster()`、在虚线上随机。相关常量：`PURPLE_SPEED 56` / `PURPLE_RADIUS 10` /
`PURPLE_IDLE_LIMIT 60`（没黑格时能等更久）/ `PURPLE_SPAWN_MARGIN 6`（不会卡在最后 6 秒才刷）。

其他关键值：抹除 `ERASE_CAST = 0.25s` · 第 30 秒锁外围 `PHASE1_DURATION` · 横幅 1s · 怪物速度 62（±12% 抖动）·
啃食距离 6px · 场上无黑格 12s 后自毁 · 格子 28px / **网格 25×25** / 目标 21×21（正居中，四边各 2 格）·
评级 S（复原 ≥95% 且噪声 ≤3）/ A（噪声 ≤ 上限 40%）/ B（通关）/ F（失败）。

**开场动画**（进关先放，共 2.10s，期间不计时）：

| 常量 | 值 | 含义 |
|---|---|---|
| `INTRO_SHOW` | 0.50s | 完整黑码停留；最后 `SHAKE_LEAD × SHAKE_STEP` = 0.21s 开始抖 |
| `INTRO_FALL` | 1.20s | 碎片爆散 + 下沉，必须够长让碎片全部落出屏幕 |
| `INTRO_FADE` | 0.40s | 灰色提示层从 alpha 0 淡入到满 |
| `SHAKE_STEP` / `SHAKE_SEQ` | 0.07s / 6 组偏移 | 抖 6 下、幅度递减；固定序列，不用 sin |
| `SHAKE_LEAD` | 3 | 震碎**之前**先抖几下（所以是「抖两三下再碎」） |
| `DEBRIS_GRAVITY` | 1800 | 碎片重力 px/s²；改它就要同步改 `INTRO_FALL` |
| `DEBRIS_SPEED` / `DEBRIS_UP` / `DEBRIS_JITTER` | 110~260 / 120 / 60 | 爆散初速、向上抛偏置、水平随机 |

## 5. 踩过的坑（别重犯）

1. **`SC_ENTER` 必须是 40**。原来写成 28，而 SDL2 里 28 是字母 **Y** → 按回车没反应、按 Y 反而能进关。
   固定表：字母 A=4…Z=29，数字 1=30…0=39，Return=40，Esc=41，Space=44，F1=58，←=80，→=79。**别凭记忆敲数字。**
2. **`generate_target()` 的重摇必须有上限**（`ALPHA_TRY=40`）：信息区填充率 0.5 永远够不到 0.70 的阈值，
   否则会无限递归、`RecursionError`。
3. **`draw_result()` 必须先 `s.fill(C_BG)`**，否则结算页会叠在上一帧棋盘上。这个 bug 只有「先画一帧游戏再切结算」才暴露。
4. **白底不要逐格 `fill` 576 次**：一次铺满整块网格，再补锁定格（实测 draw 9.2ms → 5.2ms）。
5. **`claims` 占用表必须在四条路径回收**：吃掉 / 改道 / 超时自毁 / 结算。漏一条会越积越大，后续的怪误以为“全被占了”。
6. **鼠标坐标要 `/ self.scale`**（窗口被等比缩放过），否则点击位置整体偏移。
7. pygame-ce 2.5.8 **没有** `set_window_size` / `get_scancode_from_key`，别指望运行时换算或改窗口大小。
8. **代码在 `src/` 里就要用 `from src.xxx import ...`**。曾经混着 `from src.board` 和 `from config`，
   结果 `python src/main.py` 报 `No module named 'src'`、`python -m src.main` 报 `No module named 'config'`，
   **两种启动方式同时挂**。改 import 时全套一起改，别只改一半。
9. **开场碎片不能画成纯黑**：黑方块飞出白网格、落到深色背景上就完全看不见，只剩描边像空心框。
   用 `C_MISSING` 实心 + `C_CELL_LINE` 描边 1px，两种底色上都读得出来。
10. **开场动画期间别画玩家**：角色会浮在碎码中间很怪。`ui.draw_world()` 里 `if g.intro_t <= 0: draw_player(...)`。
11. **`INTRO_FALL` 必须覆盖最坏下落时间**：重力 1800 时，最上一行、带 120 向上初速的碎片要约 1.18s 才出屏，
    所以取 1.20s。否则灰码淡入时天上还有碎片，看起来像没碎干净。
12. **整帧抖动不要改绘制坐标**：先把画面正常画到 `canvas`，再用 `apply_shake()` 借 `shake_buf` 中转、
    按偏移重贴一次，四周露 `C_BG`。用 `sin` 的话帧率一抖、采样点就变，会忽大忽小，所以用固定序列。
13. **改网格尺寸只动 `config.py` 三个常量**：`GRID_N`、`GRID_ORIGIN`、`TARGET_OFFSET`（外加 `GRID_PX` 的注释）。
    现在是 25×25：`GRID_ORIGIN=(150,150)`（=(1000−25×28)/2）、`TARGET_OFFSET=(2,2)`。
    **`GRID_N − TARGET_N` 必须是偶数**，21×21 才可能正居中；24×24 时差 3，只能左/上留 1 格。

## 6. 怎么验证（别只看代码）

```bash
pip install pygame-ce          # 已有 .venv 则直接用 .venv/Scripts/python.exe
python src/main.py             # 正常游玩（或 python -m src.main，都在项目根执行）
```

无窗口渲染（改界面后必须做，别靠肉眼读代码）：

```python
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, "D:/GameOff/GameOff2026")   # 让 from src.xxx 能导入
# ... 然后 pygame.image.save(win, "shot.png") 出图看画面
```

- 改界面前后**截图 md5 比对**；怪物位置要固定 `g.rng = random.Random(n)`，否则每次都不一样
- **20 项逻辑回归**：scancode 全表 / J 涂 K 抹 / 怪物吃格自毁 / 无黑格 12s 自毁 / 30s 锁定 / 阶段横幅 /
  S·F 评级 / 菜单回车（含小键盘 88）/ Y 键无副作用 / 通关解锁 / R 进下一关 / 结算清屏 /
  第 5 关 140s 整局 / `claims` 归零 / 开场动画期间 elapsed 不动 / 开场绘制 <16.6ms
  - 测玩法时记得 **`g.intro_t = 0`** 跳过开场动画，否则 `update()` 会一直停在动画阶段
- 开场动画专项检查：抖动脉冲出现在震碎**之前**（约提前 0.21s）；碎片峰值 = 目标黑格数（约 219 块）；
  **淡入开始那一刻碎片数必须为 0**；动画结束后跑 1 秒 `elapsed == 1.00`
- 性能基线：局内 3.2ms/帧、开场碎片期 4.9ms、开始页 2.2、选关页 2.15、结算 2.4（60FPS 预算 16.6ms）

## 7. 铁律

- 只依赖 `pygame` + 标准库（`random`），不引入 numpy / PIL / qrcode
- 不用 asyncio；普通 `while` + `clock.tick(60)`
- **不做粒子 / 残影**；怪物就是一个 `draw.circle`。
  **震屏只有一处例外：关卡开场动画**（用户明确要求，见 §4 开场动画参数），别处一律禁止
- 界面文字**全部大写 ASCII**；字体只建一次（`pygame.font.Font(None, size)`）
- 键盘只用 `event.scancode`；初始化 `pygame.key.stop_text_input()`；`WINDOWFOCUSLOST` 清空按键集合
- 涂改只作用于**脚下这一格**；鼠标只允许点菜单按钮
- 数值只在 `config.py`，画法只在 `ui.py`，规则只在 `game.py`
- 代码都在 `src/` 包内，import 一律 `from src.xxx import ...`

## 8. 下一步

1. **M7 打包**：`pyinstaller --onefile --windowed src/main.py`（`src/main.py` 顶部有路径引导，
   打包后也能找到 `src.*` 模块）；打完记得在干净机器上试跑一次
2. 解锁进度不落盘，重开归零；要持久化就存一个小 txt（代价：多一个外部文件）
3. 平衡待试玩：出怪 15/分时同屏常常只有 1~2 只，压迫感偏弱 → 优先调 `LEVELS[i]["spawn"]`，**别动胜利条件**
4. 已知缺口：无音效；结算页只有数字，没有趋势图；开场动画时长 2.1s 偏长，重试多的话可以把 `INTRO_*` 调短

---

## 9. 工作日志（技术向，最近在上）

### 2026-11-08 · 紫怪（第二关）：撞到黑格清掉整行

- 需求：第二关在红怪之外加一个紫怪，撞到黑格后让**那一整行变白**（灰色提示不动，逼玩家重涂这一行）；
  第 2 关数量 3 只（要能调）；刷新时刻是开局前 2 分半内的随机时刻；出生点在虚线上随机。
- 做法：`Monster.__init__(pos, speed, kind="red")`，紫怪只是多一个 `kind`；寻路、选目标、`claims` 全复用。
  `update()` 里唯一的分叉：
  ```python
  if self.kind == "purple":
      board.clear_row(self.target[0])
  else:
      board.force_white(*self.target)
  ```
  颜色/半径/闲置超时都在构造时按 `kind` 取，所以 `ui.py` 直接画 `m.color` / `m.radius`，不用判断类型。
- **`clear_row` 只动 `BLACK`**：白格本来就是白的；灰提示是从 `target` 推出来的，清完后这些格子
  又变回「该黑且还白」，提示自动回来 —— 这一行等于白涂。这正是「灰色格子别被覆盖成白色」的要求。
- 刷怪时刻：`new_round()` 里排好 `purple_times = sorted(rng.uniform(1.0, span) ...)`，
  `span = min(PURPLE_SPAWN_WINDOW, duration - PURPLE_SPAWN_MARGIN)`，`update()` 到点各刷一只。
  比「每秒抽一次骰子」更稳：数量精确等于 `purple`，时刻可复现、可测试。
- 验证：13 项紫怪专项（数量/窗口/30 次采样/整局只刷 3 只/清整行且不动其它行/生效后自毁/提示全回来/
  红怪仍只吃一格）+ 26 项原回归全过；8 只怪同屏 4.48ms/帧。
- 截图确认：紫怪与红怪颜色可区分；清行那一下整行闪 0.15s，随后灰色提示重新出现。


### 2026-11-08 · 网格 24×24 → 25×25，二维码正居中

- 用户要求「白色网格改成 25×25，21×21 的二维码放正中」。改完的好处是**四边各留 2 格**、完全对称；
  原来 24×24 时 24−21=3 是奇数，只能左/上留 1 格、右/下留 2 格，视觉上是偏的。
- 只动了 `config.py` 三个常量：`GRID_N 24→25`、`GRID_ORIGIN (164,164)→(150,150)`、`TARGET_OFFSET (1,1)→(2,2)`；
  `GRID_PX` 672→700。**逻辑代码一行没改**（全走常量推导，`grid.py` 的换算函数自动适配）。
- 几何：网格 150~850（700px），二维码 206~794（588px），左右/上下留白各 56px = 2 格；
  生成环 840 不变 → 怪物进场走廊从 84px 收窄到 70px。
- 验证：`pos_to_cell(150,150)=(0,0)`、`pos_to_cell(850,150)=None`、`cell_center(12,12)=(500,500)` 正中；
  26 项回归全过（新增 4 项几何断言）；截图确认黑码阶段、阶段1、阶段2 锁定环（正好 2 格厚）、结算页都正常。
- 文档：规格书升到 v3.3（§3.1 尺寸表、§3.2 原点与布局图重建、§4 常量重同步、§17 加两条验收）。

### 2026-11-07 晚 · 关卡开场动画（震碎 → 下沉 → 灰码浮现）+ 迁到 `src/`

- **进场动画**：点选关后不再直接开打，先放 2.10s：完整二维码以**黑色**铺满 21×21（不是灰色提示）→
  整屏抖 3 下 → 每个黑格炸成一块碎片、四散后被重力拉出屏幕（此时网格全白）→
  灰码从透明淡入 → 才开始计时。
- **「不计时」怎么做的**：`Game.intro_t`，`update()` 里 `if self.intro_t > 0: self.update_intro(dt); return`，
  在计时/出怪/涂改**之前**就返回，所以这 2.1 秒里 `elapsed` 恒为 0、没有怪、按 J 也涂不上。
- **抖动在震碎之前**：`SHAKE_LEAD = 3` 让抖动比震碎提前 3 下（0.21s），碎完还剩 3 下 —— 读起来是「抖两三下然后炸开」。
  用固定偏移序列 `SHAKE_SEQ`，不用 `sin`（帧率波动会让 `sin` 采样点漂，看起来忽大忽小）。
  整帧位移由 `apply_shake()` 借 `shake_buf` 中转完成，不动任何绘制坐标。
- **三次视觉返工**（都记进 §5 坑里了）：纯黑碎片飞出白网格后在深色底上像空心框 → 改深灰实心 + 细亮边；
  角色浮在碎码中间 → 动画期间不画玩家；碎片没落完就淡入 → 重力 1800 + `INTRO_FALL` 1.20s 保证落尽。
- **目录调整**：用户手动把所有 `.py` 挪进 `src/` 便于管理。PyCharm 只改了一半 import（混着 `from src.x` 与
  `from config`），导致**两种启动方式都报 ModuleNotFoundError**。已统一为 `from src.xxx`、加 `src/__init__.py`、
  在 `src/main.py` 顶部加路径引导，现在 `python src/main.py` 与 `python -m src.main` 都能跑。
- 验证：六个阶段截图逐张看过 + 20 项回归全过；碎片峰值 219 块、开场绘制 4.9ms、正常局内 3.2ms。

### 2026-11-07 · 拆分为 9 模块 + 选关系统 + 回车 bug

- **单文件拆成 9 个模块**：原来 `main.py` 一千多行，找东西全靠 `Ctrl+F`。按职责拆成
  `config / grid / qr / board / input_state / entities / ui / game / main`，
  `ui.py` 承接全部绘制（函数首参是 `Game`），`game.py` 只留规则。
- **拆分怎么验证的**：先截 6 张参考图（开始页 / 选关页 / 局内 / 阶段2 / 横幅 / 结算），
  拆完重画并逐像素 md5 比对 → **完全一致**；再跑 19 项逻辑回归全过。
- **新增开始页 + 选关页**：`TITLE → SELECT → PLAY` 三段式，5 个关卡按钮逐关解锁
  （`unlocked` 初始 1，通关解锁下一个）；鼠标可点按钮、键盘 `Enter`/`A`·`D`·`←`·`→` 也能选。
- **修掉回车键 bug**：`SC_ENTER` 原来写 28（= 字母 Y），改成 **40**，并补小键盘回车 **88**。
- **IDE 友好化**（不改行为）：顶层 `def`/`class` 之间补 2 空行（25 处）；
  `ui.py` 函数首参加 `g: "Game"` 类型标注（`TYPE_CHECKING` 导入，运行时零影响）；
  `game.py` 给 `new_round()` 里赋值的 15 个属性在 `__init__` 补默认值。
- 顺带修掉一个必崩点：`generate_target()` 的重摇加了次数上限（见「踩过的坑」第 2 条）。

### 2026-11-06 · 怪物与结算

- 加上 `Monster`（选最近黑格、走到底就吃掉一格后自毁、无黑格时漂移 + 12s 超时）和 `claims` 占用表。
- 30 秒阶段锁定 + 1 秒 `PHASE SHIFT` 遮罩 + 结算页（两张 21×21 缩略图、S/A/B/F 评级）。
- 修掉「结算页不清屏」和「锁定区与涂黑同色」两个视觉 bug；白底改成一次 `fill`（性能）。

### 2026-11-05 · 立项

- 定下玩法：限时复原中心 21×21 的「形似 QR」图案，红圆侵蚀体从外围环涌入吃黑格。

### 2026-11-04 · 起步

- 第一个练手项目（扫雷），主要收获是学会从 PyCharm 往 GitHub 推代码。
