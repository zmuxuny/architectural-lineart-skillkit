> **v0.5 建筑画卷提示：** 对学校/城市地标纪念画卷，默认选择 `landmark-scroll`（6–10 个真实地标），而不是 2–5 个建筑加大片树木和水纹。详见 [完整画卷流程](LANDMARK_SCROLL.zh-CN.md)。此模式以建筑为主体，低装饰密度；原来的 `hero-montage` 只适合明确要求少量主角时。

# 纪念式地标组合：commemorative-montage




这条路线针对 **校庆海报、帆布袋、城市纪念插画、文创主视觉**。要求多栋建筑形成有主次、前后遮挡、共同连接层的单幅插画。它不同于 `compose.py` 的素材陈列：不能把 3 个互不相干的完整建筑剪贴图依次摆放就算成功。




## 三种意图与正确路由




| 意图 | 模式 | 最终要求 |
| --- | --- | --- |
| 单栋校门、钟楼、图书馆 | `single-building` | 单体结构与照片一致；无需多建筑排版 |
| 建筑素材目录、对照表、逐项展示 | `gallery-layout` | 各栋独立可见；可用原 `compose.py` |
| 校庆、学校/城市地标主视觉、宣传帆布袋、文创 | **`commemorative-montage`** | **一幅整体和谐的作品**，不是建筑样本陈列板 |




没有明确要求每栋完全展示时，学校/城市主题纪念图**优先第三种**。不强求人工选择 3–5 栋：Agent 可自行选择并给出实际照片证据；需要严格指定建筑时遵循用户名单。每一栋真实建筑都必须单独有可核实原照片依据。




## 新路线做了什么，什么尚未自动化




1. **Agent 调查**学校/城市和 2–5 个地标（稀疏 hero 模式），或 6–10 个地标（建筑地标画卷）。使用 `reference_pipeline.py` 建证据包：每栋至少两个不同视角原图、主视角、可观察关键特征、版权情况、文件哈希。不同校区/城区拼在一起必须称为**艺术拼贴**。
2. **Agent 调用实际生图模型**，给每栋传入原始照片像素、特征局部图与**仅用于画风**的风格图，得到各自的 RGBA 透明建筑线稿。不能用文字描述或文件名冒充图片输入。
3. **构图规划**：运行新 `compose_v2.py plan`。自动给主建筑更大的视觉权重，将其他建筑放到支持位置，允许局部重叠。这是**构图建议**，Agent 可以据实调整 JSON。
4. **构图草图**：`compose_v2.py draft` 绘制共用的装饰性地面波纹、层次与遮挡关系。输出 ***草图*** 而非可直接交付的主视觉。它不凭空画写实桥梁、钟楼或未核实的真实城市景观。
5. **整图统一重绘**：Agent 必须调用支持多图输入的图像生成/编辑工具，实际传入草图、各建筑裁切图、风格图和每栋的主视角实拍，让模型制作**同一幅**艺术线稿。目标是统一线密度、色阶、前中后景、环境连接与印刷表现。对有误的地标定向返工，不允许无依据补楼或虚构校名。若没有可用的生图模型，应停在草图阶段，并报告缺失能力；不得假装已完成。
6. **最终整图审查**：`montage_audit.py` 基于真实照片与最终图，逐栋进行两轮视觉审核，另外对整幅画进行两轮**构图审核**。均有实际图像输入、图片哈希、来源 ID 和模型调用记录。发现陈列板感、额外建筑、错的门窗、文字、风格不一致或不确定 → `needs_review`，不能生成可信交付审批。
7. 审核通过后，用最终整图的 `approval.json` 调用 `convert.py --approval` 生成 SVG/PNG，再由 `build.py` 打包离线 HTML。**不接受草图的审批用于最终图。**




### 结构 / 事实约束不会因“艺术感”消失




