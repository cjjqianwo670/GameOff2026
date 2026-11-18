# DATA\_SHIFT\_第二幕英文文案

# DATA SHIFT · 第二幕英文文案

> 游戏界面**全英文**。这份文件是第二幕唯一的文案来源，实现时**照抄，不要自己改写**。
> 第一幕的文案在 `DATA_SHIFT_第一幕英文文案.md`，译名表与大小写规则完全沿用那一份。
>
> **状态：草稿**（2026-11-11，AI 按第一幕的调子起草）。台词部分需要作者逐句过一遍才算定稿。
> 定稿后会把 `# 待定` 标记去掉，并同步进 `src/story.py`。

---

## 0. 译名表（在第一幕的基础上只新增两条）

| 中文 | English | 说明 |
| --- | --- | --- |
| 定时图案 | **the timing pattern** | QR 第 6 行 / 第 6 列那两条交替的黑格。专有名词，小写 t |
| 紫色生物 | **the purple one** | **不给学名**。跟「the red ones」同一逻辑；它一次只来一只，所以用单数 |

沿用第一幕：`Sequencer` / `the Altar` / `the Dark` / `the Anomaly` / `the grey` / `a stain` / `the plain` / `the old man` / `the red ones` / `erosion`。

> **第二幕没有对话。** 老者走了（他没有回来），场上没有第二个人。所以这一幕的全部文本 =
> 内心独白 + 系统提示 + 结尾字幕。**这是有意为之**：第一幕很吵，第二幕只剩他自己。

---

## 1. 大小写规则

与第一幕完全一致：HUD / 系统提示**全大写**，独白**正常大小写**。不重复展开。

---

## 2. 内心独白（正常大小写，不打断操作）

| # | 时机 | 英文 | 中文原文（草稿，非最终） |
| --- | --- | --- | --- |
| **A2\_****M1** ✅ | 第二幕开场，光退下去之后（**作者已确认**） | `The old man hasn't come back.`<br>`The three corners are still here.`<br>`Something between them is missing.` | 老者没有回来。三个角还在，但角与角之间少了什么。 |
| **A2\_****M2** | 第一次照出定时图案的绿框 | `Two lines.`<br>`They run between the corners.`<br>`I never looked there.` | 两条线，从角与角之间穿过去。我从来没往那儿看过。 |
| ~~**A2\_**~~~~**M3**~~ | ~~紫色生物第一次出现~~ | `That's not one of the red ones.`<br>`It's slower. It's looking at the lines.` | ~~那不是红色生物。它更慢，而且它在看那两条线。~~ |
| ~~**A2\_**~~~~**M4**~~ | ~~第一次被清掉一整条之后~~ | `It didn't take one cell.`<br>`It took the whole line.` | ~~它不是拿走一格。它拿走了整条。~~ |

> **2026-11-16 变更**：紫怪从第二幕**延后到第四幕**。`A2_M3` / `A2_M4` 两条台词随之挪到第四幕
> （`A2_M3` → `A4_PURPLE`，`A2_M4` → 并入 `A4_M2`）。第二幕只剩红怪（咬核心→板块分离）。

**2026-11-12 补充**（原系统提示改成嘀咕）：

| 常量 | 时机 | 英文 | 中文意思 |
| --- | --- | --- | --- |
| `MONO_PURPLE_IN` | 紫怪第一次进场 | `Something else is moving.` | 有别的什么在动 |
| `MONO_PURPLE_HIT` | 坛内没黑域，紫怪扑人撞到 | `So it wants me instead.` | 它不拿格子了，冲我来了 |

> 清行（被整条拿走）**只有第一次**会触发独白 `A2_M4`，之后完全静默 ——
> 作者 2026-11-12：每次都说会影响体验。后续靠画面（整条变白）和 `wipe` 音效传达，
> 不再有 `ROW n WIPED` 提示，也没有短嘀咕。

> 三条写作约束：
>
> 1. **A2\_****M1 要和第一幕最后一句咬住** —— 老者说过 `I'll come back as soon as I can.` / `If I can.`，这里只用一句
> `hasn't come back` 就够了，不解释、不煽情。
> 2. **A2\_****M3 不说「紫色」**。玩家看到的是一种颜色，但「purple」这个词由系统提示去说会更冷；
> 独白里只对比「不是那些红色的」，保持第一幕 M4 的句式（`It looks like the things the old man drove off`）。
> 3. **A2\_****M4 是全幕的情绪落点**。它必须短、平、不喊，因为玩家刚看着自己十几格进度被抹掉。

