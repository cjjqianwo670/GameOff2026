# DATA\_SHIFT\_第三幕英文文案

# DATA SHIFT · 第三幕英文文案

> 游戏界面**全英文**。这份文件是第三幕唯一的文案来源，实现时**照抄，不要自己改写**。
> 第一 / 第二幕的文案在 `DATA_SHIFT_第一幕英文文案.md` / `DATA_SHIFT_第二幕英文文案.md`，译名表与大小写规则完全沿用。
>
> **状态：草稿**（2026-11-12，作者给了中文意图，AI 起草英文）。台词需要作者逐句过一遍才算定稿。
>
> **2026-11-19 设计变更**：本幕老者不再只写格式信息，而是写**整副骨架**（定位图案 + 定时图案 + 暗模块 + 格式信息，代码 `game.scribe_scope = structural_black_cells`）。骨架写完即通关（不再有「还差格要玩家补」的阶段）。`format_cells` 仍单独保留——只有格式格玩家才要按住 J 补。

---

## 0. 译名表（在前两幕基础上新增两条）

| 中文 | English | 说明 |
| --- | --- | --- |
| 格式信息 | **the format** | QR 里决定「怎么读这张码」的那 30 个位置。**不叫** the format information，口语就叫 the format |
| 黄色生物 | **the yellow ones** | 跟 `the red ones` 同一逻辑。它们认为格式信息是被偷走的 |

沿用：`Sequencer` / `the Altar` / `the Dark` / `the Anomaly` / `the grey` / `a stain` / `the plain` / `the old man` / `the red ones` / `erosion` / `the timing pattern` / `the purple one`。

> 第三幕的**格式信息**（the format）和**定时图案**（the timing pattern）是两个东西，别混：
> 定时图案是两条贯穿的交替线（第二幕），格式信息是贴着三个角的那 30 格（第三幕）。

---

## 1. 大小写规则

与第一幕完全一致：HUD / 系统提示**全大写**，对话与独白**正常大小写**。

---

## 2. 对话（第三幕开场，老者回来）

场景：老者从外面回来，带回「怎么读这张码」的知识。他一边说，一边准备替码序使写整副骨架（定位 + 定时 + 暗模块 + 格式）。

| # | 谁 | 英文 | 中文意图 |
| --- | --- | --- | --- |
| 1 | OLD MAN | `I found another Altar. Out past the edge. Fallen in — but the code on it still reads.` | 我在外面又找到一座圣坛，塌了，但上面的码还能读 |
| 2 | SEQUENCER | `You can read it?` | 你能读？ |
| 3 | OLD MAN | `Not the code. What reads it. Every code carries a short note telling you how to read the rest. Two lines, running out from the corners.` | 读不了码，读到的是「读法」。每张码都带着一小段说明 |
| 4 | SEQUENCER | `I've never seen anything there.` | 我从来没在那儿看见过东西 |
| 5 | OLD MAN | `You wouldn't. It doesn't glow, and the Anomaly won't show it. It took me years to learn where to look. You've had an hour.` | 你当然看不见。它不发光，异象也照不出来。我学了好几年，你才来了一小时 |
| 6 | OLD MAN | `At your speed you'd be at it all night. I'll write it. I know the order.` | 按你的速度得写到天亮。我来写，我知道顺序 |
| 7 | SEQUENCER | `Then what do I do?` | 那我做什么 |
| 8 | OLD MAN | `Keep them off me. And keep what you've already written — they'll take that too.` | 别让它们靠近我。也守住你已经写好的，它们连那个也抢 |
| 9 | SEQUENCER | `Who?` | 谁 |
| 10 | OLD MAN | `Behind me.` | 我后面 |
| 11 | OLD MAN | `Yellow ones. They guard what's left of the old Altar. I read the half-sentence off it before it fell — they've been after me since.` | 黄色的东西。它们守着旧圣坛剩下的东西。我在它塌掉之前读走了上面的半句话——从那时起它们就一直在追我（2026-11-18 改动机：黄怪=旧圣坛守墓人） |
| 12 | SEQUENCER | `They're coming.` | 它们来了 |
| 13 | OLD MAN | `They're already here. Don't let them reach the lines.` | 它们已经到了。别让它们碰到那两条线 |

