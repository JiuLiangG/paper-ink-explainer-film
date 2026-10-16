# -*- coding: utf-8 -*-
"""Ink-on-paper drawing toolkit (pycairo + numpy + Pillow text)."""
import math, functools, zlib
import numpy as np, cairo
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
# 色板（全片只用这四色；RED 只给母题/重音）
INK = (0.13, 0.11, 0.095)
PAPER = (0.925, 0.886, 0.808)
RED = (0.76, 0.12, 0.14)
GREY = (0.45, 0.42, 0.38)
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
FONT_MED = _os.path.join(_HERE, 'fonts', 'NotoSansSC-Medium.otf')   # 思源黑体 SC Medium = 正文/字幕/写字
FONT_BOLD = _os.path.join(_HERE, 'fonts', 'NotoSansSC-Bold.otf')    # 标题
FONT_KAI = FONT_MED; FONT_KAI_M = FONT_BOLD; FONT_SANS = FONT_MED; FONT_SANS_B = FONT_BOLD; FONT_SERIF = FONT_MED

# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def lin(t, t0, t1): return clamp((t - t0) / (t1 - t0)) if t1 != t0 else float(t >= t1)
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def eio(x): x = clamp(x); return 0.5 - 0.5 * math.cos(math.pi * x)
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def ein(x): x = clamp(x); return x ** 3
def seg(t, t0, t1, f=ease): return f(lin(t, t0, t1))
def mix(a, b, k): return a + (b - a) * k
def fade(t, t0, t1, t2, t3):  # in [t0,t1], hold, out [t2,t3]
    return seg(t, t0, t1) * (1 - seg(t, t2, t3))

# ---------------- paper ----------------
def _paper_array(seed):
    rng = np.random.default_rng(seed)
    def blur_noise(scale, amp):
        h, w = H // scale + 2, W // scale + 2
        n = rng.standard_normal((h, w)).astype(np.float32)
        im = Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        return (np.asarray(im, np.float32) - 128) / 40 * amp
    base = np.zeros((H, W, 3), np.float32)
    base[:] = np.array(PAPER) * 255
    lum = blur_noise(160, 4.0) + blur_noise(40, 2.5) + blur_noise(8, 1.6) + rng.standard_normal((H, W)).astype(np.float32) * 3.2
    # fibres
    fib = Image.new('L', (W, H), 0); d = ImageDraw.Draw(fib)
    for _ in range(260):
        x, y = rng.uniform(0, W), rng.uniform(0, H); a = rng.uniform(0, math.pi); L = rng.uniform(8, 40)
        d.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=int(rng.uniform(20, 60)), width=1)
    fib = np.asarray(fib.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255 * 14
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    vig = (np.clip(r - 0.55, 0, 1) ** 1.6) * 52
    out = base + (lum - fib - vig)[..., None] * np.array([1.0, 0.97, 0.9])
    return out.clip(0, 255).astype(np.uint8)

def _to_surface(rgb):
    h, w, _ = rgb.shape
    a = np.zeros((h, w, 4), np.uint8); a[..., 0] = rgb[..., 2]; a[..., 1] = rgb[..., 1]; a[..., 2] = rgb[..., 0]; a[..., 3] = 255
    s = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
    np.ndarray((h, s.get_stride() // 4, 4), np.uint8, s.get_data())[:, :w] = a
    s.mark_dirty(); return s

@functools.lru_cache(None)
def paper_surface(i):
    return _to_surface(_paper_array(1000 + i))

def paper(ctx, t, rect=None):
    pat = cairo.SurfacePattern(paper_surface(0)); pat.set_extend(cairo.EXTEND_REFLECT)
    ctx.save(); ctx.set_source(pat)
    if rect: ctx.rectangle(*rect); ctx.fill()
    else: ctx.paint()
    ctx.restore()

# ---------------- geometry ----------------
def resample(pts, step=4.0, closed=False):
    p = np.asarray(pts, np.float64)
    if closed: p = np.vstack([p, p[:1]])
    if len(p) < 2: return p
    d = np.sqrt(((p[1:] - p[:-1]) ** 2).sum(1)); s = np.concatenate([[0], np.cumsum(d)]); L = s[-1]
    if L < 1e-6: return p[:1].repeat(2, 0)
    n = max(2, int(L / step) + 1); u = np.linspace(0, L, n)
    return np.stack([np.interp(u, s, p[:, 0]), np.interp(u, s, p[:, 1])], 1)

def resample_n(pts, n, closed=False):
    p = np.asarray(pts, np.float64)
    if closed: p = np.vstack([p, p[:1]])
    d = np.sqrt(((p[1:] - p[:-1]) ** 2).sum(1)); s = np.concatenate([[0], np.cumsum(d)])
    u = np.linspace(0, s[-1], n)
    return np.stack([np.interp(u, s, p[:, 0]), np.interp(u, s, p[:, 1])], 1)

def catmull(ctrl, n=16, closed=False):
    P = [np.array(c, float) for c in ctrl]
    if closed: P = [P[-1]] + P + [P[0], P[1]]
    else: P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out)

def rect_pts(x, y, w, h): return np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]], float)
def ellipse_pts(cx, cy, rx, ry, a0=0, a1=2 * math.pi, n=90):
    a = np.linspace(a0, a1, n); return np.stack([cx + rx * np.cos(a), cy + ry * np.sin(a)], 1)
