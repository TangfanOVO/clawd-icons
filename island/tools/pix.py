"""灵动岛小螃蟹 · 像素画底座

画法：一帧 = 一张 W×H 的格子图，每格一个调色板字母（'.' = 空）。
    from pix import Frame, export
    f = Frame(24, 18); f.rect(5, 6, 13, 8, 'O'); f.spr(["XX", ".X"], 3, 2); f.put(1, 1, 'K')

一个状态交给 export()：
    export(key, title, detail, accent, palette, z, frames,
           smooth=[(帧号, 毫秒), ...],          # 顺滑版：推送配图 / app 里 / 聊天
           island=[帧号] * 40,                 # 灵动岛：40 格 × 0.25 秒 = 10 秒一圈（可以给 8/10/20 格，会自动重复到 40）
           lock=[帧号] * 10,                   # 锁屏：10 格 × 1 秒（锁屏是玻璃底，只能一秒换一次，不能用黑蒙版）
           out=目录)

灵动岛的规矩（simulate 照这个算，算出来的就是手机上真会看到的样子）：
  四组 Text(timerInterval:) 起点错开 0.25 秒；每组每秒换一次字形 → 每 0.25 秒画面能变一次。
  一种颜色 × 一组 = 一层字体。一层字形换上以后要挂满 1 秒，后放上去的盖不掉先放的，
  只能靠最上面的纯黑蒙版整块盖住；蒙版也挂满 1 秒。所以：
    · 点亮随时可以；
    · 一个点熄掉（变回黑底）以后要黑满 1 秒（4 格），不然前一秒的颜色会留成残影；
    · 颜色只往 z 序更高的颜色变才干净，往低处变等于高的那层要先「熄」。
  十秒里从头到尾一直不变的点，放进一张静态底图，不占计时器层。
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

SLOT, CYCLE, N = 0.25, 10.0, 40


def _find_font():
    """样机上写中文用的字体：环境变量 CRAB_FONT > 系统里常见的几种；都没有就用 PIL 自带的（只有英文）。"""
    for p in (os.environ.get('CRAB_FONT', ''), '/System/Library/Fonts/Hiragino Sans GB.ttc', '/System/Library/Fonts/PingFang.ttc',
              '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
              'C:/Windows/Fonts/msyh.ttc'):
        if p and os.path.exists(p): return p
    return None


FONT = _find_font()


def font(size):
    if FONT: return ImageFont.truetype(FONT, size)
    try: return ImageFont.load_default(size)
    except TypeError: return ImageFont.load_default()


class Frame:
    def __init__(s, w, h, px=None):
        s.w, s.h, s.px = w, h, dict(px or {})

    def copy(s):
        return Frame(s.w, s.h, s.px)

    def put(s, x, y, c):
        if 0 <= x < s.w and 0 <= y < s.h:
            if c == '.' or c is None: s.px.pop((x, y), None)
            else: s.px[(x, y)] = c
        return s

    def get(s, x, y):
        return s.px.get((x, y))

    def rect(s, x, y, w, h, c):
        for j in range(h):
            for i in range(w): s.put(x + i, y + j, c)
        return s

    def spr(s, rows, ox, oy, transparent='.', recolor=None):
        """字符画贴上去；'.' 透明，'_' 擦成空。recolor={'A':'B'} 换色。"""
        for j, row in enumerate(rows):
            for i, c in enumerate(row):
                if c == transparent: continue
                if c == '_': s.put(ox + i, oy + j, None); continue
                s.put(ox + i, oy + j, (recolor or {}).get(c, c))
        return s

    def many(s, pts, c, dx=0, dy=0):
        for x, y in pts: s.put(x + dx, y + dy, c)
        return s

    def shift(s, dx, dy):
        return Frame(s.w, s.h, {(x + dx, y + dy): c for (x, y), c in s.px.items() if 0 <= x + dx < s.w and 0 <= y + dy < s.h})

    def over(s, other):
        f = s.copy(); f.px.update(other.px); return f

    def image(s, pal, scale=1, bg=None):
        im = Image.new('RGBA', (s.w, s.h), bg or (0, 0, 0, 0)); p = im.load()
        for (x, y), c in s.px.items(): p[x, y] = hexrgb(pal[c]) + (255,)
        return im.resize((s.w * scale, s.h * scale), Image.NEAREST) if scale != 1 else im

    def rows(s):
        return [''.join(s.px.get((x, y), '.') for x in range(s.w)) for y in range(s.h)]


def hexrgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def expand(seq, n):
    if len(seq) == n: return list(seq)
    if n % len(seq): raise ValueError(f'序列长 {len(seq)} 不能整除 {n}')
    return list(seq) * (n // len(seq))


def simulate(frames, seq, z):
    """seq: 40 个帧号。z: 颜色字母按层序从低到高（没列到的颜色当最低层，报出来）。
    返回 (显示帧列表, 每格残影点数, 层统计)。"""
    tgt = [frames[i] for i in seq]; n = len(tgt)
    W, H = tgt[0].w, tgt[0].h
    zi = {c: i for i, c in enumerate(z)}
    unknown = sorted({c for f in tgt for c in f.px.values() if c not in zi})
    for c in unknown: zi[c] = -1
    static = {p: c for p, c in tgt[0].px.items() if all(f.px.get(p) == c for f in tgt)}
    shown, bad = [], []
    for k in range(n):
        f = Frame(W, H); b = 0
        for y in range(H):
            for x in range(W):
                p = (x, y)
                if p in static: f.px[p] = static[p]; continue
                masked = any(all(tgt[(k - d + e) % n].px.get(p) is None for e in range(4)) for d in range(4))
                if masked: v = None
                else:
                    cands = [tgt[(k - d) % n].px.get(p) for d in range(4)]
                    cands = [c for c in cands if c is not None]
                    v = max(cands, key=lambda c: zi[c]) if cands else None
                if v is not None: f.px[p] = v
                if v != tgt[k].px.get(p): b += 1
        shown.append(f); bad.append(b)
    # 要几层计时器：会变的点用到的颜色 × 4 组 + 4 层蒙版
    varying = {c for f in tgt for p, c in f.px.items() if p not in static}
    needs_mask = any(any(all(tgt[(k + e) % n].px.get(p) is None for e in range(4)) and any(tgt[(k - d) % n].px.get(p) for d in range(1, 4))
                         for k in range(n)) for p in {p for f in tgt for p in f.px if p not in static})
    stats = {'变的颜色': sorted(varying), '计时器层数': len(varying) * 4 + (4 if needs_mask else 0),
             '静态点': len(static), 'z序里没有的颜色': unknown}
    return shown, bad, stats


def pill(img, mode, title, detail, accent, S=3):
    """灵动岛样机（@3x）。img 已经按格子放大好的螃蟹（RGBA）。"""
    A = hexrgb(accent)
    if mode == 'compact':
        W, H = 250 * S, 37 * S
        bg = Image.new('RGB', (W + 24 * S, H + 24 * S), (38, 36, 42)); d = ImageDraw.Draw(bg)
        d.rounded_rectangle([12 * S, 12 * S, 12 * S + W, 12 * S + H], radius=H // 2, fill=(0, 0, 0))
        bg.paste(img, (12 * S + 16 * S, 12 * S + (H - img.size[1]) // 2), img)
        f = font(15 * S); tw = d.textlength(title, font=f)
        d.text((12 * S + W - 18 * S - tw, 12 * S + (H - 15 * S) // 2 - 2 * S), title, font=f, fill=A)
        return bg
    if mode == 'minimal':
        D = 37 * S
        bg = Image.new('RGB', (D + 24 * S, D + 24 * S), (38, 36, 42)); d = ImageDraw.Draw(bg)
        d.ellipse([12 * S, 12 * S, 12 * S + D, 12 * S + D], fill=(0, 0, 0))
        while img.size[0] > D - 6 * S or img.size[1] > D - 6 * S:      # 圆里放不下就整数倍缩小
            img = img.resize((img.size[0] // 2, img.size[1] // 2), Image.NEAREST)
        bg.paste(img, (12 * S + (D - img.size[0]) // 2, 12 * S + (D - img.size[1]) // 2), img)
        return bg
    if mode == 'lock':
        W, H = 370 * S, 120 * S
        bg = Image.new('RGB', (W + 24 * S, H + 24 * S), (70, 78, 96)); d = ImageDraw.Draw(bg)
        d.rounded_rectangle([12 * S, 12 * S, 12 * S + W, 12 * S + H], radius=26 * S, fill=(96, 104, 124))
        bg.paste(img, (12 * S + 18 * S, 12 * S + (H - img.size[1]) // 2), img)
        x0 = 12 * S + 18 * S + img.size[0] + 16 * S
        f1, f2 = font(17 * S), font(14 * S)
        d.text((x0, 12 * S + 34 * S), title, font=f1, fill=(255, 255, 255))
        d.text((x0, 12 * S + 60 * S), detail, font=f2, fill=(228, 232, 240))
        return bg
    W, H = 380 * S, 150 * S
    bg = Image.new('RGB', (W + 24 * S, H + 24 * S), (38, 36, 42)); d = ImageDraw.Draw(bg)
    d.rounded_rectangle([12 * S, 12 * S, 12 * S + W, 12 * S + H], radius=44 * S, fill=(0, 0, 0))
    bg.paste(img, (12 * S + 22 * S, 12 * S + (H - img.size[1]) // 2), img)
    f1, f2, f3 = font(17 * S), font(14 * S), font(13 * S)
    x0 = 12 * S + 22 * S + img.size[0] + 16 * S
    d.text((x0, 12 * S + 40 * S), title, font=f1, fill=(255, 255, 255))
    d.text((x0, 12 * S + 66 * S), detail, font=f2, fill=(0x9A, 0xA3, 0xA5))
    d.text((x0, 12 * S + 94 * S), '12:34', font=f3, fill=A)
    return bg


def save_gif(frames, path, ms, transparent=False):
    """frames: RGBA 或 RGB；ms: 一个数或每帧一个。透明版 alpha<128 当透明。"""
    if transparent:
        outs = []
        for f in frames:
            f = f.convert('RGBA'); a = f.split()[3]
            q = f.convert('RGB').quantize(colors=255, method=Image.Quantize.MEDIANCUT)
            q.paste(255, mask=a.point(lambda v: 255 if v < 128 else 0))
            q.info['transparency'] = 255; outs.append(q)
        outs[0].save(path, save_all=True, append_images=outs[1:], duration=ms, loop=0, disposal=2, transparency=255, optimize=False)
    else:
        fs = [f.convert('RGB') for f in frames]
        fs[0].save(path, save_all=True, append_images=fs[1:], duration=ms, loop=0, optimize=False)


def export(key, title, detail, accent, palette, z, frames, smooth, island, lock=None, out=None, scale_compact=4, scale_expanded=8, scale_gif=10):
    """出全套：smooth.gif / smooth-dark.gif / island-compact.gif（真实）/ island-compact-想要的.gif /
    island-expanded.gif / island-minimal.gif / lock.gif / frames.json / report.json。返回报告。"""
    out = out or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out', key)
    os.makedirs(out, exist_ok=True)
    seq = expand(island, N)
    shown, bad, stats = simulate(frames, seq, z)
    ms = int(SLOT * 1000)
    save_gif([pill(f.image(palette, scale_compact), 'compact', title, detail, accent) for f in shown], f'{out}/island-compact.gif', ms)
    save_gif([pill(frames[i].image(palette, scale_compact), 'compact', title, detail, accent) for i in seq], f'{out}/island-compact-想要的.gif', ms)
    save_gif([pill(f.image(palette, scale_expanded), 'expanded', title, detail, accent) for f in shown], f'{out}/island-expanded.gif', ms)
    # 最小态：只放螃蟹那一块（去掉两边道具），用同一套模拟
    save_gif([pill(f.image(palette, 3), 'minimal', title, detail, accent) for f in shown], f'{out}/island-minimal.gif', ms)
    if lock:
        lk = expand(lock, 10)
        save_gif([pill(frames[i].image(palette, scale_expanded), 'lock', title, detail, accent) for i in lk], f'{out}/lock.gif', 1000)
    sm = [frames[i].image(palette, scale_gif) for i, _ in smooth]; dur = [d for _, d in smooth]
    save_gif(sm, f'{out}/smooth.gif', dur, transparent=True)
    dk = []
    for im in sm:
        b = Image.new('RGBA', im.size, (0, 0, 0, 255)); b.alpha_composite(im); dk.append(b)
    save_gif(dk, f'{out}/smooth-dark.gif', dur)
    json.dump({'key': key, 'title': title, 'detail': detail, 'accent': accent, 'palette': palette, 'z': z,
               'grid': [frames[0].w, frames[0].h], 'frames': [f.rows() for f in frames],
               'smooth': smooth, 'island': seq, 'lock': expand(lock, 10) if lock else None},
              open(f'{out}/frames.json', 'w'), ensure_ascii=False)
    tot = frames[0].w * frames[0].h
    rep = {'key': key, '残影点数每格': bad, '最多一格残影': max(bad), '残影占比%': round(100 * sum(bad) / (N * tot), 2), **stats}
    json.dump(rep, open(f'{out}/report.json', 'w'), ensure_ascii=False, indent=1)
    return rep


def sheet(cells, palette, path, scale=8, cols=6, label_font=18, bg=(24, 24, 28)):
    """表情表 / 帧表：cells = [(名字, Frame), ...]，黑底格子带名字。"""
    w, h = cells[0][1].w * scale, cells[0][1].h * scale
    cw, ch = w + 24, h + 24 + label_font + 10
    rows = (len(cells) + cols - 1) // cols
    im = Image.new('RGB', (cols * cw + 12, rows * ch + 12), bg); d = ImageDraw.Draw(im)
    f = font(label_font)
    for i, (name, fr) in enumerate(cells):
        x, y = 12 + (i % cols) * cw, 12 + (i // cols) * ch
        d.rectangle([x, y, x + w + 12, y + h + 12], fill=(0, 0, 0))
        im.paste(fr.image(palette, scale), (x + 6, y + 6), fr.image(palette, scale))
        d.text((x + 2, y + h + 16), name, font=f, fill=(220, 214, 204))
    im.save(path)
    return path


def simulate_tiers(slow, fast, z, hold=4):
    """两层：slow = 每 hold 格才换一次的大东西，整块交给同一组计时器（换就是整张换，不留残影、不用蒙版）；
    fast = 每格都可能变的小东西，四组轮流 + 黑蒙版（规矩同 simulate：熄了要黑满 1 秒）。
    显示 = 蒙版 > fast 最上层颜色 > slow。目标 = fast 盖在 slow 上。返回 (显示帧, 目标帧, 每格残影点数, 层统计)。"""
    n = len(slow); W, H = slow[0].w, slow[0].h
    zi = {c: i for i, c in enumerate(z)}
    for f in fast:
        for c in f.px.values(): zi.setdefault(c, -1)
    target = [s.over(f) for s, f in zip(slow, fast)]
    shown, bad = [], []
    fast_pts = {p for f in fast for p in f.px}
    for k in range(n):
        f = slow[k].copy(); b = 0
        for p in fast_pts:
            masked = any(all(target[(k - d + e) % n].px.get(p) is None for e in range(4)) for d in range(4))
            if masked: f.px.pop(p, None); continue
            cands = [fast[(k - d) % n].px.get(p) for d in range(4)]
            cands = [c for c in cands if c is not None]
            if cands: f.px[p] = max(cands, key=lambda c: zi[c])
        for y in range(H):
            for x in range(W):
                if f.px.get((x, y)) != target[k].px.get((x, y)): b += 1
        shown.append(f); bad.append(b)
    static = {p for p, c in slow[0].px.items() if all(s.px.get(p) == c for s in slow)}
    slow_cols = {c for s in slow for p, c in s.px.items() if p not in static}
    fast_cols = {c for f in fast for c in f.px.values()}
    stats = {'慢层颜色': sorted(slow_cols), '快层颜色': sorted(fast_cols),
             '计时器层数': len(slow_cols) + (len(fast_cols) * 4 + 4 if fast_cols else 0), '静态点': len(static)}
    return shown, target, bad, stats
