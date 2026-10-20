#!/usr/bin/env python3
"""出门走走 · travel —— 生成同目录的 travel.svg

身子是 clawd-tank 的静态底；登山包（顶上捆着一卷奶白的睡垫）、地图、鸟、叶子、尘土、表情都是自己画的。
10 秒一圈，一秒一个姿势（灵动岛每秒取一张）：
  0 走·左脚抬   1 走·右脚抬   2 走·左脚抬（右上来了只鸟）   3 走·右脚抬，抬眼看鸟
  4 蹦一下 ^^ 招手（鸟在头顶）   5 挥手拜拜，眼睛跟着鸟往左上   6 东张西望，往左看
  7 掏出地图，低头看   8 找到了 ^^ 把地图举高一点   9 收起地图接着走·右脚抬
快层（每秒四下）：dust 脚边尘土、bird 飞过的小鸟、leaf 右边飘下来的叶子。
    python3 crabs/travel/gen.py        # 写 svg ＋ 查快层
"""
import os

L = 10.0
OUT = os.environ.get('OUT') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'travel.svg')

BODY, INK, GRN, DGRN, CREAM, RED = '#DE886D', '#000000', '#9BD77A', '#4E8F3E', '#FFFDE7', '#FF5365'


def pct(t):
    s = f'{t / L * 100:.3f}'.rstrip('0').rstrip('.')
    return s + '%'


def kf(name, pts, fn):
    pts = sorted(pts, key=lambda p: p[0])
    assert pts[0][0] == 0 and pts[-1][0] == L, name
    seen = set()
    out = [f'      @keyframes {name} {{']
    for t, v in pts:
        assert t not in seen, (name, t); seen.add(t)
        out.append(f'        {pct(t)} {{ {fn(v)} }}')
    out.append('      }')
    return '\n'.join(out)


tr = lambda v: f'transform: translate({v[0]}px, {v[1]}px);'
trr = lambda v: f'transform: translate({v[0]}px, {v[1]}px) rotate({v[2]}deg);'
ty = lambda v: f'transform: translateY({v}px);'
op = lambda v: f'opacity: {v};'
sy = lambda v: f'transform: scaleY({v});'


def windows(wins, on=1, off=0):
    """step-end 开关：wins = [(起, 止), ...] 秒，这段里 on，其余 off。"""
    pts = {0.0: off, L: off}
    for a, b in wins:
        pts[a] = on; pts[b] = off
    if any(a <= 0 for a, b in wins): pts[0.0] = on
    return sorted(pts.items())


SLOT = L / 40
def mid(s):            # 第 s 格前后的半格边界（快层在格子正中取样）
    return round((s - 0.5) * SLOT, 4)


# ───────────── 慢层：姿势 ─────────────
leg_a = [(0, -1), (0.2, -1), (0.55, 0), (1.45, 0), (1.8, -1), (2.2, -1), (2.55, 0), (9.45, 0), (9.8, -1), (L, -1)]
leg_b = [(0, 0), (0.45, 0), (0.8, -1), (1.2, -1), (1.55, 0), (2.45, 0), (2.8, -1), (3.2, -1), (3.55, 0),
         (8.45, 0), (8.8, -1), (9.2, -1), (9.55, 0), (L, 0)]
bob = [(0, (0, 0)), (0.5, (0, -0.5)), (1, (0, 0)), (1.5, (0, -0.5)), (2, (0, 0)), (2.5, (0, -0.5)), (3, (0, 0)),
       (3.45, (0, 0.4)), (3.8, (0, -1)), (4.3, (0, -1)), (4.6, (0, 0)), (5.5, (0, 0)), (5.8, (-1, 0)), (6.35, (-1, 0)),
       (6.7, (0, 0)), (9, (0, 0)), (9.5, (0, -0.5)), (L, (0, 0))]
# 走路左右晃：左脚抬那步左边翘（顺时针），右脚抬那步右边翘
tilt = [(0, 5), (0.2, 5), (0.5, 0), (0.8, -5), (1.2, -5), (1.5, 0), (1.8, 5), (2.2, 5), (2.5, 0), (2.8, -5), (3.2, -5),
        (3.6, 0), (8.75, 0), (8.95, -5), (9.2, -5), (9.5, 0), (9.8, 5), (L, 5)]
