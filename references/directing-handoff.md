# 编导执行合约：缺步骤不能静默进入制作

适用于所有调用者及新旧项目。不是本片手部模板，也不以固定镜头数代替编导。入口已经执行 `validate_review.py` 的工程自动受到该检查约束；复制 Skill 到其他路径后使用当地 Python、FFmpeg 与现有 Remotion，核心检查无本机项目路径。

## 一、已有规范如何落到产物

先执行 vox-content 的语义/真人分工和 edit-execution-outline 的逐镜方案；Director 分支读取 director-integration 指定的原始资料，落实所选方法。将判断写进实际编导报告，报告引用用过的规则/资源与产物位置，不把读过文件当完成证据。

在 `production/shot-plan.json` 保存：

- `version:1`；`directing_report` 和 `source_observation` 是非空实际文件引用 `{path,sha256}`。前者逐镜说明选择与舍弃、用到的 Skill 方法及实现依据；后者记录实际看/听的原片时段、表演/停顿与尚未核对项。不能用字幕复述冒充原片观察。纯音频项目如实记录音频观察。
- `source_audio` 必须与 semantic-timeline 的批准原声引用一致。
- `shots` 按镜头顺序，每项 `id,range,source_cue_ids,purpose,persona_mode,persona_reason,framing,main_action,new_information,handoff,visual_family,implementation`。`range` 末帧不含，必须匹配时间轴和图层清单；source_cue_ids 必须覆盖范围内全部字幕。implementation 是实际组件文件哈希引用，必须与清单路径相同。代码变更要重新核对方案，不能只补新哈希。
- persona_mode 允许 full/circle/rectangle/collage/brief_cameo/voice_only；不是 voice_only 时保存 `presenter_source` 实际视频引用。真人锚点必须 full。原片存在不等于画面已正确使用，仍需实际合成检查。

可复制 `templates/shot-plan.example.json`，但它故意留空，不能直接通过；填写的是已做的判断与证据，不是为了过关补词。资产生成前先完成报告中的设计；代码/素材齐备后 compose 检查全部文件。图像生成工具不在本地渲染器的控制范围内，禁止将此称为能自动阻断所有外部生图。

## 二、跨镜头检查

`visual_family` 如实描述观众看到的主场景/表达方式，同一个画面只改变标题、位移或放大不应改名冒充新类型。连续同一类超过8秒触发检查义务（工程筛查阈值，不是美学定律或最大镜长）：必须增加 `continuity_review={path,sha256,shot_ids}`，报告为什么保留、各段新增理解和停止条件。长镜有充分理由可以通过；不能为躲阈值改标签或强行碎切。

送审前另存 `production/evidence/sequence-review.json`，内容为 `{decision:ready_for_user,report:{path,sha256},shot_ids:[全部镜头按顺序],contact_sheets:[实际合成总览图片引用]}`。报告须结合实际持续时间串看总览，核对主体占用、真人/拼贴分工、语义推进和接力；总览必须来自真实合成帧，素材板不算。内部合成 compose 允许此项待完成，不要求预先拥有尚未渲染的图。

整段自审置于 evidence 而非 shot-plan，避免写入渲染后证据使已有渲染指纹循环失效；真正的镜头设计变更仍会使旧渲染失效。

判不合格填 needs_revision，禁止继续送审；不把“握笔姿态正确”外推为“12秒编排正确”。程序核对报告存在、文件哈希、镜头覆盖与状态，不鉴定报告作者是否诚实、图片是否好看、代码是否完整呈现所写意图。这些仍必须用实际画面/声音检查。

## 三、执行与分发

标准 render_review、package studio/render、build-preview 都经同一个 validate_review 检查。从 compose 开始缺交接即阻断，keyframes 起要求整段自审。shot-plan 进入项目指纹，改变方案会使旧渲染/审批凭据失效。新机器接线时运行 wire_review_gate，不能复制旧机器绝对路径脚本。

回归：`python3 scripts/test_review.py`。要求 Python3、FFmpeg 和 Node/npm（入口回归使用），无需额外 Python 库、账号密钥或付费 API。测试夹具均为合成，绝不用于生产批准。不得通过关闭检查器、改测试期望放行失败样例来“修复”。

边界：Skill 无权修改其他宿主的权限系统，任意代理仍可能不读 Skill、伪造报告或直接运行裸引擎。需要更强限制时，应由宿主强制执行前置检查、限制绕过权限；不能声称复制这份 Skill 就能保证任何模型永不违规。可保证的是：使用随包标准入口时，可检测的必需步骤缺失会失败退出，并给出缺口。
