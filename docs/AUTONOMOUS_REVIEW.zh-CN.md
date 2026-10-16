# 让 Agent 自己审建筑线稿：图像证据、两轮视觉检查、按风险升级

这是 `campus-architectural-lineart` 的 **v0.3.0** 新能力，目标是减少真人重复检查照片、门窗、屋顶的工作量，而不是声称图像模型能保证建筑绝对真实。

## 谁负责什么？

| 环节 | Agent / 视觉模型 | 程序 |
| --- | --- | --- |
| 查找建筑照片 | Agent 用网站检索和视觉能力查找、交叉核实并提供出处 | `reference_pipeline.py fetch` 仅下载已登记照片 |
| 确定结构事实 | Agent 对照原始实拍，填写门洞、屋顶、钟楼和未知区域，留下照片 ID | 检查字段、分辨率、重复照片、视角与哈希，裁切指定结构区域 |
| 生成建筑 | 有图片输入能力的生图模型处理**真实照片像素**与风格图 | 用 JSON 记录实际生成调用和每栋 PNG 哈希 |
| 审核生成 | 单独的视觉审查调用，**两轮**从候选图和实拍中找差异 | `agent_audit.py` 强制证据引用、完整 ID、置信度与哈希检查 |
| 多栋拼贴 | Agent 选布局，每栋单独生图、审核 | `compose.py` 纯像素合成，不编造建筑 |
| 返工 | Agent 根据审核缺陷和局部参考照片编辑失败的建筑 | 输出 `retry-brief.md`，更新图片哈希并要求重新审查 |
| 最终导出 | 低风险双轮一致时自动放行，不确定或高风险升级人审 | `convert.py --approval` 校验审查模式与原图哈希 |

## 输入协议

**Agent 自动整理来源，不等于网页被可信地证明是真实建筑。**

对公开、有明确可复用许可的照片，可以用 `agent_confirmed_photo: true` 搭配结构化 `agent_evidence`，而不是伪造 `human_confirmed_photo`。至少有可核实的来源页、许可依据 URL、浏览/视觉模型调用标识、置信度和具体观察，且需要明确 `derivatives_allowed: true` 的证据。

例子（**字段示例，绝不是对真实照片的事实认证**）：

```json
{
  "id": "front",
  "file": "photos/front.jpg",
  "source_page": "https://EXAMPLE.ORG/original/photo",
  "original_url": "https://EXAMPLE.ORG/original.jpg",
  "photographer": "verified source credit",
  "license": "verified permissive license",
  "derivatives_allowed": true,
  "human_confirmed_photo": false,
  "agent_confirmed_photo": true,
  "source_verified_by": "Agent vision reviewer",
  "view_angle": "front",
  "agent_evidence": {
    "model": "actual vision model",
    "call_id": "actual recorded response ID",
    "confidence": 0.95,
    "source_page_checked": true,
    "building_identity_checked": true,
    "license_checked": true,
    "license_evidence_url": "https://EXAMPLE.ORG/actual-license-page",
    "observation": "Concrete details linking the photograph, source page and observed facade"
  }
}
```

对建筑局部特征使用 `visible_and_agent_verified: true` 和 `agent_evidence`，其中需要 `image_input_ids` 指向真实看过的建筑照片，例如 `["BuildingA:front"]`，另有模型标识、调用 ID、具体观察和置信度。

**这些字段仅能证明登记形式完整，不能证明所填信息客观正确。** 用户自有照片的授权和未知版权仍需相关权利人的实际确认；无法确认来源、文字/校徽授权时必须阻断。

## 生成完成后运行双轮自动审核

完整用法参见 [`agent-audit.md`](../skills/campus-architectural-lineart/references/agent-audit.md)。预先准备：

- `project.json`：逐建筑照片与结构特征清单。
- `evidence-lock.json`：已通过 `prepare` 的原图/清单哈希。
- `final.png`：当前模型生成图，如果是多栋拼贴，额外提供 `cutouts/BuildingA.png` 等逐栋图。
- `generation-log.json`：**实际**图像生成调用记录，照片输入 ID 以及真实文件 SHA256。

有自己的 OpenAI 视觉 API 凭证时：

```bash
python skills/campus-architectural-lineart/scripts/agent_audit.py \
    --manifest workspace/project.json \
    --evidence-lock workspace/grounding/evidence-lock.json \
    --generation-log workspace/artwork/generation-log.json \
    --image workspace/artwork/final.png \
    --feature-crops-dir workspace/grounding/feature-crops \
    --output-dir workspace/artwork/agent-audit \
    --provider openai --model gpt-4.1
```

环境变量 `OPENAI_API_KEY` 需要用户设置，不会写进仓库。当前实现使用 OpenAI Responses API 发送真实图片像素和严格 JSON Schema；成功的审查调用在报告中保留响应 ID。**没有密钥时不会假装已经完成审查。**

在已有多模态 Agent 环境中，可以让 Agent 实际查看候选与原始照片两次，输出两份结构化 `BuildingA__feature.json`、`BuildingA__adversarial.json`，再运行相同的脚本并指定 `--provider agent-json --verdict-dir ...`。这种模式依赖执行 Agent 正确记录它看过的图片和调用 ID，`agent-json` 必须为每张实际查看的图片填入 `input_sha256`；脚本将这些哈希与当前文件核对，防止复用旧图的判断，但仍无法加密证明视觉模型真的看过这些图片。

## 审核决策

- 两轮审查目的不同：一轮逐特征确认，一轮主动寻找反例；不会把一个模型一句「看起来没问题」当作通过。
- 每项审查结果必须是 `pass / fail / unknown`，有具体证据照片 ID、可观察的比较事实、明确的差异字段、数值置信度。默认阈值 `0.90`；这是模型自报值，不是可靠校准的概率。
- 所有建筑与全局检查均一致通过、参考哈希不变、生成调用记录完整后，才写 `approval.json` 的 `approved`。它清楚标记为 `agent_vision_two_pass`，不是人工证明。
- 任一不确定、两次不同、模型输出截断、文字或新增结构、生成图被修改、照片来源未锁定，都返回 `blocked`。失败时给出 `retry-brief.md`，Agent 可用局部证据重试最多两轮，不通过则只把具体疑点交给人。
- `photo-faithful` 严格复原默认升级人工审查；明确要求低保障自主模式时才可以使用 `--permit-photo-faithful-auto`。商标/官方文字以及法律授权仍不可用自动评分替代权利确认。

## 已验证的内容与未验证的内容

代码通过模拟输入的单元测试，证明发现缺证据、不同意见、低置信度等情况可以拒绝错误放行。**仓库里的旧浙大图是未经逐栋核验的示例，不自动得到新的 Agent 审核合格证明**。

当前测试**没有使用真实模型 API**，因为 CI 不持有用户密钥。实际模型的判断准确率还需用人工标注的真实建筑基准测试，不能把「代码运行通过」误报成「现实中的审核准确率已达标」。
