#!/usr/bin/env python3
"""在钓鱼 · fish 的生成器：算钓竿 / 线 / 浮漂的几何，写出同目录的 fish.svg。
    python3 crabs/fish/gen.py
"""
import math, os

L = 10.0                    # 一圈 10 秒，1% = 0.1 秒
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('OUT') or os.path.join(HERE, 'fish.svg')

C_BODY, C_EYE = '#DE886D', '#000000'
C_WATER, C_SURF = '#2E7AA8', '#7FD1E8'
C_WHITE, C_RED, C_ROD = '#FFFFFF', '#FF5365', '#A85A3A'

PIV = (14.5, 10.0); ROD = 7.5        # 竿子绕右手转，竿长 7.5


def tip(m):
    th = math.radians(m['th'])
    return (PIV[0] + m['bx'] + m['ax'] + ROD * math.sin(th), PIV[1] + m['by'] + m['ay'] - ROD * math.cos(th))


def P(t):
    return f'{t * 100 / L:.2f}'.rstrip('0').rstrip('.') + '%'


def f(v):
    s = f'{v:.3f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


# ── 主表：身子、右手、竿、线，一起走同一组关键帧（竿和线的反转才能每一刻都对得上）
# l = ('float', y) → 浮漂顶在 y；数字 = 直接给线长
W0 = dict(bx=0, by=0, ax=0, ay=0, th=17, ph=0, l=('float', 11.5))      # 等着：浮漂漂在水面
MASTER = [
    (0.0, W0), (0.22, dict(W0, l=('float', 11.7))), (0.45, W0),        # 浮漂轻轻一浮一沉
    (0.9, dict(W0, by=0.5)), (1.05, dict(W0, by=0.5)),                 # 打瞌睡：身子往下塌一点
    (1.38, dict(W0, by=0.8, l=('float', 11.65))), (1.72, dict(W0, by=0.5)),   # 头一点
    (1.85, dict(W0, by=-0.5, th=19, l=('float', 12.2))),                # 有动静：浮漂往下一点，人一激灵
    (2.45, dict(W0, by=-0.5, th=19, l=('float', 12.2))),
    (2.62, dict(bx=0, by=-1, ax=0.5, ay=-1.5, th=0, ph=-32, l=3)),      # 一拽：拽空了
    (2.8, dict(bx=0, by=-1, ax=0.5, ay=-1.5, th=5, ph=-25, l=3)),
    (3.4, dict(bx=0, by=-1, ax=0.5, ay=-1.5, th=5, ph=-25, l=3)),
    (3.8, dict(bx=0, by=0, ax=0, ay=-1, th=12, ph=6, l=2)),             # 空钩晃着，挠头
    (4.0, dict(bx=0, by=0, ax=0, ay=-1, th=12, ph=0, l=2)),
    (4.2, dict(bx=0, by=0, ax=0, ay=-1, th=12, ph=-4, l=2)),
    (4.45, dict(bx=0, by=0, ax=0, ay=-1, th=12, ph=0, l=2)),
    (4.6, dict(bx=0, by=0, ax=0, ay=-1, th=-5, ph=28, l=2)),            # 往后一甩
    (4.8, dict(W0, th=21, l=('float', 11.5))),                          # 抛出去
    (4.95, W0), (5.08, W0), (5.3, dict(W0, l=('float', 11.7))), (5.5, W0), (5.7, W0),
    (5.85, dict(bx=0.5, by=0.5, ax=0.5, ay=0.5, th=24, ph=0, l=('float', 14))),   # 咬钩了：浮漂整个被拖下去
    (6.05, dict(bx=0.5, by=0.5, ax=0.5, ay=0.5, th=24, ph=0, l=('float', 14))),
    (6.2, dict(bx=0.5, by=0.5, ax=0.5, ay=0.5, th=26.5, ph=0, l=('float', 14.4))),
    (6.45, dict(bx=0.5, by=0.5, ax=0.5, ay=0.5, th=24, ph=0, l=('float', 14))),
    (6.62, dict(bx=-0.5, by=-1, ax=0.5, ay=-1.5, th=6, ph=-18, l=5.4)),           # 拽上来
    (6.75, dict(bx=-0.5, by=-1, ax=0.5, ay=-1.5, th=10, ph=-8, l=5.4)),
    (7.35, dict(bx=-0.5, by=-1, ax=0.5, ay=-1.5, th=10, ph=-8, l=5.4)),
    (7.8, dict(bx=0, by=-0.5, ax=0.5, ay=-1.5, th=16, ph=0, l=0.6)),               # 举起来看：鱼挂在脸旁边
    (8.45, dict(bx=0, by=-0.5, ax=0.5, ay=-1.5, th=16, ph=0, l=0.6)),
    (8.85, dict(W0, l=('float', 8.8))),                                            # 放回去：鱼一半没进水
    (9.35, dict(W0, l=('float', 8.8))),
    (9.8, W0), (10.0, W0),
]


