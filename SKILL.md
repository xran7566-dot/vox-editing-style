---
name: vox-editing-style
description: 制作或审核保留原声与人物表达的 Vox/编导型口播短视频。用于素材审计、剪辑大纲、Director 视觉、多图层 MG、字幕声音对齐、Remotion 渲染和局部返工；按阶段加载资料，避免简单任务进入完整制作链。
---

# Vox 剪辑工作室

原片、原声和语义是时间主轴；Director 负责视觉语言与主资产，Remotion 负责真人、字幕、独立图层、声音和最终时间轴。先识别当前阶段，只加载该阶段资料；用户未要求继续时，不自动进入下一阶段。

## 轻量路由

- **A 素材接收**：确认素材、成片画幅、原声、SRT、参考范围和缺口。只读本文件；用户要看全流程时读 [端到端流程](references/vox-editing-workflow.md)。
- **B 本地预处理**：媒体探测、字幕生成/导入、粗剪候选。用户提供参考视频且明确同意云端拉片时，才读 [CineSleuth 适配器](references/cine-sleuth-adapter.md)；只运行对应本地脚本或适配器；不读 Director、MG、内容审核和渲染资料。
- **C 内容与大纲**：读 [内容编导](references/vox-content.md) 和 [原始资料审核](references/source-audit-contract.md)；审核获批后才读 [剪辑执行大纲](references/edit-execution-outline.md)。
- **D 视觉方案**：读 [Director 集成](references/director-integration.md) 和 [主生成路径](references/director-first-route.md)；只有执行大纲明确需要公共素材时才读 [公共素材来源](references/public-material-source.md)；只有此时才读 `vendor/vox-director/SKILL.md`。
- **E 分层动画**：读 [分层场景](references/layered-scene-contract.md)；复杂关系再读 [MG 任务单](references/mg-task-card.md)；涉及字幕、进度或声音再读 [字幕·动画·声音](references/subtitle-motion-sound.md)。
- **F 预览与验收**：读 [审批与验收](references/approval-and-qc.md)；只有发生已知复发问题时才读 [防错闸门](references/recurring-failure-gates.md)。

只有用户要求完整融合生产时，才读 [完整运行层](references/fusion-operating-model.md) 和 [运行单合约](references/fusion-run-contract.md)。

## 全阶段硬闸门

1. 视觉制作前必须确认成片画幅；不得继承旧项目的版式、构图、人物位置、颜色、素材、SVG、水印或参考范围。
2. 有可用真人原声时保留原声、口型、表演、人设和原意；无可用人声或用户明确要求时，才允许本地配音。
3. 未获批准，不调用付费转写、TTS、音乐、图像或视频 API，也不上传私有素材；默认禁止一切工具或第三方水印。
4. Director 主资产缺失时停止视觉制作，不能用旧资产、卡片、抽象 SVG 或素材板替代；SVG 只能辅助。
5. 每个正式语义镜头至少有 3 个来源与职责独立的可控视觉层；真人、字幕、渐变、调色和音频不计入。复制或裁切同一压平图片仍算 1 层。
6. 关键帧必须来自实际合成画面；完整渲染前先审语义关键帧或短片段，返工只修改失败段。

## 断点复用

项目目录维护 `run-state.json`，仅记录素材哈希、画幅、当前阶段、产物路径、审批和阻塞项。继续时先读它：素材未变就复用字幕、审核、大纲、资产和审批；素材变化只重跑受影响的后续阶段。不要把整份 SRT、日志或手册反复写入对话，脚本只返回摘要、异常和路径。

## 核心制作规则

- 真人按语义选择全屏、动态抠像、圆形/矩形窗口、局部出现或隐藏；卡片不是默认形式。
- 字幕默认一句一行；只有同一句不宜拆分时才两行。不得在侧边重复底部字幕。
- 进度、节点和路径必须绑定原声/SRT 的语义事件帧，不得按固定帧匀速运行。
- BGM 默认使用符合语义的低调本地纯器乐，用户明确不要时关闭；音效只服务节点、关系、结论和 CTA，并低于人声。
- 变化必须有因果和接力。不得用重复图片、空白卡片、漂浮缩放或无意义符号凑层次。
- 交付保留可编辑工程、素材、时间码和可再次打开的预览入口，不能只交 MP4。

## 依赖边界

本地字幕、粗剪和配音使用可选适配器，模型文件不进入仓库。缺少适配器时先说明下载体积和资源要求，由用户决定是否安装。风格扩展优先使用小型 `visual-style.json`；只有真正更换执行引擎时才接外部 Skill。
