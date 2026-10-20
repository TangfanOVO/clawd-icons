#!/usr/bin/env python3
"""小螃蟹 · 在挑吃的（food）—— 生成同目录的 food.svg（python3 crabs/food/gen.py）
一圈 L=10 秒。灵动岛每秒在整秒处拍一个姿势（S0..S9），顺滑版在整秒之间做过渡。
  S0 抱着骰子，眼睛往右上瞟：吃什么呢      S1 举过头顶往左摇（>< 使劲）
  S2 往右摇（>< 使劲）                      S3 扔出去，骰子飞到右上，抬眼追着看
  S4 骰子往下掉（翻了一面）                 S5 落地，吓得一蹦，头上一个「!」，落地冒星星
  S6 凑过去，手搭在骰子上，低头看是几       S7 骰子上冒出一碗面，^^ 拍手一蹦
  S8 搓手 A（腮红）面冒热气                 S9 搓手 B（腮红）；之后面收回去、骰子捡回怀里
快层（每秒四下）：fx-tick（摇骰子的咔啦）、fx-star（落地星星）、fx-steam（面的热气）。
任何会在整秒被拍到的变化都离整秒远一点；整秒之间才过渡。
"""
import os
L = 10.0
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('OUT') or os.path.join(HERE, 'food.svg')

BODY, DARK, BLACK, WHITE, YEL, BLUE, RED = '#DE886D', '#A85A3A', '#000000', '#FFFFFF', '#FFE066', '#5C9CE6', '#FF5365'
LIGHT = '#F4B39B'       # 手挪到身子前面时换成浅一号的颜色，跟身子分得开
css = []


def pct(t):
    return f'{t / L * 100:.3f}'.rstrip('0').rstrip('.') + '%'


def anim(name, sel, frames, fmt, ease='ease-in-out', extra=''):
    """frames: [(t, v) 或 (t, v, 这一段的缓动)]；自动补 0% / 100%（首尾同值）。"""
    fr = sorted(frames, key=lambda f: f[0])
    if fr[0][0] > 0: fr.insert(0, (0.0,) + tuple(fr[-1][1:2]))
    assert all(a[0] < b[0] for a, b in zip(fr, fr[1:])), (name, [f[0] for f in fr])
    if fr[-1][0] < L: fr.append((L, fr[0][1]))      # 末尾不写就接回开头；写了 L 就用写的（转圈用）
    lines = []
    for f in fr:
        e = f'animation-timing-function: {f[2]}; ' if len(f) > 2 else ''
        lines.append(f'  {pct(f[0])} {{ {fmt(f[1])} {e}}}')
    css.append(f'{sel} {{ animation: {name} {L:g}s infinite {ease};{extra} }}')
    css.append(f'@keyframes {name} {{\n' + '\n'.join(lines) + '\n}')


tr = lambda v: f'transform: translate({v[0]:g}px, {v[1]:g}px);'
op = lambda v: f'opacity: {v:g};'


def windows(spans):
    """spans: [(开, 关), ...]（可以跨 0 点：开 > 关）→ 一串 (t, 0/1)，配 step-end。"""
    on = lambda t: any((a <= t < b) if a < b else (t >= a or t < b) for a, b in spans)
    ts = sorted({0.0} | {a for a, b in spans} | {b for a, b in spans})
    return [(t, 1 if on(t) else 0) for t in ts if t < L]


# ───────────────────────── 姿势 ─────────────────────────
# 身子（躯干 + 眼睛 + 腮红）偏移；手是绝对位置（左上角）；骰子绝对位置（左上角，5×5）
CHEST_L, CHEST_R, CHEST_D = (4, 10), (9, 10), (5, 9)
OVL, OVR = 3, 7                                  # 举过头顶：骰子 x（y=0）
def over(x):                                      # 举着骰子时两只手的位置（扣住骰子下面两个角）
    return (x - 1, 3), (x + 4, 3)