def resolve(m):
    m = dict(m)
    if isinstance(m['l'], tuple):
        m['l'] = m['l'][1] - tip(m)[1]
    return m


MASTER = [(t, resolve(m)) for t, m in MASTER]


def kf(name, pts, fn):
    rows = []
    for t, m in pts:
        rows.append(f'        {P(t)} {{ {fn(m)} }}')
    return f'      @keyframes {name} {{\n' + '\n'.join(rows) + '\n      }'


def tl(pts):
    """pts: [(t, css)] → keyframes body"""
    return '\n'.join(f'        {P(t)} {{ {c} }}' for t, c in pts)


css = []
css.append(kf('bm', MASTER, lambda m: f'transform: translate({f(m["bx"])}px, {f(m["by"])}px);'))
# 腿跟着身子走——左右挪一起挪，往上蹦一起蹦（脚离地，影子留在地上），往下塌腿不动
css.append(kf('legs', MASTER, lambda m: f'transform: translate({f(m["bx"])}px, {f(min(m["by"], 0))}px);'))
css.append(kf('am', MASTER, lambda m: f'transform: translate({f(m["ax"])}px, {f(m["ay"])}px);'))
css.append(kf('rod', MASTER, lambda m: f'transform: rotate({f(m["th"])}deg);'))
css.append(kf('hang', MASTER, lambda m: f'transform: rotate({f(m["ph"] - m["th"])}deg);'))
css.append(kf('ln', MASTER, lambda m: f'transform: scaleY({f(m["l"])});'))
css.append(kf('tk', MASTER, lambda m: f'transform: translate(0px, {f(m["l"])}px);'))


def tr(x, y, r):
    return f'transform: translate({f(x)}px, {f(y)}px) rotate({f(r)}deg);'


REST, UP, STARTLE = (0, 0, 0), (-0.5, -2, 30), (-0.5, -1, 20)
SCR_HI, SCR_LO = (1.5, -4, 35), (0.6, -2.6, 5)
YAY, YAY2 = (-1, -3, 60), (-1, -3.4, 70)
WAVE, WAVE2 = (-0.5, -2.5, 40), (-0.5, -2.3, 8)
ARM_L = [(0, REST), (1.72, REST), (1.85, STARTLE), (2.45, STARTLE), (2.62, (-0.5, -2.2, 38)), (2.8, UP), (3.4, UP),
         (3.6, SCR_LO), (3.75, SCR_HI), (3.88, SCR_LO), (4.0, SCR_HI), (4.12, SCR_LO), (4.24, SCR_HI), (4.36, SCR_LO), (4.45, SCR_HI),
         (4.65, REST), (5.7, REST), (5.85, STARTLE), (6.45, STARTLE), (6.62, (-0.5, -2.2, 38)), (6.75, UP), (7.35, UP),
         (7.8, YAY), (8.0, YAY), (8.12, YAY2), (8.24, YAY), (8.36, YAY2), (8.45, YAY),
         (8.85, WAVE), (9.0, WAVE), (9.12, WAVE2), (9.25, WAVE), (9.38, WAVE2), (9.5, WAVE), (9.85, REST), (10, REST)]
css.append('      @keyframes arm-l {\n' + tl([(t, tr(*v)) for t, v in ARM_L]) + '\n      }')

