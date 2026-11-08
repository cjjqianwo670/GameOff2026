# -*- coding: utf-8 -*-
"""DATA SHIFT —— 全局常量

所有可调数值都集中在这里：调难度、换配色、加关卡都只动这个文件。
其它模块一律从这里 import，不允许在自己文件里另写数字。
"""

# ==== 常量与颜色 ====

# ==== 画面 ====
WINDOW_W = WINDOW_H = 1000        # 逻辑画布尺寸（所有布局都按它算）
FPS = 60
CELL = 28
GRID_N = 25                       # 25×28 = 700px
GRID_ORIGIN = (150, 150)          # (1000 - 25*28) / 2
TARGET_N = 21
TARGET_OFFSET = (2, 2)            # (25-21)/2 = 2，四周各留 2 格 → 正居中
SPAWN_N = 30
SPAWN_ORIGIN = (80, 80)
SPAWN_PX = SPAWN_N * CELL         # 840

# 窗口自适应：高 DPI 屏逻辑分辨率常只有 1400×900 上下，1000×1000 会溢出屏幕，
# 所以真实窗口按桌面可用空间缩、画面整帧贴进去，逻辑坐标始终是 1000×1000。
FIT_MARGIN_X, FIT_MARGIN_Y = 80, 120   # 预留左右边距 + 标题栏 + 任务栏
MIN_WINDOW = 520                        # 再小就看不清了

GRID_PX = GRID_N * CELL           # 700

# ==== 颜色 ====
C_BG = (11, 15, 20)               # 窗外废墟底色
C_BG_GRID = (18, 24, 32)          # 废墟暗格
C_CELL_WHITE = (247, 247, 249)    # 未涂黑格子
C_CELL_LINE = (228, 228, 232)     # 格子分隔线
C_CELL_BLACK = (17, 17, 24)       # 已涂黑
C_GHOST = (60, 60, 70, 110)       # 目标提示（半透明深灰，SRCALPHA）
C_ERASING = (150, 150, 160)       # 抹除进行中
C_LOCK = (30, 36, 45)             # 阶段2 锁定区遮罩
C_MONSTER = (255, 61, 110)        # 侵蚀体猩红（红怪：吃一格）
C_PURPLE = (176, 112, 255)        # 紫怪：撞到黑格就清掉整行
C_PLAYER = (108, 255, 196)        # 玩家（青绿）
C_ACCENT = (108, 255, 196)        # 进度条 / 结算里的「涂对」
C_WARN = (255, 176, 32)           # 警示黄
C_MISSING = (46, 52, 62)          # 结算缩略图：该黑却没涂的格子
C_PANEL = (26, 32, 42)            # 菜单按钮底色
C_DIM = (74, 82, 94)              # 锁定态的文字/描边
C_TEXT = (232, 236, 240)

# ==== 规则 ====
PHASE1_DURATION = 30.0
PHASE_SHIFT_TIME = 1.0            # 阶段横幅（PHASE SHIFT）持续时长
STORY_BANNER_TIME = 2.2           # 剧情字幕（开场句 / 一次触发句）停留时长
MENU_BLINK_HZ = 2.0               # 菜单闪字频率
ERASE_CAST = 0.25
# 目标黑格占比下限：低于它的一版太稀、太难，重摇（§14 平衡值约 220/441 ≈ 0.50）
ALPHA_MIN = 0.48
ALPHA_TRY = 40                    # 重摇次数上限，兜底取最密的一版

# ==== 关卡 ====
# 只改数字、不加新机制：cover=需复原比例 / time=时长(秒)
# spawn=红怪每分钟 / noise=噪声上限比例 / delay=首怪延迟(秒)
# purple=紫怪数量（0=这一关没有；第二关暂定 3 只，随便调）
LEVELS = (
    {"cover": 0.70, "time": 180.0, "spawn": 15, "noise": 0.25, "delay": 2.0, "purple": 0},
    {"cover": 0.72, "time": 170.0, "spawn": 20, "noise": 0.22, "delay": 2.0, "purple": 3},
    {"cover": 0.75, "time": 160.0, "spawn": 25, "noise": 0.20, "delay": 1.5, "purple": 0},
    {"cover": 0.78, "time": 150.0, "spawn": 30, "noise": 0.18, "delay": 1.5, "purple": 0},
    {"cover": 0.80, "time": 140.0, "spawn": 35, "noise": 0.15, "delay": 1.0, "purple": 0},
)

# ==== 关卡开场动画（完整黑码 → 抖动震碎 → 碎片下沉 → 灰色提示浮现）====
INTRO_SHOW = 1.50                 # 完整黑色二维码停留多久（后半段开始抖）就震碎
INTRO_FALL = 1.20                 # 碎片爆散 + 下沉的时长（必须够长，让碎片全部落出屏幕）
INTRO_FADE = 0.40                 # 灰色提示层浮现时长
INTRO_TOTAL = INTRO_SHOW + INTRO_FALL + INTRO_FADE   # 共 2.10s，这期间不计时、不出怪、不能涂

