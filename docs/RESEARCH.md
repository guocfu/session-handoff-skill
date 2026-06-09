# Session Handoff 项目启发分析

> 本文档只分析与 `session-handoff` 直接相关的能力：保存当前会话状态，并让下一个会话可靠恢复或继续。
> 不分析完整长期记忆、向量库、Web UI、MCP server、治理框架、发布系统或通用知识库能力。

## 一、结论

`session-handoff` 仍然有必要继续做，但不应该做成更大的记忆系统。

它的合理定位是：

> 一个跨 agent、跨工具、无服务依赖、可审计的短期会话交接 skill。

它应该吸收 `agent-handoff-kit`、`ai-memory`、`OpenViking` 中的这些轻量机制：

- 状态指纹：确认项目、分支、HEAD、未提交文件和验证状态。
- 恢复边界：默认只读恢复，用户明确要求后才继续执行。
- 防自污染：不要把旧 handoff、旧恢复复述、recall 注入块或完整日志写回新 handoff。
- 状态对账：完成项、风险、验证结果、下一步之间不能互相矛盾。
- 可审计性：所有关键状态写在项目文件里，而不是隐藏在服务、数据库或模型记忆中。

它不应该吸收这些重型能力：

- 向量检索和自动 recall。
- 完整 transcript 捕获。
- MCP/server/SQLite/wiki runtime。
- 多文件治理目录和 rule pack 系统。
- 隐式长期偏好记忆或跨项目全局记忆。

最有价值的下一版不是“记住更多”，而是“更可靠地保存一份短、准、可继续的 handoff”。

## 二、相关项目只看会话保存部分

### 2.1 ai-memory

**保存会话机制**

`ai-memory` 通过生命周期 hook 管理会话状态。`session-start` 读取最新 handoff 并注入新会话；`session-end` 或类似事件把会话摘要、open questions、next steps、files touched 等字段写入 handoff。它把 handoff 作为一等结构，而不是从日志里临时推断。

它还有状态机概念，例如 `open -> accepted/expired`。这适合自动注入型系统，因为读取 handoff 可以被视为一次“消费”。

**值得借鉴**

- handoff 应短小、结构化、面向下一步，不是完整聊天记录。
- 保存前应做隐私清洗、长度限制和字段校验。
- 应保留来源信息，例如来源会话、agent、cwd、创建时间。
- 项目归属需要明确，否则容易跨目录误恢复。
- 自动 hook 可以提高可靠性，但应先做提醒或草稿，不能默认生成低质量 handoff。

**不建议照搬**

- 不照搬 Rust/MCP/SQLite/server/wiki 体系。
- 不采用“读取即消费”的默认语义。`session-handoff` 的只读恢复应可重复查看。
- 不依赖粗糙的自动摘要作为唯一 handoff。最终 handoff 应可审阅、可修改。

### 2.2 OpenViking

**保存会话机制**

OpenViking 把 session 按 `session_id` 持久化。消息先写入当前会话记录，到达 compact、session end 或阈值时 commit。恢复时不重放完整 transcript，而是组合 archive overview、当前未归档消息和必要 recall。

它特别强调 capture 和 recall 隔离：保存新状态时要剥离上次注入的上下文，避免把召回内容再次写入记忆，造成自污染。

**值得借鉴**

- 保存和恢复要分层：capture 记录事实，save 生成稳定摘要，resume 注入精简上下文。
- handoff 主体应有 token budget 意识，细节用文件路径、命令、归档链接指向。
- 恢复时应先验证本地状态是否和 handoff 匹配。
- 保存前需要防自污染规则，避免旧 handoff、recall 块、旧启动提示循环放大。
- compact/end 前的保存应同步落盘，不能依赖后台最终一致性。

**不建议照搬**

- 不引入完整向量库、自动 recall、LLM 记忆抽取。
- 不捕获每轮完整 transcript 或完整 tool output。
- 不让恢复依赖异步摘要生成。
- 不把摘要当作高于当前工作区、git 状态和用户最新指令的事实来源。

### 2.3 agent-handoff-kit

