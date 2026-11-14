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
C_PURPLE = (176, 112, 255)        # 紫怪（第二幕）：整条清完就走，不追人
C_YELLOW = (255, 203, 82)         # 黄怪（第三幕）：为「被偷的格式信息」而来，专打老者
C_YELLOW_DARK = (168, 120, 20)
C_YELLOW_CORE = (66, 40, 0)       # 黄怪瞳孔
C_PROP_TOOL = (96, 104, 116)      # 用过的道具（灰）
C_PANEL = (31, 23, 17)            # 右侧面板底
C_PANEL_LINE = (62, 47, 36)       # 面板分隔线
C_DIM = (110, 94, 80)             # 弱化文字 / 描边
C_TEXT = (238, 233, 226)          # 主文字：偏暖的白

# ==== 第一幕 · 规则 ====
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
PURPLE_SPAWN_PER_MIN_ACT3 = 2.0   # 第三幕慢下来（作者 2026-11-12）：格式信息正好躺在第 10 行/列上，
                                  # 一次清行能抹掉 16 个格式格，6 只/分太狠；2 只/分 = 30 秒一次
PURPLE_SPAWN_PER_MIN_ACT4 = 4.0   # 第四幕回潮：那一幕是「扫」，玩家一趟能写几十格，
                                  # 没有清行的压力就 30 秒通关；4 只/分 = 15 秒一次，一次抹 17 格
                                  # 原来是 3（20 秒一只）。仍比红怪 12 只/分慢，守住 P1「比红怪长」
PURPLE_SPEED = 45.0               # 比红怪慢（RED_SPEED=62）：看得见、躲得开
PURPLE_RADIUS = 11                # 比红怪大（RED_RADIUS=9）：体型就是威胁预告
PURPLE_EAT_DIST = 7.0             # 撞到黑格的判定距离（红怪 6）
PURPLE_HIT_DIST = 13.0            # 坛内没黑域时改为扑人：撞到码序使的判定距离（体型大，比红怪 11 宽）
PURPLE_HIT_DAMAGE = 10            # 被紫怪撞一下扣 10%（比红怪 5% 重一倍，作者 2026-11-12 定）

# ==== 第三幕 · 黄怪（the yellow ones）====
# 行为见 entities.YellowOne：冲老者 —— 被打一次就转火玩家；老者倒下后没人可打，也转火玩家。
YELLOW_FIRST_DELAY = 7.0          # 开场几秒后第一只到场（给玩家读完对话的时间）
YELLOW_SPAWN_PER_MIN = 7.0        # 之后每分钟 7 只（约 8.6 秒一只；作者 2026-11-13 要求加快）
YELLOW_SPEED = 74.0               # 比红怪（62）快一点：它们是冲着老者去的，慢了就永远够不着
YELLOW_RADIUS = 10
YELLOW_MAX = 3                    # 场上同时最多几只（2026-11-12 加：不限的话它们会越积越多，
                                  # 轮流咬 = 老者永久硬直，一个字都写不出来）
YELLOW_HP = 2                     # **两剑**（作者定）
# 剑对其他怪：**一剑就死**（红怪、紫怪没有 hp，砍中直接移除）—— 作者 2026-11-12 定
YELLOW_BITE_DIST = 16.0           # 够到老者的距离（体型比红怪大）
YELLOW_BITE_CD = 1.4              # 每咬一口的间隔
YELLOW_BITE_DAMAGE = 10           # 咬老者 10%
YELLOW_PLAYER_DAMAGE = 10         # 咬玩家 10%（作者 2026-11-12 定；比红怪 5% 疼一倍）
YELLOW_AGGRO_TIME = 7.0           # 被打之后盯玩家多久，然后回去找老者

# ==== 第三幕 · 老者与剑 ====
OLDMAN_HP = 100
OLDMAN_REVIVE_TIME = 4.0          # 按住 H 多久把他救起来（作者 2026-11-12 定）
OLDMAN_REVIVE_RANGE = 54.0        # 要站多近才能救
OLDMAN_REVIVE_HP = 50             # 救起来之后有多少血
OLDMAN_BLAST_RADIUS = 92.0        # 救起来那一下把他身边的黄怪震开的半径
                                  # （没有这一下会滚成「起来→被咬→又倒」的死循环）
