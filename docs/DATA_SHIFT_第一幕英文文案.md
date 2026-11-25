# DATA\_SHIFT\_第一幕英文文案

# DATA SHIFT · 第一幕英文文案

> 游戏界面**全英文**。这份文件是唯一的文案来源，实现时**照抄，不要自己改写**。
> 中文原文在 `DATA_SHIFT_游戏指导方案.md` 里，这里是对应的英文版。
> 改文案只改这一个文件。

---

## 0. 译名表（**先统一，再动笔**）

| 中文 | English | 说明 |
| --- | --- | --- |
| 码序使 | **Sequencer** | 身份名。玩家角色，全大写时 `SEQUENCER` |
| 圣坛 | **the Altar** | 21×21 那一片。专有名词，大写 A |
| 黑域 | **the Dark** | 你涂出来的有效黑格。专有名词，大写 D |
| 异象 | **the Anomaly** | 按 Shift 照出灰域这件事 |
| 灰域 / 灰格子 | **the grey** | 提示层，不算专有名词，小写 |
| 脏黑 | **a stain** | 涂错留下的黑白相间格 |
| 平地 | **the plain** | 圣坛之外 |
| 老者 | **the old man** | **不给名字**。他不知道玩家是谁，也不需要自我介绍 |
| 红色生物 | **the red ones** | **不给学名**。玩家不知道它们是什么，别起名字 |
| 侵蚀 | **erosion** | 老者那句「抵抗怪物侵蚀」用它 |

> 为什么不给「老者」和「红怪」起名字：这个故事里没有人有余力互相介绍。**无名的称呼本身就是内容。**

---

## 1. 大小写规则

| 类型 | 规则 | 例 |
| --- | --- | --- |
| HUD、按钮、系统提示 | **全大写** | `NOISE 3` / `PRESS T` / `LEVEL 1/5` |
| 剧情台词、独白、对话 | **正常大小写** | `Who am I? Where is this?` |

一整句全大写的英文读起来很累，而且没有语气。**只有短提示才全大写。**

---

## 2. 独白（内心独白，玩家看不到说话人）

显示方式建议：屏幕下方一行，斜体或略暗的字色，**不打断操作**，停留 2.5\~3 秒。

| # | 时机 | 英文 | 中文原文 |
| --- | --- | --- | --- |
| M1 | 醒来后 1 秒 | `Who am I?`<br>`Where is this?` | 我是谁？我在哪？ |
| M2 | 第一次照出异象后 | `Why do I feel the pattern under the floor... moving?` | 为什么我有时候能够感受到地上的图案在变化？ |
| M3 | 看见红怪逃走之后 | `Why you two?` | 为什么是你们？ |
| M4 | 靠近死亡的红怪（可选） | `What is this? It looks like the things the old man drove off. It's not moving.` | 这里是什么？好像刚刚老者驱赶的生物，不过它们好像已经死了。 |
| M5 | 靠近用过的道具（可选） | `These tools are dead. What were they for?` | 这些工具好像已经不能用了，它们是用来做什么的呢？ |

> M4 和 M5 是**可选**的，玩家不去碰就不触发。两个都碰了也可以，不冲突。

**2026-11-12 补充**：下面这些原本是「系统提示」，作者要求改成码序使的嘀咕（增强代入感），也归到独白这一类：

| 常量 | 时机 | 英文 | 中文意思 |
| --- | --- | --- | --- |
| `MONO_STAIN` | 涂错成脏格 | `That one failed. It's just a stain.` | 好像失败了，这只是一块污渍 |
| `MONO_BLIND` | 没照出灰域就落笔 | `I can't see it. I should look first.` | 我还看不清，得先照一照 |
| `MONO_INCOMING` | 红怪来袭（开战） | `They're coming back.` | 它们回来了 |
| `MONO_HIT` | 被红怪咬 | `Agh! It bit me.` | 啊！它咬到我了 |
| `MONO_STAIN_HURT` | 脏格超标开始扣血 | `Too many stains... it's taking a toll.` | 污渍太多了……在侵蚀我 |
| `A1_GUIDE` | 第一幕老者走后（开战前） | `The Anomaly shows three finder squares and one fixed dark dot. Restore them all.`<br>`Restore a slab, and it joins to the next — only a whole slab opens the way.` | 用异象照出三个定位图案和一个固定黑点完成复原；每复原一块板块就与下一块合并，复原完整才能继续探索 |