**保存会话机制**

`agent-handoff-kit` 的核心不是 CLI 自动保存，而是让 agent 在“收工 / wrap up / handoff”时按固定合同维护文件。

它把 `dev/SESSION_HANDOFF.md` 作为当前状态真源；`START_NEXT_SESSION_PROMPT.txt` 是便利副本；`dev/SESSION_LOG.md` 只做近期证据和追溯，不承担下一次继续的责任。

它还强调 closeout：不要在旧状态后继续追加新快照，而是重写或确认当前状态区。

**值得借鉴**

- `SESSION_HANDOFF.md` 应是真源；启动提示副本只能是镜像。
- 当前状态和历史证据要分开。
- closeout 时做生命周期一致性检查。
- opening message 中应包含项目/目录校验。
- 用户说“开工/收工”这类短语时，如果语义可能有歧义，应先确认。

**不建议照搬**

- 不照搬完整治理层：`PROJECT_INDEX`、`DOC_SYNC_REGISTRY`、`RULE_PACKS`、决策日志、集成治理等。
- 不照搬大量 `ack:*` 机器锚点。轻量 handoff 用固定标题和少量可选标识即可。
- 不引入 npm 安装、升级迁移、doctor 全套 runtime 作为 skill 核心。
- 不默认引入长期 `SESSION_LOG` 维护机制。

## 三、共同设计原则

### 3.1 handoff 是短期接力，不是长期记忆

handoff 只保存下一位 agent 继续工作所需的状态：

- 当前目标。
- 已完成事项。
- 当前工作区状态。
- 关键文件。
- 决策与原因。
- 验证结果。
- 风险和阻塞。
- 下一步。

它不保存完整聊天记录、完整日志、长期偏好、通用知识或跨项目记忆。

### 3.2 只读恢复是默认安全边界

新会话读取 handoff 后，默认只应：

- 复述当前目标。
- 说明当前状态。
- 列出风险/阻塞。
- 说明验证状态。
- 推荐下一步。

只有用户明确说“继续执行”“continue”“按 Next Steps 做”时，agent 才应开始修改文件或运行有副作用命令。

### 3.3 当前工作区高于 handoff 摘要

handoff 可能过期。恢复时应优先相信：

1. 用户最新指令。
2. 当前文件系统和 git 状态。
3. 当前测试/验证结果。
4. `SESSION_HANDOFF.md`。
5. 更早的归档或日志。

如果 handoff 与当前状态冲突，应先说明差异并请求确认，不能静默继续。

### 3.4 防自污染要具体

保存 handoff 时禁止写入：

- 上次 `SESSION_HANDOFF.md` 的 `Next Session Opening Message` 作为当前事实。
- 只读恢复时 agent 的复述文本，例如“当前目标是……”。
- 完整聊天记录。
- 完整命令输出，例如整段 `git status`、测试日志或 stack trace。
- 其他项目或其他 session 的 `SESSION_HANDOFF.md` 内容。
- `MEMORY.md`、`CLAUDE.md`、recall 注入块里的长期记忆内容，除非它已经被明确验证为本项目当前事实。

handoff 应只保存最新事实、决策、验证结果和下一步。

## 四、对 Claude Code 补充意见的判断

Claude Code 对上一版分析的批评整体合理，尤其是这些点：

- 绝对路径跨机器会失效。
- `Handoff Sufficiency` 不能作为纯脚本客观校验。
- 防自污染规则需要具体示例。
- “启动提示副本漂移”表述不清晰。
- checkpoint 和 full save 的区别需要定义清楚。
- P0 项过多，需要再次排序。
- 多个建议和已有分析重复，需要合并。

整理后的修正判断如下。

### 4.1 Workspace Identity 不应只用绝对路径

绝对路径对同一台机器很有用，但跨机器、WSL、容器、CI 或不同用户目录时会失效。

更合理的做法是同时记录“可迁移身份”和“本地观察值”：

