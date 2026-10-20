#!/usr/bin/env node
/* 灵动岛小螃蟹 · 离线核字体：按 Swift 里的叠法（慢层→快层→蒙版，各层起点晚 phase 秒），用造好的字体把 40 格画出来，存成一张横条 PNG。
 * 再拿 Python 跟 from_svg.py 算的真实显示逐格比像素。浏览器找法见 chrome.mjs（环境变量 CHROME 可以指定）。
 *   node verify_fonts.mjs <字体目录> <CrabStates2.swift> <key> <输出.png>
 * 一格 = 1 像素（font-size 100px，1 em = 100 格），秒的个位 = floor(k/4 - phase) mod 10，跟灵动岛里计时器的个位一样。
 */
import { spawn } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';
import { findChrome } from './chrome.mjs';

const [fontDir, swift, key, out] = process.argv.slice(2);
const src = readFileSync(swift, 'utf8');
const m = src.match(new RegExp(`"${key}": CrabState2\\(w: (\\d+), h: (\\d+), layers: \\[([\\s\\S]*?)\\]\\)`));
if (!m) { console.error('没找到', key); process.exit(1); }
const W = +m[1], H = +m[2];
const layers = [...m[3].matchAll(/font: "(\w+)", color: 0x([0-9A-F]{6}), phase: ([\d.]+)/g)].map(x => ({ font: x[1], color: '#' + x[2], phase: +x[3] }));
const faces = layers.map(l => `@font-face{font-family:${l.font};src:url("${pathToFileURL(resolve(fontDir, l.font + '.ttf')).href}")}`).join('\n');
const html = `<!doctype html><meta charset="utf-8"><style>${faces} body{margin:0;background:#000}</style>
<canvas id="c" width="${W * 40}" height="${H}"></canvas>
<script>
const L=${JSON.stringify(layers)}, W=${W}, H=${H};
window.go = async () => {
  await Promise.all(L.map(l => document.fonts.load('100px ' + l.font, '0123456789')));
  const c = document.getElementById('c'), x = c.getContext('2d');
  x.fillStyle = '#000'; x.fillRect(0, 0, c.width, c.height);
  for (let k = 0; k < 40; k++) {
    x.save(); x.beginPath(); x.rect(k * W, 0, W, H); x.clip();
    for (const l of L) {
      const d = ((Math.floor(k / 4 - l.phase + 1e-9) % 10) + 10) % 10;
      x.font = '100px ' + l.font; x.fillStyle = l.color; x.fillText(String(d), k * W, H);
    }
    x.restore();
  }
  return c.toDataURL('image/png');
};
</script>`;
const page = join(mkdtempSync(join(tmpdir(), 'vf-')), 'v.html'); writeFileSync(page, html);

const BIN = findChrome();
const prof = mkdtempSync(join(tmpdir(), 'vfp-'));
const cp = spawn(BIN, ['--headless=new', '--remote-debugging-pipe', '--user-data-dir=' + prof, '--allow-file-access-from-files', '--force-color-profile=srgb', '--disable-lcd-text', '--disable-font-subpixel-positioning', 'about:blank'], { stdio: ['ignore', 'ignore', 'ignore', 'pipe', 'pipe'] });
const wr = cp.stdio[3], rd = cp.stdio[4]; let seq = 0, buf = Buffer.alloc(0); const pending = new Map();
rd.on('data', c => { buf = Buffer.concat([buf, c]); let i; while ((i = buf.indexOf(0)) >= 0) { const msg = JSON.parse(buf.subarray(0, i).toString('utf8')); buf = buf.subarray(i + 1); if (msg.id && pending.has(msg.id)) { const [ok, no] = pending.get(msg.id); pending.delete(msg.id); msg.error ? no(new Error(msg.error.message)) : ok(msg.result); } } });
const send = (method, params = {}, sessionId) => new Promise((ok, no) => { const id = ++seq; pending.set(id, [ok, no]); wr.write(JSON.stringify({ id, method, params, sessionId }) + '\0'); });
const done = c => { try { cp.kill(); } catch (e) {} try { rmSync(prof, { recursive: true, force: true }); } catch (e) {} process.exit(c); };
try {
  const { targetInfos } = await send('Target.getTargets');
  const { sessionId: S } = await send('Target.attachToTarget', { targetId: targetInfos.find(t => t.type === 'page').targetId, flatten: true });
  await send('Page.enable', {}, S); await send('Runtime.enable', {}, S);
  await send('Page.navigate', { url: pathToFileURL(page).href }, S);
  await new Promise(r => setTimeout(r, 800));
  const r = await send('Runtime.evaluate', { expression: 'window.go()', awaitPromise: true, returnByValue: true }, S);
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  mkdirSync(dirname(resolve(out)), { recursive: true });
  writeFileSync(out, Buffer.from(r.result.value.split(',')[1], 'base64'));
  console.log(`${key}: ${layers.length} 层，${W}×${H}×40 格 → ${out}`); done(0);
} catch (e) { console.error('✗', e.message); done(1); }
