# -*- coding: utf-8 -*-
"""DATA SHIFT —— 第一幕全部文本。

**唯一来源**：`D:/Al_WorkPlace/WorrkBuddy_WorkPlace/游戏机制/DATA_SHIFT_第一幕英文文案.md`。
这里是从那份文件**逐字抄下来**的：不要改写、不要翻译、不要新增台词、不要给角色起名字。
要改文案，先改那份文件，再同步这里。

译名（定死）：Sequencer / the Altar / the Dark / the Anomaly / the grey / a stain /
the plain / the old man / the red ones / erosion。
"""

# ==== 0. 幕 ====

ACT_TITLE = "ACT 1 \u2014 END"

# ==== 1. 系统提示（全大写）====

TUTORIAL_MOVE = "[W] UP    [S] DOWN    [A] LEFT    [D] RIGHT"
TUTORIAL_SHIFT = "TRY [SHIFT]"
PROMPT_CALL = "PRESS [T] TO CALL OUT"
PROMPT_PICK = "PRESS [B] TO PICK UP"
STAIN_WARNING = "THAT IS NOT DARK. IT IS A STAIN.  [K] TO CLEAR IT."
STEP_INTO_ALTAR = "STEP INTO THE ALTAR"
INCOMING = "THEY ARE COMING."

# ==== 2. 内心独白（不打断操作）====

M1 = "Who am I?\nWhere is this?"
M2 = "Why do I feel the pattern under the floor... moving?"
M3 = "Why you two?"
M4 = "What is this? It looks like the things the old man drove off. It's not moving."
M5 = "These tools are dead. What were they for?"

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


def branch(on_altar):
    """坛内呼喊 → 对话一；坛外呼喊 → 对话二 + 汇合点之后的对话一。"""
    if on_altar:
        return list(DIALOG_ONE)
    return list(DIALOG_TWO) + list(DIALOG_ONE[MERGE_INDEX:])


# ==== 旧五关街机版残留：新版不读，留着让旧界面函数不报错（见开工单 §5）====

TITLE = "YOU WAKE UP MID-SENTENCE."
FAIL = "NOT YET READABLE."
UNREADABLE = "FRAGMENT ?? / UNREADABLE"
LEVELS = ({ "key": "01", "name": "SHAPE", "open": "PAINT WHAT LOOKS RIGHT.",
            "trigger": None, "end": "IT LOOKS RIGHT. THAT IS ENOUGH." },)


def level(i):
    return LEVELS[max(0, min(len(LEVELS) - 1, i - 1))]


def label(i):
    it = level(i)
    return "FRAGMENT %s / %s" % (it["key"], it["name"])
