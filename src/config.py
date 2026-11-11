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
C_BG = (38, 27, 20)               # 废墟底色：深胡桃褐（原来是近乎黑的冷蓝）
C_BG_GRID = (52, 38, 28)          # 废墟暗格（比底色亮一档，看得见纹路但不抢）
C_CELL_WHITE = (247, 247, 249)    # 未涂黑格子
C_CELL_LINE = (228, 228, 232)     # 格子分隔线
C_CELL_BLACK = (19, 16, 15)       # 有效黑域（the Dark）：带一点暖的近黑
C_MIRAGE = (90, 95, 105)          # 灰域底色（配 alpha 用，越淡越接近白）
C_MUST = (74, 222, 128)           # 绿框：本轮必涂格
C_ERASING = (168, 158, 148)       # 抹除进行中 / 次级文字（暖灰，别在褐底上发蓝）
C_ALTAR = (92, 78, 64)            # 圣坛边框（暖灰褐）
C_RING = (104, 86, 70)            # 生成环虚线（褐底上别用亮白，会抢戏）
C_MONSTER = (255, 61, 110)        # 红怪猩红
C_PLAYER = (108, 255, 196)        # 玩家（青绿）
C_ACCENT = (108, 255, 196)        # 进度 / 正向强调
C_WARN = (255, 176, 32)           # 警示黄
C_MISSING = (62, 50, 40)          # 该黑却没涂 / 开场碎片
C_OLDMAN = (214, 198, 160)        # 老者（暖米色，和玩家的青绿分开）
C_STAFF = (150, 132, 96)          # 拐杖
C_ITEM = (255, 214, 102)          # 道具的高光 / 金属件
C_ITEM_LEATHER = (186, 128, 68)   # 背包：皮革亮面
C_ITEM_LEATHER_DARK = (124, 80, 42)   # 背包：皮革暗面 / 缝线
C_ITEM_PAPER = (232, 220, 188)    # 地图：纸
C_ITEM_PAPER_DARK = (188, 172, 136)   # 地图：卷边的背光面
C_ITEM_INK = (86, 62, 38)         # 地图：墨线
C_ITEM_MARK = (206, 72, 56)       # 地图：红色标记（唯一一点暖红，视线落点）
C_BAG_SLOT = (26, 19, 14)         # 物品栏的槽底（暖色，别在褐面板里发蓝）
C_PROP_DEAD = (120, 44, 58)       # 地上死掉的红怪（暗红）
# ---- 角色分层配色（sprites.py 用：剪影 / 体积 / 高光 / 描边各一层）----
C_OUTLINE = (14, 11, 10)          # 角色统一描边：近黑，压在褐底或白格上都分得开
C_PLAYER_DEEP = (13, 44, 39)      # 码序使：斗篷剪影
C_PLAYER_DARK = (28, 84, 71)      # 码序使：受光的体积
C_PLAYER_LIGHT = (192, 255, 226)  # 码序使：面罩 / 光标 / 核心高光
C_OLDMAN_DARK = (168, 148, 114)   # 老者：袍子暗部 / 头发
C_OLDMAN_LIGHT = (242, 233, 210)  # 老者：胡须
C_OLDMAN_SKIN = (233, 204, 168)   # 老者：脸（比袍子亮一档，不然头和身体糊成一块）
C_SASH = (146, 106, 66)           # 腰带 / 拐杖缠布
C_MONSTER_DARK = (130, 16, 46)    # 红怪：外圈肉
C_MONSTER_CORE = (255, 232, 238)  # 红怪：眼珠高光
C_MONSTER_RING = (255, 138, 168)  # 红怪：追人时的红环
C_PROP_TOOL = (96, 104, 116)      # 用过的道具（灰）
C_PANEL = (31, 23, 17)            # 右侧面板底
C_PANEL_LINE = (62, 47, 36)       # 面板分隔线
C_DIM = (110, 94, 80)             # 弱化文字 / 描边
C_TEXT = (238, 233, 226)          # 主文字：偏暖的白

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

# ==== 第二幕 · 紫怪（the purple one）====
# 行为见 entities.PurpleOne：锁圣坛内的黑格 → 比「行/列」哪条黑格多 → 撞到清整条 25 格。
PURPLE_FIRST_DELAY = 8.0          # 首只到场（作者 2026-11-11 定：8 秒）
PURPLE_SPAWN_PER_MIN = 6.0        # 之后每分钟 6 只（= 10 秒一只）。作者 2026-11-11 要求「加快一些」，
                                  # 原来是 3（20 秒一只）。仍比红怪 12 只/分慢，守住 P1「比红怪长」
PURPLE_SPEED = 45.0               # 比红怪慢（RED_SPEED=62）：看得见、躲得开
PURPLE_RADIUS = 11                # 比红怪大（RED_RADIUS=9）：体型就是威胁预告
PURPLE_EAT_DIST = 7.0             # 撞到判定的距离（红怪 6）

