#!/usr/bin/env python3
"""在看外面 · window 的生成脚本
跑：python3 crabs/window/gen.py  → 写同目录的 window.svg，顺手检查快层排班。

10 秒一圈，灵动岛每秒取一个姿势（t = 0..9 整秒那一刻），快层每 0.25 秒一格（40 格）。
"""
import os, sys
OUT = os.environ.get('OUT') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'window.svg')
L = 10.0
SLOT = L / 40

BODY = '#DE886D'; INK = '#000000'; FRAME = '#90A4AE'; CLOUD = '#CFD8DC'; RAIN = '#BFEAFF'; GOLD = '#FFE066'

def pct(t):
    return f'{100 * t / L:.3f}'.rstrip('0').rstrip('.') + '%'

# ───────────── 慢层：每秒一个姿势 ─────────────
def pose_kf(name, vals, fmt, pre=0.3, post=0.5, extras=()):
    """vals[k] = 第 k 秒那一刻的姿势；姿势在 [k-pre, k+post] 停住，其余时间过渡。extras = [(t, v)] 只给顺滑版加的小细节（别落在整秒上）。"""
    pts = {}
    for k, v in enumerate(vals):
        pts[round((k - pre) % L, 4)] = v
        pts[round(k + post, 4)] = v
    for t, v in extras:
        pts[round(t, 4)] = v
    for k, v in enumerate(vals):          # 整秒那一刻钉死在姿势上（extras 不许把它带歪）
        pts[float(k)] = v
    pts[0.0] = vals[0]; pts[L] = vals[0]
    body = '\n'.join(f'        {pct(t)} {{ {fmt(pts[t])} }}' for t in sorted(pts))
    return f'      @keyframes {name} {{\n{body}\n      }}'

def step_kf(name, vals, fmt, at=0.6, at_k=None):
    """整块换（step-end）：第 k 秒的值从 k-1+at 开始生效，所以整秒那一刻一定是 vals[k]。at_k = {k: 另给的生效点}。"""
    pts = {0.0: vals[0]}
    for k in range(1, 10):
        pts[round(k - 1 + (at_k or {}).get(k, at), 4)] = vals[k]
    pts[round(9 + at, 4)] = vals[0]; pts[L] = vals[0]
    body = '\n'.join(f'        {pct(t)} {{ {fmt(pts[t])} }}' for t in sorted(pts))
    return f'      @keyframes {name} {{\n{body}\n      }}'

tr = lambda v: f'transform: translate({v[0]}px, {v[1]}px);'
op = lambda v: f'opacity: {v};'

