# -*- coding: utf-8 -*-
"""游戏主类：状态机、每帧更新、输入分发。

只管「规则」：画法在 ui.py，数值在 config.py。

第一幕 Phase A 的状态机（剧情层 Phase B 再往上加）：
    TITLE ──> PLAY ──(100 格全复原)──> CLEAR ──> END
                └──(血量归零)──> DEAD ──(点击)──> PLAY（回检查点）
"""

import math
import random

import pygame

from src.board import Board
from src.config import (
    BANNER_TIME, CELL, C_MIRAGE, C_MONSTER, C_PLAYER, FPS, HEALTH_MAX, HINT_TIME, HIT_DAMAGE,
    PANEL_X, PLAYER_GLOW_R, RED_SPAWN_ACCEL, RED_SPAWN_ACCEL_PERIOD, RED_SPAWN_MARGIN,
    RED_SPAWN_PER_MIN, RED_SPD_JITTER, RED_SPEED, SC_ENTER, SC_ESC, SC_F1, SC_J, SC_K,
    SC_KP_ENTER, SC_R, SC_SHIFT, SC_SPACE, SPAWN_ORIGIN, SPAWN_PX, STAIN_LIMIT,
    CLEAR_GLOW_TIME, CLEAR_WAVE_HOLD, CLEAR_WAVE_SPEED, WINDOW_H, WINDOW_W
)
from src.entities import Monster, Player
from src.grid import altar_center, cell_center, target_rect
from src.input_state import InputState
from src.qr import generate_target, required_cells
from src.ui import draw_dead, draw_end, draw_hud, draw_title, draw_world

# 系统提示文本（HUD 类，全大写）。剧情台词不在这个文件里。
MSG_STAIN = "THAT IS NOT DARK. IT IS A STAIN.  [K] TO CLEAR IT."
MSG_STEP_IN = "STEP INTO THE ALTAR"
MSG_ACT_END = "ACT 1 \u2014 END"

# ==== 游戏主类 ====


