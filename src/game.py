# -*- coding: utf-8 -*-
"""游戏主类：状态机、每帧更新、输入分发。

只管「规则」：画法在 ui.py，数值在 config.py，台词在 story.py。

第一幕（含剧情层）的相位：
    TITLE
      └ INTRO      碎码动画 → 只剩脚下 5×5 → M1
        └ TUTORIAL 提示走路 → 移动满 5 秒 → 提示 Shift → 第一次照出灰域 → M2
          └ FREE_ROAM  老者驱赶两只红怪（狠话 → M3）；可选看死怪 / 道具；靠近按 T 呼喊
            └ DIALOG   回车逐句；坛内 / 坛外两条支线在指定句汇合
              └ GAP    老者离开 → 10 秒空档（**检查点打在这里**）
                └ BATTLE  红怪来袭：涂满 100 格
                  └ CLEAR   圣坛发光 → 走进圣坛 → 圆形波清场
                    └ REWARD  BAG / MAP 浮出 → 按 B 拾取 → 光扩散
                      └ END  ACT 1 — END
    战斗相位血量归零 → DEAD → 回到 GAP 起点
"""

import math
import random

import pygame

from src import sfx, story
from src.board import Board
from src.config import (
    BANNER_TIME, CALL_RANGE_PX, CELL, CLEAR_WAVE_HOLD, CLEAR_WAVE_SPEED, C_BG, C_MIRAGE, C_MONSTER, C_OLDMAN,
    C_PLAYER, C_PURPLE, CLOSE_RANGE_PX, DEBRIS_ANGLE, DEBRIS_DEATH, DEBRIS_DRAG, DEBRIS_SHRINK,
    DEBRIS_POP, DEBRIS_PULL, DEBRIS_PULL_EASE, DEBRIS_UP, FPS,
    GAP_SECONDS, HEALTH_MAX, HINT_TIME, HIT_DAMAGE, INTRO_FADE, INTRO_FALL, INTRO_SHOW, MIRAGE_ALPHA_MAX,
    CLEAR_GLOW_TIME, MINI_WAVE_REACH, DLG_CPS, DLG_FONT, DLG_LAST_MIN_SHOW, DLG_NAME_FONT, INTRO_TOTAL, MAP_OPEN_TIME,
    ITEM_PICK_RANGE,
    ITEM_RISE_TIME, MONO_CPS, MONO_FADE_OUT, MONO_FONT, MONO_REPEAT_GAP, MONOLOGUE_TIME, OLDMAN_CELL,
    TOAST_GAP, TOAST_MAX, TOAST_TIME,
    OLDMAN_BLAST_RADIUS, OLDMAN_HP, OLDMAN_REVIVE_HP,
    OLDMAN_REVIVE_RANGE, OLDMAN_REVIVE_TIME, PROMPT_FONT,
    OLDMAN_LEAVE_SPEED, OLDMAN_RUN_SPEED, PLAYER_GLOW_R, PLAYER_START_CELL, PROP_DEAD_CELL, PROP_RANGE_PX,
    PROP_TOOL_CELL, RED_RADIUS, RED_SPAWN_ACCEL, RED_SPAWN_ACCEL_PERIOD, RED_SPAWN_PER_MIN,
    RED_SPD_JITTER,
    RED_SPEED, REWARD_DELAY, REWARD_WAIT, SC_B, SC_ENTER, SC_ESC, SC_F1, SC_J, SC_K, SC_KP_ENTER,
    SC_H, SC_M, SC_R, SC_SHIFT, SC_SPACE, SC_T, SC_U, SHAKE_LEAD, SHAKE_SEQ, SHAKE_STEP, SPAWN_ORIGIN,
    SPAWN_PX,
    SCRIBE_FLASH, SCRIBE_PAUSE, SCRIBE_WALK_SPEED, FORMAT_HOLD_TIME, SPREAD_TIME, STAIN_DAMAGE, STAIN_LIMIT,
    SWORD_CD, SWORD_RANGE, SWORD_SWING_TIME, TARGET_N,
    TARGET_OFFSET,
    THREAT_TIME, VALID, WHITE, YELLOW_BITE_DAMAGE, YELLOW_FIRST_DELAY, YELLOW_PLAYER_DAMAGE,
    YELLOW_MAX, YELLOW_SPAWN_PER_MIN,
    ANOMALY_MISS_LIMIT, TUTORIAL_MOVE_SECONDS, WINDOW_H, WINDOW_W,
    A2_OPEN_SECONDS, PURPLE_FIRST_DELAY, PURPLE_HIT_DAMAGE, PURPLE_SPAWN_PER_MIN,
    PURPLE_SPAWN_PER_MIN_ACT3, PURPLE_SPAWN_PER_MIN_ACT4,
    MIRAGE_RADIUS_ACT4, ALMOST_OWE, ERODE_BLOCKS, PURPLE_SPAWN_PER_MIN_ACT5, SCAN_TIME,
    ERODE_EVERY, ERODE_CAP, OLDMAN_REPAIR_PAUSE
)
from src.entities import Item, Monster, OldMan, Player, PurpleOne, SceneRed, YellowOne
from src.grid import altar_center, cell_center
from src.input_state import InputState
from src.qr import (ERROR_TOLERANCE, format_dark_cells, generate_target, module_table,
                      required_cells, structural_black_cells)
from src.ui import (draw_dead, draw_dialog, draw_end, draw_hud, draw_title, draw_world,
                    make_stain_tile)

# 可移动 / 可涂的相位
MOVE_STATES = ("TUTORIAL", "FREE_ROAM", "GAP", "BATTLE", "CLEAR", "REWARD", "A2_OPEN")
PAINT_STATES = ("TUTORIAL", "FREE_ROAM", "GAP", "BATTLE", "A2_OPEN")

# ==== 音效（可选：设备开不出来就静音，绝不拖垮游戏）====


class _Audio:
    """把 sfx.py 合成的 WAV 包成 pygame.mixer.Sound，按名播放。

    mixer 初始化失败（无声卡 / 权限）时静默降级为 no-op，游戏照常跑。
    """

    def __init__(self):
        self.enabled = False
        self._sounds = {}
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            for name in sfx.SOUNDS:
                self._sounds[name] = pygame.mixer.Sound(buffer=sfx.build(name))
            self.enabled = True
        except Exception:
            self.enabled = False
            self._sounds = {}

    def play(self, name):
        if not self.enabled:
            return
        s = self._sounds.get(name)
        if s is not None:
            s.play()


# ==== 游戏主类 ====


