# -*- coding: utf-8 -*-
"""DATA SHIFT —— 第一幕全部文本。

**唯一来源**：`docs/DATA_SHIFT_第一幕英文文案.md`（2026-11-14 从工作区 `游戏设计方案/` 搬进仓库）。
这里是从那份文件**逐字抄下来**的：不要改写、不要翻译、不要新增台词、不要给角色起名字。
要改文案，先改那份文件，再同步这里。

译名（定死）：Sequencer / the Altar / the Dark / the Anomaly / the grey / a stain /
the plain / the old man / the red ones / erosion。
"""

# ==== 0. 幕 ====

ACT_TITLE = "ACT 1 \u2014 END"
ACT2_TITLE = "ACT 2 \u2014 END"
ACT3_TITLE = "ACT 3 \u2014 END"
ACT4_TITLE = "ACT 4 \u2014 END"
ACT5_TITLE = "ACT 5 \u2014 END"

# ==== 1. 系统提示（全大写，只留按键 / 道具 / 行动指令）====

TUTORIAL_MOVE = "[W] UP    [S] DOWN    [A] LEFT    [D] RIGHT"
TUTORIAL_SHIFT = "TRY [SHIFT]"
PROMPT_CALL = "PRESS [T] TO CALL OUT"
PROMPT_WRITE = "PRESS [J] TO WRITE HERE"   # 第一次站在灰域上：J 从来没被教过（2026-11-14 补）
PROMPT_PICK = "PRESS [B] TO PICK UP"
HINT_CLEAR = "[K] TO CLEAR IT."            # 第一次涂脏格时教 K（从旧 STAIN_WARNING 拆出，按键相关保留）
HINT_WAVE2 = "%d LEFT.  TWO CORNERS."      # （旧文案，第一幕改板块制后不再用）
HINT_BOARD = "%d LEFT.  ANOTHER SLAB."     # 合并一块板块后：还剩多少格
STEP_INTO_ALTAR = "STEP INTO THE ALTAR"
HINT_FORMAT_BROKEN = "A LINE IS BROKEN.  [J] TO PUT IT BACK"   # 第三幕：老者写的格式格被吃掉
HINT_HELP_OLDMAN = "[H] TO HELP HIM"                     # 第三幕：老者倒下，按住 H 四秒救他
HINT_FILL_REST = "%d LEFT.  FILL THEM."                      # 第三幕：格式写完但整张码还差格
HINT_FORMAT_HOLD = "FORMAT CELLS:  HOLD [J]"                 # 第三幕：格式格要按住才写得动（2026-11-13）
# 界丝（第二幕起，贯穿始终）
HINT_THREAD_PICK = "PRESS [B] TO TAKE THE THREAD"            # 站到固定黑点旁：拾取界丝
HINT_THREAD_FULL = "BAG FULL.  NO ROOM FOR THE THREAD."      # 背包满：放不下
HINT_THREAD_EMPTY = "NO THREAD.  WAIT FOR THE ALTAR."        # 没界丝：等圣坛生产
HINT_THREAD_CAST = "[I] TO SPAN THE GAP"                     # 站在裂缝旁：搭通道
HINT_SWEEP = "HOLD [J] TO SWEEP \u2014 THE GREY, NOT THE BLIND"   # 第四幕：按住 J 扫灰域，盲格不写
HINT_TOLERANCE = "ERRORS %d / %d \u2014 IT ONLY NEEDS TO READ"      # 第五幕：错误压进容量就能被读出来

# ==== 道具（2026-11-16 作者定：每幕一个新，固定字母键）====
HINT_TIME_SLOW = "[E] TO HOLD THEM STILL"                          # 第二幕：时停
HINT_DASH = "[Q] TO DASH"                                          # 第三幕：冲刺
HINT_DECOY = "[F] TO LAY A DECOY"                                  # 第四幕：诱饵
HINT_SCROLL = "[G] TO PULL A SLAB BACK"                            # 第五幕：修复卷轴

