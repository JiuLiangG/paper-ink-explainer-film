# -*- coding: utf-8 -*-
"""通用画面助手：时间轴取值（ls/le/wt）、分步笔画 sp、气泡、箭头、圈注、卡片。人物/道具画法写在各片自己的 scenes_*.py 里。"""
import math, numpy as np
from ink import *
from timeline import build
_SC, _LI, MK, TOTAL = build()
def L(i): return MK[i]
def ls(i): return MK[i][0]
def le(i): return MK[i][1]
LINES = {l['id']: l for l in _LI}
def wt(i, sub, frac=0.0):
    """approximate time when substring `sub` is spoken inside line i."""
    l = LINES[i]; s = l['text'].replace('"', ''); k = s.find(sub)
    if k < 0: return l['start']
    return l['start'] + (l['end'] - l['start']) * (k + frac * len(sub)) / max(1, len(s))
def sp(p, i, n, overlap=0.0):
    """sub-progress for the i-th of n sequential strokes"""
    return clamp(p * n - i * (1 - overlap))

RENDER = {}  # hook: RENDER['f'](t, scale) -> (surface, doorlog)

def bubble_pts(cx, cy, rx, ry, tail=(-0.55, 1.35), n=240):
    a = np.linspace(0, 2 * math.pi, n)
    pts = np.stack([cx + rx * np.cos(a), cy + ry * np.sin(a)], 1)
    # insert a tail near angle of tail vector
    ang = math.atan2(tail[1], tail[0]); k = int((ang % (2 * math.pi)) / (2 * math.pi) * n)
    tip = np.array([cx + rx * tail[0], cy + ry * tail[1]])
    out = list(pts[:k - 6]) + [tip] + list(pts[k + 6:])
    return np.array(out + [out[0]])

def cloud_pts(cx, cy, rx, ry, bumps=9, n=360):
    a = np.linspace(0, 2 * math.pi, n)
    r = 1 + 0.09 * np.abs(np.sin(a * bumps / 2)) ** 0.5
    return np.stack([cx + rx * r * np.cos(a), cy + ry * r * np.sin(a)], 1)

def arrow(ctx, pts, t, w=2.6, p=1.0, a=1.0, head=16, color=INK):
    pts = np.asarray(pts, float)
    if len(pts) > 2: pts = catmull(pts, 12)
    stroke(ctx, pts, t, w=w, p=p, alpha=a, color=color)
    if p >= 0.98:
        q = resample(pts, 3); d = q[-1] - q[-4]; d /= (np.linalg.norm(d) + 1e-9); n = np.array([-d[1], d[0]])
        tip = q[-1]
        stroke(ctx, np.array([tip - d * head + n * head * 0.55, tip]), t, w=w, alpha=a, color=color, taper=4)
        stroke(ctx, np.array([tip - d * head - n * head * 0.55, tip]), t, w=w, alpha=a, color=color, taper=4)

def circle_mark(ctx, cx, cy, rx, ry, t, p=1.0, w=3.2, a=1.0, color=INK):
    """hand-drawn loose ellipse (overshooting)"""
    pts = ellipse_pts(cx, cy, rx, ry, -2.2, -2.2 + 2 * math.pi * 1.08, 120)
    pts[:, 1] += np.linspace(0, ry * 0.12, len(pts))
    stroke(ctx, pts, t, w=w, p=p, alpha=a, color=color)

def dim(ctx, a, color=PAPER):
    if a <= 0: return
    ctx.save(); ctx.set_source_rgba(*color, a); ctx.paint(); ctx.restore()

def nested(ctx, t_src, rect, alpha=1.0, register=False, subs=False):
    """draw the film's own frame at time t_src into rect=(x,y,w,h) of the current context"""
    import ink as _ink
    x, y, w, h = rect
    ctx.save(); ctx.translate(x, y); ctx.scale(w / W, h / H)
    ctx.rectangle(0, 0, W, H); ctx.clip()
    if alpha < 1: ctx.push_group()
    old = _ink.REG[0]; _ink.REG[0] = register
    sc = RENDER['scene_at'](t_src); f = RENDER['scene_fn'](sc['id'])
    ctx.save(); f(ctx, t_src); ctx.restore()
    if subs: RENDER['draw_subs'](ctx, t_src)
    _ink.REG[0] = old
    if alpha < 1: ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha)
    ctx.restore()

def paint_surface(ctx, surf, x, y, scale=1.0, alpha=1.0, rot=0.0, cx=None, cy=None):
    """paint surface with its top-left at (x,y) scaled; rotate around its centre"""
    w, h = surf.get_width() * scale, surf.get_height() * scale
    ctx.save(); ctx.translate(x + w / 2, y + h / 2); ctx.rotate(rot); ctx.translate(-w / 2, -h / 2); ctx.scale(scale, scale)
    ctx.set_source_surface(surf, 0, 0); ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint_with_alpha(alpha); ctx.restore()

def card(ctx, x, y, w, h, t, a=1.0, shadow=True, lw=2.6):
    if shadow:
        ctx.save(); ctx.set_source_rgba(0, 0, 0, 0.12 * a); ctx.rectangle(x + 8, y + 10, w, h); ctx.fill(); ctx.restore()
    stroke(ctx, rect_pts(x, y, w, h), t, w=lw, alpha=a, closed=True)