RUB_A, RUB_B = ((5, 10), (8, 11)), ((5, 11), (8, 10))

# S0：骰子托在左手手心上，举在脑袋左边，眼睛往左上瞟着它
HOLD_D, HOLD_L, HOLD_R = (-3, 2), (0, 7), (13, 9)
body = [(0, (0, 0)), (0.3, (0, 0)), (0.55, (0, 0))]
lh = [(0, HOLD_L), (0.3, HOLD_L), (0.55, (1, 3))]
rh = [(0, HOLD_R), (0.3, HOLD_R), (0.55, (6, 3))]
dice = [(0, HOLD_D), (0.3, HOLD_D), (0.55, (2, 0))]
rot = [(0, 0), (0.3, 0), (0.55, 0)]
# 摇：每 0.2 秒换一边，整秒（1.0 左、2.0 右）正好停在边上、不歪
side = {0.8: 'R', 1.0: 'L', 1.2: 'R', 1.4: 'L', 1.6: 'R', 1.8: 'L', 2.0: 'R', 2.2: 'L', 2.4: 'R'}
for t, s in side.items():
    x = OVR if s == 'R' else OVL
    l_, r_ = over(x)
    body.append((t, (1, 0) if s == 'R' else (-1, 0)))
    lh.append((t, l_)); rh.append((t, r_)); dice.append((t, (x, 0))); rot.append((t, 0))
    if t < 2.4:                                   # 两边中间那一下骰子歪一点、往上颠一点
        m = t + 0.1; nx = OVL if s == 'R' else OVR; mx = (x + nx) / 2
        dice.append((m, (mx, -0.6))); rot.append((m, 10 if s == 'R' else -10))
# 扔
body += [(2.52, (0, 0)), (3.0, (0, 0))]
lh += [(2.52, (4, 4)), (2.66, (2, 6)), (3.0, (0, 7))]
rh += [(2.52, (9, 4)), (2.66, (12, 5)), (3.0, (14, 5))]
dice += [(2.52, (6, 1)), (2.66, (9, -1.5), 'linear'), (2.83, (12, -2.2)), (3.0, (14, 0)), (3.35, (14, 0.8)),
         (4.0, (14, 4), 'ease-in'), (4.45, (14, 10)), (4.58, (14, 8.8)), (4.72, (14, 10))]
rot += [(2.52, -12), (2.66, 30, 'linear'), (2.83, 110), (3.0, 180, 'linear'), (3.35, 240, 'linear'), (4.0, 360, 'linear'),
        (4.45, 450), (4.58, 462), (4.72, 450)]
# 落地吓一蹦
body += [(3.7, (0, 0)), (4.45, (0, 0)), (4.6, (0, -1)), (5.0, (0, -1)), (5.3, (0, -1))]
lh += [(3.7, (0, 9)), (4.45, (0, 9)), (4.6, (0, 3)), (5.0, (0, 3)), (5.3, (0, 3))]
rh += [(3.7, (13, 9)), (4.45, (13, 9)), (4.6, (13, 3)), (5.0, (13, 3)), (5.3, (13, 3))]
# 凑过去看
body += [(5.7, (1, 0)), (6.0, (1, 0)), (6.3, (1, 0))]
lh += [(5.7, (1, 9)), (6.0, (1, 9)), (6.3, (1, 9))]
rh += [(5.7, (14, 9)), (6.0, (14, 9)), (6.3, (14, 9))]
dice += [(6.0, (14, 10)), (9.5, (14, 10))]
rot += [(9.5, 450)]
# 冒出面：拍手一蹦
body += [(6.7, (0, -1)), (7.0, (0, -1)), (7.25, (0, -1)), (7.45, (0, 0))]
lh += [(6.5, (3, 11)), (6.7, (5, 9)), (7.0, (5, 9)), (7.25, (5, 9))]      # 6.5 从眼睛下面绕过来，别挡脸
rh += [(6.5, (11, 11)), (6.7, (8, 9)), (7.0, (8, 9)), (7.25, (8, 9))]
# 搓手：0.2 秒换一下，8.0 = A，9.0 = B
for i, t in enumerate([7.45, 7.6, 7.8, 8.0, 8.2, 8.4, 8.6, 8.8, 9.0, 9.2, 9.4]):
    a = RUB_B if i % 2 == 0 else RUB_A
    lh.append((t, a[0])); rh.append((t, a[1]))
