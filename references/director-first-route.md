# Director 主生成路径（硬性合约）

## 角色边界

`Vox Director（Vox 拼贴生成器）` 是具体视觉的主生成器，不是可选装饰层。它负责根据语义生成真实的拼贴图/海报、图片素材、纸媒材质、构图、视觉隐喻和元素运动方案。

`Vox剪辑风格（vox-editing-style）` 负责内容、人物使用、时间码、字幕、声音、画幅和审核。

`Remotion`（本地视频合成工具）负责确定性合成：把 Director 产出的视觉资产与真人原片、原声、字幕、BGM 和音效按时间码组合起来。

## 固定调用顺序（不得改路由）

`Director 视觉规则/提示词主导 → 获准的图片生成工具产出 Director 资产 → 本地 Remotion 合成`。

- Director 决定主题、媒介、构图、版式、层级和运动意图；图片生成工具只是执行 Director 提示词的资产生产工具，不能反过来主导版式。
- Remotion 只做本地确定性合成、动态人物窗口、字幕、MG 辅助、时间码对齐和声音层；它不能替代 Director 生成主视觉。
- 未经用户明确批准，不得切换到 Atlas 或其他云端付费视觉 API，不得用 API 生成结果覆盖 Director 路径，也不得因缺少 API 密钥而静默换成 CSS/SVG 主视觉。
- 任何一环不可用都要报告阻断原因并停止，不得自由发挥或偷偷改用另一条生成链路。

## 强制路由

1. 先由 Director 根据每个语义单元生成具体拼贴视觉资产，并记录 `director_asset_id`、来源、提示词、画幅和语义范围。若镜头需要构建式 MG，必须生成可独立控制的组件包或拆层资产，不能只交付一张压平海报。
2. 先审核 Director 关键帧是否具备真实图片、纸媒、材质、层级和叙事关系；不合格就重生成，不得进入 Remotion。
3. Remotion 只能引用已审核的 Director 资产或用户原始素材。它不得凭空用 CSS/SVG 画出主视觉，也不得复制同一张 Director 完整图后通过裁切、放大或遮罩冒充多个图层。
4. SVG、CSS、路径和 MG 只能作为 Director 画面中的局部辅助层，例如遮罩、连线、进度、局部强调和转场；面积和信息量不得取代主拼贴资产。
5. Director 生图或资产读取失败时，状态必须为 `blocked: director_asset_missing`，停止制作并报告缺口；禁止自动降级为抽象 SVG、卡片、色块或临时符号。

## 参考范围隔离

- 用户参考图默认只记录为 `visual_quality` 或 `scene_solution`，仅在本次任务指定范围内生效。
- 只有用户明确说“作为系列统一视觉系统”时，才允许写入 `system_anchor`。
- 新任务启动时清空上一任务的构图、人物位置、版式、颜色、主物件和组件选择；Director 必须重新进行主题/风格选择。
- 参考片不能改变 Director 的原始提示结构、主题预设、拼贴生图能力或其他任务的默认风格。

## 水印隔离

- Vox剪辑成片默认无任何 Skill、工具、模型、Atlas、Director、Remotion 或内部项目水印。
- 不得调用带有默认水印的旧版 `assemble.py` 作为本 Skill 的合成入口。
- 若必须调用上游合成脚本，必须显式关闭水印并在 QC 中检查四角；无法关闭时直接阻断，不得交付。

## 路由验收字段

每个语义单元必须存在：

```json
{
  "visual_source": "director_generated",
  "director_asset_id": "...",
  "director_asset_approved": true,
  "svg_role": "auxiliary_only",
  "watermark": "disabled"
}
```

缺少 `director_asset_id`、`director_asset_approved` 或 `watermark=disabled`，不得启动 Remotion 渲染。

此外必须提供通过 `scripts/validate_layer_manifest.py` 的 `layer-manifest.json`；该校验未通过时，即使 Director 图片存在，也不得启动 Remotion。