# 眼睛：方眼（看浮漂）/ 闭眼线（打瞌睡）/ >< 使劲 / ^^ 高兴
def vis(name, on):
    """on: [(t, 0/1)] step-end"""
    return f'      @keyframes {name} {{\n' + tl([(t, f'opacity: {v};') for t, v in on]) + '\n      }'


css.append(vis('eye-rect', [(0, 1), (0.7, 0), (1.82, 1), (2.55, 0), (3.45, 1), (6.55, 0), (9.75, 1), (10, 1)]))
css.append(vis('eye-line', [(0, 0), (0.7, 1), (1.82, 0), (10, 0)]))
css.append(vis('eye-x', [(0, 0), (2.55, 1), (3.45, 0), (6.55, 1), (7.5, 0), (10, 0)]))
css.append(vis('eye-smile', [(0, 0), (7.5, 1), (9.75, 0), (10, 0)]))
G0 = (1.5, 0.5)
GAZE = [(0, G0), (0.45, G0), (1.75, G0), (1.85, (2, 0)), (2.45, (2, 0)), (3.45, (0, 0)), (3.62, (-1, -1)), (4.45, (-1, -1)),
        (4.75, G0), (5.7, G0), (5.85, (2, 0.5)), (6.5, (2, 0.5)), (6.55, (0, 0)), (9.75, (0, 0)), (9.9, G0), (10, G0)]
css.append('      @keyframes gaze {\n' + tl([(t, f'transform: translate({f(x)}px, {f(y)}px);') for t, (x, y) in GAZE]) + '\n      }')
BLINK = [(0, 1), (0.45, 1), (0.65, 0.35), (0.7, 0.35), (0.72, 1), (3.55, 1), (3.6, 0.1), (3.66, 1), (5.25, 1), (5.3, 0.1), (5.36, 1), (10, 1)]
css.append('      @keyframes blink {\n' + tl([(t, f'transform: scaleY({f(v)});') for t, v in BLINK]) + '\n      }')

# 头上的小东西：! ? 心
css.append(vis('bang-vis', [(0, 0), (1.85, 1), (2.5, 0), (5.85, 1), (6.5, 0), (10, 0)]))
css.append('      @keyframes bang-pop {\n' + tl([(t, f'transform: translate(0px, {f(v)}px);') for t, v in
                                                [(0, 0.8), (1.85, 0.8), (1.95, 0), (5.85, 0.8), (5.95, 0), (10, 0)]]) + '\n      }')
css.append(vis('qm-vis', [(0, 0), (3.6, 1), (4.5, 0), (10, 0)]))
css.append('      @keyframes qm-pop {\n' + tl([(t, f'transform: translate(0px, {f(v)}px);') for t, v in
                                              [(0, 1), (3.6, 1), (3.72, 0), (4.5, 0), (10, 0)]]) + '\n      }')
HEART = [(0, (5, 4.5, 0.5)), (7.75, (5, 4.5, 0.5)), (7.9, (5, 2.8, 1.1)), (8.0, (5, 2.8, 1)), (8.45, (5, 2.3, 1)),
         (9.0, (4, 1.3, 0.9)), (9.5, (3.5, -0.2, 0.7)), (10, (3.5, -0.2, 0.7))]
css.append('      @keyframes heart-move {\n' + tl([(t, f'transform: translate({f(x)}px, {f(y)}px) scale({f(s)});') for t, (x, y, s) in HEART]) + '\n      }')
css.append(vis('heart-vis', [(0, 0), (7.75, 1), (9.55, 0), (10, 0)]))
ZZ = [(0, (0, 1)), (0.75, (0, 1)), (1.0, (0, 0)), (1.7, (-1, -1)), (10, (-1, -1))]      # 1 秒整那一刻正好在 (0, 0)
css.append('      @keyframes zz-move {\n' + tl([(t, f'transform: translate({f(x)}px, {f(y)}px);') for t, (x, y) in ZZ]) + '\n      }')
css.append(vis('zz-vis', [(0, 0), (0.8, 1), (1.72, 0), (10, 0)]))
css.append(vis('fish-vis', [(0, 0), (5.5, 1), (9.7, 0), (10, 0)]))
css.append(vis('hook-vis', [(0, 1), (5.5, 0), (9.7, 1), (10, 1)]))
WIG = [(0, 0), (6.6, 0), (6.75, -10), (6.9, 14), (7.0, 0), (7.12, -14), (7.24, 12), (7.35, 0), (7.6, 10), (7.8, -10), (8.0, -8),
       (8.12, -14), (8.24, 14), (8.36, -10), (8.5, 8), (8.7, -4), (9.0, 0), (10, 0)]
