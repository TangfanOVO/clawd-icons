#!/usr/bin/env python3
"""小螃蟹 · 在给你写信（letter）—— 生成同目录的 letter.svg（python3 crabs/letter/gen.py）
一圈 L=10 秒，灵动岛每秒在整秒处拍一个姿势（S0..S9），顺滑版在整秒之间做过渡。
  S0 新的一页，趴着落笔      S1 第一行写到一半          S2 第一行写完、第二行起头
  S3 抬头想（腮红、笔点脑袋） S4 想到了 ^^ 刷刷写完       S5 对折、托在肚子前
  S6 装进信封                S7 封口贴一颗心 ^^           S8 举过头顶给你看 ^^
  S9 落下来一点、睁眼看你（腮红）；之后信飞走、换下一页
快层（每秒四下）：heart（想你时一颗、举信时左右两颗），ink（行尾甩出的墨点）。
任何会在整秒被拍到的变化都离整秒至少 0.05 秒；整秒之间才过渡。
"""
import os
L = 10.0
OUT = os.environ.get('OUT') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'letter.svg')

BODY, BLACK, PAPER, INK, RED, BLUSH = '#DE886D', '#000000', '#E9DCC4', '#3D7AC7', '#FF2D3D', '#FF97A2'
css = []


def pct(t):
    return f'{t / L * 100:.3f}'.rstrip('0').rstrip('.') + '%'


def anim(name, sel, frames, fmt, ease='ease-in-out'):
    """frames: [(t, value), ...]，t 从 0 起；自动补 100% = 0% 的值。"""
    fr = sorted(frames, key=lambda f: f[0])
    assert fr[0][0] == 0, name
    assert all(a[0] < b[0] for a, b in zip(fr, fr[1:])), name
    if fr[-1][0] < L: fr.append((L, fr[0][1]))
    body = '\n'.join(f'  {pct(t)} {{ {fmt(v)} }}' for t, v in fr)
    css.append(f'{sel} {{ animation: {name} {L:g}s infinite {ease}; }}')
    css.append(f'@keyframes {name} {{\n{body}\n}}')


tr = lambda v: f'transform: translate({v[0]:g}px, {v[1]:g}px);'
sy = lambda v: f'transform: scaleY({v:g});'
op = lambda v: f'opacity: {v:g};'
trop = lambda v: f'transform: translate({v[0]:g}px, {v[1]:g}px); opacity: {v[2]:g};'


def win(spans, eps=0.02):
    """spans: [(a, b)] 可见区间，瞬切；跨圈的写成 a > b。返回 opacity 关键帧。"""
    pts = []
    for a, b in spans:
        pts += [(a - eps, 0), (a, 1), (b - eps, 1), (b, 0)]
    vis0 = any(a > b for a, b in spans)
    return sorted([(0, 1 if vis0 else 0)] + [(t, v) for t, v in pts if 0 < t < L])


# ---------------- 身子 ----------------
# 身子上下：趴着写 +1 / 坐直 0 / 举高 -1
BD = [(0, (0, 1)), (2.2, (0, 1)), (2.75, (0, 0)), (7.2, (0, 0)), (7.8, (0, -1)), (8.3, (0, -1)),
      (8.7, (0, 0)), (9.62, (0, 0)), (9.9, (0, 1))]
anim('bd', '.bd', BD, tr)
# 腿跟着身子走——左右挪一起挪，往上举高时一起离地（影子留在地上），趴下时腿不动
anim('legs', '.legs', [(t, (v[0], min(v[1], 0))) for t, v in BD], tr)
css.append('.breathe { transform-origin: 7.5px 13px; animation: breathe 2.5s infinite ease-in-out; }')
css.append('@keyframes breathe { 0%, 100% { transform: scale(1, 1); } 50% { transform: scale(1.02, 0.98); } }')

# 左手：写字时垂着 → 折纸时扶左边 → 托信封 → 举高
anim('al', '.arm-l', [(0, (0, 0)), (4.2, (0, 0)), (4.45, (2, 3)), (4.75, (2, 3)), (4.95, (1, 2)), (5.05, (1, 2)),
                      (5.2, (1, -1)), (5.3, (1, -1)), (5.5, (1, 2)), (7.2, (1, 2)), (7.8, (1, -5)), (9.3, (1, -5)),
                      (9.4, (1, -6)), (9.6, (0, 0))], tr)