---

## 3. 系统提示（全大写）

| 时机 | 英文 | 中文原文 |
| --- | --- | --- |
| 学会走路 | `[W] UP    [S] DOWN    [A] LEFT    [D] RIGHT` | W向上走，S向后走，A向左走，D向右走 |
| 学会异象 | `TRY [SHIFT]` | 尝试按一下shift，会触发异象 |
| 进入老者范围 | `PRESS [T] TO CALL OUT` | 按T呼喊老者 |
| 第一次涂出脏格（只教按键） | `[K] TO CLEAR IT.` | 按K清除（叙事部分已改成心声 `MONO_STAIN`） |
| 拾取道具 | `PRESS [B] TO PICK UP` | 按b拾取 |

> `THEY ARE COMING.`（红怪来袭）原来也在这张表里，2026-11-12 改成了心声 `MONO_INCOMING`。
> `ONE PATTERN LEFT.` / `TWO PATTERNS LEFT.`（进度提示）从未实现，也不再需要——删了。

---

## 4. 红怪的狠话

原文只写了「红色生物放狠话」，没给台词。英文版：

```
WE WILL BE BACK FOR BOTH OF YOU.
```

显示方式：红怪逃走那一刻，屏幕中央偏上，**全大写、猩红色**，2 秒。

> 用 `WE`，不用 `I`——它们是两只，而且**用复数让玩家隐约觉得它们是一个集体**。
> 后面老者说「它们原来都是码序使」，这句话会回头咬这一句。

---

## 5. 对话（按回车逐句推进）

### 5.1 对话一 · 坛内呼喊（老者兴奋地跑过来）

| 说话人 | 英文 | 中文原文 |
| --- | --- | --- |
| OLD MAN | `You— you're a Sequencer, aren't you? I've waited so long. These creatures are a plague. They ruin my work, and sometimes they come for me.` | 太好了！你一定是码序者吧！我等你很久了，这里的怪物实在太可恶了，总是妨碍我的工作，甚至有时还会攻击我。 |
| SEQUENCER | `Sequencer? Me? I only just got here. I don't even know what that is.` | 码序使？您是说我吗？我并不知道自己是不是码序使，我是刚来的，并不熟悉这里。 |
| OLD MAN | `You've felt it, haven't you. The Anomaly under your feet, when you stand on the Altar. That's what this place is. The Altar. Only a Sequencer can call the Anomaly. I can see it on you, clear as day. You just don't know your own hands yet.` | 想必你注意到了你站在圣坛上的时候脚下有时会出现异象吧？没错你现在站着的位置就叫圣坛，只有码序使才有能力触发这种异象，我现在就能清晰看到，只是你现在不太熟悉你的能力。 |
| SEQUENCER | `I don't understand.` | 我不太理解...... |
| OLD MAN | `I didn't either, at first. I was like you. But my predecessor told me one thing: a Sequencer only survives by finishing the rite.` | 我开始的时候其实也和你一样并不知道自己是码序使，但是听我的前辈说，码序者只有真正地完成圣坛的仪式我们才能存活下去。 |
| SEQUENCER | `...` | ...... |
| OLD MAN | `You saw me drive off those two red ones. They used to be Sequencers. They got taken. I don't know who went first. All I know is they hate this place now — they tear up the Dark on the Altar, and when there's no Dark left, they come for whoever can still make it.` | 你刚刚应该也看到我驱逐的那两个红色怪物了吧？其实他们原来都是这里的码序使，但是他们最终被红色怪物同化了，最初是谁先变成红色怪物的我也不知道，只知道他们很憎恨这个世界，所以会疯狂地破坏圣坛上的黑域，如果黑羽不存在了他们就会疯狂攻击能制造黑域的码序使，他们真的很可怕，像得了失心疯。 |
| SEQUENCER | `Will that happen to us? What do we do?` | 我们最后也会变成他们那样吗？那我们该怎么办？ |
| OLD MAN | `Finish the rite. That's all I know. I never managed it. I meant to do it with you — but I can barely call the Anomaly anymore. The writing I still remember, but I can't see what to write. I don't know why.` | 只能试着完成祭坛的仪式了，我到目前都没能成功。我本来想和你一起完成仪式的，但是我发现我现在几乎召唤不出异象了——写我还记得，却再也看不见该往哪里写。我也不知道为什么。 |
| OLD MAN | `Anyway. I chased them off. They'll be back. It's yours now — you've got something in you. I'll go look outside, see if there's anything left that can help us.` | 总之刚刚红色怪物被我赶跑了，不过他们等会应该还会来。这里就先交给你了，我看你气场很强大，我去外面找一下看看有没有什么东西可以帮助我们复原圣坛。 |
| SEQUENCER | `Me?` | 我？ |
| OLD MAN | `Trust it. A Sequencer can hold off the erosion. Every part of the rite you finish, the Altar shields you for a while.` | 相信自己，码序者都有抵抗怪物侵蚀的能力，你每完成圣坛的仪式的一部分，圣坛就会保护你一段时间。 |
| SEQUENCER | `...All right.` | 好吧。 |