#            0       1       2       3       4        5        6        7       8        9
EYE   = ['n',    'c',    'n',    'x',    'n',     'n',     'h',     'h',    'n',     'n']
GAZE  = [(1, 0), (1, 0), (1, 0), (1, 0), (1, 1),  (1, -1), (1, -1), (1, 0), (1, -1), (1, 0)]
BODYP = [(0, 0), (0, 0), (1, 0), (1, 0), (0, 0),  (0, 0),  (0, 0),  (1, 0), (0, 0),  (0, 0)]
HOP   = [(0, 0)] * 6 + [(0, -1)] + [(0, 0)] * 3          # 6 秒整只蹦起来（腿一起）
ARM_R = [(0, 0), (0, 0), (0, -1), (0, -1), (0, 0), (0, 0), (0, -2), (0, 0), (0, 0),  (0, 0)]
ARM_L = [(0, 0), (0, 0), (0, 0), (0, 0),  (0, 0),  (0, 0),  (0, -2), (0, 0), (0, 0),  (0, 0)]
CLOUD_PX = [(1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (3, 1), (1, 2), (2, 2), (3, 2)]   # 相对 (19, 1)；底边缺一角，月亮从缝里露一点
CLOUDX = [(0, 0)] * 5 + [(2, 0), (4, 0), (4, 0), (4, 0), (2, 0)]

css = []
BM_EXTRAS = [
    # 3 秒：凉！打个哆嗦（只在顺滑版里，整秒那一刻是原位）
    (3.08, (1.5, 0)), (3.16, (0.5, 0)), (3.24, (1.5, 0)), (3.32, (0.6, 0)), (3.4, (1, 0)),
    # 6 秒：先往下一蹲再蹿
    (5.6, (0, 0.6))]
HOP_EXTRAS = [(5.62, (0, 0)), (5.82, (0, -2)), (6.3, (0, -1.2)), (6.6, (0, 0.2))]
css.append(pose_kf('bm', BODYP, tr, extras=BM_EXTRAS))
css.append(pose_kf('hop', HOP, tr, extras=HOP_EXTRAS))
# 腿跟着身子走——左右挪一起挪，往上蹦一起蹦（脚离地，影子留在地上），往下蹲腿不动
up = lambda v: (v[0], min(v[1], 0))
css.append(pose_kf('legs-bm', [up(v) for v in BODYP], tr, extras=[(t, up(v)) for t, v in BM_EXTRAS]))
css.append(pose_kf('legs-hop', [up(v) for v in HOP], tr, extras=[(t, up(v)) for t, v in HOP_EXTRAS]))
css.append(pose_kf('gaze', GAZE, tr))
css.append(pose_kf('arm-r', ARM_R, tr, extras=[
    (1.62, (0, 0.5)),                       # 伸手前先往下一压
    (2.62, (0, -1.3)),                      # 托着等雨
    (4.08, (0, -0.6)), (4.18, (0, 0.2)), (4.28, (0, -0.4)), (4.38, (0, 0)),   # 甩甩手上的水
    (6.25, (0, -2.4))]))
css.append(pose_kf('arm-l', ARM_L, tr, extras=[(6.25, (0, -2.4))]))
css.append(pose_kf('cloud', CLOUDX, tr, pre=0.4, post=0.3))
for t in 'ncxh':
    css.append(step_kf(f'eye-{t}', [1 if e == t else 0 for e in EYE], op, at_k={3: 0.86}))   # 雨点 2.75 秒砸到钳子上，眯眼要在砸到之后
css.append('''      @keyframes blink {
        0%, 46.5%, 48.5%, 86.5%, 88.5%, 100% { transform: scaleY(1); }
        47.5%, 87.5% { transform: scaleY(0.1); }
      }''')

# ───────────── 快层：雨、星星、水花（每 0.25 秒一格） ─────────────
# 窗：左右框 x=14/22，中梃 x=18，横档 y=5，窗台 y=11。四格：左上 15-17×1-4，右上 19-21×1-4，左下 15-17×6-10，右下 19-21×6-10
PANE = {'UL': (1, 3), 'LL': (6, 4), 'LR': (6, 4)}   # (起始行, 走几格)
DROPS = [  # (起始格, 窗格, 列)
    (36, 'UL', 16), (37, 'LR', 19), (37, 'LL', 15), (38, 'UL', 17), (39, 'LR', 21),
    (0, 'LL', 16), (1, 'UL', 15), (2, 'LR', 20), (3, 'LL', 17), (4, 'UL', 16),
    (5, 'LR', 19), (6, 'UL', 17), (7, 'LR', 21), (8, 'UL', 15), (9, 'LR', 20),
    (10, 'UL', 16), (11, 'LR', 19), (12, 'UL', 17), (13, 'LR', 21), (14, 'UL', 15),
    (15, 'LR', 20), (16, 'UL', 16), (17, 'LR', 19), (17, 'LL', 16),
]
CATCH = (11, 15, 6)       # 第 11 格，第 15 列，从横档后面冒出来，正好落在伸出窗外的钳子上（钳子占 14-15 × 8-9）
# 水花：每颗一串 (格, x, y)；第一颗往右上蹦，第二颗往上蹦钻到横档后面
SPLASH = [[(12, 16, 7), (13, 17, 6)], [(12, 16, 6)]]
# 星星：大的 = 一下鼓起来再缩回去（中心亮三格，十字的四个角只在中间那一格亮），小的 = 一个点亮两格
def plus(cx, cy):
    return [(cx, cy - 1), (cx - 1, cy), (cx + 1, cy), (cx, cy + 1)]
STARS = [  # (起始格, 中心, 大/小)
    (22, (16, 2), 'big'), (24, (17, 4), 'dot'), (25, (20, 8), 'big'), (27, (17, 8), 'dot'),
    (28, (21, 6), 'dot'), (29, (16, 3), 'big'), (30, (15, 4), 'dot'), (32, (20, 9), 'big'),
    (31, (21, 10), 'dot'),
]

def cyc_kf(name, events):
    """events = [(t, {prop: val})]，线性插值，首尾按一圈接上。"""
    ev = sorted(((round(t % L, 5), d) for t, d in events), key=lambda e: e[0])
    t0, d0 = ev[0]; tn, dn = ev[-1]
    # 0 时刻的值：在 (tn-L, dn) 和 (t0, d0) 之间插
    span = t0 - (tn - L); a = (0 - (tn - L)) / span if span else 0
    v0 = {k: dn[k] + (d0[k] - dn[k]) * a for k in d0}
    pts = [(0.0, v0)] + [e for e in ev if 0 < e[0] < L] + [(L, v0)]
    if ev[0][0] == 0: pts[0] = ev[0]
    def f(d):
        s = []
        if 'y' in d: s.append(f'transform: translate({d.get("x", 0):.3f}px, {d["y"]:.3f}px);')
        if 'o' in d: s.append(f'opacity: {round(d["o"], 3)};')
        return ' '.join(s)
    body = '\n'.join(f'        {pct(t)} {{ {f(d)} }}' for t, d in pts)
    return f'      @keyframes {name} {{\n{body}\n      }}'

EPS = 0.002
fast_px = {}      # (x, y) -> 亮着的格子集合
def lit(x, y, k, what):
    fast_px.setdefault((x, y), {})[k % 40] = what

els = []
# 雨：每格往下走 1，长 2；在第 a-0.5 格从框/横档后面露头，最后一格之后 0.5 格钻到下面那根木条后面
for i, (a, pane, col) in enumerate(DROPS):
    y0, n = PANE[pane]
    t_on, t_off = (a - 0.5) * SLOT, (a + n - 1 + 0.5) * SLOT
    y_on, y_off = y0 - 0.5, y0 + n - 1 + 0.5
    for j in range(n):
        lit(col, y0 + j, a + j, 'rain'); lit(col, y0 + j + 1, a + j, 'rain')
    css.append(cyc_kf(f'r{i}', [(t_on - EPS, {'y': y_on, 'o': 0}), (t_on, {'y': y_on, 'o': 1}),
                                 (t_off, {'y': y_off, 'o': 1}), (t_off + EPS, {'y': y_off, 'o': 0})]))
    els.append(f'    <rect class="rain r{i}" x="{col}" y="0" width="1" height="2" fill="{RAIN}"/>')
a, col, y0 = CATCH
t_on, t_off = (a - 0.5) * SLOT, (a + 0.5) * SLOT
lit(col, y0, a, 'rain'); lit(col, y0 + 1, a, 'rain')
css.append(cyc_kf('rc', [(t_on - EPS, {'y': y0 - 0.5, 'o': 0}), (t_on, {'y': y0 - 0.5, 'o': 1}),
                          (t_off, {'y': y0 + 0.5, 'o': 1}), (t_off + EPS, {'y': y0 + 0.5, 'o': 0})]))
els.append(f'    <rect class="rain rc" x="{col}" y="0" width="1" height="2" fill="{RAIN}"/>')
# 水花：一颗一颗沿着自己那串格子走，最后一格之后再往同方向飘半格消失
for side, path in enumerate(SPLASH):
    k1, x1, y1 = path[0]
    for k, x, y in path: lit(x, y, k, 'splash')
    ev = [((k1 - 0.5) * SLOT - EPS, {'x': 0, 'y': 0.5, 'o': 0}), ((k1 - 0.5) * SLOT, {'x': 0, 'y': 0.5, 'o': 1})]
    for k, x, y in path: ev.append((k * SLOT, {'x': x - x1, 'y': y - y1, 'o': 1}))
    kl, xl, yl = path[-1]
    dx, dy = ((xl - path[-2][1]), (yl - path[-2][2])) if len(path) > 1 else (0, -1)
    ev.append(((kl + 0.5) * SLOT, {'x': xl - x1 + dx * 0.5, 'y': yl - y1 + dy * 0.5, 'o': 1}))
    ev.append(((kl + 0.5) * SLOT + EPS, {'x': 0, 'y': 0.5, 'o': 0}))
    css.append(cyc_kf(f's{side}', ev))
    els.append(f'    <rect class="splash s{side}" x="{x1}" y="{y1}" width="1" height="1" fill="{RAIN}"/>')
# 星星：中心亮 [a, a+2]，十字的四个角只在 a+1 亮；小星星亮 [a, a+1]
for i, (a, (cx, cy), kind) in enumerate(STARS):
    if kind == 'big':     # 一个点 → 整颗十字 → 又缩回一个点 → 灭
        on = [(cx, cy, a, a + 2)] + [(x, y, a + 1, a + 1) for x, y in plus(cx, cy)]
    else:
        on = [(cx, cy, a, a + 1)]
    for j, (x, y, k0, k1) in enumerate(on):
        for k in range(k0, k1 + 1): lit(x, y, k, 'star')
        t_on, t_off = (k0 - 0.5) * SLOT, (k1 + 0.5) * SLOT
        css.append(cyc_kf(f'st{i}-{j}', [(t_on - EPS, {'o': 0}), (t_on, {'o': 1}), (t_off, {'o': 1}), (t_off + EPS, {'o': 0})]))
        els.append(f'    <rect class="star st{i}-{j}" x="{x}" y="{y}" width="1" height="1" fill="{GOLD}"/>')

# ───────────── 自查：快层每个点熄了要黑满 4 格；不许碰到慢层 ─────────────
def slow_px(sec):
    """第 sec 秒（整秒那一刻）慢层占了窗格里哪些点（只算窗格里，快层只在窗格里走）。"""
    bx, by = BODYP[sec]; ax, ay = ARM_R[sec]
    pts = set()
    X, Y = 13 + bx + ax, 9 + by + ay + HOP[sec][1]
    pts |= {(X + i, Y + j) for i in range(2) for j in range(2)}
    cx = CLOUDX[sec][0]
    pts |= {(19 + cx + i, 1 + j) for i, j in CLOUD_PX if 19 <= 19 + cx + i <= 21}
    moon = {(20, 1), (21, 1), (19, 2), (19, 3), (20, 4), (21, 4)}
    pts |= moon
    frame = {(x, y) for x in (14, 18, 22) for y in range(0, 12)} | {(x, 5) for x in range(14, 23)} | {(x, 0) for x in range(14, 23)} | {(x, 11) for x in range(13, 23)}
    return pts | frame

problems = []
for p, ks in fast_px.items():
    on = sorted(ks)
    for k in on:
        # 亮着的这一格起，慢层在这一点要空满 4 格
        for d in range(4):
            if p in slow_px(((k + d) % 40) // 4):
                problems.append(f'{p} 第{k}格亮 {ks[k]}，第{(k + d) % 40}格慢层有东西'); break
    # 熄灭段至少 4 格
    for k in on:
        if (k + 1) % 40 in ks: continue
        gap = 1
        while (k + gap) % 40 not in ks and gap < 40: gap += 1
        if gap - 1 < 4 and gap < 40:
            problems.append(f'{p} 第{k}格熄，第{(k + gap) % 40}格又亮（只黑了 {gap - 1} 格）')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-15 -25 45 45" width="500" height="500" shape-rendering="crispEdges">
  <!-- 在看外面 · window（身子是 clawd-tank 的静态底；窗、雨、云、月亮、星星、表情都是自己画的，表情是整数格像素字）
       10 秒一圈，一秒一个姿势（灵动岛每秒取一张）：
         0 扒着窗台看雨            1 闭眼听雨
         2 把钳子伸出窗外接雨      3 雨点砸在钳子上，凉得眯成 &gt;&lt;，打个哆嗦
         4 收手甩水，抬头看天      5 雨停了，云往右挪，月亮露出半边
         6 月亮全出来了，蹿起来举手 ^ ^     7 趴近窗户笑 ^ ^
         8 抬头看月亮              9 云又飘回来，雨又下了
       快层（每秒四下）：rain 雨丝、splash 水花、star 星星，只在四格窗玻璃里走，不碰窗框、钳子、月亮和云。 -->
  <defs>
    <style>
      .breathe {{ transform-origin: 7.5px 13px; animation: breathe 2.5s infinite ease-in-out; }}
      @keyframes breathe {{
        0%, 100% {{ transform: scale(1, 1); }}
        50% {{ transform: scale(1.02, 0.98); }}
      }}
      .shadow {{ transform-origin: 7.5px 15.5px; animation: shadow-breathe 2.5s infinite ease-in-out; }}
      @keyframes shadow-breathe {{
        0%, 100% {{ transform: scaleX(1); }}
        50% {{ transform: scaleX(1.03); }}
      }}
      .hop {{ animation: hop 10s infinite ease-in-out; }}
      .legs-hop {{ animation: legs-hop 10s infinite ease-in-out; }}
      .legs-bm {{ animation: legs-bm 10s infinite ease-in-out; }}
      .bm {{ animation: bm 10s infinite ease-in-out; }}
      .gaze {{ animation: gaze 10s infinite ease-in-out; }}
      .arm-r {{ animation: arm-r 10s infinite ease-in-out; }}
      .arm-l {{ animation: arm-l 10s infinite ease-in-out; }}
      .cloud {{ animation: cloud 10s infinite ease-in-out; }}
      .eye-n {{ animation: eye-n 10s infinite step-end; }}
      .eye-c {{ opacity: 0; animation: eye-c 10s infinite step-end; }}
      .eye-x {{ opacity: 0; animation: eye-x 10s infinite step-end; }}
      .eye-h {{ opacity: 0; animation: eye-h 10s infinite step-end; }}
      .blink {{ transform-origin: 7.5px 9px; animation: blink 10s infinite linear; }}
      .rain, .splash, .star {{ opacity: 0; animation-duration: 10s; animation-iteration-count: infinite; animation-timing-function: linear; }}
{chr(10).join(f'      .{c} {{ animation-name: {c}; }}' for c in [f'r{i}' for i in range(len(DROPS))] + ['rc'] + [f's{i}' for i in range(len(SPLASH))] + [l.split('class="star ')[1].split('"')[0] for l in els if 'class="star ' in l])}
{chr(10).join(css)}
    </style>
    <clipPath id="pane-ur">
      <rect x="19" y="1" width="3" height="4"/>
    </clipPath>
  </defs>

  <rect class="shadow" x="3" y="15" width="9" height="1" fill="{INK}" opacity="0.45"/>

  <!-- 窗外：雨、水花、星星、月亮、云（都在窗框后面） -->
  <g>
{chr(10).join(els)}
  </g>
  <g fill="{GOLD}">
    <rect x="20" y="1" width="2" height="1"/>
    <rect x="19" y="2" width="1" height="2"/>
    <rect x="20" y="4" width="2" height="1"/>
  </g>
  <g clip-path="url(#pane-ur)">
    <g class="cloud" fill="{CLOUD}">
      <rect x="20" y="1" width="2" height="1"/>
      <rect x="19" y="2" width="4" height="1"/>
      <rect x="20" y="3" width="3" height="1"/>
    </g>
  </g>

  <!-- 窗：上框、左右框、中梃、横档、窗台 -->
  <g fill="{FRAME}">
    <rect x="14" y="0" width="9" height="1"/>
    <rect x="14" y="1" width="1" height="10"/>
    <rect x="22" y="1" width="1" height="10"/>
    <rect x="18" y="1" width="1" height="10"/>
    <rect x="15" y="5" width="7" height="1"/>
    <rect x="13" y="11" width="10" height="1"/>
  </g>

  <!-- 小螃蟹：腿是 clawd-tank 原版的长短（第 13 行起、高 2），跟着身子左右挪；6 秒整只蹦一下 -->
  <g class="legs-hop"><g class="legs-bm" fill="{BODY}">
    <rect x="3" y="13" width="1" height="2"/>
    <rect x="5" y="13" width="1" height="2"/>
    <rect x="9" y="13" width="1" height="2"/>
    <rect x="11" y="13" width="1" height="2"/>
  </g></g>
  <g class="hop">
  <g class="bm">
    <g class="breathe">
      <rect x="2" y="6" width="11" height="7" fill="{BODY}"/>
      <g class="arm-l"><rect x="0" y="9" width="2" height="2" fill="{BODY}"/></g>
      <g class="arm-r"><rect x="13" y="9" width="2" height="2" fill="{BODY}"/></g>
      <g class="gaze">
        <g class="eye-n">
          <g class="blink" fill="{INK}">
            <rect x="4" y="8" width="1" height="2"/>
            <rect x="10" y="8" width="1" height="2"/>
          </g>
        </g>
        <g class="eye-c" fill="{INK}">
          <rect x="4" y="9" width="2" height="1"/>
          <rect x="9" y="9" width="2" height="1"/>
        </g>
        <g class="eye-x" fill="{INK}">
          <rect x="4" y="8" width="1" height="1"/><rect x="5" y="9" width="1" height="1"/><rect x="4" y="10" width="1" height="1"/>
          <rect x="10" y="8" width="1" height="1"/><rect x="9" y="9" width="1" height="1"/><rect x="10" y="10" width="1" height="1"/>
        </g>
        <g class="eye-h" fill="{INK}">
          <rect x="4" y="8" width="1" height="1"/><rect x="3" y="9" width="1" height="1"/><rect x="5" y="9" width="1" height="1"/>
          <rect x="10" y="8" width="1" height="1"/><rect x="9" y="9" width="1" height="1"/><rect x="11" y="9" width="1" height="1"/>
        </g>
      </g>
    </g>
  </g>
  </g>
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print('wrote', OUT, f'{len(svg)} bytes; drops {len(DROPS)}, stars {len(STARS)}')
print('fast check:', 'OK' if not problems else '\n  ' + '\n  '.join(problems))
