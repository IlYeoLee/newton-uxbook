// 마지막 장 크레딧 카드 — three.js 3D 버전.
// reactbits Lanyard 가 React + rapier 로 하는 것을, 이 책은 번들러가 없어서
// three 만 로컬로 쓰고 물리는 베를레 로프로 직접 돌린다.
// card.glb 의 UV 아틀라스는 왼쪽 절반이 앞면, 오른쪽 절반이 뒷면이다.
import * as THREE from '../vendor/three.module.js';
import { GLTFLoader } from '../vendor/GLTFLoader.js';

const FRONT_UV = { x: 0, y: 0, w: 0.5, h: 0.755 };
const BACK_UV = { x: 0.5, y: 0, w: 0.5, h: 0.757 };

const CARD_W = 1.6, CARD_H = 2.25;      // card.glb 의 콜라이더 기준 크기
const GAP = 0.34;
const SEG = 12, ITER = 8, GRAV = 0.0055, DAMP = 0.92;

export async function initLanyard3D(stage, people) {
  const canvas = document.createElement('canvas');
  canvas.className = 'lany3d';
  stage.appendChild(canvas);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setClearAlpha(0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(20, 1, 0.1, 200);
  camera.position.set(0, 0, 30);

  scene.add(new THREE.AmbientLight(0xffffff, Math.PI * 0.55));
  // reactbits 의 Lightformer 배치를 방향광으로 옮긴 것 — 표면에 빛이 흐르게 한다
  [[-10, 2, 14, 2.4], [10, 4, 10, 1.6], [0, -6, 8, 1.0], [0, 8, -6, 0.8]]
    .forEach(([x, y, z, i]) => {
      const l = new THREE.DirectionalLight(0xffffff, i);
      l.position.set(x, y, z);
      scene.add(l);
    });

  const gltf = await new GLTFLoader().loadAsync('assets/card.glb');
  const src = {};
  gltf.scene.traverse(o => { if (o.isMesh) src[o.name] = o; });
  const cardMesh = src.card || Object.values(src)[0];
  const baseMap = cardMesh.material.map;

  const bandTex = await new THREE.TextureLoader().loadAsync('assets/lanyard.png');
  bandTex.wrapS = bandTex.wrapT = THREE.RepeatWrapping;

  // 사람마다 앞/뒤 이미지를 아틀라스 절반씩에 굽는다
  async function atlasFor(p) {
    const [front, back] = await Promise.all([loadImg(p.front), loadImg(p.back)]);
    const W = baseMap.image.width, H = baseMap.image.height;
    const cv = document.createElement('canvas');
    cv.width = W; cv.height = H;
    const ctx = cv.getContext('2d');
    ctx.drawImage(baseMap.image, 0, 0, W, H);
    const fit = (img, r) => {
      const rx = r.x * W, ry = r.y * H, rw = r.w * W, rh = r.h * H;
      const s = Math.max(rw / img.width, rh / img.height);
      const dw = img.width * s, dh = img.height * s;
      ctx.save(); ctx.beginPath(); ctx.rect(rx, ry, rw, rh); ctx.clip();
      ctx.drawImage(img, rx + (rw - dw) / 2, ry + (rh - dh) / 2, dw, dh);
      ctx.restore();
    };
    if (front) fit(front, FRONT_UV);
    if (back) fit(back, BACK_UV);
    const t = new THREE.CanvasTexture(cv);
    t.colorSpace = THREE.SRGBColorSpace;
    t.flipY = baseMap.flipY;
    t.anisotropy = 16;
    return t;
  }
  const loadImg = s => new Promise(res => {
    if (!s) return res(null);
    const i = new Image(); i.crossOrigin = 'anonymous';
    i.onload = () => res(i); i.onerror = () => res(null); i.src = s;
  });

  const total = people.length * CARD_W + (people.length - 1) * GAP;
  const items = [];

  for (let k = 0; k < people.length; k++) {
    const map = await atlasFor(people[k]);
    const group = new THREE.Group();
    const mesh = new THREE.Mesh(cardMesh.geometry, new THREE.MeshPhysicalMaterial({
      map, clearcoat: 1, clearcoatRoughness: 0.15, roughness: 0.9, metalness: 0.8,
    }));
    group.add(mesh);
    ['clip', 'clamp'].forEach(n => {
      if (!src[n]) return;
      group.add(new THREE.Mesh(src[n].geometry, new THREE.MeshPhysicalMaterial({
        color: 0xb8bec4, metalness: 1, roughness: 0.3,
      })));
    });
    scene.add(group);

    const band = new THREE.Mesh(
      new THREE.PlaneGeometry(1, 1, 1, SEG),
      new THREE.MeshBasicMaterial({ map: bandTex, transparent: true, side: THREE.DoubleSide })
    );
    scene.add(band);

    const anchorX = -total / 2 + CARD_W / 2 + k * (CARD_W + GAP);
    items.push({ group, band, anchorX, pts: [], hang: people[k].hang ?? 0.28, phase: k * 1.73 });
  }

  function resize() {
    const r = stage.getBoundingClientRect();
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.setSize(r.width, r.height, false);
    camera.aspect = r.width / r.height;
    camera.updateProjectionMatrix();
    // 카드 5장이 가로로 다 들어오도록 카메라를 뒤로 뺀다
    const need = total * 1.18;
    const fovH = 2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2) * camera.aspect);
    camera.position.z = (need / 2) / Math.tan(fovH / 2);
  }
  resize();
  addEventListener('resize', resize);

  // 로프: 앵커에서 카드 위쪽까지, 세그먼트 등간격
  items.forEach(it => {
    const topY = 6.2;
    const len = (topY - CARD_H / 2 - it.hang * 6) / SEG;
    it.len = len;
    it.anchorY = topY;
    for (let i = 0; i <= SEG; i++) {
      const p = { x: it.anchorX, y: topY - i * len, px: it.anchorX, py: topY - i * len };
      it.pts.push(p);
    }
  });

  const clock = new THREE.Clock();
  function frame() {
    const t = clock.getElapsedTime();
    for (const it of items) {
      const gust = Math.sin(t * 0.62 + it.phase) * 0.9 + Math.sin(t * 1.73 + it.phase * 1.6) * 0.32;
      for (let i = 0; i < it.pts.length; i++) {
        const p = it.pts[i];
        const vx = (p.x - p.px) * DAMP, vy = (p.y - p.py) * DAMP;
        p.px = p.x; p.py = p.y;
        p.x += vx + gust * 0.0011 * (i / SEG);
        p.y += vy - GRAV;
      }
      for (let k = 0; k < ITER; k++) {
        it.pts[0].x = it.anchorX; it.pts[0].y = it.anchorY;
        for (let i = 0; i < SEG; i++) {
          const a = it.pts[i], b = it.pts[i + 1];
          const dx = b.x - a.x, dy = b.y - a.y;
          const d = Math.hypot(dx, dy) || 1e-5;
          const f = (d - it.len) / d * 0.5;
          if (i > 0) { a.x += dx * f; a.y += dy * f; }
          b.x -= dx * f; b.y -= dy * f;
        }
      }
      const end = it.pts[SEG], prev = it.pts[SEG - 1];
      it.group.position.set(end.x, end.y - CARD_H / 2, 0);
      it.group.rotation.z = Math.atan2(end.x - prev.x, -(end.y - prev.y));
      updateBand(it);
    }
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }

  const BAND_W = 0.16;
  function updateBand(it) {
    const pos = it.band.geometry.attributes.position;
    for (let i = 0; i <= SEG; i++) {
      const p = it.pts[i];
      const a = it.pts[Math.max(0, i - 1)], b = it.pts[Math.min(SEG, i + 1)];
      const tx = b.x - a.x, ty = b.y - a.y;
      const m = Math.hypot(tx, ty) || 1e-5;
      const nx = -ty / m * BAND_W, ny = tx / m * BAND_W;
      pos.setXYZ(i * 2, p.x - nx, p.y - ny, 0);
      pos.setXYZ(i * 2 + 1, p.x + nx, p.y + ny, 0);
    }
    pos.needsUpdate = true;
    it.band.geometry.computeBoundingSphere();
  }

  requestAnimationFrame(frame);
  return { scene, camera, renderer, items };
}