```md
## Workspace Identity
- Project name: <repo or directory name>
- Git root name: <repo root directory name or unknown>
- Relative path: <path from workspace root or .>
- Branch: <branch or unknown>
- HEAD: <commit hash or unknown>
- Local root observed at save time: <absolute path or unknown>
- Dirty files: <summary or none>
```

恢复时：

- `Project name / Git root name / Branch / HEAD` 是主要匹配依据。
- `Local root observed at save time` 只做提示，不应在跨机器时直接判定失败。
- 如果项目名、分支、HEAD 或 dirty files 明显不一致，应先说明差异。

### 4.2 Handoff Sufficiency 是 agent 自检，不是脚本真理

`Handoff Sufficiency` 可以保留，但应明确它是保存流程中的 agent 自检：

```md
## Handoff Sufficiency
- Can the next agent continue without old chat history? <yes/no>
- Missing context if no: <what must be added>
```

脚本只能做有限检查：

- 该 section 是否存在。
- 是否仍是占位符。
- 是否为空。

脚本无法客观判断“是否真的不需要旧聊天历史”。这部分必须由 agent 在保存时负责。

### 4.3 启动提示副本漂移要改成明确说法

不要使用“prompt mirror drift”这种术语。

应写成：

```text
SESSION_HANDOFF.md 中的 Next Session Opening Message 与 START_NEXT_SESSION_PROMPT.txt 是否一致。
```

如果两者都存在且不一致，以 `SESSION_HANDOFF.md` 为准。

### 4.4 Checkpoint 和 Full Save 要分清楚

可以引入 checkpoint，但必须定义边界：

| 特性 | Checkpoint | Full Save |
|------|------------|-----------|
| 目标 | 长会话中途防丢进度 | 会话结束交接 |
| 归档旧 handoff | 可选，默认可不归档以减少噪声 | 是 |
| 更新范围 | 当前目标、风险、下一步、关键文件 | 完整 handoff |
| 状态对账 | 简化检查 | 完整检查 |
| 适用场景 | “先保存一下进度”、pre-compact | “收工”、切换 agent、结束会话 |

为了避免 checkpoint 覆盖掉有价值的旧 handoff，至少应使用原子写入；是否归档可以作为参数。

### 4.5 P0 需要拆成更细优先级

上一版 4 个 P0 太多。更合理的顺序是：

| 优先级 | 改进项 | 理由 |
|--------|--------|------|
| P0-a | 防自污染规则 | 纯规则改动，成本最低，立即提升质量 |
| P0-b | 扩展 `check`：占位符、Next Steps、Verification、opening message | 标准库脚本即可实现，收益高 |
| P0-c | Workspace Identity / 状态指纹 | 模板和脚本都要改，收益高但成本中等 |
| P1-a | Handoff Sufficiency 自检 | 有价值，但依赖 agent 判断 |
| P1-b | `status` 输出 stale/mismatch 信息 | 实用，但可在状态指纹之后做 |

## 五、整理后的改进路线图

### P0-a：防自污染规则

更新 `SKILL.md` 的 Writing Rules，加入明确禁止内容和示例。

验收标准：

- 保存 handoff 的规则中明确禁止复制旧恢复文本、完整日志、recall 注入块。
- README 或研究文档说明该规则来自 capture/recall 隔离思想，但不引入自动 transcript 捕获。

### P0-b：增强 `handoff.py check`

增加低成本确定性检查：

- 必备标题存在。
- 疑似 secret。
- 行数上限。
- 未替换占位符，例如 `<...>`。
- `Next Steps` 不应为空或只写 `None`，除非任务确实结束。
- `Verification` 不应只有空泛内容。
- `Next Session Opening Message` 必须同时有 read-only 和 continue 两种入口。

验收标准：

- 新增测试覆盖这些检查。
- `check` 的错误信息能指导 agent 修复。

### P0-c：Workspace Identity / 状态指纹

在 handoff 模板中加入工作区身份信息：

```md
## Workspace Identity
- Project name: <repo or directory name>
- Git root name: <repo root directory name or unknown>
- Relative path: <path from workspace root or .>
- Branch: <branch or unknown>
- HEAD: <commit hash or unknown>
- Local root observed at save time: <absolute path or unknown>
- Dirty files: <summary or none>
```

