# Director 原生引擎与融合路由

## 原则

`vendor/vox-director/` 是上游 Director 的完整只读归档，保留 MIT License。不要在 Vendor 内直接修改文件。它用于保留和研究主题预设、提示词结构、Beat/Shot、A/B/C-roll 与运动机制，不是本 Skill 的生产执行入口。

真人口播融合路线的确定性合成引擎是本地 Remotion，但具体拼贴视觉必须优先来自 Director 的生图/拼贴资产。已经在 `local-remotion-preview` 中成立的 Director 风格组件、构图和动画代码只能作为资产适配与运动层复用，不得绕过 Director 改用简化 SVG 主视觉。该路线不调用带默认水印的旧版合成脚本。

我们的新增规范只处理语义准确性、人物使用、不能挡脸、三级安全区、原声时间轴、阅读停留、版本保留和局部返工。它们不得接管或削弱 Director 已经成立的美术系统。

需要更改行为时，在外层增加适配器、配置或 Remotion Composition。这样可随时运行原生基准，并能判断融合版本是否变差。

## 工作前必读

选择 Director 路线时，依次读取：

1. `vendor/vox-director/SKILL.md`
2. `vendor/vox-director/references/prompt-guide.md`
3. `vendor/vox-director/references/beat-layer.md`
4. 需要精确元素动画时读取 `vendor/vox-director/references/local-engine.md`
5. 调用云端模型前读取 `vendor/vox-director/references/models-and-gotchas.md`

不要用本 Skill 中的简短总结代替这些原始说明。

## 基准与生产模式

需要先区分“上游 Director 原生引擎”和“此前依据 Director 机制写成的本地 Remotion 样片”。两者不是同一条执行链。若用户指定 `ai-match-hybrid-15s-v2.mp4` 为对标，质量基准就是该 MP4 及其 Remotion Composition，不得自动改成 Atlas Cloud 版进行比较。

### `director-remotion-baseline`

用途：复现或冻结已经使用 Remotion 制作、并被用户认可的 Director 风格样片。

- 直接读取原 Remotion Composition、素材、关键帧和已交付 MP4；
- 已交付 MP4 是画面事实，使用哈希锁定，不能被后来修改过的工程复渲结果替代；
- 不要求 Atlas API，也不因系统缺少全局 ffmpeg 就判定无法渲染；Remotion 使用自身运行时和媒体工具；
- 融合测试从该工程复制分支做加法，不从云端 Director 流程重新开始。

### `talking-head-fusion-remotion`

用途：已有真人口播，保留原声、人设和表演，同时获得 Director 视觉质量。

保留 Director：

- 主题预设与多轴风格组合；
- Style Bake-off；
- 五段式图片提示结构；
- 视觉 DNA、材质、字体、摄影和拼贴层级；
- Beat/Shot、wide/detail、camera motion 与 element motion；
- 关键帧生成；
- Living poster；
- 元素拆分和本地运动引擎；
- 抽帧和末帧检查。

外层覆盖：

- 原始人声是主时钟，禁止替换配音；
- 使用 SRT 和原片语义段；
- 真人使用原视频、动态抠像或动态窗口；
- 同帧一个真人实例，不挡脸；
- 三级安全区；
- 横竖版重新构图；
- 关键帧审批和局部返工；
- Remotion 负责确定性图层、字幕、人物、地图、路径和工程预览。

该模式不把 Remotion 的 CSS/SVG 当作 Director 生图替代品。以 Director 已审核的拼贴资产、用户原始素材、动态抠像和 Remotion 确定性图层完成画面；CSS/SVG 仅做局部辅助。缺少 Director 资产时提交阻断缺口，不得用抽象符号糊弄，也不在本流程内部静默切换路径。

## 风格调用

主题设计优先调用已经验证的 Director-derived Remotion 组件与资产。需要补足新画面时，可参考 `vendor/vox-director/scripts/styles.py` 与原 `prompt-guide.md` 的媒介、时代、构图、色彩、字体、印刷、情绪和运动维度，但不能把它们缩减成几种颜色、纸片和基础 CSS 图形。不要执行其中的云端生成脚本。

新主题写在外层适配配置，验证后再决定是否向 Vendor 的派生版本合并。原始预设始终保留。

## 关键帧与动画路由

1. 先使用已经成立的 Director-derived Remotion 画面机制设计关键帧；已有优秀本地关键帧可直接保留，例如批准的“选择范围被打开”。
2. 画面只需材质、局部视差和生命感时，在 Remotion 内实现 living-poster 式运动。
3. 关系、人物、字幕和路径全部由 Remotion / 本地元素动画精确控制。
4. 所有片段属于同一视觉系统并共享原声时间轴和最终画幅，但不要求同色、同构图或同一组件模板。

## 质量保护

每轮测试至少保留：

- Director 原生输出；
- 融合输出；
- 相同时间点检查帧；
- 风格、构图、运动、人物、呼吸和完成度比较。

融合输出在关键维度明显弱于原生输出时，不得标记为通过。先定位是关键帧、适配、Remotion 实现还是模型漂移，再只返工失败层。

## 上游完整性

使用 `scripts/verify_director_vendor.py` 检查核心文件、许可证和主题预设入口。Vendor 更新时先复制到新目录进行差异审查，不覆盖当前可运行版本。