> 第 13 句之后直接开打（**没有**第一幕那句 `LEAVE_LINE`，他这次不走了）。

---

## 3. 内心独白（正常大小写，不打断操作）

| # | 时机 | 英文 | 中文意图 |
| --- | --- | --- | --- |
| **A3\_****M1** | 老者落下第一格 | `He writes without looking down.`<br>`I still can't see the lines.` | 他连看都不看就写。我还是看不见那两条线 |
| **A3\_****M2** | 第一次有格式格被怪吃掉 | `It's eating what he wrote.` | 它在吃他写的东西 |
| **A3\_****M3** | 清屏前的最后一格写完 | `The corners line up.`<br>`The rest is only pattern.` | 角对齐了。剩下只是图案 |
| **A3\_****Y1** | 第一只黄怪进场 | `That one isn't going for the code.`<br>`It's going for him.` | 它不冲码来。它冲他来的 |
| **A3\_****DOWN** | 老者被打倒 | `He's down.`<br>`I have to get to him.` | 他倒了。我得过去 |
| **A3\_****UP** | ~~把他救起来~~ | `Up. Come on. Up.` | ⚠️ **暂未使用**：救援中说台词会冻住世界，反而救不起来 |

## 2b. 老者自己说的话（2026-11-12 新增）

这三句就是为了「让老者开口」——他的台词全走同一套框，只是名牌是暖米色、不空心变实心，
这样一眼能分清「我在想」和「他在说」。三句都会冻住世界，按回车继续。

| 常量 | 时机 | 英文 | 中文意思 |
| --- | --- | --- | --- |
| **A3\_****STAGGER** | 第一次被黄怪咬断（笔停在半空） | `Ah— hold on. I lost the line.` | 啊——等等。我把线写丢了 |
| **A3\_****UP\_****MAN** | 被救起来之后 | `Still here. Keep going.` | 还在。接着来 |
| **A3\_****READ** | 整副骨架写完了（清屏前，骨架写完即通关） | `That's the reading. The rest is yours.` | 读法成了。剩下的归你 |

> `A3_STAGGER` 只说**一次** —— 被咬是 1.4 秒一口，每口都说话会吵到没法玩。
> `A3_READ` 也只说一次（骨架写完即通关，不再有「还差几格」的阶段）。

| 系统提示 | 时机 | 英文 | 备注 |
| --- | --- | --- | --- |
| ~~`HINT_FILL_REST`~~ | ~~骨架写完后还差格~~ | ~~`%d LEFT.  FILL THEM.`~~ | **2026-11-19 起不再触发**：老者写整副骨架，写完即通关，不存在「还差格」阶段 |

---

## 4. 系统提示（全大写，只留按键 / 道具 / 行动指令）

| 时机 | 英文 | 说明 |
| --- | --- | --- |
| 第三幕第一次有格式格被吃掉 | `A LINE IS BROKEN.  [J] TO PUT IT BACK` | 行动指令：告诉玩家该干什么。**只出现一次** |
| 第三幕第一次按住格式格想补 | `FORMAT CELLS:  HOLD [J]` | 按键教学：格式格要**按住** J 满 0.8 秒才写得动（2026-11-13）。**只出现一次** |
| 老者倒下 | `[H] TO HELP HIM` | 行动指令：站到他旁边按住 H 四秒。**他一起来就消失** |

---

## 5. 道具说明

| 时机 | 英文 | 中文意图 |
| --- | --- | --- |
| 第二幕结束，拾取剑 | `SWORD — the last Sequencer left it. He never finished.` | 剑。上一位码序使留下的。他没能写完（2026-11-18 定） |

> ~~⚠️ 待作者定~~：剑是谁留下的？**2026-11-18 已定**：是上一位（前前任）码序使留下的——他没写完就死了。
> 这句回收了「前人会死在这里」这件事，也解释了为什么剑「一直在光里等着」。

---

## 6. 幕字幕

`ACT 3 — END`
