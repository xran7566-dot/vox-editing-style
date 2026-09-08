# 本次交付核对与测试边界

本清单是维护记录，不在每次视频制作时默认加载。

## 已落实的讨论项

| 事项 | 实际位置 | 边界 |
| --- | --- | --- |
| 轻量入口、阶段按需读、断点复用 | SKILL.md | 不承诺固定 Token 数或五小时额度百分比 |
| 内容理解与视觉编导、统一时间码大纲 | vox-content.md、visual-direction.md、edit-execution-outline.md | 原话不改；无依据不造钩子；大纲确认前核对可实现性 |
| 镜头制作内置、模板/卡片/代码关系完整 | vendor/video-shotcraft、shotcraft-integration.md | Vox 管流程；上游 799 文件字节不改；第三方音频不打包 |
| 小索引查询 | scripts/find_shot.py | 返回少量匹配，不输出全库 |
| Pexels 图片/视频，Pixabay 图片/视频/音乐/音效 | public-material-source.md | 网站可选；API 按需确认，不禁用；不依赖别人安装 OpenMontage |
| 图片整理、语义匹配与真实独立图层 | public-material-source.md、layered-scene-contract.md | 不乱用、不强抠、不复制整图凑层；找不到则报告/取消来源 |
| 用户 SRT / TXT / 无文字三路 | local-transcription-and-rough-cut.md | SRT 直接使用；后两路生成草稿由用户校正；音频+文案也须确认 |
| faster-whisper + Auto-Editor | scripts/local_preprocess.py、preprocess-requirements.txt | 本地转写与静音候选，不直接批准或覆盖原片 |
| 大气口、口误、重复、长静音审批 | source-review-template.md、rough-cut-candidates-template.json | 试听大气口；保护小气口和自然/情绪停顿；并入原审核 |
| 删减时间轴与字幕重映射 | local_preprocess.py、RoughCutSource.tsx | 拒绝未审批、源文件变化、受保护删除及跨字幕切点 |
| 配音 | local-transcription-and-rough-cut.md | 粗剪不加配音；无可用人声时单独确认，不安装新 TTS |
| 已有可选参考拆解与既有视觉/字幕/声音规则 | cine-sleuth-adapter.md、subtitle-motion-sound.md 等 | 未删除、未改成硬依赖；不冒充已安装/实测 |

以上是本次已明确采纳项。MoviePy、其他宣传片总控技能或新渲染引擎仅讨论，不擅自安装；没有授权的新 API 不连接。原始素材、真实字幕、测试 MP4、虚拟环境与模型均不放进仓库。

## 实测结果（macOS，本次维护测试）

- 内置上游提交：5f047c7cfe10d6616fe59160a750fcfaea510b2e；799 文件指纹与上游相同。Director 原库 42 文件校验通过。
- Skill 元数据校验通过。入口约 2409 字符；镜头库存储约 17 MB 不代表全部读入上下文。本次未测得可信的整条视频 Token 降幅，不做百分比承诺。
- faster-whisper 1.2.1、Auto-Editor 29.3.1、Python 3.11 CPU 环境：11.89 秒实际原片转写得到 9 个草稿段；同一原片按阈值未检出超过 0.8 秒的长静音，不能据此宣称无口误/无大气口。
- 合成 4 秒音视频：检测到 1–3 秒静音，保留两端各 0.15 秒，候选为 1.15–2.85 秒。真实用户素材没有自动批准。
- 9 项自动化测试通过：时间映射、未审批拒绝、未语义审核拒绝、源指纹变化拒绝、自然停顿保护、区间重叠拒绝、字幕保字、跨句切点拒绝、无需粗剪整段保留。
- Pexels/Pixabay 来源校验另有 7 项离线正反例测试：两站合法记录接受，伪装域名、被拒素材、缺创作者、文件指纹变化、Pexels 音乐类型拒绝。测试不下载真实素材，不充当许可凭据。
- Remotion 4.0.503 代表性渲染：原库 BezierSourceConvergeMerge 168 帧；原模板 SceneFlyIn 191 帧；640×360 技术预览，抽帧见入场、关系构建和落定。仅视觉接入验证，无配乐/音效验收，不是正式成片。
- RoughCutSource：合成测试剪辑输出 69 帧（30 fps，视频时间 2.3 秒），音频编码封装可有尾部 padding；不宣称真实口播剪辑已验收。
- 测试运行环境约 351 MB（含约 141 MB base 模型）；这是本机实测，不是所有平台最低内存要求。

## 尚未验证、不冒充完成

全部 157 张卡与完整模板未逐一渲染；音乐授权/试听、网站素材自动下载、Windows 安装与剪映导出、本地 TTS、真实原片全文校正及内容粗剪仍各按实际任务执行。素材来源规则写入不等于已下载素材；新增源码不是全平台运行证明。

发布必须在程序检查和敏感信息检查后进行，并读回远端版本、对比安装目录；发布结果以实际 Git 提交和本次交付报告为准，不能只凭本文件说已上传。