def line_pts(x0, y0, x1, y1): return np.array([[x0, y0], [x1, y1]], float)

def _key(pts):
    """translation-invariant shape key: a stroke that moves keeps its hand-drawn irregularity (no re-randomising)"""
    p = np.asarray(pts, float)
    ch = p[-1] - p[0]; L = float(np.hypot(*ch))
    b = (len(p), int(round(math.log2(L + 1) * 2)), int(round(math.atan2(ch[1], ch[0]) / 0.6)) if L > 4 else 0)
    return zlib.crc32(np.array(b, np.int32).tobytes()) & 0xffffff

# Wobble ("boil") is a signal, not a texture: 0 = steady line (default); >0 only in meaningful moments.
WOB = [0.0]
WOB_GAIN = 1.6

# ---------------- the brush ----------------
BOIL = 8.0
WSCALE = 1.18
def stroke(ctx, pts, t, w=3.2, p=1.0, color=INK, alpha=0.92, jitter=1.3, seed=None, taper=14.0, closed=False, dry=True, step=4.0):
    """Hand-drawn tapered brush stroke along polyline pts; p = drawn fraction."""
    if p <= 0 or alpha <= 0: return
    w = w * WSCALE
    q = resample(pts, step, closed)
    if len(q) < 2: return
    seed = _key(pts) if seed is None else seed
    wv = WOB[0]
    rng = np.random.default_rng((seed * 131) & 0x7fffffff)
    rngb = np.random.default_rng((seed * 131 + int(t * BOIL) + 1) & 0x7fffffff) if wv > 0.01 else None
    d = np.sqrt(((q[1:] - q[:-1]) ** 2).sum(1)); s = np.concatenate([[0], np.cumsum(d)]); L = s[-1]
    if p < 1:
        m = s <= L * p
        k = int(m.sum())
        if k < 2: return
        q = q[:k]; s = s[:k]
    tan = np.gradient(q, axis=0); nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
    nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9)
    ph = rng.uniform(0, 2 * math.pi, 3); fr = np.array([1.0, 2.7, 6.1]) * (2 * math.pi / max(L, 60))
    wf = lambda P: np.sin(s * fr[0] * 3 + P[0]) * 0.6 + np.sin(s * fr[1] * 5 + P[1]) * 0.3 + np.sin(s * 0.09 + P[2]) * 0.25
    off = jitter * wf(ph)
    if rngb is not None:
        phb = rngb.uniform(0, 2 * math.pi, 3)
        off = (1 - wv) * off + wv * (jitter * (1 + WOB_GAIN * wv) + 1.2 * wv) * wf(phb)
        rng = rngb
    c = q + nrm * off[:, None]
    Lp = s[-1]
    if closed and p >= 1: tp = np.ones_like(s)
    else: tp = np.clip(np.minimum(s / taper, (Lp - s) / (taper * 0.7)), 0.0, 1.0) ** 0.6
    wid = w * (0.25 + 0.75 * tp) * (0.88 + 0.12 * np.sin(s * 0.05 + ph[1]))
    left = c + nrm * (wid / 2)[:, None]; right = c - nrm * (wid / 2)[:, None]
    poly = np.vstack([left, right[::-1]])
    ctx.save(); ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.move_to(*poly[0])
    for x, y in poly[1:]: ctx.line_to(x, y)
    ctx.close_path(); ctx.set_source_rgba(*color, alpha); ctx.fill()
    if dry and w > 1.6:
        ctx.set_line_width(max(0.6, w * 0.22)); ctx.set_source_rgba(*color, alpha * 0.28)
        c2 = c + nrm * (w * 0.55) + rng.normal(0, 0.25, c.shape)
        ctx.move_to(*c2[0])
        for x, y in c2[1:]: ctx.line_to(x, y)
        ctx.stroke()
    ctx.restore()