body += [(9.0, (0, 0)), (9.5, (0, 0))]
# 收：面缩回去，骰子跳回怀里
body += [(9.75, (0, 0))]
lh += [(9.6, (5, 10)), (9.82, (0, 8))]
rh += [(9.6, (8, 10)), (9.82, (13, 9))]
dice += [(9.62, (13, 4)), (9.76, (7, -2.5)), (9.9, (-1, 0))]
rot += [(9.62, 480), (9.76, 580), (9.9, 680), (L, 720)]      # 720 ≡ 0，接回开头不倒转

gaze = [(0, (-1, -1)), (0.45, (-1, -1)), (0.6, (0, 0)), (2.5, (0, 0)), (2.7, (1, -1)), (3.0, (1, -1)), (3.6, (1, -1)),
        (3.9, (1, 0)), (4.0, (1, 0)), (5.0, (1, 0)), (5.3, (1, 0)), (5.7, (1, 1)), (6.0, (1, 1)), (6.5, (1, 1)),
        (6.7, (0, 0)), (9.6, (0, 0)), (9.8, (-1, -1))]

# ───────────────────────── CSS ─────────────────────────
css.append('.breathe { transform-origin: 7.5px 13px; animation: breathe 2.5s infinite ease-in-out; }')
css.append('@keyframes breathe { 0%, 100% { transform: scale(1, 1); } 50% { transform: scale(1.02, 0.98) translate(0, 0.25px); } }')
css.append('.shadow { transform-origin: 7.5px 15.5px; animation: shadow-breathe 2.5s infinite ease-in-out; }')
css.append('@keyframes shadow-breathe { 0%, 100% { transform: scaleX(1); opacity: 0.5; } 50% { transform: scaleX(1.03); opacity: 0.45; } }')

anim('bd', '.bd', body, tr)
# 腿跟着身子走——左右挪一起挪，往上蹦一起蹦（脚离地，影子留在地上），往下蹲腿不动
anim('legs', '.legs', [(t, (v[0], min(v[1], 0))) + tuple(e) for t, v, *e in body], tr)
anim('lh', '.lh', [(t, (v[0] - 0, v[1] - 9)) + tuple(e) for t, v, *e in lh], tr)
anim('rh', '.rh', [(t, (v[0] - 13, v[1] - 9)) + tuple(e) for t, v, *e in rh], tr)
# 拍手、搓手那几秒手在身子前面：两只手换成浅一号的颜色
anim('hdk', '.hdk', windows([(6.65, 9.6)]), op, 'step-end')
anim('gaze', '.gaze', gaze, tr)
anim('dmv', '.dmv', dice, tr)
anim('drot', '.drot', rot, lambda v: f'transform: rotate({v:g}deg);', extra=' transform-origin: 2.5px 2.5px;')
# 落地那一下压扁、弹起来拉长（只在整秒之间）
anim('dsq', '.dsq', [(0, 1), (4.38, 1), (4.45, 0.8), (4.52, 1.08), (4.66, 1), (4.72, 0.88), (4.8, 1)],
     lambda v: f'transform: scale({2 - v:g}, {v:g});', extra=' transform-origin: 2.5px 5px;')
# 眼睛：方眼 / >< / ^^
anim('e-rect', '.e-rect', windows([(9.62, 0.62), (2.52, 6.68)]), op, 'step-end')
anim('e-x', '.e-x', windows([(0.62, 2.52)]), op, 'step-end')
anim('e-hap', '.e-hap', windows([(6.68, 9.62)]), op, 'step-end')
anim('blink', '.blink', [(0, 1), (0.38, 1), (0.45, 0.1), (0.52, 1), (5.48, 1), (5.55, 0.1), (5.62, 1)],
     lambda v: f'transform: scaleY({v:g});', 'linear', ' transform-origin: 7.5px 9px;')
