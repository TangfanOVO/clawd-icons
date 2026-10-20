/* 找一个能用的 Chromium：参数 > 环境变量 CHROME > Playwright 缓存里的 chromium > 系统里装的 Chrome / Chromium。 */
import { existsSync, readdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

export function findChrome(explicit) {
  if (explicit) return explicit;
  if (process.env.CHROME) return process.env.CHROME;
  const cands = [];
  for (const base of [join(homedir(), 'Library/Caches/ms-playwright'), join(homedir(), '.cache/ms-playwright')]) {
    let dirs = [];
    try { dirs = readdirSync(base).filter(d => d.startsWith('chromium-')).sort().reverse(); } catch (e) {}
    for (const d of dirs) cands.push(
      join(base, d, 'chrome-mac/Chromium.app/Contents/MacOS/Chromium'),
      join(base, d, 'chrome-mac-arm64/Chromium.app/Contents/MacOS/Chromium'),
      join(base, d, 'chrome-linux/chrome'));
  }
  cands.push('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome');
  const hit = cands.find(p => existsSync(p));
  if (!hit) {
    console.error('✗ 找不到 Chromium：npx playwright install chromium，或者用 CHROME=浏览器路径 指定');
    process.exit(1);
  }
  return hit;
}