SWORD_RANGE = 36.0                # 挥剑的够到距离（约一格半）
SWORD_CD = 0.34                   # 两次挥剑的间隔
SWORD_SWING_TIME = 0.18           # 挥砍的视觉时长

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
TOAST_TIME = 2.2                 # 嘀咕（飘字）活多久
TOAST_GAP = 2.5                  # 同一句嘀咕多久内不重复（比心声短：它是反馈，不是台词）
TOAST_MAX = 2                    # 同时最多几条：多了会糊在头顶
TOAST_LIFT = 46                  # 飘在玩家头顶上方多少像素（约一个身位）
MONO_REPEAT_GAP = 4.0             # 同一句心声在关闭后多久内不再弹：连续涂错只冻一次，
                                  # 否则一场战斗要按几十次回车（作者 2026-11-12 选的范围）
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
SC_R = 21                         # 重开一局
SC_U = 24                         # 挥剑（第三幕，拿到剑之后）—— 作者指定的键，别再自己换
SC_H = 11                         # 救老者（第三幕，他倒下之后按住 4 秒）
SC_M = 16                         # 铺开 / 卷起地图（只在拿到地图后有效）
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

# ==== 第三幕：老者替你写格式信息 ====
# 他经验老到（不用走过去，抬手就落一格），但手慢 —— 这个间隔就是这一幕的节奏旋钮。
# ⚠️ 他**必须走到那一格才落笔**（作者 2026-11-12），所以这一幕的节奏 = 他走多远 + 停多久。
SCRIBE_WALK_SPEED = 88.0          # 他走路的速度（玩家约 215，他慢得多）
SCRIBE_PAUSE = 0.9                # 站定之后停多久再落笔（秒）
                                  # 2026-11-13 作者：格式信息要「难涂」—— 他每格从 0.35 拉到 0.9
FORMAT_HOLD_TIME = 0.8            # 玩家自己补格式信息时，必须**按住 J 满这么久**才写得动
                                  # （普通格仍是一按就成；作者 2026-11-13）
OLDMAN_STAGGER = 0.7              # 被咬一口后笔停多久（2026-11-12 作者采纳：
                                  # 不加这个「守老者」就是假的 —— 实测玩家全程不动他也能写完）
                                  # ⚠️ 必须 < `YELLOW_BITE_CD`(1.4)。调成 1.5 试过：一只黄怪咬住
                                  # 就是**永久硬直**，他一个字都写不出来，整幕直接卡死
SCRIBE_FLASH = 0.45               # 他落笔那一下的暖色闪光（和红怪/紫怪的闪光区分开）

# ==== 第四幕 · 扫（sweep）2026-11-14 ====
# 数据区没有结构可讲，只能一格一格填；但让玩家按一百次 J 是搬砖，所以这一幕换动词：
# 按住 J 走过**灰域**就自动制造黑域，没照过的格直接跳过（不写、也不算脏格）。
# 于是这一幕的技能从「手快」变成「照哪儿、怎么走」。
MIRAGE_RADIUS_ACT4 = 3            # 7×7：照一次 49 格，走完要 6.4 秒 > 褪色 5 秒 —— 覆盖不完，必须取舍
OLDMAN_REPAIR_PAUSE = 0.6         # 第四幕：他补骨架时站定多久落笔（比第三幕写格式快一点）
ALMOST_OWE = 15                   # 第四幕剩下这么多格时嘀咕一句「别停」（只一次）

# ==== 第五幕 · 读（read）2026-11-14 ====
# 这一幕**不涂新格**：侵蚀把几个码字吃掉，玩家把错误压进容错容量就能被读出来。
# ⚠️ 容量按**码字**算，不按格算：v1-L 有 7 个纠错码字，t = 3 —— **一格错也毁一个码字**。
# `qr.ERROR_TOLERANCE` 就是那个 3，别在这儿另写一个。
ERODE_BLOCKS = 9                  # 开场被侵蚀掉几个码字（9 > 3，所以至少得修 6 块）
PURPLE_SPAWN_PER_MIN_ACT5 = 3.0   # 20 秒一只：这一幕要的是"取舍"，不是"手忙脚乱"
SCAN_TIME = 2.6                   # 码被读出来那一下：扫描束从上扫到下用多久
ERODE_CAP = 12                   # 侵蚀最多吃到 12 块就停手（"Never all of it"）
                                  # 不封顶的话，放着不管 90 秒会坏 23 块 —— 那不是难，是无解
ERODE_EVERY = 6.0                 # 侵蚀不会停：每 6 秒再吃掉一个码字（只在战斗里吃）
                                  # 所以「压到 3 块」不是终点 —— 得压住它 2.6 秒，让它读出来