# 右手（拿笔）。手 = (hx..hx+1, hy..hy+1)；笔尖在手左边 (hx-1, hy)，笔杆一格在手右上 (hx+2, hy-1)。
# tx = 笔尖x - 12；第一行（第 12 行）ty=2，第二行（第 14 行）ty=3 且笔往下挪一格（.penpos）。
ar = [(0, (-8, 2)), (0.10, (-7.5, 2)), (0.20, (-7, 2)), (0.30, (-6.5, 2)), (0.38, (-6, 2)), (0.46, (-5.5, 1.5)),
      (0.55, (-5, 2)), (0.70, (-4.5, 2)), (0.85, (-4, 2)), (1.05, (-4, 2)), (1.15, (-3, 2)), (1.22, (-2.5, 1.5)),
      (1.30, (-2, 2)), (1.42, (-1, 2)), (1.50, (-0.5, 1.4)), (1.60, (-1, 2)),
      (1.85, (-8, 3)), (2.0, (-7, 3)), (2.2, (-7, 3)), (2.75, (0, -3)), (2.9, (0, -3.5)), (3.05, (0, -3)),
      (3.3, (0, -3)), (3.45, (-7, 3)), (3.52, (-6, 3)), (3.60, (-5, 3)), (3.68, (-4, 3)), (3.76, (-3.5, 2.5)),
      (3.85, (-2, 3)), (3.95, (-1, 3)), (4.2, (-1, 3)), (4.45, (-2, 3)), (4.75, (-2, 3)), (4.95, (-1, 2)),
      (5.05, (-1, 2)), (5.2, (-1, -1)), (5.3, (-1, -1)), (5.5, (-1, 2)), (6.2, (-1, 2)), (6.35, (-7, 3)),
      (6.45, (-7, 3.5)), (6.55, (-7, 3.5)), (6.6, (-7, 3)), (6.8, (-1, 2)), (7.2, (-1, 2)), (7.8, (-1, -5)),
      (9.3, (-1, -5)), (9.4, (-1, -6)), (9.6, (0, 0)), (9.66, (0, 0)), (9.9, (-8, 2))]
# S3、S4 身子坐直（dy 0），手的 y 要再 +1 才落到同一行
ar = [(t, (v[0], v[1] + 1)) if 3.3 < t <= 4.2 else (t, v) for t, v in ar]
anim('ar', '.arm-r', ar, tr)
anim('pen', '.pen', [(0, 1), (4.22, 1), (4.32, 0), (9.72, 0), (9.8, 1)], op)
anim('penpos', '.penpos', [(0, (0, 0)), (1.62, (0, 0)), (1.7, (0, 1)), (9.74, (0, 1)), (9.76, (0, 0))], tr)

# 眼睛：睁眼组看哪儿（dx, dy）
anim('eo', '.eo', [(0, (0, 0)), (1.6, (0, 0)), (1.85, (-1, 0)), (2.2, (-1, 0)), (2.75, (-1, -1)), (3.3, (-1, -1)),
                   (3.4, (0, 1)), (5.05, (0, 1)), (5.15, (0, -1)), (5.35, (0, -1)), (5.45, (0, 0))], tr)
anim('eo-vis', '.eo-vis', win([(4.3, 6.6), (8.6, 9.3), (9.75, 3.35)]), op)
anim('es-vis', '.es', win([(3.35, 4.3), (6.6, 8.6), (9.3, 9.75)]), op)
css.append('.eb { transform-origin: 7.5px 9px; }')
anim('eb', '.eb', [(0, 1), (0.5, 1), (0.55, 0.1), (0.62, 1), (5.7, 1), (5.75, 0.1), (5.82, 1),
                   (9.1, 1), (9.15, 0.1), (9.22, 1)], sy, ease='linear')
anim('bl', '.bl', win([(2.6, 4.3), (6.6, 9.75)]), op)

