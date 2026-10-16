# 配音与读音排雷

## 音色
- edge-tts `zh-CN-YunxiNeural`，rate +0%，pitch -2Hz（原片定稿）。单句可 `rate='-3%'`。
- box 上 edge-tts 旧版本会 403（Sec-MS-GEC 失效）：`pip install --user --break-system-packages -U edge-tts`（7.3.1 可用）。

## 每句必过耳
1. `python3 asr_check.py`：faster-whisper 转写，与稿子比对，`??` 标出可疑句。ASR 只是筛子，同音字它分不出，**最终靠人耳**。
2. 怀疑某词读错时：同一句生成 2–3 个变体（换同音字、调 rate），每个跑 small+medium 两模型 × beam 1/5，统计命中率挑最好的（原片 `cand3.py` 就这样选出 b18）。

## 已踩过的坑
| 词 | 问题 | 解法 |
|---|---|---|
| 凝缩 | 「缩」被读歪 | `say='第一种手法，叫凝蓑：…'`（同音字 蓑 suō），`rate='-3%'`；字幕仍显示「凝缩」 |
| 迭代地 | 「地」作副词助词应读 de，且断句不能断成「迭代/地…」 | 稿子避免歧义断句；必要时 `say=` 写成「迭代的」或改句式，过耳确认 |
| 拾 | 用户认为「拾」不自然 | 换常用字「捡」 |
| 引号 | 送 TTS 前去掉 `"`，否则停顿怪 | `spoken()` 已处理 |
| 「我们……我们」 | 省略号产生的停顿长度不稳 | 过耳；必要时拆成两句加 ('p', x) |

## 常见多音字清单（写稿时就避开或用 say= 指定）
地(de/dì) 得(de/dé/děi) 了(le/liǎo) 着(zhe/zháo/zhuó) 行(xíng/háng) 重(zhòng/chóng) 还(hái/huán) 长(cháng/zhǎng) 为(wèi/wéi) 处(chù/chǔ) 应(yīng/yìng) 便(biàn/pián) 觉(jué/jiào) 发(fā/fà) 数(shù/shǔ) 相(xiāng/xiàng) 中(zhōng/zhòng) 量(liàng/liáng) 调(diào/tiáo) 种(zhǒng/zhòng)
- 「X地+动词」的副词结构最容易被读成 dì，务必过耳。

## 抑扬顿挫
- 用户反馈「抑扬顿挫和停顿都莫名其妙」时，先查是不是硬插的短句（桥接句）导致——单独一句「举个例子。」TTS 语调孤立、像念稿。删掉比调参有效。
- 不要用 SSML 硬加停顿；停顿交给 story.py 的 ('p', x)。
