# -*- coding: utf-8 -*-
"""棋盘：格子状态、异象灰域、脏格计数、涂改与抹除计时。

只管「数据」，不碰任何绘制。四条状态：
    WHITE   白（没涂）
    VALID   有效黑域（the Dark）—— 必涂格上的黑，或平地上的诱饵黑，都算它
    DIRTY   脏黑（a stain）—— 圣坛内涂在非必涂格上，黑白相间，必须 K 擦掉
    ERASING 抹除中（0.25s 塌陷）
"""

from src.config import (
    BOARD_ADJACENT, BOARDS, DARK_MODULE, DIRTY, ERASE_CAST, ERASING, GRID_N, MERGE_SLIDE,
    MIRAGE_FADE, MIRAGE_RADIUS, TARGET_OFFSET, VALID, WHITE
)
from src.grid import to_target

# ==== 棋盘 ====


class Board:
    def __init__(self, target, must, open_boards=None):
        self.target = target                                   # 21×21 的 0/1 真码
        self.must = set(must)                                  # 本轮必涂格（主网格坐标）
        # 已经接回来的板块（名字见 config.BOARDS）。空/None = 四块全通（第 2~5 幕的常态）
        self.open_boards = set(BOARDS) if open_boards is None else set(open_boards)
        # 第二幕起：核心被怪物破坏 → 板块「分离」。它仍在 open_boards（能站、能写，好让玩家
        # 走过去补核心），但被记进 detached —— 分离中的板块**不计入通关进度**，视觉上被推开一格。
        self.detached = set()
        self.slide = {}                                        # 板块名 → 滑回原位的剩余秒（纯表现）
        self.state = [[WHITE] * GRID_N for _ in range(GRID_N)]
        self.erase_t = [[0.0] * GRID_N for _ in range(GRID_N)]
        self.reveal = [[0.0] * GRID_N for _ in range(GRID_N)]   # 异象灰域剩余秒
        self.flash = {}
        self.flash_kind = {}                  # (r,c) -> "red" / "purple"，ui 据此选闪光色                                        # {(r,c): 剩余秒}，被怪啃那一下的红闪
        self.stains = 0                                        # ⚠️ 本幕**累计**涂错格数，擦掉不返还

    # --- 查询 ---
    def board_of(self, r, c):
        """这一格属于哪块板块（名字）；在圣坛外返回 None。

        2026-11-14：**裂缝不是格子**。四块板块刚好铺满 441 格，缝是「板块被推开后空出来的
        额外空间」，只存在于画面上（`config.BOARD_PUSH`），所以这里永远能查到板块。
        """
        t = to_target(r, c)
        if t is None:
            return None
        tr, tc = t
        for name, (r0, c0, r1, c1) in BOARDS.items():
            if r0 <= tr <= r1 and c0 <= tc <= c1:
                return name
        return None

    def in_altar(self, r, c):
        """圣坛 = **已经接回来的板块**。没接回来的板子算平地（the plain）。

        2026-11-14：圣坛从「一整块 21×21」改成四块。没接回来的板块站不上去 ——
        但那条限制在 game 的移动里做（`can_stand`），这里只回答「能不能写/能不能照」。
        """
        b = self.board_of(r, c)
        return b is not None and b in self.open_boards

    def open_board(self, name):
        """接回一块板块：它从「被推开一格」滑回原位（0.3 秒）。"""
        self.open_boards.add(name)
        self.slide[name] = MERGE_SLIDE

    def detach_board(self, name):
        """核心被怪物破坏 → 这块板块和**相邻的两块**分离（第二幕起）。

        作者 2026-11-15 定的语义：分离不是「这块板自己飘走」，而是「它和左右邻居之间裂开缝」。
        视觉上它被推开一格（`BOARD_PUSH`），于是和 `BOARD_ADJACENT[name]` 里那两块各裂开一条缝；
        其余相邻板块之间仍连着。右下角（BR）没有核心，永远不会自己分离，是「不动的锚点」。

        它仍在 open_boards（能站、能写，好让玩家走过去补核心），
        但被记进 detached —— 分离中的板块**不计入通关进度**，直到玩家补满核心再并回来。
        """
        self.detached.add(name)
        self.slide.pop(name, None)

    def reattach_board(self, name):
        """补满核心 → 板块滑回原位，和相邻两块之间的缝合上。"""
        self.detached.discard(name)
        self.slide[name] = MERGE_SLIDE

    def adjacent_boards(self, name):
        """这块板块的两个邻居（按 config.BOARD_ADJACENT）。"""
        return BOARD_ADJACENT.get(name, ())

    def push_frac(self, name):
        """这块此刻被推开了几成：0 = 已经归位，1 = 还差一整格。"""
        if name not in self.open_boards or name in self.detached:
            return 1.0
        return max(0.0, self.slide.get(name, 0.0)) / MERGE_SLIDE

    def fractured(self):
        """圣坛还裂着吗（第一幕：还有板块没接回来）。"""
        return len(self.open_boards) < len(BOARDS)

    def can_stand(self, r, c):
        """能不能站上去（这格本身是不是可站区域）。

        - **还裂着的时候：只能站在已经接回来的板块上**（2026-11-14 修 bug）。
          原来坛外的平地一律放行，于是玩家能从自己那块「走」到外面去 ——
          而石板是被**画**在外面的，脚底下那格逻辑上还是平地，看起来就像踩在裂缝里、或者
          走到了祭坛框里面。
        - **分离板块内部能站能走**：分离的板还在 open_boards 里，玩家被困在里面时得能动。
          「跨缝」的隔离不在这里做，而在 game 的移动判定里（`_can_stand` 按「从哪到哪」判）。
        - **坛外（圣坛之外，`board_of` 返回 None）永远不能站**（2026-11-16 作者定）：
          码序者不能走进虚空。老者 / 道具都在坛边，玩家站在圣坛最外沿就能交互，
          不需要出坛。怪物可以越过，那是它们的领域。
        """
        b = self.board_of(r, c)
        if b is None:                                          # 坛外 / 虚空
            return False
        return b in self.open_boards

    def is_seam(self, a, b):
        """板块 a 和 b 之间此刻是不是「分离缝」（有缝、不能直接跨，得走界丝通道）。"""
        if a == b or b not in self.adjacent_boards(a):
            return False
        return a in self.detached or b in self.detached

    def progress(self):
        """已复原本轮必涂格数。分离中的板块（`detached`）不计入 —— 核心被破坏，
        那一块就算「暂时丢了」，补满核心才会回来。"""
        n = 0
        for (r, c) in self.must:
            if self.state[r][c] == VALID and self.board_of(r, c) not in self.detached:
                n += 1
        return n

    def is_complete(self):
        """完成条件：100 格全为有效黑域。

        脏格**不再**卡通关：超出额度改为每次扣血（见 game.paint_here），
        所以手滑的代价是命，不是「这局废了」。
        """
        return self.progress() >= len(self.must)

    def revealed(self, r, c):
        """这一格此刻该不该画灰域。"""
        return self.reveal[r][c] > 0 and self.state[r][c] == WHITE

    # --- 操作 ---
    def paint(self, r, c):
        """涂黑脚下这一格。返回 "valid" / "dirty" / "plain" / None（没变化）。

        **圣坛内必须先照出来**（作者 2026-11-12 定）：灰域还亮着（`reveal > 0`）才写得对 ——
          必涂格 + 灰域亮着 → VALID
          其余（非必涂格 / 灰域已褪 / 从没照过 / 被怪清掉后重涂）→ DIRTY，累计 +1
        也就是「闭着眼睛写」一律算脏格。紫怪清掉一行之后想补回来，**必须重新按 Shift 照**。

        平地（诱饵）→ VALID：那里照不出灰域（`reveal_around` 只在坛内生效），
        但也不参与判定、不计数，所以按老规矩放行。

        分离板块**能涂**（它还在 open_boards，玩家站上去补核心/补格子靠这个）。
        「隔缝涂」不需要在这里挡 —— 涂只作用于脚下格，移动挡了跨缝，自然就涂不过去。
        """
        if self.state[r][c] != WHITE:
            return None
        if self.in_altar(r, c):
            if (r, c) in self.must and self.reveal[r][c] > 0:
                self.state[r][c] = VALID
                return "valid"
            self.state[r][c] = DIRTY
            self.stains += 1
            return "dirty"
        self.state[r][c] = VALID
        return "plain"

    def start_erase(self, r, c):
        """K：0.25 秒塌陷。脏格的累计计数**不减**（擦了也不返还）。"""
        if self.state[r][c] not in (VALID, DIRTY):
            return False
        self.state[r][c] = ERASING
        self.erase_t[r][c] = ERASE_CAST
        return True

    def force_white(self, r, c, kind="red"):
        """被怪物清掉：无条件变白 + 闪一下。kind 只用来决定闪什么颜色
        （红怪啃单格 = red，紫怪清整条 = purple）。"""
        self.state[r][c] = WHITE
        self.erase_t[r][c] = 0.0
        self.flash[(r, c)] = 0.15
        self.flash_kind[(r, c)] = kind

    def reveal_around(self, r, c, radius=None):
        """异象：以 (r,c) 为中心 (2R+1)² 照出灰域，返回被点亮（含给旧灰域续期）的格数。

        ⚠️ **只照「本轮必涂格」**（2026-11-14 改）。原来是按整张目标码 `target` 照 ——
            结果第一幕圣坛中央能照出 13 格灰，而那 13 格全部不在本幕清单里，
            照着灰域涂 = 13 个脏格、掉 15% 血。玩家学的是「灰的就能写」，
            却在 56% 的面积上被这条规则反过来罚（实测：谨慎机器人 67 秒攒 29 个脏格，掉到 5% 血）。
            现在灰域的语义只有一条：**它亮着，就是此刻该写的地方**。

        - 只在圣坛内生效；站在平地上按 Shift 一个灰域都没有（叙事设定 + 玩法边界）
        - 已经涂黑的、本来就不该黑的，照了也没意义
        - 已经照过的格子会把 5 秒重新充满（再照一次就是再看一眼）
        - `radius` 不传就用默认的 `MIRAGE_RADIUS`；第四幕给 3（7×7），因为那一幕是「扫」
        """
        if not self.in_altar(r, c):
            return 0
        k = MIRAGE_RADIUS if radius is None else radius
        n = 0
        for rr in range(max(0, r - k), min(GRID_N, r + k + 1)):
            for cc in range(max(0, c - k), min(GRID_N, c + k + 1)):
                if (rr, cc) not in self.must:          # 本幕还轮不到的部分：不照，也就不骗人
                    continue
                if self.state[rr][cc] != WHITE:
                    continue
                n += 1
                self.reveal[rr][cc] = MIRAGE_FADE
        return n

    def clear_row(self, r, kind="red"):
        """把这一整行的有效黑域清成白色，返回清掉几格。"""
        n = 0
        for c in range(GRID_N):
            if self.state[r][c] == VALID:
                self.force_white(r, c, kind)
                n += 1
        return n

    def clear_area(self, r, c, radius=1, kind="green"):
        """清以 (r,c) 为中心 (2*radius+1)² 区域里的有效黑域，返回清掉的格子列表。

        绿怪用：radius=1 → 3×3。只清有效黑域，脏格不动（和红怪/紫怪一致）。
        """
        wiped = []
        for rr in range(max(0, r - radius), min(GRID_N, r + radius + 1)):
            for cc in range(max(0, c - radius), min(GRID_N, c + radius + 1)):
                if self.state[rr][cc] == VALID:
                    self.force_white(rr, cc, kind)
                    wiped.append((rr, cc))
        return wiped

    def clear_column(self, c, kind="red"):
        """把一整列的有效黑域清成白色，返回清掉几格。"""
        n = 0
        for r in range(GRID_N):
            if self.state[r][c] == VALID:
                self.force_white(r, c, kind)
                n += 1
        return n

    def clear_line(self, axis, index, kind="purple"):
        """清整条线：axis = "row" / "col"。**只清有效黑域，脏格不动**

        （脏格不是 the Dark —— 紫怪清行/红怪吃格都不碰它，规则一致。）
        """
        return (self.clear_row(index, kind) if axis == "row"
                else self.clear_column(index, kind))

    def line_dark(self, axis, index):
        """这条线上有多少**有效黑域**（紫怪用它挑「黑格最多的那条」；脏格不算）。"""
        if axis == "row":
            return sum(1 for c in range(GRID_N) if self.state[index][c] == VALID)
        return sum(1 for r in range(GRID_N) if self.state[r][index] == VALID)

    def set_must(self, must):
        """换本幕的必涂格集合（第二幕在第一幕 100 格的基础上加定时图案 6 格）。

        只换集合，不动格子状态 —— 第一幕涂好的黑格原地保留。
        """
        self.must = set(must)
        return len(self.must)

    def wipe_stains(self):
        """清屏：把全部脏格抹回白色，返回抹掉几格。累计计数不动（本幕账已经记下了）。"""
        n = 0
        for r in range(GRID_N):
            for c in range(GRID_N):
                if self.state[r][c] == DIRTY:
                    self.state[r][c] = WHITE
                    n += 1
        return n

    def update(self, dt):
        for k in list(self.slide):
            self.slide[k] = max(0.0, self.slide[k] - dt)
            if self.slide[k] <= 0.0:
                del self.slide[k]
        for r in range(GRID_N):
            srow, erow, vrow = self.state[r], self.erase_t[r], self.reveal[r]
            for c in range(GRID_N):
                if srow[c] == ERASING:
                    erow[c] -= dt
                    if erow[c] <= 0:
                        erow[c] = 0.0
                        srow[c] = WHITE
                if vrow[c] > 0:
                    vrow[c] = max(0.0, vrow[c] - dt)
        for k in list(self.flash):
            self.flash[k] -= dt
            if self.flash[k] <= 0:
                del self.flash[k]

    # --- 检查点快照 ---
    def snapshot(self):
        """只存「会变」的东西：格子状态、抹除计时、灰域、累计脏格、分离的板块。"""
        return {
            "state": [row[:] for row in self.state],
            "erase_t": [row[:] for row in self.erase_t],
            "reveal": [row[:] for row in self.reveal],
            "stains": self.stains,
            "detached": set(self.detached),
        }

    def restore(self, snap):
        self.state = [row[:] for row in snap["state"]]
        self.erase_t = [row[:] for row in snap["erase_t"]]
        self.reveal = [row[:] for row in snap["reveal"]]
        self.stains = snap["stains"]
        self.detached = set(snap.get("detached", ()))
        self.flash.clear()

    # --- 界丝（BOUND-THREAD）与跨缝通道 ---
    def thread_cell(self):
        """界丝的固定黑点（主网格坐标）—— 就是暗模块 `DARK_MODULE`，全图唯一。"""
        return (DARK_MODULE[0] + TARGET_OFFSET[0], DARK_MODULE[1] + TARGET_OFFSET[1])

    def bridge_cells(self, facing, cell):
        """按朝向 `facing` 从 `cell` 搭一条跨缝通道，返回通道格子列表；搭不了返回 None。

        通道 = [起点格, 对面格]。起点是玩家脚下（必须属于某块板块），对面是沿朝向走一格
        之后落入的**另一块板块**（或坛外平地）。两块板块之间的「缝」在逻辑坐标里就是板块
        边界，宽度为 0（推开一格只是画面表现），所以逻辑上起点和对面就是相邻的两格。
        """
        r, c = cell
        dr, dc = _FACING_DELTA[facing]
        nr, nc = r + dr, c + dc
        if not (0 <= nr < GRID_N and 0 <= nc < GRID_N):
            return None
        here, there = self.board_of(r, c), self.board_of(nr, nc)
        # 必须真的跨过一条「缝」：起点在板块内，对面在另一块板块或坛外。
        if here is None:
            return None
        if there == here:
            return None
        return [(r, c), (nr, nc)]

    def can_bridge(self, facing, cell):
        """玩家此刻能不能朝 `facing` 搭通道（脚下得是板块格、对面得跨了缝）。"""
        return self.bridge_cells(facing, cell) is not None


# facing 0上 1下 2左 3右 → (dr, dc)，和 input_state.DIR_KEYS 的 (dr, dc) 语义一致
_FACING_DELTA = {0: (-1, 0), 1: (1, 0), 2: (0, -1), 3: (0, 1)}
