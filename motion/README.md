# Clawd 动态版

111 个功能与备选，每个都有专属动作、眨眼、开心、待机与睡着状态。

![身体与物件的互动](../preview/interactions.gif)

请将 `svg/` 中需要的 SVG **内联**到页面，引入 `clawd-motion.css`、`clawd-motion.js`，再调用 `ClawdMotion.play(element)`。仅通过 `<img>` 或外部雪碧图 `<use>` 引用时是静态图形。

[完整用法与许可](../README.md) · [在线动态预览](https://TangfanOVO.github.io/clawd-icons/interaction.html)

## 单个下载

在线页面：[单个下载](https://TangfanOVO.github.io/clawd-icons/motion/)。在“单个下载”里选图标、版本和动作，或点每个图标下面的“下载”。

| 选项 | 可选 |
| --- | --- |
| 版本 | 现在；主页、消息、书、睡眠另有生动版 |
| 动作 | 专属动作、眨眼、开心、待机、睡着、醒来 |
| 线条颜色 | 改 `currentColor` 的线条；身体、眼睛等固定颜色不变 |
| 背景 | 透明、白色、深色 |
| 尺寸 | 128 / 256 / 512 px |
| 速度 | 正常、慢放 ×0.4 |

| 格式 | 说明 |
| --- | --- |
| 静态 SVG | 停在静止的样子，选“睡着”就是闭眼；不带样式和脚本 |
| 动态 SVG | 内嵌所需样式，无脚本、无外部引用，放进 `<img>` 也会动；动作播一次，待机一直循环 |
| GIF | 循环播放，在浏览器本地生成，有进度和取消；透明 GIF 的半透明边缘按白底处理，深色背景建议选深色或用 SVG |

动态 SVG 和 GIF 四周各留 2 格动作空间。文件名包含图标、版本、动作和尺寸，例如 `clawd-home-vivid-trick-256px.gif`。GIF 编码用 [gifenc](vendor/README.md)（MIT）。

## 生动版

主页、消息、书、睡眠多一种画法：动作更大，带笑眼、腮红这些表情。原来那版不变，两版都能用。

| 预览 | 图标 | 动作 |
| --- | --- | --- |
| <img src="vivid/gif/clawd-home.gif" width="72" alt="主页生动版：伸个懒腰"> | 主页 `clawd-home` | 伸个懒腰 |
| <img src="vivid/gif/clawd-chat.gif" width="72" alt="消息生动版：说完发出"> | 消息 `clawd-chat` | 说完发出 |
| <img src="vivid/gif/clawd-book.gif" width="72" alt="书生动版：捧书翻页"> | 书 `clawd-book` | 捧书翻页 |
| <img src="vivid/gif/clawd-sleep.gif" width="72" alt="睡眠生动版：偷看一眼"> | 睡眠 `clawd-sleep` | 偷看一眼 |

| 文件 | 用途 |
| --- | --- |
| `vivid/svg/` | 动态源，内联进页面用 |
| `vivid/static/` | 静态 SVG，不需要样式 |
| `vivid/gif/` | 预览 GIF：专属动作，白底，256 px |
| `vivid/clawd-vivid.css` | 这四个的专属动作 |
| `vivid/vivid.json` | 名单和动作说明 |

用法和原来一样，多引入一份样式；眨眼、开心、待机、睡着照常由 `clawd-motion.css` 管。睡眠的生动版一直闭着眼，没有眨眼和醒来。

```html
<link rel="stylesheet" href="motion/clawd-motion.css">
<link rel="stylesheet" href="motion/vivid/clawd-vivid.css">
<!-- 在这里放入 motion/vivid/svg/clawd-home.svg 的完整内容 -->
<script src="motion/clawd-motion.js"></script>
```

身子只用 clawd-tank 的静态基础图形（MIT），见 [THIRD_PARTY.md](../THIRD_PARTY.md)。