### 5.2 对话二 · 坛外呼喊（老者疑惑，走近再按 T 才开始）

| 说话人 | 英文 | 中文原文 |
| --- | --- | --- |
| SEQUENCER | `Excuse me — where is this? And what were those two red things?` | 您好，请问这里是哪里？还有那两个红色生物是什么啊？ |
| OLD MAN | `I can't tell you. I haven't been here long myself. Doesn't look like anywhere meant for living. Those two keep tearing up the Dark I make. One of them came at me, so I drove them off. Maybe they saw you.` | 我也没法给你一个确定的答案，因为我也没有在这生活很久，这里看起来也不像是一个适合居住的地方。那两个怪物总是破坏我制造的黑域，甚至还会攻击我，于是我把他们赶走了。也许是它们看到你在吧。 |
| OLD MAN | `...Who are you?` | 话说你是？ |
| SEQUENCER | `I don't know. I don't know my own name. I only know something strange happens here — under my feet, sometimes.` | 我也不知道我是谁，我只知道这里发生的事情很奇怪，我脚下有时居然会出现一些奇怪现象。 |
| OLD MAN | `The Dark? Do you get the Anomaly, when you stand on the Altar?` | 你说的是黑域吗？你是不是在这个圣坛上有时会出现一些异象？ |
| SEQUENCER | `I don't know what that means. But it sounds... close.` | 我不明白，但是好像和你说的有一点像。 |
| OLD MAN | `Then you're a Sequencer. That's why they ran from you and not from me.` | 那你就是码序使没错了，难怪刚刚那两个怪物不攻击我只管溜走了。 |
| SEQUENCER | `I don't understand.` | 我不理解...... |

> **从这里开始，接着走对话一里 **`OLD MAN: I didn't either, at first...`** 那一句，之后完全一样。**
> 两条支线在这里汇合，不要在汇合点重复内容。

### 5.3 老者离开前最后一句（标记点 14）

| 说话人 | 英文 | 中文原文 |
| --- | --- | --- |
| OLD MAN | `One more thing. It's not only the red ones out here — I've heard there are other lost ones. Watch yourself. I'll come back as soon as I can. If I can.` | 对了，这里不止有红色生物，听说还有别的失心疯，你注意保护自己，我会尽快赶回来，如果我能的话...... |

> 最后那句 `If I can.` 单独一行显示，停 1 秒，然后老者离开。
> 这是第一幕唯一一次「他可能不会回来」的暗示，不要加任何解释。

---

## 6. 道具说明（拾取后显示）

| 道具 | 英文 | 中文原文 |
| --- | --- | --- |
| 背包 | `BAG — you can carry what you find.` | 背包 |
| 地图 | `MAP — out past the edge. A second altar, still holding a code.` | 地图 |

> 地图是第一幕收尾的**纯收藏品**（不绑按键），那句只负责埋「第二圣坛」的位置线索，不提示怎么涂格。

---

## 7. 结尾字幕

| 时机 | 英文 |
| --- | --- |
| 第一幕结束 | `ACT 1 — END` |

> 按现有的规矩：短提示全大写。第一幕结束这种大标题保持全大写是对的。

---

## 8. 实现提醒

1. **一条台词一行，不要自动换行**，宽度交给渲染层去折行
2. 对话里 `...` 是**沉默**，不是省略号，显示时不要合并到上一句
3. 说话人名固定两个：`OLD MAN` / `SEQUENCER`，**不要给玩家角色起名字**
4. 所有文本只出现在这一个文件里，别散落在 `game.py` 或 `ui.py` 中