gaze = [(0, (1, 0)), (2.4, (1, 0)), (2.75, (1, -1)), (3.35, (1, -1)), (3.7, (0, -1)), (4.4, (0, -1)), (4.7, (-1, -1)),
        (5.35, (-1, -1)), (5.7, (-1, 0)), (6.35, (-1, 0)), (6.75, (-1, 1)), (7.25, (-1, 1)), (7.55, (1, 1)),
        (7.7, (1, 1)), (7.85, (0, 0)), (8.5, (0, 0)), (8.8, (1, 0)), (L, (1, 0))]
rect_on = windows([(0, 3.5), (4.5, 7.8), (8.6, L)])
smile_on = windows([(3.5, 4.5), (7.8, 8.6)])
blink = [(0, 1), (1.42, 1), (1.5, 0.1), (1.58, 1), (6.47, 1), (6.55, 0.1), (6.63, 1), (9.42, 1), (9.5, 0.1), (9.58, 1), (L, 1)]
arm_l = [(0, (0, 0)), (0.2, (0, 0)), (0.8, (0, -1)), (1.2, (0, -1)), (1.8, (0, 0)), (2.2, (0, 0)), (2.8, (0, -1)),
         (3.2, (0, -1)), (3.7, (0, 0)), (6.4, (0, 0)), (6.75, (2, 2)), (7.6, (2, 2)), (7.85, (2, 1)), (8.45, (2, 1)),
         (8.8, (0, -1)), (9.2, (0, -1)), (9.8, (0, 0)), (L, (0, 0))]
arm_r = [(0, (0, -1, 0)), (0.2, (0, -1, 0)), (0.8, (0, 0, 0)), (1.2, (0, 0, 0)), (1.8, (0, -1, 0)), (2.2, (0, -1, 0)),
         (2.8, (0, 0, 0)), (3.2, (0, 0, 0)), (3.7, (1, -5, 0)), (4.0, (1, -5, 0)), (4.2, (2, -4, 0)),
         (4.4, (1, -5, 0)), (4.6, (2, -4, 0)), (4.8, (1, -5, 0)), (5.0, (2, -4, 0)), (5.2, (1, -5, 0)),
         (5.4, (2, -4, 0)), (5.75, (0, 0, 0)), (6.4, (0, 0, 0)), (6.75, (-2, 2, 0)), (7.6, (-2, 2, 0)),
         (7.85, (-2, 1, 0)), (8.45, (-2, 1, 0)), (8.8, (0, 0, 0)), (9.2, (0, 0, 0)), (9.8, (0, -1, 0)), (L, (0, -1, 0))]
map_mv = [(0, (1, 0.34)), (6.4, (1, 0.34)), (6.8, (0, 1)), (7.6, (0, 1)), (7.85, (-1, 1)), (8.45, (-1, 1)),
          (8.75, (0, 0.34)), (L, (0, 0.34))]
map_on = windows([(6.4, 8.8)])

# ───────────── 快层：每格（0.25 秒）一张 ─────────────
# 尘土：A 步（0、2 秒）在左脚边往左飘，B 步（1、3、9 秒）在右脚边往右飘；两边格子不重
DUST_L = [[(2, 14)], [(1, 13), (0, 14)], [(-1, 13), (-2, 14)]]
DUST_R = [[(12, 14)], [(13, 13), (14, 14)], [(15, 13), (16, 14)]]
dust_starts = [(0, DUST_L), (4, DUST_R), (8, DUST_L), (12, DUST_R), (36, DUST_R)]

# 小鸟：5 格宽，扇翅膀（u / ∩ 交替），每格往左 2，从右上飞到左上
# 两个样子交替；每格往左 2，翅尖在哪一行，另一个样子那一行的正中就得亮着（不然那个点熄一格又亮＝残影）
BIRD_UP = [(1, 0), (2, 0), (3, 0), (0, 1), (4, 1)]      # ∩：翅膀往下扇
BIRD_DN = [(0, 0), (1, 0), (3, 0), (4, 0), (2, 1)]      # ‾v‾：翅膀抬平，身子吊在中间
# 12 格起就压到第 1 行：4 秒那只举起来的手（右上 14–15 列、3–4 行）落下来之前，那块要先黑满一秒
bird_path = {11: (15, 2), 12: (13, 1), 13: (11, 1), 14: (9, 1), 15: (7, 1), 16: (5, 1), 17: (3, 1), 18: (1, 0),
             19: (-1, 0), 20: (-3, 0)}
