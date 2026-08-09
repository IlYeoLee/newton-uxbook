# 남은 작업

## 1. 마지막 두 장 전수 검수 (다음 세션 최우선)
사용자가 하나씩 발견해 알려주는 구조를 끝내는 게 목적이다. 한 번 돌려 표로 받는
스크립트를 짤 것. 아래 "검수하는 법" 방식으로 실제 브라우저에서 값을 받는다.

**아카이빙(archive)**
- 42장 로드 상태 — 즉시 5장 / 지연 37장이 다가올 때 실제로 붙는지
- 스테이지 밖으로 넘치는 장이 있는지
- 칩 6개와 현재 묶음 표시가 어긋나지 않는지
- 무한 고리에서 어느 위치든 양옆이 채워지는지
- 탭 확대가 42장 전부에서 열리는지

**크레딧(credits)**
- 슬롯 5개 전부에 __band 가 붙는지
- 카드별로 자기 사람이 열리는지(5장 각각)
- 드래그 후 반드시 놓이는지(마우스에 안 붙는지)
- 확대 시 뒷면이 먼저 뜨는지 · 플립이 도는지 · SNS 버튼이 눌리는지
- 콘솔 에러 0

## 2. 영상 용량 (사용자 결정 대기)
C:\Users\user\Downloads\화질비교 에 sc3 네 가지를 뽑아뒀다.
원본 2560/CRF18 57MB · 1920/CRF18 43MB · 1920/CRF20 33MB · 1920/CRF22 25MB.
고르면 sc1~sc6, lead_* 전체를 같은 설정으로 교체한다.
현재 assets 338MB 중 시나리오 영상이 150MB 가량.

## 3. 미뤄둔 것
- card.glb(2.3MB) 유지하기로 결정(B안). 3D 번들 6.2MB 그대로.
- 김소진·박주원 역할 문구 없음.
- 카드 면이 <Html transform> DOM 이라 drei 의 CSS3D 히트박스가 보이는 카드와
  어긋난다. 그래서 판정을 getBoundingClientRect() 로 직접 한다.

## 검수하는 법 (헤드리스로는 3D 가 안 뜬다 — 실제 크롬 + 서버 로그)
1. 로그 남는 서버: python -m http.server 8833 --bind 127.0.0.1 > /c/tmp/srv.log 2>&1 &
2. index.html 사본 끝에 스크립트를 넣고 fetch("/REPORT?"+encodeURIComponent(값))
   으로 결과를 보낸다. 페이지 이동은 #nzRight 클릭 반복(표지에서 credits 까지 20회).
3. 실제 크롬으로 연다:
   "/c/Program Files/Google/Chrome/Application/chrome.exe" --new-window "http://127.0.0.1:8833/사본.html"
4. 로그에서 읽는다: grep -o 'REPORT?[^ ]*' /c/tmp/srv.log | tail -1

주의
- 헤드리스 스크린샷은 --use-angle=swiftshader --enable-unsafe-swiftshader 로 WebGL 이
  뜨지만 GLB 가 안 끝나 3D 는 비어 나온다. 2D 페이지 확인용으로만 쓸 것.
- 스크린샷 모드에서 --timeout 만 주면 setInterval 이 안 돈다. --virtual-time-budget 필요.
- 단, 가상시간에서는 CSS 트랜지션이 진행되지 않는다(전환 중 화면으로 오판하기 쉽다).

## 되돌릴 지점
- 태그 css3d-credits (9118a88) = 3D 이전, CSS 카드가 돌던 마지막 지점.
  git reset --hard css3d-credits
- main 과 lanyard-3d 는 같은 지점을 가리키게 유지 중(따로 두면 번들에서 충돌).

## 이번 세션에서 끝낸 것
- Archive 탭 신설 — 과정 사진 + Designed By 를 하나로
- 아카이빙 페이지 신설 — 원형 갤러리 · 무한 고리 · 묶음 칩 6개 · 탭 확대 ·
  거리 기반 스와이프 + 플릭 관성
- 아카이빙 이미지 249MB → 4.5MB (WebP 1100px), 첫 진입 5장만
- 3D 카드 — 판정을 보이는 판 기준으로, 카드별 물리 드래그, 확대는 3D 밖 DOM
  오버레이(딤·블러·SNS 버튼·진짜 3D 플립, 뒷면 우선)
- 3D 번들 유휴 프리페치 + 로딩 표시, 실패해도 책은 안 죽음
- 구형 태블릿 대응 — 픽셀비 1.5, 터치 판정 34px/500ms, 물리 중력 -18·감쇠 20
- 표지 — 한 번 눌러 전체화면, 코드펜 터치 애니메이션, 상하 딤 완화
- 크레딧 THANKS TO 영문 대문자