# ---------------- 纸（画在信封后面：装信封时从信封口滑进去） ----------------
anim('paper', '.paper', [(0, (0, 0, 1)), (4.75, (0, 0, 1)), (4.95, (0, -2, 1)), (5.05, (0, -2, 1)), (5.2, (0, -5, 1)),
                         (5.3, (0, -5, 1)), (5.5, (0, -2, 1)), (5.52, (0, -2, 0)), (9.6, (0, 2, 0)), (9.85, (0, 0, 1))], trop)
css.append('.ptop, .pflap { transform-box: view-box; transform-origin: 7.5px 13px; }')
anim('ptop', '.ptop', [(0, 1), (4.45, 1), (4.6, 0), (9.0, 0), (9.05, 1)], sy)
anim('pflap', '.pflap', [(0, 0), (4.6, 0), (4.75, 1), (9.0, 1), (9.05, 0)], sy)
# 字：每格一个出现时间（第一行 12，第二行 14）
words = [((4, 12), 0.10), ((5, 12), 0.30), ((7, 12), 0.65), ((8, 12), 1.10), ((10, 12), 1.35),
         ((4, 14), 1.90), ((6, 14), 3.52), ((7, 14), 3.60), ((8, 14), 3.68), ((10, 14), 3.86)]
for i, (_, r) in enumerate(words):
    anim(f'w{i}', f'.w{i}', win([(r, 9.0)]), op, ease='linear')

# ---------------- 信封（11×5，列 2..12、行 10..14） ----------------
anim('env', '.env', [(0, (0, 0, 0)), (5.1, (0, 0, 0)), (5.2, (0, 0, 1)), (7.2, (0, 0, 1)), (7.8, (0, -10, 1)),
                     (8.3, (0, -10, 1)), (8.7, (0, -9, 1)), (9.3, (0, -9, 1)), (9.6, (0, -13, 0)), (9.66, (0, -13, 0)),
                     (9.7, (0, 0, 0))], trop)
anim('eopen', '.eopen', win([(5.1, 5.65)]), op, ease='linear')
anim('vee', '.vee', win([(5.65, 9.7)]), op, ease='linear')
anim('seal', '.seal', win([(6.5, 9.7)]), op, ease='linear')

# ---------------- 快层：心、墨点（每 0.25 秒一个整数位置，只往前走、不压身子和道具） ----------------
HEART = [(x, y) for y, row in enumerate(['XX.XX', 'XXXXX', '.XXX.', '..X..']) for x, c in enumerate(row) if c == 'X']


def path_anim(pts, fade=0.08):
    t0, x0, y0 = pts[0]; t1, x1, y1 = pts[-1]
    fr = [(0, (x0, y0, 0)), (t0 - fade, (x0, y0, 0)), (t0, (x0, y0, 1))]
    fr += [(t, (x, y, 1)) for t, x, y in pts[1:]]
    fr += [(t1 + fade, (x1, y1 - 0.4, 0))]
    if t1 + fade + 0.05 < L: fr.append((t1 + fade + 0.05, (x0, y0, 0)))
    return fr


hearts = {
    'h1': [(3.0, 3, 2), (3.25, 3, 1), (3.5, 3, 0)],
    'h2': [(8.0, -4, 9), (8.25, -4, 8), (8.5, -4, 7), (8.75, -4, 6), (9.0, -4, 5), (9.25, -4, 4), (9.5, -4, 3)],
    'h3': [(8.5, 14, 10), (8.75, 14, 9), (9.0, 14, 8), (9.25, 14, 7), (9.5, 14, 6), (9.75, 14, 5)],
}
inks = {
    'k1': [(1.25, 14, 10), (1.5, 15, 9), (1.75, 16, 8)],
    'k2': [(1.25, 14, 12), (1.5, 15, 12), (1.75, 16, 13)],
    'k3': [(4.0, 16, 11), (4.25, 17, 10), (4.5, 18, 9)],
    'k4': [(4.0, 16, 13), (4.25, 17, 12), (4.5, 18, 12)],
}
for k, p in {**hearts, **inks}.items():
    anim(k, '.' + k, path_anim(p), trop, ease='linear')