anim('blush', '.blush', windows([(7.6, 9.6)]), op, 'step-end')
# 骰子的面：5 抱着摇 → 3 → 6 → 2 翻着飞 → 4（红）落地
anim('f5', '.f5', windows([(9.86, 2.72)]), op, 'step-end')
anim('f3', '.f3', windows([(2.72, 3.4)]), op, 'step-end')
anim('f6', '.f6', windows([(3.4, 3.75)]), op, 'step-end')
anim('f2', '.f2', windows([(3.75, 4.3)]), op, 'step-end')
anim('f4', '.f4', windows([(4.3, 9.86)]), op, 'step-end')
anim('dsh', '.dsh', windows([(4.45, 9.58)]), op, 'step-end')
# 碗：6.62 弹出来，9.45 收回去
anim('bwv', '.bwv', windows([(6.62, 9.72)]), op, 'step-end')
anim('bwsc', '.bwsc', [(0, 0.3), (6.62, 0.3), (6.8, 1.2), (6.95, 1), (9.45, 1), (9.58, 1.15), (9.72, 0.3)],
     lambda v: f'transform: scale({v:g});', extra=' transform-origin: 16px 9px;')
# 「!」
anim('bang', '.bang', windows([(4.55, 5.62)]), op, 'step-end')

# ───────────────────────── 快层（每 0.25 秒一格） ─────────────────────────
fx_svg = []
SLOT = 0.25


def particle(cls, shape, path, color):
    """path: [(格号 k, x, y), ...] 连续格；格号 k 的时刻 = k*0.25。"""
    i = len(fx_svg)
    name = f'p{i}'
    ks = [k for k, _, _ in path]
    t0, t1 = ks[0] * SLOT, ks[-1] * SLOT
    pos = [(k * SLOT, (x, y), 'linear') for k, x, y in path]
    # 开着之前、关了之后都停在端点，免得满屏乱飘
    vis = windows([(max(0.0, t0 - 0.1) if t0 > 0 else L - 0.1, min(L - 0.001, t1 + 0.15))])
    anim(name + 'm', f'.{name}', pos, tr, 'linear')
    anim(name + 'o', f'.{name}o', vis, op, 'step-end')
    if shape == 'dot': d = '<rect x="0" y="0" width="1" height="1"/>'
    elif shape == 'plus': d = '<rect x="-1" y="0" width="3" height="1"/><rect x="0" y="-1" width="1" height="3"/>'
    elif shape == 'wisp': d = '<rect x="0" y="0" width="1" height="2"/>'
    fx_svg.append(f'<g class="{cls}"><g class="{name}o"><g class="{name}" fill="{color}">{d}</g></g></g>')


# 摇骰子的咔啦（往外甩的小点）：t1 左边，t2 右边
for path in ([(4, 2, 1), (5, 1, 0)], [(5, 1, 3), (6, 0, 2), (7, -1, 1)], [(6, 2, 0), (7, 1, 1)],
             [(8, 12, 1), (9, 13, 0)], [(9, 12, 2), (10, 13, 1)], [(10, 12, 0), (11, 13, 2)],
             [(8, 5, 0)], [(10, 6, 1), (11, 5, 2)]):
    particle('fx-tick', 'dot', path, YEL)
# 落地星星 + 看是几的时候亮一亮
# 6 秒身子往右凑，右脚踩在 (12,14)：那一格不放星星，不然会残影
for shape, path in (('plus', [(20, 16, 8)]), ('dot', [(20, 13, 13)]), ('dot', [(21, 13, 14)]),
                    ('plus', [(21, 17, 4)]), ('plus', [(22, 15, 2)]), ('dot', [(23, 18, 2)]),
                    ('dot', [(24, 18, 9)]), ('dot', [(25, 13, 13)]), ('dot', [(26, 16, 9)]), ('dot', [(27, 13, 14)])):
    particle('fx-star', shape, path, YEL)