# ==== 2. 内心独白（不打断操作）====
# 2026-11-12：原「叙事型系统提示」都搬到这里，变成码序使的嘀咕（增强代入感）。
# 除了上面那几条按键 / 道具 / 行动指令，别再用全大写系统提示「念」这些。

M1 = "Who am I?\nWhere is this?"
M2 = "Why do I feel the pattern under the floor... moving?"
M3 = "Why you two?"
# 第一幕第一波清完之后的一句（2026-11-14 拆两波）：老者交代过「每写完一部分，圣坛会护你一会儿」
A1_WAVE = "One corner holds.\nIt pushed them back."
A1_MERGE = "The edge is whole again."      # 合并一句（飘字，不冻世界）

# 这些是「从系统提示改成心声」的嘀咕（2026-11-12 作者要求），正常大小写：
MONO_STAIN = "That one failed. It's just a stain."          # 涂错成脏格
MONO_FIRST = "That one held."                                # 第一次涂对（和 MONO_STAIN 对称）
MONO_BLIND = "I can't see it. I should look first."          # 没照出灰域就落笔
MONO_EMPTY = "Nothing here yet."                             # 照了，但这个位置此刻没有可写的东西
MONO_INCOMING = "They're coming back."                       # 红怪来袭（第一幕开战）
MONO_PURPLE_IN = "Something else is moving."                 # 紫怪第一次进场
MONO_HIT = "Agh! It bit me."                                 # 被红怪咬
MONO_STAIN_HURT = "Too many stains... it's taking a toll."   # 脏格超标开始扣血
MONO_PURPLE_HIT = "So it wants me instead."                   # 坛内没黑域，紫怪转来扑人

# ==== 3. 红怪的狠话 ====

THREAT = "WE WILL BE BACK FOR BOTH OF YOU."

# ==== 4. 对话 ====

OLD_MAN = "OLD MAN"
SEQUENCER = "SEQUENCER"

# 5.1 对话一 · 坛内呼喊（13 句）
DIALOG_ONE = [
    (OLD_MAN, "You\u2014 you're a Sequencer, aren't you? I've waited so long. These creatures are a "
              "plague. They ruin my work, and sometimes they come for me."),
    (SEQUENCER, "Sequencer? Me? I only just got here. I don't even know what that is."),
    (OLD_MAN, "You've felt it, haven't you. The Anomaly under your feet, when you stand on the Altar. "
              "That's what this place is. The Altar. Only a Sequencer can call the Anomaly. I can see it "
              "on you, clear as day. You just don't know your own hands yet."),
    (SEQUENCER, "I don't understand."),
    (OLD_MAN, "I didn't either, at first. I was like you. But my predecessor told me one thing: a "
              "Sequencer only survives by finishing the rite."),
    (SEQUENCER, "..."),
    (OLD_MAN, "You saw me drive off those two red ones. They used to be Sequencers. They got taken. I "
              "don't know who went first. All I know is they hate this place now \u2014 they tear up the "
              "Dark on the Altar, and when there's no Dark left, they come for whoever can still make it."),
    (SEQUENCER, "Will that happen to us? What do we do?"),
    (OLD_MAN, "Finish the rite. That's all I know. I never managed it. I meant to do it with you \u2014 "
              "but I can barely call the Anomaly anymore. The writing I still remember, but I can't see "
              "what to write. I don't know why."),
    (OLD_MAN, "Anyway. I chased them off. They'll be back. It's yours now \u2014 you've got something in "
              "you. I'll go look outside, see if there's anything left that can help us."),
    (SEQUENCER, "Me?"),
    (OLD_MAN, "Trust it. A Sequencer can hold off the erosion. Every part of the rite you finish, the "
              "Altar shields you for a while."),
    (SEQUENCER, "...All right."),
]

