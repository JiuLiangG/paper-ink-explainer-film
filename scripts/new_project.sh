#!/bin/bash
# 开新片：把引擎复制到项目目录（不要在 skill 目录里直接渲染）
# 用法: bash new_project.sh /workspace/<片名>-film
set -e
SRC="$(cd "$(dirname "$0")" && pwd)/engine"; DST="${1:?项目目录}"
mkdir -p "$DST"; cp -r "$SRC" "$DST/engine"; rm -rf "$DST/engine/tts" "$DST/engine/out" "$DST/engine/qa"
python3 -c "import cairo, edge_tts, pyloudnorm, scipy, PIL" 2>/dev/null || cat <<'M'
缺依赖。box 上已验证可用的装法：
  sudo apt-get install -y python3-cairo        # pip 装 pycairo 会因缺 Python dev 头失败
  pip install --user --break-system-packages -U edge-tts pyloudnorm scipy pillow numpy
  (可选读音自检) pip install --user --break-system-packages faster-whisper
M
echo "新工程: $DST/engine  → 改 config.py / story.py / scenes_*.py，然后 bash render_all.sh $DST <片名>"
