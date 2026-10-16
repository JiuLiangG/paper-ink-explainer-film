#!/bin/bash
# 全流程：TTS → 时间轴 → 母题扫描 → 混音 → 并行渲染 → 合成母带 → 分享版 → QA 静帧
# 用法: bash render_all.sh [输出目录] [片名]
set -e
E="$(cd "$(dirname "$0")" && pwd)"; cd "$E"
OUT="${1:-$E/out}"; NAME="${2:-film}"; mkdir -p "$OUT" out qa
python3 tts.py
python3 timeline.py | tail -1
python3 render.py scan
python3 audio.py
NF=$(python3 render.py info | cut -d' ' -f1)
J=${J:-$(nproc)}; STEP=$(( (NF + J - 1) / J ))
rm -f out/part_*.mp4
for i in $(seq 0 $((J-1))); do
  f0=$((i*STEP)); f1=$(((i+1)*STEP)); [ $f0 -ge $NF ] && break
  python3 render.py chunk $f0 $f1 out/part_$i.mp4 > out/log_$i.txt 2>&1 &
done
wait
ls out/part_*.mp4 | sort -V | sed "s#^out/#file '#; s/$/'/" > out/list.txt
ffmpeg -y -v error -f concat -safe 0 -i out/list.txt -c copy out/video.mp4
# 母带：视频直拷 + AAC 192k
ffmpeg -y -v error -i out/video.mp4 -i out/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT/$NAME.mp4"
bash "$E/encode_share.sh" "$OUT/$NAME.mp4" "$OUT/${NAME}_分享.mp4"
python3 stills.py "$OUT/$NAME.mp4" "$OUT/stills"
ls -la "$OUT"
