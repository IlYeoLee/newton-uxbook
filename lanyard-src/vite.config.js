import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// 정적 책에서 <script src> 하나로 불러 쓸 수 있게 IIFE 한 덩어리로 뽑는다.
export default defineConfig({
  plugins: [react()],
  // 라이브러리 모드로 뽑으면 vite 가 이걸 안 넣어줘서 브라우저에서 process 가 없다
  define: { 'process.env.NODE_ENV': JSON.stringify('production'), 'process.env': '{}' },
  assetsInclude: ['**/*.glb'],
  build: {
    outDir: '../assets',
    emptyOutDir: false,
    lib: { entry: 'src/mount.jsx', name: 'NewtonLanyard', formats: ['iife'], fileName: () => 'lanyard.bundle.js' },
  },
});
