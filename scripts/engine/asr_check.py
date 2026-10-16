# -*- coding: utf-8 -*-
"""读音自检：faster-whisper 转写每句配音，与稿子逐字比对，列出可疑句（多音字、误读、吞字）。
用法: python3 asr_check.py [line_id ...]    依赖: pip install faster-whisper
ASR 不认识的词也会报，最后必须人耳确认；它只是筛子。"""
import sys, json, os, difflib
import numpy as np
from scipy.signal import resample_poly
import soundfile_shim as sf
from story import SCENES
from faster_whisper import WhisperModel
HERE = os.path.dirname(os.path.abspath(__file__))
PUNC = set('，。；：？！、“”"——…… ,.;:?!')
norm = lambda s: ''.join(c for c in s if c not in PUNC)
m = WhisperModel(os.environ.get('ASR_MODEL', 'small'), device='cpu', compute_type='int8')
want = set(sys.argv[1:]); out = {}
for s in SCENES:
    for b in s['beats']:
        if b[0] != 'l' or (want and b[1] not in want): continue
        x, sr = sf.read(f"{HERE}/tts/{b[1]}.wav"); x = resample_poly(x, 16000, sr).astype(np.float32)
        segs, _ = m.transcribe(x, language='zh', initial_prompt='以下是普通话的句子。')
        hyp = ''.join(g.text for g in segs); r = difflib.SequenceMatcher(None, norm(b[2]), norm(hyp)).ratio()
        out[b[1]] = dict(ref=b[2], hyp=hyp, ratio=round(r, 3))
        print(('  ' if r > 0.92 else '??'), b[1], f'{r:.2f}', '|', b[2], '|', hyp, flush=True)
json.dump(out, open(f'{HERE}/tts/asr.json', 'w'), ensure_ascii=False, indent=1)
