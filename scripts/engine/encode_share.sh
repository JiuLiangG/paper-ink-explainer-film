#!/bin/bash
# 分享版：<100MB（Drive UploadFile/CopyFromBox 上限）且手机可直接播放
# 5 分半片约 40–45MB。超过目标就把 CRF +2 重压。
IN="$1"; OUT="$2"; CRF="${CRF:-23}"
ffmpeg -y -v error -i "$IN" -c:v libx264 -preset slow -crf "$CRF" -tune animation -maxrate 1.2M -bufsize 2.4M \
  -pix_fmt yuv420p -profile:v high -level 4.1 -c:a aac -b:a 128k -movflags +faststart "$OUT"
du -h "$OUT"
