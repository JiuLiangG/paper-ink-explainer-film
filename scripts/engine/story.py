# -*- coding: utf-8 -*-
"""唯一真相源：场景、旁白、停顿、口误字幕、颤动信号。
Beat 类型:
  ('p', secs)                 停顿（画面呼吸），概念块之间 ≈0.95–1.3s
  ('l', id, text, {opts})     旁白句。opts:
        say='送 TTS 的文本'     多音字/误读时用同音字替换，字幕仍显示 text
        rate='-3%' pitch='-2Hz' 单句语速/音高
        slip=dict(alt='字幕错字版', at=秒, frames=10) 快闪口误；或 dict(alt=..., hold=True) 整句持续
        nosub=True             说出但不出字幕
        wob=True               这句期间线条「沸腾」（只给关键时刻！）
        gain=1.0
  ('m', name)                 零长度标记，scene 里用 MK[name]
Scene 选项: nosubs=True  该场景画面自己写字（write_on），压掉底部字幕
"""
SCENES = [
 dict(id='open', beats=[
  ('p', 0.8),
  ('l', 'o01', '有一句话，我们每天都在说。', {}),
  ('p', 0.4),
  ('l', 'o02', '可它真正的意思，藏在说错的地方。', {'slip': dict(alt='可它真正的意思，藏在那扇门后。', at=1.0, frames=10)}),
  ('p', 1.0),
 ]),
 dict(id='close', nosubs=True, beats=[
  ('p', 0.3),
  ('l', 'c01', '你注意到了吗？', {'wob': True}),
  ('p', 6.4),   # 结尾：写字定住→淡出→门渐入→静持→开门推黑→黑场
 ]),
]
