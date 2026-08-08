# 남은 작업

## 영상 3편 붙이기 (인코딩만 끝난 상태)
`assets/` 에 들어와 있고 아직 어느 페이지에도 안 붙었다.

| 파일 | 해상도 | 갈 자리 |
|---|---|---|
| `bx_logo_sym.mp4` | 1186×450 | Logo 페이지(sec-11). 지금 이미지와 **같은 프레임 안**에서 이미지 → 영상 → 이미지 로 페이드 인아웃 루프. 타이밍은 기존 캐러셀과 동일하게. |
| `sol_pack.mp4` | 1580×2664 | Solution(sec-04) 좌측 이미지 자리. **데스크톱만** 교체하고 모바일은 기존 이미지 유지. |
| `lead_home.mp4` | 1920×1080 | Solution 다음 장에 새 풀페이지(패딩 + 라운드만). Products 첫 장(`products-lead`)과 같은 형식, 재생 컨트롤바도 그대로. |

## 크레딧 페이지 모바일
3D 캔버스에 모바일 규칙이 없다. 폰 폭에 카드 5장이 가로로 늘어서서 손톱만 해진다.

- 카드 5장을 가로 스크롤 한 줄로. 캔버스는 두고 카메라만 당겨 한 번에 2장쯤 보이게, 스와이프로 넘긴다.
- 탭 확대·딤·닫기·플립은 데스크톱과 동일하게.
- `thanks to` 4열 → 2열 (규칙은 이미 넣어둠).
- WebGL 없거나 `prefers-reduced-motion` 이면 기존 CSS 카드로 폴백. 마크업이 DOM 에 남아 있어 `display` 만 바꾸면 된다.

## 카드 면을 굽지 말고 편집 가능한 레이어로
지금은 인물 사진만 캔버스에 구워 텍스처로 넣는다. drei 의 `<Html transform>` 으로
카드 앞/뒷면에 실제 DOM 을 붙이면 사진·이름·역할 칩·그라디언트가 전부 HTML/CSS 로
남아 코드에서 실시간 수정이 된다.

## 확인 못 한 것
- 리드 페이지 모바일 블러 필러는 CSS 만 넣고 실제 화면으로는 아직 못 봤다.
  헤드리스에서 탭 이동이 안 잡혀서다. 로컬에서 눈으로 볼 것.
- 김소진·박주원 역할 문구가 아직 없다.

## 되돌릴 지점
- 태그 `css3d-credits` (9118a88) = CSS 3D 크레딧이 동작하던 마지막 지점.
  `git reset --hard css3d-credits`

## 크레딧 페이지 캡쳐하는 법 (이걸 못 찾아서 계속 눈으로 못 보고 수치만 고쳤다)
```bash
CHROME="/c/Program Files/Google/Chrome/Application/chrome.exe"
# index.html 끝에 이 스크립트를 넣은 사본을 만들고:
#   setTimeout(()=>{let n=0;const iv=setInterval(()=>{
#     const a=document.querySelector('.page.active');
#     if(a&&a.getAttribute('data-page')==='credits'){clearInterval(iv);return;}
#     const b=document.getElementById('nzRight'); if(b) b.click();
#     if(++n>22) clearInterval(iv);},200);},600);
"$CHROME" --headless=new --no-sandbox --hide-scrollbars \
  --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist \
  --window-size=1200,760 --virtual-time-budget=25000 \
  --user-data-dir=/c/tmp/cap --screenshot=/c/tmp/out.png "http://127.0.0.1:8811/사본.html"
```
- WebGL 은 `--use-angle=swiftshader --enable-unsafe-swiftshader` 로 소프트웨어 렌더링해야 잡힌다.
- **스크린샷 모드에서 `--timeout` 만 주면 setInterval 이 안 돈다.** `--virtual-time-budget` 을 써야
  페이지 넘기기가 실제로 일어난다. 이걸 몰라서 계속 표지만 찍혔다.
- 페이지는 21장이고 credits 가 마지막. 표지에서 `#nzRight` 20번.
- 측정만 할 때는 `--dump-dom` + `--virtual-time-budget` 조합.

## 지금 확인된 것 (위 방법으로 실제 캡쳐)
- 크레딧 페이지에 **카드가 한 장도 안 보인다**. 캔버스가 비어 있다.
  `boot()` 재시도 문제는 고쳤으니, 다음은 GLB/텍스처 로딩이나 Band 렌더 실패를 봐야 한다.
- 그 전 로컬 화면에서는 카드 DOM 이 뒤집힌 채(글자 좌우 반전) 줄과 떨어져 가운데 뭉쳐 있었다.
  <Html transform> 의 위치·방향이 RigidBody 를 못 따라가는 것으로 보인다.
