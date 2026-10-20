#!/usr/bin/env python3
"""care（惦记你身体）SVG 生成器，写出同目录的 care.svg（python3 crabs/care/gen.py）
一秒一个姿势（slow），飘浮物按 0.25 秒一格的路径算（fast）。"""
import os

L = 10.0
SLOT = 0.25
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('OUT') or os.path.join(HERE, 'care.svg')

BODY, INK, CUP, WATER, PINK, LIGHT = '#DE886D', '#000000', '#F4F4F6', '#40C4FF', '#FF6B7A', '#F4B39B'


def pc(t):
    return f'{t / L * 100:.3f}'.rstrip('0').rstrip('.') + '%'


def fmt(v):
    return f'{v:.4f}'.rstrip('0').rstrip('.') if abs(v) > 1e-9 else '0'


# ---------- 慢层：每秒一个姿势 ----------
def pose_frames(poses, hold, trans=None):
    """poses[s] = (dx, dy)；hold[s] = 这一秒姿势停多久的一半（秒）。返回 [(t, (dx,dy))]，0..10 闭合。"""
    pts = []
    for s in range(10):
        h = hold[s] if isinstance(hold, (list, tuple)) else hold
        pts.append((s - h, poses[s])); pts.append((s + h, poses[s]))
    pts = [((t % L), v) for t, v in pts]
    pts.sort(key=lambda p: p[0])
    # 0 和 10 的值：第 0 秒的姿势（hold 覆盖了 0）
    return [(0.0, poses[0])] + pts + [(L, poses[0])]


def steps(vals, switch=None):
    """离散值（0/1 透明度）：第 s 秒的值从 switch[s] 生效到 switch[s+1]。默认 s-0.5。"""
    sw = switch or [s - 0.5 for s in range(10)]
    pts = []
    eps = 0.01
    for s in range(10):
        a = sw[s] % L
        prev = vals[(s - 1) % 10]
        pts.append((a - eps, prev)); pts.append((a, vals[s]))
    pts = [((t % L), v) for t, v in pts]
    pts.sort(key=lambda p: p[0])
    # 算 0 时刻的值
    def at(t):
        best = None
        for s in range(10):
            a = sw[s] % L
            if a <= t + 1e-9 and (best is None or a > sw[best] % L): best = s
        if best is None:
            best = max(range(10), key=lambda s: sw[s] % L)
        return vals[best]
    v0 = at(0.0)
    return [(0.0, v0)] + pts + [(L, v0)]


def kf_translate(name, frames):
    lines = [f'      @keyframes {name} {{']
    seen = set()
    for t, (dx, dy) in frames:
        k = pc(t)
        if k in seen: continue
        seen.add(k)
        lines.append(f'        {k} {{ transform: translate({fmt(dx)}px, {fmt(dy)}px); }}')
    lines.append('      }')
    return '\n'.join(lines)


def kf_opacity(name, frames):
    lines = [f'      @keyframes {name} {{']
    seen = set()
    for t, v in frames:
        k = pc(t)
        if k in seen: continue
        seen.add(k)
        lines.append(f'        {k} {{ opacity: {v}; }}')
    lines.append('      }')
    return '\n'.join(lines)


# ---------- 快层：飘浮物 ----------
def particle(path):
    """path = [(slot, x, y)]，连续格子；第一格前 0.15 秒淡入，最后一格后 0.15 秒淡出（灵动岛取样只看得到 0/1）。
    返回 [(t, opacity, x, y)]（实数轴上，可能跨 10 秒）。"""
    (k0, x0, y0), (k1, x1, y1) = path[0], path[-1]
    v0 = ((path[1][1] - x0), (path[1][2] - y0)) if len(path) > 1 else (0, 0)
    v1 = ((x1 - path[-2][1]), (y1 - path[-2][2])) if len(path) > 1 else (0, 0)
    f = 0.15 / SLOT
    pts = [(k0 * SLOT - 0.15, 0, x0 - v0[0] * f, y0 - v0[1] * f)]
    pts += [(k * SLOT, 1, x, y) for k, x, y in path]
    pts += [(k1 * SLOT + 0.15, 0, x1 + v1[0] * f, y1 + v1[1] * f)]
    return pts