bird_shape = {s: (BIRD_UP if s % 2 else BIRD_DN) for s in bird_path}

# 叶子：右边空地里往下飘，每格落一行、左右摆
LEAF_H = [(0, 0), (1, 0)]
LEAF_D = [(0, 0), (1, 1)]
leaf_path = {}
for i, s in enumerate(range(24, 39)):
    leaf_path[s] = (17 + (i % 2), i)
leaf_shape = {s: (LEAF_H if (s % 2 == 0) else LEAF_D) for s in leaf_path}


def fast_cells():
    """每格快层点亮的格子 {slot: {(x,y): 名}}"""
    cells = {s: {} for s in range(40)}
    for s0, fr in dust_starts:
        for k, pts in enumerate(fr):
            for p in pts: cells[(s0 + k) % 40][p] = 'dust'
    for s, (x, y) in bird_path.items():
        for dx, dy in bird_shape[s]: cells[s][(x + dx, y + dy)] = 'bird'
    for s, (x, y) in leaf_path.items():
        for dx, dy in leaf_shape[s]: cells[s][(x + dx, y + dy)] = 'leaf'
    return cells


def check_fast():
    cells = fast_cells(); bad = []
    allp = {p for s in cells for p in cells[s]}
    for p in allp:
        on = [p in cells[s] for s in range(40)]
        for s in range(40):
            if on[s] and not on[(s + 1) % 40]:          # 熄了
                for d in range(2, 5):
                    if on[(s + d) % 40]: bad.append((p, s, s + d)); break
    for s in range(40):
        for p in cells[s]:
            if p[0] < -4 or p[0] > 19 or p[1] < 0 or p[1] > 14: bad.append(('出框', p, s))
    return bad


# ───────────── 写 SVG ─────────────
def stepped_group(cls, frames_by_slot, fill, extra=''):
    """快层零件：每格一组 rect，step-end 只在自己那格亮（半格边界切换）。"""
    out = [f'  <g class="{cls}" fill="{fill}"{extra}>']
    css = []
    for i, (s, pts) in enumerate(sorted(frames_by_slot.items())):
        name = f'{cls}-f{i}'
        a, b = mid(s), mid(s + 1)
        if a < 0:
            wins = [(0, b), (L + a, L)]
        else:
            wins = [(a, b)]
        css.append(f'      .{name} {{ opacity: 0; animation: {name} {L:g}s infinite step-end; }}')
        css.append(kf(name, windows(wins), op))
        out.append(f'    <g class="{name}">' + ''.join(f'<rect x="{x}" y="{y}" width="1" height="1"/>' for x, y in pts) + '</g>')
    out.append('  </g>')
    return '\n'.join(out), '\n'.join(css)


