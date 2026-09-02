# 原始资料审核脚本合约

## 目的

将“看过原始资料”变成可审批、可追溯、可校验的生产闸门。拆解 Skill 负责提取与结构分析；本合约负责锁定事实、身份、时间、禁令和用户批准。

## 输入路由

- 公开抖音/小红书链接：当环境已安装时可选调用 `$zhiqi-ip-talking-head-decomposer` 的“提取+拆解”路由；它不是本 Skill 的硬依赖。没有该适配器时，要求用户提供视频、SRT 或文稿。只提取文案时不下载视频；不自动调用付费 API。
- 本地原片/SRT/文稿/图片/录屏：本地读取和拆解，不上传私有素材。
- 混合输入：为每条结论保留 `source_id`，不把参考视频的人物、背景、姓名或账号合并进主体素材。

## 人工审核脚本

生成 `source-review.md`，使用以下顺序：

1. 项目、平台、画幅、时长和传播目标。
2. 创作者姓名/账号、原始表达意图和绝不能替换的身份信息。
3. 素材清单：角色、绝对路径或公开 URL、SHA-256、提取方式。
4. 按原声/SRT 时间切分的语义单元：原文、关键词、核心观点、观众应理解什么、必须保留、禁止虚构。
5. 内容遗漏与错误检查：已识别关键词、已识别核心观点、可能遗漏、疑似错误/错听/时间码不一致、需要用户确认。
6. 事实/主张表：原片明说、外部已核实、待确认或只是参考假设。
7. 参考素材范围：`scene_solution`、`visual_quality`、`technical_mechanism`、`system_anchor` 或 `needs_user_decision`。必须记录本次是否允许继承上一任务的版式/风格；未明确批准时，参考图只对当前任务生效，不得自动继承到后续任务。
8. 素材缺口、不确定项和是否阻塞生产。
9. 声音方案：BGM 情绪、能量曲线、乐器/音色禁忌，以及每个语义节点允许的音效类型、落点和强度。所有声音选择必须能回指到文案语意，禁止后期凭听感自由添加。
10. 用户审批区：通过、需修改或拒绝，并记录确认时间。

`source-review.md` 是审核证据，不是新口播稿。不改写原文，不将推断写成事实。

## 机器校验清单

生成同目录的 `source-audit.json`，使用 `vox-source-audit/v1` schema，必须包含：

- `project_name`、`source_mode`、`public_source_urls`、`duration_seconds`；
- `review_script`；
- `source_artifacts[]`：`id`、`role`、`path`、`sha256`；当 `bgm_enabled=true` 时必须包含 `role=bgm` 的已指纹音轨。
- `creator_identity`：`creator_name`、`account_name`、`must_preserve[]`、`must_not_substitute[]`；
- `content_intent`；
- `content_plan`：开头候选、选定开头、前三秒检查、中段钩子、结论、CTA、真人出现时机和动效层次；每个判断必须能回指语义单元。
- `sound_direction`：`bgm_enabled`、`emotion`、`energy_curve`、`must_avoid[]`、`selection_rule`；
- `semantic_units[]`：`id`、`time`、`transcript_exact`、`takeaway`、`must_preserve[]`、`must_not_invent[]`；
- 每个 `semantic_units[]` 还必须有 `sound_plan`：`bgm_role`、`emotion`、`sfx_events[]`；
- `reference_decisions[]`：`id`、`scope`、`applies_to[]`；
- `uncertainties[]` 与 `asset_gaps[]`：`item`、`status`；
- `approval`：`status`、`approved_by`、`approved_at`。

产生不变式：

- `source_video` 必须存在且指纹一致。
- `srt` 或 `transcript` 至少存在一个且指纹一致。
- 语义单元不重叠，不超出视频时长。
- 没有 `blocking` 不确定项或素材缺口。
- `approval.status` 必须为 `approved`，`approved_by` 必须为 `user`。
- `sound_direction` 和每段 `sound_plan` 必须与文案语意一致；不得用未在审核稿中记录的情绪、乐器或音效。

运行：

```bash
python3 scripts/fingerprint_source_audit.py /absolute/path/to/source-audit.draft.json /absolute/path/to/source-audit.json
python3 scripts/validate_source_audit.py /absolute/path/to/source-audit.json
```

通过后，将 `source_audit` 绝对路径写入 fusion input。任何素材修改都会使 SHA-256 校验失败，必须重新拆解和审批。
