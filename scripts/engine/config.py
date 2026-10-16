# -*- coding: utf-8 -*-
"""每部片子只改这里 + story.py + scenes_*.py。"""
TITLE = '示例：纸墨讲解片'
SCENE_MODULES = ['scenes_demo']          # 场景模块，函数名 scene_<id>(ctx, t)
# 配音（edge-tts）。YunxiNeural + pitch -2Hz 是《精神分析的本质》定稿音色
VOICE = 'zh-CN-YunxiNeural'; RATE = '+0%'; PITCH = '-2Hz'
# 字幕
SUB_Y = 1000; SUB_SIZE = 48; SUB_MAXC = 19; SUB_TAIL = 0.35   # 底部安全区 y≈1000，每屏≤19字，句尾多留0.35s
# 混音
TARGET_LUFS = -16.0; PEAK_DBFS = -2.2
# 母带编码（chunk）与分享编码
MASTER_CRF = 19; SHARE_CRF = 23; SHARE_MAXRATE = '1.2M'
