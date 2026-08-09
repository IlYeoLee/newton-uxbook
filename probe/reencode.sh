#!/bin/sh
# 시나리오 영상을 1920 / CRF20 으로 통일한다. 원본은 assets/_orig/ 로 옮겨 남긴다.
# 새로 뽑은 게 더 크면(이미 작게 눌린 장면) 원본을 그대로 쓴다.
set -e
cd "$(dirname "$0")/.."
mkdir -p assets/_orig

for f in sc1 sc2 sc3 sc4 sc5 sc6 lead_home lead_products lead_scenario; do
  src="assets/_orig/$f.mp4"
  [ -f "$src" ] || cp "assets/$f.mp4" "$src"
  ffmpeg -v error -y -i "$src" \
    -vf "scale='min(1920,iw)':-2" \
    -c:v libx264 -crf 20 -preset slow -pix_fmt yuv420p -profile:v high \
    -c:a copy -movflags +faststart "assets/$f.new.mp4"
  o=$(stat -c%s "$src") n=$(stat -c%s "assets/$f.new.mp4")
  if [ "$n" -lt "$o" ]; then
    mv "assets/$f.new.mp4" "assets/$f.mp4"; tag="→"
  else
    rm "assets/$f.new.mp4"; cp "$src" "assets/$f.mp4"; tag="원본유지"
  fi
  awk -v f="$f" -v o="$o" -v t="$tag" -v n="$(stat -c%s "assets/$f.mp4")" \
      'BEGIN{printf "%-15s %6.1fMB %s %6.1fMB\n", f, o/1048576, t, n/1048576}'
done

echo "---"
printf 'assets 합계 %s\n' "$(du -sh --exclude=_orig assets | cut -f1)"
