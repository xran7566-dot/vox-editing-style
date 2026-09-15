# 送审证据与执行入口

## 职责与阶段

`validate_layer_manifest.py` 保留结构职责；`validate_review.py` 检查阶段证据、版本与本地媒体。它不能判断好看、动作自然、音效合适，也不能鉴定一句话是否真由用户说出。代理必须保存真实消息出处并实际看图、听声，禁止制造审批或用测试夹具作生产证据。

| stage | 用途 | 要求 |
|---|---|---|
| compose | 内部实际静态合成 | 结构、资产设计与实际文件、原声与字幕事件表；允许待检资产的内部静态合成 |
| keyframes | 交付静态关键帧 | 实际 PNG、渲染回执、原话/时间/重点/动作、资产及合成观察报告 |
| sample-render | 带声短样制作 | 上项 + 用户明确认可当前关键帧及版本 |
| sample-review | 带声样片送审、Studio 与播放器 | 上项 + 实际视频、音轨/时长/原声相关性检查 |
| final-render | 整片制作 | 上项 + 短样用户审核及分轨试听报告；不得把局部测试当整片 |
| final-review | 整片送审 | 上项 + 完整视频检查；最终视觉/听感与用户接受仍需人工完成 |

缺文件、失败、旧版本均阻断，不因 `status=approved` 绕过。最先保存失败原因和下一项可执行工作；已有大纲批准不重新索取。

## 工程文件（相对工程根目录）

- `production/layer-manifest.json`：原有结构清单。
- `production/semantic-timeline.json`：`composition, fps, duration_frames, scope`（`full` 或 `segment`）、`original_audio, approved_srt, captions, scenes, events`。文件引用为 `{path, sha256}`。原声是已批准剪辑对应的本地音频/视频；不能用音乐替代。`captions` 指向 JSON cue 数组，每项 `id,text,start_frame,end_frame`，从批准字幕和已确认剪点映射，不重新转写。`approved_srt` 引用用户批准的原字幕；检查 cue 文本一致。`scenes` 每项含 `id,range:[起帧,末帧不含],new_information,relationship,handoff`，须与分层镜头匹配、范围连续；full 覆盖全片。保存映射依据；SRT 只能定位句子，精确字音仍需试听校准。
- 每个 event：`id,scene_id,cue_id,quote,frame,before,after,information,text_role,relation,sfx,review_required`。句内帧点来自原声校准，动作、文字、接触与音效代码共用 event，不把另一套常数写进组件。`sfx={mode:none,reason:...}` 或 `{mode:file,asset:{path,sha256},frame:事件帧}`。静帧阶段未选音效须明确待办，不能据此声称混音完成。
- `production/asset-plan.json`：`assets` 数组；每项 `id,file,origin,purpose,composition,states,occlusion,text_role,inspection`。生成资产另有 `director_asset_id,prompt:{path,sha256}`；复用旧资产保留实际旧来源，丢失提示词时如实记录缺口，不能伪造生成记录。
- `inspection={decision:usable,observations:实际观察,report:{path,sha256},images:[{path,sha256}]}`。深/浅底边缘、遮挡、合成试摆由人实际查看；仅补字段不会自动变合格。
- `production/review.json`：`project_sha256,keyframes,required_event_ids,internal_visual_review`。每个 keyframe 含 `{path,sha256,receipt:{path,sha256},frame,event_id,quote,focus,expected_action}`。回执由渲染脚本自动生成，记录工程指纹、输出哈希、composition、帧/范围；不能手填替代真实渲染。帧与 fps 提供时间点。
- `internal_visual_review={project_sha256,decision:ready_for_user,observations,report:{path,sha256}}`。
- `keyframe_approval={by:user,decision:approved,project_sha256,artifact_sha256s:[按关键帧顺序],message:{path,sha256},quote,source_reference}`。未收到用户明确认可时不建这项。保留真实消息内容与任务/消息出处，不能拿大纲批准充数。程序核对证据一致性，不赋予代理伪造用户确认的权力。
- 样片 `sample`、整片 `final` 使用同样文件/回执引用；`sample_approval` 结构同上，绑定样片。`internal_audio_review` 含 `project_sha256,sample_sha256,decision,voice_only,voice_with_sfx,observations,report`。填写实际试听观察，不能只写 passed。

指纹覆盖 src、public、根目录配置、语义表、资产计划、分层表和 MG 任务单；代码、遮罩、字幕、声音或素材变化均使旧回执及审核失效。证据放在 `production/evidence/`，不把它再导入 src 造成循环哈希。外部资产必须以文件引用哈希登记；运行时不依赖远程可变 URL。一次只审核明确范围，扩大范围重新补关键帧；局部 `scope=segment` 不得走整片入口。

## 必须接入入口

新建或接续工程先运行 `wire_review_gate.py --project-root 工程目录`，接入现有 package.json 和独立 build-preview.cjs；可用 `--skill-root` 指定安装路径。它不改组件，也不启动播放器。

设 `SKILL` 为当前安装目录，`PROJECT` 为实际工程：

```sh
python3 "$SKILL/scripts/validate_review.py" --project-root "$PROJECT" --stage keyframes
python3 "$SKILL/scripts/render_review.py" --project-root "$PROJECT" --kind still --frame 120 --output /absolute/output/frame-120.png
python3 "$SKILL/scripts/render_review.py" --project-root "$PROJECT" --kind sample --start 120 --end 239 --output /absolute/output/sample.mp4
python3 "$SKILL/scripts/validate_review.py" --project-root "$PROJECT" --stage sample-review
```

`render_review.py` 使用已有本地 Remotion，不安装依赖；必要时指定已有 `--browser-executable`。静帧入口只检查 compose，不错误要求尚未产生的静帧审核。普通 `studio` 与 `build-preview.cjs` 在实际启动/编译前必须执行 `sample-review`（先有经过音轨检查的实际短样）；`render` 使用包装脚本，不直接运行裸 Remotion 视频渲染。输出后才执行 sample-review/final-review，不能只检源组件有 Audio 标签。原声相关性检查仅用于当前未变速的粗剪音轨；变速等情况需先生成与批准时间轴一致的原声参考，不能降低检查阈值掩盖错误。

裸 CLI 可以绕过包装器，这不是访问控制系统。代理必须遵守这些入口；不能把内部无声诊断公开成动态送审。回归测试通过仅证明所列反例被拦截，不能证明所有潜在内容错误都能自动检测。

## 旧入口迁移

`validate_review_gate.py` 保留旧命令名和 stills/sample/review-sample/full 参数，统一映射到本合约；不维护第二套审批。旧 review-plan.json/review-state.json 不自动升格为新审批。迁移实际素材、事件和检查报告后重新生成回执，用户未认可的关键帧保持待审。旧改动中的逐镜范围、字幕原文核对、资产覆盖和真人锚点限制已并入主检查器。

历史生成资产缺原始提示词/ID时可以进行内部静态检查并交付明确标注缺口的关键帧，但动态入口仍阻断，不能编造记录；已存在的本地追踪ID须明确其来源，不能冒称提供商ID。