脚本可提供辅助信息，但最终仍由 agent 写入 handoff。

验收标准：

- `template` 输出包含该 section。
- `status` 能读取并展示当前 handoff 的关键身份信息。
- 恢复流程要求比较 handoff 与当前本地状态。

### P1-a：Handoff Sufficiency 自检

在模板中加入：

```md
## Handoff Sufficiency
- Can the next agent continue without old chat history? <yes/no>
- Missing context if no: <what must be added>
```

验收标准：

- `check` 只检查该 section 是否存在和是否仍是占位符。
- SKILL.md 明确这是 agent 自检，不是脚本可完全判断的事实。

### P1-b：增强 status

让 `status` 输出更接近恢复前检查：

- handoff 是否存在。
- 更新时间和年龄。
- handoff 中记录的分支/HEAD。
- 当前分支/HEAD。
- 是否存在 Next Steps。
- 是否存在占位符。
- 如存在 `START_NEXT_SESSION_PROMPT.txt`，它是否和 handoff 中的 opening message 一致。

验收标准：

- 不修改文件。
- 输出短、可扫描。
- 测试覆盖 handoff 存在、不存在、分支不匹配、占位符存在。

### P1-c：可选 START_NEXT_SESSION_PROMPT.txt

支持生成便利副本，但保持 `SESSION_HANDOFF.md` 为真源。

建议命令：

```bash
python scripts/handoff.py prompt --root <project-root> --write
```

规则：

- 从 `SESSION_HANDOFF.md` 的 `Next Session Opening Message` 生成。
- 两者不一致时，以 `SESSION_HANDOFF.md` 为准。
- 不强制每个项目都使用该文件。

### P2-a：Checkpoint 模式

增加轻量保存语义，用于长会话中途。

建议命令方向：

```bash
python scripts/handoff.py checkpoint --root <project-root>
```

但要谨慎：脚本无法替 agent 总结上下文。更现实的第一步是只在 SKILL.md 定义 checkpoint workflow，而不是马上写自动生成器。

### P2-b：可选 lifecycle hook 示例

为 Codex / Claude Code 提供可选示例，而不是默认安装。

用途：

- session end 时提醒保存 handoff。
- pre-compact 前提醒 checkpoint。
- stop 时检查 handoff 是否过期。

不建议默认自动写入 handoff，因为低质量自动摘要会误导下个会话。

### P2-c：归档索引

为 `.codex/handoffs/` 生成简单索引：

```text
.codex/handoffs/INDEX.md
```

记录：

- 时间。
- 分支。
- HEAD。
- 当前目标。
- 归档文件名。

这可以提升追溯能力，但不应发展成长期记忆数据库。

## 六、最终判断

Claude Code 的补充意见合理，但不能直接原样附在文档末尾，否则文档会变成“分析、再批注、再批注”的堆叠结构。

整理后的判断是：

1. 绝对路径问题成立，但应改为“可迁移身份 + 本地观察路径”，而不是完全删除本地路径。
2. `Handoff Sufficiency` 有价值，但属于 agent 自检，不属于纯脚本客观校验。
3. 防自污染是下一版最应该先做的规则增强。
4. checkpoint 有价值，但必须和 full save 明确区分。
5. P0 应拆成 P0-a/P0-b/P0-c，按成本和收益实施。
6. session-handoff 应继续保持轻量，不引入数据库、向量召回、完整 transcript 捕获或治理 runtime。

下一步最合理的实现顺序：

1. 更新 SKILL.md：防自污染规则。
2. 扩展 `handoff.py check`：占位符、Next Steps、Verification、opening message。
3. 增加 Workspace Identity 模板和状态辅助。
4. 再考虑 Handoff Sufficiency、status 增强和 START_NEXT_SESSION_PROMPT.txt。

---

*整理时间：2026-06-09*
*分析来源：Claude Code 对三个项目的分析、三个隔离子 agent 的会话保存专项分析、Codex 对 session-handoff 当前实现的综合判断。*
