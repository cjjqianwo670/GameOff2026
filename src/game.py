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

from src import story
from src.board import Board
from src.config import (
    BANNER_TIME, CALL_RANGE_PX, CELL, CLEAR_WAVE_HOLD, CLEAR_WAVE_SPEED, C_MIRAGE, C_MONSTER,
    C_PLAYER, CLOSE_RANGE_PX, DEBRIS_GRAVITY, DEBRIS_JITTER, DEBRIS_SPEED, DEBRIS_UP, FPS,
    GAP_SECONDS, HEALTH_MAX, HINT_TIME, HIT_DAMAGE, INTRO_FADE, INTRO_FALL, INTRO_SHOW, MIRAGE_ALPHA_MAX,
    INTRO_TOTAL, ITEM_PICK_RANGE, ITEM_RISE_TIME, MONOLOGUE_TIME, OLDMAN_CELL,
    OLDMAN_LEAVE_SPEED, OLDMAN_RUN_SPEED, PLAYER_GLOW_R, PROP_DEAD_CELL, PROP_RANGE_PX,
    PROP_TOOL_CELL, RED_SPAWN_ACCEL, RED_SPAWN_ACCEL_PERIOD, RED_SPAWN_PER_MIN, RED_SPD_JITTER,
    RED_SPEED, REWARD_DELAY, REWARD_WAIT, SC_B, SC_ENTER, SC_ESC, SC_F1, SC_J, SC_K, SC_KP_ENTER,
    SC_R, SC_SHIFT, SC_SPACE, SC_T, SHAKE_LEAD, SHAKE_SEQ, SHAKE_STEP, SPAWN_ORIGIN, SPAWN_PX,
    SPREAD_TIME, STAIN_DAMAGE, STAIN_LIMIT, TARGET_N, TARGET_OFFSET, THREAT_TIME,
    TUTORIAL_MOVE_SECONDS, WINDOW_H, WINDOW_W
)
from src.entities import Item, Monster, OldMan, Player, SceneRed
from src.grid import altar_center, cell_center
from src.input_state import InputState
from src.qr import generate_target, required_cells
from src.ui import (draw_dead, draw_dialog, draw_end, draw_hud, draw_title, draw_world,
                    make_stain_tile)

