# -*- coding: utf-8 -*-
"""edge-tts 逐句合成 → 去首尾静音 → 48k mono wav → tts/durations.json（timeline 的输入）。
文本或语速改了自动重合成（md5 缓存键）。"""
import asyncio, json, os, subprocess, hashlib
import edge_tts
import config as C
from story import SCENES
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'tts')
AF = ('silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.02,areverse,'
      'silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.06,areverse')
def spoken(t): return t.replace('"', '').replace('“', '').replace('”', '')
async def one(sem, lid, text, rate=None, pitch=None):
    rate = rate or C.RATE; P = pitch or C.PITCH
    async with sem:
        key = hashlib.md5((C.VOICE + rate + P + spoken(text)).encode()).hexdigest()[:10]
        mp3 = f'{OUT}/{lid}_{key}.mp3'; wav = f'{OUT}/{lid}.wav'
        if not os.path.exists(mp3):
            for k in range(4):
                try: await edge_tts.Communicate(spoken(text), C.VOICE, rate=rate, pitch=P).save(mp3); break
                except Exception as e: print('retry', lid, e); await asyncio.sleep(2)
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', mp3, '-af', AF, '-ar', '48000', '-ac', '1', wav], check=True)
        d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav]))
        return lid, d
async def main():
    os.makedirs(OUT, exist_ok=True); sem = asyncio.Semaphore(6)
    jobs = [one(sem, b[1], b[3].get('say', b[2]), b[3].get('rate'), b[3].get('pitch'))
            for s in SCENES for b in s['beats'] if b[0] == 'l']
    res = dict(await asyncio.gather(*jobs))
    json.dump(res, open(f'{OUT}/durations.json', 'w'), indent=1, ensure_ascii=False)
    print('lines', len(res), 'total speech %.2fs' % sum(res.values()))
asyncio.run(main())