def fill_poly(ctx, pts, color, alpha=1.0, t=0, jitter=0.8, seed=None):
    q = resample(pts, 6, closed=True)
    seed = _key(pts) if seed is None else seed
    rng = np.random.default_rng((seed * 7) & 0x7fffffff)
    n0 = rng.normal(0, jitter * 0.5, q.shape)
    wv = WOB[0]
    if wv > 0.01:
        rb = np.random.default_rng((seed * 7 + int(t * BOIL) + 1) & 0x7fffffff)
        n0 = (1 - wv) * n0 + wv * rb.normal(0, jitter * 0.5 * (1 + WOB_GAIN * wv) + 0.6 * wv, q.shape)
    q = q + n0
    ctx.move_to(*q[0])
    for x, y in q[1:]: ctx.line_to(x, y)
    ctx.close_path(); ctx.set_source_rgba(*color, alpha); ctx.fill()

def hatch(ctx, x, y, w, h, t, gap=14, angle=-0.6, alpha=0.35, wd=1.4, p=1.0, clip_pts=None):
    ctx.save()
    if clip_pts is not None:
        ctx.move_to(*clip_pts[0])
        for a, b in clip_pts[1:]: ctx.line_to(a, b)
        ctx.close_path(); ctx.clip()
    else:
        ctx.rectangle(x, y, w, h); ctx.clip()
    ca, sa = math.cos(angle), math.sin(angle); R = math.hypot(w, h)
    cx, cy = x + w / 2, y + h / 2
    n = int(R * 2 / gap)
    for i in range(n):
        if (i / n) > p: break
        o = -R + i * gap
        x0, y0 = cx + o * sa * -1 - ca * R, cy + o * ca - sa * R
        x1, y1 = cx + o * sa * -1 + ca * R, cy + o * ca + sa * R
        stroke(ctx, line_pts(x0, y0, x1, y1), t, w=wd, alpha=alpha, jitter=0.8, seed=i * 97 + int(x), taper=30, dry=False, step=8)
    ctx.restore()

# ---------------- text (Pillow -> cairo mask, cached) ----------------
@functools.lru_cache(64)
def _font(path, size): return ImageFont.truetype(path, size)

@functools.lru_cache(4096)
def text_mask(s, size, font=FONT_KAI):
    f = _font(font, int(size))
    l, t_, r, b = f.getbbox(s)
    asc, desc = f.getmetrics()
    pad = int(size * 0.3)
    w = max(1, r - l + pad * 2); h = asc + desc + pad * 2
    im = Image.new('L', (w, h), 0); ImageDraw.Draw(im).text((pad - l, pad), s, font=f, fill=255)
    a = np.asarray(im, np.uint8)
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_A8, w)
    buf = np.zeros((h, stride), np.uint8); buf[:, :w] = a
    surf = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_A8, w, h, stride)
    return surf, w - pad * 2, asc, desc, pad, buf

def text_size(s, size, font=FONT_KAI):
    _, w, asc, desc, pad, _ = text_mask(s, size, font); return w, asc + desc

def text(ctx, s, x, y, size=48, font=FONT_KAI, color=INK, alpha=1.0, align='c', valign='m', rot=0.0, scale=1.0):
    """Draw text; (x,y) anchor; valign m=middle of ascent, b=baseline."""
    if alpha <= 0 or not s: return
    surf, w, asc, desc, pad, _ = text_mask(s, size * 1.0, font)
    ax = {'l': 0, 'c': w / 2, 'r': w}[align]
    ay = {'m': (asc + desc) * 0.55, 'b': asc, 't': 0}[valign]
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(scale, scale)
    ctx.set_source_rgba(*color, alpha)
    ctx.mask_surface(surf, -ax - pad, -ay - pad)
    ctx.restore()
    return w

def text_halo(ctx, s, x, y, size, font, color, alpha, halo=PAPER, hr=5, align='c'):
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-.7, -.7), (.7, .7), (-.7, .7), (.7, -.7)]:
        text(ctx, s, x + dx * hr, y + dy * hr, size, font, halo, alpha * 0.55, align)
    text(ctx, s, x, y, size, font, color, alpha, align)

