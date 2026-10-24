# 建筑手绘线稿 Skillkit

[English](README.md) · [Agent Skills 开放规范](https://agentskills.io/specification)

这个开源套件复现了我们从“校园建筑黑底灰白手绘风格图”走到**可调色、可导出 SVG 和 4K PNG 的离线 HTML 工具**的完整过程。

## v0.4.0：校庆、城市与帆布袋的真正「纪念式组合主视觉」

之前的 `compose.py` 是将单体建筑并排摆放，容易得到分散的**建筑素材陈列板**。这不是校庆海报或宣传帆布袋应有的效果。新版将任务按意图区分：

| 用户需求 | 模式 | 目标 |
| --- | --- | --- |
| 某栋校门、钟楼、图书馆 | `single-building` | 单体真实、精细线稿 |
| 多栋建筑独立展示、素材页 | `gallery-layout` | 各自清晰，旧 `compose.py` |
| **校庆、学校/城市地标群像、帆布袋、文创** | **`commemorative-montage`** | **一幅和谐统一的主视觉作品** |

新增**可运行**的 `compose_v2.py`：自动生成主建筑/辅助建筑构图计划、允许前后遮挡、添加统一装饰性地线，并输出草图与整体重绘说明。**草图不是最终成品**！Agent 必须实际传入原始建筑照片、各栋线稿、风格图和草图给支持多图输入的生成/编辑模型，整图统一绘制线密度、环境连接和明暗。之后 `montage_audit.py` 对**最终整幅画**逐栋、逐项进行两轮视觉审查，并检查是否仍然像彼此独立的贴纸。只有最终图片与证据审核通过，才进入 SVG 和 HTML。

[校庆／文创组合完整流程](docs/COMMEMORATIVE_MONTAGE.zh-CN.md) · [模式与构图说明（English）](docs/COMMEMORATIVE_MONTAGE.md) · [JSON 计划格式](skills/campus-architectural-lineart/references/montage-plan.schema.json)

**能力边界**：新流程的程序部分有合成输入测试，但尚未用真实建筑 + 生图模型完成一次端到端验证；不能把旧浙大插画补写成通过新审核。帆布袋暂支持 16:9 横向印花图案，不等于支持完整的印花制版、裁切出血与特殊颜色要求。

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

## v0.3.0：Agent 自动核验建筑

现在第一个 Skill 可以在 Agent 的视觉能力或视觉模型 API 支持下，自动核验来源、逐建筑检查生成线稿，并在证据缺失或判断冲突时仅升级具体问题给人复核。

**流程**：检索真实照片与使用许可 → 构建建筑结构证据包 → 实际将原图作为生图模型的图片输入 → 对候选图进行两轮视觉审核（逐特征 + 主动寻找反例）→ 一致且高置信度才自动通过 → 只重画失败建筑并重新审核 → SVG 和离线 HTML。

新增 [自动核验脚本](skills/campus-architectural-lineart/scripts/agent_audit.py) 和 [中文完整指南](docs/AUTONOMOUS_REVIEW.zh-CN.md)。两种方式均支持：配置自己的 OpenAI 视觉 API，通过真实的图像输入审查；或者由执行 Skill 的多模态 Agent 进行两轮视觉判断后交给脚本核对。必须记录每张实际查看图片的 SHA-256、模型调用和来源照片 ID。

**限制**：自动核验不等于建筑事实认证，模型置信度不是校准过的概率。只有来源、照片内容、所有结构特征和两轮模型判断均满足要求才可标记为 Agent-reviewed；严格复原、许可不明、学校正式标识等情况继续升级给真人。旧浙大示例没有逐栋证据，不能倒填自动核验合格报告。

## 最终用户参数

- HEX 线条颜色：**`#AEB0B2`**
- 线条可见度：**`1.15×`**
- 细节层次：**「主线突出」**
- 预览背景：白色，输出可选透明背景。

说明：截图只展示「主线突出」这个文字状态，没有显示滑块数值。示例 HTML 采用 `detail=1.65` 作为**近似默认值**，用户仍可交互调整，不能把 1.65 说成截图明确记录的精确值。


## 新增：真实建筑照片约束生图与事实审查门禁（v0.2.0）

你关心的关键阶段是**真正把可信的建筑照片交给图像生成模型，而不是只提示「画某大学」**。我们已经将第一个 Skill 从操作建议升级为带 Python 工具的取证、证据锁定、生成约束和人工审核流程。

1. **原始照片取证**：按建筑全名、校区与拍摄视角查询原始摄影页面；每栋建筑至少 **两张不同机位的原照片**，各至少 1.5MP（短边 ≥850px，长边 ≥1400px），并记录摄影师、来源和衍生创作使用许可。必须指定一个 `primary_view_id` 为主要机位，其他角度用于辅助核验，不能把两种视角拼成虚假的几何结构。
2. **事实清单**：把实际看得到的屋顶、窗户、门洞、钟楼、立柱等特征逐项绑定原图 ID，必要时人工框出局部证据图；把看不到的立面列为未知，把禁止额外创造的结构列为约束。校名与官方字标**不交给生图模型猜写**。
3. **生成前门禁**：程序检查分辨率、重复/近重复、来源字段、不同角度、证据区域；输出 `reference-board.png`、`feature-crops/`、`evidence-lock.json`、`generation-brief.md`。证据不足则直接 `blocked`。
4. **真正按图片生图**：Agent 必须调用支持图片输入的生成／编辑工具，逐栋附上**真实照片像素和风格参考图**，每栋独立生成、独立核对，再用 `compose.py` 透明切片拼接，避免不同建筑特征串扰。若要求严格几何真实而模型总是变形，则切换到参考照片的人工矢量描绘。
5. **审核后放行**：真人按原图逐项判断生成建筑有没有错误结构、额外建筑、错误文字；有 `fail` / `unknown` 就不能通过。通过后 `approval.json` 与当前生成 PNG 的 SHA-256 绑定，后续 `convert.py --approval` 拒绝未审查或替换的图片。

~~~bash
# 创建默认不通过的证据模板，接着真实填入照片、视角、版权、特征证据
python skills/campus-architectural-lineart/scripts/reference_pipeline.py template --output workspace/project.json
python skills/campus-architectural-lineart/scripts/reference_pipeline.py prepare --manifest workspace/project.json --out-dir workspace/grounding

# 完成实际的参考图生图与逐项人工审查后，填写 review.json
python skills/campus-architectural-lineart/scripts/reference_pipeline.py audit --manifest workspace/project.json --evidence-lock workspace/grounding/evidence-lock.json --image workspace/artwork/final.png --review workspace/artwork/review.json --output workspace/artwork/approval.json

# 绑定审核 PNG 的 SHA-256，才进入 SVG 阶段
python skills/raster-to-layered-svg/scripts/convert.py --input workspace/artwork/final.png --approval workspace/artwork/approval.json --out-dir workspace/dist --size 3840x2160
~~~

**直接阅读：** [完整中文操作与数据流](docs/PHOTO_GROUNDING.zh-CN.md) · [照片检索与版权核验](skills/campus-architectural-lineart/references/photo-sourcing.md) · [输入清单与审核 JSON 示例](skills/campus-architectural-lineart/references/evidence-schema.md) · [审核助手规则](skills/campus-architectural-lineart/references/assisted-review.md) · [完整取证工具源码](skills/campus-architectural-lineart/scripts/reference_pipeline.py)。

**诚实的能力边界：** 软件能强制记录来源、检查图片质量与哈希、阻止缺少人工审核记录的结果，但无法自动证明照片身份、授权或生成建筑的几何结构绝对真实。之前的浙大线稿是旧版 AI 艺术拼贴，没有逐栋核验的真实证据包，不能事后声称它通过了新版真实性审核。

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