- 可以调整**建筑相对位置和相对大小**，也允许部分遮挡；这些艺术处理不能声称真实地理关系。
- 不得改变可见建筑的屋顶轮廓、门洞数、塔楼数量、钟面或主立面识别特征。
- 已被遮挡的特征可以标注“无法核验”，不能默认为正确。必要时改构图以露出特征。
- 连接层应优先用**抽象地线、纹样、水纹、树形装饰**；如果新增“真实建筑或景观”，必须另行核实。
- 官方校名、校徽与字标不应让生图模型臆造，需从可授权的官方资产后期添加。
- 双轮 Agent 审核仍然是模型判断，不等于专家建筑测绘或法务授权。




## 可运行的工作流示例




假设已有一份**真实完成的** `workspace/project.json`，其中 `project.mode="montage"`，且实际图片已经上传给生图工具生成至少两栋的透明 cutout：




~~~bash
# 取证（会拒绝虚假/不完整的来源清单）
python skills/campus-architectural-lineart/scripts/reference_pipeline.py prepare \
  --manifest workspace/project.json --out-dir workspace/grounding




# Agent 生图后已保存 workspace/artwork/cutouts/BuildingA.png 等
# 1) 定主次构图；主建筑须与 project.json 中的 ID 一致
python skills/campus-architectural-lineart/scripts/compose_v2.py plan \
  --manifest workspace/project.json --usage tote-bag \
  --anchor-id BuildingA --output workspace/artwork/montage-plan.json




# 2) 渲染构图草图与整图重绘指令
python skills/campus-architectural-lineart/scripts/compose_v2.py draft \
  --plan workspace/artwork/montage-plan.json \
  --output-dir workspace/artwork/montage-draft
~~~




`--usage` 支持 `tote-bag`、`anniversary-poster`、`ppt-cover`、`city-poster`。目前下游 HTML 预览和导出默认是 **16:9**；`tote-bag` 意味着可作为帆布袋中部的横向印花图案，不代表已经支持全尺寸方形/竖幅印版、出血线、Pantone 或丝网印刷制版。




***非常重要：下面的步骤需要 Agent 真正调用可接收图片的生成或编辑模型。Python 脚本不能生成整图。***




Agent 至少把以下图片作为**真实模型输入**：`montage-draft/draft-layout.png`、所有建筑 cutouts、风格图、每栋建筑的主视角真实照片。模型在保留真实结构的前提下把草图统一重绘成 `workspace/artwork/final-integrated.png`。不得只返回草图或直接把各 PNG 粘贴起来当成最终图。




如果本地 Codex 配置了 `OPENAI_API_KEY`，可以直接用下面的可执行接口调用图像编辑模型，而不需要手工上传多张图片或自行拼写审核日志：


~~~bash
python skills/campus-architectural-lineart/scripts/integrated_edit.py \
  --manifest workspace/project.json \
  --evidence-lock workspace/grounding/evidence-lock.json \
  --plan workspace/artwork/montage-plan.json \
  --draft workspace/artwork/montage-draft/draft-layout.png \
  --draft-evidence workspace/artwork/montage-draft/draft-evidence.json \
  --brief workspace/artwork/montage-draft/integrated-generation-brief.md \
  --output workspace/artwork/final-integrated.png \
  --generation-log workspace/artwork/integrated-generation-log.json
~~~


这个脚本真实调用 OpenAI Images Edit API（默认模型 `gpt-image-2.5-sunburst`），将草图、风格图、每栋建筑单体切片和对应主视角**实拍像素**作为独立图片传入。它会检查输入哈希没有改变、结果确实是生成的 PNG，并写入请求 ID、各输入和最终输出的 SHA-256。需要你自己环境中的 API 密钥，会产生实际 API 费用；**本仓库的 CI 只模拟 API 响应，不等于这条真实生图链路已经跑通**。没密钥但 Codex 自身能调用有图像编辑能力的工具时，仍可以用自己的真实工具调用完成这一步；绝不能伪造日志。


生成后，用**真实**调用记录创建 `workspace/artwork/integrated-generation-log.json`（见后面示例），存储：