css.append('      @keyframes wig {\n' + tl([(t, f'transform: rotate({f(v)}deg);') for t, v in WIG]) + '\n      }')

# ── 快层：水圈 / 水花 / 小气泡（每秒四下，只在空地里走，不回头）
FAST = []  # (cls, extra-class, fill, w, h, [(t, x, y, o)])


def tip_at(t):
    for tt, m in MASTER:
        if abs(tt - t) < 1e-6: return tip(m)
    raise KeyError(t)


def ring(n, t0, cx, right_short=False, right=True):
    # 一圈水纹 = 左右两截短浪，贴着水面往外推：灵动岛里拍到两下（t0、t0+0.25），顺滑版里是一路滑出去
    # y 12.5–13 这条带只给水纹用，水花气泡都在它上面；右边离画框近，短浪只有半格宽，不出 19.4
    def dash(name, w, p0, p1, t_end):
        v = (p1 - p0) / 0.25
        pts = [(t0 - 0.06, p0 - v * 0.05, 12.5, 0), (t0 - 0.05, p0 - v * 0.05, 12.5, 1),
               (t_end, p0 + v * (t_end - t0), 12.5, 1), (t_end + 0.05, p0 + v * (t_end + 0.05 - t0), 12.5, 0)]
        FAST.append(('fx-ring', name, C_SURF, w, 0.5, pts))
    dash(f'ring{n}l', 1, cx - 2, cx - 3, t0 + 0.4)
    if not right: return
    if right_short:   # 右边紧挨着下一秒咬钩的那根线：只冒一拍
        dash(f'ring{n}r', 0.5, cx + 1, cx + 1.2, t0 + 0.12); return
    dash(f'ring{n}r', 0.5, cx + 1, min(cx + 2, 18.9), t0 + 0.4)


ring(0, 0.0, tip_at(0.0)[0])
ring(1, 2.0, tip_at(1.85)[0])
ring(2, 5.0, tip_at(4.95)[0], right_short=True)
ring(3, 6.0, tip_at(5.85)[0], right=False)
# 气泡：打瞌睡时水底下冒两个
FAST.append(('fx-bub', 'bub0', C_WHITE, 0.5, 0.5, [(1.19, 15.3, 12.0, 0), (1.2, 15.3, 12.0, 1), (1.75, 15.3, 10.35, 1), (1.8, 15.3, 10.2, 0)]))
FAST.append(('fx-bub', 'bub1', C_WHITE, 0.5, 0.5, [(1.44, 17.8, 12.0, 0), (1.45, 17.8, 12.0, 1), (1.75, 17.8, 11.1, 1), (1.8, 17.8, 10.95, 0)]))


def drop(n, pts):
    t_on, t_off = pts[0][0], pts[-1][0]
    q = [(t_on - 0.01, pts[0][1], pts[0][2], 0)] + [(t, x, y, 1) for t, x, y in pts] + [(t_off + 0.05, pts[-1][1], pts[-1][2], 0)]
    FAST.append(('fx-drop', f'drop{n}', C_WHITE, 0.5, 0.5, q))


