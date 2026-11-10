# -*- coding: utf-8 -*-
"""DATA SHIFT —— 全局常量

所有可调数值都集中在这里：调难度、换配色、改时长都只动这个文件。
其它模块一律从这里 import，不允许在自己文件里另写数字。

第一幕 · Phase A（最小可玩闭环）的数值已落地；标了 ⬜ 的是等用户拍板的。
"""

# ==== 画面 ====
# 1360×1000：左侧 0~840 是「世界」（30×30 生成环），右侧 840~1360 是 520px 状态面板
WINDOW_W, WINDOW_H = 1360, 1000
FPS = 60
CELL = 28
GRID_N = 25                       # 主网格 25×25 → 700px
GRID_PX = GRID_N * CELL           # 700
GRID_ORIGIN = (70, 130)           # 30×30 世界正中的 25×25（世界 840px，两侧各留 2.5 格 = 70px）
TARGET_N = 21
TARGET_OFFSET = (2, 2)            # (25-21)/2 = 2，四周各留 2 格 → 圣坛正居中
SPAWN_N = 30                      # 世界大小（怪物从这条虚线外来）
SPAWN_ORIGIN = (0, 60)
SPAWN_PX = SPAWN_N * CELL         # 840

# 右侧状态面板（血条 / 进度 / 脏格；Phase B 的 8 格物品栏和 21×21 进度图也放这里）
PANEL_X = 840
PANEL_W = WINDOW_W - PANEL_X      # 520
PANEL_Y = 60
PANEL_H = 840
PANEL_PAD = 26

# 顶部 HUD 行 / 底部操作提示
HUD_X = 28
HUD_Y = 12
HINT_Y = 918                      # 在生成环下沿（900）之下，不吃格子

# 窗口自适应：按桌面可用空间等比缩放，逻辑坐标始终是 1360×1000
FIT_MARGIN_X, FIT_MARGIN_Y = 60, 110
MIN_SCALE = 0.5

# ==== 颜色 ====
C_BG = (11, 15, 20)               # 窗外废墟底色
C_BG_GRID = (18, 24, 32)          # 废墟暗格
C_CELL_WHITE = (247, 247, 249)    # 未涂黑格子
C_CELL_LINE = (228, 228, 232)     # 格子分隔线
C_CELL_BLACK = (17, 17, 24)       # 有效黑域（the Dark）
C_MIRAGE = (90, 95, 105)          # 灰域底色（配 alpha 用，越淡越接近白）
C_MUST = (74, 222, 128)           # 绿框：本轮必涂格
C_ERASING = (150, 150, 160)       # 抹除进行中
C_ALTAR = (58, 68, 84)            # 圣坛边框
C_MONSTER = (255, 61, 110)        # 红怪猩红
C_PLAYER = (108, 255, 196)        # 玩家（青绿）
C_ACCENT = (108, 255, 196)        # 进度 / 正向强调
C_WARN = (255, 176, 32)           # 警示黄
C_MISSING = (46, 52, 62)          # 该黑却没涂
C_OLDMAN = (214, 198, 160)        # 老者（暖米色，和玩家的青绿分开）
C_STAFF = (150, 132, 96)          # 拐杖
C_ITEM = (255, 214, 102)          # 道具（BAG / MAP）
C_PROP_DEAD = (120, 44, 58)       # 地上死掉的红怪（暗红）
C_PROP_TOOL = (96, 104, 116)      # 用过的道具（灰）
C_PANEL = (20, 25, 33)            # 右侧面板底
C_PANEL_LINE = (38, 46, 58)       # 面板分隔线
C_DIM = (74, 82, 94)              # 弱化文字 / 描边
C_TEXT = (232, 236, 240)

# ==== 第一幕 · 规则 ====
MUST_TOTAL = 100                  # 三个定位图案（各 33）+ 暗模块 1
STAIN_LIMIT = 10                  # 第一幕脏格额度（累计值）；**超过不判负**，改成扣血
STAIN_DAMAGE = 5                  # 额度之外的每一格脏格 = 一次外伤：血量 -5%
ERASE_CAST = 0.25                 # K 抹除的塌陷时长

# ==== 异象（the Anomaly）：Shift 照出脚下 5×5 灰域 ====
MIRAGE_RADIUS = 2                 # 2 → 5×5
MIRAGE_FADE = 5.0                 # 灰域 5 秒内渐变回白
MIRAGE_ALPHA_MAX = 150            # 灰域最深时的不透明度（0~255）

