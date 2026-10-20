#!/usr/bin/env node
/* 灵动岛小螃蟹 · 把一个 SVG 的 CSS 动画停在某几个时刻，一帧一帧拍成透明底 PNG。
 * 用本机的 Chromium（走 DevTools 管道，不用装 npm 包）；找浏览器的规矩见 chrome.mjs，也可以 --chrome 指定。
 *
 *   node tools/render.mjs --svg crabs/fish/fish.svg --out frames --px 6 --times 0,0.25,0.5
 *   node tools/render.mjs --svg crabs/fish/fish.svg --out frames --px 6 --fps 12 --loop 10
 *
 * --px 每个 SVG 单位几像素；--css 额外塞一段 CSS（比如关掉呼吸）；--hide / --only 按 class 藏掉或只留某几层。
 * 所有动画要 infinite；根 <svg data-loop="10"> 可以写一圈几秒（--loop 优先）。
 */
import { spawn } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { findChrome } from './chrome.mjs';

const a = process.argv.slice(2), opt = { fps: 12, px: 30, hide: '', only: '' };
for (let i = 0; i < a.length; i++) {
  const k = a[i];
  if (k === '--svg') opt.svg = a[++i]; else if (k === '--out') opt.out = a[++i]; else if (k === '--fps') opt.fps = +a[++i];
  else if (k === '--loop') opt.loop = +a[++i]; else if (k === '--px') opt.px = +a[++i];
  else if (k === '--hide') opt.hide = a[++i]; else if (k === '--only') opt.only = a[++i];
  else if (k === '--times') opt.times = a[++i].split(',').map(Number);
  else if (k === '--css') opt.css = a[++i];   // 额外 CSS（灵动岛版关掉呼吸这类细抖）
  else if (k === '--chrome') opt.chrome = a[++i];
}
const svgText = readFileSync(resolve(opt.svg), 'utf8');
const vb = (svgText.match(/viewBox="([^"]+)"/) || [, '0 0 32 24'])[1].split(/\s+/).map(Number);
const loopAttr = +(svgText.match(/data-loop="([\d.]+)"/) || [, 0])[1];
const loop = opt.loop || loopAttr || 4;
const W = Math.round(vb[2] * opt.px), H = Math.round(vb[3] * opt.px);
const LAYERS = ['L-body', 'L-eye', 'L-lid', 'L-line', 'L-accent'];
let css = 'html,body{margin:0;background:transparent;overflow:hidden} #host svg{display:block;width:' + W + 'px;height:' + H + 'px;color:#F2E9DC}';
if (opt.css) css += opt.css;
if (opt.hide) css += opt.hide.split(',').map(c => `#host .${c}`).join(',') + '{visibility:hidden !important}';
if (opt.only) css += LAYERS.filter(c => !opt.only.split(',').includes(c)).map(c => `#host .${c}`).join(',') + '{visibility:hidden !important}';

const BIN = findChrome(opt.chrome);
const prof = mkdtempSync(join(tmpdir(), 'islcap-'));
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
const done = code => { try { cp.kill(); } catch (e) {} try { rmSync(prof, { recursive: true, force: true }); } catch (e) {} process.exit(code); };

try {
  const { targetInfos } = await send('Target.getTargets');
  const page = targetInfos.find(t => t.type === 'page');
  const { sessionId: S } = await send('Target.attachToTarget', { targetId: page.targetId, flatten: true });
  await send('Page.enable', {}, S); await send('Runtime.enable', {}, S);
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false }, S);
  await send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } }, S);
  const html = `<!doctype html><meta charset="utf-8"><style>${css}</style><div id="host">${svgText}</div>`;
  const { frameTree } = await send('Page.getFrameTree', {}, S);
  await send('Page.setDocumentContent', { frameId: frameTree.frame.id, html }, S);
  const ev = async (expression) => {
    const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, S);
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result.value;
  };
  // 所有动画停住，按时间点拨到那一刻（infinite 动画 currentTime 超过时长会自己绕回去）
  await ev(`(async()=>{ await document.fonts.ready; const A=document.getAnimations(); A.forEach(x=>x.pause());
    window.seek=async t=>{ for(const x of document.getAnimations()){ x.pause(); x.currentTime=t*1000; } await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))); };
    return A.length; })()`);
  const nAnim = await ev('document.getAnimations().length');
  const times = opt.times || Array.from({ length: Math.round(loop * opt.fps) }, (_, k) => +(k / opt.fps).toFixed(4));
  mkdirSync(opt.out, { recursive: true });
  let k = 0;
  for (const t of times) {
    await ev(`window.seek(${t})`);
    const { data } = await send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: W, height: H, scale: 1 }, captureBeyondViewport: false }, S);
    writeFileSync(join(opt.out, `f_${String(k++).padStart(4, '0')}.png`), Buffer.from(data, 'base64'));
  }
  writeFileSync(join(opt.out, 'meta.json'), JSON.stringify({ svg: opt.svg, loop, fps: opt.fps, px: opt.px, w: W, h: H, frames: times.length, animations: nAnim, hide: opt.hide, only: opt.only }));
  console.log(`${opt.svg}: ${times.length} 帧 ${W}×${H}，动画 ${nAnim} 个，一圈 ${loop}s → ${opt.out}`);
  done(0);
} catch (e) { console.error('✗', e.message); done(1); }