# 拽空：浮漂出水溅两滴
drop(0, [(2.7, 15.75, 12.0), (3.0, 15.1, 11.4), (3.25, 14.5, 10.9), (3.5, 14.0, 11.2)])
drop(1, [(2.7, 18.0, 12.0), (3.0, 18.5, 11.3), (3.25, 18.9, 11.0)])
# 钓上来：大一点的水花
drop(2, [(6.68, 15.6, 11.95), (7.0, 15.0, 11.6), (7.25, 14.4, 10.9), (7.5, 13.9, 10.7), (7.75, 13.5, 11.1)])
drop(3, [(6.95, 15.3, 11.0), (7.0, 15.2, 10.8), (7.25, 14.7, 9.9), (7.5, 14.3, 9.5)])
drop(4, [(6.95, 18.75, 11.6), (7.0, 18.8, 11.3), (7.25, 18.9, 10.7)])
# 放回去：扑通
drop(5, [(8.8, 14.9, 12.0), (9.0, 14.7, 11.9), (9.25, 14.1, 11.3), (9.5, 13.6, 11.1), (9.75, 13.2, 11.5)])
drop(6, [(8.8, 18.1, 12.0), (9.0, 18.3, 11.9), (9.25, 18.7, 11.3), (9.5, 18.9, 11.0)])

def periodic(pts):
    """把可能跨过 0 / 10 秒的点折回一圈里；0% 和 100% 用跨圈插值补上，首尾接得上。"""
    q = sorted(((t % L), x, y, o) for t, x, y, o in pts)
    a, b = q[-1], q[0]                       # 跨圈那一段：a（圈尾）→ b（下一圈开头）
    span = b[0] + L - a[0]
    k = (L - a[0]) / span if span > 0 else 0
    edge = (a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k, a[3] if a[3] == b[3] else (a[3] if k < 0.5 else b[3]))
    body = []
    if q[0][0] > 1e-9: body.append((0.0,) + edge)
    body += q
    if q[-1][0] < L - 1e-9: body.append((L,) + edge)
    return body


fast_css, fast_svg = [], []
for cls, ec, fill, w, h, pts in FAST:
    body = periodic(pts)
    fast_css.append(f'      .{ec} {{ animation: {ec} 10s infinite linear; }}\n'
                    f'      @keyframes {ec} {{\n' + tl([(t, f'transform: translate({f(x)}px, {f(y)}px); opacity: {o};') for t, x, y, o in body]) + '\n      }')
    fast_svg.append(f'  <rect class="{cls} {ec}" x="0" y="0" width="{f(w)}" height="{f(h)}" fill="{fill}" opacity="0"/>')

for t, m in MASTER:
    tx, ty = tip(m)
    print(f'{t:5.2f}  tip=({tx:6.2f},{ty:5.2f})  th={m["th"]:5.1f} ph={m["ph"]:5.1f} l={m["l"]:5.2f}  bob-top-y={ty + m["l"]:5.2f}')

SVG = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-15 -25 45 45" width="500" height="500" shape-rendering="crispEdges">
  <!-- 在钓鱼 · fish（身子是 clawd-tank 的静态底；钓竿、浮漂、鱼、水、表情、Z ! ? 都是自己画的）
       10 秒一圈，一秒一个姿势（灵动岛每秒取一张）：
         0 等着，眼睛盯浮漂      1 等困了，闭眼打瞌睡     2 浮漂一沉，一激灵 !
         3 一拽，拽空了 ><       4 空钩晃着，挠头 ?        5 甩竿重抛，浮漂落水
         6 浮漂整个被拖下去 !    7 拽上来一条小白条 ><     8 举到脸边看，^^ 冒心
         9 放回水里，挥手拜拜
       快层（每秒四下）：fx-ring 水圈、fx-drop 水花、fx-bub 气泡，都在身子旁边的空地里走。
       竿、线、浮漂走同一组关键帧：hang 的转角 = 摆角 - 竿角，线每一刻都垂直挂在竿尖上。 -->
  <defs>
    <style>
      .bm {{ animation: bm 10s infinite ease-in-out; }}
      .legs {{ animation: legs 10s infinite ease-in-out; }}
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
      .am {{ animation: am 10s infinite ease-in-out; }}
      .rod {{ transform-origin: 14.5px 10px; animation: rod 10s infinite ease-in-out; }}
      .hang {{ transform-origin: 14.5px 2.5px; animation: hang 10s infinite ease-in-out; }}
      .ln {{ transform-origin: 14.5px 2.5px; animation: ln 10s infinite ease-in-out; }}
      .tk {{ animation: tk 10s infinite ease-in-out; }}
      .arm-l {{ transform-origin: 1px 10px; animation: arm-l 10s infinite ease-in-out; }}
      .gaze {{ animation: gaze 10s infinite ease-in-out; }}
      .eye-rect {{ transform-origin: 7.5px 9px; animation: eye-rect 10s infinite step-end, blink 10s infinite ease-in-out; }}
      .eye-line {{ opacity: 0; animation: eye-line 10s infinite step-end; }}
      .eye-x {{ opacity: 0; animation: eye-x 10s infinite step-end; }}
      .eye-smile {{ opacity: 0; animation: eye-smile 10s infinite step-end; }}
      .bang {{ opacity: 0; animation: bang-vis 10s infinite step-end, bang-pop 10s infinite ease-out; }}
      .qm {{ opacity: 0; animation: qm-vis 10s infinite step-end, qm-pop 10s infinite ease-out; }}
      .heart {{ opacity: 0; animation: heart-vis 10s infinite step-end, heart-move 10s infinite ease-in-out; }}
      .zz {{ opacity: 0; animation: zz-vis 10s infinite step-end, zz-move 10s infinite ease-out; }}
      .fish {{ opacity: 0; animation: fish-vis 10s infinite step-end; }}
      .fish-wig {{ transform-origin: 14.5px 5px; animation: wig 10s infinite ease-in-out; }}
      .hook {{ animation: hook-vis 10s infinite step-end; }}

