# -*- coding: utf-8 -*-
"""从成片抽 QA 静帧：每场景中点 + 每句旁白中点 + 每个母题出现中点，外加一张联系表 contact.jpg。
用法: python3 stills.py film.mp4 out_dir"""
import sys, os, json, subprocess
from timeline import build
from PIL import Image
src, od = sys.argv[1], sys.argv[2]; os.makedirs(od, exist_ok=True)
SC, LI, MK, TOT = build(); ts = {}
for s in SC: ts[f"scene_{s['id']}"] = (s['start'] + s['end']) / 2
for l in LI: ts[f"line_{l['id']}"] = (l['start'] + l['end']) / 2
if os.path.exists('motifs.json'):
    for tag, segs in json.load(open('motifs.json')).items():
        for k, sg in enumerate(segs): ts[f'motif_{tag}{k}'] = (sg['start'] + sg['end']) / 2
ts['tail'] = TOT - 0.6
files = []
for name, t in sorted(ts.items(), key=lambda x: x[1]):
    fn = f'{od}/{t:07.2f}_{name}.jpg'
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{t:.3f}', '-i', src, '-frames:v', '1', '-q:v', '3', fn], check=True); files.append(fn)
ims = [Image.open(f).resize((480, 270)) for f in files]; cols = 4; rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (480 * cols, 270 * rows), 'white')
for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 480, (i // cols) * 270))
sheet.save(f'{od}/contact.jpg', quality=85); print(len(files), 'stills →', od)
