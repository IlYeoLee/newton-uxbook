// 마지막 두 장(아카이빙 · 크레딧) 전수 검수. index.html 에 주입되어 실제 크롬에서
// 한 번 돌고, 결과를 POST /REPORT 로 보낸다. 헤드리스로는 3D 가 안 뜬다 — 실제 크롬으로.
(function () {
  const t0 = Date.now();
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  // 창이 뒤에 깔리면 rAF 가 아예 안 돈다 — 그대로 두면 검수가 거기서 멈춘다.
  const raf2 = () => Promise.race([
    new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))),
    sleep(250)
  ]);

  // ── 콘솔 에러 수집 (가장 먼저) ──
  const errs = [];
  const ce = console.error;
  console.error = function (...a) { errs.push(a.map(String).join(' ')); ce.apply(console, a); };
  addEventListener('error', e => errs.push('window.error: ' + (e.message || e.type)));
  addEventListener('unhandledrejection', e => errs.push('unhandled: ' + String(e.reason)));

  // ── 합성 포인터 ──
  // setPointerCapture 는 합성 pointerId 로 부르면 던진다. 잠깐 비활성화한다
  // (핸들러는 `el.setPointerCapture && ...` 로 감싸져 있어 null 이면 건너뛴다).
  function noCapture(el, fn) {
    const s = el.setPointerCapture, r = el.releasePointerCapture;
    el.setPointerCapture = null; el.releasePointerCapture = null;
    try { return fn(); } finally { el.setPointerCapture = s; el.releasePointerCapture = r; }
  }
  const pev = (type, x, y, buttons) => new PointerEvent(type, {
    bubbles: true, cancelable: true, composed: true, clientX: x, clientY: y,
    pointerId: 1, isPrimary: true, pointerType: 'mouse', button: 0, buttons: buttons ?? 1
  });
  function tap(el, x, y) {
    noCapture(el, () => {
      el.dispatchEvent(pev('pointerdown', x, y, 1));
      el.dispatchEvent(pev('pointerup', x, y, 0));
    });
  }
  const mid = r => [r.left + r.width / 2, r.top + r.height / 2];

  const waitFor = async (fn, ms = 20000, step = 120) => {
    const end = Date.now() + ms;
    while (Date.now() < end) { const v = fn(); if (v) return v; await sleep(step); }
    return null;
  };

  const sections = [];
  const sec = title => { const s = { title, rows: [] }; sections.push(s); return s; };
  const add = (s, name, ok, note) => s.rows.push({ name, ok: !!ok, note: note || '' });

  // ───────────────────────── 아카이빙 ─────────────────────────
  async function archive() {
    const S = sec('아카이빙 (archive)');
    show(ids.indexOf('archive'));
    await sleep(700);

    const stage = document.getElementById('arStage');
    const page = stage.closest('.archive-page');
    const items = [...stage.querySelectorAll('.ar-item')];
    const chips = [...page.querySelectorAll('.ar-chip')];
    const curEl = page.querySelector('.ar-cur');
    const titleEl = page.querySelector('.ar-title');
    const lb = document.querySelector('.lightbox');
    const lbImg = lb.querySelector('.lb-stage img');

    add(S, '장 수 42', items.length === 42, `${items.length}장`);
    add(S, '묶음 칩 6개', chips.length === 6, `${chips.length}개 · at=${chips.map(c => c.dataset.at).join(',')}`);

    const eager = items.filter(el => !el.querySelector('img[data-src]')).length;
    add(S, '진입 직후 붙은 장 (지연 나머지)', eager > 0 && eager < items.length,
        `즉시 ${eager}장 / 지연 ${items.length - eager}장`);

    const bad = { chip: [], title: [], count: [], neigh: [], over: [], img: [], zoom: [], vis: [], pop: [] };
    let dimOK = true;

    for (let i = 0; i < items.length; i++) {
      // 이웃 이미지가 붙을 시간을 준다
      await sleep(160);
      const c = items[i];

      if (curEl.textContent.trim() !== String(i + 1)) bad.count.push(`${i + 1}≠${curEl.textContent.trim()}`);
      if (titleEl.textContent.trim() !== (c.dataset.en || '').trim()) bad.title.push(`${i + 1}:${titleEl.textContent.trim()}`);

      // 칩: data-at 이 cur 이하인 마지막 칩이 켜져야 한다
      let want = 0;
      chips.forEach((ch, k) => { if (+ch.dataset.at <= i) want = k; });
      const on = chips.findIndex(ch => ch.classList.contains('on'));
      if (on !== want) bad.chip.push(`${i + 1}: ${on}≠${want}`);
      if (chips.filter(ch => ch.classList.contains('on')).length !== 1) bad.chip.push(`${i + 1}:다중선택`);

      // 보이는 장 = 최단거리 3칸 이내 → 7장. 무한 고리에서 양옆이 비면 여기서 걸린다.
      const vis = items.filter(el => getComputedStyle(el).visibility !== 'hidden');
      if (vis.length !== 7) bad.vis.push(`${i + 1}:${vis.length}장`);
      const L = items.length;
      for (const d of [-1, 1]) {
        const n = items[((i + d) % L + L) % L];
        const im = n.querySelector('img');
        if (getComputedStyle(n).visibility === 'hidden') bad.neigh.push(`${i + 1}${d > 0 ? '→' : '←'}숨김`);
        else if (!im || !im.naturalWidth) bad.neigh.push(`${i + 1}${d > 0 ? '→' : '←'}빈이미지`);
      }

      // 스테이지 밖으로 넘치는 장
      const sr = stage.getBoundingClientRect();
      for (const el of vis) {
        const r = el.getBoundingClientRect();
        if (r.left < sr.left - 1 || r.right > sr.right + 1 || r.top < sr.top - 1 || r.bottom > sr.bottom + 1) {
          bad.over.push(`${i + 1}:${items.indexOf(el) + 1}장`);
          break;
        }
      }

      if (c.style.getPropertyValue('--dim').trim() !== '0') dimOK = false;
      if (!c.classList.contains('is-center')) bad.vis.push(`${i + 1}:가운데표시없음`);

      const cim = c.querySelector('img');
      if (!cim || !cim.naturalWidth) bad.img.push(String(i + 1));

      // 탭 확대
      const r = c.getBoundingClientRect();
      tap(c, ...mid(r));
      await raf2();
      const opened = lb.classList.contains('open');
      const src = (lbImg.getAttribute('src') || '').split('/').pop();
      const want2 = ((cim && (cim.currentSrc || cim.src)) || '').split('/').pop();
      if (!opened || src !== want2) bad.zoom.push(`${i + 1}${opened ? ':다른이미지' : ':안열림'}`);
      dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
      await sleep(60);
      if (lb.classList.contains('open')) bad.zoom.push(`${i + 1}:안닫힘`);

      // 다음 장으로 (휠 = 갤러리 한 칸)
      const wasHidden = items.map(el => getComputedStyle(el).visibility === 'hidden');
      stage.dispatchEvent(new WheelEvent('wheel', { deltaY: 1, bubbles: true, cancelable: true }));
      // 새로 나타난 장은 제자리에 순간이동해야 한다. 미끄러져 오면 밝은 장이
      // 화면을 가로질러 튀어 보인다. 붙자마자와 전환이 끝난 뒤 자리를 비교한다.
      const born = items.filter((el, k) => wasHidden[k] && getComputedStyle(el).visibility !== 'hidden');
      const at0 = born.map(el => el.getBoundingClientRect().left);
      await sleep(340);
      born.forEach((el, k) => {
        if (Math.abs(el.getBoundingClientRect().left - at0[k]) > 8)
          bad.pop.push(`${i + 1}:${items.indexOf(el) + 1}장`);
      });
    }

    const loaded = items.filter(el => { const im = el.querySelector('img'); return im && im.naturalWidth > 0; }).length;
    const short = a => a.length ? a.slice(0, 6).join(' ') + (a.length > 6 ? ` 외 ${a.length - 6}` : '') : '';

    add(S, '42장 전부 실제로 붙음', loaded === items.length, `${loaded}/${items.length}장 로드`);
    add(S, 'n/42 카운터', !bad.count.length, short(bad.count));
    add(S, '칩 현재 묶음 표시', !bad.chip.length, short(bad.chip));
    add(S, '타이틀이 묶음 따라 바뀜', !bad.title.length, short(bad.title));
    add(S, '무한 고리 — 양옆이 늘 채워짐', !bad.neigh.length, short(bad.neigh));
    add(S, '보이는 장 7장 · 가운데 표시', !bad.vis.length, short(bad.vis));
    add(S, '가운데 장 어둡지 않음(--dim 0)', dimOK, '');
    add(S, '스테이지 밖으로 넘침 없음', !bad.over.length, short(bad.over));
    add(S, '가운데 이미지 로드', !bad.img.length, short(bad.img));
    add(S, '탭 확대 42장 전부', !bad.zoom.length, short(bad.zoom));
    add(S, '스와이프 — 새 장이 안 튐', !bad.pop.length, short(bad.pop));
    add(S, '한 바퀴 돌아 제자리', curEl.textContent.trim() === '1', `현재 ${curEl.textContent.trim()}`);
  }

  // ───────────────────────── 크레딧 ─────────────────────────
  async function credits() {
    const S = sec('크레딧 (credits)');
    const preloaded = !!window.NewtonLanyard;   // 유휴 시간에 미리 실행돼 있어야 한다
    const enter = Date.now();
    show(ids.indexOf('credits'));

    const slots = await waitFor(() => {
      const s = [...document.querySelectorAll('.cc3d-slot')];
      return s.length >= 5 && s.every(x => x.getBoundingClientRect().width) ? s : null;
    }, 40000);
    if (!slots) { add(S, '3D 카드 5장 마운트', false, '번들/캔버스가 안 떴다 (WebGL 확인)'); return; }
    const tCard = Date.now() - enter;
    const res = performance.getEntriesByType('resource');
    const pick = n => res.find(r => r.name.includes(n));
    const b = pick('lanyard.bundle.js'), g = pick('.glb');
    add(S, '도착 전에 번들이 준비됨', preloaded, preloaded ? '유휴 시간에 미리 실행됨' : '도착해서야 받기 시작 — 검은 화면이 길어진다');
    add(S, '들어가서 카드 뜰 때까지', tCard < 3000, `${(tCard / 1000).toFixed(1)}s (데스크톱 기준 — 태블릿은 훨씬 느리다)`);
    add(S, '번들 · glb 내려받기', true,
        `번들 ${b ? (b.transferSize / 1048576).toFixed(2) + 'MB/' + Math.round(b.duration) + 'ms' : '캐시'}` +
        ` · glb ${g ? (g.transferSize / 1048576).toFixed(2) + 'MB/' + Math.round(g.duration) + 'ms' : '캐시'}`);
    await sleep(1600);   // 줄이 중력으로 자리를 잡는 시간

    const page = document.querySelector('.credits-page');
    const host = document.querySelector('.lany3d-host');
    add(S, '3D 카드 5장 마운트', slots.length === 5, `${slots.length}장`);
    add(S, '슬롯 5개 전부 __band', slots.every(s => s.__band && ['start', 'move', 'end'].every(k => typeof s.__band[k] === 'function')),
        slots.map(s => (s.__band ? 'o' : 'x')).join(''));

    // band 호출 기록 — "놓였는지"는 이걸로 본다
    const log = [];
    slots.forEach((s, i) => {
      if (!s.__band) return;
      const b = s.__band;
      ['start', 'move', 'end'].forEach(k => {
        const f = b[k].bind(b);
        b[k] = (...a) => { log.push({ i, k, t: Date.now() }); return f(...a); };
      });
    });

    // SNS 링크는 진짜로 이동하면 안 된다 — 눌리는지만 본다
    document.addEventListener('click', e => { if (e.target.closest && e.target.closest('.cc-sns')) e.preventDefault(); }, true);

    // 앱과 같은 방식으로 어느 판이 잡히는지 고른다(겹치면 뒤에 그린 것이 이긴다)
    const pickAt = (x, y) => {
      const all = [...document.querySelectorAll('.cc3d-slot')];
      for (let i = all.length - 1; i >= 0; i--) {
        const r = all[i].getBoundingClientRect();
        if (r.width && x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) return all[i];
      }
      return null;
    };
    // 그 판만 잡히는 점을 찾는다(다른 카드가 덮고 있으면 그 자리는 피한다)
    const ownPoint = slot => {
      const r = slot.getBoundingClientRect();
      for (const fy of [0.5, 0.3, 0.7, 0.15, 0.85])
        for (const fx of [0.5, 0.25, 0.75, 0.1, 0.9]) {
          const x = r.left + r.width * fx, y = r.top + r.height * fy;
          if (pickAt(x, y) === slot) return [x, y];
        }
      return null;
    };

    const nameOf = el => { const n = el.querySelector('.cc-name'); return n ? n.textContent.replace(/\s+/g, ' ').trim() : '?'; };
    // 확대 카드는 .cc-inner 가 rotateY(180deg) 면 뒷면이다(m11 이 음수).
    const isBack = cc => new DOMMatrixReadOnly(getComputedStyle(cc.querySelector('.cc-inner')).transform).m11 < 0;
    const bad = { drag: [], own: [], zoom: [], back: [], flip: [], sns: [] };

    for (let i = 0; i < slots.length; i++) {
      const slot = slots[i];
      const who = nameOf(slot);

      // ── 드래그 후 반드시 놓이는지 ──
      let p = ownPoint(slot);
      if (!p) { bad.own.push(`${who}:가려짐`); continue; }
      noCapture(host, () => {
        host.dispatchEvent(pev('pointerdown', p[0], p[1], 1));
        for (let k = 1; k <= 6; k++) host.dispatchEvent(pev('pointermove', p[0] + k * 14, p[1] + k * 8, 1));
        host.dispatchEvent(pev('pointerup', p[0] + 6 * 14, p[1] + 6 * 8, 0));
      });
      const upAt = Date.now();
      await sleep(30);
      // 놓은 뒤 마우스가 지나가도 카드가 따라오면 안 된다
      for (let k = 0; k < 4; k++) { host.dispatchEvent(pev('pointermove', 40 + k * 60, 60 + k * 40, 0)); await sleep(40); }
      const stuck = log.filter(e => e.k === 'move' && e.t > upAt + 10);
      const ended = log.some(e => e.k === 'end' && e.t >= upAt - 5);
      if (stuck.length || !ended) bad.drag.push(`${who}${stuck.length ? ':마우스에붙음' : ':end없음'}`);
      log.length = 0;
      await sleep(900);   // 물리가 가라앉을 시간

      // ── 탭 → 자기 사람이 열리는지 ──
      p = ownPoint(slot);
      if (!p) { bad.own.push(`${who}:가려짐`); continue; }
      noCapture(host, () => {
        host.dispatchEvent(pev('pointerdown', p[0], p[1], 1));
        host.dispatchEvent(pev('pointerup', p[0], p[1], 0));
      });
      const zoom = document.querySelector('.cc-zoom');
      if (!zoom || !page.classList.contains('zoomed')) { bad.zoom.push(`${who}:안열림`); continue; }
      const clone = zoom.querySelector('.cc');
      if (nameOf(clone) !== who) bad.zoom.push(`${who}→${nameOf(clone)}`);

      // ── 뒷면이 먼저 뜨는지 (붙기 전에 flipped + no-anim → 도는 게 안 보인다) ──
      // 확대 카드는 opacity 가 아니라 rotateY + backface-visibility 로 뒤집힌다.
      if (!clone.classList.contains('flipped')) bad.back.push(who);
      if (!zoom.classList.contains('no-anim')) bad.back.push(`${who}:앞면에서돌아옴`);
      await raf2(); await raf2();
      if (!isBack(clone)) bad.back.push(`${who}:면반대`);
      // 실제로 한 면만 그려지는지. backface-visibility 만 믿으면 filter 걸린
      // 조상 때문에 두 면이 겹쳐 그려진다(태블릿에서 앞뒤가 섞여 보이던 것).
      const vis = ['.cc-front', '.cc-back'].filter(s => +getComputedStyle(clone.querySelector(s)).opacity > 0.01);
      if (vis.length !== 1 || vis[0] !== '.cc-back') bad.back.push(`${who}:두면겹침(${vis.join('+') || '없음'})`);

      // ── SNS 버튼이 눌리는지 (덮여 있지 않은지 · 눌러도 안 뒤집히는지) ──
      const sns = [...clone.querySelectorAll('.cc-sns')];
      if (!sns.length) bad.sns.push(`${who}:없음`);
      for (const a of sns) {
        const [x, y] = mid(a.getBoundingClientRect());
        const hit = document.elementFromPoint(x, y);
        if (!hit || !hit.closest('.cc-sns')) { bad.sns.push(`${who}:가려짐`); break; }
        if (!a.getAttribute('href')) { bad.sns.push(`${who}:href없음`); break; }
        const was = clone.classList.contains('flipped');
        a.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, clientX: x, clientY: y }));
        if (clone.classList.contains('flipped') !== was) { bad.sns.push(`${who}:눌러서뒤집힘`); break; }
      }

      // ── 플립이 도는지 (클래스만이 아니라 판이 실제로 돌아야 한다) ──
      // no-anim 은 rAF 로 벗겨진다. 창이 뒤에 깔리면 rAF 이 안 돌아 영영 남는다 —
      // 그때는 트랜지션 유무를 물어봐야 의미가 없으니 그 항목만 건너뛴다.
      const animReady = await waitFor(() => !zoom.classList.contains('no-anim'), 1500, 60);
      const before = clone.classList.contains('flipped');
      clone.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
      await sleep(120);
      const inner = clone.querySelector('.cc-inner');
      const moving = !animReady || getComputedStyle(inner).transitionDuration !== '0s';
      await sleep(760);   // .62s 트랜지션이 끝날 때까지
      if (clone.classList.contains('flipped') === before) bad.flip.push(`${who}:안뒤집힘`);
      else if (isBack(clone) === before) bad.flip.push(`${who}:판이안돎`);
      else if (!moving) bad.flip.push(`${who}:트랜지션없음`);

      // 닫기 — 실제 닫기 버튼으로
      const closeBtn = page.querySelector('.cc-close');
      if (closeBtn) closeBtn.click(); else page.__closeZoom && page.__closeZoom();
      await sleep(400);
      if (document.querySelector('.cc-zoom')) bad.zoom.push(`${who}:안닫힘`);
      await sleep(400);
    }

    const short = a => a.length ? [...new Set(a)].join(' ') : '';
    add(S, '드래그 후 반드시 놓임', !bad.drag.length, short(bad.drag));
    add(S, '카드별 자기 사람이 열림', !bad.zoom.length && !bad.own.length, short([...bad.zoom, ...bad.own]));
    add(S, '확대 시 뒷면이 먼저', !bad.back.length, short(bad.back));
    add(S, '플립이 돎', !bad.flip.length, short(bad.flip));
    add(S, 'SNS 버튼이 눌림', !bad.sns.length, short(bad.sns));
  }

  // ───────────── 가로 넘침 (토글 안 이미지가 잘리는지) ─────────────
  // 22장을 돌며 토글을 전부 펼치고, 책 밖으로 삐져나가는 요소를 잡는다.
  async function overflow() {
    const S = sec('가로 넘침 — 토글 펼친 상태');
    const worst = [];
    for (let i = 0; i < pages.length; i++) {
      show(i);
      await sleep(260);
      const p = pages[i];
      p.querySelectorAll('details').forEach(d => { d.open = true; });
      await sleep(320);
      // 잘리는 곳은 "책 밖"이 아니라 가장 가까운 클리핑 조상이다.
      // 가로 스크롤이 되는 조상(표 감싸개 등)은 넘쳐도 정상이니 제외한다.
      const clipper = el => {
        for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
          const ox = getComputedStyle(a).overflowX;
          if (ox === 'hidden' || ox === 'clip') return a;
          // overflow-y 만 auto 로 줘도 overflow-x 가 auto 로 계산된다. 진짜로 가로
          // 스크롤이 되는지(scrollWidth) 봐야 한다 — 아니면 그냥 잘리는 것이다.
          if (ox === 'auto' || ox === 'scroll') return a.scrollWidth > a.clientWidth + 2 ? null : a;
        }
        return null;
      };
      p.querySelectorAll('figure.figure, img, table, .finding').forEach(el => {
        // .fade-track 은 가로 스트립을 밀어 넘기는 캐러셀이다 — 밖에 있는 게 정상
        if (el.closest('.fade-track')) return;
        const r = el.getBoundingClientRect();
        if (!r.width) return;
        const c = clipper(el);
        if (!c) return;
        const cr = c.getBoundingClientRect();
        const over = Math.max(cr.left - r.left, r.right - cr.right);
        if (over > 1) worst.push({ page: ids[i], el: el.tagName.toLowerCase() +
          (el.getAttribute('src') ? ':' + el.getAttribute('src').split('/').pop() : '.' + (el.className || '').split(' ')[0]),
          by: '.' + (c.className || c.tagName).split(' ')[0], over: Math.round(over) });
      });
      p.querySelectorAll('details').forEach(d => { d.open = false; });
    }
    worst.sort((a, b) => b.over - a.over);
    add(S, '책 밖으로 삐져나가는 요소', !worst.length,
        worst.slice(0, 10).map(w => `${w.page}/${w.el} +${w.over}px(${w.by})`).join(' · ') || '없음');
    return worst;
  }

  (async function run() {
    try {
      if (document.readyState !== 'complete') await new Promise(r => addEventListener('load', r));
      await sleep(800);
      const q = new URLSearchParams(location.search);
      const only = q.get('only');
      if (only === 'detail') {
        // 한 장의 모든 그림을 있는 그대로 잰다 — 원본 비율, 그려진 상자, 잘리는 조상.
        const S = sec('상세 실측 — ' + q.get('page'));
        show(ids.indexOf(q.get('page')));
        await sleep(400);
        const p = pages[ids.indexOf(q.get('page'))];
        p.querySelectorAll('details').forEach(d => { d.open = true; });
        await sleep(600);
        add(S, '창 크기', true, `${innerWidth}×${innerHeight} · 책 ${Math.round(book.getBoundingClientRect().width)}px`);
        p.querySelectorAll('figure.figure img').forEach(im => {
          const r = im.getBoundingClientRect();
          let c = im.parentElement, cr = null, cn = '';
          for (; c && c !== document.body; c = c.parentElement) {
            const ox = getComputedStyle(c).overflowX;
            if (ox === 'hidden' || ox === 'clip') { cr = c.getBoundingClientRect(); cn = '.' + (c.className || c.tagName).split(' ')[0]; break; }
            if (ox === 'auto' || ox === 'scroll') break;
          }
          const cut = cr ? Math.round(Math.max(cr.left - r.left, r.right - cr.right)) : 0;
          const st = getComputedStyle(im);
          // 잘리진 않아도 토글 카드 밖으로 삐져나오면 "좌우가 초과"로 보인다
          const card = im.closest('.finding') || im.closest('.toggle-body');
          if (card) {
            const kr = card.getBoundingClientRect();
            add(S, '  ↳ 카드 대비', r.left >= kr.left - 1 && r.right <= kr.right + 1,
                `카드 ${Math.round(kr.width)}px(${Math.round(kr.left)}~${Math.round(kr.right)})` +
                ` · 그림 ${Math.round(r.width)}px(${Math.round(r.left)}~${Math.round(r.right)})` +
                ` · 왼쪽 ${Math.round(kr.left - r.left)}px 오른쪽 ${Math.round(r.right - kr.right)}px 초과`);
          }
          add(S, (im.getAttribute('src') || '').split('/').pop(), cut <= 1,
              `원본 ${im.naturalWidth}×${im.naturalHeight} · 상자 ${Math.round(r.width)}×${Math.round(r.height)}` +
              ` · fit:${st.objectFit} ratio:${st.aspectRatio}` +
              (cr ? ` · ${cn} 기준 ${cut > 1 ? '잘림 ' + cut + 'px' : '안 잘림'}` : ' · 자르는 조상 없음'));
        });
      }
      else if (only === 'mobile') {
        // 모바일 폭에서만 도는 것들 — 사진 자리에 들어간 영상이 진짜로 재생되는지.
        const S = sec('모바일 (' + innerWidth + 'px)');
        add(S, '모바일 레이아웃', matchMedia('(max-width:640px)').matches,
            matchMedia('(max-width:640px)').matches ? '' : '창을 640px 이하로 줄여야 한다');
        show(ids.indexOf('sec-04'));
        await sleep(900);
        const p = pages[ids.indexOf('sec-04')];
        const v = p.querySelector('video.media');
        add(S, '사진이 영상으로 바뀜', !!v, v ? v.getAttribute('src') : 'video.media 없음');
        if (v) {
          const pauses = [];
          v.addEventListener('pause', () => pauses.push(new Error().stack.split('\n').slice(1, 4).join(' | ')));
          await waitFor(() => v.readyState >= 2, 8000);
          const t0v = v.currentTime;
          await sleep(1200);
          if (v.paused) add(S, '멈춘 이유', false, pauses.join(' // ').slice(0, 300) || '이벤트 없음(처음부터 재생 안 됨)');
          const r = v.getBoundingClientRect();
          add(S, '실제로 재생됨', v.currentTime > t0v && !v.paused,
              `${v.currentTime.toFixed(1)}s · ${v.videoWidth}×${v.videoHeight} · paused=${v.paused}`);
          add(S, '상자가 16:9 로 들어감', Math.abs(r.width / r.height - 16 / 9) < 0.05,
              `${Math.round(r.width)}×${Math.round(r.height)} (${(r.width / r.height).toFixed(2)})`);
          add(S, '남은 사진 자리도 정상', [...document.querySelectorAll('img[data-msrc]')].every(im => im.src.includes(im.dataset.msrc)),
              [...document.querySelectorAll('img[data-msrc]')].length + '개');
          show(ids.indexOf('sec-01'));
          await sleep(700);
          add(S, '장을 떠나면 멈춤', v.paused, `paused=${v.paused}`);
        }
      }
      else if (only === 'overflow') { await overflow(); }
      else { await archive(); await credits(); }
    } catch (e) {
      sections.push({ title: '검수 중단', rows: [{ name: '예외', ok: false, note: String(e && e.stack || e) }] });
    }
    const E = sec('공통');
    add(E, '콘솔 에러 0', errs.length === 0, errs.slice(0, 5).join(' | '));
    const body = JSON.stringify({ ms: Date.now() - t0, sections, errors: errs }, null, 1);
    fetch('/REPORT', { method: 'POST', body });
    document.title = '검수 끝';
  })();
})();