class Game:
    def __init__(self, window):
        self.window = window
        # 绘制都打到逻辑画布，最后一次性缩放进窗口，布局常量与判定逻辑都不用改
        self.canvas = pygame.Surface((WINDOW_W, WINDOW_H))
        self.screen = self.canvas
        self.scale = window.get_width() / float(WINDOW_W)
        self.needs_scale = window.get_width() != WINDOW_W
        self.input = InputState()
        self.running = True
        self.debug = False
        self._last_dt = 1.0 / FPS              # 给 F1 调试显示用

        # 字体只在初始化时创建一次，绝不在 draw 里新建
        self.f_small = pygame.font.Font(None, 21)
        self.f_main = pygame.font.Font(None, 27)
        self.f_panel = pygame.font.Font(None, 30)
        self.f_mid = pygame.font.Font(None, 46)
        self.f_big = pygame.font.Font(None, 104)

        # --- 复用贴图（每帧新建 Surface 会掉帧）---
        self.mirage_tile = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.mirage_tile.fill(C_MIRAGE)
        self.glow = pygame.Surface((PLAYER_GLOW_R * 2, PLAYER_GLOW_R * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.glow, (*C_PLAYER, 46), (PLAYER_GLOW_R, PLAYER_GLOW_R), PLAYER_GLOW_R)
        self.flash_surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        self.flash_surf.fill((*C_MONSTER, 120))
        self.stain_tile = make_stain_tile()

        # --- 运行时状态（start_act 里铺开）---
        self.state = "TITLE"
        self.menu_t = 0.0
        self.hover = None
        # 旧五关版残留字段：新版不进入 SELECT / RESULT，留着让 ui 里那几个旧界面不报错
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
        self.health = HEALTH_MAX
        self.monsters = []
        self.claims = {}                       # {(r,c): 有几只怪锁着这一格}
        self.elapsed = 0.0                     # 战斗计时（从检查点开始算）
        self.spawn_rate = RED_SPAWN_PER_MIN
        self.spawn_acc = 0.0
        self.accel_step = 0
        self.checkpoint = None
        self.stain_warned = False
        self.reveal_used = False

        self.hint_text = ""
        self.hint_t = 0.0
        self.banner_text = ""
        self.banner_t = 0.0
        self.banner_total = 1.0

        self.clear_phase = None                # "glow" / "wave" / "hold"
        self.clear_t = 0.0
        self.wave_r = 0.0
        self.glow_t = 0.0

    # ---------- 开局 ----------
    def start_act(self):
        """第一幕开局 = 检查点。Phase A 没有剧情，直接从「老者离开那一刻」开始。"""
        self.target, self.qr_content = generate_target(self.rng)
        self.must = required_cells(self.target)
        self.board = Board(self.target, self.must)
        self.player = Player()
        self.health = HEALTH_MAX
        self.monsters = []
        self.claims = {}
        self.elapsed = 0.0
        self.spawn_acc = 0.0
        self.spawn_rate = RED_SPAWN_PER_MIN
        self.accel_step = 0
        self.stain_warned = False
        self.reveal_used = False
        self.hint_text = ""
        self.hint_t = 0.0
        self.banner_text = ""
        self.banner_t = 0.0
        self.clear_phase = None
        self.clear_t = 0.0
        self.wave_r = 0.0
        self.glow_t = 0.0
        self.checkpoint = self.make_checkpoint()
        self.state = "PLAY"
        self.input.held.clear()

    def make_checkpoint(self):
        """「老者离开那一刻」的快照：棋盘 + 血量 + 刷怪节奏。"""
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
        for m in self.monsters:                 # claims 必须归零，否则后面的怪以为全被占了
            m.claim(self.claims)
        self.monsters.clear()
        self.claims.clear()
        self.spawn_acc = 0.0
        self.player.reset()
        self.hint_text = ""
        self.hint_t = 0.0
        self.clear_phase = None
        self.clear_t = 0.0
        self.wave_r = 0.0
        self.input.held.clear()
        self.state = "PLAY"

    # ---------- 提示 ----------
    def show_hint(self, text, secs=HINT_TIME):
        """底部一行系统提示（全大写）。"""
        self.hint_text = text
        self.hint_t = secs

    def show_banner(self, text, secs=BANNER_TIME):
        self.banner_text = text
        self.banner_t = secs
        self.banner_total = secs

    # ---------- 事件 ----------
    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.on_click(*self.mouse_xy())        # 鼠标只用于菜单，不参与涂色
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
            else:
                self.state = "TITLE"               # 回开始页（无存档，重开就重摇一张码）
                self.input.held.clear()
            return

        if st == "TITLE":
            if sc in (SC_ENTER, SC_KP_ENTER, SC_SPACE):
                self.start_act()
            return

        if st == "DEAD":
            if sc in (SC_ENTER, SC_KP_ENTER, SC_SPACE):
                self.restore_checkpoint()
            return

        if st == "END":
            if sc in (SC_ENTER, SC_KP_ENTER, SC_SPACE, SC_R):
                self.start_act()
            return

        if st != "PLAY":
            return

        if sc == SC_R:
            self.start_act()
        elif sc in SC_SHIFT:
            self.cast_anomaly()

    def cast_anomaly(self):
        """Shift：照出脚下 5×5 的灰域。只在圣坛内有效，涂的时候不能照。"""
        if self.input.down(SC_J):
            return                                  # 正在涂：按不动异象
        n = self.board.reveal_around(*self.player.cell)
        if n > 0:
            self.reveal_used = True

    def on_click(self, x, y):
        if self.state == "TITLE":
            self.start_act()
        elif self.state == "DEAD":
            self.restore_checkpoint()
        elif self.state == "END":
            self.start_act()

    def mouse_xy(self):
        """窗口坐标 → 逻辑坐标（画布被缩放过，鼠标也得换算）。"""
        mx, my = pygame.mouse.get_pos()
        return int(mx / self.scale), int(my / self.scale)

    def update_hover(self):
        self.hover = None

    def shift_held(self):
        return any(self.input.down(sc) for sc in SC_SHIFT)

    # ---------- 更新 ----------
    def update(self, dt):
        self._last_dt = dt                          # 仅供 F1 显示
        if self.state in ("TITLE", "DEAD", "END"):
            self.menu_t += dt
            if self.banner_t > 0:
                self.banner_t -= dt
            return
        if self.state == "CLEAR":
            self.update_clear(dt)
            return
        if self.state != "PLAY":
            return

        self.tick_timers(dt)

        # 1) 走格子
        self.player.update(dt, self.input.dir4())

        # 2) 脚下：按住 J 边走边涂；按住 K 边走边抹。
        #    按着 Shift 的时候涂不上去（异象和涂不能同时）
        if self.input.down(SC_J) and not self.shift_held():
            self.paint_here()
        elif self.input.down(SC_K):
            self.board.start_erase(*self.player.cell)

        self.board.update(dt)

        # 3) 红怪：吃黑域 / 追人
        for m in self.monsters[:]:
            res = m.update(dt, self.board, self.claims, self.player)
            if res != "alive":
                if res == "hit":
                    self.health = max(0, self.health - HIT_DAMAGE)
                    self.show_hint("HIT  -%d%%" % HIT_DAMAGE, 1.4)
                self.monsters.remove(m)

        # 4) 刷怪：每 30 秒提速 5%
        self.elapsed += dt
        step = int(self.elapsed // RED_SPAWN_ACCEL_PERIOD)
        if step > self.accel_step:
            self.accel_step = step
            self.spawn_rate *= RED_SPAWN_ACCEL
        if self.elapsed >= RED_SPAWN_MARGIN:
            self.spawn_acc += dt
            interval = 60.0 / self.spawn_rate
            while self.spawn_acc >= interval:
                self.spawn_acc -= interval
                self.spawn_monster()

        # 5) 判定
        if self.health <= 0:
            self.state = "DEAD"
            self.menu_t = 0.0
            self.banner_t = 0.0
            return
        if self.board.is_complete():
            self.enter_clear()

    def tick_timers(self, dt):
        if self.hint_t > 0:
            self.hint_t = max(0.0, self.hint_t - dt)
        if self.banner_t > 0:
            self.banner_t = max(0.0, self.banner_t - dt)

    def paint_here(self):
        res = self.board.paint(*self.player.cell)
        if res == "dirty" and not self.stain_warned:
            self.stain_warned = True
            self.show_hint(MSG_STAIN, 4.0)

    def spawn_monster(self):
        """在 30×30 生成环的四条边上等概率取点：先选边再选 t，长边不会被多算。"""
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
        for m in self.monsters:                     # 仪式已成：它们不再吃黑域，被光牵着走
            m.claim(self.claims)
            m.mode = "hunt"
            m.target = None
        self.claims.clear()
        self.show_hint(MSG_STEP_IN, 999.0)

    def update_clear(self, dt):
        self.tick_timers(dt)
        self.glow_t += dt
        cx, cy = altar_center()
        # 清屏期间红怪不再伤害玩家：它们被圣坛的光牵着，往中心漂
        for m in self.monsters:
            d = pygame.Vector2(cx - m.pos.x, cy - m.pos.y)
            if d.length_squared() > 1.0:
                m.pos += d.normalize() * m.speed * 0.5 * dt

        if self.clear_phase == "glow":
            self.clear_t += dt
            # 圣坛边缘发光 → 玩家走进圣坛就开始扩散波
            if self.board.in_altar(*self.player.cell):
                self.clear_phase = "wave"
                self.clear_t = 0.0
                self.wave_r = 0.0
        elif self.clear_phase == "wave":
            self.wave_r += CLEAR_WAVE_SPEED * dt
            self.clear_monsters_in_wave()
            far = max(math.hypot(x - cx, y - cy) for x in (0, WINDOW_W) for y in (0, WINDOW_H))
            if self.wave_r >= far:
                self.board.wipe_stains()            # 顺手把全部脏格抹掉（设计的一部分）
                self.clear_phase = "hold"
                self.clear_t = 0.0
        elif self.clear_phase == "hold":
            self.clear_t += dt
            if self.clear_t >= CLEAR_WAVE_HOLD:
                self.state = "END"
                self.menu_t = 0.0
                self.hint_t = 0.0                     # 收掉「走进圣坛」的旧提示
                self.show_banner(MSG_ACT_END, 999.0)

    def clear_monsters_in_wave(self):
        cx, cy = altar_center()
        keep = []
        for m in self.monsters:
            if math.hypot(m.pos.x - cx, m.pos.y - cy) <= self.wave_r:
                m.claim(self.claims)
            else:
                keep.append(m)
        self.monsters = keep

    # ---------- 绘制（具体画法都在 ui.py） ----------
    def present(self):
        if self.needs_scale:
            pygame.transform.smoothscale(self.canvas, self.window.get_size(), self.window)
        else:
            self.window.blit(self.canvas, (0, 0))

    def draw(self):
        if self.state == "TITLE":
            draw_title(self)
        else:
            draw_world(self)
            draw_hud(self)
            if self.state == "DEAD":
                draw_dead(self)
            elif self.state == "END":
                draw_end(self)
        self.present()

    # ---------- 旧五关版残留（新版不进入这些状态）----------
    def start_btn(self):
        return pygame.Rect((WINDOW_W - 300) // 2, 470, 300, 92)

    def level_btns(self):
        return []

    def goto_select(self):
        self.state = "TITLE"


def make_stain_tile():
    """脏黑的样子：黑底 + 白色斜条。必须和「纯黑的有效黑域」一眼可分。"""
    surf = pygame.Surface((CELL, CELL))
    surf.fill((17, 17, 24))
    for i in range(-CELL, CELL * 2, 10):
        pygame.draw.line(surf, (226, 226, 232), (i, 0), (i + CELL, CELL), 4)
    return surf