# 5.2 对话二 · 坛外呼喊（前 8 句，之后汇合到对话一的第 5 句）
DIALOG_TWO = [
    (SEQUENCER, "Excuse me \u2014 where is this? And what were those two red things?"),
    (OLD_MAN, "I can't tell you. I haven't been here long myself. Doesn't look like anywhere meant for "
              "living. Those two keep tearing up the Dark I make. One of them came at me, so I drove them "
              "off. Maybe they saw you."),
    (OLD_MAN, "...Who are you?"),
    (SEQUENCER, "I don't know. I don't know my own name. I only know something strange happens here \u2014 "
                "under my feet, sometimes."),
    (OLD_MAN, "The Dark? Do you get the Anomaly, when you stand on the Altar?"),
    (SEQUENCER, "I don't know what that means. But it sounds... close."),
    (OLD_MAN, "Then you're a Sequencer. That's why they ran from you and not from me."),
    (SEQUENCER, "I don't understand."),
]

# 汇合点：对话一的第 5 句（下标 4，从 `I didn't either, at first...` 开始）
MERGE_INDEX = 4

# 5.3 老者离开前最后一句（`If I can.` 单独一行）
LEAVE_LINE = (OLD_MAN,
              "One more thing. It's not only the red ones out here \u2014 I've heard there are other lost "
              "ones. Watch yourself. I'll come back as soon as I can.\nIf I can.")

# ==== 5. 道具说明（拾取后显示）====

ITEM_BAG = "BAG \u2014 you can carry what you find."
ITEM_SWORD = "SWORD \u2014 the last Sequencer left it. He never finished."   # 第二幕结束的奖励：前任码序使留下（2026-11-18 定）


def branch(on_altar):
    """坛内呼喊 → 对话一；坛外呼喊 → 对话二 + 汇合点之后的对话一。"""
    if on_altar:
        return list(DIALOG_ONE)
    return list(DIALOG_TWO) + list(DIALOG_ONE[MERGE_INDEX:])


# ==== 第二幕（2026-11-11 新增，草稿见 DATA_SHIFT_第二幕英文文案.md）====
# 第二幕没有对话：老者没回来，场上没有第二个人。
# 2026-11-16：紫怪从第二幕延后到第四幕，所以这一幕只剩红怪（咬核心→板块分离），
# 紫怪的登场介绍（A4_PURPLE / A4_M2）挪到第四幕去了。绿怪（清 3×3）在第二幕低频登场。

A2_M1 = ("The old man hasn't come back.\nThe three corners are still here.\n"
         "Something between them is missing.")
A2_M2 = "Two lines.\nThey run between the corners.\nI never looked there."
A2_GREEN = "That one's green.\nIt eats a whole patch."        # 绿怪第一次进场（清 3×3）

# 道具解锁（2026-11-16 作者定：每幕一个新）
A2_TIMESLOW = "I can make the pattern hold them still."       # 第二幕：时停
A3_DASH = "I can cross the lines in one step."                # 第三幕：冲刺
A4_DECOY = "A false cell. Let them chase it."                 # 第四幕：诱饵
A5_SCROLL = "One loose slab. I can pull it back."             # 第五幕：修复卷轴

# 天赋觉醒横幅（2026-11-16：屏幕中央大横幅，比飘字更醒目，不冻世界）
AWAKEN = {
    "timeslow": ("TIME SLOW", "[E]"),
    "dash": ("DASH", "[Q]"),
    "decoy": ("DECOY", "[F]"),
    "scroll": ("PULL BACK", "[G]"),
}

# 按键教学动画（2026-11-20）：键帽文本 + 右侧短标签，画法在 ui.py。
# 元组 = (短标签, 键帽文本)；E/Q/F/G 四技能走觉醒横幅（AWAKEN），不在此列。
TEACH = {
    "move":    ("MOVE",    "WASD"),
    "shift":   ("ANOMALY", "SHIFT"),
    "write":   ("DARK",    "J"),
    "erase":   ("ERASE",   "K"),
    "call":    ("CALL",    "T"),
    "pick":    ("PICK UP", "B"),
    "bridge":  ("SPAN",    "I"),
    "sword":   ("SWORD",   "U"),
    "revive":  ("HELP",    "H"),
    "sweep":   ("SWEEP",   "HOLD J"),
    "holdfmt": ("HOLD",    "HOLD J"),
}

