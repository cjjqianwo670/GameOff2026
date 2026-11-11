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
    BANNER_TIME, CALL_RANGE_PX, CELL, CLEAR_WAVE_HOLD, CLEAR_WAVE_SPEED, C_BG, C_MIRAGE, C_MONSTER,
    C_PLAYER, C_PURPLE, CLOSE_RANGE_PX, DEBRIS_GRAVITY, DEBRIS_JITTER, DEBRIS_SPEED, DEBRIS_UP, FPS,
    GAP_SECONDS, HEALTH_MAX, HINT_TIME, HIT_DAMAGE, INTRO_FADE, INTRO_FALL, INTRO_SHOW, MIRAGE_ALPHA_MAX,
    CLEAR_GLOW_TIME, DLG_CPS, DLG_FONT, DLG_LAST_MIN_SHOW, DLG_NAME_FONT, INTRO_TOTAL, MAP_OPEN_TIME,
    ITEM_PICK_RANGE,
    ITEM_RISE_TIME, MONO_CPS, MONO_FONT, MONOLOGUE_TIME, OLDMAN_CELL, PROMPT_FONT,
    OLDMAN_LEAVE_SPEED, OLDMAN_RUN_SPEED, PLAYER_GLOW_R, PROP_DEAD_CELL, PROP_RANGE_PX,
    PROP_TOOL_CELL, RED_RADIUS, RED_SPAWN_ACCEL, RED_SPAWN_ACCEL_PERIOD, RED_SPAWN_PER_MIN,
    RED_SPD_JITTER,
    RED_SPEED, REWARD_DELAY, REWARD_WAIT, SC_B, SC_ENTER, SC_ESC, SC_F1, SC_J, SC_K, SC_KP_ENTER,
    SC_M, SC_R, SC_SHIFT, SC_SPACE, SC_T, SHAKE_LEAD, SHAKE_SEQ, SHAKE_STEP, SPAWN_ORIGIN,
    SPAWN_PX,
    SPREAD_TIME, STAIN_DAMAGE, STAIN_LIMIT, TARGET_N, TARGET_OFFSET, THREAT_TIME, VALID,
    ANOMALY_MISS_LIMIT, TUTORIAL_MOVE_SECONDS, WINDOW_H, WINDOW_W,
    A2_OPEN_SECONDS, PURPLE_EAT_DIST, PURPLE_FIRST_DELAY, PURPLE_SPAWN_PER_MIN
)
from src.entities import Item, Monster, OldMan, Player, PurpleOne, SceneRed
from src.grid import altar_center, cell_center
from src.input_state import InputState
from src.qr import generate_target, required_cells
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
        self.board = None
        self.player = None
        self.oldman = None
        self.oldman_turned = False
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
        self.must = required_cells(self.target, act=self.act)
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

        self.mono_text, self.mono_t = "", 0.0
        self.hint_text, self.hint_t = "", 0.0
        self.prompt_text = ""
        self.threat_t = 0.0
        self.banner_text, self.banner_t = "", 0.0

        self.move_time = 0.0
        self.last_cell = self.player.cell
        self.reveal_used = False
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
        self.items = []
        self.has_bag = self.has_map = False
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
        self.shake_t = 0.0
        self.shake_started = False
        self.shake_off = (0, 0)
        self.burst_done = False
        self.hint_alpha = 0

        self.state = "INTRO"
        self.input.held.clear()

    def next_act(self):
        """幕结束画面按下回车：第一幕 → 第二幕；第二幕 → 回标题（后面几幕还没做）。"""
        if self.act < 2:
            self.start_act2()
        else:
            self.state = "TITLE"
            self.menu_t = 0.0
            self.input.held.clear()

    def start_act2(self):
        """第一幕结束 → 第二幕。

        **不清空棋盘**（作者定）：第一幕涂好的 100 格原地保留，本幕只多 6 格定时图案。
        所以这里不能重播碎码动画，只换必涂格集合 + 复位血量/怪物/计时。
        """
        self.act = 2
        # 同一个 target、同一个 board：只把必涂格从 100 扩到 106
        self.must = required_cells(self.target, act=self.act)
        self.board.set_must(self.must)

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
        # ⚠️ 不要重置 has_bag / has_map：这两个是第一幕拿到的，之后一直带着
        self.clear_phase, self.clear_t, self.wave_r, self.glow_t = None, 0.0, 0.0, 0.0
        self.reward_phase, self.reward_t, self.spread_r = None, 0.0, 0.0
        self.dlg_lines = None
        if self.oldman is not None:
            self.oldman.gone = True

        # 开场：一行独白，不打断操作；读完自动进战斗
        self.state = "A2_OPEN"
        self.open_t = 0.0
        self.say(story.A2_M1)
        self.audio.play("clear")                     # 复用圣坛低鸣：仪式又开始了
        self.checkpoint = self.make_checkpoint()

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
            "bag": self.has_bag,          # 第一幕之后一直带着，回检查点不能丢
            "map": self.has_map,
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
        self.spawn_acc = 0.0
        self.player.reset()
        self.hint_text, self.hint_t = "", 0.0
        self.mono_text, self.mono_t = "", 0.0
        self.threat_t = 0.0
        self.clear_phase, self.clear_t, self.wave_r = None, 0.0, 0.0
        self.reward_phase, self.reward_t, self.spread_r = None, 0.0, 0.0
        self.dlg_lines = None
        if self.oldman is not None:
            self.oldman.gone = True                      # 他早就走了
            self.oldman.leaving = False
        self.state = cp.get("state", "GAP")
        self.gap_t = 0.0
        self.open_t = 0.0
        self.input.held.clear()

    # ---------- 文本通道 ----------
    def say(self, text, secs=MONOLOGUE_TIME):
        """内心独白：屏幕下方，不打断操作。"""
        self.mono_text = text
        self.mono_t = secs
        self.mono_total = secs

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
        if st == "INTRO":
            return

        # ---- 以下都是可动相位 ----
        if sc == SC_R:
            self.start_act()
        # 地图摊开 = 双手捧着纸，涂改 / 擦除 / 照异象全都做不了（作者 2026-11-12 定的代价）。
        # 挡在这里是为了给一句话的反馈；真正拦住动作的是 update() 里那个 `not self.map_open`。
        elif self.map_open and st in PAINT_STATES and (sc in (SC_J, SC_K) or sc in SC_SHIFT):
            self.map_busy()
        elif sc in SC_SHIFT:
            self.cast_anomaly()
        elif sc == SC_M and self.has_map and st in MOVE_STATES:
            self.map_open = not self.map_open
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
                self.paint_here()
            elif self.input.down(SC_K):
                if self.board.start_erase(*self.player.cell):
                    self.audio.play("erase")            # 抹除：收回的一声上滑

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

    def tick_timers(self, dt):
        if self.hint_t > 0:
            self.hint_t = max(0.0, self.hint_t - dt)
        if self.mono_t > 0:
            self.mono_t = max(0.0, self.mono_t - dt)
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

        alive = []
        for d in self.debris:
            d[3] += DEBRIS_GRAVITY * dt
            d[0] += d[2] * dt
            d[1] += d[3] * dt
            if d[1] < WINDOW_H + CELL:
                alive.append(d)
        self.debris = alive

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
        orr, occ = TARGET_OFFSET
        cx, cy = WINDOW_W / 2.0, WINDOW_H / 2.0
        self.debris = []
        for tr in range(TARGET_N):
            row = self.target[tr]
            for tc in range(TARGET_N):
                if not row[tc]:
                    continue
                x, y = cell_center(orr + tr, occ + tc)
                dx, dy = x - cx, y - cy
                dist = (dx * dx + dy * dy) ** 0.5 or 1.0
                speed = random.uniform(*DEBRIS_SPEED)
                vx = dx / dist * speed + random.uniform(-DEBRIS_JITTER, DEBRIS_JITTER)
                vy = dy / dist * speed - random.uniform(0, DEBRIS_UP)
                self.debris.append([x - CELL / 2.0, y - CELL / 2.0, vx, vy])

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
        if self.move_time >= TUTORIAL_MOVE_SECONDS and self.prompt_text != story.TUTORIAL_SHIFT:
            self.prompt_text = story.TUTORIAL_SHIFT

    def cast_anomaly(self):
        if self.state not in PAINT_STATES:
            return
        if self.map_open:                                # 手占着（手柄以外的入口也挡一下）
            return
        if self.input.down(SC_J):
            return                                      # 正在涂：按不动异象
        n = self.board.reveal_around(*self.player.cell)
        if n > 0:
            self.audio.play("anomaly")
            if not self.reveal_used:
                self.reveal_used = True
                self.say(story.M2)                      # 第一次真的照出灰域 → M2
                if self.state == "TUTORIAL":
                    self.enter_free_roam()
            return
        # 按了却什么都没照出来（多半是站在平地上）：不给提示，但要防止永远卡住
        self.anomaly_miss += 1
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
        elif self.oldman_turned and not on_altar and d > CLOSE_RANGE_PX:
            self.prompt_text = ""                        # 已经转身了：再走近才喊得动
        else:
            self.prompt_text = story.PROMPT_CALL

    def try_call(self):
        d = self.oldman_dist()
        if d > CALL_RANGE_PX:
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
    def start_dialog(self, lines, run_over=False):
        self.state = "DIALOG"
        self.dlg_lines = list(lines) + [story.LEAVE_LINE]
        self.dlg_i = 0
        self.dlg_phase = "run" if run_over else "talk"
        self.dlg_run_t = 0.0
        self.dlg_hold = 0.0
        self.dlg_t = 0.0
        self.dlg_show_t = 0.0          # 这一句已经显示了多久（dlg_t 会被「补完」改成 99，不能兼用）
        self.prompt_text = ""
        self.mono_text, self.mono_t = "", 0.0      # 开口说话时，心里那句立刻收掉

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
        self.state = "FREE_ROAM"
        self.oldman.leaving = True
        self.prompt_text = ""

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
        # 第一幕的「它们要来了」，第二幕换成紫怪那句（它才是这一幕的新东西）
        self.show_hint(story.INCOMING if self.act < 2 else story.A2_PURPLE_IN, 2.8)

    def update_gap(self, dt):
        self.gap_t += dt
        if self.gap_t >= GAP_SECONDS:
            self.start_battle()

    # ---------- 战斗 ----------
    def update_battle(self, dt):
        for m in self.monsters[:]:
            res = m.update(dt, self.board, self.claims, self.player)
            if res != "alive":
                if res == "hit":
                    self.health = max(0, self.health - HIT_DAMAGE)
                    self.audio.play("hurt")             # 被咬：下坠的一声
                    self.show_hint("HIT  -%d%%" % HIT_DAMAGE, 1.4)
                elif res == "eat":
                    self.audio.play("red_die")          # 吃掉了黑域，然后自毁
                self.monsters.remove(m)

        # ---- 第二幕：紫怪（the purple one）----
        if self.act >= 2:
            self.purple_t += dt
            # 首只按 PURPLE_FIRST_DELAY（作者定 8 秒），之后按 PURPLE_SPAWN_PER_MIN
            due = PURPLE_FIRST_DELAY if self.purple_spawned == 0 else 60.0 / max(PURPLE_SPAWN_PER_MIN, 1e-6)
            if self.purple_t >= due:
                self.purple_t = 0.0
                self.purple_spawned += 1
                self.spawn_purple()
            for pu in self.purples[:]:
                res2 = pu.update(dt, self.board, self.player)
                if res2 != "alive":
                    if isinstance(res2, tuple) and res2[0] == "wipe":
                        self.on_line_wiped(res2[1], res2[2], res2[3])
                    self.purples.remove(pu)
                    self.claims.clear()          # 紫怪不占 claims，但清一下更稳

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
        if self.board.is_complete():
            self.enter_clear()

    def paint_here(self):
        r, c = self.player.cell
        res = self.board.paint(r, c)
        if res == "valid":
            self.audio.play("paint")                    # 落子：写对了
            return
        if res == "dirty":
            self.audio.play("stain")                    # 落错：失谐的一声
            # 两种脏格，提示要分开：「看都没看清」和「涂错地方」不是一回事
            blind = (r, c) in self.board.must and self.board.reveal[r][c] <= 0
            if blind:
                self.show_hint(story.PAINT_BLIND, 1.8)
            elif not self.stain_warned:
                self.stain_warned = True
                self.show_hint(story.STAIN_WARNING, 4.0)
            if self.board.stains > STAIN_LIMIT:
                # 额度用完之后的每一格脏格：一次外伤，不是判负
                self.health = max(0, self.health - STAIN_DAMAGE)
                self.audio.play("hurt")
                self.show_hint("STAIN  -%d%%" % STAIN_DAMAGE, 1.4)
        elif res == "plain":
            self.audio.play("paint")                    # 平地诱饵也算「写下一格」

    def map_busy(self):
        """地图摊开时想干活：先卷起来。给一行提示 + 一声闷响，别让玩家以为按键坏了。"""
        self.show_hint(story.MAP_IN_HANDS, 1.6)
        self.audio.play("dull")

    def spawn_purple(self):
        """紫怪从生成环上进场。"""
        self.purples.append(PurpleOne(self.ring_spawn_pos()))
        if self.purple_spawned == 1:                 # 第一次来：给一句独白 + 一记低音
            self.say(story.A2_M3)
            self.audio.play("purple")
        else:
            self.audio.play("purple")

    def on_line_wiped(self, axis, idx, cleared):
        """紫怪清掉一整条：报给玩家 + 出声。idx 是主网格 0~24，显示成 1~25。"""
        label = (story.A2_WIPE_ROW if axis == "row" else story.A2_WIPE_COL) % (idx + 1)
        self.show_hint(label, 1.5)
        self.audio.play("wipe")
        if not self.wipe_warned:                     # 第一次被清：一句独白
            self.wipe_warned = True
            self.say(story.A2_M4)

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
        self.state = "CLEAR"
        self.clear_phase = "glow"
        self.clear_t = 0.0
        self.wave_r = 0.0
        self.glow_t = 0.0
        self.prompt_text = ""
        self.show_hint(story.STEP_INTO_ALTAR, 999.0)
        for m in self.monsters:
            m.claim(self.claims)
            m.mode = "hunt"
            m.target = None
        self.purples.clear()                        # 仪式的光把它们一起收掉
        self.claims.clear()

    def update_clear(self, dt):
        self.glow_t += dt
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
            far = max(math.hypot(x - cx, y - cy) for x in (0, WINDOW_W) for y in (0, WINDOW_H))
            if self.wave_r >= far:
                self.board.wipe_stains()                 # 顺手把全部脏格抹掉
                self.capture_map()                       # 这一幕的圣坛定妆了 → 记进地图
                self.clear_phase = "hold"
                self.clear_t = 0.0
        elif self.clear_phase == "hold":
            self.clear_t += dt
            if self.clear_t >= CLEAR_WAVE_HOLD:          # 光散完停一下，再让道具浮出来
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
        """两个随机「已复原的黑格」上浮出 BAG 和 MAP。"""
        cells = sorted(c for c in self.must if self.board.state[c[0]][c[1]] == 1)
        self.rng.shuffle(cells)
        picks = cells[:2]
        self.items = []
        for kind, cell in zip(("bag", "map"), picks):
            self.items.append(Item(kind, cell))

    def update_reward(self, dt):
        for it in self.items:
            it.t = min(1.0, it.t + dt / ITEM_RISE_TIME)

        if self.reward_phase == "wait":
            self.reward_t += dt
            if self.reward_t >= REWARD_DELAY:
                if self.act >= 2:
                    # 背包和地图第一幕就拿到了，第二幕不再浮出来一次：直接收尾
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