# 热气：一缕一缕往上飘，左右轻轻扭；同一个点熄了一秒内不再亮
def wisp(k0, x0, dx, n=4):
    return [(k0 + j, x0 + (dx if j % 2 else 0), 3 - j) for j in range(n) if k0 + j < 40]
def cells(shape, x, y):
    return {'dot': [(x, y)], 'plus': [(x - 1, y), (x, y), (x + 1, y), (x, y - 1), (x, y + 1)], 'wisp': [(x, y), (x, y + 1)]}[shape]
def lit_map(parts):
    m = {}
    for shape, path in parts:
        for k, x, y in path:
            for c in cells(shape, x, y): m.setdefault(c, set()).add(k % 40)
    return m
def ok_relight(m):
    for c, ks in m.items():
        ks = sorted(ks)
        for a, b in zip(ks, ks[1:] + [ks[0] + 40]):
            if 1 < b - a <= 4: return False
    return True
steam = []
BOWL = {(17, 5), (18, 4)} | {(x, 5) for x in range(14, 17)} | {(x, y) for y in range(6, 9) for x in range(13, 19)}
def wisp_y(k0, x0, dx, y0, n=4):
    return [(k0 + j, x0 + (dx if j % 2 else 0), y0 - j) for j in range(n) if k0 + j < 40 and y0 - j >= 0]
# 两对列各管各的：14/15 往右扭、17/16 往左扭；同一对列两缕之间隔 5 格（熄了的点黑满一秒才再亮）
for k0, x0, dx, n in ((28, 14, 1, 4), (30, 17, -1, 4), (33, 14, 1, 4), (35, 17, -1, 4), (38, 14, 1, 1)):   # 最后一口只冒一下，碗收回去前就散
    w = ('wisp', wisp_y(k0, x0, dx, 3, n))
    assert not ({c for k, x, y in w[1] for c in cells('wisp', x, y)} & BOWL)
    steam.append(w)
assert ok_relight(lit_map(steam))
for shape, path in steam:
    particle('fx-steam', shape, path, WHITE)
print('steam wisps:', [(p[0][0], p[0][1]) for _, p in steam])

# ───────────────────────── 画 ─────────────────────────
def pips(face, col):
    P = {5: [(1, 1), (3, 1), (2, 2), (1, 3), (3, 3)], 3: [(3, 1), (2, 2), (1, 3)], 6: [(1, 1), (3, 1), (1, 2), (3, 2), (1, 3), (3, 3)],
         2: [(1, 1), (3, 3)], 4: [(1, 1), (3, 1), (1, 3), (3, 3)]}[face]
    return ''.join(f'<rect x="{x}" y="{y}" width="1" height="1"/>' for x, y in P)


svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-15 -25 45 45" width="500" height="500" shape-rendering="crispEdges">
  <!-- 在挑吃的 · 掷骰子选晚饭（food）。10 秒一圈，一秒一个姿势：
       0 抱着骰子想吃什么 → 1 举起来往左摇 → 2 往右摇 → 3 扔出去 → 4 翻着往下掉 → 5 落地，吓一蹦「!」
       → 6 凑过去看是几 → 7 冒出一碗面，^^ 拍手 → 8 搓手 → 9 搓手；然后面收回去、骰子捡回怀里。
       身子是 clawd-tank 的静态底；骰子、面碗、表情（&gt;&lt; 和 ^^ 是整数格像素字）、手在身子前面时的浅色都是自己画的。
       飘浮物（摇骰子的咔啦 fx-tick、落地星星 fx-star、热气 fx-steam）0.25 秒一格，只在身子旁边的空地里。 -->
  <defs>
    <style>
{chr(10).join(css)}
    </style>
  </defs>

  <rect class="shadow" x="3" y="15" width="9" height="1" fill="{BLACK}" opacity="0.5"/>
  <g class="dsh"><rect class="shadow-d" x="14" y="15" width="5" height="1" fill="{BLACK}" opacity="0.5"/></g>

  <!-- 腿：clawd-tank 原版的长短（第 13 行起、高 2），跟着身子挪 -->
  <g class="legs" fill="{BODY}">
    <rect x="3" y="13" width="1" height="2"/>
    <rect x="5" y="13" width="1" height="2"/>
    <rect x="9" y="13" width="1" height="2"/>
    <rect x="11" y="13" width="1" height="2"/>
  </g>

  <g class="bd"><g class="breathe">
    <rect x="2" y="6" width="11" height="7" fill="{BODY}"/>
    <g class="gaze">
      <g class="e-rect"><g class="blink" fill="{BLACK}">
        <rect x="4" y="8" width="1" height="2"/>
        <rect x="10" y="8" width="1" height="2"/>
      </g></g>
      <g class="e-x" fill="{BLACK}">
        <rect x="4" y="8" width="1" height="1"/><rect x="5" y="9" width="1" height="1"/><rect x="4" y="10" width="1" height="1"/>
        <rect x="10" y="8" width="1" height="1"/><rect x="9" y="9" width="1" height="1"/><rect x="10" y="10" width="1" height="1"/>
      </g>
      <g class="e-hap" fill="{BLACK}">
        <rect x="4" y="8" width="1" height="1"/><rect x="3" y="9" width="1" height="1"/><rect x="5" y="9" width="1" height="1"/>
        <rect x="10" y="8" width="1" height="1"/><rect x="9" y="9" width="1" height="1"/><rect x="11" y="9" width="1" height="1"/>
      </g>
    </g>
    <g class="blush" fill="{RED}">
      <rect x="3" y="10" width="2" height="1"/>
      <rect x="10" y="10" width="2" height="1"/>
    </g>
  </g></g>

  <g class="bang" fill="{WHITE}">
    <rect x="7" y="0" width="1" height="3"/>
    <rect x="7" y="4" width="1" height="1"/>
  </g>

  <g class="dmv"><g class="dsq"><g class="drot">
    <rect x="0" y="0" width="5" height="5" fill="{WHITE}"/>
    <g class="f5" fill="{BLACK}">{pips(5, BLACK)}</g>
    <g class="f3" fill="{BLACK}">{pips(3, BLACK)}</g>
    <g class="f6" fill="{BLACK}">{pips(6, BLACK)}</g>
    <g class="f2" fill="{BLACK}">{pips(2, BLACK)}</g>
    <g class="f4" fill="{RED}">{pips(4, RED)}</g>
  </g></g></g>

  <g class="bwv"><g class="bwsc">
    <rect x="14" y="5" width="3" height="1" fill="{YEL}"/>
    <rect x="17" y="5" width="1" height="1" fill="{DARK}"/>
    <rect x="18" y="4" width="1" height="1" fill="{DARK}"/>
    <rect x="13" y="6" width="6" height="1" fill="{BLUE}"/>
    <rect x="14" y="7" width="4" height="1" fill="{BLUE}"/>
    <rect x="15" y="8" width="2" height="1" fill="{BLUE}"/>
  </g></g>

  <g fill="{BODY}">
    <g class="lh"><rect x="0" y="9" width="2" height="2"/></g>
    <g class="rh"><rect x="13" y="9" width="2" height="2"/></g>
  </g>
  <g class="hdk" fill="{LIGHT}">
    <g class="lh"><rect x="0" y="9" width="2" height="2"/></g>
    <g class="rh"><rect x="13" y="9" width="2" height="2"/></g>
  </g>

  {chr(10).join('  ' + s for s in fx_svg)}
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(svg)
print('wrote', os.path.abspath(OUT), len(svg), 'bytes')