# ==== 血量 ====
HEALTH_MAX = 100
HIT_DAMAGE = 5                    # 每次被红怪命中 -5% → 20 次即死
HEALTH_LOW = 30                   # 低于这个值血条转警示色

# ==== 红怪 ====
RED_SPEED = 62.0
RED_RADIUS = 9
RED_SPD_JITTER = (0.88, 1.12)     # 每只怪速度随机浮动，别齐步走
RED_EAT_DIST = 6.0                # 到这个距离就算啃到黑域
RED_HIT_DIST = 11.0               # 到这个距离就算追上玩家
RED_SPAWN_PER_MIN = 12.0          # 开局生成速率（每分钟）
RED_SPAWN_ACCEL_PERIOD = 30.0     # 每 30 秒提速一次
RED_SPAWN_ACCEL = 1.05            # 提速幅度 5%（用户之后自己调）
RED_SPAWN_MARGIN = 6.0            # 第一只怪在检查点之后多久出现（先给个空档）

# ==== 清屏（Phase A 简化版）====
CLEAR_GLOW_TIME = 1.2             # 圣坛边缘发光的憋气时长
CLEAR_WAVE_SPEED = 460.0          # 圆形波扩散速度 px/s
CLEAR_WAVE_HOLD = 0.6             # 波扫完之后停一下再出收尾字幕
CLEAR_WAVE_WIDTH = 5              # 波环描边粗细

# ==== 提示 / 横幅 ====
HINT_TIME = 2.6                   # 底部系统提示停留时长
BANNER_TIME = 2.4                 # 中央大字横幅（ACT 1 — END 之类）

# ==== 剧情层（Phase B）====
MONOLOGUE_TIME = 3.6              # 内心独白停留（2.5~3 秒 + 读完一点余量）
TUTORIAL_MOVE_SECONDS = 5.0       # 必须「移动」满 5 秒才提示 Shift（站着不动不算）
ANOMALY_MISS_LIMIT = 3            # 在坛外连按 3 次 Shift 都没灰域 → 放行，别把教程变成死胡同
CALL_RANGE_PX = 150.0             # 呼喊范围（约 5 格）：进这个圈才显示 PRESS [T]
CLOSE_RANGE_PX = 72.0             # 「走近再说」的范围（约 2.5 格）
OLDMAN_CELL = (1, 12)             # 老者站位：圣坛上方那条平地上，背对玩家（朝世界外）
OLDMAN_BODY_W, OLDMAN_BODY_H = 18, 26
OLDMAN_RUN_SPEED = 230.0          # 坛内呼喊时他兴奋地跑过来
OLDMAN_LEAVE_SPEED = 140.0        # 对话结束后往世界外走
THREAT_TIME = 2.0                 # 红怪狠话停留
THREAT_Y = 250                    # 屏幕中央偏上
GAP_SECONDS = 10.0                # 老者离开后的空档
DLG_BOX = (40, 688, 760, 204)     # 对话框：x / y / 宽 / 高
DLG_LINE_H = 34
PROP_DEAD_CELL = (4, 1)           # 死亡的红怪（可选独白 M4）
PROP_TOOL_CELL = (19, 1)          # 用过的道具（可选独白 M5）
PROP_RANGE_PX = 54.0
ITEM_PICK_RANGE = 46.0
ITEM_RISE_TIME = 0.8
REWARD_DELAY = 1.6                # 波扫完到道具浮出的延迟
REWARD_WAIT = 5.0                 # 两个都捡起来之后，等光扩散
SPREAD_TIME = 2.0                 # 圣坛的光扩散到整个世界
BAG_SLOTS = 8                     # 背包格数
MAP_CELL = 11                     # 21×21 进度图每格像素（231px）

# ==== 玩家（格子对齐移动）====
PLAYER_START_CELL = (12, 12)      # ⬜ B1 未拍板：设计建议挪到 (13,10)，先按原方案
MOVE_REPEAT = 0.13                # 长按方向键时每走一格的间隔（按下瞬间必定先走一格）
PLAYER_BODY_W, PLAYER_BODY_H = 16, 22
PLAYER_GLOW_R = 14

