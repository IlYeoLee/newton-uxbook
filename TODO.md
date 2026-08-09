# 남은 작업

## 1. View Now 버튼 링크 (사용자 결정 대기)
체험 장(Archive 첫 장)의 버튼 두 개가 아직 갈 곳이 없다. 주소가 정해지면
build.py 의 이 한 줄만 채우면 각각 새 탭으로 열린다.

    TRY_CTA = {"app": "", "sim": ""}

비어 있는 동안은 aria-disabled 로 나가서 눌러도 아무 데도 안 간다.

## 2. 원고 대조에서 남은 것
- sec-05 본문이 원고와 다르다. 원고는 "Newton은 IMU 센서를 비롯한 다중 감각
  센서를 통해…"로 시작하는데 책은 "낯선 움직임을 시작할 때, Newton은 하체의
  보폭과 착지…"다. 갈아끼울지 확인 필요.
- 네비 탭 이름: 원고는 04 를 Concept, 07 을 Expandability 로 부르는데 탭은
  아직 Solution / Extensibility 다(킥커는 이미 원고대로 바꿨다).
- "▶ Newton의 전체 플레이 여정 보기"는 뺀 상태로 둔다(사용자 지시).

## 3. 잠시 꺼둔 것
- "Newton User-facing 와이어프레임 (Mobile)" 토글은 안 그린다. 원본은
  structure_full.json 에 그대로 있고, build.py 의 SHOW_WIREFRAME 을 True 로
  되돌리면 그 자리에 그대로 돌아온다.
- ?dbg=1 진단판(판정 사각형 초록 테두리 + 이벤트 사슬 로그)은 남겨 뒀다.
  평소에는 아무것도 그리지 않는다.

## 4. 미뤄둔 것
- card.glb(2.3MB) 유지하기로 결정(B안). 3D 번들 6.4MB 그대로.

## 배포 (푸시만으로는 안 올라간다)
GitHub Pages 가 푸시 뒤 빌드를 스스로 안 도는 일이 잦다(짧은 시간에 여러 번
푸시하면 특히). 푸시 → 빌드 요청 → 완료 확인 → 라이브에서 읽어보기까지 해야
"배포했다"고 말할 수 있다.

    git push origin main lanyard-3d
    gh api -X POST repos/IlYeoLee/newton-uxbook/pages/builds --jq '.status'
    gh api repos/IlYeoLee/newton-uxbook/pages/builds/latest --jq '.status, .commit'
    curl -s https://ilyeolee.github.io/newton-uxbook/index.html | grep -c '무엇이든'

에셋은 빌드가 주소 뒤에 수정시각·크기 도장을 붙인다(assets/x.js?v=1a2b3c4d).
그래서 ?v= 를 손으로 붙일 일이 없다. 도장이 없으면 브라우저가 옛 파일을 계속
쓴다 — 태블릿에서 고친 게 반영이 안 되던 원인이 이것이었다.

## 검수하는 법
### 터치·확대 흐름 (태블릿) — probe/touchtest.js
크롬을 원격 디버깅으로 몰아 진짜 touchStart/touchEnd 를 넣는다. 태블릿과 같은
조건(1280x800, 픽셀비 2, 터치 기기)이라 사람이 누르는 것과 같은 경로다.
카드 다섯 장을 각각 눌러 확대가 열리는지, 그리고 확대 흐름 7가지를 본다.

    node probe/touchtest.js
    node probe/touchtest.js https://ilyeolee.github.io/newton-uxbook/index.html

이걸 만들기 전에는 "안 된다"는 말만 듣고 판정 방식을 다섯 번 바꿨는데 전부
헛짚었다. 터치를 건드리면 반드시 이걸 돌리고 올린다.

### 글·그림이 사라졌는지 — probe/check_content.py
직전 index.html 과 견줘서 이번 변경으로 흘린 글이나 파일이 있는지 본다.
원본(structure_full.json)과 견주지 않는 이유는 빌드가 TEXT_PATCHES 로 문장을
갈아끼우고 일부러 버리는 것도 있어서다.

    python probe/check_content.py

### 마지막 두 장 전수 검수 — probe/serve.js + probe/audit.js
    node probe/serve.js 8877
    "/c/Program Files/Google/Chrome/Application/chrome.exe" --new-window       "http://127.0.0.1:8877/_audit.html"

주의
- 헤드리스 스크린샷은 --use-angle=swiftshader --enable-unsafe-swiftshader 로
  WebGL 이 뜨지만 GLB 가 안 끝나 3D 는 비어 나온다. 2D 페이지 확인용으로만.
- --timeout 만 주면 setInterval 이 안 돈다. --virtual-time-budget 이 필요하다.
  단 가상시간에서는 CSS 트랜지션이 진행되지 않는다.

## 되돌릴 지점
- 태그 css3d-credits (9118a88) = 3D 이전, CSS 카드가 돌던 마지막 지점.
- main 과 lanyard-3d 는 같은 지점을 가리키게 유지 중(따로 두면 번들에서 충돌).

## 이번 세션에서 끝낸 것
- 토글 안을 한 벌로 통일 — 카드(라벨·주장·본문·출처) 아니면 중첩 토글, 둘뿐.
  "근거" 토글을 없애 출처를 주장 바로 밑으로. 외부 이모지 전부 제거.
- 원고(피그마 영한검수) 대조 — 킥커 03/04/07/09, Now, Every Turn Is Yours.,
  Find Your Movement., 표기를 Newton 하나로(조사 앞에서 안 바뀌던 버그 포함).
- 모드 표에 영문이 통째로 없던 것을 채움. 지금 한글 조각 중 영문 없는 것 0.
- 새 장 셋: Products 개요(원고), Solution 뒤 홈 영상, Archive 첫 장 "체험"
  (피그마 93:493 실측 이식 — 카드 두 장·그라디언트·버튼, 한영/리플/등장 모션).
- 로고 장: 가이드 사진 2초 → 심볼 모션 루프. Solution 사진 → Pack 프로토 영상.
  시나리오 마지막에 세탁 사진.
- 페이지는 나갔다 들어오면 그 장의 처음 상태로(장마다 __reset).
- 좌우·하단 여백을 0.830cqw 하나로 통일. 스크롤 유도에 표지와 같은 결의 띠.
- 크레딧: THANKS TO 만 대문자, 김소진·박주원 역할, 카드 뒷면 레이아웃 정리
  (칩과 이름은 자리 고정, 가운데 띠만 줄 수에 따라 늘고 준다).
- 태블릿에서 카드가 안 눌리던 것 — 진짜 원인은 딤(.cc-dim)에 걸린 옛 폴백
  모듈의 close 가 확대를 여는 그 탭의 합성 click 에 맞아 즉시 닫던 것이었다.
  3D 가 붙으면 폴백은 아무것도 하지 않게 막았다. probe/touchtest.js 로 검증.
- 에셋 주소에 버전 도장 — 캐시 때문에 고친 게 반영 안 되던 것.