# 核心被破坏 / 修复（2026-11-15 作者定的「核心」机制）
CORE_BROKEN = "The core broke.\nThat slab is loose."          # 板块分离（飘字）
CORE_FIXED = "The core holds.\nThe slab is whole again."      # 补满核心、板块合回（飘字）



# ==== 第三幕（2026-11-12 新增，草稿见 DATA_SHIFT_第三幕英文文案.md）====
# 老者回来了，带回「怎么读这张码」，替码序使写整副骨架（定位+定时+暗模块+格式，2026-11-19 起）；追兵（黄怪，M2）随后就到。
#
# 能力设定（2026-11-15 作者定，解决「他没能力了为什么还能写」的矛盾）：
#   · 「召唤异象（照灰域）」是码序者独有的天赋，也是唯一在衰退的能力
#   · 「写黑域」是照着灰域落笔的机械活，谁都能做
#   · 老者写了几十年，把「召唤异象」的感知力烧到几乎没了 —— 还能写，但看不见该写哪
#   · 所以第三幕他只能写「背得下来的」整副骨架（定位/定时/暗模块/格式都是固定结构，异象照不出来），
#     数据区要现照现写，那是码序使（玩家）的活。第一幕台词已按此埋下伏笔。

DIALOG_THREE = [
    (OLD_MAN, "I found another Altar. Out past the edge. Fallen in \u2014 but the code on it still reads."),
    (SEQUENCER, "You can read it?"),
    (OLD_MAN, "Not the code. What reads it. Every code carries a short note telling you how to read the "
              "rest. Two lines, running out from the corners."),
    (SEQUENCER, "I've never seen anything there."),
    (OLD_MAN, "You wouldn't. It doesn't glow, and the Anomaly won't show it. It took me years to learn "
              "where to look. You've had an hour."),
    (OLD_MAN, "At your speed you'd be at it all night. I'll write it. I know the order."),
    (SEQUENCER, "Then what do I do?"),
    (OLD_MAN, "Keep them off me. And keep what you've already written \u2014 they'll take that too."),
    (SEQUENCER, "Who?"),
    (OLD_MAN, "Behind me."),
    (OLD_MAN, "Yellow ones. They guard what's left of the old Altar. I read the half-sentence off it "
              "before it fell \u2014 they've been after me since."),
    (SEQUENCER, "They're coming."),
    (OLD_MAN, "They're already here. Don't let them reach the lines."),
]

A3_M1 = ("He writes without looking down.\nI still can't see the lines.")
A3_M2 = "It's eating what he wrote."                       # 第一次格式格被怪吃掉
A3_M3 = "The corners line up.\nThe rest is only pattern."  # 清屏前最后一格写完

# 第三幕 M2：黄怪 / 老者倒下与救援
A3_Y1 = "That one isn't going for the code.\nIt's going for him."   # 第一只黄怪进场
A3_DOWN = "He's down.\nI have to get to him."                        # 老者倒下
A3_UP = "Up. Come on. Up."                                           # ⚠️ 暂未使用：救援中说台词会冻住世界，
                                                                  # 反而救不起来（见 Game.update_revive）
A3_UP_MAN = "Still here. Keep going."                              # 他站起来之后自己回一句
A3_STAGGER = "Ah\u2014 hold on. I lost the line."                   # 第一次被咬断（笔停在半空）
A3_READ = "That\u2019s the reading. The rest is yours."             # 整副骨架写完：剩下的归玩家