---

## 3. 系统提示（全大写）

| 时机 | 英文 | 备注 |
| --- | --- | --- |
| 第二幕完成 | `STEP INTO THE ALTAR` | 复用第一幕同一句，不新写 |

> `SOMETHING ELSE IS MOVING.`（紫怪进场）2026-11-12 改成了心声 `MONO_PURPLE_IN`（见上）。
> `ROW n WIPED.`（清行）整条去掉：第一次清行走 `A2_M4` 独白，之后静默 —— 玩家看画面就知道是哪条线。

> `WIPED` 而不是 `ERASED`：第一幕的 `[K] ERASE` 是玩家自己的动作，这个词已经被占了。
> 被怪物拿掉用另一个词，玩家才不会以为是自己按错了。

---

## 4. 紫色生物不说话（✅ 已定 · 2026-11-11 作者确认）

第一幕那两只说了 `WE WILL BE BACK FOR BOTH OF YOU.`，因为它们是"曾经的码序使"，还有话要说。

**第二幕这只一句台词都没有。** 它不解释自己，也不威胁。它只是来把线吃掉。
它的存在感全部由三样东西承担：`MONO_PURPLE_IN` 那句心声、`A2_M3` 那句独白、以及清行时那声提示。

> 作者原话：「别放狠话了，这样子很怪异」。**定案：不给它任何台词，也不给它名字之外的解释。**
> 它只由三样东西存在：`MONO_PURPLE_IN` 那句心声、`A2_M3` 那句独白、清行时那声提示。
>
> 顺带一个设计上的好处：第一幕那两只会说话（曾经是码序使，还有话要说），**这一只不会** ——
> 玩家不用被告知，也会自己意识到「它已经不是人了」。

---

## 5. 结尾字幕

| 时机 | 英文 |
| --- | --- |
| 第二幕结束 | `ACT 2 — END` |

> 幕名（给文档和选关界面用的）：`TIMING`。第一幕是 `SHAPE`（三个角 = 形状），第二幕补的是
> timing pattern，幕名直接对应机制。**这个名字需要你点头**；不点头就先用 `ACT 2`。

---

## 6. 代码里的常量名（实现时照这个落）

```python
# 独白
A2_M1 = "The old man hasn't come back.\nThe three corners are still here.\nSomething between them is missing."
A2_M2 = "Two lines.\nThey run between the corners.\nI never looked there."
A2_M3 = "That's not one of the red ones.\nIt's slower. It's looking at the lines."
A2_M4 = "It didn't take one cell.\nIt took the whole line."

# 系统提示
A2_PURPLE_IN = "SOMETHING ELSE IS MOVING."
A2_WIPE_ROW = "ROW %d WIPED."          # 1~25
A2_WIPE_COL = "COLUMN %d WIPED."       # 1~25
# STEP_INTO_ALTAR 复用第一幕

# 结尾
ACT2_TITLE = "ACT 2 \u2014 END"
```

---

## 7. 实现提醒（沿用第一幕那份）

1. **一条台词一行**，`\n` 是硬换行（独白里用来断句），宽度交给渲染层折行
2. `...` 是**沉默**，不是省略号
3. 说话人：第二幕**没有**说话人（只有内心独白），不要新造 `SEQUENCER` 的对话行
4. 所有文本只出现在这一个文件里，代码里逐字抄，不要就地改字
5. `ROW %d` 的 `%d` 用**玩家视角的 1\~****25**，写代码时记得 `+1`

---

## 8. 这份草稿里唯一「我替你做了决定」的地方

| # | 决定 | 你可以推翻 |
| --- | --- | --- |
| 1 | 第二幕**没有对话** | **紫怪不说话 ✅ 已定**；老者不出现仍是我的默认，想让他回来就说 |
| 2 | 紫怪**不给名字**，叫 `the purple one` | 想给它学名就说，但要和「the red ones 无名」的规则一起改 |
| 3 | 幕名建议 `TIMING` | 不满意就先用 `ACT 2`，幕名不进游戏画面 |
| 4 | 独白只写 4 条 | 觉得不够就指个时机，我补 |
| 5 | `A2_M3` 里故意不提"紫色" | 如果你想直接点明颜色，改一个词就行 |
