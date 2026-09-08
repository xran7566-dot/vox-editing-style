# 本地转写与口播粗剪

## 字幕优先级

1. 用户提供 SRT：原样作为字幕依据，不由系统改写。
2. 用户未提供 SRT、但提供 TXT/文案：TXT 是文字依据；本地转写只负责产生时间码草稿。
3. 两者都没有：使用本地 `faster-whisper` 生成 `draft.srt`。

后两种情况都必须把 `draft.srt` 交回用户本人修改专有名词、口头表达和遗漏。只有用户确认的 `approved.srt` 才能进入内容拆解；系统只标记疑点，不得静默改字。

用户提供 SRT 即记录为用户提供，不额外要求改名或重复确认。时间越界、与原声矛盾等异常单列询问。无 SRT 不代表一定是未剪原片，有 SRT 也不代表无需粗剪。音频+文案沿用相同字幕确认流程，不需要真人视频。TXT 不能凭空提供准确时间：先转写取得时间草稿，再依据用户文字校对；无法对应的句子标疑，不能伪造精确对齐。

## 粗剪候选

`Auto-Editor` 仅用于找明显长静音候选。基于已确认的 SRT，Vox 再标记口误、假起句、重复重说与无效整句候选。所有建议写入 `rough-cut-candidates.json`，包括时间码、保留段、删除原因和置信度。

大气口、明显吸气声或句前长换气可列为候选，但必须位于句间或可安全切点附近，并保留自然留白。细小气口、呼吸、自然停顿和情绪停顿默认保留，不能自动删除。

粗剪候选并入 `source-review.md` 由用户一次确认；不得覆盖原片。通过后，Remotion 只按已批准时间码进行非破坏性拼接。

没有候选或用户明确不粗剪时，记录理由、空 items 与完整保留时间轴；不虚构删减。`semantic_review=complete` 只在实际听看检查后设置。审批字段来自用户实际确认，自动测试的模拟批准绝不能写进真实项目。

口误/重复必须同时注明删去原话、保留哪一次表达及依赖关系。Auto-Editor 低音量检测不能判断语义，也不能识别所有大气口；大气口需要试听。长停顿若承担情绪或解释作用仍保留。最终切点避开字音，保留前后留白并听查爆音、吞字和节奏突变。

## 本地安装与命令

先探测系统、Python（建议 3.11+）、FFmpeg 和磁盘空间。使用项目外独立虚拟环境；安装 `scripts/preprocess-requirements.txt`，不修改全局 Python。首次依赖和模型下载需要用户同意；Auto-Editor 可能在首次调用下载对应平台二进制。CPU int8 模式可用，耗时因设备而异；模型越大资源越高，先用 base 做流程测试，不宣称它识别最准。

```sh
python3 -m venv /path/to/vox-runtime
/path/to/vox-runtime/bin/python -m pip install -r scripts/preprocess-requirements.txt
/path/to/vox-runtime/bin/python scripts/local_preprocess.py transcribe /path/to/source.mov --output /path/to/asr --model base --model-cache /path/to/models --allow-download
/path/to/vox-runtime/bin/python scripts/local_preprocess.py silence /path/to/source.mov --auto-editor /path/to/vox-runtime/bin/auto-editor --output /path/to/rough-cut-candidates.json
```

Windows 虚拟环境使用 `Scripts/python.exe` 与 `Scripts/auto-editor.exe`。命令是安装指引，不表示 Windows 已实测。已缓存模型时省略 `--allow-download`，避免重复联网。模型与转写均在本地，模型下载不是上传原片。

试听、文字确认和候选审批完成后：

```sh
python3 scripts/local_preprocess.py timeline /path/to/rough-cut-candidates.json --output /path/to/cut-timeline.json
python3 scripts/local_preprocess.py captions /path/to/rough-cut-candidates.json --srt /path/to/approved.srt --output /path/to/edited.srt
```

候选中保留 `source_sha256`、时长、语义检查状态、批准人/时间；源文件或审批内容变化需重新确认。审核文档记录候选文件 SHA-256。字幕重映射不改字；切点穿过字幕句子会拒绝，先校正切点或按原声拆句并重新确认。执行大纲同时记录原片时间和成片时间，Remotion 可使用 `assets/RoughCutSource.tsx` 接受批准后的保留段；渲染前重新运行审批校验，不接受手写绕过审批的时间轴。

## 配音与消耗边界

粗剪后的完整制作必须使用 [v3 制作连接](execution-bridge.md)，不能只创建 cut-timeline.json 却继续渲染未删减的原片。

粗剪保留已有原声，不新增配音来覆盖口误。只有没有可用人声且用户需要时，单独确认文案和音色后接入配音适配器；本次不捆绑 TTS 模型，不默认调用付费服务。

本地转写与音量检测本身由程序计算，不由语言模型逐帧判断；但工具交互、内容理解与校对仍有 Token 消耗。只读摘要、疑点及必要字幕，不反复灌入完整日志或重跑已通过阶段，不承诺固定额度或百分比。

## 依赖与输出

- 使用本地 `faster-whisper`，不调用云端转写 API。
- 使用本地 `Auto-Editor`，不让它直接交付成片。
- 依赖、模型和下载体积在首次安装前说明并经用户同意；模型文件不进入 Skill 仓库。
- 保留 `draft.srt`、`approved.srt`、`rough-cut-candidates.json`、审核记录和原片，供重开项目时复用。