def svg():
    css = []
    add = css.append
    add('      .shadow { transform-origin: 7.5px 15.5px; animation: shadow 10s infinite ease-in-out; }')
    add(kf('shadow', [(t, 1 + (-v[1]) * 0.04) for t, v in bob], lambda v: f'transform: scaleX({v:.3f});'))
    add('      .leg-a { animation: leg-a 10s infinite ease-in-out; }')
    add(kf('leg-a', leg_a, ty))
    add('      .leg-b { animation: leg-b 10s infinite ease-in-out; }')
    add(kf('leg-b', leg_b, ty))
    add('      .bob { animation: bob 10s infinite ease-in-out; }')
    add(kf('bob', bob, tr))
    # 腿跟着身子走——左右挪一起挪，往上蹦一起蹦（脚离地，影子留在地上），往下蹲腿不动
    add('      .legs { animation: legs 10s infinite ease-in-out; }')
    add(kf('legs', [(t, (v[0], min(v[1], 0))) for t, v in bob], tr))
    add('      .tilt { transform-origin: 7.5px 13px; animation: tilt 10s infinite ease-in-out; }')
    add(kf('tilt', tilt, lambda v: f'transform: rotate({v}deg);'))
    add('      .gaze { animation: gaze 10s infinite ease-in-out; }')
    add(kf('gaze', gaze, tr))
    add('      .eyes-rect { transform-origin: 7.5px 9px; animation: eyes-rect 10s infinite step-end, blink 10s infinite ease-in-out; }')
    add(kf('eyes-rect', rect_on, op))
    add(kf('blink', blink, sy))
    add('      .eyes-smile { opacity: 0; animation: eyes-smile 10s infinite step-end; }')
    add(kf('eyes-smile', smile_on, op))
    add('      .arm-l { animation: arm-l 10s infinite ease-in-out; }')
    add(kf('arm-l', arm_l, tr))
    add('      .arm-r { transform-origin: 13px 10px; animation: arm-r 10s infinite ease-in-out; }')
    add(kf('arm-r', arm_r, trr))
    add('      .map { opacity: 0; transform-origin: 7.5px 13px; animation: map-mv 10s infinite ease-in-out, map-op 10s infinite step-end; }')
    add(kf('map-mv', map_mv, lambda v: f'transform: translateY({v[0]}px) scaleX({v[1]});'))
    add(kf('map-op', map_on, op))

    # 快层：鸟、叶子用平移（每格落在整数格上，中间线性滑），形状 step-end 切换；尘土直接逐格
    bird_html, bird_css = [], []
    s_list = sorted(bird_path)
    pts = [(round(s * SLOT, 4), bird_path[s]) for s in s_list]
    pts = [(0, pts[0][1])] + pts + [(L, pts[-1][1])]
    add('      .bird { opacity: 0; animation: bird-vis 10s infinite step-end; }')
    add(kf('bird-vis', windows([(mid(s_list[0]), mid(s_list[-1] + 1))]), op))
    add('      .bird-fly { animation: bird-fly 10s infinite linear; }')
    add(kf('bird-fly', pts, tr))
    up_w = [(mid(s), mid(s + 1)) for s in s_list if bird_shape[s] is BIRD_UP]
    dn_w = [(mid(s), mid(s + 1)) for s in s_list if bird_shape[s] is BIRD_DN]
    add('      .wing-up { opacity: 0; animation: wing-up 10s infinite step-end; }')
    add(kf('wing-up', windows(up_w), op))
    add('      .wing-dn { opacity: 0; animation: wing-dn 10s infinite step-end; }')
    add(kf('wing-dn', windows(dn_w), op))
    r = lambda ps: ''.join(f'<rect x="{x}" y="{y}" width="1" height="1"/>' for x, y in ps)
    bird_svg = (f'  <g class="bird" fill="{CREAM}"><g class="bird-fly">'
                f'<g class="wing-up">{r(BIRD_UP)}</g><g class="wing-dn">{r(BIRD_DN)}</g></g></g>')

    s_list = sorted(leaf_path)
    pts = [(round(s * SLOT, 4), leaf_path[s]) for s in s_list]
    pts = [(0, pts[0][1])] + pts + [(L, pts[-1][1])]
    add('      .leaf { opacity: 0; animation: leaf-vis 10s infinite step-end; }')
    add(kf('leaf-vis', windows([(mid(s_list[0]), mid(s_list[-1] + 1))]), op))
    add('      .leaf-fall { animation: leaf-fall 10s infinite linear; }')
    add(kf('leaf-fall', pts, tr))
    h_w = [(mid(s), mid(s + 1)) for s in s_list if leaf_shape[s] is LEAF_H]
    d_w = [(mid(s), mid(s + 1)) for s in s_list if leaf_shape[s] is LEAF_D]
    add('      .leaf-h { opacity: 0; animation: leaf-h 10s infinite step-end; }')
    add(kf('leaf-h', windows(h_w), op))
    add('      .leaf-d { opacity: 0; animation: leaf-d 10s infinite step-end; }')
    add(kf('leaf-d', windows(d_w), op))
    leaf_svg = (f'  <g class="leaf" fill="{GRN}"><g class="leaf-fall">'
                f'<g class="leaf-h">{r(LEAF_H)}</g><g class="leaf-d">{r(LEAF_D)}</g></g></g>')

    dust_frames = {}
    for s0, fr in dust_starts:
        for k, ps in enumerate(fr): dust_frames[(s0 + k) % 40] = ps
    dust_svg, dust_css = stepped_group('dust', dust_frames, CREAM)
    add(dust_css)

    style = '\n'.join(css)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-15 -25 45 45" width="500" height="500" shape-rendering="crispEdges">
  <!-- 出门走走 · travel（身子是 clawd-tank 的静态底；登山包、地图、鸟、叶子、尘土、表情都是自己画的）
       10 秒一圈，一秒一个姿势（灵动岛每秒取一张）：
         0 走·左脚抬      1 走·右脚抬      2 走·左脚抬，右上飞来一只鸟
         3 走·右脚抬，抬眼看鸟             4 蹦一下 ^^ 招手，鸟在头顶
         5 挥手拜拜，眼睛跟着鸟去左上       6 东张西望，往左看
         7 掏出地图，低头看                 8 找到了 ^^ 把地图举高
         9 收起地图接着走·右脚抬
       快层（每秒四下）：dust 脚边尘土、bird 小鸟、leaf 叶子，都在身子旁边的空地里走，不从身子上过。
       由同目录的 gen.py 生成，改这里不如改那边。 -->
  <defs>
    <style>
{style}
    </style>
  </defs>

  <rect class="shadow" x="3" y="15" width="9" height="1" fill="{INK}" opacity="0.5"/>

  <!-- 腿：clawd-tank 原版的长短（第 13 行起、高 2），A 组（外左、内右）和 B 组（内左、外右）轮流抬；
       身子往上蹦时整只一起离地，往下蹲时腿留在地上；走路左右晃时腿跟身子一起晃，不然翘起来那边会跟身子断开一条缝 -->
  <g class="legs"><g class="tilt" fill="{BODY}">
    <rect class="leg-a" x="3" y="13" width="1" height="2"/>
    <rect class="leg-b" x="5" y="13" width="1" height="2"/>
    <rect class="leg-a" x="9" y="13" width="1" height="2"/>
    <rect class="leg-b" x="11" y="13" width="1" height="2"/>
  </g></g>

  <g class="bob"><g class="tilt">
    <!-- 登山包：背在身后，从左肩上和左边探出来；顶上横捆一卷奶白睡垫（两道深绿绑带），左边挂个深绿侧袋。
         顶边不高过第 4 行：4 秒那只鸟从头顶飞过，身子再往上蹦一格也碰不到 -->
    <g>
      <rect x="-1" y="5" width="4" height="7" fill="{GRN}"/>
      <rect x="-2" y="7" width="1" height="3" fill="{DGRN}"/>
      <rect x="-2" y="4" width="6" height="1" fill="{CREAM}"/>
      <rect x="-1" y="4" width="1" height="1" fill="{DGRN}"/>
      <rect x="2" y="4" width="1" height="1" fill="{DGRN}"/>
    </g>

    <rect x="2" y="6" width="11" height="7" fill="{BODY}"/>

    <g class="gaze">
      <g class="eyes-rect" fill="{INK}">
        <rect x="4" y="8" width="1" height="2"/>
        <rect x="10" y="8" width="1" height="2"/>
      </g>
      <g class="eyes-smile" fill="{INK}">
        <rect x="4" y="8" width="1" height="1"/><rect x="3" y="9" width="1" height="1"/><rect x="5" y="9" width="1" height="1"/>
        <rect x="10" y="8" width="1" height="1"/><rect x="9" y="9" width="1" height="1"/><rect x="11" y="9" width="1" height="1"/>
      </g>
    </g>

    <!-- 地图：奶白纸、绿色的地、虚线小路、红点是要去的地方 -->
    <g class="map">
      <rect x="3" y="11" width="9" height="4" fill="{CREAM}"/>
      <rect x="4" y="12" width="2" height="2" fill="{GRN}"/>
      <rect x="6" y="13" width="1" height="1" fill="{DGRN}"/>
      <rect x="8" y="13" width="1" height="1" fill="{DGRN}"/>
      <rect x="9" y="12" width="1" height="1" fill="{DGRN}"/>
      <rect x="10" y="12" width="1" height="1" fill="{RED}"/>
    </g>

    <g fill="{BODY}">
      <g class="arm-l"><rect x="0" y="9" width="2" height="2"/></g>
      <g class="arm-r"><rect x="13" y="9" width="2" height="2"/></g>
    </g>
  </g></g>

{bird_svg}
{leaf_svg}
{dust_svg}
</svg>
'''


if __name__ == '__main__':
    bad = check_fast()
    print('快层自查：', '没问题' if not bad else bad[:20])
    open(OUT, 'w', encoding='utf-8').write(svg())
    print('写好', OUT)
