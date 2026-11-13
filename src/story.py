# -*- coding: utf-8 -*-
"""DATA SHIFT —— 第一幕全部文本。

**唯一来源**：`D:/Al_WorkPlace/WorrkBuddy_WorkPlace/游戏设计方案/DATA_SHIFT_第一幕英文文案.md`。
这里是从那份文件**逐字抄下来**的：不要改写、不要翻译、不要新增台词、不要给角色起名字。
要改文案，先改那份文件，再同步这里。

译名（定死）：Sequencer / the Altar / the Dark / the Anomaly / the grey / a stain /
the plain / the old man / the red ones / erosion。
"""

# ==== 0. 幕 ====

ACT_TITLE = "ACT 1 \u2014 END"
ACT2_TITLE = "ACT 2 \u2014 END"
ACT3_TITLE = "ACT 3 \u2014 END"

# ==== 1. 系统提示（全大写，只留按键 / 道具 / 行动指令）====

TUTORIAL_MOVE = "[W] UP    [S] DOWN    [A] LEFT    [D] RIGHT"
TUTORIAL_SHIFT = "TRY [SHIFT]"
PROMPT_CALL = "PRESS [T] TO CALL OUT"
PROMPT_PICK = "PRESS [B] TO PICK UP"
HINT_CLEAR = "[K] TO CLEAR IT."            # 第一次涂脏格时教 K（从旧 STAIN_WARNING 拆出，按键相关保留）
STEP_INTO_ALTAR = "STEP INTO THE ALTAR"
MAP_IN_HANDS = "FOLD THE MAP FIRST   [M]"  # 地图摊开时想涂：双手捧着纸（2026-11-12 作者要求）
HINT_FORMAT_BROKEN = "A LINE IS BROKEN.  [J] TO PUT IT BACK"   # 第三幕：老者写的格式格被吃掉
HINT_HELP_OLDMAN = "[H] TO HELP HIM"                     # 第三幕：老者倒下，按住 H 四秒救他
HINT_FILL_REST = "%d LEFT.  FILL THEM."                      # 第三幕：格式写完但整张码还差格
HINT_FORMAT_HOLD = "FORMAT CELLS:  HOLD [J]"                 # 第三幕：格式格要按住才写得动（2026-11-13）

# ==== 2. 内心独白（不打断操作）====
# 2026-11-12：原「叙事型系统提示」都搬到这里，变成码序使的嘀咕（增强代入感）。
# 除了上面那几条按键 / 道具 / 行动指令，别再用全大写系统提示「念」这些。

M1 = "Who am I?\nWhere is this?"
M2 = "Why do I feel the pattern under the floor... moving?"
M3 = "Why you two?"
M4 = "What is this? It looks like the things the old man drove off. It's not moving."
M5 = "These tools are dead. What were they for?"

# 这些是「从系统提示改成心声」的嘀咕（2026-11-12 作者要求），正常大小写：
MONO_STAIN = "That one failed. It's just a stain."          # 涂错成脏格
MONO_BLIND = "I can't see it. I should look first."          # 没照出灰域就落笔
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
              "but I can barely call the Anomaly anymore. I don't know why."),
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
ITEM_MAP = "MAP \u2014 everything you have looked at stays on it."
ITEM_SWORD = "SWORD \u2014 it was waiting in the light."   # 第二幕结束的奖励（来源待作者定）


def branch(on_altar):
    """坛内呼喊 → 对话一；坛外呼喊 → 对话二 + 汇合点之后的对话一。"""
    if on_altar:
        return list(DIALOG_ONE)
    return list(DIALOG_TWO) + list(DIALOG_ONE[MERGE_INDEX:])


# ==== 第二幕（2026-11-11 新增，草稿见 DATA_SHIFT_第二幕英文文案.md）====
# 第二幕没有对话：老者没回来，场上没有第二个人。紫怪也不说话。

A2_M1 = ("The old man hasn't come back.\nThe three corners are still here.\n"
         "Something between them is missing.")
A2_M2 = "Two lines.\nThey run between the corners.\nI never looked there."
A2_M3 = "That's not one of the red ones.\nIt's slower. It's looking at the lines."
A2_M4 = "It didn't take one cell.\nIt took the whole line."



# ==== 第三幕（2026-11-12 新增，草稿见 DATA_SHIFT_第三幕英文文案.md）====
# 老者回来了，带回「怎么读这张码」，替码序使写格式信息；追兵（黄怪，M2）随后就到。

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
    (OLD_MAN, "Yellow ones. They were on the old Altar when I got there. They think we stole it. "
              "Maybe we did."),
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
A3_READ = "That\u2019s the reading. The rest is yours."             # 格式信息写完：剩下的归玩家


def act_title(act):
    """第 N 幕的结束字幕。"""
    if act >= 3:
        return ACT3_TITLE
    return ACT2_TITLE if act >= 2 else ACT_TITLE
