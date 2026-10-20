//  灵动岛里一直在动的小螃蟹：一层一套「计时器字体」，叠起来画。
//
//  tools/fonts.py 会生成两样东西：
//    · 一堆 XFxxxx.ttf —— 拖进 widget extension，Info.plist 的 UIAppFonts 里逐个登记；
//    · CrabStates2.swift —— 里面是 CRAB_STATES_2（状态名 → CrabState2）和下面这两个结构。
//  这个文件只是用法示例；结构以 fonts.py 生成的那份为准，两边别重复定义。
//
//  原理：Text(timerInterval:) 是系统自己会走的计时器，秒的个位每秒换一次。字体把数字 0–9 画成这一层的十帧，
//  个位走到几就显示第几帧。每层的计时器起点晚 phase 秒（0 / 0.25 / 0.5 / 0.75），四组错开，画面每 0.25 秒能变一次：
//  慢层（身子、眼睛、道具）一秒一个姿势、整块一组；快层（水花、心、星星…）四组轮流；最上面四层黑蒙版盖残影。
//  锁屏是液态玻璃底，黑蒙版会变成黑块 → lock 时只用 phase 0、而且不是蒙版的层（一秒一换，不留残影）。
//  苹果没说支持这种用法，可能多耗一点电，建议做成开关。

import SwiftUI

// kind：0 慢层 / 1 快层 / 2 黑蒙版
struct CrabLayer2 { let font: String; let color: UInt32; let phase: Double; let kind: Int }
struct CrabState2 { let w: Int; let h: Int; let layers: [CrabLayer2] }

struct CrabFrames2: View {
    let st: CrabState2
    let since: Date      // 计时器起点：对齐到整 10 秒，每次都从第 0 帧开始
    let box: CGSize      // 给它多大地方（点）
    let lock: Bool
    var body: some View {
        let p = min(box.width / CGFloat(st.w), box.height / CGFloat(st.h))   // 一格多少点
        let w = CGFloat(st.w) * p, h = CGFloat(st.h) * p
        let layers = lock ? st.layers.filter { $0.phase == 0 && $0.kind != 2 } : st.layers
        ZStack(alignment: .bottomTrailing) {
            ForEach(Array(layers.enumerated()), id: \.offset) { _, l in
                let start = since.addingTimeInterval(l.phase)
                Text(timerInterval: start...start.addingTimeInterval(8 * 3600), countsDown: false)
                    .font(.custom(l.font, fixedSize: p * 100))   // 字体里一格 = 10 单位，1 em = 100 格
                    .foregroundStyle(crabColor(l.color))
                    .multilineTextAlignment(.trailing)
                    .lineLimit(1)
                    .frame(width: w * 6, height: h, alignment: .bottomTrailing)   // 只露最后一个字（秒的个位），冒号零宽
            }
        }
        .frame(width: w, height: h, alignment: .bottomTrailing)
        .clipped()
    }
}

private func crabColor(_ rgb: UInt32) -> Color {
    Color(red: Double((rgb >> 16) & 0xFF) / 255, green: Double((rgb >> 8) & 0xFF) / 255, blue: Double(rgb & 0xFF) / 255)
}

// 用法（实时活动里）：
//   if let st = CRAB_STATES_2["在钓鱼"] {
//       CrabFrames2(st: st, since: since, box: CGSize(width: 44, height: 30), lock: false)   // 紧凑态
//   }
//   锁屏卡片传 lock: true。