def circ_frames(pts):
    """实数轴上的分段线性 → 10 秒一圈的关键帧。"""
    lo, hi = pts[0][0], pts[-1][0]
    def val(t):
        for tt in (t, t + L, t - L, t + 2 * L):
            if lo - 1e-9 <= tt <= hi + 1e-9:
                for (ta, *a), (tb, *b) in zip(pts, pts[1:]):
                    if ta - 1e-9 <= tt <= tb + 1e-9:
                        u = 0 if tb == ta else (tt - ta) / (tb - ta)
                        return tuple(p + (q - p) * u for p, q in zip(a, b))
        return (0, pts[0][2], pts[0][3])
    ts = sorted({round(t % L, 4) for t, *_ in pts} | {0.0, L})
    out = []
    for t in ts:
        o, x, y = val(t if t < L else 0.0) if t < L else val(0.0)
        out.append((t, o, x, y))
    # 关键帧挨得太近会被同一个百分比吃掉，去重
    return out


def kf_particle(name, frames):
    lines = [f'      @keyframes {name} {{']
    seen = set()
    for t, o, x, y in frames:
        k = pc(t)
        if k in seen: continue
        seen.add(k)
        lines.append(f'        {k} {{ transform: translate({fmt(x)}px, {fmt(y)}px); opacity: {fmt(o)}; }}')
    lines.append('      }')
    return '\n'.join(lines)


def run(k0, n, x, y, vel):
    """从第 k0 格开始走 n 格。vel(k) -> (vx, vy) 每格位移。"""
    path = [(k0, x, y)]
    for k in range(k0, k0 + n - 1):
        vx, vy = vel(k % 40)
        x, y = x + vx, y + vy
        path.append((k + 1, x, y))
    return path


# ===== 故事（L = 10 秒，一秒一个姿势）=====
#  9 回到身边，低头看杯子          0 抬眼担心地看你（皱眉）
#  1 凑过去吹（闭眼、嘟嘴）         2 吸口气                    3 再吹一下
#  4 眯眼笑：不烫了                 5 双手捧到你面前，皱眉看你   6 往前一递（跳一下），笑
#  7 笑眯眯等你接，冒心             8 还皱着眉看你：喝一点嘛
HOME, GIVE, GIVEUP = (0, 0), (-8.5, 4), (-8.5, 3)
TOR = [(0, 0), (1, 0), (0, 0), (1, 0), (0, 0), (0, 0), (0, -1), (0, 0), (0, 0), (0, 0)]
ARML = [(0, 0), (1, 0), (0, 0), (1, 0), (0, 0), (4.5, 1.5), (4.5, 0.5), (4.5, 1.5), (4.5, 1.5), (0, 0)]
ARMR = [(0, -1)] * 5 + [(-4.5, 1.5), (-4.5, 0.5), (-4.5, 1.5), (-4.5, 1.5), (0, -1)]   # 面前：两只爪各压住杯沿 1 格，右爪连杯把一起握住
MUG = [HOME] * 5 + [GIVE, GIVEUP, GIVE, GIVE, HOME]
HOLD = [0.3, 0.32, 0.3, 0.32, 0.3, 0.3, 0.3, 0.3, 0.28, 0.28]
# 眼睛（1 = 这一秒露出来）
EN = [1, 0, 0, 0, 0, 1, 0, 0, 1, 1]        # 方眼
EB = [1, 0, 0, 0, 0, 1, 0, 0, 1, 0]        # 皱眉
EC = [0, 1, 1, 1, 0, 0, 0, 0, 0, 0]        # 闭眼
ES = [0, 0, 0, 0, 1, 0, 1, 1, 0, 0]        # ^ ^
MO = [0, 1, 0, 1, 0, 0, 0, 0, 0, 0]        # 嘟嘴吹
CK = [0, 0, 0, 0, 0, 0, 1, 1, 0, 0]        # 腮红
DK = [0, 0, 0, 0, 0, 1, 1, 1, 1, 0]        # 手在身子前面时换成浅一号的颜色（离你更近、迎着光）
LOOK = [(0, 0)] * 9 + [(1, 0)]             # 方眼往杯子那边看
SLOOK = [(1, 0)] * 5 + [(0, 0)] * 5        # 笑眼第 4 秒朝杯子

