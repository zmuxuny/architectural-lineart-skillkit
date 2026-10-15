# 建筑手绘线稿 Skillkit

[English](README.md) · [Agent Skills 开放规范](https://agentskills.io/specification)

这个开源套件复现了我们从“校园建筑黑底灰白手绘风格图”走到**可调色、可导出 SVG 和 4K PNG 的离线 HTML 工具**的完整过程。

## 案例展示：浙江大学主题建筑线稿

下面是本仓库**真实提供的完整案例**，从选定的 AI 插画原稿，经过矢量化和调色，得到可叠加到白底 PPT 的建筑线稿。它是**艺术性拼贴**，不是经逐栋核验的真实校园建筑图（详见[素材与商标说明](ASSET_NOTICE.md)）。

| 输入：AI 建筑插画原稿 | 输出：白底浅灰建筑线稿 |
| :--: | :--: |
| ![黑底白线浙江大学主题原始插画](examples/zju/source-ai-illustration.png) | ![最终白底浅灰建筑线条预览](examples/zju/final-gray-on-white-preview.jpg) |
| 原图 **1672 × 941** | 最终配色 **`#AEB0B2`**，可见度 **`1.15×`** |

### 实际运行的 SVG 调色工作台

<img src="docs/assets/workbench-screenshot.png" alt="真实运行的离线 SVG 调色工具截图，展示建筑线稿、灰度预设、可见度与细节滑块、4K PNG 和 SVG 导出按钮" width="950">

这张是**实际浏览器运行截图，不是 UI 概念图**。可以调整 HEX 线条颜色、可见度和细节层次，切换白底／黑底／透明预览，最后导出 4K PNG 或真实 SVG 路径。你的最终选择是「主线突出」，但截图未显示该滑块的精确数值；示例中使用可调的近似初值 `detail=1.65`。

**直接体验与查看案例产物：**

| 产物 | 预览／使用入口 |
| --- | --- |
| 选定的 AI 插画原稿 | [黑底原图 PNG](examples/zju/source-ai-illustration.png) |
| 最终白底 PPT 效果 | [灰线效果预览](examples/zju/final-gray-on-white-preview.jpg) |
| 4K 透明背景线稿 | [透明底 PNG](examples/zju/lineart-transparent.png) |
| 真正的分层矢量路径 | [11 层路径 SVG](examples/zju/lineart.svg) |
| 可交互的完整调色器 | [下载 `workbench.html`](examples/zju/workbench.html)，用 Edge／Chrome 双击打开 |

**完整案例流水线：** 建筑参考与真实性检查 → AI 生成精细插画 → 透明背景和 11 级轮廓矢量化 → 导出 3840 × 2160 PNG／SVG → 打包单文件离线 HTML。

## 最终用户参数

- HEX 线条颜色：**`#AEB0B2`**
- 线条可见度：**`1.15×`**
- 细节层次：**「主线突出」**
- 预览背景：白色，输出可选透明背景。

说明：截图只展示「主线突出」这个文字状态，没有显示滑块数值。示例 HTML 采用 `detail=1.65` 作为**近似默认值**，用户仍可交互调整，不能把 1.65 说成截图明确记录的精确值。

## 3 个 Agent Skills

1. **[campus-architectural-lineart](skills/campus-architectural-lineart/SKILL.md)**：真实建筑参考素材核验 → 场景构图 → 生成手绘风格插画 → 与参考照片比对。AI 生成的建筑可能不准确，不能以图像替代事实核验。
2. **[raster-to-layered-svg](skills/raster-to-layered-svg/SKILL.md)**：黑底亮线图片 → 4K 透明底 PNG → 多阈值灰度轮廓 SVG；包括可运行的 Python 脚本。
3. **[offline-svg-color-workbench](skills/offline-svg-color-workbench/SKILL.md)**：把 SVG 路径、PNG、JS 和 CSS 打成独立 HTML，离线调灰度、可见度、主线突出程度及背景，导出 SVG 或 PNG。

## 不用编程也能立即体验

下载并双击 [`examples/zju/workbench.html`](examples/zju/workbench.html)，用 Edge 或 Chrome 打开，不需要网络、服务端或账号。

**推荐从最终配色出发继续微调**：#AEB0B2 + 1.15× +「主线突出」，然后导出透明底 PNG 叠加白色 PPT。

## 自己跑一遍

```bash
python -m pip install -r requirements.txt

python skills/raster-to-layered-svg/scripts/convert.py \
    --input examples/zju/source-ai-illustration.png \
    --out-dir dist/zju --size 3840x2160

python skills/offline-svg-color-workbench/scripts/build.py \
    --svg dist/zju/lineart.svg \
    --png dist/zju/lineart-transparent.png \
    --output dist/zju/workbench.html
```

之后用浏览器打开 `dist/zju/workbench.html`。

将 `skills/` 下任一 Skill 文件夹复制到支持 Agent Skills 的工具的技能目录，例如 Codex 的 `$HOME/.agents/skills/`，即可通过自然语言触发相应工作流。仓库发布后，也可尝试 `npx skills add <GitHub 仓库地址>`，具体取决于客户端支持情况。

## 必须说清楚的技术事实

- 最初的插画是 AI 生成，并非手工逐笔画的 SVG。**使用图像生成模型不能保证真实校园的建筑结构没有错误**。
- SVG 是按 11 级阈值做轮廓描摹，拥有真实 `<path>`，但没有“教学楼、树木、桥”这样的语义图层。
- 原图分辨率 **1672×941**，导出 PNG 为 **3840×2160**。4K 是输出像素，不代表凭空生成了缺失的原生细节。
- HTML 前端可以操作颜色、alpha 和背景，不负责重新生成或修正建筑事实。
- 示例中包含大学主题字样，不代表学校官方发布或认可；参见 [素材与版权说明](ASSET_NOTICE.md)。

## 代码质量

支持 `python -m unittest discover -s tests -v` 自动测试、Node.js 语法检查和 GitHub Actions CI。代码使用 MIT License。
