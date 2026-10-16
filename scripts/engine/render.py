# -*- coding: utf-8 -*-
"""帧渲染器：scene 函数 + 烧录字幕 + 口误字幕 + 颤动窗口 + 母题扫描。
  python3 render.py info                 帧数/总长
  python3 render.py still 3.5 12 ...     导出静帧到 qa/s_<t>.png
  python3 render.py chunk f0 f1 out.mp4  渲染一段帧（render_all.sh 并行调用）
  python3 render.py scan                 扫描所有 register_door 母题出现时刻 → motifs.json
"""
import sys, os, json, subprocess, time, importlib
import ink
from ink import *
import figs, config as C
from timeline import build
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
SCENES, LINES, MK, TOTAL = build()
NFR = int(round(TOTAL * FPS))
MODS = [importlib.import_module(m) for m in C.SCENE_MODULES]
def scene_fn(sid):
    for m in MODS:
        f = getattr(m, 'scene_' + sid, None)
        if f: return f
    return None
def scene_at(t):
    for s in SCENES:
        if s['start'] <= t < s['end']: return s
    return SCENES[-1]

# ---------------- 字幕：按标点切块，每块≤SUB_MAXC字，按字数比例分配时长 ----------------
BREAKS = '，。；：？！'
def quotes(s):
    out = []; o = True
    for ch in s:
        if ch == '"': out.append('“' if o else '”'); o = not o
        else: out.append(ch)
    return ''.join(out)
def chunks(s, maxc=C.SUB_MAXC):
    s = quotes(s); parts = []; cur = ''; i = 0; toks = []
    while i < len(s):
        if s[i:i + 2] in ('——', '……'): toks.append(s[i:i + 2]); i += 2
        else: toks.append(s[i]); i += 1
    for tk in toks:
        cur += tk
        if tk in BREAKS or tk == '——': parts.append(cur); cur = ''
    if cur: parts.append(cur)
    out = []; buf = ''
    for p in parts:
        if len(buf) + len(p) <= maxc: buf += p
        else:
            if buf: out.append(buf)
            buf = p
    if buf: out.append(buf)
    return out
def clean(c): return c.rstrip('。，；')
SUB_OFF = [(s['start'], s['end']) for s in SCENES if s['opts'].get('nosubs')]
def sub_state(t):
    for k, l in enumerate(LINES):
        nxt = LINES[k + 1]['start'] if k + 1 < len(LINES) else 1e9
        end = min(l['end'] + C.SUB_TAIL, nxt)
        if l['start'] <= t < end:
            if l['opts'].get('nosub'): return None
            ch = chunks(l['text']); n = sum(len(c) for c in ch)
            dur = l['end'] - l['start']; acc = 0; idx = len(ch) - 1
            for i, c in enumerate(ch):
                acc += len(c)
                if t < l['start'] + dur * acc / n: idx = i; break
            s = ch[idx]; slip = False; sl = l['opts'].get('slip')
            if sl:
                alt = chunks(sl['alt'])
                active = True if sl.get('hold') else (l['start'] + sl['at'] <= t < l['start'] + sl['at'] + sl['frames'] / FPS)
                if active: s = alt[min(idx, len(alt) - 1)]; slip = (s != ch[idx])
            return clean(s), slip
    return None
def draw_sub_text(ctx, s, alpha=1.0, y=C.SUB_Y):
    text_halo(ctx, s, W / 2, y, C.SUB_SIZE, FONT_SANS, (0.1, 0.085, 0.075), alpha, halo=(0.96, 0.93, 0.86), hr=4)
def draw_subs(ctx, t):
    for a, b in SUB_OFF:
        if a <= t < b: return
    st = sub_state(t)
    if st: draw_sub_text(ctx, st[0])

# ---------------- 颤动：默认静止，只在 wob=True 的句子（+可选额外窗口）沸腾 ----------------
WOB_EXTRA = []   # [(t0,t1)] 例如片尾开门
def _wob_windows():
    win = [(l['start'] - 0.1, l['end'] + 1.2) for l in LINES if l['opts'].get('wob')]
    return sorted(win + WOB_EXTRA)
WOB_WIN = _wob_windows()
def wob_at(t):
    v = 0.0
    for a, b in WOB_WIN:
        if a - 0.3 <= t <= b + 0.5: v = max(v, fade(t, a - 0.25, a + 0.1, b - 0.35, b + 0.25))
    return v

# ---------------- frame ----------------
def render_frame(t, scale=1.0, subs=True):
    saved = list(ink.DOOR_LOG); ink.DOOR_LOG.clear()
    surf, ctx = new_frame_surface(scale)
    ink.WOB[0] = wob_at(t)
    s = scene_at(t); f = scene_fn(s['id'])
    ctx.save()
    if f: f(ctx, t)
    else: paper(ctx, t); text(ctx, s['id'], 960, 400, 80, color=GREY)
    ctx.restore()
    if subs: draw_subs(ctx, t)
    log = list(ink.DOOR_LOG); ink.DOOR_LOG[:] = saved
    return surf, log
figs.RENDER.update(f=render_frame, sub_state=sub_state, draw_sub_text=draw_sub_text, scene_at=scene_at, scene_fn=scene_fn, draw_subs=draw_subs)

def render_range(f0, f1, out):
    cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr0', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', str(C.MASTER_CRF), '-pix_fmt', 'yuv420p', '-g', '60', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); t0 = time.time()
    for fi in range(f0, f1):
        surf, _ = render_frame(fi / FPS); surf.flush(); p.stdin.write(surf.get_data())
        if (fi - f0) % 300 == 0: print(f'[{out}] {fi - f0}/{f1 - f0} {time.time() - t0:.0f}s', flush=True)
    p.stdin.close(); p.wait()

def scan(step=2):
    hits = {}
    for fi in range(0, NFR, step):
        t = fi / FPS; _, log = render_frame(t, scale=0.25)
        for tag, bb in log: hits.setdefault(tag, []).append(t)
    out = {}
    for tag, h in hits.items():
        segs = []; cur = [h[0]]
        for a, b in zip(h, h[1:]):
            if b - a > step / FPS * 1.6: segs.append(cur); cur = [b]
            else: cur.append(b)
        segs.append(cur); out[tag] = [dict(start=s[0], end=s[-1] + step / FPS) for s in segs]
    json.dump(out, open('motifs.json', 'w'), indent=1); return out

if __name__ == '__main__':
    mode = sys.argv[1]; os.makedirs('qa', exist_ok=True); os.makedirs('out', exist_ok=True)
    if mode == 'still':
        for a in sys.argv[2:]:
            t = float(a); surf, log = render_frame(t); fn = f'qa/s_{t:07.2f}.png'; surf.write_to_png(fn); print(fn, log)
    elif mode == 'scan':
        for k, v in scan().items(): print(k, [(round(s['start'], 2), round(s['end'], 2)) for s in v])
    elif mode == 'chunk':
        render_range(int(sys.argv[2]), min(int(sys.argv[3]), NFR), sys.argv[4])
    elif mode == 'info':
        print(NFR, TOTAL)
