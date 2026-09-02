# 分层场景合约

## 目的

把“多图层、构建式 MG”从审美提示变成可程序阻断的生产合约。任何 Vox 拼贴镜头在进入 Remotion 前都必须建立 `production/layer-manifest.json`。

## 独立图层的定义

一个合格的独立视觉层必须同时满足：

- 有独立的 `id`、`source`、`role` 和 `semantic_function`；
- 能在 Remotion 中单独控制位置、遮罩、透明度、缩放、旋转或路径；
- 有自己的进入、关系建立、落定和退出/接力描述；
- 不是同一张完整图片的复制、裁切、模糊、调色、放大或遮罩变体；
- 不把真人、字幕、渐变、调色、音频计入拼贴视觉层数。

每个语义镜头至少需要 3 个独立视觉层，并覆盖背景、结构/关系、主物件/信息、前景/强调中的至少 3 类。至少一个层必须是具备真实质感的图片、照片、抠图、纸媒或视频资产；SVG/CSS 只能辅助，不能用三个抽象形状凑够数量。

每个镜头必须填写 `base_mode`：

- `source_video_base_overlay`
- `collage_main_with_presenter`
- `dynamic_cutout_fusion`
- `mixed_by_scene`

当 `base_mode=source_video_base_overlay` 时，必须有一个 `role=background, source_kind=video` 的原片底层，并在它上方至少存在 3 个独立视觉组件；原片本身不计入这 3 个上层组件。

## 共轴与联动组件

钟表指针、罗盘针、天平臂、坐标轴、仪表盘等“共用一个中心但方向或运动独立”的元素，必须拆成独立 Remotion 组件，禁止预先合并在同一张 PNG、SVG 组或不可分离的图层里。每组必须记录：共同轴心坐标、每个组件的独立 ID、起始角度、目标角度、进入帧和落定帧。

预检至少阻断三类错误：组件轴心坐标不一致；两个方向最终重合或夹角小于项目阈值；把整组旋转当成各组件独立旋转。关键帧必须包含运动前、落点和稳定状态，以目视确认轴心位于真实中心、方向关系符合语义。

## 压平资产

若一张图片已经包含该镜头全部主物件、纸层和关系，它就是 `contains_complete_composition=true` 的压平场景。它可以作为：

- 视觉质量参考；
- 不计入独立层数的底纹；
- 拆层工作的来源母版。

它不能被复制两次后命名为“背景”和“前景”，也不能通过裁切或缩放变成两个独立层。

## 必需文件

- `production/layer-manifest.json`：逐镜头列出真实图层；
- 每个镜头对应的 MG 任务单 Markdown；
- 清单中引用的每个素材文件；
- 清单中引用的 Remotion Composition 文件。

从 `assets/layer-manifest-template.json` 复制模板。完成后运行：

```bash
python3 scripts/validate_layer_manifest.py /path/to/layer-manifest.json --project-root /path/to/project
```

校验失败时状态必须为 `blocked: layered_scene_invalid`。不得生成关键帧、启动 Studio 或渲染样片。

## Remotion 接入

项目的 `check:preview`、`studio`、`stills` 和 `render` 必须先调用本校验器。关键帧审批状态只有在校验通过后才能改为 `approved`。用户说“继续”只能推进已明确展示并通过的当前闸门，不能自动替代分层清单或 MG 动态验收。