# ==== 第二幕 · 开场 ====
# 格子不清空，所以不能重播碎码动画；用「一行独白 + 圣坛低鸣」过渡一下。
A2_OPEN_SECONDS = 2.6             # 开场独白读得完就走（玩家可以边走边看）


# ==== 清屏（Phase A 简化版）====
CLEAR_GLOW_TIME = 1.2             # 圣坛边缘至少亮这么久，才认「玩家已站进来」
CLEAR_WAVE_SPEED = 460.0          # 圆形波扩散速度 px/s
CLEAR_WAVE_HOLD = 0.6             # 波扫完、脏格抹掉之后停一下，再浮出道具
CLEAR_WAVE_WIDTH = 5              # 波环描边粗细

# ==== 提示 / 横幅 ====
HINT_TIME = 2.6                   # 底部系统提示停留时长
BANNER_TIME = 2.4                 # 中央大字横幅（ACT 1 — END 之类）

# ==== 剧情层（Phase B）====
MONOLOGUE_TIME = 5.0              # 内心独白停留（含打字；长句也能读完）
PROMPT_FONT = 34                  # 底部提示字号（原来 27，偏小）
TUTORIAL_MOVE_SECONDS = 5.0       # 必须「移动」满 5 秒才提示 Shift（站着不动不算）
ANOMALY_MISS_LIMIT = 3            # 在坛外连按 3 次 Shift 都没灰域 → 放行，别把教程变成死胡同
CALL_RANGE_PX = 150.0             # 呼喊范围（约 5 格）：进这个圈才显示 PRESS [T]
CLOSE_RANGE_PX = 72.0             # 「走近再说」的范围（约 2.5 格）
OLDMAN_CELL = (1, 12)             # 老者站位：圣坛上方那条平地上，背对玩家（朝世界外）
OLDMAN_RUN_SPEED = 230.0          # 坛内呼喊时他兴奋地跑过来
OLDMAN_LEAVE_SPEED = 140.0        # 对话结束后往世界外走
THREAT_TIME = 2.0                 # 红怪狠话停留
THREAT_Y = 250                    # 屏幕中央偏上
GAP_SECONDS = 10.0                # 老者离开后的空档
# ==== 字幕呈现（心声 / 对话）====
# 对话：底部一块带名牌的框，正文 36px，最多 5 行
DLG_BOX = (24, 620, 792, 264)     # x / y / 宽 / 高（264 = 4 行的满高，也是上限）
DLG_BOTTOM = 884                  # 框底固定，高度按这一句的行数往下缩（最少 2 行）
DLG_MIN_ROWS = 2
DLG_PAD = 34                      # 框内左右留白
DLG_FONT = 32                     # 正文字号（原来 25；32 是「4 行能装下全部台词」的上限）
DLG_LINE_H = 48
DLG_NAME_FONT = 26                # 名牌字号
DLG_CPS = 58                      # 打字速度：字符/秒
DLG_LAST_MIN_SHOW = 0.8           # 最后一句至少显示这么久：防手快连按把它一帧跳过去
# 心声：和对话框共用同一套框（同宽同底边），字比对话更大，进出淡入淡出
# ⚠️ 原来的「浮在世界下方的字幕带」已经废弃：`MONO_TOP` / `MONO_WIDTH` / `MONO_PLATE_ALPHA`
#    三个常量随之删掉 —— 别再加回来，框的尺寸由 `ui.mono_box()` 按行数算。
MONO_FONT = 40
MONO_LINE_H = 54
MONO_CPS = 46                     # 比对话（58）略慢：心声是「想」出来的，快不得
MONO_FADE_IN = 0.22
MONO_FADE_OUT = 0.55
PROP_DEAD_CELL = (4, 1)           # 死亡的红怪（可选独白 M4）
PROP_TOOL_CELL = (19, 1)          # 用过的道具（可选独白 M5）
PROP_RANGE_PX = 54.0
ITEM_PICK_RANGE = 46.0
ITEM_RISE_TIME = 0.8
REWARD_DELAY = 1.6                # 波扫完到道具浮出的延迟
REWARD_WAIT = 5.0                 # 两个都捡起来之后，等光扩散
SPREAD_TIME = 2.0                 # 圣坛的光扩散到整个世界
BAG_SLOTS = 8                     # 背包格数
MAP_CELL = 13                     # 21×21 进度图每格像素（273px）
MAP_Y = 604                       # 地图这一块在右侧面板里的顶边
MAP_OPEN_TIME = 0.22              # 卷轴铺开 / 收起的时长
MAP_SCROLL_W, MAP_SCROLL_H = 138, 42   # 收起时那个卷轴的尺寸

# ==== 玩家（格子对齐移动）====
PLAYER_START_CELL = (12, 12)      # ⬜ B1 未拍板：设计建议挪到 (13,10)，先按原方案
MOVE_REPEAT = 0.13                # 长按方向键时每走一格的间隔（按下瞬间必定先走一格）
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
SC_R, SC_LEFT, SC_RIGHT = 21, 80, 79
SC_M = 16                         # M：铺开 / 卷起地图（只在拿到地图后有效）
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
