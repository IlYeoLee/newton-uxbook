// 정적 책에서 부를 수 있게 감싼 진입점.
// window.NewtonLanyard.mount(el, props) 로 붙인다.
import React from 'react';
import { createRoot } from 'react-dom/client';
import Lanyard from './Lanyard.jsx';
import './Lanyard.css';

export function mount(el, props = {}) {
  const root = createRoot(el);
  root.render(<Lanyard {...props} />);
  return () => root.unmount();
}
