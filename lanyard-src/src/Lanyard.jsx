/* eslint-disable react/no-unknown-property */
// reactbits Lanyard (JS-CSS) 원본을 이 책에 맞게 확장한 것.
// 원본과 달라진 점은 세 가지뿐이고, 물리·재질·조명은 원본 그대로 둔다.
//   1) Band 가 anchor 를 받아 한 Canvas 안에 다섯 장이 나란히 매달린다
//   2) 카드를 누르면(끌지 않고) 확대 — 카메라 앞으로 kinematic 이동
//   3) 확대 중 한 번 더 누르면 Y축 180° 회전으로 뒷면
import { Suspense, useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, extend, useFrame, useThree } from '@react-three/fiber';
import { useGLTF, useTexture, Environment, Lightformer, Html } from '@react-three/drei';
import { BallCollider, CuboidCollider, Physics, RigidBody, useRopeJoint, useSphericalJoint } from '@react-three/rapier';
import { MeshLineGeometry, MeshLineMaterial } from 'meshline';

import cardGLB from './card.glb';
import lanyard from './lanyard.png';

import * as THREE from 'three';
import './Lanyard.css';

extend({ MeshLineGeometry, MeshLineMaterial });

export default function Lanyard({
  people = [],
  position = [0, 0, 20],
  gravity = [0, -40, 0],
  fov = 20,
  transparent = true,
  imageFit = 'cover',
  lanyardImage = null,
  lanyardWidth = 1,
  gap = 2.5,
  selected = null,
  flipped = false,
  onSelect = () => {}
}) {
  const [isMobile, setIsMobile] = useState(() => typeof window !== 'undefined' && window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 카드가 매달리는 x 좌표. 원본 Band 는 앵커에서 오른쪽으로 2 만큼 떨어진 곳에
  // 카드가 오므로, 그만큼 빼고 전체를 가운데 정렬한다.
  const anchors = useMemo(() => {
    const n = people.length || 1;
    const span = (n - 1) * gap;
    return people.map((_, i) => -span / 2 + i * gap);
  }, [people, gap]);

  return (
    <div className="lanyard-wrapper">
      <Canvas
        camera={{ position: position, fov: fov }}
        dpr={[1, isMobile ? 1.5 : 2]}
        gl={{ alpha: transparent }}
        onCreated={({ gl }) => gl.setClearColor(new THREE.Color(0x000000), transparent ? 0 : 1)}
      >
        <ambientLight intensity={Math.PI} />
        <Suspense fallback={null}>
        <Physics gravity={gravity} timeStep={isMobile ? 1 / 30 : 1 / 60}>
          {people.map((p, i) => (
            <Band
              key={i}
              index={i}
              anchorX={anchors[i]}
              hangY={p.hangY ?? 4}
              isMobile={isMobile}
              cardEl={p.el}
              frontImage={p.front}
              backImage={p.back}
              imageFit={imageFit}
              lanyardImage={lanyardImage}
              lanyardWidth={lanyardWidth}
              zoomed={selected === i}
              dimmed={selected !== null && selected !== i}
              flipped={selected === i && flipped}
              onSelect={onSelect}
            />
          ))}
        </Physics>
        </Suspense>
        <Environment blur={0.75}>
          <Lightformer intensity={2} color="white" position={[0, -1, 5]} rotation={[0, 0, Math.PI / 3]} scale={[100, 0.1, 1]} />
          <Lightformer intensity={3} color="white" position={[-1, -1, 1]} rotation={[0, 0, Math.PI / 3]} scale={[100, 0.1, 1]} />
          <Lightformer intensity={3} color="white" position={[1, 1, 1]} rotation={[0, 0, Math.PI / 3]} scale={[100, 0.1, 1]} />
          <Lightformer intensity={10} color="white" position={[-10, 0, 14]} rotation={[0, Math.PI / 2, Math.PI / 3]} scale={[100, 10, 1]} />
        </Environment>
      </Canvas>
    </div>
  );
}

function Band({
  maxSpeed = 50,
  minSpeed = 0,
  isMobile = false,
  index = 0,
  anchorX = 0,
  hangY = 4,
  cardEl = null,
  frontImage = null,
  backImage = null,
  imageFit = 'cover',
  lanyardImage = null,
  lanyardWidth = 1,
  zoomed = false,
  dimmed = false,
  flipped = false,
  onSelect = () => {}
}) {
  const band = useRef(),
    fixed = useRef(),
    j1 = useRef(),
    j2 = useRef(),
    j3 = useRef(),
    card = useRef();
  const vec = new THREE.Vector3(),
    ang = new THREE.Vector3(),
    rot = new THREE.Vector3(),
    dir = new THREE.Vector3();
  const segmentProps = { type: 'dynamic', canSleep: true, colliders: false, angularDamping: 13, linearDamping: 13 };
  const { nodes, materials } = useGLTF(cardGLB);
  const texture = useTexture(lanyardImage || lanyard);
  const { camera } = useThree();
  const slot = useRef();
  const manual = useRef(null);   // DOM 판이 직접 미는 동안의 포인터(NDC)
  // .cc 를 통째로 복제해 넣는다. 원본은 .lany 안에서 숨은 채 남아 있어
  // 예전 CSS-3D 루프가 계속 돌아도 화면에 영향을 주지 않는다.
  useEffect(() => {
    if (!cardEl) return;
    // drei 의 Html 은 자식을 포털로 나중에 붙인다. 첫 실행 때 slot.current 가
    // 아직 없어서 복제본이 영영 안 들어가는 일이 있었다. 붙을 때까지 기다린다.
    let raf = 0, clone = null;
    const put = () => {
      if (!slot.current) { raf = requestAnimationFrame(put); return; }
      if (slot.current._cc) return;
      clone = cardEl.cloneNode(true);
      clone.removeAttribute("style");
      clone.classList.remove("grabbing", "flipped");
      slot.current.appendChild(clone);
      slot.current._cc = clone;
      // 이 판이 곧 이 카드다. 판이 자기 물리를 직접 민다(레이캐스트를 안 탄다).
      slot.current.__band = {
        start: (nx, ny) => { manual.current = { x: nx, y: ny }; drag(new THREE.Vector3()); },
        move:  (nx, ny) => { if (manual.current) manual.current = { x: nx, y: ny }; },
        end:   () => { manual.current = null; drag(false); }
      };
    };
    put();
    return () => { cancelAnimationFrame(raf); if (clone) clone.remove(); };
  }, [cardEl]);
  // 앞뒤 뒤집기는 메시를 돌리지 않고 기존 .cc.flipped CSS 규칙에 맡긴다.
  useEffect(() => {
    const cc = slot.current && slot.current._cc;
    if (cc) cc.classList.toggle("flipped", !!flipped);
  }, [flipped]);

  const [curve] = useState(
    () => new THREE.CatmullRomCurve3([new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()])
  );
  const [dragged, drag] = useState(false);
  const [hovered, hover] = useState(false);
  // 끌었는지 눌렀는지 구분한다. 끈 거리가 짧으면 "탭"으로 보고 확대한다.
  const moved = useRef(0);

  useRopeJoint(fixed, j1, [[0, 0, 0], [0, 0, 0], 0.7]);
  useRopeJoint(j1, j2, [[0, 0, 0], [0, 0, 0], 0.7]);
  useRopeJoint(j2, j3, [[0, 0, 0], [0, 0, 0], 0.7]);
  useSphericalJoint(j3, card, [
    [0, 0, 0],
    [0, 2.0, 0]
  ]);

  useEffect(() => {
    if (hovered) {
      document.body.style.cursor = dragged ? 'grabbing' : 'pointer';
      return () => void (document.body.style.cursor = 'auto');
    }
  }, [hovered, dragged]);

  // 확대 목표 자리 — 카메라 앞 고정 거리. 화면 가운데에 정면으로 선다.
  const zoomTarget = useMemo(() => new THREE.Vector3(), []);
  const zoomQuat = useMemo(() => new THREE.Quaternion(), []);
  const tmpQ = useMemo(() => new THREE.Quaternion(), []);

  useFrame((state, delta) => {
    if (dragged && !zoomed) {
      const pt = manual.current || state.pointer;
      vec.set(pt.x, pt.y, 0.5).unproject(state.camera);
      dir.copy(vec).sub(state.camera.position).normalize();
      vec.add(dir.multiplyScalar(state.camera.position.length()));
      [card, j1, j2, j3, fixed].forEach(ref => ref.current?.wakeUp());
      card.current?.setNextKinematicTranslation({ x: vec.x - dragged.x, y: vec.y - dragged.y, z: vec.z - dragged.z });
    }


    if (fixed.current) {
      [j1, j2].forEach(ref => {
        if (!ref.current.lerped) ref.current.lerped = new THREE.Vector3().copy(ref.current.translation());
        const clampedDistance = Math.max(0.1, Math.min(1, ref.current.lerped.distanceTo(ref.current.translation())));
        ref.current.lerped.lerp(ref.current.translation(), delta * (minSpeed + clampedDistance * (maxSpeed - minSpeed)));
      });
      curve.points[0].copy(j3.current.translation());
      curve.points[1].copy(j2.current.lerped);
      curve.points[2].copy(j1.current.lerped);
      curve.points[3].copy(fixed.current.translation());
      band.current.geometry.setPoints(curve.getPoints(isMobile ? 16 : 32));
      ang.copy(card.current.angvel());
      rot.copy(card.current.rotation());
      card.current.setAngvel({ x: ang.x, y: ang.y - rot.y * 0.25, z: ang.z });

      // 아주 약한 바람. 카드마다 위상을 달리해 다섯 장이 한 몸처럼 움직이지 않게 한다.
      if (!dragged && !zoomed) {
        const t = state.clock.elapsedTime;
        const w = Math.sin(t * 0.55 + index * 1.73) * 0.004 + Math.sin(t * 1.31 + index * 2.4) * 0.0015;
        j2.current.applyImpulse({ x: w, y: 0, z: w * 0.35 }, true);
      }
    }
  });

  curve.curveType = 'chordal';
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;

  const cardType = dragged ? 'kinematicPosition' : 'dynamic';

  return (
    <>
      <group position={[anchorX, hangY, 0]}>
        <RigidBody ref={fixed} {...segmentProps} type="fixed" />
        <RigidBody position={[0, -0.5, 0]} ref={j1} {...segmentProps}>
          <BallCollider args={[0.1]} />
        </RigidBody>
        <RigidBody position={[0, -1, 0]} ref={j2} {...segmentProps}>
          <BallCollider args={[0.1]} />
        </RigidBody>
        <RigidBody position={[0, -1.5, 0]} ref={j3} {...segmentProps}>
          <BallCollider args={[0.1]} />
        </RigidBody>
        <RigidBody position={[0, -2, 0]} ref={card} {...segmentProps} type={cardType}>
          <CuboidCollider args={[1.067, 1.500, 0.02]} />
          <group
            scale={3}
            position={[0, -1.6, -0.05]}
            onPointerOver={() => hover(true)}
            onPointerOut={() => hover(false)}
            onPointerUp={e => {
              e.target.releasePointerCapture(e.pointerId);
              drag(false);
              if (moved.current < 8) onSelect(index, cardEl);   // 끌지 않았으면 탭
            }}
            onPointerMove={e => {
              if (dragged) moved.current += Math.abs(e.movementX || 0) + Math.abs(e.movementY || 0);
            }}
            onPointerDown={e => {
              e.target.setPointerCapture(e.pointerId);
              moved.current = 0;
              if (!zoomed)
                drag(new THREE.Vector3().copy(e.point).sub(vec.copy(card.current.translation())));
            }}
          >
            <mesh geometry={nodes.card.geometry} visible={false}>
              <meshPhysicalMaterial
                color="#101215"
                depthWrite={false}
                clearcoat={isMobile ? 0 : 0.35}
                clearcoatRoughness={0.15}
                roughness={0.62}
                metalness={0.32}
                transparent
                opacity={0}
              />
            </mesh>
            {/* 터치·드래그 판정면. 보이는 카드와 크기가 정확히 같다. */}
            <mesh position={[0, 0.533, 0.03]}>
              <planeGeometry args={[0.711, 1.0]} />
              <meshBasicMaterial transparent opacity={0} depthWrite={false} />
            </mesh>
            <Html transform position={[0, 0.533, 0.0283]} rotation={[0, Math.PI, 0]} scale={0.09481} zIndexRange={[8, 0]}
                  style={{ pointerEvents: "none" }}>
              <div className="cc3d-slot" ref={slot} />
            </Html>
            <mesh geometry={nodes.clip.geometry} material={materials.metal} material-roughness={0.3} />
            <mesh geometry={nodes.clamp.geometry} material={materials.metal} />
          </group>
        </RigidBody>
      </group>
      <mesh ref={band}>
        <meshLineGeometry />
        <meshLineMaterial
          color="white"
          depthTest={false}
          resolution={isMobile ? [1000, 2000] : [1000, 1000]}
          useMap
          map={texture}
          repeat={[-4, 1]}
          lineWidth={lanyardWidth}
          transparent
          opacity={dimmed ? 0.28 : 1}
        />
      </mesh>
    </>
  );
}
