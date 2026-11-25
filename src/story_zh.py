# -*- coding: utf-8 -*-
"""中文译文表（`lang.T` 唯一查表的地方）。

两本字典：
  · `ZH` —— 整句映射，key 是 **story.py / ui.py 里的英文原句**（逐字，含空格与破折号）；
  · `TPL` —— 含 `%` 的模板。状态里存的是已经格式化好的英文（如 `TIME 01:23`），
    `lang.T()` 会反向匹配这些模板再把数字塞进译文。

维护约定：
  · 译名沿用 story.py 顶部：码序使 / 圣坛 / 黑域 / 异象 / 灰域 / 脏格 / 平地 / 老者 / 红怪 / 侵蚀；
  · 键帽（`[J]`、`WASD`）与 URL 保持原样，只翻能读的英文；
  · 语气跟英文一致：短句、不解释、不煽情；
  · 新增英文文案必须同时补这里，`tests/_verify_i18n.py` 会逐条查。
"""

ZH = {
    # ==== 幕标题 ====
    "ACT 1 \u2014 END": "第一幕 \u2014 结束",
    "ACT 2 \u2014 END": "第二幕 \u2014 结束",
    "ACT 3 \u2014 END": "第三幕 \u2014 结束",
    "ACT 4 \u2014 END": "第四幕 \u2014 结束",
    "ACT 5 \u2014 END": "第五幕 \u2014 结束",

    # ==== 操作提示（全大写指令） ====
    "[W] UP    [S] DOWN    [A] LEFT    [D] RIGHT": "[W] 上    [S] 下    [A] 左    [D] 右",
    "TRY [SHIFT]": "试试 [SHIFT]",
    "PRESS [T] TO CALL OUT": "按 [T] 呼喊",
    "PRESS [J] TO WRITE HERE": "按 [J] 在这里写",
    "PRESS [B] TO PICK UP": "按 [B] 拾取",
    "[K] TO CLEAR IT.": "按 [K] 清掉它。",
    "STEP INTO THE ALTAR": "走进圣坛",
    "A LINE IS BROKEN.  [J] TO PUT IT BACK": "一条线断了。按住 [J] 补回去",
    "[H] TO HELP HIM": "按住 [H] 帮他",
    "FORMAT CELLS:  HOLD [J]": "格式格：按住 [J]",
    "PRESS [B] TO TAKE THE THREAD": "按 [B] 拿起界丝",
    "BAG FULL.  NO ROOM FOR THE THREAD.": "背包满了。放不下界丝。",
    "NO THREAD.  WAIT FOR THE ALTAR.": "没有界丝。等圣坛再长一根。",
    "[I] TO SPAN THE GAP": "按住 [I] 搭桥过裂缝",
    "HOLD [J] TO SWEEP \u2014 THE GREY, NOT THE BLIND": "按住 [J] 扫灰域\u2014\u2014只扫照到的，别碰盲格",
    "[E] TO HOLD THEM STILL": "按 [E] 定住它们",
    "[Q] TO DASH": "按 [Q] 冲刺",
    "[F] TO LAY A DECOY": "按 [F] 放诱饵",
    "[G] TO PULL A SLAB BACK": "按 [G] 拉回石板",

    # ==== 内心独白 ====
    "Who am I?\nWhere is this?": "我是谁？\n这里是什么地方？",
    "Why do I feel the pattern under the floor... moving?": "为什么我觉得地板下的图案……在动？",
    "Why you two?": "为什么是你们两个？",
    "One corner holds.\nIt pushed them back.": "守住了一个角。\n它们被推回去了。",
    "The edge is whole again.": "边缘又完整了。",
    ("The Anomaly shows three finder squares and one fixed dark dot. Restore them all.\n"
     "Restore a slab, and it joins to the next \u2014 only a whole slab opens the way."):
        "异象照出三个定位方块和一个固定黑点。把它们全部复原。\n"
        "复原一块石板，它就会接上下一块\u2014\u2014只有完整的石板才能开路。",
    "That one failed. It's just a stain.": "那一格废了。只是一块脏格。",
    "That one held.": "那一格成了。",
    "I can't see it. I should look first.": "我看不见。该先看清楚。",
    "Nothing here yet.": "这里还什么都没有。",
    "They're coming back.": "它们又来了。",
    "Something else is moving.": "有别的东西在动。",
    "Agh! It bit me.": "啊！它咬我。",
    "Too many stains... it's taking a toll.": "脏格太多了……在耗我。",
    "So it wants me instead.": "所以它冲我来了。",

    # ==== 红怪狠话 ====
    "WE WILL BE BACK FOR BOTH OF YOU.": "我们会回来找你们两个。",

    # ==== 说话人 ====
    "OLD MAN": "老者",
    "SEQUENCER": "码序使",

    # ==== 对话一（坛内呼喊，13 句） ====
    ("You\u2014 you're a Sequencer, aren't you? I've waited so long. These creatures are a "
     "plague. They ruin my work, and sometimes they come for me."):
        "你\u2014\u2014你是码序使，对吧？我等了太久了。这些东西是场瘟疫。它们毁我写的东西，有时也冲我来。",
    "Sequencer? Me? I only just got here. I don't even know what that is.":
        "码序使？我？我才刚到这里。我连那是什么都不知道。",
    ("You've felt it, haven't you. The Anomaly under your feet, when you stand on the Altar. "
     "That's what this place is. The Altar. Only a Sequencer can call the Anomaly. I can see it "
     "on you, clear as day. You just don't know your own hands yet."):
        "你已经感觉到了，对吧。站在圣坛上的时候，脚下的异象。这地方就是圣坛。"
        "只有码序使能唤出异象。我看得清清楚楚，就在你身上。你只是还没认识自己的手。",
    "I don't understand.": "我不明白。",
    ("I didn't either, at first. I was like you. But my predecessor told me one thing: a "
     "Sequencer only survives by finishing the rite."):
        "我一开始也不明白。我也像你一样。但我之前的那个码序使只告诉了我一件事："
        "码序使只有把仪式做完才能活下来。",
    "...": "……",
    ("You saw me drive off those two red ones. They used to be Sequencers. They got taken. I "
     "don't know who went first. All I know is they hate this place now \u2014 they tear up the "
     "Dark on the Altar, and when there's no Dark left, they come for whoever can still make it."):
        "你看见我把那两只红怪赶走了。它们以前也是码序使。它们被夺走了。我不知道谁先变的。"
        "我只知道它们现在恨这地方\u2014\u2014它们撕掉圣坛上的黑域，黑域没了，"
        "就来咬还能写出黑域的人。",
    "Will that happen to us? What do we do?": "我们也会变成那样吗？我们该怎么办？",
    ("Finish the rite. That's all I know. I never managed it. I meant to do it with you \u2014 "
     "but I can barely call the Anomaly anymore. The writing I still remember, but I can't see "
     "what to write. I don't know why."):
        "把仪式做完。我只知道这个。我从没做成过。我本来想和你一起做\u2014\u2014"
        "可我已经几乎唤不出异象了。字我还记得怎么写，却看不见该写哪儿。我不知道为什么。",
    ("Anyway. I chased them off. They'll be back. It's yours now \u2014 you've got something in "
     "you. I'll go look outside, see if there's anything left that can help us."):
        "总之。我把它们赶走了。它们还会回来。现在轮到你了\u2014\u2014你身上有点东西。"
        "我去外面找找，看还有没有能帮上我们的。",
    "Me?": "我？",
    ("Trust it. A Sequencer can hold off the erosion. Every part of the rite you finish, the "
     "Altar shields you for a while."):
        "相信它。码序使挡得住侵蚀。仪式每完成一部分，圣坛就会护你一阵。",
    "...All right.": "……好吧。",

    # ==== 对话二（坛外呼喊，前 8 句） ====
    "Excuse me \u2014 where is this? And what were those two red things?":
        "打扰一下\u2014\u2014这里是哪儿？那两只红色的东西又是什么？",
    ("I can't tell you. I haven't been here long myself. Doesn't look like anywhere meant for "
     "living. Those two keep tearing up the Dark I make. One of them came at me, so I drove them "
     "off. Maybe they saw you."):
        "我说不上来。我自己也没来多久。这儿不像个能住人的地方。那两只一直撕我写下的黑域。"
        "有一只朝我扑过来，我就把它们赶走了。也许它们看见你了。",
    "...Who are you?": "……你是谁？",
    ("I don't know. I don't know my own name. I only know something strange happens here \u2014 "
     "under my feet, sometimes."):
        "我不知道。我连自己的名字都不知道。我只知道这里有怪事\u2014\u2014有时候，在脚底下。",
    "The Dark? Do you get the Anomaly, when you stand on the Altar?":
        "黑域？你站上圣坛的时候，能看见异象吗？",
    "I don't know what that means. But it sounds... close.":
        "我不知道那是什么意思。但听起来……很接近。",
    "Then you're a Sequencer. That's why they ran from you and not from me.":
        "那你就是码序使。所以它们躲的是你，不是我。",

    # ==== 老者离开前最后一句 ====
    ("One more thing. It's not only the red ones out here \u2014 I've heard there are other lost "
     "ones. Watch yourself. I'll come back as soon as I can.\nIf I can."):
        "还有一件事。外面不只有红怪\u2014\u2014我听说还有别的迷失者。当心点。"
        "我会尽快回来。\n如果我能回来。",

    # ==== 道具说明 ====
    "BAG \u2014 you can carry what you find.": "背包\u2014\u2014捡到的东西可以带着走。",
    "MAP \u2014 out past the edge. A second altar, still holding a code.":
        "地图\u2014\u2014边缘之外。另一座圣坛，还留着一张码。",
    "SWORD \u2014 the last Sequencer left it. He never finished.":
        "剑\u2014\u2014上一个码序使留下的。他没做完。",

    # ==== 第二幕 ====
    ("The old man hasn't come back.\nThe three corners are still here.\n"
     "Something between them is missing."):
        "老者没有回来。\n三个角还在。\n它们之间缺了什么。",
    "Two lines.\nThey run between the corners.\nI never looked there.":
        "两条线。\n它们连在角与角之间。\n我从没往那儿看过。",
    "That one's green.\nIt eats a whole patch.": "那只是绿的。\n它一口吃掉一整片。",
    ("The altar grew a thread.\n"
     "One at a time, on the dark dot."):
        "圣坛长出一根丝。\n一次一根，长在固定的黑点上。",
    ("It's the altar's own material.\n"
     "It knows it's broken.\n"
     "I can pull it across a gap."):
        "这是圣坛自己的料。\n圣坛知道自己裂了。\n我能把它拉过裂缝。",
    "It won't hold long.": "它撑不了多久。",
    "I can make the pattern hold them still.": "我能用这张图案定住它们。",
    "I can cross the lines in one step.": "我能一步跨过那些线。",
    "A false cell. Let them chase it.": "一个假格子。让它们去追它。",
    "One loose slab. I can pull it back.": "一块松动的石板。我能把它拉回来。",

    # ==== 觉醒横幅 / 教学标签 ====
    "TIME SLOW": "时停",
    "DASH": "冲刺",
    "DECOY": "诱饵",
    "PULL BACK": "拉回",
    "MOVE": "移动",
    "ANOMALY": "异象",
    "DARK": "黑域",
    "ERASE": "抹除",
    "PICK UP": "拾取",
    "SPAN": "搭桥",
    "SWORD": "剑",
    "HELP": "救助",
    "SWEEP": "扫",
    "HOLD": "按住",

    # ==== 核心 / 第三幕 ====
    "The core broke.\nThat slab is loose.": "核心碎了。\n那块石板松了。",
    "The core holds.\nThe slab is whole again.": "核心守住了。\n石板又完整了。",
    ("He writes without looking down.\nI still can't see the lines."):
        "他写的时候连头都不低。\n我还是看不见那些线。",
    "It's eating what he wrote.": "它在吃他写下的东西。",
    "The corners line up.\nThe rest is only pattern.": "角对齐了。\n剩下的只是图案。",
    ("That one isn't going for the code.\nIt's going for him."):
        "那一只不是冲着码来的。\n它冲他去了。",
    "He's down.\nI have to get to him.": "他倒下了。\n我得过去。",
    "Up. Come on. Up.": "起来。快。起来。",
    "Still here. Keep going.": "我还在。继续。",
    "Ah\u2014 hold on. I lost the line.": "啊\u2014\u2014等等。我把线弄丢了。",
    "That\u2019s the reading. The rest is yours.": "读法就是这个。剩下的归你。",

    # ==== 第三幕对话 ====
    "I found another Altar. Out past the edge. Fallen in \u2014 but the code on it still reads.":
        "我找到另一座圣坛。就在边缘外面。塌了\u2014\u2014可上面的码还读得出来。",
    "You can read it?": "你读得出来？",
    ("Not the code. What reads it. Every code carries a short note telling you how to read the "
     "rest. Two lines, running out from the corners."):
        "不是码本身。是读它的方法。每张码都带着一段短注，告诉你剩下的怎么读。"
        "两条线，从角上伸出来。",
    "I've never seen anything there.": "我从没在那儿看见过什么。",
    ("You wouldn't. It doesn't glow, and the Anomaly won't show it. It took me years to learn "
     "where to look. You've had an hour."):
        "你当然看不见。它不发光，异象也照不出来。我花了好几年才学会往哪儿看。你才只有一小时。",
    "At your speed you'd be at it all night. I'll write it. I know the order.":
        "照你这个速度，得写一整夜。我来写。顺序我记得。",
    "Then what do I do?": "那我做什么？",
    "Keep them off me. And keep what you've already written \u2014 they'll take that too.":
        "别让它们靠近我。还有，守住你已经写下的\u2014\u2014它们连那个也会抢。",
    "Who?": "谁？",
    "Behind me.": "我后面。",
    ("Yellow ones. They guard what's left of the old Altar. I read the half-sentence off it "
     "before it fell \u2014 they've been after me since."):
        "黄怪。它们守着旧圣坛剩下的东西。它塌之前，我从上面读到了半句话\u2014\u2014"
        "从那以后它们就一直追着我。",
    "They're coming.": "它们来了。",
    "They're already here. Don't let them reach the lines.":
        "它们已经到了。别让它们碰到那些线。",

    # ==== 第四幕 ====
    ("He came back.\nHe keeps the frame. I keep the words.\n"
     "The frame is everyone's. The words are only mine."):
        "他回来了。\n他守骨架。我管字。\n骨架是所有人的。字只属于我。",
    "No more stains. I've learned to look first.": "不再有脏格了。我学会了先看清楚。",
    ("That's not one of the red ones.\nIt's slower. It's looking at the lines."):
        "那不是红怪。\n它更慢。它在盯着线。",
    "It didn't take one cell.\nIt took the whole line.": "它拿走的不是一格。\n是一整条。",
    "Almost.\nDon't stop now.": "快了。\n现在别停。",

    # ==== 第五幕 ====
    ("It's not eating the cells.\nIt's eating what they say.\n"
     "Not all of it. Never all of it.\n"
     "If I don't remember in time... it's gone."):
        "它吃的不是格子。\n它吃的是格子里说的话。\n不会全吃掉。从不会全吃掉。\n"
        "如果我没能及时想起来……就没了。",
    "Three blocks.\nThat's all it needs.": "三块。\n它只要这么多。",
    "Enough.\nLet it read.": "够了。\n让它读。",
    "The frame.\nLet him have it.": "骨架。\n交给他。",
    "SCAN IT WITH YOUR PHONE.": "用手机扫它。",

    # ==== 尾声 ====
    "You finished it.\nYou won't be forgotten.": "你把它做完了。\n你不会被忘记。",
    ("Me \u2014 I couldn't keep my own data.\nI'll be forgotten.\n"
     "But not like them. Not one of them."):
        "我\u2014\u2014我留不住自己的数据。\n我会被忘记。\n但不会像它们那样。不会变成它们中的一个。",
    "And you'll remember me.\nSo it's all right.": "而你会记得我。\n那就没关系了。",
    "Goodbye, child.": "再见，孩子。",
    "I'll remember.\nI'll write it down somewhere.": "我会记得。\n我会找个地方把它写下来。",
    "You were here.": "你来过。",

    # ==== 第二圣坛 ====
    ("The map was right.\nA second altar \u2014 his frame is still here.\n"
     "The words are gone."):
        "地图是对的。\n第二座圣坛\u2014\u2014他的骨架还在这儿。\n字没了。",
    "You wrote it down.\nSo I wasn't forgotten.": "你写下来了。\n所以我没有被忘记。",
    "THE END": "终",

    # ==== 标题页 / 键位 ====
    "PRESS ENTER": "按回车",
    "ESC: QUIT      F1: DEBUG": "ESC：退出      F1：调试",
    "CALL": "呼喊",

    # ==== HUD ====
    "HEALTH": "生命",
    "ALTAR II": "第二圣坛",
    "[ESC] MENU": "[ESC] 菜单",
    "FILL": "待补",
    "FRAME": "骨架",
    "ERRORS": "错误",
    "STAINS": "脏格",
    "RED ON FIELD": "场上红怪",
    "PURPLE ON FIELD": "场上紫怪",
    "NO MONSTERS": "场上没有怪",
    "IT READS WHEN IT IS WHOLE": "完整后才能读出",
    "HE'S ON THE FRAME": "他在守骨架",
    "THE FRAME IS BROKEN": "骨架坏了",
    "BAG": "背包",
    "ABILITIES": "技能",
    "MAP": "地图",

    # ==== 常驻键位表 ====
    "[WASD] MOVE   [SHIFT] ANOMALY   [J] DARK   [K] ERASE   [T] CALL":
        "[WASD] 移动   [SHIFT] 异象   [J] 黑域   [K] 抹除   [T] 呼喊",
    "[WASD] MOVE   [SHIFT] ANOMALY   [J] DARK":
        "[WASD] 移动   [SHIFT] 异象   [J] 黑域",
    "[WASD] MOVE   [SHIFT] ANOMALY   [J] DARK   [K] ERASE":
        "[WASD] 移动   [SHIFT] 异象   [J] 黑域   [K] 抹除",
    "[WASD] MOVE   [SHIFT] ANOMALY   HOLD [J] SWEEP   [K] ERASE":
        "[WASD] 移动   [SHIFT] 异象   按住 [J] 扫   [K] 抹除",
    "   [U] SWORD": "   [U] 剑",
    "   [I] BRIDGE": "   [I] 搭桥",
    "   [E] HOLD": "   [E] 时停",
    "   [Q] DASH": "   [Q] 冲刺",
    "   [F] DECOY": "   [F] 诱饵",
    "   [G] PULL": "   [G] 拉回",

    # ==== 覆盖层 / 菜单 ====
    "ENTER": "回车",
    "PAUSED": "已暂停",
    "AWAKENED  ": "觉醒  ",
    "SEQUENCER DOWN": "码序使倒下",
    "THE ALTAR WILL TAKE YOU BACK": "圣坛会把你送回去",
    "CLICK OR PRESS ENTER": "点击或按回车",
    "CONTINUE": "继续",
    "LANGUAGE": "语言",
    "RESTART ACT": "重开本幕",
    "QUIT TO TITLE": "回到标题",
    "[W/S] SELECT    [ENTER] CONFIRM    [ESC] RESUME":
        "[W/S] 选择    [回车] 确认    [ESC] 继续",
    "SOUND ON": "声音开",
    "SOUND OFF": "声音关",
}


# 含 % 的模板：状态里存的是**格式化后**的英文，lang.T() 反向匹配后把数字塞回译文。
TPL = {
    "%d LEFT.  TWO CORNERS.": "还剩 %d 格。两个角。",
    "%d LEFT.  ANOTHER SLAB.": "还剩 %d 格。下一块石板。",
    "%d LEFT.  FILL THEM.": "还剩 %d 格。补完它们。",
    "ERRORS %d / %d \u2014 IT ONLY NEEDS TO READ": "错误 %d / %d\u2014\u2014只要读得出来就行",
    "IT READS AT %d OR LESS": "\u2264 %d 就能读出",
    "IT READS:  %s": "它读出来：%s",
    "TIME %02d:%02d": "时间 %02d:%02d",
    "ACT %d": "第 %d 幕",
}


# 指令式「键帽」：真键名（WASD / SHIFT / J…）原样显示，只有这种要翻
# （教学动画顶部的 HOLD J → 按住 J）。
KEYS = {
    "HOLD J": "按住 J",
}