SHAKE_STEP = 0.07                 # 每一下抖动持续多久
# 固定偏移序列（抖 6 下、幅度递减）：前 3 下在震碎之前，后 3 下在震碎之后
SHAKE_SEQ = ((9, -7), (-8, 6), (7, 6), (-6, -5), (4, 4), (0, 0))
SHAKE_LEAD = 3                    # 震碎之前先抖几下（乘 SHAKE_STEP 就是提前量）
DARK_MODULE_LEAD = 0.20           # 开场时先单独亮「暗模块」这一格，其余格子随后才出现
DARK_MODULE = (13, 8)             # 暗模块在 21×21 目标里的坐标（整张码里唯一永远为黑的格）

DEBRIS_GRAVITY = 1800.0           # 碎片重力 px/s²，负责把它们拽到屏幕下方
DEBRIS_SPEED = (110.0, 260.0)     # 爆散初速范围
DEBRIS_UP = 120.0                 # 额外的向上抛偏置，先飞起来再落
DEBRIS_JITTER = 60.0              # 水平随机量，避免所有碎片走同一条直线

# ==== 玩家（格子对齐移动）====
PLAYER_START_CELL = (12, 12)      # 出生于主网格正中，一眼能看到脚下的目标区
MOVE_REPEAT = 0.13                # 长按方向键时每走一格的间隔（按下瞬间必定先走一格）
PLAYER_BODY_W, PLAYER_BODY_H = 16, 22
PLAYER_GLOW_R = 14

# ==== 怪物 ====
MONSTER_SPEED = 62.0
MONSTER_RADIUS = 9
MONSTER_IDLE_LIMIT = 12.0
MONSTER_EAT_DIST = 6.0            # 到这个距离就算啃到，直接吃掉
MONSTER_RETRY = 0.5               # 场上没有黑格时，隔多久重试一次选目标
MONSTER_SPD_JITTER = (0.88, 1.12)  # 每只怪速度随机浮动，别齐步走

# ==== 紫怪（第二关起）：撞到黑格，把那一整行清成白色 ====
# 数量按关卡配（见 LEVELS 的 purple 键），0 = 这一关不出现
PURPLE_SPEED = 56.0               # 比红怪慢一点，给玩家反应时间
PURPLE_RADIUS = 10
PURPLE_IDLE_LIMIT = 60.0          # 场上没黑格时能撑很久：它要等玩家先涂出东西
PURPLE_SPAWN_WINDOW = 150.0       # 前 2 分半内的随机时刻刷新
PURPLE_SPAWN_MARGIN = 6.0         # 但不会卡在最后 6 秒才出来
# 选目标的方式：
#   "nearest"  撞最近的黑格（撞到的那行是随机的）
#   "best_row" 专挑「已涂对的目标黑格数最多」的那一行 —— 它看得懂你在干什么
PURPLE_MODE = "best_row"

# ==== 结算 ====
THUMB_CELL = 10                   # 21×21 缩略图每格 10px → 210×210
GRADE_S_COVERAGE = 0.95           # S 级门槛
GRADE_S_NOISE = 3
GRADE_A_NOISE_PCT = 0.4           # A 级：噪声不超过上限的 40%

# ==== 输入：scancode 是物理键位，与输入法/CapsLock/Shift 无关 ====
SC_W, SC_A, SC_S, SC_D = 26, 4, 22, 7
SC_J, SC_K, SC_SPACE = 13, 14, 44   # J 涂黑 / K 抹除 / 空格=J 的别名
SC_R, SC_ESC, SC_F1 = 21, 41, 58
# SDL2 物理键位：字母 A=4 ... Z=29，数字 1=30 ... 0=39，Return=40，Esc=41，Space=44
SC_ENTER = 40                     # 回车：开始 / 确认选关
SC_KP_ENTER = 88                  # 小键盘回车，同样当确认
SC_LEFT, SC_RIGHT = 80, 79        # 方向键左右：选关页切换
DIR_KEYS = {SC_W: (-1, 0), SC_S: (1, 0), SC_A: (0, -1), SC_D: (0, 1)}

# ==== 格子状态 ====
WHITE, BLACK, ERASING = 0, 1, 2

# ==== 布局：HUD ====
HUD_PAD = 80
BAR_W, BAR_H = 320, 10

# ==== 菜单按钮 ====
BTN_W, BTN_H = 300, 92                          # 开始页的 START
LV_BTN_W, LV_BTN_H, LV_BTN_GAP = 150, 154, 20   # 选关页的 1~5