# ===== 飘浮物 =====
BLOW = set(range(4, 8)) | set(range(12, 16))      # 吹的那两下：热气被吹歪
def steam_v(k):
    return (0.5, -0.25) if k in BLOW else (1 / 6, -0.5)
STEAM = [  # (出生格, 走几格, x, 顶 y) —— 用 gen.check() 挑过：同一格熄了一秒内不再亮、两缕热气不挨着；吹的那两下在空中的被吹歪
    (36, 8, 16.0, 4.0), (39, 7, 14.5, 4.0), (5, 4, 16.0, 4.0), (8, 7, 14.5, 4.0), (14, 5, 16.5, 4.0), (16, 4, 14.5, 4.0)]
PLUS = [(0, 19, -4, 11.0), (20, 19, -4, 11.0)]
HEART = [  # (出生格, 走几格, x, 顶 y, 大/小, vx)
    (24, 4, 6.0, 1.5, 'big', 0), (26, 4, 2.5, 3.0, 'small', -1 / 6), (28, 4, 10.0, 3.0, 'small', 1 / 6),
    (32, 4, 6.0, 2.0, 'big', 0)]

BIG = ['.XX.XX.', 'XXXXXXX', 'XXXXXXX', '.XXXXX.', '..XXX..', '...X...']
SMALL = ['XX.XX', 'XXXXX', '.XXX.', '..X..']


def cells(rows, c=0.5):
    out = []
    for j, r in enumerate(rows):
        i = 0
        while i < len(r):
            if r[i] == 'X':
                a = i
                while i < len(r) and r[i] == 'X': i += 1
                out.append(f'<rect x="{fmt(a * c)}" y="{fmt(j * c)}" width="{fmt((i - a) * c)}" height="{fmt(c)}"/>')
            else:
                i += 1
    return ''.join(out)


