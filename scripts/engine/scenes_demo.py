# -*- coding: utf-8 -*-
"""两场景示范：①纸面世界坐标 + 缓移镜头 + 分步笔画 + 角落藏一扇红门（母题）
②画面写字（nosubs 场景）→ 只剩一扇红门 → 缓开 + 推入全黑（无旁白开放式结尾）。
新片照这个写法：每个 scene_<id>(ctx, t) 用 ls/le/wt 取旁白时间，不手填秒数。"""
from figs import *
from timeline import build
_SC = {s['id']: s for s in build()[0]}

def scene_open(ctx, t):
    paper(ctx, t)
    s0, s1 = _SC['open']['start'], _SC['open']['end']
    p = seg(t, s0 + 0.2, s0 + 2.6, eout)                         # 线条逐步画出
    cx = mix(1060, 900, seg(t, s0 + 0.5, s1, eio))               # 缓移：过渡用慢的
    ctx.save(); camera(ctx, cx, 540, 1.0)
    stroke(ctx, line_pts(-200, 820, 2400, 820), t, w=3.0, p=sp(p, 0, 4))             # 地平线
    head = ellipse_pts(700, 560, 46, 50); stroke(ctx, head, t, w=3.0, p=sp(p, 1, 4), closed=True)
    stroke(ctx, catmull([[700, 612], [690, 700], [700, 820]], 10), t, w=3.0, p=sp(p, 1, 4))
    stroke(ctx, bubble_pts(1080, 400, 260, 120, tail=(-0.8, 1.2)), t, w=2.8, p=sp(p, 2, 4))
    write_on(ctx, '每天都在说', 1080, 400, 56, t, ls('o01') + 0.3, 0.9, alpha=1.0)
    if t > ls('o02'):                                             # 圈出「说错」的地方：笔迹即重点
        circle_mark(ctx, 1080, 400, 230, 70, t, p=seg(t, wt('o02', '说错'), wt('o02', '说错') + 0.7), color=RED, w=3.0)
    hatch(ctx, 1500, 640, 260, 180, t, gap=16, alpha=0.22, p=sp(p, 3, 4))
    red_door(ctx, 1840, 820, 150, t, alpha=seg(p, 0.5, 0.9), tag='demo')   # 隐藏母题：藏在边缘，从不点名
    ctx.restore()

def scene_close(ctx, t):
    paper(ctx, t)
    s0, s1 = _SC['close']['start'], _SC['close']['end']
    c0, c1 = L('c01')
    # 画面写字（问句，不是结论）→ 淡出
    a = 1 - seg(t, c1 + 0.6, c1 + 1.2)
    write_on(ctx, '你注意到了吗？', 960, 470, 76, t, c0, 0.9, alpha=a)
    # 只剩一扇红门：渐入 → 静持 → 缓开同时推镜入门内全黑
    # 时长比例照《精神分析的本质》v3b：定住1.0 + 淡出0.75 + 门渐入1.25 + 静持1.0 + 开门推镜3.9 + 黑场/空气
    tin = c1 + 1.2; topen = tin + 1.25 + 0.6; tend = min(topen + 3.0, s1 - 0.6)
    da = seg(t, tin, tin + 1.25)
    if da <= 0: return
    if t >= tend: ctx.set_source_rgb(0, 0, 0); ctx.paint(); return
    op = seg(t, topen, tend, eio)
    z = mix(1.0, 9.0, seg(t, topen + 0.2, tend, ein))
    dx, dy, h = 960 - 0.24 * 300, 540 + 150, 300
    ctx.save(); camera(ctx, 960, 540, z)                      # 推镜中心=门洞中心，门洞填满画面即全黑
    red_door(ctx, dx, dy, h, t, open_=op, alpha=da, tag='end')
    ctx.restore()
    dim(ctx, seg(t, tend - 0.5, tend), color=(0, 0, 0))
