// 전수 검수용 서버. 정적 파일 + /_audit.html(감사 스크립트를 주입한 index.html)
// + POST /REPORT(결과 수신 → 표로 출력하고 종료).
// 쓰는 법:  node probe/serve.js   그리고 실제 크롬으로 http://127.0.0.1:8833/_audit.html
const http = require('http'), fs = require('fs'), path = require('path');

const ROOT = path.join(__dirname, '..');
const PORT = +(process.env.PORT || process.argv[2] || 8877);
const MIME = {'.html':'text/html;charset=utf-8','.js':'text/javascript;charset=utf-8',
  '.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg',
  '.webp':'image/webp','.mp4':'video/mp4','.glb':'model/gltf-binary','.woff2':'font/woff2',
  '.svg':'image/svg+xml','.ico':'image/x-icon'};

const srv = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  if (!/\.(webp|png|jpg|woff2|svg)$/i.test(url)) console.log('  ←', req.method, url);

  if (req.method === 'POST' && url === '/REPORT') {
    let body = '';
    req.on('data', c => body += c);
    req.on('end', () => {
      res.writeHead(200, {'Access-Control-Allow-Origin':'*'}); res.end('ok');
      fs.writeFileSync(path.join(__dirname, 'report.json'), body);
      try { print(JSON.parse(body)); } catch (e) { console.log(body); }
      srv.close(); process.exit(0);
    });
    return;
  }

  // 감사 스크립트를 끼운 index.html
  if (url === '/_audit.html') {
    const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8')
      .replace('</body>', '<script src="/probe/audit.js"></script></body>');
    res.writeHead(200, {'Content-Type':'text/html;charset=utf-8'});
    return res.end(html);
  }

  const f = path.join(ROOT, url === '/' ? 'index.html' : url);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) {
    res.writeHead(404); return res.end('404');
  }
  res.writeHead(200, {'Content-Type': MIME[path.extname(f).toLowerCase()] || 'application/octet-stream'});
  fs.createReadStream(f).pipe(res);
});

function print(r) {
  const OK = '  OK  ', NG = ' 실패 ';
  const line = (n, ok, note) => console.log(`${ok ? OK : NG}│ ${n.padEnd(34)}│ ${note || ''}`);
  for (const sec of r.sections) {
    console.log('\n' + '═'.repeat(78));
    console.log('  ' + sec.title);
    console.log('─'.repeat(78));
    sec.rows.forEach(x => line(x.name, x.ok, x.note));
  }
  const bad = r.sections.flatMap(s => s.rows).filter(x => !x.ok);
  console.log('\n' + '═'.repeat(78));
  console.log(bad.length ? `  실패 ${bad.length}건 — ${bad.map(b => b.name).join(', ')}`
                         : '  전부 통과');
  console.log(`  걸린 시간 ${(r.ms / 1000).toFixed(1)}s · 자세한 값은 probe/report.json`);
}

// 태블릿에서도 같은 검수를 돌려야 하므로 LAN 에 연다(같은 와이파이).
srv.listen(PORT, '0.0.0.0', () => {
  const nets = require('os').networkInterfaces();
  const lan = Object.values(nets).flat().find(n => n.family === 'IPv4' && !n.internal);
  console.log(`PC   http://127.0.0.1:${PORT}/_audit.html`);
  if (lan) console.log(`태블릿 http://${lan.address}:${PORT}/_audit.html   ← 같은 와이파이에서`);
  console.log('결과를 기다린다...');
});