def write_on(ctx, s, x, y, size, t, t0, dur=None, font=FONT_KAI, color=INK, alpha=1.0, align='c', spacing=1.0, rise=6):
    """Characters appear one by one (hand-written feel)."""
    if t < t0 or alpha <= 0: return
    n = len(s); dur = dur if dur is not None else 0.07 * n + 0.2
    widths = [text_size(ch, size, font)[0] * spacing for ch in s]
    total = sum(widths)
    x0 = {'l': x, 'c': x - total / 2, 'r': x - total}[align]
    cx = x0
    for i, ch in enumerate(s):
        k = seg(t, t0 + dur * i / max(n, 1), t0 + dur * i / max(n, 1) + 0.25)
        if k > 0:
            text(ctx, ch, cx + widths[i] / 2, y + (1 - k) * rise, size, font, color, alpha * k, 'c')
        cx += widths[i]
    return total

def char_positions(s, x, y, size, font=FONT_KAI, align='c', spacing=1.0):
    widths = [text_size(ch, size, font)[0] * spacing for ch in s]
    total = sum(widths); x0 = {'l': x, 'c': x - total / 2, 'r': x - total}[align]
    out = []; cx = x0
    for wv in widths: out.append((cx + wv / 2, y)); cx += wv
    return out, total

# ---------------- camera ----------------
def camera(ctx, cx, cy, z=1.0, rot=0.0):
    ctx.translate(W / 2, H / 2); ctx.rotate(rot); ctx.scale(z, z); ctx.translate(-cx, -cy)

# ---------------- door registry ----------------
DOOR_LOG = []  # 母题登记：任何红色隐藏母题都调用 register_door(ctx, tag, ...) 以便 scan 出现时刻   # list of (tag, (x0,y0,x1,y1)) in device px for the current frame

REG = [True]
def register_door(ctx, tag, x, y, w, h):
    if not REG[0]: return
    pts = [ctx.user_to_device(px, py) for px, py in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    bb = (min(xs), min(ys), max(xs), max(ys))
    sw, sh = ctx.get_target().get_width(), ctx.get_target().get_height()
    if bb[2] < 0 or bb[0] > sw or bb[3] < 0 or bb[1] > sh: return
    DOOR_LOG.append((tag, bb))

def red_door(ctx, x, y, h, t, open_=0.0, alpha=1.0, tag=None, outline=True, lw=None, flip=False, inner=(0, 0, 0)):
    """Small red door, bottom-left anchored at (x, y) (y = floor). width = 0.48 h."""
    if alpha <= 0: return
    w = h * 0.48; top = y - h
    if tag: register_door(ctx, tag, x, top, w, h)
    lw = lw or max(1.4, h * 0.022)
    frame = rect_pts(x, top, w, h)
    if open_ > 0:
        if inner is not None: fill_poly(ctx, frame, inner, alpha, t, jitter=0.3)
        k = 1 - open_
        if k > 0.01:
            hx = x + (w if flip else 0)
            dw = w * k
            px0 = hx if not flip else hx - dw
            panel = np.array([[hx, top], [hx + (dw if not flip else -dw), top - h * 0.04 * open_], [hx + (dw if not flip else -dw), y + h * 0.04 * open_], [hx, y], [hx, top]])
            fill_poly(ctx, panel, RED, alpha, t)
            if outline: stroke(ctx, panel, t, w=lw, alpha=alpha * 0.9, closed=True)
    else:
        fill_poly(ctx, frame, RED, alpha, t)
        # subtle panel lines + knob
        if outline:
            stroke(ctx, rect_pts(x + w * 0.18, top + h * 0.12, w * 0.64, h * 0.32), t, w=lw * 0.6, alpha=alpha * 0.45, closed=True)
            stroke(ctx, rect_pts(x + w * 0.18, top + h * 0.52, w * 0.64, h * 0.36), t, w=lw * 0.6, alpha=alpha * 0.45, closed=True)
            ctx.arc(x + w * 0.82, top + h * 0.55, max(1.2, h * 0.025), 0, 6.283); ctx.set_source_rgba(*INK, alpha * 0.85); ctx.fill()
    if outline: stroke(ctx, frame, t, w=lw, alpha=alpha * 0.9, closed=True)

def new_frame_surface(scale=1.0):
    s = cairo.ImageSurface(cairo.FORMAT_RGB24, int(W * scale), int(H * scale))
    c = cairo.Context(s); c.scale(scale, scale)
    return s, c
