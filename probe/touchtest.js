// 태블릿 터치를 실제로 흉내 내서 카드 확대가 열리는지 본다.
// 크롬을 원격 디버깅으로 띄우고 CDP 로 진짜 touchStart/touchEnd 를 넣는다 —
// 사람이 태블릿에서 누르는 것과 같은 경로다(합성 click 까지 브라우저가 만든다).
//
//   node probe/touchtest.js [주소]
//
// 통과하면 "확대 열림 · 유지" 를 찍고 0 으로 끝난다.
const { spawn } = require('child_process');
const os = require('os'), path = require('path'), fs = require('fs');

const URL_ = process.argv[2] || 'http://127.0.0.1:8833/index.html';
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PORT = 9333;

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function targets() {
  const res = await fetch(`http://127.0.0.1:${PORT}/json`);
  return res.json();
}

function rpc(ws) {
  let id = 0;
  const waiting = new Map();
  ws.addEventListener('message', ev => {
    const m = JSON.parse(ev.data);
    if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m); waiting.delete(m.id); }
  });
  return (method, params = {}) => new Promise((resolve, reject) => {
    const n = ++id;
    waiting.set(n, m => m.error ? reject(new Error(method + ': ' + m.error.message)) : resolve(m.result));
    ws.send(JSON.stringify({ id: n, method, params }));
  });
}

(async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'touchtest-'));
  const chrome = spawn(CHROME, [
    '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
    `--remote-debugging-port=${PORT}`, `--user-data-dir=${dir}`, '--no-first-run',
    '--window-size=1280,800', 'about:blank'
  ], { stdio: 'ignore' });

  let list = [];
  for (let i = 0; i < 40 && !list.length; i++) {
    await sleep(250);
    try { list = (await targets()).filter(t => t.type === 'page'); } catch {}
  }
  if (!list.length) { console.log('크롬을 못 띄웠다'); chrome.kill(); process.exit(2); }

  const ws = new WebSocket(list[0].webSocketDebuggerUrl);
  await new Promise(r => ws.addEventListener('open', r));
  const send = rpc(ws);

  const ev = async (expr) => (await send('Runtime.evaluate',
    { expression: expr, returnByValue: true, awaitPromise: true })).result.value;

  await send('Page.enable');
  await send('Runtime.enable');
  // 갤럭시 탭 S5e 가로: CSS 1280x800, 픽셀비 2, 터치 기기
  await send('Emulation.setDeviceMetricsOverride',
    { width: 1280, height: 800, deviceScaleFactor: 2, mobile: true });
  await send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });
  await send('Emulation.setEmitTouchEventsForMouse', { enabled: true, configuration: 'mobile' });

  await send('Page.navigate', { url: URL_ });
  await sleep(2500);

  // 크레딧 장으로 이동하고 3D 가 붙을 때까지 기다린다
  await ev(`(() => { const p=[...document.querySelectorAll('.page')];
    const i=p.findIndex(x=>x.dataset.page==='credits');
    p.forEach((x,n)=>x.classList.toggle('active',n===i));
    document.getElementById('book').classList.remove('is-cover'); return i; })()`);

  let slots = 0;
  for (let i = 0; i < 60 && slots < 5; i++) {
    await sleep(500);
    slots = await ev(`document.querySelectorAll('.cc3d-slot').length`);
  }
  console.log('카드 판:', slots, '· 3D:', await ev(`document.querySelector('.lany-stage').className`));
  if (!slots) { chrome.kill(); process.exit(2); }

  await sleep(2500);   // 줄이 가라앉기를 기다린다

  let pass = 0;
  for (let n = 0; n < slots; n++) {
    // 카드 한복판 좌표를 그 순간에 읽는다
    const pt = await ev(`(() => { const s=document.querySelectorAll('.cc3d-slot')[${n}];
      const r=s.getBoundingClientRect();
      return { x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2) }; })()`);

    const touch = [{ x: pt.x, y: pt.y, radiusX: 12, radiusY: 12, force: 1, id: 1 }];
    await send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: touch });
    await sleep(90);
    await send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });

    await sleep(900);   // 합성 click 이 늦게 오는 것까지 지나 보낸다
    const open = await ev(`!!document.querySelector('.cc-zoom')`);
    const who = await ev(`(document.querySelector('.cc-zoom .cc-sig')||{}).textContent || ''`);
    console.log(`카드 ${n + 1} (${pt.x},${pt.y}) → ${open ? '열림 ' + who : '안 열림'}`);
    if (open) pass++;
    // 닫고 다음 장으로
    await ev(`(() => { const p=document.querySelector('.credits-page');
      p.__closeZoom && p.__closeZoom(); p.classList.remove('zoomed'); })()`);
    await sleep(500);
  }

  // ---- 확대 상태의 흐름 검사 ----
  const tap = async (x, y, wait = 900) => {
    await send('Input.dispatchTouchEvent',
      { type: 'touchStart', touchPoints: [{ x, y, radiusX: 12, radiusY: 12, force: 1, id: 1 }] });
    await sleep(90);
    await send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await sleep(wait);
  };
  const state = () => ev(`(() => { const p=document.querySelector('.credits-page');
    const d=p.querySelector('.cc-dim'), b=p.querySelector('.cc-close');
    const cs=d&&getComputedStyle(d), bs=b&&getComputedStyle(b);
    return { zoom: !!document.querySelector('.cc-zoom'), zoomed: p.classList.contains('zoomed'),
      dim: cs && +cs.opacity, dimHits: cs && cs.pointerEvents, closeShown: bs && bs.display !== 'none' }; })()`);
  const center = n => ev(`(() => { const r=document.querySelectorAll('.cc3d-slot')[${n}].getBoundingClientRect();
    return { x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2) }; })()`);
  const sig = () => ev(`(document.querySelector('.cc-zoom .cc-sig')||{}).textContent||''`);

  const checks = [];
  const ok = (name, cond, got) => { checks.push(cond);
    console.log(`  ${cond ? 'OK  ' : '실패 '}${name}${cond ? '' : '  ← ' + JSON.stringify(got)}`); };

  console.log('\n[확대 흐름]');
  const c0 = await center(0), c2 = await center(2);
  await tap(c0.x, c0.y);
  let st = await state();
  ok('카드를 누르면 확대된다', st.zoom && st.zoomed, st);
  ok('배경이 딤된다', st.dim > 0.5, st);
  ok('배경이 터치를 막는다', st.dimHits === 'auto', st);
  ok('닫기 버튼이 보인다', st.closeShown, st);

  const before = await sig();
  await tap(c2.x, c2.y);
  st = await state();
  ok('확대 중 배경 카드는 안 눌린다', st.zoom && before === (await sig()), { before, st });

  if (!(await state()).zoom) await tap(c0.x, c0.y);
  await tap(60, 700);
  st = await state();
  ok('배경을 누르면 닫힌다', !st.zoom && !st.zoomed, st);

  await tap(c0.x, c0.y);
  const btn = await ev(`(() => { const r=document.querySelector('.credits-page .cc-close').getBoundingClientRect();
    return { x: Math.round(r.left+r.width/2), y: Math.round(r.top+r.height/2) }; })()`);
  await tap(btn.x, btn.y);
  st = await state();
  ok('닫기 버튼으로 닫힌다', !st.zoom && !st.zoomed, st);

  const bad = checks.filter(c => !c).length;
  console.log(`\n결과: 카드 열기 ${pass}/${slots} · 흐름 ${checks.length - bad}/${checks.length}`);
  chrome.kill();
  process.exit(pass === slots && !bad ? 0 : 1);
})().catch(e => { console.error('실패:', e.message); process.exit(2); });