# ---------------- 画（后画的在上层） ----------------
R = lambda x, y, w=1, h=1, f=None: f'<rect x="{x}" y="{y}" width="{w}" height="{h}"' + (f' fill="{f}"' if f else '') + '/>'
svg = []
svg.append(f'<rect class="shadow" x="3" y="15" width="9" height="1" fill="{BLACK}" opacity="0.5"/>')
# 腿：clawd-tank 原版的长短（第 13 行起、高 2），跟着身子挪
svg.append(f'<g class="legs" fill="{BODY}">' + ''.join(R(x, 13, 1, 2) for x in (3, 5, 9, 11)) + '</g>')
# 后身：躯干、眼睛、腮红
svg.append('<g class="bd"><g class="breathe">')
svg.append(R(2, 6, 11, 7, BODY))
svg.append(f'<g class="eo"><g class="eo-vis"><g class="eb" fill="{BLACK}">{R(4, 8, 1, 2)}{R(10, 8, 1, 2)}</g></g></g>')
# ^^ 笑眼：三格的像素 ^（整数格）
svg.append(f'<g class="es" fill="{BLACK}">' + ''.join(R(x, y) for x, y in ((4, 8), (3, 9), (5, 9), (10, 8), (9, 9), (11, 9))) + '</g>')
svg.append(f'<g class="bl" fill="{BLUSH}">{R(3, 10, 2, 1)}{R(10, 10, 2, 1)}</g>')
svg.append('</g></g>')
# 纸
svg.append('<g class="paper">')
svg.append(R(3, 13, 9, 2, PAPER))
svg.append(f'<g fill="{INK}">' + ''.join(f'<rect class="w{i}" x="{x}" y="{y}" width="1" height="1"/>' for i, ((x, y), _) in enumerate(words) if y == 14) + '</g>')
svg.append(f'<g class="ptop">{R(3, 11, 9, 2, PAPER)}<g fill="{INK}">' +
           ''.join(f'<rect class="w{i}" x="{x}" y="{y}" width="1" height="1"/>' for i, ((x, y), _) in enumerate(words) if y == 12) + '</g></g>')
svg.append(f'<g class="pflap">{R(3, 13, 9, 2, PAPER)}</g>')
svg.append('</g>')
# 信封
svg.append('<g class="env">')
svg.append(R(2, 10, 11, 5, PAPER))
svg.append(f'<g class="eopen">{R(2, 10, 11, 1, INK)}</g>')
svg.append(f'<g class="vee" fill="{INK}">{R(2, 10, 2, 1)}{R(11, 10, 2, 1)}{R(4, 11, 2, 1)}{R(9, 11, 2, 1)}{R(6, 12, 3, 1)}</g>')
svg.append(f'<g class="seal" fill="{RED}">' + ''.join(R(5 + x, 11 + y) for x, y in HEART) + '</g>')
svg.append('</g>')
# 前身：两只手（右手拿笔：蓝笔尖、红笔杆）
svg.append('<g class="bd"><g class="breathe">')
svg.append(f'<g class="arm-l">{R(0, 9, 2, 2, BODY)}</g>')
svg.append(f'<g class="arm-r"><g class="pen"><g class="penpos">{R(12, 9, 1, 1, INK)}{R(15, 8, 1, 1, RED)}</g></g>{R(13, 9, 2, 2, BODY)}</g>')
svg.append('</g></g>')
# 快层
for k in hearts:
    svg.append(f'<g class="heart {k}" fill="{RED}">' + ''.join(R(x, y) for x, y in HEART) + '</g>')
for k in inks:
    svg.append(f'<g class="ink {k}" fill="{INK}">{R(0, 0)}</g>')

head = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-15 -25 45 45" width="500" height="500" shape-rendering="crispEdges">\n'
        '  <!-- 小螃蟹 · 在给你写信（letter）· 10 秒一圈，整秒一个姿势：\n'
        '       落笔 / 写第一行 / 换行 / 抬头想你 / 想到了刷刷写完 / 对折 / 装信封 / 封口贴心 / 举高给你看 / 看你，然后信飞走换下一页 -->\n'
        '  <defs>\n    <style>\n' + '\n'.join('      ' + l for c in css for l in c.split('\n')) + '\n    </style>\n  </defs>\n')
open(OUT, 'w', encoding='utf-8').write(head + '\n'.join('  ' + s for s in svg) + '\n</svg>\n')
print(OUT)
