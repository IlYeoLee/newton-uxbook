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
  const handleSelect = i => {
    setSelected(prev => {
      if (prev === i) { setFlipped(f => !f); return prev; }
      setFlipped(false);
      onZoom(i);
      return i;
    });
  };
  const close = () => { setSelected(null); setFlipped(false); onZoom(null); };
  apiRef.close = close;

  return (
    <Lanyard
      people={people}
      position={[0, 0, 24]}
      gravity={[0, -40, 0]}
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
  const list = people.slice();
  list.bandImage = bandImage;
  const api = {};
  const root = createRoot(el);
  root.render(<App people={list} onZoom={onZoom} apiRef={api} />);
  return {
    close: () => api.close && api.close(),
    unmount: () => root.unmount()
  };
}