def build():
    css, parts = [], {}
    def slow(name, poses, hold=HOLD):
        css.append(f'      .{name} {{ animation: {name} 10s infinite ease-in-out; }}')
        css.append(kf_translate(name, pose_frames(poses, hold)))
    def disc(name, vals, switch=None):
        css.append(f'      .{name} {{ animation: {name} 10s infinite linear; }}')
        css.append(kf_opacity(name, steps(vals, switch)))
    slow('tor', TOR); slow('arml', ARML); slow('armr', ARMR); slow('mugmv', MUG)
    # 腿跟着身子走——左右挪一起挪，往上蹦一起蹦（脚离地，影子留在地上），往下蹲腿不动
    slow('legs', [(x, min(y, 0)) for x, y in TOR])
    slow('look', LOOK); slow('slook', SLOOK)
    # 眼睛在动作中途换；闭眼提前一点（凑过去的路上就闭上）
    # 右手：杯子从身边搬到面前（4→5）、再搬回去（8→9）那 0.4 秒里，右手要从杯子左边绕到右边，
    # 前面那份先藏起来，只留杯子后面那份，免得爪子从杯面上划过去（灵动岛只取整秒，不受影响）
    hide = [(4 + HOLD[4], 5 - HOLD[5]), (8 + HOLD[8], 9 - HOLD[9])]
    pts = [(0.0, 1)]
    for a, b in hide:
        pts += [(a, 1), (a + 0.02, 0), (b - 0.02, 0), (b, 1)]
    pts += [(L, 1)]
    css.append('      .armrf { animation: armrf 10s infinite linear; }')
    css.append(kf_opacity('armrf', pts))
    disc('en', EN); disc('eb', EB); disc('ec', EC); disc('es', ES); disc('mo', MO); disc('ck', CK); disc('dk', DK)

    pdefs = []
    for i, (k0, n, x, y) in enumerate(STEAM):
        nm = f'st{i}'
        css.append(f'      .{nm} {{ animation: {nm} 10s infinite linear; opacity: 0; }}')
        css.append(kf_particle(nm, circ_frames(particle(run(k0, n, x, y, steam_v)))))
        pdefs.append(('steam', nm, '<rect x="0" y="0" width="1" height="2"/>'))
    for i, (k0, n, x, y) in enumerate(PLUS):
        nm = f'pl{i}'
        css.append(f'      .{nm} {{ animation: {nm} 10s infinite linear; opacity: 0; }}')
        css.append(kf_particle(nm, circ_frames(particle(run(k0, n, x, y, lambda k: (0, -0.5))))))
        pdefs.append(('plus', nm, '<rect x="1" y="0" width="1" height="3"/><rect x="0" y="1" width="3" height="1"/>'))
    for i, (k0, n, x, y, size, vx) in enumerate(HEART):
        nm = f'ht{i}'
        css.append(f'      .{nm} {{ animation: {nm} 10s infinite linear; opacity: 0; }}')
        css.append(kf_particle(nm, circ_frames(particle(run(k0, n, x, y, lambda k, vx=vx: (vx, -0.5))))))
        pdefs.append(('heart', nm, cells(BIG if size == 'big' else SMALL)))

    def grp(cls, color):
        return f'  <g class="{cls}" fill="{color}">\n' + '\n'.join(
            f'    <g class="{nm}">{shape}</g>' for c, nm, shape in pdefs if c == cls) + '\n  </g>'

    style = '\n'.join(css)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-15 -25 45 45" width="500" height="500" shape-rendering="crispEdges">
  <!-- 惦记你身体 · 记得喝热水（care）。10 秒一圈，一秒一个姿势：
       9 低头看杯子 → 0 抬眼皱眉看你 → 1 凑过去吹 → 2 吸口气 → 3 再吹 → 4 眯眼笑（不烫了）
       → 5 双手捧到你面前、皱眉 → 6 往前一递 → 7 笑着等你接、冒心 → 8 还皱着眉：喝一点嘛。
       身子是 clawd-tank 的静态底；杯子、表情、手在身子前面时的浅色、热气加号和心都是自己画的。
       飘浮物（热气 steam、小加号 plus、心 heart）走 0.25 秒一格的路，只在身子旁边的空地里。 -->
  <defs>
    <style>
      .breathe {{ transform-origin: 7.5px 13px; animation: breathe 2.5s infinite ease-in-out; }}
      @keyframes breathe {{
        0%, 100% {{ transform: scale(1, 1); }}
        50% {{ transform: scale(1.02, 0.98) translate(0, 0.25px); }}
      }}
      .shadow {{ transform-origin: 7.5px 15.5px; animation: shadow-breathe 2.5s infinite ease-in-out; }}
      @keyframes shadow-breathe {{
        0%, 100% {{ transform: scaleX(1); opacity: 0.5; }}
        50% {{ transform: scaleX(1.03); opacity: 0.45; }}
      }}
{style}
    </style>
  </defs>

  <rect class="shadow" x="3" y="15" width="9" height="1" fill="{INK}" opacity="0.5"/>