class Game:
    def __init__(self, window):
        self.window = window
        self.canvas = pygame.Surface((WINDOW_W, WINDOW_H))
        self.screen = self.canvas
        self.scale = window.get_width() / float(WINDOW_W)
        self.needs_scale = window.get_width() != WINDOW_W
        self.input = InputState()
        self.running = True
        self.debug = False
        self.last_sc = -1
        self._last_dt = 1.0 / FPS
        self.audio = _Audio()

        # 字体只建一次
        self.f_small = pygame.font.Font(None, 21)
        self.f_main = pygame.font.Font(None, 27)
        self.f_panel = pygame.font.Font(None, 30)
        self.f_mid = pygame.font.Font(None, 46)
        self.f_big = pygame.font.Font(None, 104)
        self.f_tiny = pygame.font.Font(None, 18)      # 道具标签
        self.f_dlg_name = pygame.font.Font(None, DLG_NAME_FONT)  # 对话名牌
        self.f_dlg = pygame.font.Font(None, DLG_FONT)         # 对话台词
        self.f_mono = pygame.font.Font(None, MONO_FONT)       # 内心独白
        self.f_prompt = pygame.font.Font(None, PROMPT_FONT)   # 底部提示

        # 复用贴图（每帧新建 Surface 会掉帧）
        self.mirage_tile = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.mirage_tile.fill(C_MIRAGE)
        self.ghost = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.ghost.fill((*C_MIRAGE, 255))
        self.glow = pygame.Surface((PLAYER_GLOW_R * 2, PLAYER_GLOW_R * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.glow, (*C_PLAYER, 42), (PLAYER_GLOW_R, PLAYER_GLOW_R), PLAYER_GLOW_R)
        # 红怪身下的一圈暗红光：贴图里现画会掉帧，预生成一张
        self.red_glow = pygame.Surface((RED_RADIUS * 2 + 20, RED_RADIUS * 2 + 20), pygame.SRCALPHA)
        pygame.draw.circle(self.red_glow, (*C_MONSTER, 22),
                           (RED_RADIUS + 10, RED_RADIUS + 10), RED_RADIUS + 5)
        self.flash_surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.flash_surf.fill((*C_MONSTER, 120))
        self.flash_surf_purple = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.flash_surf_purple.fill((*C_PURPLE, 130))
        # 第三幕：老者落笔的暖色闪光（和「被咬红」「被清紫」区分开 —— 这是好事发生）
        self.flash_surf_scribe = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.flash_surf_scribe.fill((*C_OLDMAN, 110))
        self.stain_tile = make_stain_tile()
        self.shake_buf = pygame.Surface((WINDOW_W, WINDOW_H))
        self.spread_surf = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)

        # --- 状态 ---
        self.state = "TITLE"
        self.menu_t = 0.0
        self.rng = random.Random()
        self.target = []
        self.qr_content = ""
        self.must = set()
        self.cw_modules = {}                          # 第五幕：码字编号 → [(r, c, 该黑吗)]
        self.fn_modules = []                          # 第五幕：骨架格 [(r, c, 该黑吗)]
        self.scan_t = 0.0
        self.erode_t = 0.0
        self.end_line = ""                            # 结局页副标题（读出来的内容）
        self.board = None
        self.player = None
        self.oldman = None
        self.oldman_turned = False
        self.has_sword = False                        # 第二幕收尾拿到（M2 才能用）
        self.dlg_after = None                         # 对话结束之后去哪（第三幕说完就开打）
        # 第三幕：老者替你写格式信息
        self.format_cells = set()                     # 本幕该黑的格式格（主网格坐标）
        self.format_seen = set()                      # 已经写黑过的 → 用来发现「又被吃掉了」
        self.format_warned = False
        self.scribe_cells = []                        # 格式信息的 20 个位置（清单，测试用）
        self.scribe_target = None                     # 当前锁定的那一格（写完就清空，下一帧重挑）
        self.scribe_i = 0                             # **累计写过几格**（只增，给测试看「他在干活」）
        self.scribe_done_said = False                 # 「读通了，剩下归你」说过没有
        self.stagger_said = False                     # 「被咬断」那句说过没有
        self.scribe_t = 0.0
        self.scribe_writing = False                   # False=在走 / True=站定了准备落笔
        self.scribe_said = False
        self.fill_t = 0.0                             # 按住 J 写格式格的进度（0 → FORMAT_HOLD_TIME）
        self.fill_cell = None                         # 这个进度属于哪一格（换格就从 0 数）
        self.hold_said = False                        # 「格式格要按住」教过一次没有
        self.almost_said = False                      # 第四幕「快写完了」那句说过没有
        # 第四幕：老者回来补骨架（定位/定时/格式/暗模块），数据区他一格不碰
        self.repair_cells = set()
        self.repair_target = None
        self.repair_writing = False
        self.repair_t = 0.0
        self.repair_i = 0
        self.frame_said = False                       # 第五幕「骨架归他」那句说过没有
        # 第三幕 M2：黄怪 / 老者倒下与救援 / 挥剑
        self.yellows = []
        self.yellow_t = 0.0
        self.yellow_spawned = 0
        self.revive_t = 0.0                           # 按住 H 的累计时间（0 → OLDMAN_REVIVE_TIME）
        self.down_said = False
        self.swing_t = 0.0                            # 挥砍的视觉残留
        self.sword_cd = 0.0
        self.health = HEALTH_MAX
        self.monsters = []
        self.claims = {}
        self.scene_reds = []

        self.map_open = False                        # 地图是不是铺开着
        self.map_t = 0.0                             # 铺开进度 0（卷着）→ 1（全展开）
        self.act = 1                                 # 第几幕（第二幕复用同一个棋盘）
        self.purples = []                            # 第二幕的紫怪（the purple one）
        self.purple_t = 0.0                          # 距离上一只紫怪的计时
        self.purple_spawned = 0                      # 本幕已经来过几只（首只要 8 秒）
        self.open_t = 0.0                            # 第二幕开场的计时
        self.anim_t = 0.0                            # 只给贴图动画用（呼吸 / 触须 / 光标闪）
        self.elapsed = 0.0
        self.spawn_rate = RED_SPAWN_PER_MIN
        self.spawn_acc = 0.0
        self.accel_step = 0
        self.checkpoint = None

        # 开场动画
        self.intro_t = 0.0
        self.debris = []
        self.shake_t = 0.0
        self.shake_started = False
        self.shake_off = (0, 0)
        self.burst_done = False
        self.hint_alpha = 0

        # 文本通道
        self.mono_text = ""
        self.mono_t = 0.0
        self.mono_total = 0.0
        # 心声会**冻住整个世界**等回车（作者 2026-11-12）：
        #   mono_hold    True = 暂停中（update 直接 return，只走打字机）
        #   mono_elapsed 出现多久了（打字机 + 淡入）
        #   mono_type_time 这一句打完要多久
        #   mono_gap / mono_last 同句冷却：连续涂错只冻一次
        self.mono_hold = False
        self.mono_elapsed = 0.0
        self.mono_type_time = 0.0
        self.mono_gap = 0.0
        #   toasts 嘀咕（不冻世界的反馈）：[[文字, 活了多久, 寿命, 说话人], ...]
        self.toasts = []
        self.mumble_last = ""
        self.mumble_gap = 0.0
        self.mono_who = ""
        self.mono_last = ""
        self.hint_text = ""
        self.hint_t = 0.0
        self.prompt_text = ""
        self.threat_t = 0.0
        self.banner_text = ""
        self.banner_t = 0.0
        self.banner_total = 1.0

        # 教程
        self.move_time = 0.0
        self.last_cell = None
        self.reveal_used = False
        self.looked = False             # 「认真看过一次地面」：T 的提示要等它
        self.taught_write = False       # 第一笔落下去之前，一直教「站在灰上按 J」
        self.tut_t = 0.0                # 教程计时：站着不动的玩家也得收到提示
        self.anomaly_miss = 0
        self.stain_warned = False
        self.wipe_warned = False                     # 第二幕：第一次被清行的独白只放一次

        # 过场
        self.cs_t = 0.0
        self.cs_red_in = False
        self.cs_flee = False
        self.cs_m3 = False
        self.oldman_faced_altar = False

        # 对话
        self.dlg_lines = None
        self.dlg_i = 0
        self.dlg_t = 0.0
        self.dlg_phase = "talk"
        self.dlg_run_t = 0.0
        self.dlg_hold = 0.0
        self.dlg_t = 0.0

        # 可选互动
        self.prop_done = {"dead": False, "tool": False}

        # 清屏 / 奖励
        self.clear_phase = None
        self.clear_t = 0.0
        self.wave_r = 0.0
        self.glow_t = 0.0
        self.items = []
        self.has_bag = False
        self.has_map = False
        # 地图上记的东西：**每一幕收尾那一瞬**圣坛的样子（21×21 的 (tr,tc) 集合）。
        # 本幕中途的涂改 / 怪物清掉的格子都不实时上图 —— 见 capture_map()。
        self.map_cells = set()
        self.map_act = 0                             # 这份记录是第几幕收尾拍的
        self.reward_phase = None
        self.reward_t = 0.0
        self.spread_r = 0.0
        self.gap_t = 0.0

    # ---------- 开局 ----------
    def start_act(self):
        self.act = 1
        self.target, self.qr_content = generate_target(self.rng)
        self.must_all = required_cells(self.target, act=self.act)
        # 第一幕分两波（2026-11-14）：先写完自己醒来的那个角（左下定位图案 33 格）→ 一次清屏 →
        # 再写另外两个角 + 暗模块（67 格）。理由：100 格是全程最长的活，却压在玩家最不熟练的时候；
        # 拆开之后「清屏」这个爽点在第一幕就出现一次，而不是只在幕末。
        self.act1_wave = 1
        self.must = self.wave1_cells()
        self.board = Board(self.target, self.must)
        self.player = Player()
        self.oldman = OldMan(OLDMAN_CELL, facing=0)      # 背对玩家：朝世界外（上方）
        self.oldman_turned = False
        self.health = HEALTH_MAX
        self.monsters = []
        self.purples = []
        self.purple_t = 0.0
        self.purple_spawned = 0
        self.open_t = 0.0
        self.claims = {}
        self.scene_reds = []
        self.elapsed = 0.0
        self.spawn_acc = 0.0
        self.spawn_rate = RED_SPAWN_PER_MIN
        self.accel_step = 0

        self.reset_mono()
        self.hint_text, self.hint_t = "", 0.0
        self.prompt_text = ""
        self.threat_t = 0.0
        self.banner_text, self.banner_t = "", 0.0

        self.move_time = 0.0
        self.last_cell = self.player.cell
        self.reveal_used = False
        self.looked = False             # 「认真看过一次地面」：T 的提示要等它
        self.taught_write = False       # 第一笔落下去之前，一直教「站在灰上按 J」
        self.tut_t = 0.0                # 教程计时：站着不动的玩家也得收到提示
        self.anomaly_miss = 0
        self.stain_warned = False
        self.wipe_warned = False

        self.cs_t, self.cs_red_in, self.cs_flee, self.cs_m3 = 0.0, False, False, False
        self.oldman_faced_altar = False
        self.dlg_lines, self.dlg_i, self.dlg_hold = None, 0, 0.0
        self.dlg_show_t = 0.0
        self.dlg_phase = "talk"
        self.prop_done = {"dead": False, "tool": False}

        self.clear_phase, self.clear_t, self.wave_r, self.glow_t = None, 0.0, 0.0, 0.0
        self.mini_wave = False                       # 第一幕第一波那种「只放波、不放道具」的清屏
        self.items = []
        self.has_bag = self.has_map = self.has_sword = False
        self.format_cells = set()
        self.format_seen = set()
        self.format_warned = False
        self.scribe_cells = []
        self.scribe_target = None
        self.scribe_i = 0
        self.scribe_t = 0.0
        self.scribe_writing = False
        self.scribe_said = False
        self.scribe_done_said = False
        self.fill_t = 0.0
        self.fill_cell = None
        self.hold_said = False
        self.almost_said = False
        self.taught_write = False
        self.looked = False
        self.tut_t = 0.0
        self.repair_cells = set()
        self.repair_target = None
        self.repair_writing = False
        self.repair_t = 0.0
        self.frame_said = False
        self.stagger_said = False
        self.dlg_after = None
        self.yellows = []
        self.yellow_t = 0.0
        self.yellow_spawned = 0
        self.revive_t = 0.0
        self.down_said = False
        self.swing_t = 0.0
        self.sword_cd = 0.0
        self.map_cells = set()                        # 重开一局：地图上还没有任何一幕的记录
        self.map_act = 0
        # 地图必须收起来：重开后没有地图（`has_map=False`），但 `map_open` 若留着 True，
        # 涂改就会被「捧着纸」永久封住，而且按 M 也解不开（M 要求 has_map）—— 死锁
        self.map_open = False
        self.map_t = 0.0
        self.reward_phase, self.reward_t, self.spread_r = None, 0.0, 0.0
        self.gap_t = 0.0

        # 开场动画：完整码铺出 → 抖 → 碎成碎片 → 只剩脚下 5×5
        self.intro_t = INTRO_TOTAL
        self.debris = []
        self.burst_center = cell_center(*self.player.cell)   # 塌陷的收敛点：脚下，不是屏幕中心
        self.shake_t = 0.0
        self.shake_started = False
        self.shake_off = (0, 0)
        self.burst_done = False
        self.hint_alpha = 0

        self.state = "INTRO"
        self.input.held.clear()

    def wave1_cells(self):
        """第一幕第一波要写的格：**左下定位图案**的 33 个黑格。

        出生点 `(19,5)` 就在这一块的 3×3 黑核正中 —— 所以第一波是「把你醒来的那个角补完」，
        不是随机切一刀。⚠️ 出生点换到哪个角，这里就得跟着换：
        否则一睁眼脚下没有活，开场那片灰是空的，`reveal_around` 也照不出东西（2026-11-14 教训）。
        """
        orr, occ = TARGET_OFFSET
        return {(orr + r, occ + c) for r in range(14, 21) for c in range(7) if self.target[r][c]}

    def start_wave2(self):
        """第一波清完：换回整张码，接着写另外两个角和暗模块。

        ⚠️ 这里**重打检查点**（state=BATTLE）：第一波写完是一个真正的里程碑，
        死在第二波不该被踢回「什么都没写」的开场。
        """
        self.act1_wave = 2
        self.must = set(self.must_all)
        self.board.set_must(self.must)
        self.state = "BATTLE"
        self.mini_wave = False
        self.clear_phase = None
        self.clear_t = 0.0
        self.wave_r = 0.0
        self.spawn_acc = 0.0
        owe = len(self.must) - self.board.progress()
        self.show_hint(story.HINT_WAVE2 % owe, 4.0)
        self.say(story.A1_WAVE)
        self.checkpoint = self.make_checkpoint()

    def next_act(self):
        """幕结束画面按下回车：1 → 2 → 3 → 4 → 5；第五幕之后回标题。"""
        if self.act < 2:
            self.start_act2()
        elif self.act < 3:
            self.start_act3()
        elif self.act < 4:
            self.start_act4()
        elif self.act < 5:
            self.start_act5()
        else:
            self.state = "TITLE"
            self.menu_t = 0.0
            self.input.held.clear()

    def _begin_act(self, act):
        """开一幕时的**公共复位**（第二、三幕共用）。

        ⚠️ 这里不动 `must` / `state` / 老者 —— 每一幕的开场方式不一样，交给各自的 start_actN。
        ⚠️ 也**不要**重置 `has_bag` / `has_map` / `has_sword`：拿到的道具跨幕一直带着。
        """
        self.act = act
        self.health = HEALTH_MAX
        self.monsters = []
        self.purples = []
        self.claims.clear()
        self.scene_reds = []
        self.elapsed = 0.0
        self.spawn_acc = 0.0
        self.spawn_rate = RED_SPAWN_PER_MIN
        self.accel_step = 0
        self.purple_t = 0.0
        self.purple_spawned = 0
        self.wipe_warned = False
        self.hint_text, self.hint_t = "", 0.0
        self.prompt_text = ""
        self.threat_t = 0.0
        self.banner_text, self.banner_t = "", 0.0
        self.items = []
        self.clear_phase, self.clear_t, self.wave_r, self.glow_t = None, 0.0, 0.0, 0.0
        self.reward_phase, self.reward_t, self.spread_r = None, 0.0, 0.0
        self.dlg_lines, self.dlg_after = None, None
        self.reset_mono()
        self.format_cells = set()
        self.format_seen = set()
        self.format_warned = False
        self.scribe_cells = []
        self.scribe_target = None
        self.scribe_i = 0
        self.scribe_t = 0.0
        self.scribe_writing = False
        self.scribe_said = False
        self.scribe_done_said = False
        self.fill_t = 0.0
        self.fill_cell = None
        self.hold_said = False
        self.almost_said = False
        # ⚠️ 这里**故意不复位** taught_write / looked：Shift 和 J 只教一次，
        # 每一幕开头再把提示顶出来就是噪音（2026-11-14 审计发现）。只有 start_act（重开一局）才清。
        self.tut_t = 0.0
        self.repair_cells = set()
        self.repair_target = None
        self.repair_writing = False
        self.repair_t = 0.0
        self.frame_said = False
        self.stagger_said = False
        self.yellows = []
        self.yellow_t = 0.0
        self.yellow_spawned = 0
        self.revive_t = 0.0
        self.down_said = False
        self.swing_t = 0.0
        self.sword_cd = 0.0
        if self.oldman is not None:                   # 默认他不在场，谁需要谁把他放回来
            self.oldman.gone = True
            self.oldman.leaving = False

    def start_act2(self):
        """第一幕结束 → 第二幕。

        **不清空棋盘**（作者定）：第一幕涂好的 100 格原地保留，本幕只多 6 格定时图案。
        所以这里不能重播碎码动画，只换必涂格集合 + 复位血量/怪物/计时。
        """
        self._begin_act(2)
        # 同一个 target、同一个 board：只把必涂格从 100 扩到 106
        self.must = required_cells(self.target, act=2)
        self.must_all = set(self.must)                   # 幕变了，must_all 也跟着幕走
        self.board.set_must(self.must)

        # 开场：一行独白，不打断操作；读完自动进战斗
        self.state = "A2_OPEN"
        self.open_t = 0.0
        self.say(story.A2_M1)
        self.audio.play("clear")                     # 复用圣坛低鸣：仪式又开始了
        self.checkpoint = self.make_checkpoint()

    def start_act3(self):
        """第二幕结束 → 第三幕：**老者回来了**，带回「怎么读这张码」。

        这一幕玩家**不写格式信息** —— 老者走过去一格一格写（`SCRIBE_WALK_SPEED` / `SCRIBE_PAUSE`）。
        玩家要做的是守住他写下的东西：被怪吃掉的格式格，他**不回头补**，得玩家自己补。
        """
        self._begin_act(3)
        self.must = required_cells(self.target, act=3)   # 106 + 格式信息里该黑的 10~20 格
        self.must_all = set(self.must)
        self.board.set_must(self.must)

        # 他按顺序写：先把「贴着左上的那一份」写完，再写「右上 + 左下」那一份
        self.format_cells = format_dark_cells(self.target)
        self.scribe_cells = sorted(self.format_cells)

        # 老者回来，站在坛外老位置，这回面朝坛内
        self.oldman = OldMan(OLDMAN_CELL, facing=1)
        self.oldman_turned = True

        # 先说话，说完直接开打（`after="BATTLE"`，他这次不走了，所以 tail=False）
        self.start_dialog(story.DIALOG_THREE, tail=False, after="BATTLE")
        self.audio.play("clear")
        self.checkpoint = self.make_checkpoint()

    def start_act4(self):
        """第三幕结束 → 第四幕：**骨架齐了，剩下的是「内容」**。

        这一幕换动词：不再一格一格按 J，而是**按住 J 扫**（`sweep`）——
        走过照出来的灰域就自动制造黑域；没照过的格直接跳过（不写、也不算脏格）。
        所以压力从「手快不快」变成「照哪儿、怎么走」，而灰域 5 秒就褪，
        7×7 的窗口走完要 6.4 秒 —— 覆盖不完，必须取舍。

        数据区没有结构可讲（它就是这张码的内容），所以这一幕没有新图案 ——
        只有紫怪回潮（4 只/分，一次清一行）和照旧的红怪：**你写多快，它吃多快**。

        **老者回来了（作者 2026-11-14）**：他只补**骨架** —— 定位图案、定时图案、
        固定黑点（暗模块）、格式信息，数据区他一格都不碰。分工正好接第三幕：
        他懂结构，不懂内容。所以玩家可以安心扫数据区，碎片由他兜着。
        """
        self._begin_act(4)
        self.must = required_cells(self.target, act=4)    # 整张码的所有黑格 206~244
        self.must_all = set(self.must)
        self.board.set_must(self.must)

        # 他只负责这一批格（结构黑格），玩家负责数据区
        self.repair_cells = structural_black_cells(self.target)

        # 他回来，站在坛外老位置（和第三幕同一个位置、同一朝向）
        self.oldman = OldMan(OLDMAN_CELL, facing=1)
        self.oldman_turned = True

        self.state = "BATTLE"
        self.spawn_rate = RED_SPAWN_PER_MIN
        self.say(story.A4_M1)
        self.show_hint(story.HINT_SWEEP, 6.0)
        self.audio.play("clear")
        self.checkpoint = self.make_checkpoint()

    def start_act5(self):
        """第四幕结束 → 第五幕：**读**。

        这一幕不涂新格。开场先被「侵蚀」掉几个**码字**（整块变白，`ERODE_BLOCKS=6`），
        玩家的活不是「把码补完」，而是**把错误压进容错容量**（`qr.ERROR_TOLERANCE = 3`）：
        3 个码字以内的错，纠错码自己能修回来，码就能被读出来。

        ⚠️ 容量按**码字**算：一格错也毁一个码字。所以「放弃一整块」和「错一格」代价一样，
        这才是这一幕要玩家做的判断 —— 不是再细心一点，是决定哪几块不要了。
        """
        self._begin_act(5)
        self.must = required_cells(self.target, act=4)    # 整张码（和第四幕同一套必涂格）
        self.must_all = set(self.must)
        self.board.set_must(self.must)
        self.cw_modules, self.fn_modules = module_table(self.target)

        # 老者也在场（作者 2026-11-14）：他**只补骨架** —— 定位图案、定时图案、
        # 暗模块、格式信息。这一幕紫怪清掉一整行时会连骨架一起清，
        # 而骨架坏一格就根本读不出来；他替你把这一头兜住，你才能专心压错误数。
        # 数据区（那 26 个码字）他一格不碰：那正是你要判断「放弃哪几块」的地方。
        self.repair_cells = structural_black_cells(self.target)
        self.oldman = OldMan(OLDMAN_CELL, facing=1)
        self.oldman_turned = True

        self.erode(ERODE_BLOCKS)                          # 侵蚀：挑几块整块抹掉
        self.erode_t = 0.0

        self.state = "BATTLE"
        self.spawn_rate = RED_SPAWN_PER_MIN
        self.say(story.A5_M1)
        self.audio.play("clear")
        self.checkpoint = self.make_checkpoint()

    def erode(self, n):
        """侵蚀 n 个码字：把它们该黑的格整块抹白（这就是这一幕开局的「欠账」）。

        只挑「黑格够多」的码字 —— 抹一个只有 2 格黑的码字，玩家看不出发生了什么，
        但 HUD 上照样 +1 错误，那是骗人。
        """
        n = min(n, max(0, ERODE_CAP - self.act5_errors()))   # 封顶在这儿，别指望调用方记得
        if n <= 0:
            return
        pools = [k for k, mods in self.cw_modules.items()
                 if sum(1 for (_, _, dark) in mods if dark) >= 4]
        if not pools:
            return
        # 只吃「还是好的」那些块：吃一块已经坏了的等于没吃，HUD 数字不动，玩家会以为卡了
        intact = [k for k in pools
                  if all((self.board.state[r][c] == VALID) if dark
                         else (self.board.state[r][c] == WHITE)
                         for (r, c, dark) in self.cw_modules[k])]
        for k in self.rng.sample(intact or pools, min(n, len(intact or pools))):
            for (r, c, dark) in self.cw_modules[k]:
                if dark:
                    self.board.state[r][c] = WHITE           # 只抹黑格：白格本来就是白的

    def tick_erode(self, dt):
        """侵蚀不会停：每 `ERODE_EVERY` 秒再吃掉一个码字，但**吃到 `ERODE_CAP` 就收手**。

        封顶的理由（2026-11-14 实测）：不封顶的话晾着不管 90 秒就坏到 23 块，
        玩家要修 20 块才够得着 3 —— 那不是难，是没有路。
        而且这一行也接上了 `A5_M1` 那句 `Never all of it`：它吃不完整张码。
        """
        self.erode_t += dt
        if self.erode_t >= ERODE_EVERY:
            self.erode_t = 0.0
            if self.act5_errors() < ERODE_CAP:
                self.erode(1)                        # 封顶由 erode() 自己保证
                self.audio.play("purple")

    def act5_errors(self):
        """现在有几个**码字**是坏的（第五幕的 HUD 数字，也是能不能读出来的唯一判据）。"""
        bad = 0
        for mods in self.cw_modules.values():
            for (r, c, dark) in mods:
                st = self.board.state[r][c]
                if (st != VALID) if dark else (st != WHITE):
                    bad += 1
                    break
        return bad

    def frame_broken(self):
        """骨架坏了几格（定位 / 定时 / 格式）。**一格都不能坏** —— 骨架坏了根本扫不到码。"""
        n = 0
        for (r, c, dark) in self.fn_modules:
            st = self.board.state[r][c]
            if (st != VALID) if dark else (st != WHITE):
                n += 1
        return n

    def enter_scan(self):
        """错误压进容量了：圣坛开始「读」这张码。

        ⚠️ 扫描**不清场**：怪被光定住不再动，但**侵蚀照吃**。
        所以「压到 3 块」不是终点 —— 得压住它 2.6 秒，让它读出来。
        """
        self.state = "SCAN"
        self.scan_t = 0.0
        self.hint_text, self.hint_t = "", 0.0
        self.claims.clear()
        self.audio.play("clear")
        self.say(story.A5_M3)

    def update_scan(self, dt):
        """扫描束从上往下走一遍：走完就进结局。

        ⚠️ 扫描期间**侵蚀暂停**（`tick_erode` 只在 `update_battle` 里走）。
        理由是公平：玩家看不见「还有几秒被侵蚀」，拿一个看不见的计时器去断他最后 2.6 秒，
        赢的时候只会觉得倒霉。难度全部放在「怎么把它压到 3 块」上。
        """
        self.scan_t += dt
        if self.scan_t < SCAN_TIME:
            return
        self.state = "END"
        self.menu_t = 0.0
        self.show_banner(story.ACT5_TITLE, 999.0)
        self.end_line = story.END_LINE % self.qr_content.upper()

    def pick_repair_target(self):
        """挑下一个要补的结构格：离他最近的、该黑却是白的。全好了就返回 None。"""
        need = [(r, c) for (r, c) in self.repair_cells if self.board.state[r][c] == WHITE]
        if not need:
            return None
        om = self.oldman
        if om is None:
            return need[0]
        px, py = om.pos.x, om.pos.y
        return min(need, key=lambda rc: (cell_center(*rc)[0] - px) ** 2
                   + (cell_center(*rc)[1] - py) ** 2)

    def update_repair(self, dt):
        """第四、五幕：老者补**骨架**（定位图案 / 定时图案 / 暗模块 / 格式信息）。

        作者 2026-11-14：「老者帮忙制造黑域，但是他只能修复定位图案、定时图案、
        固定黑点以及格式信息」。所以数据区他一格都不碰 —— 那是玩家的活。
        走位和落笔沿用第三幕那套（走过去、站定、停 `OLDMAN_REPAIR_PAUSE` 再写），
        只是不再需要长按、也不会「写完就清屏」。
        """
        om = self.oldman
        if om is None or om.gone or om.down:
            return
        if self.repair_target is None:
            self.repair_target = self.pick_repair_target()
            self.repair_writing = False
            if self.repair_target is None:
                return
        r, c = self.repair_target
        if self.board.state[r][c] != WHITE:           # 玩家先补上了 / 又被清成别的
            self.repair_target = None
            self.repair_writing = False
            return
        if not self.repair_writing:
            if om.move_toward(cell_center(r, c), SCRIBE_WALK_SPEED, dt):
                self.repair_writing = True
                self.repair_t = 0.0
                om.face_to(pygame.Vector2(*cell_center(r, c)))
            return
        self.repair_t += dt
        if self.repair_t < OLDMAN_REPAIR_PAUSE:
            return
        self.board.state[r][c] = VALID
        self.board.flash[(r, c)] = SCRIBE_FLASH       # 暖色一闪：和第三幕他写的格一个样子
        self.board.flash_kind[(r, c)] = "scribe"
        self.audio.play("paint")
        self.repair_i += 1
        self.repair_target = None
        self.repair_writing = False

    def pick_format_target(self):
        """挑下一个要写的格式格：**离他最近的那一格白的**。

        2026-11-12 起他会**回头补**（作者：紫怪把格式信息清了，让他再涂一遍就行），
        所以这里不是「按清单走一遍」，而是**每写完一格就重新找一次**。
        全都黑了就返回 None —— 那一刻格式信息写完了。
        """
        need = [(r, c) for (r, c) in self.format_cells if self.board.state[r][c] == WHITE]
        if not need:
            return None
        om = self.oldman
        if om is None:
            return need[0]
        px, py = om.pos.x, om.pos.y
        return min(need, key=lambda rc: (cell_center(*rc)[0] - px) ** 2 + (cell_center(*rc)[1] - py) ** 2)

    def update_scribe(self, dt):
        """第三幕：老者走过去，一格一格写格式信息。

        作者 2026-11-12 定的两条，缺任何一条这一幕都不成立：
          1. **他必须站到那一格上才落笔** —— 所以节奏由「路程」决定，不是由格数决定；
          2. **被咬一口就停手** `OLDMAN_STAGGER` 秒 —— 不加这条，实测玩家全程不动他也能 21.6 秒写完，
             「守老者」就是个摆设。

        他会**回头补**被怪吃掉的格式格（作者定的），所以没有「干完收工」这回事：
        只有「暂时没有白的格要写」，那一刻走 `on_scribe_idle()`。
        """
        self.check_format_broken()
        om = self.oldman
        if om is None or om.gone or om.down:          # 走了 / 倒下了就写不动了（第四幕他已离场）
            return

        if self.scribe_target is None:
            self.scribe_target = self.pick_format_target()
            self.scribe_writing = False
            if self.scribe_target is None:
                self.on_scribe_idle()
                return

        r, c = self.scribe_target
        if self.board.state[r][c] != WHITE:           # 玩家抢先涂了 / 已经被补上
            self.scribe_target = None
            self.scribe_writing = False
            return

        if not self.scribe_writing:
            if om.move_toward(cell_center(r, c), SCRIBE_WALK_SPEED, dt):
                self.scribe_writing = True            # 站定了
                self.scribe_t = 0.0
                om.face_to(pygame.Vector2(*cell_center(r, c)))
            return

        if om.stagger_t > 0:
            # 刚被咬：**这一笔写不下去**（进度归零，硬直过了重数），但他还能走 ——
            # 直接 return 会把他钉在原地，黄怪一多就是永久硬直（2026-11-12 踩过）
            self.scribe_t = 0.0
            return
        self.scribe_t += dt
        if self.scribe_t < SCRIBE_PAUSE:
            return

        self.board.state[r][c] = VALID
        self.board.flash[(r, c)] = SCRIBE_FLASH        # 暖色一闪：让玩家看见「是他写的」
        self.board.flash_kind[(r, c)] = "scribe"
        self.audio.play("paint")
        if not self.scribe_said:
            self.scribe_said = True
            self.say(story.A3_M1)
        self.scribe_i += 1                            # 累计写过几格（只增）
        self.scribe_target = None
        self.scribe_writing = False
        if self.board.is_complete():
            self.enter_clear()

    def on_scribe_idle(self):
        """格式信息暂时写完了（没有白的格式格要写）。

        如果整张码还没完成，**差的就是玩家自己该补的格** —— 说一句、并在底部点名还差几格。
        只喊一次：不喊玩家会以为游戏卡了；每帧喊又太吵。
        """
        if not self.scribe_done_said:
            self.scribe_done_said = True
            self.say(story.A3_READ, 3.0, who=story.OLD_MAN)
            left = max(0, len(self.must) - self.board.progress())
            if left:
                self.show_hint(story.HINT_FILL_REST % left, 5.0)
        if self.board.is_complete():
            self.enter_clear()

    def check_format_broken(self):
        """格式信息被你之外的东西弄掉了？第一次给一句提示 + 一句心声。

        玩家必须自己补 —— 老者不会回头（他正忙着往前写）。
        """
        for cell in self.format_cells:
            if self.board.state[cell[0]][cell[1]] == VALID:
                self.format_seen.add(cell)
            elif cell in self.format_seen:
                self.format_seen.discard(cell)
                if not self.format_warned:
                    self.format_warned = True
                    self.show_hint(story.HINT_FORMAT_BROKEN, 3.0)
                    self.mumble(story.A3_M2)

    def update_a2_open(self, dt):
        self.open_t += dt
        if self.open_t >= A2_OPEN_SECONDS:
            self.start_battle()

    def start_gap(self):
        """老者离开那一刻 = 检查点。"""
        self.state = "GAP"
        self.gap_t = 0.0
        self.prompt_text = ""
        self.dlg_lines = None
        if self.oldman is not None:               # 他已经走了
            self.oldman.gone = True
            self.oldman.leaving = False
        self.checkpoint = self.make_checkpoint()

    def make_checkpoint(self):
        return {
            "board": self.board.snapshot(),
            "health": self.health,
            "elapsed": self.elapsed,
            "spawn_rate": self.spawn_rate,
            "accel_step": self.accel_step,
            "act": self.act,
            "state": self.state,          # 第一幕回 GAP、第二幕回 A2_OPEN
            "must": set(self.must),
            "act1_wave": getattr(self, "act1_wave", 1),
            "bag": self.has_bag,          # 第一幕之后一直带着，回检查点不能丢
            "map": self.has_map,
            "sword": self.has_sword,      # 第二幕之后一直带着
            # ⚠️ 故意不存 map_cells / map_act：那是「每幕收尾拍下的定妆照」，
            # 只增不减的历史账。存进快照反而会让「回到本幕开头」把上一幕的记录抹掉。
        }

    def restore_checkpoint(self):
        cp = self.checkpoint
        self.board.restore(cp["board"])
        self.act = cp.get("act", 1)
        if "must" in cp:
            self.must = set(cp["must"])
            self.board.set_must(self.must)
        self.act1_wave = cp.get("act1_wave", 1)
        self.health = cp["health"]
        self.elapsed = cp["elapsed"]
        self.spawn_rate = cp["spawn_rate"]
        self.accel_step = cp["accel_step"]
        for m in self.monsters:
            m.claim(self.claims)
        self.monsters.clear()
        self.purples.clear()
        self.purple_t = 0.0
        self.purple_spawned = 0
        self.claims.clear()
        self.scene_reds.clear()
        self.items.clear()
        # 按检查点恢复：第一幕的检查点在拿道具之前（False），第二幕在拿之后（True）
        self.has_bag = cp.get("bag", False)
        self.has_map = cp.get("map", False)
        self.has_sword = cp.get("sword", False)
        self.spawn_acc = 0.0
        self.player.reset()
        self.hint_text, self.hint_t = "", 0.0
        self.reset_mono()
        self.threat_t = 0.0
        self.clear_phase, self.clear_t, self.wave_r = None, 0.0, 0.0
        self.reward_phase, self.reward_t, self.spread_r = None, 0.0, 0.0
        self.dlg_lines = None
        if self.oldman is not None:
            # 第一、二幕回到检查点时他早就走了；第三幕他就在坛边，不能让他「消失」
            self.oldman.gone = self.act < 3
            self.oldman.leaving = False
        self.yellows.clear()
        self.yellow_t = 0.0
        self.revive_t = 0.0
        self.down_said = False
        if self.oldman is not None and self.act >= 3:
            self.oldman.hp = OLDMAN_HP                   # 回到本幕开头：他也满血站起来
            self.oldman.down = False
        self.scribe_cells = []                           # 检查点里没存写格进度，回来重排
        if self.act >= 3:
            self.scribe_cells = sorted(self.format_cells)
            self.scribe_target = None
            self.scribe_i = 0
            self.scribe_t = 0.0
            self.scribe_writing = False
            self.scribe_done_said = False
            self.stagger_said = False
            self.format_seen = set()
            self.format_warned = False
        self.state = cp.get("state", "GAP")
        self.gap_t = 0.0
        self.open_t = 0.0
        self.input.held.clear()

    # ---------- 文本通道 ----------
    def reset_mono(self):
        """把心声相关状态全部归零（重开 / 换幕 / 回检查点都要走它）。"""
        self.mono_text = ""
        self.mono_t = 0.0
        self.mono_total = 0.0
        self.mono_hold = False
        self.mono_elapsed = 0.0
        self.mono_type_time = 0.0
        self.mono_gap = 0.0
        self.toasts = []
        self.mumble_last = ""
        self.mumble_gap = 0.0

    def say(self, text, secs=MONOLOGUE_TIME, who=None):
        """内心独白 / NPC 说话：**整个世界静止**，直到玩家按回车（作者 2026-11-12 定）。

        `who` 不传就是码序使（青名牌）；传 `story.OLD_MAN` 就是老者（暖米色名牌）。
        2026-11-12 起老者也会在这套框里说话（被打断 / 被救起 / 写完），不用另开一套界面。

        改这个是因为原来它会自己淡走、而世界照常跑 —— 玩家涂错一格，心声挡住半屏、
        怪还在打他，看不清也躲不掉。现在停下来，玩家读完再走。

        改这个是因为原来它会自己淡走、而世界照常跑 —— 玩家涂错一格，心声挡住半屏、
        怪还在打他，看不清也躲不掉。现在停下来，玩家读完再走。

        - 同一句在 `MONO_REPEAT_GAP` 秒内不重复弹：连续涂错只冻一次。
        - `secs` 现在只用来算「打完这一句要多久」（字数 / MONO_CPS），
          寿命不再由它决定 —— 由玩家按几次回车决定。
        """
        if text == self.mono_last and self.mono_gap > 0 and not self.mono_hold:
            return                                   # 冷却期内，同一句不重复冻屏
        self.mono_text = text
        self.mono_total = secs
        self.mono_elapsed = 0.0
        self.mono_hold = True
        self.mono_t = 0.0
        self.mono_last = text
        self.mono_who = who or story.SEQUENCER
        chars = len(text.replace("\n", ""))
        self.mono_type_time = max(0.30, chars / float(MONO_CPS))

    def advance_monologue(self):
        """回车：**第一下把字补完，第二下关闭继续**（和老者对话同一套手感）。

        返回 True = 这次按键被心声吃掉了。
        """
        if not self.mono_hold:
            return False
        if self.mono_elapsed < self.mono_type_time:
            self.mono_elapsed = self.mono_type_time  # 字还没打完 → 一次补完
        else:
            self.mono_hold = False
            self.mono_t = MONO_FADE_OUT               # 开始淡出
            self.mono_gap = MONO_REPEAT_GAP           # 同句冷却从「关闭」那一刻算
        return True

    def mumble(self, text, secs=TOAST_TIME, who=None):
        """嘀咕：**不冻世界**的反馈，飘在他头顶上方一行，2 秒淡掉。

        为什么和 `say()` 分开（作者 2026-11-14）：
        原来所有心声都冻世界 + 等回车，可「涂错一格」「被咬一口」这种事一分钟要发生十几次，
        每次都停车读一句，玩起来像被不断打断。真正的问题从来是**遮挡**（框占半屏、怪还在打你），
        不是世界在动 —— 所以反馈类改成不遮不挡的飘字，叙事类（进幕、老者说话、倒下）仍然停。

        同一句 `TOAST_GAP` 秒内不重复；同时最多 `TOAST_MAX` 条（新的把最老的顶掉）。
        """
        if text == self.mumble_last and self.mumble_gap > 0:
            return
        self.mumble_last = text
        self.mumble_gap = TOAST_GAP
        self.toasts.append([text, 0.0, secs, who or story.SEQUENCER])
        while len(self.toasts) > TOAST_MAX:
            self.toasts.pop(0)

    def show_hint(self, text, secs=HINT_TIME):
        """系统提示：底部一条，全大写。"""
        self.hint_text = text
        self.hint_t = secs

    def show_banner(self, text, secs=BANNER_TIME):
        self.banner_text = text
        self.banner_t = secs
        self.banner_total = secs

    # ---------- 事件 ----------
    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.on_click(*self.mouse_xy())
            return
        if e.type != pygame.KEYDOWN:
            return

        sc = e.scancode
        self.last_sc = sc                             # F1 调试用：最后按下的 scancode
        if sc == SC_F1:
            self.debug = not self.debug
            return

        st = self.state
        if sc == SC_ESC:
            if st == "TITLE":
                self.running = False
            elif st == "DIALOG":
                self.close_dialog()                      # 中途退出不卡死
            else:
                self.state = "TITLE"
                self.input.held.clear()
            return

        if st == "TITLE":
            if sc in (SC_ENTER, SC_KP_ENTER, SC_SPACE):
                self.start_act()
            return
        if st == "DEAD":
            if sc in (SC_ENTER, SC_KP_ENTER, SC_SPACE, SC_R):
                self.restore_checkpoint()
            return
        if st == "END":
            if sc in (SC_ENTER, SC_KP_ENTER, SC_SPACE, SC_R):
                self.next_act()
            return
        if st == "DIALOG":
            if sc in (SC_ENTER, SC_KP_ENTER):
                self.advance_dialog()
            return

        # 心声暂停中：世界停着，只认回车（继续）和 R（重开一局）
        if self.mono_hold:
            if sc in (SC_ENTER, SC_KP_ENTER, SC_SPACE):
                self.advance_monologue()
            elif sc == SC_R:
                self.start_act()
            return
        if st == "INTRO":
            return

        # ---- 以下都是可动相位 ----
        if sc == SC_R:
            self.start_act()
        elif sc == SC_U and self.has_sword and self.act >= 3 and st in PAINT_STATES:
            self.swing_sword()
        # 地图摊开 = 双手捧着纸，涂改 / 擦除 / 照异象全都做不了（作者 2026-11-12 定的代价）。
        # 挡在这里是为了给一句话的反馈；真正拦住动作的是 update() 里那个 `not self.map_open`。
        elif self.map_open and st in PAINT_STATES and (sc in (SC_J, SC_K) or sc in SC_SHIFT):
            self.map_busy()
        elif sc in SC_SHIFT:
            self.cast_anomaly()
        elif sc == SC_M and self.has_map and st in MOVE_STATES:
            self.map_open = not self.map_open
            self.fill_t = 0.0                            # 收纸 / 铺纸都算「手离笔」
            self.fill_cell = None
            self.audio.play("ui")
        elif sc == SC_T and st == "FREE_ROAM":
            self.try_call()
        elif sc == SC_B and st == "REWARD":
            self.try_pick()

    def on_click(self, x, y):
        if self.state == "TITLE":
            self.start_act()
        elif self.state == "DEAD":
            self.restore_checkpoint()
        elif self.state == "END":
            self.next_act()

    def mouse_xy(self):
        mx, my = pygame.mouse.get_pos()
        return int(mx / self.scale), int(my / self.scale)

    def shift_held(self):
        return any(self.input.down(sc) for sc in SC_SHIFT)

    # ---------- 更新 ----------
    def update(self, dt):
        self._last_dt = dt
        # 心声暂停：整个世界静止（连贴图动画、怪物、碎屑都停），只走打字机。
        # 必须放在最前面 —— 放后面的话怪还在这一帧里打过你（作者 2026-11-12）。
        if self.mono_hold:
            self.mono_elapsed += dt
            return
        self.anim_t += dt                            # 贴图动画的时基：所有相位都在走
        # 卷轴铺开 / 收起（和相位无关，看地图时世界照常跑）
        want = 1.0 if self.map_open else 0.0
        if self.map_t != want:
            step = dt / MAP_OPEN_TIME
            self.map_t = (min(1.0, self.map_t + step) if want > self.map_t
                          else max(0.0, self.map_t - step))
        st = self.state
        if st in ("TITLE", "DEAD", "END"):
            self.menu_t += dt
            return

        self.tick_timers(dt)

        if st == "INTRO":
            self.update_intro(dt)
            return
        if st == "DIALOG":
            self.update_dialog(dt)
            return

        if self.oldman is not None:
            self.oldman.update(dt)

        # 走动（CLEAR / REWARD 也要走：要走进圣坛、要走到道具旁）
        if st in MOVE_STATES:
            self.player.update(dt, self.input.dir4())
            self.note_move(dt)

        # 脚下涂改：按着 Shift 时涂不上去（异象和涂不能同时）；
        # 地图摊开时也不行 —— 两只手捧着纸，写字改字都没手（作者 2026-11-12）
        if st in PAINT_STATES and not self.map_open:
            if self.input.down(SC_J) and not self.shift_held():
                self.hold_paint(dt)
            elif self.input.down(SC_K):
                self.fill_t = 0.0
                self.fill_cell = None
                if self.board.start_erase(*self.player.cell):
                    self.audio.play("erase")            # 抹除：收回的一声上滑
            else:
                self.fill_t = 0.0
                self.fill_cell = None

        self.board.update(dt)

        if st == "TUTORIAL":
            self.update_tutorial(dt)
        elif st == "FREE_ROAM":
            self.update_roam(dt)
        elif st == "GAP":
            self.update_gap(dt)
        elif st == "A2_OPEN":
            self.update_a2_open(dt)
        elif st == "BATTLE":
            self.update_battle(dt)
        elif st == "CLEAR":
            self.update_clear(dt)
        elif st == "REWARD":
            self.update_reward(dt)
        elif st == "SCAN":
            self.update_scan(dt)

        if st in PAINT_STATES:
            if st != "TUTORIAL":                 # 教程自己有一套提示顺序，别抢
                self.update_look_prompt()
            self.update_write_prompt()

    def tick_timers(self, dt):
        if self.mono_gap > 0:
            self.mono_gap = max(0.0, self.mono_gap - dt)
        if self.mumble_gap > 0:
            self.mumble_gap = max(0.0, self.mumble_gap - dt)
        if self.toasts:
            for t in self.toasts:
                t[1] += dt
            self.toasts = [t for t in self.toasts if t[1] < t[2]]
        if self.hint_t > 0:
            self.hint_t = max(0.0, self.hint_t - dt)
        if self.mono_t > 0:
            self.mono_t = max(0.0, self.mono_t - dt)
            if self.mono_t == 0.0 and not self.mono_hold:
                self.mono_text = ""               # 淡出结束：连文字一起收掉
        if self.threat_t > 0:
            self.threat_t = max(0.0, self.threat_t - dt)
        if self.banner_t > 0:
            self.banner_t = max(0.0, self.banner_t - dt)

    def note_move(self, dt):
        """只有按着方向键在走才算「移动」。站着不动，计时一秒都不涨。"""
        if self.input.dir4() is not None:
            self.move_time += dt
            self.last_cell = self.player.cell

    # ---------- 开场动画 ----------
    def update_intro(self, dt):
        t = INTRO_TOTAL - self.intro_t
        self.intro_t -= dt

        if not self.shake_started and t >= INTRO_SHOW - SHAKE_STEP * SHAKE_LEAD:
            self.shake_t = SHAKE_STEP * len(SHAKE_SEQ)
            self.shake_started = True
        if not self.burst_done and t >= INTRO_SHOW:
            self.burst()
            self.burst_done = True

        if self.shake_t > 0:
            self.shake_t = max(0.0, self.shake_t - dt)
            total = SHAKE_STEP * len(SHAKE_SEQ)
            idx = int((total - self.shake_t) / SHAKE_STEP)
            self.shake_off = SHAKE_SEQ[min(idx, len(SHAKE_SEQ) - 1)]
        else:
            self.shake_off = (0, 0)

        # 塌陷：碎片被吸回脚下（k = 这一拍走了多少）
        if self.burst_done:
            k = min(1.0, max(0.0, (t - INTRO_SHOW) / INTRO_FALL))
            self._collapse_debris(dt, k)

        # 淡入只到「灰域最深」那一档，和醒来后脚下那一片无缝接上
        fade_start = INTRO_SHOW + INTRO_FALL
        if t >= fade_start:
            self.hint_alpha = int(MIRAGE_ALPHA_MAX * min(1.0, (t - fade_start) / INTRO_FADE))

        if self.intro_t <= 0:
            self.intro_t = 0.0
            self.debris.clear()
            self.shake_off = (0, 0)
            self.hint_alpha = 0
            self.enter_tutorial()

    def burst(self):
        """炸开：每一格变成一个**要被吸回去**的碎片。

        ⚠️ 收敛点是**玩家脚下**，不是屏幕中心（2026-11-14）。出生点挪到定位图案之后，
        从屏幕中心炸开会显得「我掉到了角落」；从脚下炸开再收回脚下，讲的是同一件事：
        这张码最后只剩你脚边那一小片。

        每个碎片存 `[x, y, vx, vy, scale, k]`，`max(CELL/2)` 是它的中心点。
        """
        orr, occ = TARGET_OFFSET
        pr, pc = self.player.cell
        cx, cy = cell_center(pr, pc)
        self.burst_center = (cx, cy)
        self.debris = []
        far = math.hypot(WINDOW_W / 2.0 - cx, WINDOW_H / 2.0 - cy) or 1.0
        for tr in range(TARGET_N):
            row = self.target[tr]
            for tc in range(TARGET_N):
                if not row[tc]:
                    continue
                x, y = cell_center(orr + tr, occ + tc)
                dx, dy = x - cx, y - cy
                d = math.hypot(dx, dy) or 1.0
                # 离得越远炸得越快：远处先散，近处先被吸回来，中间不会挤成一团
                speed = self.rng.uniform(*DEBRIS_POP) * (0.45 + 0.75 * d / far)
                ang = math.atan2(dy, dx) + self.rng.uniform(-DEBRIS_ANGLE, DEBRIS_ANGLE)
                self.debris.append([x, y, math.cos(ang) * speed,
                                    math.sin(ang) * speed - DEBRIS_UP,
                                    1.0, 0.0, self.rng.uniform(*DEBRIS_DEATH)])

    def _collapse_debris(self, dt, k):
        """塌陷每一帧：阻尼 + 向玩家的引力（越到后面吸得越狠）。

        每个碎片有自己的死亡尺寸（`d[6]`），缩到就消失 —— 所以这一批是**渐次**没的，
        不会在 k=1 那一帧整批凭空不见。
        """
        cx, cy = self.burst_center
        pull = DEBRIS_PULL * (k ** DEBRIS_PULL_EASE)
        drag = math.exp(-DEBRIS_DRAG * dt)
        alive = []
        for d in self.debris:
            d[2] *= drag
            d[3] *= drag
            dx, dy = cx - d[0], cy - d[1]
            dist = math.hypot(dx, dy) or 1.0
            if dist > 1.0:
                d[2] += dx / dist * pull * dt
                d[3] += dy / dist * pull * dt
            d[0] += d[2] * dt
            d[1] += d[3] * dt
            d[4] = max(0.0, 1.0 - (k / d[6]) ** DEBRIS_SHRINK)
            d[5] = k
            if dist > 3.0 and d[4] > 0.02:
                alive.append(d)
        self.debris = alive

    def enter_tutorial(self):
        self.state = "TUTORIAL"
        self.prompt_text = story.TUTORIAL_MOVE
        self.say(story.M1)
        # 醒来时只剩脚下这一小片灰：异象真的在，只是他还不知道为什么
        self.board.reveal_around(*self.player.cell)
        self.move_time = 0.0
        self.last_cell = self.player.cell

    # ---------- 教程 ----------
    def update_tutorial(self, dt):
        # 走到老者跟前，就说明该往下走了 —— 教程只是提示，不许把人锁死
        if self.oldman_dist() <= CALL_RANGE_PX:
            self.enter_free_roam()
            return
        # 还没亲手照过：开场那一小片灰**先别褪**。
        # 它会散，但玩家还没学会按 Shift 之前，散掉就等于「邀请消失了」（2026-11-14）。
        # 只续出生点那一片（不跟着人走）：跟着走的话玩家可以一路按住 J 不用学 Shift。
        if not self.reveal_used:
            self.board.reveal_around(*PLAYER_START_CELL)
        # 提示：走满 5 秒，或者原地站够 6 秒都算 —— 站着不动的玩家不能永远收不到提示
        self.tut_t += dt
        if (self.move_time >= TUTORIAL_MOVE_SECONDS or self.tut_t >= 6.0) \
                and self.prompt_text != story.TUTORIAL_SHIFT:
            self.prompt_text = story.TUTORIAL_SHIFT

    def mirage_radius(self):
        """这一幕的异象半径：第四幕给 7×7（扫街要覆盖），前三幕还是 5×5。"""
        return MIRAGE_RADIUS_ACT4 if self.act >= 4 else None

    def update_look_prompt(self):
        """还没照过一次灰域：**在任何位置**都提示 `TRY [SHIFT]`。

        2026-11-14 作者要求：这条提示不该挂在老者身上（之前只在呼喊范围内给，是错的）——
        玩家可以站在任意位置收到它，因为「照地面」这件事和老者没关系。
        TUTORIAL 里不接管：那一阶段有自己的顺序（先教走路，再教 Shift）。
        """
        if self.looked:
            if self.prompt_text == story.TUTORIAL_SHIFT:
                self.prompt_text = ""           # 照到了：这句立刻退场
            return
        self.prompt_text = story.TUTORIAL_SHIFT

    def update_write_prompt(self):
        """第一笔之前：站在亮着的灰域上就提示「按 J」。

        J 是全程唯一一个**没有被任何演出教过**的键（Shift 有 TRY [SHIFT]，T 有 PRESS [T] TO CALL OUT，
        B 有 PRESS [B] TO PICK UP）—— 玩家照出灰域之后，屏幕上只有 HUD 的 `DARK 0/33` 和底部一行小字。
        这条提示不是一次性弹窗：只要还没写下第一笔、脚下又是亮的，它就会一直在（走开就收），
        所以玩家怎么绕都绕不出提示范围，也不会刷屏。
        """
        if self.taught_write:
            return
        r, c = self.player.cell
        lit = self.board.reveal[r][c] > 0 and self.board.state[r][c] == WHITE
        if lit and not self.prompt_text:
            self.prompt_text = story.PROMPT_WRITE
        elif not lit and self.prompt_text == story.PROMPT_WRITE:
            self.prompt_text = ""

    def cast_anomaly(self):
        if self.state not in PAINT_STATES:
            return
        if self.map_open:                                # 手占着（手柄以外的入口也挡一下）
            return
        if self.input.down(SC_J):
            return                                      # 正在涂：按不动异象
        n = self.board.reveal_around(*self.player.cell, radius=self.mirage_radius())
        if n > 0:
            self.looked = True
            self.audio.play("anomaly")
            if not self.reveal_used:
                self.reveal_used = True
                self.say(story.M2)                      # 第一次真的照出灰域 → M2
                if self.state == "TUTORIAL":
                    self.enter_free_roam()
            return
        # 按了却什么都没照出来：坛外是平地（不给提示），坛内是「这一层还轮不到你写」。
        # 2026-11-14 起灰域只说真话，坛内也会有照不出东西的位置 —— 那就得给一句，
        # 否则玩家会以为 Shift 坏了。
        self.anomaly_miss += 1
        if self.state != "TUTORIAL" and self.board.in_altar(*self.player.cell):
            self.mumble(story.MONO_EMPTY)
        if self.state == "TUTORIAL" and self.anomaly_miss >= ANOMALY_MISS_LIMIT:
            self.enter_free_roam()

    def enter_free_roam(self):
        self.state = "FREE_ROAM"
        self.prompt_text = ""
        self.cs_t = 0.0
        self.cs_red_in = self.cs_flee = self.cs_m3 = False
        self.oldman_faced_altar = False

    # ---------- 自由探索 + 开场演出 ----------
    def update_roam(self, dt):
        # 1) 老者离开中：走到世界外就进空档
        if self.oldman.leaving:
            # 往世界外走（他站上方，就往上走出画面）
            self.oldman.move_toward((self.oldman.pos.x, -80), OLDMAN_LEAVE_SPEED, dt)
            if self.oldman.pos.y <= -60:
                self.oldman.gone = True
                self.oldman.leaving = False
                self.start_gap()
            return

        # 2) 驱赶那两只红怪
        self.cs_t += dt
        t = self.cs_t
        ox, oy = self.oldman.pos.x, self.oldman.pos.y
        if not self.cs_red_in and t >= 0.4:
            self.cs_red_in = True
            self.scene_reds = [SceneRed((ox - 44, -50), (0, 150.0)),
                               SceneRed((ox + 44, -50), (0, 132.0))]
        if self.cs_red_in and not self.cs_flee:
            for r in self.scene_reds:
                r.update(dt, stop_y=oy - 52)
        if not self.cs_flee and t >= 1.6:
            self.cs_flee = True
            self.oldman.wave(0.9)
            self.audio.play("staff")                    # 老者挥杖：一下呼啸
            self.threat_t = THREAT_TIME
            for r in self.scene_reds:
                r.vel.update(0, -300.0)
        if self.cs_flee:
            for r in self.scene_reds:
                r.update(dt)
                if r.pos.y < -70:
                    r.gone = True
            self.scene_reds = [r for r in self.scene_reds if not r.gone]
            if not self.oldman_faced_altar:
                self.oldman_faced_altar = True
                self.oldman.facing = 1                   # 之后站在原地，朝向圣坛（往下）
        if not self.cs_m3 and t >= 3.4:
            self.cs_m3 = True
            self.say(story.M3)

        # 3) 可选互动（各只触发一次）
        self.check_prop("dead", PROP_DEAD_CELL, story.M4)
        self.check_prop("tool", PROP_TOOL_CELL, story.M5)

        # 4) 呼喊提示
        self.update_call_prompt()

    def check_prop(self, key, cell, line):
        if self.prop_done[key]:
            return
        if self.dist(self.player.pos, pygame.Vector2(cell_center(*cell))) <= PROP_RANGE_PX:
            self.prop_done[key] = True
            self.say(line)

    def dist(self, a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    def oldman_dist(self):
        return self.dist(self.player.pos, self.oldman.pos)

    def update_call_prompt(self):
        d = self.oldman_dist()
        on_altar = self.board.in_altar(*self.player.cell)
        if d > CALL_RANGE_PX:
            self.prompt_text = ""
        elif not self.looked:
            # 还没照过灰域：T 的提示**不出现**（不是换成别的句子）。
            # 「按 Shift」那句是全局的 —— 站在哪儿都给，见 update_look_prompt()。
            self.prompt_text = ""
        elif self.oldman_turned and not on_altar and d > CLOSE_RANGE_PX:
            self.prompt_text = ""                        # 已经转身了：再走近才喊得动
        else:
            self.prompt_text = story.PROMPT_CALL

    def try_call(self):
        d = self.oldman_dist()
        if d > CALL_RANGE_PX:
            return
        if not self.looked:
            # 提示都没给，就不该能跳过那一步：按了只回一句「TRY [SHIFT]」
            self.show_hint(story.TUTORIAL_SHIFT, 2.0)
            return
        if self.board.in_altar(*self.player.cell):
            # 坛内呼喊：他看到脚下的异象，兴奋地跑过来
            self.oldman.face_to(self.player.pos)
            self.start_dialog(story.branch(True), run_over=True)
        else:
            # 坛外喊：隔着距离喊，他只会转身（带着疑惑），得走近再喊一次；
            # 但已经贴到跟前了，就没必要让他先转个身——直接开口。
            if d > CLOSE_RANGE_PX:
                if not self.oldman_turned:
                    self.oldman_turned = True
                    self.oldman.face_to(self.player.pos)
                return
            self.start_dialog(story.branch(False))

    # ---------- 对话 ----------
    def start_dialog(self, lines, run_over=False, tail=True, after=None):
        """开一段对话。

        `tail=True`  → 末尾自动接第一幕那句 `LEAVE_LINE`（他说完就走）
        `tail=False` → 不接（第三幕他不走）
        `after`      → 说完去哪：None = 第一幕那套（老者离开 + 自由探索）；"BATTLE" = 直接开打
        """
        self.state = "DIALOG"
        self.dlg_lines = list(lines) + ([story.LEAVE_LINE] if tail else [])
        self.dlg_after = after
        self.dlg_i = 0
        self.dlg_phase = "run" if run_over else "talk"
        self.dlg_run_t = 0.0
        self.dlg_hold = 0.0
        self.dlg_t = 0.0
        self.dlg_show_t = 0.0          # 这一句已经显示了多久（dlg_t 会被「补完」改成 99，不能兼用）
        self.prompt_text = ""
        self.reset_mono()                          # 开口说话时，心里那句立刻收掉（连暂停一起解）

    def update_dialog(self, dt):
        if self.dlg_phase == "run":
            self.dlg_run_t += dt
            target = (self.player.pos.x - 34, self.player.pos.y)
            done = self.oldman.move_toward(target, OLDMAN_RUN_SPEED, dt)
            if done or self.dlg_run_t > 1.8:
                self.dlg_phase = "talk"
            return
        self.dlg_t += dt
        self.dlg_show_t += dt
        if self.dlg_hold > 0:
            self.dlg_hold = max(0.0, self.dlg_hold - dt)
            if self.dlg_hold <= 0:
                self.end_dialog()

    def dlg_typing(self):
        """这一句还没打完？"""
        from src.ui import dialog_char_total
        return self.dlg_t * DLG_CPS < dialog_char_total(self)

    def advance_dialog(self):
        if self.dlg_phase != "talk" or self.dlg_lines is None:
            return
        self.hint_t = 0.0
        if self.dlg_typing():
            self.dlg_t = 99.0                            # 先补完这一句，视觉小说的手感
            return
        # 最后一句：**等玩家再按一次回车**才让老者离开。
        # （原来是 `dlg_hold = 1.0` 自动走 —— 玩家还没看完 `If I can.` 人就没了）
        #
        # 必须在重置 dlg_t 之前判断：否则计时又被清零，条件永远成立，就再也走不了了。
        # 这一句刚显示出来的瞬间也不认按键 —— 玩家从上一句连按两下时，第二下会把
        # 最后一句一帧跳过去，看起来就像「最后一句被删掉了」。
        if self.dlg_i >= len(self.dlg_lines) - 1:
            if self.dlg_show_t >= DLG_LAST_MIN_SHOW:
                self.end_dialog()
            return

        self.dlg_t = 0.0
        self.dlg_show_t = 0.0
        self.dlg_i += 1
        self.audio.play("ui")                            # 翻页：极轻一声

    def end_dialog(self):
        self.dlg_lines = None
        self.prompt_text = ""
        after, self.dlg_after = self.dlg_after, None
        if after == "BATTLE":                        # 第三幕：话说完了，它们也到了
            self.start_battle()
            return
        self.state = "FREE_ROAM"
        self.oldman.leaving = True

    def close_dialog(self):
        """Esc：收起对话框，回到自由探索（老者还在原地，可以再喊）。"""
        self.dlg_lines = None
        self.state = "FREE_ROAM"
        self.dlg_hold = 0.0
        self.prompt_text = ""

    # ---------- 空档 ----------
    def start_battle(self):
        self.state = "BATTLE"
        self.elapsed = 0.0
        self.spawn_acc = 0.0
        self.purple_t = 0.0
        self.purple_spawned = 0
        # 第一幕「它们要来了」/ 第二幕紫怪那句。第三幕不喊 —— 情绪已经由开场对话给足了。
        if self.act < 2:
            self.mumble(story.MONO_INCOMING)
        elif self.act < 3:
            self.mumble(story.MONO_PURPLE_IN)

    def update_gap(self, dt):
        self.gap_t += dt
        if self.gap_t >= GAP_SECONDS:
            self.start_battle()

    # ---------- 战斗 ----------
    def update_battle(self, dt):
        if self.act == 3:
            self.update_scribe(dt)                   # 他一直在写（写完这一格就清屏了）
            if self.state != "BATTLE":               # 刚写完最后一格 → 已经进 CLEAR
                return
        elif self.act >= 4:
            self.update_repair(dt)                   # 第四、五幕：他只补骨架，不碰数据区
        for m in self.monsters[:]:
            res = m.update(dt, self.board, self.claims, self.player)
            if res != "alive":
                if res == "hit":
                    self.health = max(0, self.health - HIT_DAMAGE)
                    self.break_pen()                    # 被咬 → 手里的这一笔断了
                    self.audio.play("hurt")             # 被咬：下坠的一声
                    self.mumble(story.MONO_HIT)        # 掉血用飘字：不冻世界，血条 HUD 已经反映
                elif res == "eat":
                    self.audio.play("red_die")          # 吃掉了黑域，然后自毁
                self.monsters.remove(m)

        # ---- 第二幕：紫怪（the purple one）----
        if self.act >= 2:
            self.purple_t += dt
            # 首只按 PURPLE_FIRST_DELAY（作者定 8 秒），之后按 PURPLE_SPAWN_PER_MIN
            # 第三幕慢下来（作者 2026-11-12）：格式信息躺在第 10 行/列上，一次清行能抹掉 16 格
            # 第四幕回潮（4 只/分）：那一幕玩家一趟能写几十格，没有清行就没压力
            if self.act >= 5:
                rate = PURPLE_SPAWN_PER_MIN_ACT5
            elif self.act >= 4:
                rate = PURPLE_SPAWN_PER_MIN_ACT4
            elif self.act >= 3:
                rate = PURPLE_SPAWN_PER_MIN_ACT3
            else:
                rate = PURPLE_SPAWN_PER_MIN
            due = PURPLE_FIRST_DELAY if self.purple_spawned == 0 else 60.0 / max(rate, 1e-6)
            if self.purple_t >= due:
                self.purple_t = 0.0
                self.purple_spawned += 1
                self.spawn_purple()
            for pu in self.purples[:]:
                res2 = pu.update(dt, self.board, self.player)
                if res2 != "alive":
                    if isinstance(res2, tuple):
                        if res2[0] == "wipe":
                            self.on_line_wiped(res2[1], res2[2], res2[3])
                        elif res2[0] == "hit":          # 坛内没黑域 → 它扑人（P10）
                            self.health = max(0, self.health - PURPLE_HIT_DAMAGE)
                            self.break_pen()            # 被撞 → 这一笔也断
                            self.audio.play("hurt")
                            self.mumble(story.MONO_PURPLE_HIT)
                    self.purples.remove(pu)
                    self.claims.clear()          # 紫怪不占 claims，但清一下更稳

        # ---- 第三幕：黄怪（它们冲着老者来）+ 救他 ----
        if self.act >= 3:
            self.sword_cd = max(0.0, self.sword_cd - dt)
            self.swing_t = max(0.0, self.swing_t - dt)
            self.update_yellows(dt)
            self.update_revive(dt)

        self.elapsed += dt
        step = int(self.elapsed // RED_SPAWN_ACCEL_PERIOD)
        if step > self.accel_step:
            self.accel_step = step
            self.spawn_rate *= RED_SPAWN_ACCEL
        self.spawn_acc += dt
        interval = 60.0 / max(self.spawn_rate, 1e-6)
        while self.spawn_acc >= interval:
            self.spawn_acc -= interval
            self.spawn_monster()

        if self.health <= 0:
            self.state = "DEAD"
            self.menu_t = 0.0
            return
        # 第五幕：骨架完好 + 错误压进容错容量 → 码能读了。**先于「涂满了」判定** ——
        # 这一幕的胜利条件不是「补完」，是「够用」。
        if self.act >= 5:
            self.tick_erode(dt)
            if not self.frame_said and self.frame_broken() > 0:
                self.frame_said = True                   # 只一次：把「他管骨架」这件事说清
                self.mumble(story.A5_FRAME)
            if self.frame_broken() == 0 and self.act5_errors() <= ERROR_TOLERANCE:
                self.enter_scan()
                return
        # 第四幕：快写完了 —— 说一句，只一次（不然整幕静悄悄的，收尾没有情绪）
        if self.act == 4 and not self.almost_said:
            owe = len(self.must) - self.board.progress()
            if 0 < owe <= ALMOST_OWE:
                self.almost_said = True
                self.mumble(story.A4_M3)
        if self.board.is_complete():
            self.enter_clear()

    def needs_hold(self, r, c):
        """这一格要不要「按住」才写得动？—— 只有第三幕的**格式信息格**要。

        作者 2026-11-13：格式信息是这张码的读法本身，写起来比普通格慢得多；
        所以玩家补它也得压住 J 满 `FORMAT_HOLD_TIME`，不能像普通格那样一点就成。
        """
        return (self.act >= 3 and (r, c) in self.format_cells
                and self.board.state[r][c] == WHITE)

    def break_pen(self):
        """被怪咬一口 → 这一笔断了：正在**制造黑域**的那格进度作废，得重新按住 J。

        和老者被咬停笔（`OLDMAN_STAGGER`）是同一个道理 —— 挨打不该只掉血，
        否则「守」这件事就只对老头成立，对玩家自己没成本。
        """
        self.fill_t = 0.0
        self.fill_cell = None

    def hold_paint(self, dt):
        """按住 J 写字：普通格立即落笔，格式格要压满 `FORMAT_HOLD_TIME` 秒。

        **第四幕换成「扫」**（作者 2026-11-14）：按住 J 走过照出来的灰域就自动制造黑域，
        没照过的格**直接跳过** —— 不写、也不算脏格。于是盲涂在第四幕不是「罚」，是「白走」；
        压力从手速变成「照哪儿、怎么走」。

        进度**绑在这一格上**（`fill_cell`）：松手 / 走开 / 换格都从 0 重数。
        不绑的话会串味 —— 在 A 上按半秒、挪到 B 再按 0.3 秒就能把 B 写掉（实测踩过）。
        """
        r, c = self.player.cell
        if self.act >= 4:                               # 扫：只写灰域，灰域褪了就停手
            self.fill_t = 0.0
            self.fill_cell = None
            if self.board.reveal[r][c] > 0:
                self.paint_here()
            return
        if not self.needs_hold(r, c):
            self.fill_t = 0.0
            self.fill_cell = None
            self.paint_here()                           # 普通格：和以前一样，一按就成
            return
        if self.fill_cell != (r, c):                    # 换了一格：这一笔从头数
            self.fill_cell = (r, c)
            self.fill_t = 0.0
        if not self.hold_said:                          # 第一次碰到格式格：教一下「按住」
            self.hold_said = True
            self.show_hint(story.HINT_FORMAT_HOLD, 3.0)
        self.fill_t = min(FORMAT_HOLD_TIME, self.fill_t + dt)
        if self.fill_t >= FORMAT_HOLD_TIME:
            self.fill_t = 0.0
            self.fill_cell = None
            self.paint_here()

    def paint_here(self):
        r, c = self.player.cell
        res = self.board.paint(r, c)
        if res == "valid":
            self.audio.play("paint")                    # 落子：写对了
            if not self.taught_write:                   # 第一笔：给一句确认，然后不再教了
                self.taught_write = True
                self.prompt_text = ""
                self.mumble(story.MONO_FIRST)
            return
        if res == "dirty":
            self.audio.play("stain")                    # 落错：失谐的一声
            # 两种脏格，提示要分开：「看都没看清」和「涂错地方」不是一回事
            blind = (r, c) in self.board.must and self.board.reveal[r][c] <= 0
            if not self.stain_warned:                  # 第一次：教一下 K（按键教学，保留系统提示）
                self.stain_warned = True
                self.show_hint(story.HINT_CLEAR, 3.0)
            if blind:
                self.mumble(story.MONO_BLIND)          # 「还没看」→ 嘀咕（不冻世界）
            else:
                self.mumble(story.MONO_STAIN)          # 涂错成脏格 → 嘀咕「好像失败了」
            if self.board.stains > STAIN_LIMIT:
                # 额度用完之后的每一格脏格：一次外伤，不是判负
                self.health = max(0, self.health - STAIN_DAMAGE)
                self.audio.play("hurt")
                self.mumble(story.MONO_STAIN_HURT)     # 超标扣血 → 嘀咕
        elif res == "plain":
            self.audio.play("paint")                    # 平地诱饵也算「写下一格」

    def map_busy(self):
        """地图摊开时想干活：先卷起来。给一行提示 + 一声闷响，别让玩家以为按键坏了。"""
        self.show_hint(story.MAP_IN_HANDS, 1.6)
        self.audio.play("dull")

    # ---------- 第三幕：黄怪 / 倒下 / 救援 / 挥剑 ----------
    def update_yellows(self, dt):
        """黄怪从生成环进场，一路冲老者；被打一次就转火玩家（`YellowOne.update` 里判）。"""
        self.yellow_t += dt
        due = YELLOW_FIRST_DELAY if self.yellow_spawned == 0 else 60.0 / max(YELLOW_SPAWN_PER_MIN, 1e-6)
        # 只有第三幕会刷黄怪（2026-11-14 明确定死）：第四幕的追兵是紫怪 + 红怪，
        # 不然再加上「谁近咬谁」的黄怪，那一幕会同时有扫街、清行、咬人三件事，节奏就散了。
        if self.act == 3 and self.yellow_t >= due and len(self.yellows) < YELLOW_MAX:
            self.yellow_t = 0.0
            self.yellow_spawned += 1
            self.yellows.append(YellowOne(self.ring_spawn_pos()))
            self.audio.play("purple")                # 低音：和紫怪同一种「东西进场了」
            if self.yellow_spawned == 1:
                self.mumble(story.A3_Y1)

        for y in self.yellows[:]:
            res = y.update(dt, self.oldman, self.player)
            if res == "bite_oldman":
                self.audio.play("hurt")
                if self.oldman is not None and self.oldman.bitten(YELLOW_BITE_DAMAGE):
                    self.on_oldman_down()
                elif not self.stagger_said:          # 第一次被咬断：他自己嘟囔一句（只一次，不然太吵）
                    self.stagger_said = True
                    self.mumble(story.A3_STAGGER, who=story.OLD_MAN)
            elif res == "bite_player":
                self.health = max(0, self.health - YELLOW_PLAYER_DAMAGE)
                self.break_pen()                     # 被黄怪咬：正在制造的黑域作废（作者 2026-11-13）
                self.audio.play("hurt")
                self.mumble(story.MONO_HIT)

    def on_oldman_down(self):
        """老者倒下：停笔、呼救、等玩家来救（作者定：站到他旁边按住 H 四秒）。"""
        self.revive_t = 0.0
        self.scribe_writing = False                  # 笔停在半空
        self.audio.play("wipe")
        self.show_hint(story.HINT_HELP_OLDMAN, 999.0)
        if not self.down_said:
            self.down_said = True
            self.say(story.A3_DOWN, 3.0)

    def update_revive(self, dt):
        """按住 H 救人。松手会退一点（不是一键归零），但要满 4 秒他才起得来。"""
        om = self.oldman
        if om is None or not om.down:
            self.revive_t = 0.0
            return
        near = math.hypot(self.player.pos.x - om.pos.x, self.player.pos.y - om.pos.y) <= OLDMAN_REVIVE_RANGE
        if not (near and self.input.down(SC_H)):
            self.revive_t = max(0.0, self.revive_t - dt * 2.0)
            return
        # ⚠️ 这里**不能说台词**：心声会冻住世界，一说话 `revive_t` 就不涨了，
        # 玩家按着 H 反而救不起来（2026-11-12 踩过）。救起来之后老者的回应在下面。
        self.revive_t += dt
        if self.revive_t >= OLDMAN_REVIVE_TIME:
            self.revive_t = 0.0
            om.revive(OLDMAN_REVIVE_HP)
            self.audio.play("clear")
            self.hint_text, self.hint_t = "", 0.0
            self.mumble(story.A3_UP_MAN, who=story.OLD_MAN)     # 他自己回一句
            self.blast_yellows(om)

    def blast_yellows(self, om, radius=OLDMAN_BLAST_RADIUS):
        """他站起来的那一刻，把身边的黄怪震开。

        为什么要这一下（2026-11-12 实测）：没有它就是个死循环 ——
        他倒 → 玩家救起（50 血）→ 贴着他的黄怪立刻又咬 → 5 口又倒。2 分钟里倒下 40 次，
        格式信息一个字都写不出来。这一下把「救他」变成「换来一段清净」，
        而不是「白救」。也接得上第一幕：他当年是用光把红怪赶走的。
        """
        if om is None:
            return
        gone = 0
        keep = []
        for y in self.yellows:
            if math.hypot(y.pos.x - om.pos.x, y.pos.y - om.pos.y) <= radius:
                gone += 1
            else:
                keep.append(y)
        if gone:
            self.yellows = keep
            self.audio.play("red_die")

    def swing_sword(self):
        """挥剑：砍最近的**一只怪**（黄怪 / 红怪 / 紫怪都算）。

        伤害（作者 2026-11-12 定）：
          · **黄怪要两剑**（`YELLOW_HP=2`），挨了剑必然转火玩家
          · **红怪 / 紫怪一剑就死** —— 它们没有 hp，是「抢格子」的单位，不是「打人」的单位
        挥空也有动作 + 声音，CD 照旧。
        """
        if self.sword_cd > 0:
            return
        self.sword_cd = SWORD_CD
        self.swing_t = SWORD_SWING_TIME
        self.audio.play("sword")

        px, py = self.player.pos.x, self.player.pos.y

        def near(pos, cur):
            d = math.hypot(pos.x - px, pos.y - py)
            return d if d <= SWORD_RANGE and (cur is None or d < cur) else None

        best_kind, best_obj, best_d = None, None, None
        for y in self.yellows:
            d = near(y.pos, best_d)
            if d is not None:
                best_kind, best_obj, best_d = "yellow", y, d
        for m in self.monsters:
            d = near(m.pos, best_d)
            if d is not None:
                best_kind, best_obj, best_d = "red", m, d
        for pu in self.purples:
            d = near(pu.pos, best_d)
            if d is not None:
                best_kind, best_obj, best_d = "purple", pu, d

        if best_obj is None:
            return                                       # 挥空

        if best_kind == "yellow":
            if best_obj.hurt(1):
                self.yellows.remove(best_obj)
                self.audio.play("red_die")
            return
        # 红怪 / 紫怪：一剑一个
        if best_kind == "red":
            self.monsters.remove(best_obj)
        else:
            self.purples.remove(best_obj)
        self.audio.play("red_die")

    def spawn_purple(self):
        """紫怪从生成环上进场。"""
        self.purples.append(PurpleOne(self.ring_spawn_pos()))
        if self.purple_spawned == 1:                 # 第一次来：给一句独白 + 一记低音
            self.say(story.A2_M3)
            self.audio.play("purple")
        else:
            self.audio.play("purple")

    def on_line_wiped(self, axis, idx, cleared):
        """紫怪清掉一整条：只出声，不再弹提示。

        心声**只在第一次**被清时说（`A2_M4`，作者 2026-11-12：每次都说会影响体验）。
        之后靠画面（整条变白）+ "wipe" 音效就够了，玩家自己看得见。
        第四幕换一句 `A4_M2` —— 那一幕你一眨眼就写了十几格，被清一行是另一种痛。
        """
        self.audio.play("wipe")
        if not self.wipe_warned:                     # 一生只一次：正式独白
            self.wipe_warned = True
            self.mumble(story.A4_M2 if self.act >= 4 else story.A2_M4)

    def ring_spawn_pos(self):
        """在 30×30 生成环上随机取一点（红怪和紫怪共用）。"""
        side = self.rng.randrange(4)
        t = self.rng.random() * SPAWN_PX
        x0, y0 = SPAWN_ORIGIN
        if side == 0:
            return (x0 + t, y0)
        if side == 1:
            return (x0 + SPAWN_PX, y0 + t)
        if side == 2:
            return (x0 + t, y0 + SPAWN_PX)
        return (x0, y0 + t)

    def spawn_monster(self):
        speed = RED_SPEED * self.rng.uniform(*RED_SPD_JITTER)
        self.monsters.append(Monster(self.ring_spawn_pos(), speed))

    # ---------- 清屏 ----------
    def enter_clear(self):
        self.scribe_cells = []                       # 写完了，他停手（剩下的交给清屏波）
        self.scribe_target = None
        self.mini_wave = (self.act == 1 and self.act1_wave == 1)
        self.state = "CLEAR"
        self.clear_phase = "glow"
        self.clear_t = 0.0
        self.wave_r = 0.0
        self.glow_t = 0.0
        self.prompt_text = ""
        # 第一波时玩家本来就站在坛里，不用再叫他进去；
        # 整幕收尾时他多半也站在坛里（刚涂完最后一格）—— 那就别喊了，否则这句会一直挂到波扫完。
        if not self.mini_wave and not self.board.in_altar(*self.player.cell):
            self.show_hint(story.STEP_INTO_ALTAR, 999.0)
        for m in self.monsters:
            m.claim(self.claims)
            m.mode = "hunt"
            m.target = None
        self.purples.clear()                        # 仪式的光把它们一起收掉
        self.yellows.clear()
        self.claims.clear()

    def update_clear(self, dt):
        self.glow_t += dt
        # 「走进圣坛」只说给还没进来的人听：他一进来就把这句收掉（2026-11-14）
        if self.hint_text == story.STEP_INTO_ALTAR and self.board.in_altar(*self.player.cell):
            self.hint_text, self.hint_t = "", 0.0
        cx, cy = altar_center()
        for m in self.monsters:                          # 被光牵着往中心漂，不再伤人
            d = pygame.Vector2(cx - m.pos.x, cy - m.pos.y)
            if d.length_squared() > 1.0:
                m.pos += d.normalize() * m.speed * 0.5 * dt

        if self.clear_phase == "glow":
            self.clear_t += dt
            # 圣坛先亮够 CLEAR_GLOW_TIME，再认玩家「站进来了」。
            # （玩家涂完最后一格时通常本来就站在坛内，不设这个下限的话发光一帧都不会出现）
            if self.clear_t >= CLEAR_GLOW_TIME and self.board.in_altar(*self.player.cell):
                self.clear_phase = "wave"
                self.clear_t = 0.0
                self.wave_r = 0.0
                self.audio.play("clear")                # 圣坛发动：渐强的咻 + 一记低鸣
        elif self.clear_phase == "wave":
            self.wave_r += CLEAR_WAVE_SPEED * dt
            self.clear_monsters_in_wave()
            if self.mini_wave:                       # 半场：扫到圣坛外沿就停（整屏要 3.7 秒，太干）
                far = MINI_WAVE_REACH
            else:
                far = max(math.hypot(x - cx, y - cy) for x in (0, WINDOW_W) for y in (0, WINDOW_H))
            if self.wave_r >= far:
                self.board.wipe_stains()                 # 顺手把全部脏格抹掉
                if not self.mini_wave:
                    self.capture_map()                   # 这一幕的圣坛定妆了 → 记进地图
                self.clear_phase = "hold"
                self.clear_t = 0.0
        elif self.clear_phase == "hold":
            self.clear_t += dt
            if self.clear_t >= CLEAR_WAVE_HOLD:          # 光散完停一下，再让道具浮出来
                if self.mini_wave:
                    self.start_wave2()                   # 第一幕第一波 → 接着写第二波
                else:
                    self.enter_reward()

    def clear_monsters_in_wave(self):
        cx, cy = altar_center()
        keep = []
        for m in self.monsters:
            if math.hypot(m.pos.x - cx, m.pos.y - cy) <= self.wave_r:
                m.claim(self.claims)
            else:
                keep.append(m)
        self.monsters = keep

    def capture_map(self):
        """把此刻圣坛的样子拍进地图 —— 地图**只记每一幕收尾那一瞬**（作者定的规则）。

        所以它是一本「幕账」：进下一幕时打开地图，看到的是上一幕结束时圣坛的样子，
        这一幕的涂改、被紫怪清掉的整行，都不会实时改地图上的墨。
        唯一的调用点是 `update_clear()` 里清屏波扫完、脏格抹掉之后 ——
        那一刻本幕的圣坛才真正定妆（必涂格全黑、脏格全无）。
        """
        orr, occ = TARGET_OFFSET
        cells = set()
        for tr in range(TARGET_N):
            for tc in range(TARGET_N):
                if self.board.state[orr + tr][occ + tc] == VALID:
                    cells.add((tr, tc))
        self.map_cells = cells
        self.map_act = self.act

    # ---------- 奖励 ----------
    def enter_reward(self):
        self.state = "REWARD"
        self.reward_phase = "wait"
        self.reward_t = 0.0
        self.spread_r = 0.0
        self.hint_t = 0.0
        self.items = []
        self.prompt_text = ""

    def spawn_items(self):
        """道具浮出来：第一幕 BAG + MAP，第二幕 SWORD（第三幕之后还没定）。"""
        kinds = {1: ("bag", "map"), 2: ("sword",)}.get(self.act, ())
        cells = sorted(c for c in self.must if self.board.state[c[0]][c[1]] == 1)
        self.rng.shuffle(cells)
        self.items = [Item(kind, cell) for kind, cell in zip(kinds, cells[:len(kinds)])]

    def update_reward(self, dt):
        for it in self.items:
            it.t = min(1.0, it.t + dt / ITEM_RISE_TIME)

        if self.reward_phase == "wait":
            self.reward_t += dt
            if self.reward_t >= REWARD_DELAY:
                if self.act >= 3:
                    # 第三幕之后暂时不发道具：直接收尾
                    self.reward_phase = "spread"
                    self.reward_t = 0.0
                    self.spread_r = 0.0
                else:
                    self.spawn_items()
                    self.reward_phase = "items"
                    self.reward_t = 0.0
        elif self.reward_phase == "items":
            near = self.nearest_item()
            self.prompt_text = story.PROMPT_PICK if near is not None else ""
            if not self.items:
                self.reward_phase = "wait2"
                self.reward_t = 0.0
                self.prompt_text = ""
        elif self.reward_phase == "wait2":
            self.reward_t += dt
            if self.reward_t >= REWARD_WAIT:
                self.reward_phase = "spread"
                self.reward_t = 0.0
                self.spread_r = 0.0
        elif self.reward_phase == "spread":
            self.spread_r += (max(WINDOW_W, WINDOW_H) / SPREAD_TIME) * dt
            if self.spread_r >= math.hypot(WINDOW_W, WINDOW_H):
                self.state = "END"
                self.menu_t = 0.0
                self.show_banner(story.act_title(self.act), 999.0)

    def nearest_item(self):
        best, best_d = None, None
        for it in self.items:
            d = self.dist(self.player.pos, it.pos)
            if d <= ITEM_PICK_RANGE and (best_d is None or d < best_d):
                best, best_d = it, d
        return best

    def try_pick(self):
        it = self.nearest_item()
        if it is None:
            return
        it.picked = True
        self.items.remove(it)
        self.audio.play("pickup")
        if it.kind == "bag":
            self.has_bag = True
            self.show_hint(story.ITEM_BAG, 5.0)
        elif it.kind == "sword":
            self.has_sword = True
            self.show_hint(story.ITEM_SWORD, 5.0)
        else:
            self.has_map = True
            self.show_hint(story.ITEM_MAP, 5.0)

    # ---------- 绘制 ----------
    def present(self):
        if self.needs_scale:
            pygame.transform.smoothscale(self.canvas, self.window.get_size(), self.window)
        else:
            self.window.blit(self.canvas, (0, 0))

    def draw(self):
        if self.state == "TITLE":
            draw_title(self)
            self.present()
            return

        draw_world(self)
        draw_hud(self)
        if self.state == "DIALOG":
            draw_dialog(self)
        if self.state == "DEAD":
            draw_dead(self)
        elif self.state == "END":
            draw_end(self)
        self.apply_shake()                 # 开场碎码那一下的屏幕抖动（0,0 时是空操作）
        self.present()

    def apply_shake(self):
        dx, dy = self.shake_off
        if dx == 0 and dy == 0:
            return
        self.shake_buf.blit(self.canvas, (0, 0))
        self.canvas.fill(C_BG)                 # 补边用世界底色（旧版是冷蓝，早就不对了）
        self.canvas.blit(self.shake_buf, (dx, dy))