# 可移动 / 可涂的相位
MOVE_STATES = ("TUTORIAL", "FREE_ROAM", "GAP", "BATTLE", "CLEAR", "REWARD")
PAINT_STATES = ("TUTORIAL", "FREE_ROAM", "GAP", "BATTLE")

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
        self._last_dt = 1.0 / FPS

        # 字体只建一次
        self.f_small = pygame.font.Font(None, 21)
        self.f_main = pygame.font.Font(None, 27)
        self.f_panel = pygame.font.Font(None, 30)
        self.f_mid = pygame.font.Font(None, 46)
        self.f_big = pygame.font.Font(None, 104)
        self.f_tiny = pygame.font.Font(None, 18)      # 道具标签
        self.f_name = pygame.font.Font(None, 24)      # 对话说话人
        self.f_dlg = pygame.font.Font(None, 25)       # 对话台词

        # 复用贴图（每帧新建 Surface 会掉帧）
        self.mirage_tile = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.mirage_tile.fill(C_MIRAGE)
        self.ghost = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.ghost.fill((*C_MIRAGE, 255))
        self.glow = pygame.Surface((PLAYER_GLOW_R * 2, PLAYER_GLOW_R * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.glow, (*C_PLAYER, 46), (PLAYER_GLOW_R, PLAYER_GLOW_R), PLAYER_GLOW_R)
        self.flash_surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.flash_surf.fill((*C_MONSTER, 120))
        self.stain_tile = make_stain_tile()
        self.shake_buf = pygame.Surface((WINDOW_W, WINDOW_H))
        self.spread_surf = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)

        # --- 状态 ---
        self.state = "TITLE"
        self.menu_t = 0.0
        self.hover = None
        # 旧五关版残留字段（新版不进 SELECT / RESULT）
        self.level = 1
        self.unlocked = 1
        self.sel = 1
        self.result = None

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
        self.stain_warned = False

        # 过场
        self.cs_t = 0.0
        self.cs_red_in = False
        self.cs_flee = False
        self.cs_m3 = False
        self.oldman_faced_altar = False

        # 对话
        self.dlg_lines = None
        self.dlg_i = 0
        self.dlg_phase = "talk"
        self.dlg_run_t = 0.0
        self.dlg_hold = 0.0

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
        self.reward_phase = None
        self.reward_t = 0.0
        self.spread_r = 0.0
        self.gap_t = 0.0

    # ---------- 开局 ----------
    def start_act(self):
        self.target, self.qr_content = generate_target(self.rng)
        self.must = required_cells(self.target)
        self.board = Board(self.target, self.must)
        self.player = Player()
        self.oldman = OldMan(OLDMAN_CELL, facing=0)      # 背对玩家：朝世界外（上方）
        self.oldman_turned = False
        self.health = HEALTH_MAX
        self.monsters = []
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
        self.stain_warned = False

        self.cs_t, self.cs_red_in, self.cs_flee, self.cs_m3 = 0.0, False, False, False
        self.oldman_faced_altar = False
        self.dlg_lines, self.dlg_i, self.dlg_hold = None, 0, 0.0
        self.dlg_phase = "talk"
        self.prop_done = {"dead": False, "tool": False}

        self.clear_phase, self.clear_t, self.wave_r, self.glow_t = None, 0.0, 0.0, 0.0
        self.items = []
        self.has_bag = self.has_map = False
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
        }

    def restore_checkpoint(self):
        cp = self.checkpoint
        self.board.restore(cp["board"])
        self.health = cp["health"]
        self.elapsed = cp["elapsed"]
        self.spawn_rate = cp["spawn_rate"]
        self.accel_step = cp["accel_step"]
        for m in self.monsters:
            m.claim(self.claims)
        self.monsters.clear()
        self.claims.clear()
        self.scene_reds.clear()
        self.items.clear()
        self.has_bag = self.has_map = False
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
        self.state = "GAP"
        self.gap_t = 0.0
        self.input.held.clear()

    # ---------- 文本通道 ----------
    def say(self, text, secs=MONOLOGUE_TIME):
        """内心独白：屏幕下方，不打断操作。"""
        self.mono_text = text
        self.mono_t = secs

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
                self.start_act()
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
        elif sc in SC_SHIFT:
            self.cast_anomaly()
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
            self.start_act()

    def mouse_xy(self):
        mx, my = pygame.mouse.get_pos()
        return int(mx / self.scale), int(my / self.scale)

    def update_hover(self):
        self.hover = None

    def shift_held(self):
        return any(self.input.down(sc) for sc in SC_SHIFT)

    # ---------- 更新 ----------
    def update(self, dt):
        self._last_dt = dt
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

        # 脚下涂改：按着 Shift 时涂不上去（异象和涂不能同时）
        if st in PAINT_STATES:
            if self.input.down(SC_J) and not self.shift_held():
                self.paint_here()
            elif self.input.down(SC_K):
                self.board.start_erase(*self.player.cell)

        self.board.update(dt)

        if st == "TUTORIAL":
            self.update_tutorial(dt)
        elif st == "FREE_ROAM":
            self.update_roam(dt)
        elif st == "GAP":
            self.update_gap(dt)
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
        if self.move_time >= TUTORIAL_MOVE_SECONDS and self.prompt_text != story.TUTORIAL_SHIFT:
            self.prompt_text = story.TUTORIAL_SHIFT

    def cast_anomaly(self):
        if self.state not in PAINT_STATES:
            return
        if self.input.down(SC_J):
            return                                      # 正在涂：按不动异象
        n = self.board.reveal_around(*self.player.cell)
        if n <= 0:
            return
        if not self.reveal_used:
            self.reveal_used = True
            if self.state == "TUTORIAL":
                self.say(story.M2)
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
            if not self.oldman_turned:
                self.oldman_turned = True                # 只是转身（带着疑惑）
                self.oldman.face_to(self.player.pos)
                return
            if d <= CLOSE_RANGE_PX:
                self.start_dialog(story.branch(False))

    # ---------- 对话 ----------
    def start_dialog(self, lines, run_over=False):
        self.state = "DIALOG"
        self.dlg_lines = list(lines) + [story.LEAVE_LINE]
        self.dlg_i = 0
        self.dlg_phase = "run" if run_over else "talk"
        self.dlg_run_t = 0.0
        self.dlg_hold = 0.0
        self.prompt_text = ""

    def update_dialog(self, dt):
        if self.dlg_phase == "run":
            self.dlg_run_t += dt
            target = (self.player.pos.x - 34, self.player.pos.y)
            done = self.oldman.move_toward(target, OLDMAN_RUN_SPEED, dt)
            if done or self.dlg_run_t > 1.8:
                self.dlg_phase = "talk"
            return
        if self.dlg_hold > 0:
            self.dlg_hold = max(0.0, self.dlg_hold - dt)
            if self.dlg_hold <= 0:
                self.end_dialog()

    def advance_dialog(self):
        if self.dlg_phase != "talk" or self.dlg_lines is None:
            return
        if self.dlg_i < len(self.dlg_lines) - 1:
            self.dlg_i += 1
        else:
            self.dlg_hold = 1.0                          # `If I can.` 停 1 秒
        self.hint_t = 0.0

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
        self.show_hint(story.INCOMING, 2.8)

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
                    self.show_hint("HIT  -%d%%" % HIT_DAMAGE, 1.4)
                self.monsters.remove(m)

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
        res = self.board.paint(*self.player.cell)
        if res != "dirty":
            return
        if not self.stain_warned:
            self.stain_warned = True
            self.show_hint(story.STAIN_WARNING, 4.0)
        if self.board.stains > STAIN_LIMIT:
            # 额度用完之后的每一格脏格：一次外伤，不是判负
            self.health = max(0, self.health - STAIN_DAMAGE)
            self.show_hint("STAIN  -%d%%" % STAIN_DAMAGE, 1.4)

    def spawn_monster(self):
        side = self.rng.randrange(4)
        t = self.rng.random() * SPAWN_PX
        x0, y0 = SPAWN_ORIGIN
        if side == 0:
            pos = (x0 + t, y0)
        elif side == 1:
            pos = (x0 + SPAWN_PX, y0 + t)
        elif side == 2:
            pos = (x0 + t, y0 + SPAWN_PX)
        else:
            pos = (x0, y0 + t)
        speed = RED_SPEED * self.rng.uniform(*RED_SPD_JITTER)
        self.monsters.append(Monster(pos, speed))

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
            if self.board.in_altar(*self.player.cell):
                self.clear_phase = "wave"
                self.clear_t = 0.0
                self.wave_r = 0.0
        elif self.clear_phase == "wave":
            self.wave_r += CLEAR_WAVE_SPEED * dt
            self.clear_monsters_in_wave()
            far = max(math.hypot(x - cx, y - cy) for x in (0, WINDOW_W) for y in (0, WINDOW_H))
            if self.wave_r >= far:
                self.board.wipe_stains()
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
                self.show_banner(story.ACT_TITLE, 999.0)

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
        self.present()

    def apply_shake(self):
        dx, dy = self.shake_off
        if dx == 0 and dy == 0:
            return
        self.shake_buf.blit(self.canvas, (0, 0))
        self.canvas.fill((11, 15, 20))
        self.canvas.blit(self.shake_buf, (dx, dy))

    # ---------- 旧五关版残留 ----------
    def start_btn(self):
        return pygame.Rect((WINDOW_W - 300) // 2, 470, 300, 92)

    def level_btns(self):
        return []

    def goto_select(self):
        self.state = "TITLE"
