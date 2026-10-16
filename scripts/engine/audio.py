# -*- coding: utf-8 -*-
"""配乐与混音（全 numpy 合成，无外部素材）：
旁白 + 柔 pad（按场景换和弦）+ 音乐盒母题（跟着母题第一次出现，轻）+ 语音闪避 + 关键问句后近静音 + 响度 -16 LUFS + 软限幅。
输出 out/mix.wav。新片：改 PADS / 母题音符 / QUIET_AFTER。"""
import json, os, numpy as np
from scipy.signal import fftconvolve, butter, sosfilt, resample_poly
import pyloudnorm as pyln
import soundfile_shim as sf, config as C
from timeline import build
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
SCENES, LINES, MK, TOTAL = build()
SR = 48000; N = int((TOTAL + 0.2) * SR); rng = np.random.default_rng(5)
def at(t): return int(t * SR)
def SC(i): return [(s['start'], s['end']) for s in SCENES if s['id'] == i][0]
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, f0, f1, o=2): return sosfilt(butter(o, [f0, f1], 'band', fs=SR, output='sos'), x)
IR = rng.standard_normal(int(2.4 * SR)) * np.exp(-np.linspace(0, 2.4, int(2.4 * SR)) * 2.6)
IR = lp(IR, 5000); IR /= np.abs(IR).sum() ** 0.5 * 6
def reverb(x, wet=0.35): return x * (1 - wet) + fftconvolve(x, IR)[:len(x)] * wet * 4
def add(buf, x, t, g=1.0):
    i = at(t)
    if i >= len(buf): return
    if i < 0: x = x[-i:]; i = 0
    n = min(len(x), len(buf) - i); buf[i:i + n] += x[:n] * g
def hz(n): return 440 * 2 ** ((n - 69) / 12)

# 旁白：轻高通 + 极少混响（wet 0.06），可选 presence 提亮
voice = np.zeros(N)
for l in LINES:
    x, sr = sf.read(f"tts/{l['id']}.wav"); assert sr == SR
    if l['opts'].get('presence'): x = x + l['opts']['presence'] * bp(x, 1800, 4800)
    add(voice, x * l['opts'].get('gain', 1.0), l['start'])
voice = reverb(hp(voice, 70), wet=0.06)

# pad：三个微失谐正弦 + 低通，慢起慢收
music = np.zeros(N)
def pad(notes, t0, t1, g=0.05, att=2.0, rel=2.0, bright=900):
    n = at(t1) - at(t0); t = np.arange(n) / SR; y = np.zeros(n)
    for m in notes:
        f = hz(m)
        for det in (-0.12, 0.0, 0.11):
            ph = rng.uniform(0, 6.28); y += np.sin(2 * np.pi * f * (1 + det / 100) * t + ph) + 0.25 * np.sin(2 * np.pi * 2 * f * t + ph)
    y = lp(y, bright)
    env = np.minimum(1, t / att) * np.minimum(1, (t[-1] - t) / rel + 1e-9).clip(0, 1)
    env *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.07 * t)
    add(music, y * env * g / len(notes), t0)
# 每个场景一组和弦（MIDI 音高）。D 小调色彩：[50,57]=D+A，[46,53,62]=Bb 紧张
PADS = {'open': [50, 57, 65], 'close': [50, 57]}
for sid, notes in PADS.items():
    a, b = SC(sid); pad(notes, max(0, a - 0.3), b + 0.8, g=0.045)

# 音乐盒母题 D5 F5 E5 A4 D5：跟着隐藏母题第一次出现轻声响起
def bell(f, d=1.6, a=1.0):
    t = np.arange(int(d * SR)) / SR; env = np.exp(-t * 3.0) * (1 - np.exp(-t * 400))
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) * np.exp(-t * 5) + 0.18 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t * 8)) * env * a
MOTIF = [74, 77, 76, 69, 74]
def motif(gap=0.30, tail=1.8):
    out = np.zeros(int((gap * len(MOTIF) + tail) * SR))
    for k, n in enumerate(MOTIF):
        b = bell(hz(n)); i = int(k * gap * SR); out[i:i + len(b)] += b[:len(out) - i]
    return reverb(out, 0.45) * 0.5
sfx = np.zeros(N)
MOTIF_SKIP = ['end']   # 片尾开放式结尾不放母题，只留空气声→静音
if os.path.exists('motifs.json'):
    for tag, segs in json.load(open('motifs.json')).items():
        if tag in MOTIF_SKIP: continue
        add(sfx, motif(), segs[0]['start'], 0.22)

# 闪避：语音包络压音乐 55%
env = lp(np.abs(voice), 4); env /= env.max() + 1e-9
duck = 1 - 0.55 * np.clip(env * 6, 0, 1)
# 关键问句之后近静音 ~2s（「你注意到了吗？」式揭示）
QUIET_AFTER = ['c01']
duck2 = np.ones(N)
for lid in QUIET_AFTER:
    e = MK[lid][1]; a0, a1, a2 = at(e - 0.25), at(e + 0.05), at(e + 2.0)
    duck2[a0:a1] = np.linspace(1, 0.08, a1 - a0); duck2[a1:a2] = 0.08; duck2[a2:] = np.minimum(duck2[a2:], 0.08)
mix = voice + music * duck * duck2 + sfx * duck ** 0.5 * duck2
# 结尾最后 0.5s 数字静音
i0, i1 = at(TOTAL - 1.3), at(TOTAL - 0.5); fd = np.ones(N); fd[i0:i1] = np.linspace(1, 0, i1 - i0); fd[i1:] = 0; mix *= fd
meter = pyln.Meter(SR); lufs = meter.integrated_loudness(mix)
mix *= 10 ** ((C.TARGET_LUFS - lufs) / 20)
lim = 10 ** (C.PEAK_DBFS / 20); k = lim * 0.8
mix = np.where(np.abs(mix) > k, np.sign(mix) * (k + (lim - k) * np.tanh((np.abs(mix) - k) / (lim - k))), mix)
tp = np.abs(resample_poly(mix, 4, 1)).max()
print('LUFS %.1f → %.1f  truepeak %.1f dBTP' % (lufs, meter.integrated_loudness(mix), 20 * np.log10(tp)))
os.makedirs('out', exist_ok=True); sf.write('out/mix.wav', mix.astype(np.float32), SR)
