#!/bin/sh
# 검수 한 번 돌리기: 서버 띄우고 → 실제 크롬으로 열고 → 결과 표를 찍는다.
# 서버는 결과를 받으면 스스로 끝난다. 창은 반드시 앞에 있어야 한다(뒤에 깔리면 느려진다).
cd "$(dirname "$0")/.."
# 쓰는 법:  sh probe/run.sh [포트]           전수 검수(아카이빙 + 크레딧)
#           QS='?only=overflow' sh probe/run.sh    가로 넘침만
#           QS='?only=mobile' SIZE=420,900 sh probe/run.sh   모바일 폭에서만
PORT=${1:-8877}
rm -f probe/report.json
node probe/serve.js "$PORT" &
SRV=$!
sleep 1
# 창 크기를 지정하려면 새 인스턴스여야 한다 — 기존 크롬이 열려 있으면 --window-size 가
# 무시되고 그 창을 재사용한다. 별도 프로필을 주면 따로 뜬다.
ARGS="--new-window"
[ -n "$SIZE" ] && ARGS="--user-data-dir=$(mktemp -d) --window-size=$SIZE --no-first-run"
"/c/Program Files/Google/Chrome/Application/chrome.exe" $ARGS "http://127.0.0.1:$PORT/_audit.html$QS" >/dev/null 2>&1 &
i=0
while [ ! -f probe/report.json ] && [ $i -lt 120 ]; do sleep 2; i=$((i+1)); done
wait $SRV 2>/dev/null
[ -f probe/report.json ] || { echo "결과가 안 왔다 — 크롬 창이 앞에 있는지 확인해라"; kill $SRV 2>/dev/null; exit 1; }