- 模型工具与实际 call ID
- 真实上传的 `DRAFT`、`STYLE`、`CUTOUT:<id>`、`PHOTO:<id>:<primary-view-id>` 图片 ID
- 布局、草图、每栋 cutout、最终生成图的 SHA-256




在使用实际 API 审核时：




~~~bash
python skills/campus-architectural-lineart/scripts/montage_audit.py \
  --manifest workspace/project.json \
  --evidence-lock workspace/grounding/evidence-lock.json \
  --plan workspace/artwork/montage-plan.json \
  --draft workspace/artwork/montage-draft/draft-layout.png \
  --draft-evidence workspace/artwork/montage-draft/draft-evidence.json \
  --final workspace/artwork/final-integrated.png \
  --generation-log workspace/artwork/integrated-generation-log.json \
  --output-dir workspace/artwork/montage-audit \
  --provider openai --model gpt-4.1




python skills/raster-to-layered-svg/scripts/convert.py \
  --input workspace/artwork/final-integrated.png \
  --approval workspace/artwork/montage-audit/approval.json \
  --out-dir workspace/dist --size 3840x2160




python skills/offline-svg-color-workbench/scripts/build.py \
  --svg workspace/dist/lineart.svg \
  --png workspace/dist/lineart-transparent.png \
  --output workspace/dist/workbench.html
~~~




有 API 审核时需通过环境变量提供 `OPENAI_API_KEY`；也可以指定 `--provider agent-json --verdict-dir ...`，由实际有视觉能力的 Codex/Agent 生成 `BuildingA__feature.json`、`BuildingA__adversarial.json` 等及 `MONTAGE__feature.json`、`MONTAGE__adversarial.json`，每份都必须登记它真正看过的图像 SHA-256。详见 `references/agent-audit.md`。




### Integrated generation log 示例（字段占位，绝不是已完成的实测日志）




~~~json
{
  "tool": "REPLACE_WITH_REAL_IMAGE_EDIT_TOOL",
  "call_id": "REPLACE_WITH_REAL_RESPONSE_ID",
  "image_input_confirmed": false,
  "reference_ids_attached": [],
  "plan_sha256": "REPLACE_WITH_SHA256",
  "draft_sha256": "REPLACE_WITH_SHA256",
  "output_sha256": "REPLACE_WITH_SHA256",
  "cutout_sha256": {
    "BuildingA": "REPLACE_WITH_SHA256",
    "BuildingB": "REPLACE_WITH_SHA256"
  }
}
~~~




**不要把这个例子的 `image_input_confirmed` 改成 `true`，除非 Agent 确实完成了实际图像输入。** `montage_audit.py` 会拒绝缺少图像输入记录或修改过的源图、草图、cutout 或最终图。




## 什么样的输出算失败？




即使每栋建筑单独很漂亮，只要出现以下现象，就不算纪念式组合：




- 建筑像三张贴纸等间距、完整分离地摆在同一张大白纸上。
- 每栋的线密度、透视画法、深浅层级互不协调。
- 没有共同地面语言或装饰连接，画面整体缺乏主次。
- 主建筑不突出，或辅助建筑被遮挡到失去识别特征。
- 为了补空白编造新桥、新校门、新钟楼、校训或城市景观。
- 模型实际只生成了单栋 PNG，却拿拼贴草图冒充最终纪念画。




`montage_audit.py` 为每栋建筑运行两轮图像审核，还对整体**一幅作品 / 主次 / 连接 / 风格 / 印花清晰度**运行两轮审核；发现问题才允许有针对性返工。必须保留模型观察与图片证据。即便审核全部通过，结论也是 `Agent-reviewed` 而非官方建筑或印刷认证。




## 这次升级的真实验证边界




当前改造已包含可运行的构图草图与完整审核接口以及合成输入的单元测试；**暂未有一个经过真人逐栋核实并用真实生图+视觉 API 完整跑通的校庆主视觉案例**。原来的浙大插画和用户本地测试截图不能被倒填为通过新流程的事实认证。要验证实际纪念式设计效果，还需要从未见过的真实校园或城市任务进行一次黑盒 Codex 端到端实验。


