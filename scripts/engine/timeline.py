# -*- coding: utf-8 -*-
"""实测配音时长 → 全片时间轴。画面一律跟着配音走，不手填秒数。"""
import json, functools, os
from story import SCENES
from ink import FPS
HERE = os.path.dirname(os.path.abspath(__file__))
@functools.lru_cache(None)
def build():
    dur = json.load(open(os.path.join(HERE, 'tts', 'durations.json')))
    t = 0.0; scenes = []; lines = []; marks = {}
    for s in SCENES:
        st = t
        for b in s['beats']:
            if b[0] == 'p': t += b[1]
            elif b[0] == 'l':
                d = dur[b[1]]
                lines.append(dict(id=b[1], text=b[2], start=t, end=t + d, opts=b[3], scene=s['id']))
                marks[b[1]] = (t, t + d); t += d
            elif b[0] == 'm': marks[b[1]] = (t, t)
        scenes.append(dict(id=s['id'], start=st, end=t, opts={k: v for k, v in s.items() if k not in ('id', 'beats')}))
    total = round(t * FPS) / FPS
    return scenes, lines, marks, total
if __name__ == '__main__':
    sc, li, mk, tot = build()
    for s in sc: print(f"{s['id']:10s} {s['start']:7.2f} {s['end']:7.2f} {s['end']-s['start']:6.2f}")
    for l in li: print(f"  {l['id']:6s} {l['start']:7.2f}–{l['end']:7.2f} {l['text']}")
    print('total', tot)
