#!/bin/bash
# Usage: video_check.sh <file> <label>. Prints a text-only check of a review video:
# container/codec, size, rotation, duration, full-decode errors, and on-screen text every 2 s.
f="$1"; echo "===== CHECK $2 ====="
file "$f"; ls -la "$f"
ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height:stream_side_data=rotation:stream_tags=rotate -of default=nw=1 "$f"
echo "--- decode errors (blank = clean):"; ffmpeg -v error -i "$f" -f null - 2>&1 | head -5
d=$(mktemp -d); ffmpeg -v error -i "$f" -vf fps=1/2,scale=1280:-1 $d/f_%03d.png
echo "--- on-screen text, one line per 2 s:"
for p in $d/f_*.png; do n=$(basename $p .png); n=${n#f_}; t=$(( (10#$n-1)*2 ))
  txt=$(tesseract $p - 2>/dev/null | tr -cs 'A-Za-z0-9£$.' ' ' | tr -s ' ' | cut -c1-160)
  printf "%3ss | %s\n" "$t" "$txt"; done