# ==== 第四幕（2026-11-14 新增）====
# 骨架齐了，剩下的是「内容」：数据区没有结构可讲，只能一格一格填。
# 所以这一幕不引入新角色、不引入新图案 —— 它换的是**动词**（按住 J 扫），
# 文案只负责把「他走了，读法留下来了」和「它不想让我把句子写完」这两句交代清楚。
# 2026-11-16：紫怪从第二幕**延后到这里**首次登场（A4_PURPLE 介绍它），清行的痛感由 A4_M2 接。

A4_M1 = ("He came back.\nHe keeps the frame. I keep the words.\n"
         "The frame is everyone's. The words are only mine.")   # 末行 2026-11-18 补：数据区=专属、骨架=通用
# 第四幕起脏格不再有（2026-11-20）：前三幕「闭眼写=脏格扣血」是教学期的纠错，
# 这一幕换成「扫灰域、盲格跳过」—— 主角已学会先看清再落笔，惩罚自然退场。
# 呼应第一幕 MONO_BLIND「I should look first」，是同一句的成长闭环。
A4_NO_STAIN = "No more stains. I've learned to look first."
A4_PURPLE = "That's not one of the red ones.\nIt's slower. It's looking at the lines."  # 紫怪首次进场
A4_M2 = "It didn't take one cell.\nIt took the whole line."        # 第一次被紫怪清行
A4_M3 = "Almost.\nDon't stop now."                                 # 剩下不到 15 格


# ==== 第五幕（2026-11-14 新增）====
# 码被侵蚀掉几块。玩家第一次知道「这张码允许你错」—— 不是补完，是**够用**。

A5_M1 = ("It's not eating the cells.\nIt's eating what they say.\n"
         "Not all of it. Never all of it.\n"
         "If I don't remember in time... it's gone.")   # 2026-11-18：末行补「侵蚀=我自己的遗忘」
A5_M2 = "Three blocks.\nThat's all it needs."                     # 第一次错误数 ≤ 容量（备用）
A5_M3 = "Enough.\nLet it read."                                   # 进入扫描
A5_FRAME = "The frame.\nLet him have it."                           # 骨架第一次被清坏：他管这一头（只一次）
END_LINE = "IT READS:  %s"                                         # 结局页副标题：把这张码的内容念出来
# 结局页脚注（2026-11-22 新增）：整条彩蛋链的第一跳是「拿手机扫屏幕上这张码」，
# 但游戏里从来没有一个字提过这件事 —— 玩家不一定想得到扫自己的屏幕。
# 这句话只做一件事：让那个动作变得可能被想到。语气保持全大写、不解释。
END_HINT = "SCAN IT WITH YOUR PHONE."

# ==== 第五幕尾声 · 老者消失（2026-11-18 新增）====
# 码读出来了，记录的是码序者。老者记不住自己的数据区，于是「这张码里没有他」——
# 他会消失，但不会变成怪物，因为还有人记得他。这是他最后一段话，逐句推进。
EPILOGUE = [
    "You finished it.\nYou won't be forgotten.",
    "Me \u2014 I couldn't keep my own data.\nI'll be forgotten.\nBut not like them. Not one of them.",
    "And you'll remember me.\nSo it's all right.",
    "Goodbye, child.",
]
# 老者消失后，码序使的收尾独白：回应「你还记得我」，也为「把他也写下来」埋下彩蛋伏笔。
EPILOGUE_LAST = "I'll remember.\nI'll write it down somewhere."
# 全游戏最后一句：这张码 / 这一切，记的是「你来过」—— 主角失忆，码替它记住了它存在过。
# 原主角码内容「YOU WERE HERE」（2026-11-19 已改成 URL），这句情感落点移到独白收尾。
EPILOGUE_FINAL = "You were here."


def act_title(act):
    """第 N 幕的结束字幕。"""
    if act >= 5:
        return ACT5_TITLE
    if act >= 4:
        return ACT4_TITLE
    if act >= 3:
        return ACT3_TITLE
    return ACT2_TITLE if act >= 2 else ACT_TITLE
