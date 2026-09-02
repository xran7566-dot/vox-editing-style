# Vox 剪辑风格

一个面向真人口播短视频的 Codex Skill：以原声和 SRT 为时间主轴，用 VOX-CONTENT 完成内容理解与剪辑执行大纲，用 Director 规则主导纸媒拼贴、视觉隐喻和分层构图，再由 Remotion 完成可编辑时间线、MG 动画、字幕、BGM、音效、预览与渲染。

当前版本：`v0.1-beta`

## 适合做什么

- 本地原视频 + SRT 的真人口播剪辑
- 只有原视频、只有语音 + 文案，或混合素材的内容拆解
- 9:16 竖屏、16:9 横屏或保持原片比例的 Vox 拼贴短视频
- 动态真人窗口、动态抠像、原片底片叠加多个 Vox/MG 图层
- 按语义节点驱动进度、路径、步骤、字幕、BGM 和音效
- 在完整渲染前输出审核文档、剪辑执行大纲、真实合成关键帧与局部预览

## 核心稳定性闸门

- 未确认成片画幅，不进入视觉生成或渲染。
- 未完成 `source-review.md`、`source-audit.json` 和用户审核，不进入制作。
- 每个语义镜头至少有 3 个来源与职责独立的可控视觉层；压平拼贴图不能冒充多图层。
- Director 负责视觉规则与主生成路径；Remotion 负责合成和动画；SVG 只能辅助，不能替代主要画面。
- 原声/SRT 是时间主轴；字幕、进度、MG、音效必须绑定语义时间点。
- 不继承上一条视频的版式；不添加工具、Skill 或内部项目水印。

## 安装

```bash
npx skills add https://github.com/xran7566-dot/vox-editing-style --skill vox-editing-style
```

安装后可以这样调用：

```text
使用 $vox-editing-style 处理这条真人口播：先审计素材并生成剪辑执行大纲，等我审核后再制作关键帧和视频。
```

## 输入建议

最稳定的输入是：

1. 原始视频或语音；
2. 对应 SRT（没有 SRT 也可以先从原视频提取/整理）；
3. 目标平台与最终画幅；
4. 受众、传播目标和必须保留的信息；
5. 参考图或参考片的适用范围。

参考内容只作为当前任务的局部依据，不会自动变成以后视频的默认模板。

## 运行结构

```text
素材输入
  ↓
VOX-CONTENT 内容编导层
  ↓
原始资料审核 + 用户确认
  ↓
按时间码生成剪辑执行大纲
  ↓
Director 视觉方案 + 分层清单 + MG 任务单
  ↓
Remotion 真实合成关键帧/短片段审核
  ↓
完整时间线、字幕、BGM、音效与渲染
  ↓
最终 QC + 可编辑工程 + 成片
```

详细流程从 [`SKILL.md`](SKILL.md) 开始，并按其中的链接渐进读取 `references/`。

## 验证

发布包包含确定性检查脚本：

```bash
python3 scripts/verify_director_vendor.py
python3 scripts/validate_source_audit.py /absolute/path/to/source-audit.json
python3 scripts/validate_layer_manifest.py /absolute/path/to/layer-manifest.json --project-root /absolute/path/to/project
python3 scripts/validate_fusion_run.py /absolute/path/to/fusion-run.json
```

## 示例说明

[`assets/approved-range-anchor.png`](assets/approved-range-anchor.png) 仅用于说明一种可接受的纸媒拼贴完成度，不是固定模板、固定配色或固定构图。

`vendor/vox-director/assets/thumbs/` 和上游仓库展示的是 Director 的基础拼贴视觉能力；它们不代表本 Skill 已经提供一条完整的真人口播 + 内容拆解 + Remotion 分层工作流官方样片。当前不收录尚未达到正式展示标准的测试成片。

上游 Director 示例与项目：[Alisa0808/vox-director](https://github.com/Alisa0808/vox-director)

## 依赖与费用边界

- 本 Skill 本身不要求付费 API。
- 本地 Remotion、FFmpeg、Python 等运行环境按具体项目准备。
- 可选的云端生图、音乐或视频接口不会自动调用；任何付费调用都应先说明模型、次数和成本并得到确认。
- `zhiqi-ip-talking-head-decomposer`、`director-brain-review` 等是可选适配能力，不是硬依赖。

## 许可证与第三方代码

本仓库自身内容采用 MIT License。内置的 `vendor/vox-director` 来自 Alisa Qian 的 MIT 项目，保留了其原始许可证和版权信息。详见 [`NOTICE.md`](NOTICE.md)。