{grp('plus', PINK)}
{grp('steam', CUP)}
{grp('heart', PINK)}

  <!-- 腿：clawd-tank 原版的长短（第 13 行起、高 2），跟着身子挪 -->
  <g class="legs" fill="{BODY}">
    <rect x="3" y="13" width="1" height="2"/>
    <rect x="5" y="13" width="1" height="2"/>
    <rect x="9" y="13" width="1" height="2"/>
    <rect x="11" y="13" width="1" height="2"/>
  </g>

  <g class="tor">
    <g class="breathe">
      <rect x="2" y="6" width="11" height="7" fill="{BODY}"/>
      <g class="en"><g class="look" fill="{INK}">
        <rect x="4" y="8" width="1" height="2"/>
        <rect x="10" y="8" width="1" height="2"/>
      </g></g>
      <g class="eb" fill="none" stroke="{INK}" stroke-width="0.6" stroke-linecap="round">
        <polyline points="3.3,7.5 5.5,6.7"/>
        <polyline points="9.5,6.7 11.7,7.5"/>
      </g>
      <g class="ec" fill="{INK}">
        <rect x="4" y="9" width="2" height="1"/>
        <rect x="9" y="9" width="2" height="1"/>
      </g>
      <g class="es"><g class="slook" fill="{INK}">
        <rect x="4" y="8" width="1" height="1"/><rect x="3" y="9" width="1" height="1"/><rect x="5" y="9" width="1" height="1"/>
        <rect x="10" y="8" width="1" height="1"/><rect x="9" y="9" width="1" height="1"/><rect x="11" y="9" width="1" height="1"/>
      </g></g>
      <rect class="mo" x="7" y="10.5" width="1" height="1" fill="{INK}"/>
      <g class="ck" fill="{PINK}">
        <rect x="2.5" y="10" width="1.5" height="0.5"/>
        <rect x="11" y="10" width="1.5" height="0.5"/>
      </g>
    </g>
  </g>

  <g fill="{BODY}"><g class="armr"><rect x="13" y="9" width="2" height="2"/></g></g>

  <g transform="translate(14 6)">
    <g class="mugmv">
      <rect x="0" y="0" width="4" height="4" fill="{CUP}"/>
      <g fill="{CUP}">
        <rect x="4" y="0.5" width="1" height="0.5"/>
        <rect x="4.5" y="0.5" width="0.5" height="2"/>
        <rect x="4" y="2" width="1" height="0.5"/>
      </g>
      <rect x="0.5" y="0.5" width="3" height="0.5" fill="{WATER}"/>
      <g fill="{PINK}">
        <rect x="1.5" y="1.5" width="0.5" height="0.5"/><rect x="2.5" y="1.5" width="0.5" height="0.5"/>
        <rect x="1.5" y="2" width="1.5" height="0.5"/><rect x="2" y="2.5" width="0.5" height="0.5"/>
      </g>
    </g>
  </g>

  <g fill="{BODY}">
    <g class="arml"><rect x="0" y="9" width="2" height="2"/></g>
    <g class="armrf"><g class="armr"><rect x="13" y="9" width="2" height="2"/></g></g>
  </g>
  <!-- 手挪到身子前面（捧杯子）那几秒，两只手换成浅一号的颜色，跟身子分得开 -->
  <g class="dk" fill="{LIGHT}">
    <g class="arml"><rect x="0" y="9" width="2" height="2"/></g>
    <g class="armrf"><g class="armr"><rect x="13" y="9" width="2" height="2"/></g></g>
  </g>
</svg>
'''
    open(OUT, 'w', encoding='utf-8').write(svg)
    print('wrote', os.path.abspath(OUT))


def check(verbose=True):
    """快层自查：按 1/6 单位一格栅格化，每格 40 拍亮/灭；熄了不到 4 拍又亮 = 残影。"""
    lit = {}
    def mark(name, path, rects):
        for k, x, y in path:
            for rx, ry, rw, rh in rects:
                for i in range(round((x + rx) * 6), round((x + rx + rw) * 6)):
                    for j in range(round((y + ry) * 6), round((y + ry + rh) * 6)):
                        lit.setdefault((i, j), {})[k % 40] = name
    for i, (k0, n, x, y) in enumerate(STEAM): mark(f'st{i}', run(k0, n, x, y, steam_v), [(0, 0, 1, 2)])
    for i, (k0, n, x, y) in enumerate(PLUS): mark(f'pl{i}', run(k0, n, x, y, lambda k: (0, -0.5)), [(1, 0, 1, 3), (0, 1, 3, 1)])
    for i, (k0, n, x, y, size, vx) in enumerate(HEART):
        mark(f'ht{i}', run(k0, n, x, y, lambda k, vx=vx: (vx, -0.5)), [(0, 0, 3.5, 3) if size == 'big' else (0, 0, 2.5, 2)])
    bad = 0; pairs = {}
    for c, ks in lit.items():
        on = [k in ks for k in range(40)]
        if all(on): continue
        start = on.index(False)
        while not on[(start - 1) % 40]: start -= 1        # 退到一段熄灭的开头
        k = 0
        while k < 40:
            if on[(start + k) % 40]: k += 1; continue
            n = 0
            while not on[(start + k + n) % 40]: n += 1
            if n < 4:
                prev = ks[(start + k - 1) % 40]; nxt = ks[(start + k + n) % 40]
                pairs[(prev, nxt)] = pairs.get((prev, nxt), 0) + n; bad += n
            k += n
    if verbose: print('快层残影(粗)', bad, sorted(pairs.items(), key=lambda p: -p[1])[:12])
    xs = [c[0] / 6 for c in lit]; ys = [c[1] / 6 for c in lit]
    if verbose: print('快层范围 x', min(xs), max(xs), 'y', min(ys), max(ys))
    return bad


if __name__ == '__main__':
    check()
    build()
