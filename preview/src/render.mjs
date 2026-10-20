#!/usr/bin/env node
/* 假手机演示 → preview/phone-demo.gif
 *
 *   node preview/src/render.mjs                    # 在仓库根目录跑，出 preview/phone-demo.gif
 *   node preview/src/render.mjs --keep 帧目录        # 顺便留下逐帧 PNG
 *   node preview/src/render.mjs --fps 20 --out x.gif --chrome 浏览器路径
 *
 * 起一个只听 127.0.0.1 的临时静态服务器（跑完就关），用本机 Chromium（找法同 island/tools/chrome.mjs）
 * 打开 phone-demo.html?capture，按 PD.render(t) 一帧一帧摆好再截，2 倍像素截、gif.py 里缩回 1 倍拼成 GIF。
 * 需要 Node 18+、Python 3 + Pillow。 */
import { spawn, spawnSync } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, readFileSync, existsSync, statSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, extname, dirname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { findChrome } from '../../island/tools/chrome.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '../..');
const a = process.argv.slice(2), opt = { fps: 20, out: join(ROOT, 'preview/phone-demo.gif') };
for (let i = 0; i < a.length; i++) {
  const k = a[i];
  if (k === '--fps') opt.fps = +a[++i]; else if (k === '--out') opt.out = resolve(a[++i]);
  else if (k === '--keep') opt.keep = resolve(a[++i]); else if (k === '--chrome') opt.chrome = a[++i];
}
const W = 400, H = 736, DPR = 2;

const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.mjs': 'text/javascript', '.svg': 'image/svg+xml', '.json': 'application/json' };
const server = createServer((req, res) => {
  const p = resolve(ROOT, '.' + decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!(p === ROOT || p.startsWith(ROOT + sep)) || !existsSync(p) || !statSync(p).isFile()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' });
  res.end(readFileSync(p));
});
await new Promise(ok => server.listen(0, '127.0.0.1', ok));
const url = `http://127.0.0.1:${server.address().port}/preview/src/phone-demo.html?capture`;

const BIN = findChrome(opt.chrome);
const prof = mkdtempSync(join(tmpdir(), 'phonecap-'));
const frames = opt.keep || mkdtempSync(join(tmpdir(), 'phoneframes-'));
mkdirSync(frames, { recursive: true });
const cp = spawn(BIN, ['--headless=new', '--remote-debugging-pipe', '--user-data-dir=' + prof, '--no-first-run', '--no-default-browser-check',
  '--hide-scrollbars', '--mute-audio', '--force-color-profile=srgb', `--window-size=${W},${H}`, 'about:blank'], { stdio: ['ignore', 'ignore', 'ignore', 'pipe', 'pipe'] });
const wr = cp.stdio[3], rd = cp.stdio[4];
let seq = 0, buf = Buffer.alloc(0); const pending = new Map();
rd.on('data', c => {
  buf = Buffer.concat([buf, c]); let i;
  while ((i = buf.indexOf(0)) >= 0) {
    const m = JSON.parse(buf.subarray(0, i).toString('utf8')); buf = buf.subarray(i + 1);
    if (m.id && pending.has(m.id)) { const [ok, no] = pending.get(m.id); pending.delete(m.id); m.error ? no(new Error(m.error.message)) : ok(m.result); }
  }
});
const send = (method, params = {}, sessionId) => new Promise((ok, no) => { const id = ++seq; pending.set(id, [ok, no]); wr.write(JSON.stringify({ id, method, params, sessionId }) + '\0'); });
const exited = new Promise(ok => cp.once('exit', ok));
const done = async code => {
  try { cp.kill(); } catch (e) {}
  server.close();
  // 等浏览器真退出再删临时配置目录，不然它退出前还会往里写，删不干净
  await Promise.race([exited, new Promise(r => setTimeout(r, 3000))]);
  try { rmSync(prof, { recursive: true, force: true }); } catch (e) {}
  if (!opt.keep) try { rmSync(frames, { recursive: true, force: true }); } catch (e) {}
  process.exit(code);
};

try {
  const { targetInfos } = await send('Target.getTargets');
  const page = targetInfos.find(t => t.type === 'page');
  const { sessionId: S } = await send('Target.attachToTarget', { targetId: page.targetId, flatten: true });
  await send('Page.enable', {}, S); await send('Runtime.enable', {}, S);
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: DPR, mobile: false }, S);
  await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] }, S);
  await send('Page.navigate', { url }, S);
  const ev = async expression => {
    const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, S);
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result.value;
  };
  let st = null;
  for (let k = 0; k < 200 && !st; k++) {
    st = await ev('window.PD ? (PD.error || (PD.ready && "ok")) : null').catch(() => null);
    if (!st) await new Promise(r => setTimeout(r, 50));
  }
  if (st !== 'ok') throw new Error('页面没准备好：' + st);
  const L = await ev('PD.L');
  const n = Math.round(L * opt.fps);
  // 先空拍两张：第一张截图有时赶在 2 倍图块画完之前，下半截会是旧的
  for (const t of [0, L / 2, 0]) {
    await ev(`PD.seek(${t})`);
    await send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: W, height: H, scale: 1 } }, S);
    await new Promise(r => setTimeout(r, 150));
  }
  for (let k = 0; k < n; k++) {
    await ev(`PD.seek(${(k / opt.fps).toFixed(4)})`);
    const { data } = await send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: W, height: H, scale: 1 }, captureBeyondViewport: false }, S);
    writeFileSync(join(frames, `f_${String(k).padStart(4, '0')}.png`), Buffer.from(data, 'base64'));
  }
  writeFileSync(join(frames, 'meta.json'), JSON.stringify({ fps: opt.fps, loop: L, frames: n, w: W, h: H, dpr: DPR }));
  console.log(`${n} 帧（${L}s × ${opt.fps}fps，${W}×${H}，截图 ${DPR} 倍）→ ${frames}`);
  const py = spawnSync('python3', [join(HERE, 'gif.py'), frames, opt.out, '--fps', String(opt.fps), '--scale', String(DPR)], { stdio: 'inherit' });
  done(py.status === 0 ? 0 : 1);
} catch (e) { console.error('失败：', e.message); done(1); }