# ==== 输入：scancode 是物理键位，与输入法/CapsLock/Shift 无关 ====
SC_W, SC_A, SC_S, SC_D = 26, 4, 22, 7
SC_J, SC_K, SC_SPACE = 13, 14, 44
# ⚠️ 这是 SDL 的 scancode（HID 表：A=4 … Z=29），**不是** PS/2 扫描码。
# T = 4+19 = 23（20 是 Q）；B = 4+1 = 5（48 是 ]）。写错过一次，按键全无反应。
SC_T, SC_B = 23, 5
SC_ESC, SC_ENTER, SC_KP_ENTER, SC_F1 = 41, 40, 88, 58
# Shift：SDL2 scancode 左 225 / 右 229（已用 SDL_GetScancodeFromKey 实测，见 HANDOFF §3）。
# ⚠️ 别写成 42 / 54 —— 那是 PS/2 扫描码，SDL2 里 42 是退格键。
SC_SHIFT = (225, 229)
DIR_KEYS = {SC_W: (-1, 0), SC_S: (1, 0), SC_A: (0, -1), SC_D: (0, 1)}

# ==== 格子状态 ====
WHITE, VALID, DIRTY, ERASING = 0, 1, 2, 3

# ==== 开场动画（Phase A 不用；Phase B 改造后挪到第一幕开场）====
INTRO_SHOW = 1.50
INTRO_FALL = 1.20
INTRO_FADE = 0.40
INTRO_TOTAL = INTRO_SHOW + INTRO_FALL + INTRO_FADE   # 3.10s
SHAKE_STEP = 0.07
SHAKE_SEQ = ((9, -7), (-8, 6), (7, 6), (-6, -5), (4, 4), (0, 0))
SHAKE_LEAD = 3
DARK_MODULE_LEAD = 0.20
DARK_MODULE = (13, 8)             # QR v1 的规范位置，别改
DEBRIS_GRAVITY = 1800.0
DEBRIS_SPEED = (110.0, 260.0)
DEBRIS_UP = 120.0
DEBRIS_JITTER = 60.0

# ==== 二维码 ====
QR_VERSION = 1                    # 锁死 v1 = 21×21
QR_ERROR = "l"                    # 纠错 L，容量 17 个 ASCII
QR_CONTENT_LEN = 8                # 现在随机 8 位；以后换短网址（上限 17）

# ==== 以下为旧五关街机版残留：新版不读，但先留着别删（见开工单 §5）====
LEVELS = (
    {"cover": 0.62, "time": 180.0, "spawn": 15, "noise": 0.25, "delay": 2.0, "purple": 0, "seen": True},
    {"cover": 0.64, "time": 175.0, "spawn": 20, "noise": 0.22, "delay": 2.0, "purple": 3, "seen": True},
    {"cover": 0.66, "time": 170.0, "spawn": 25, "noise": 0.20, "delay": 1.5, "purple": 0, "seen": True},
    {"cover": 0.68, "time": 170.0, "spawn": 30, "noise": 0.18, "delay": 1.5, "purple": 0, "seen": True},
    {"cover": 0.72, "time": 165.0, "spawn": 35, "noise": 0.15, "delay": 1.0, "purple": 0, "seen": True},
)
PHASE1_DURATION = 30.0
PHASE_SHIFT_TIME = 1.0
STORY_BANNER_TIME = 2.2
MENU_BLINK_HZ = 2.0
ALPHA_MIN = 0.48
ALPHA_TRY = 40
SEEN_RADIUS = 2
SEEN_FLASH_TIME = 0.22
C_LOCK = (30, 36, 45)
C_PURPLE = (176, 112, 255)
PURPLE_SPEED = 56.0
PURPLE_RADIUS = 10
PURPLE_IDLE_LIMIT = 60.0
PURPLE_SPAWN_WINDOW = 150.0
PURPLE_SPAWN_MARGIN = 6.0
PURPLE_MODE = "best_row"
SC_R, SC_LEFT, SC_RIGHT = 21, 80, 79
SC_KP_ENTER_ALIAS = 88
BTN_W, BTN_H = 300, 92
LV_BTN_W, LV_BTN_H, LV_BTN_GAP = 150, 154, 20
THUMB_CELL = 10
GRADE_S_COVERAGE = 0.95
GRADE_S_NOISE = 3
GRADE_A_NOISE_PCT = 0.4
MONSTER_SPEED = 62.0
MONSTER_RADIUS = 9
MONSTER_IDLE_LIMIT = 12.0
MONSTER_EAT_DIST = 6.0
MONSTER_RETRY = 0.5
MONSTER_SPD_JITTER = (0.88, 1.12)
C_GHOST = (60, 60, 70, 110)
BAR_W, BAR_H = 320, 10
HUD_PAD = 80
