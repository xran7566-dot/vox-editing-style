# 制作连接：粗剪、纯音频、B-roll 与模板

新建运行单使用 v3；v1/v2 仍可读，但不因此宣称具备新版粗剪接入。旧运行单需要新功能时，保留旧文件、重新创建 v3。

## 时间轴与原声

输入 `source_video` 或 `source_audio` 二选一，不把音频伪装成视频。`duration_seconds` 与语义单元的 `time` 保持原片时间。纯音频 persona 的 allowed_forms 必须为 `["voice_only"]`，不创造假口播人物。

`create_fusion_run.py` 先校验原始审核、字幕与粗剪批准，再自动构造 `project.execution`，同时输出 `execution.props.json` 与 `edited.srt`。这一步没有另一次转写，不改字、不自动批准。`execution.duration_seconds` 是成片时长，`segments` 是保留段映射，`semantic_units[].retained_spans` 是每个镜头在成片中的起止；全部被删除的单元不安排镜头。

Remotion 工程必须接收该 execution prop：Composition 时长按执行时长×fps；原声使用 `assets/RoughCutSource.tsx`（mediaType 区分音频/视频）；视觉镜头用 retained_spans 的 output_time 安排；字幕使用 edited.srt，不再使用原片绝对时间。BGM/SFX 也按成片时间排列，原视频不得再重复发声。源路径须复制到本项目 public 后通过 staticFile 引用，不把本机文件路径直接当浏览器 URL。

Studio/渲染命令前运行 `python3 scripts/check_execution_props.py /path/fusion-run.json /path/execution.props.json`，通过后向 Remotion 传 `--props=/path/execution.props.json`。修改源文件、字幕、批准候选或 props 都要重新核对，不能跳过检查。校验保障数据匹配；自定义场景代码仍须通过实际预览确认确实使用该数据，不把 JSON 校验当成画面验收。

## B-roll 和模板的角色

视觉编导决定辅助镜头要表达什么、时间/画幅/素材用途；素材层负责 Pexels/Pixabay 或用户合格素材；镜头制作负责构图、运动与前后衔接；Remotion 执行。B-roll 不必包成卡片，可全屏、局部、抠像或叠层，按语义与整体构图选择。

`visual.visual_source` 支持：

- `director_generated`：保留原有 director_asset_id 与 director_asset_approved。
- `public_broll`：必须有 public_asset_record，来源程序校验通过、素材类型 image/video；同时有 approved=true、selection_reason、scene_path 与 scene_sha256。
- `shotcraft_template`：必须有内置库相对路径 recipe（如 template/TEMPLATE.md 或选定镜头卡），以及 approved=true、selection_reason、scene_path 与 scene_sha256。

scene_path 是本项目实际实现，不是只填写镜头卡名。批准与理由来自用户确认的大纲，不能由工具自动批准；源码修改后重新确认。三条路径共同受 Director 语义方案、真实独立分层及预览审批约束，不放行 SVG 主导或没有素材的临时替代。

B-roll 检索与商用授权并未因此自动完成；本接口只允许有实际文件和合格记录的素材进入制作。