{chr(10).join(css)}

{chr(10).join(fast_css)}
    </style>
    <clipPath id="dry-clip">
      <rect x="-15" y="-25" width="45" height="38"/>
      <rect x="-15" y="13" width="28" height="7"/>
    </clipPath>
  </defs>

  <rect class="shadow" x="3" y="15" width="9" height="1" fill="{C_EYE}" opacity="0.5"/>

  <!-- 腿：clawd-tank 原版的长短（第 13 行起、高 2），跟着身子挪 -->
  <g class="legs" fill="{C_BODY}">
    <rect x="3" y="13" width="1" height="2"/>
    <rect x="5" y="13" width="1" height="2"/>
    <rect x="9" y="13" width="1" height="2"/>
    <rect x="11" y="13" width="1" height="2"/>
  </g>

  <g clip-path="url(#dry-clip)">
  <g class="bm">
    <g class="breathe">
      <rect x="2" y="6" width="11" height="7" fill="{C_BODY}"/>
      <g class="arm-l"><rect x="0" y="9" width="2" height="2" fill="{C_BODY}"/></g>

      <g class="gaze">
        <g class="eye-rect" fill="{C_EYE}">
          <rect x="4" y="8" width="1" height="2"/>
          <rect x="10" y="8" width="1" height="2"/>
        </g>
        <g class="eye-line" fill="{C_EYE}">
          <rect x="4" y="9" width="2" height="1"/>
          <rect x="9" y="9" width="2" height="1"/>
        </g>
      </g>
      <!-- 表情都是整数格的像素字：使劲眼是三格的 &gt; &lt;，笑眼是三格的 ^，闭眼是两格的横道 -->
      <g class="eye-x" fill="{C_EYE}">
        <rect x="4" y="8" width="1" height="1"/><rect x="5" y="9" width="1" height="1"/><rect x="4" y="10" width="1" height="1"/>
        <rect x="10" y="8" width="1" height="1"/><rect x="9" y="9" width="1" height="1"/><rect x="10" y="10" width="1" height="1"/>
      </g>
      <g class="eye-smile" fill="{C_EYE}">
        <rect x="4" y="8" width="1" height="1"/><rect x="3" y="9" width="1" height="1"/><rect x="5" y="9" width="1" height="1"/>
        <rect x="10" y="8" width="1" height="1"/><rect x="9" y="9" width="1" height="1"/><rect x="11" y="9" width="1" height="1"/>
      </g>
    </g>

    <!-- 右手 + 钓竿：一起抬、一起压 -->
    <g class="am">
      <g class="rod">
        <rect x="14" y="6" width="1" height="4" fill="{C_ROD}"/>
        <rect x="14.25" y="2.5" width="0.5" height="3.5" fill="{C_ROD}"/>
        <g class="hang">
          <rect class="ln" x="14.25" y="2.5" width="0.5" height="1" fill="{C_WHITE}"/>
          <g class="tk">
            <rect x="14" y="2.5" width="1" height="1" fill="{C_RED}"/>
            <rect x="14" y="3.5" width="1" height="1" fill="{C_WHITE}"/>
            <rect x="14.25" y="4.5" width="0.5" height="0.5" fill="{C_WHITE}"/>
            <g class="hook" fill="{C_WHITE}">
              <rect x="14.25" y="5" width="0.5" height="1"/>
              <rect x="13.75" y="6" width="1" height="0.5"/>
              <rect x="13.75" y="5.5" width="0.5" height="0.5"/>
            </g>
            <g class="fish">
              <g class="fish-wig">
                <g fill="{C_SURF}">
                  <rect x="14.25" y="5" width="0.5" height="0.5"/>
                  <rect x="13.75" y="5.5" width="1.5" height="0.5"/>
                  <rect x="13.25" y="6" width="2.5" height="1.5"/>
                  <rect x="13.75" y="7.5" width="1.5" height="0.5"/>
                  <rect x="14.25" y="8" width="0.5" height="0.5"/>
                  <rect x="13.75" y="8.5" width="1.5" height="0.5"/>
                  <rect x="13.25" y="9" width="1" height="0.5"/>
                  <rect x="14.75" y="9" width="1" height="0.5"/>
                </g>
                <rect x="13.75" y="6" width="0.5" height="0.5" fill="{C_EYE}"/>
              </g>
            </g>
          </g>
        </g>
      </g>
      <rect x="13" y="9" width="2" height="2" fill="{C_BODY}"/>
    </g>
  </g>
  </g>

  <!-- 水：画在线和鱼的后面一层，没进水的部分就被盖住 -->
  <rect x="13" y="13" width="6.5" height="0.5" fill="{C_SURF}"/>
  <rect x="13" y="13.5" width="6.5" height="1" fill="{C_WATER}"/>
  <rect x="13.5" y="14.5" width="5.5" height="1" fill="{C_WATER}"/>
  <rect x="14" y="14" width="1.5" height="0.5" fill="{C_SURF}"/>
  <rect x="17.5" y="14" width="1" height="0.5" fill="{C_SURF}"/>
  <rect x="15.5" y="15" width="1.5" height="0.5" fill="{C_SURF}"/>

  <!-- 头上：! / ? / 心 -->
  <!-- Z ! ? 是同一套 3×5 小像素字（整数格、不缩放） -->
  <g class="zz" fill="{C_WHITE}">
    <rect x="-2" y="0" width="3" height="1"/>
    <rect x="0" y="1" width="1" height="1"/>
    <rect x="-1" y="2" width="1" height="1"/>
    <rect x="-2" y="3" width="1" height="1"/>
    <rect x="-2" y="4" width="3" height="1"/>
  </g>
  <g class="bang" fill="{C_WHITE}">
    <rect x="12" y="0" width="1" height="3"/>
    <rect x="12" y="4" width="1" height="1"/>
  </g>
  <g class="qm" fill="{C_WHITE}">
    <rect x="-3" y="0" width="3" height="1"/>
    <rect x="-1" y="1" width="1" height="1"/>
    <rect x="-2" y="2" width="1" height="1"/>
    <rect x="-2" y="4" width="1" height="1"/>
  </g>
  <g class="heart" fill="{C_RED}">
    <rect x="-1" y="-1.5" width="1" height="0.5"/>
    <rect x="0.5" y="-1.5" width="1" height="0.5"/>
    <rect x="-1.5" y="-1" width="3.5" height="1"/>
    <rect x="-1" y="0" width="2.5" height="0.5"/>
    <rect x="-0.5" y="0.5" width="1.5" height="0.5"/>
    <rect x="0" y="1" width="0.5" height="0.5"/>
  </g>

  <!-- 快层 -->
{chr(10).join(fast_svg)}
</svg>
'''
open(OUT, 'w', encoding='utf-8').write(SVG)
print('wrote', os.path.abspath(OUT))
