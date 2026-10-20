/* Single-icon export: static SVG, self-contained animated SVG, GIF.
 * Icons and code: MIT, see ../LICENSE and ../THIRD_PARTY.md. GIF encoder: vendor/gifenc.esm.js (MIT). */
(() => {
  const G = window.ClawdGallery;
  const panel = document.querySelector('#download');
  const $ = s => panel.querySelector(s);
  const iconChoice = $('#dl-icon'), versionChoice = $('#dl-version'), motionChoice = $('#dl-motion');
  const status = $('#dl-status'), cancel = $('#dl-cancel'), result = $('#dl-result'), saveLink = $('#dl-save');
  const fields = panel.querySelectorAll('select, input, [data-format]');
  const SVGNS = 'http://www.w3.org/2000/svg';
  const PAD = 2;          // room around the 24-unit icon; the widest motion (sun) reaches 1.2 units past the edge
  const STEP = 50;        // GIF frame interval, ms
  const HOLD = 600;       // rest after a gesture before the GIF loops
  const MAX_LOOP = 20000; // longest idle loop worth encoding
  const MOTIONS = [
    { id: 'trick', name: '专属动作' },
    { id: 'blink', name: '眨眼', note: '眨一下眼。' },
    { id: 'happy', name: '开心', note: '开心地跳一下，挥挥手。' },
    { id: 'idle', name: '待机', note: '慢慢呼吸，偶尔眨眼，一直循环。' },
    { id: 'asleep', name: '睡着', note: '闭着眼睡着的样子，是静止的。' },
    { id: 'wake', name: '醒来', note: '睁开眼，从睡着回到醒着。' }
  ];
  const DESC = 'Clawd Icons by 唐幡 (TangfanOVO) · MIT License · https://github.com/TangfanOVO/clawd-icons · Clawd base artwork: marciogranzotto/clawd-tank (MIT). Unofficial community adaptation.';
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const serializer = new XMLSerializer();
  let outputURL = null, job = null, rules = null, stage = null, ready = false;
  let progress = '', waiting = false;
  const WAIT = '请等这一份完成，或者先取消。';
  // While a GIF is being made, a "下载" tapped elsewhere keeps its reminder next to the progress.
  function showProgress(text) {
    progress = text;
    status.textContent = waiting ? `${text} · ${WAIT}` : text;
  }
  const isLight = hex => {
    const n = parseInt(String(hex).slice(1), 16);
    return Number.isFinite(n) && (0.2126 * (n >> 16 & 255) + 0.7152 * (n >> 8 & 255) + 0.0722 * (n & 255)) / 255 > 0.6;
  };
  // A transparent export is previewed on a checkerboard that stays readable under the chosen line colour.
  const markClear = (node, o) => {
    node.classList.toggle('is-clear', o.background === 'transparent');
    node.classList.toggle('light-ink', o.background === 'transparent' && isLight(o.color));
  };
  const available = new Map();

  /* ---------- the two motion stylesheets, read as written so exports carry the author's CSS unchanged */
  const CSS_FILES = ['clawd-motion.css', 'vivid/clawd-vivid.css'];
  function parseCSS(text) {
    text = text.replace(/\/\*[\s\S]*?\*\//g, '');
    const out = [];
    let i = 0;
    while (i < text.length) {
      const open = text.indexOf('{', i);
      if (open < 0) break;
      const prelude = text.slice(i, open).trim();
      let depth = 1, j = open + 1;
      while (j < text.length && depth) { if (text[j] === '{') depth++; else if (text[j] === '}') depth--; j++; }
      const raw = text.slice(i, j).trim(), body = text.slice(open + 1, j - 1);
      if (/^@media\b/.test(prelude)) out.push({ type: 'media', prelude, rules: parseCSS(body), reduced: /prefers-reduced-motion/.test(prelude), raw });
      else if (/^@keyframes\s/.test(prelude)) out.push({ type: 'keyframes', name: prelude.split(/\s+/)[1], raw });
      else if (prelude && !prelude.startsWith('@')) out.push({ type: 'style', selector: prelude, raw });
      i = j;
    }
    return out;
  }
  async function loadRules() {
    const texts = await Promise.all(CSS_FILES.map(url => fetch(url).then(r => {
      if (!r.ok) throw new Error(`${url} ${r.status}`);
      return r.text();
    })));
    rules = texts.flatMap(parseCSS);
  }
  function motionRules() {
    if (!rules) throw new Error('动作样式没有载入');
    return rules;
  }

  /* An off-screen shadow root carries the motion CSS without the reduced-motion blocks,
   * so an export always gets the motion that was asked for. */
  function getStage() {
    if (stage) return stage;
    const host = document.createElement('div');
    host.className = 'export-stage';
    host.setAttribute('aria-hidden', 'true');
    const root = host.attachShadow({ mode: 'open' });
    const style = document.createElement('style');
    style.textContent = motionRules().filter(r => !(r.type === 'media' && r.reduced)).map(r => r.raw).join('\n');
    root.append(style);
    document.body.append(host);
    stage = root;
    return stage;
  }

  /* ---------- building one icon in one state */
  function sourceEl(icon, version) {
    const doc = new DOMParser().parseFromString(icon.src[version], 'image/svg+xml');
    return document.importNode(doc.documentElement, true);
  }
  function stateEl(o) {
    const el = sourceEl(o.icon, o.version);
    el.removeAttribute('aria-hidden');
    el.setAttribute('overflow', 'visible');
    if (['trick', 'blink', 'happy'].includes(o.motion)) { el.classList.add('is-playing'); el.setAttribute('data-motion', o.motion); }
    else if (o.motion === 'idle') el.classList.add('is-idle');
    else if (o.motion === 'asleep') el.classList.add('is-asleep');
    else if (o.motion === 'wake') el.classList.add('is-waking');
    el.style.setProperty('color', o.color);
    el.style.setProperty('--cr-speed', String(o.speed));
    return el;
  }
  function hasMotion(icon, version, motion) {
    if (motion === 'asleep') return true; // a resting state, drawn without animation
    const key = `${icon.name}|${version}|${motion}`;
    if (!available.has(key)) {
      const el = stateEl({ icon, version, motion, color: '#000', speed: 1 });
      getStage().append(el);
      available.set(key, el.getAnimations({ subtree: true }).length > 0);
      el.remove();
    }
    return available.get(key);
  }

  /* Only the rules that touch this icon in this state, plus the keyframes it uses. */
  function exportCSS(el) {
    const nodes = [el, ...el.querySelectorAll('*')];
    const names = new Set();
    nodes.forEach(n => getComputedStyle(n).animationName.split(',').forEach(x => {
      x = x.trim();
      if (x && x !== 'none') names.add(x);
    }));
    const hit = sel => { try { return nodes.some(n => n.matches(sel)); } catch (e) { return false; } };
    const walk = list => list.map(r => {
      if (r.type === 'style') return hit(r.selector) ? r.raw : '';
      if (r.type === 'keyframes') return names.has(r.name) ? r.raw : '';
      if (r.type === 'media') {
        const inner = [...new Set(walk(r.rules))].join('');
        return inner ? `${r.prelude}{${inner}}` : '';
      }
      return '';
    }).filter(Boolean);
    return [...new Set(walk(motionRules()))].join('\n');
  }

  function wrap(o, inner, css) {
    const vb = `${-PAD} ${-PAD} ${24 + 2 * PAD} ${24 + 2 * PAD}`;
    const bg = o.background === 'transparent' ? '' : `<rect x="${-PAD}" y="${-PAD}" width="${24 + 2 * PAD}" height="${24 + 2 * PAD}" fill="${o.background}"/>`;
    return `<svg xmlns="${SVGNS}" width="${o.size}" height="${o.size}" viewBox="${vb}"><title>${esc(title(o))}</title><desc>${esc(DESC)}</desc>${css ? `<style><![CDATA[\n${css}\n]]></style>` : ''}${bg}${inner}</svg>`;
  }
  const title = o => `Clawd Icons · ${o.icon.label} · ${G.VERSIONS[o.version]}`;

  function staticSVG(o) {
    const el = sourceEl(o.icon, o.version);
    if (o.motion === 'asleep') {
      el.querySelectorAll('.cr-eye-open').forEach(n => n.setAttribute('opacity', '0'));
      el.querySelectorAll('.cr-eye-sleep').forEach(n => n.removeAttribute('opacity'));
    }
    el.querySelectorAll('[opacity="0"]').forEach(n => n.remove());
    [el, ...el.querySelectorAll('*')].forEach(n => { n.removeAttribute('class'); n.removeAttribute('data-motion'); });
    el.removeAttribute('aria-hidden');
    el.setAttribute('width', String(o.size));
    el.setAttribute('height', String(o.size));
    el.setAttribute('color', o.color);
    const make = (tag, attrs, text) => {
      const n = document.createElementNS(SVGNS, tag);
      Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
      if (text) n.textContent = text;
      return n;
    };
    const head = [make('title', {}, title(o)), make('desc', {}, DESC)];
    if (o.background !== 'transparent') head.push(make('rect', { width: '24', height: '24', fill: o.background, stroke: 'none' }));
    el.prepend(...head);
    return serializer.serializeToString(el).replace(/\n\s*\n/g, '\n');
  }

  function animatedSVG(o) {
    const el = stateEl(o);
    getStage().append(el);
    try {
      const css = exportCSS(el);
      el.remove();
      return wrap(o, serializer.serializeToString(el), css);
    } finally { el.remove(); }
  }

  /* ---------- GIF: pause every animation, step through time, draw each frame */
  const frameProperties = ['transform', 'transform-origin', 'transform-box', 'opacity', 'color', 'fill', 'fill-opacity', 'fill-rule',
    'stroke', 'stroke-width', 'stroke-opacity', 'stroke-linecap', 'stroke-linejoin', 'stroke-dasharray', 'stroke-dashoffset', 'visibility'];
  function snapshot(el) {
    const clone = el.cloneNode(true);
    const originals = [el, ...el.querySelectorAll('*')], copies = [clone, ...clone.querySelectorAll('*')];
    originals.forEach((node, i) => {
      const style = getComputedStyle(node);
      frameProperties.forEach(k => copies[i].style.setProperty(k, style.getPropertyValue(k)));
      copies[i].style.setProperty('animation', 'none');
    });
    return serializer.serializeToString(clone);
  }
  async function drawFrame(context, source) {
    const url = URL.createObjectURL(new Blob([source], { type: 'image/svg+xml;charset=utf-8' }));
    try {
      const image = new Image();
      await new Promise((resolve, reject) => {
        image.onload = resolve;
        image.onerror = () => reject(new Error('图标画面读不出来'));
        image.src = url;
      });
      context.clearRect(0, 0, context.canvas.width, context.canvas.height);
      context.drawImage(image, 0, 0, context.canvas.width, context.canvas.height);
    } finally { URL.revokeObjectURL(url); }
  }
  function loopLength(animations) {
    // Idle mixes a 3.2 s breath with a 5 s blink. Their exact common loop is 80 s, so take whole breaths
    // and the first length where the blink also lands within a tenth of a cycle (9.6 s here).
    const periods = [...new Set(animations.map(a => Math.max(STEP, Math.round(a.effect.getComputedTiming().duration / 10) * 10)))].sort((x, y) => x - y);
    if (!periods.length) return STEP;
    let best = periods[0], bestError = Infinity;
    for (let length = periods[0]; length <= MAX_LOOP; length += periods[0]) {
      const error = Math.max(...periods.map(p => { const r = length / p; return Math.abs(r - Math.max(1, Math.round(r))); }));
      if (error < 0.1) return length;
      if (error < bestError) { best = length; bestError = error; }
    }
    return best;
  }
  function sameFrame(a, b) {
    if (!a || a.length !== b.length) return false;
    const x = new Uint32Array(a.buffer), y = new Uint32Array(b.buffer);
    for (let i = 0; i < x.length; i++) if (x[i] !== y[i]) return false;
    return true;
  }

  async function gif(o, signal) {
    const { GIFEncoder, quantize, applyPalette } = await import('./vendor/gifenc.esm.js');
    const el = stateEl(o);
    getStage().append(el);
    try {
      const animations = el.getAnimations({ subtree: true });
      animations.forEach(a => { a.pause(); a.currentTime = 0; });
      const timings = animations.map(a => a.effect.getComputedTiming());
      let end = 0;
      if (animations.length && timings.every(t => Number.isFinite(t.endTime))) end = Math.max(...timings.map(t => t.endTime)) + HOLD;
      else if (animations.length) end = loopLength(animations.filter((a, i) => !Number.isFinite(timings[i].endTime)));
      const frames = Math.max(1, Math.round(end / STEP));
      const size = o.size, transparent = o.background === 'transparent';
      const canvas = document.createElement('canvas');
      canvas.width = canvas.height = size;
      const context = canvas.getContext('2d', { willReadFrequently: true });
      if (!context) throw new Error('这个浏览器不能生成 GIF，请改用动态 SVG');
      const encoder = GIFEncoder();
      let pending = null, previous = null, written = 0;
      const flush = () => {
        if (!pending) return;
        encoder.writeFrame(pending.index, size, size, {
          palette: pending.palette, delay: pending.delay, repeat: 0, dispose: 2,
          transparent: pending.transparentIndex >= 0, transparentIndex: Math.max(0, pending.transparentIndex)
        });
        written++;
      };
      for (let i = 0; i < frames; i++) {
        signal.throwIfAborted();
        animations.forEach(a => { a.currentTime = i * STEP; });
        await drawFrame(context, wrap(o, snapshot(el), ''));
        const { data } = context.getImageData(0, 0, size, size);
        // GIF has one-bit alpha: soft edges are laid on a white matte, empty pixels stay clear.
        if (transparent) for (let p = 0; p < data.length; p += 4) {
          const alpha = data[p + 3] / 255;
          if (alpha < .08) { data[p] = data[p + 1] = data[p + 2] = data[p + 3] = 0; }
          else { for (let c = 0; c < 3; c++) data[p + c] = Math.round(data[p + c] * alpha + 255 * (1 - alpha)); data[p + 3] = 255; }
        }
        if (sameFrame(previous, data)) pending.delay += STEP;
        else {
          flush();
          const format = transparent ? 'rgba4444' : 'rgb565';
          const palette = quantize(data, 256, { format, oneBitAlpha: true });
          pending = {
            index: applyPalette(data, palette, format), palette, delay: STEP,
            transparentIndex: transparent ? palette.findIndex(color => color[3] === 0) : -1
          };
          previous = data;
        }
        showProgress(`正在生成 GIF：${Math.round((i + 1) / frames * 100)}%`);
        if (i % 4 === 3) await new Promise(resolve => setTimeout(resolve, 0));
      }
      signal.throwIfAborted();
      flush();
      encoder.finish();
      return { blob: new Blob([encoder.bytes()], { type: 'image/gif' }), frames: written };
    } finally { el.remove(); }
  }

  /* ---------- the panel */
  function options() {
    return {
      icon: G.byName[iconChoice.value], version: versionChoice.value, motion: motionChoice.value,
      color: $('#dl-color').value, background: $('#dl-bg').value,
      size: Number($('#dl-size').value), speed: Number($('#dl-speed').value)
    };
  }
  function fileName(o, format) {
    const base = `${o.icon.name}-${o.version}`;
    if (format === 'static') return `${base}-${o.motion === 'asleep' ? 'asleep-' : ''}static-${o.size}px.svg`;
    const slow = o.speed === 1 ? '' : `-x${+(1 / o.speed).toFixed(2)}`;
    return `${base}-${o.motion}-${o.size}px${slow}.${format}`;
  }

  function fillVersions() {
    const icon = G.byName[iconChoice.value], keep = versionChoice.value;
    const list = Object.entries(G.VERSIONS).filter(([v]) => icon.src[v]);
    versionChoice.innerHTML = list.map(([v, t]) => `<option value="${v}">${t}</option>`).join('');
    versionChoice.value = list.some(([v]) => v === keep) ? keep : 'default';
    versionChoice.disabled = list.length < 2 || !!job;
  }
  function fillMotions() {
    const o = options(), keep = motionChoice.value, info = G.info(o.icon, o.version);
    motionChoice.innerHTML = MOTIONS.map(m => {
      const ok = hasMotion(o.icon, o.version, m.id);
      const text = m.id === 'trick' ? `专属动作 · ${info.motion}` : m.name;
      return `<option value="${m.id}"${ok ? '' : ' disabled'}>${esc(text)}</option>`;
    }).join('');
    const usable = [...motionChoice.options].filter(x => !x.disabled).map(x => x.value);
    motionChoice.value = usable.includes(keep) ? keep : 'trick';
  }

  function refresh() {
    const o = options(), info = G.info(o.icon, o.version);
    const preview = $('#dl-preview');
    const el = stateEl(o);
    el.setAttribute('width', '84');
    el.setAttribute('height', '84');
    el.setAttribute('aria-hidden', 'true');
    preview.replaceChildren(el);
    preview.style.background = o.background === 'transparent' ? '' : o.background;
    markClear(preview, o);
    const m = MOTIONS.find(x => x.id === o.motion);
    $('#dl-note').textContent = `${o.icon.label} · ${G.VERSIONS[o.version]} · ${m.id === 'trick' ? info.motion : m.name}：${m.id === 'trick' ? info.description : m.note}点预览可以重播。`;
  }
  function rebuild() { fillVersions(); fillMotions(); refresh(); }

  function select(name, version) {
    if (job) {
      waiting = true;
      showProgress(progress || '正在生成');
      panel.scrollIntoView({ block: 'start' });
      return;
    }
    if (!ready || !G.byName[name]) return;
    iconChoice.value = name;
    fillVersions();
    if ([...versionChoice.options].some(x => x.value === version)) versionChoice.value = version;
    motionChoice.value = G.state.mode;
    fillMotions();
    refresh();
    panel.scrollIntoView({ block: 'start' });
    iconChoice.focus({ preventScroll: true });
  }

  function publish(blob, name, o) {
    if (outputURL) URL.revokeObjectURL(outputURL);
    outputURL = URL.createObjectURL(blob);
    saveLink.href = outputURL;
    saveLink.download = name;
    saveLink.textContent = `保存 ${name}`;
    $('#dl-image').src = outputURL;
    markClear($('#dl-image'), o);
    result.hidden = false;
    saveLink.click();
    status.textContent = '文件已生成。如果没有自动下载，点“保存”链接；手机上也可以长按预览图保存。';
  }

  async function init() {
    fields.forEach(f => { f.disabled = true; });
    const groups = new Map();
    G.icons.forEach(ic => { if (!groups.has(ic.category)) groups.set(ic.category, []); groups.get(ic.category).push(ic); });
    iconChoice.innerHTML = [...groups].map(([cat, list]) => `<optgroup label="${esc(cat)}">${list.map(ic =>
      `<option value="${ic.name}">${esc(ic.label)} · ${ic.name}${ic.vivid ? ' · 有生动版' : ''}</option>`).join('')}</optgroup>`).join('');
    iconChoice.value = G.byName['clawd-home'] ? 'clawd-home' : G.icons[0].name;
    $('#dl-speed').value = G.state.speed;
    try { await loadRules(); rebuild(); ready = true; fields.forEach(f => { f.disabled = false; }); fillVersions(); } catch (error) {
      status.textContent = `下载面板没有准备好：${error.message}。请刷新页面再试。`;
      fields.forEach(f => { f.disabled = true; });
      return;
    }

    panel.addEventListener('change', e => {
      if (job || !ready) return;
      if (e.target === $('#dl-speed')) { G.setSpeed(e.target.value); return; }
      if (e.target === iconChoice || e.target === versionChoice) { fillVersions(); fillMotions(); }
      refresh();
    });
    $('#dl-preview').addEventListener('click', () => { if (!job && ready) refresh(); });
    panel.addEventListener('click', async e => {
      const button = e.target.closest('[data-format]');
      if (!button || job || !ready) return;
      const o = options(), format = button.dataset.format, name = fileName(o, format);
      job = new AbortController();
      fields.forEach(f => { f.disabled = true; });
      panel.setAttribute('aria-busy', 'true');
      showProgress(format === 'gif' ? '正在准备 GIF…' : '正在生成…');
      cancel.hidden = format !== 'gif';
      result.hidden = true;
      try {
        let blob;
        if (format === 'gif') {
          const out = await gif(o, job.signal);
          blob = out.blob;
        } else {
          const text = format === 'static' ? staticSVG(o) : animatedSVG(o);
          blob = new Blob([text], { type: 'image/svg+xml;charset=utf-8' });
        }
        if (!job.signal.aborted) publish(blob, name, o);
      } catch (error) {
        status.textContent = error.name === 'AbortError' ? '已取消，可以重新选择或下载。' : `生成失败：${error.message}。请重试，或者换一种格式。`;
      } finally {
        fields.forEach(f => { f.disabled = false; });
        panel.removeAttribute('aria-busy');
        cancel.hidden = true;
        job = null;
        waiting = false;
        progress = '';
        fillVersions();
      }
    });
    cancel.addEventListener('click', () => job?.abort());
    document.addEventListener('click', e => {
      const button = e.target.closest('[data-download]');
      if (button) select(button.dataset.download, button.dataset.version || G.ver[button.dataset.download] || 'default');
    });
    document.addEventListener('clawd:settings', () => {
      $('#dl-speed').value = G.state.speed;
      if (!job && ready) refresh();
    });
  }

  if (G.loaded) init(); else document.addEventListener('clawd:ready', init, { once: true });
})();
