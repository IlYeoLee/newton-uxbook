// 정적 책에서 <script src> 하나로 부르는 진입점.
// window.NewtonLanyard.mount(el, { people, onZoom }) 로 붙인다.
import { useState } from 'react';
import { createRoot } from 'react-dom/client';
import Lanyard from './Lanyard.jsx';
import './Lanyard.css';

function App({ people, onZoom, apiRef }) {
  const [selected, setSelected] = useState(null);
  const [flipped, setFlipped] = useState(false);

  // 카드를 누르면: 처음이면 확대, 확대 중 같은 카드면 앞뒤 뒤집기
  const handleSelect = (i, el) => {
    setSelected(prev => {
      if (prev === i) { setFlipped(f => !f); return prev; }
      setFlipped(false);
      onZoom(i, el);
      return i;
    });
  };
  const close = () => { setSelected(null); setFlipped(false); onZoom(null); };
  apiRef.close = close;

  // 중력은 Lanyard 의 기본값(-40)을 그대로 쓴다. 여기서 -18 로 덮고 있던 탓에
  // 날린 카드가 물속처럼 내려왔고, 기본값만 고쳐서는 아무것도 안 바뀌었다.
  return (
    <Lanyard
      people={people}
      position={[0, 0, 24]}
      imageFit="cover"
      lanyardImage={people.bandImage}
      lanyardWidth={1}
      selected={selected}
      flipped={flipped}
      onSelect={handleSelect}
    />
  );
}

export function mount(el, { people = [], bandImage = null, onZoom = () => {} } = {}) {
  // 피그마 49:1445 처럼 카드 높이를 엇갈리게 건다. 다섯 장이 한 줄로 서면
  // 목걸이가 아니라 진열대처럼 보인다.
  const HANG = [4.90, 4.20, 4.85, 4.55, 4.15];
  const list = people.map((p, i) => ({ ...p, hangY: p.hangY ?? HANG[i % HANG.length] }));
  list.bandImage = bandImage;
  const api = {};
  const root = createRoot(el);
  root.render(<App people={list} onZoom={onZoom} apiRef={api} />);
  return {
    close: () => api.close && api.close(),
    unmount: () => root.unmount()
  };
}
