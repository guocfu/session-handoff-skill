# Session Handoff Skill

Lightweight, agent-agnostic session handoff workflow for preserving actionable project state across AI agents, tools, models, and conversations.

English is the default documentation language. A Simplified Chinese guide is included below.

Handoff files keep stable English headings for parser and cross-agent consistency. The content under those headings should follow the active conversation or user's language unless the repository has a stronger convention. Commands, paths, code identifiers, and quoted errors should stay in their original spelling/language.

- [English](#english)
- [中文](#中文)

## English

### What It Is

`session-handoff` is a small workflow and helper script for AI-assisted project continuity.

It helps an agent save, validate, archive, and resume concise project state through a project-level `SESSION_HANDOFF.md` file. The goal is to make the next agent, model, provider, or conversation able to continue from the real current state without relying on hidden chat history.

This project started as a Codex skill, but the handoff format is intentionally simple enough for any local coding agent that can read and write project files.

### Why Use It

AI agents often lose context when you:

- Start a new conversation.
- Switch models or providers.
- Move between CLI and editor integrations.
- Hand work from one agent to another.
- Return to a project after a break.

`session-handoff` keeps the durable, actionable part of the session in the project, where future agents can inspect it.

### What It Is Not

This is not:

- A transcript merger.
- A long-term memory database.
- An automatic recall engine.
- A full agent runtime.
- A project governance framework.
- A replacement for tests, source control, or documentation.

It is deliberately small: one handoff file, one workflow, and one helper script.

### Repository Contents

```text
SKILL.md
agents/openai.yaml
scripts/handoff.py
```

- `SKILL.md`: The agent-facing workflow for saving, resuming, and validating handoffs.
- `agents/openai.yaml`: Skill metadata for OpenAI/Codex-style skill installation.
- `scripts/handoff.py`: Deterministic helper for status, archive, template generation, and validation.

### Install For Codex

Codex skills are discovered from skill directories that contain a `SKILL.md` file. You can install this skill globally for your user or locally inside a repository.

User-wide install:

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/guocfu/session-handoff-skill.git ~/.agents/skills/session-handoff
```

Repository-scoped install:

```bash
mkdir -p .agents/skills
git clone https://github.com/guocfu/session-handoff-skill.git .agents/skills/session-handoff
```

Windows PowerShell user-wide install:

```powershell
New-Item -ItemType Directory -Force "$HOME\.agents\skills"
git clone https://github.com/guocfu/session-handoff-skill.git "$HOME\.agents\skills\session-handoff"
```

Restart Codex if the skill does not appear immediately. Invoke it explicitly with:

```text
Use $session-handoff to read SESSION_HANDOFF.md in read-only mode.
```

To save the current session:

```text
Use $session-handoff to save the current session handoff.
```

### Use With Claude Code

Claude Code also supports `SKILL.md` based skills. Install this repository as a Claude Code skill under `~/.claude/skills/` for all projects, or under `.claude/skills/` for one project.

User-wide setup:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/guocfu/session-handoff-skill.git ~/.claude/skills/session-handoff
```

Project-scoped setup:

```bash
mkdir -p .claude/skills
git clone https://github.com/guocfu/session-handoff-skill.git .claude/skills/session-handoff
```

Windows PowerShell user-wide setup:

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills"
git clone https://github.com/guocfu/session-handoff-skill.git "$HOME\.claude\skills\session-handoff"
```

Run Claude Code from the project directory:

```bash
claude
```

Invoke the skill directly:

```text
/session-handoff read SESSION_HANDOFF.md in read-only mode.
```

```text
/session-handoff read SESSION_HANDOFF.md, verify local state, then continue from Next Steps.
```

Claude Code can also select the skill automatically when your request matches the skill description. If Claude Code does not pick up a newly created skills directory, restart Claude Code.

Optional project policy in `CLAUDE.md`:

```md
## Session Handoff

When I ask to save, read, resume, or continue a session handoff, use the `session-handoff` skill.
Default to read-only mode after reading SESSION_HANDOFF.md unless I explicitly ask you to continue or execute next steps.
```

### Handoff File

By default, the workflow stores state in:

```text
SESSION_HANDOFF.md
```

The file uses stable headings so future agents can quickly scan the current goal, completed work, workspace state, key files, decisions, verification, open questions, next steps, and notes.

The headings stay in English by design. Write the section content in the active conversation or user's language unless repository conventions clearly require another language, and keep commands, paths, code identifiers, and quoted errors verbatim.

The default resume behavior is **read-only**. A new agent should read the handoff, restate the current state, and recommend the next action without editing files. Continuing execution requires an explicit continue instruction.

The exact handoff template lives in [SKILL.md](SKILL.md) and can be printed with `python scripts/handoff.py template --root <project-root>`. Keeping the template source there avoids README and agent instructions drifting apart.

Historical decisions or logs should be compressed into current conclusions before they enter the handoff. Keep only decisions, risks, verification results, or next steps that still affect the next session; leave full history in archives, commits, or separate project notes.

### Helper Commands

Run commands from the skill directory, or point to the script by path.

The helper uses Python 3.9+ and no third-party packages.

Show whether a handoff exists:

```bash
python scripts/handoff.py status --root <project-root>
```

Archive the current handoff before replacing it:

```bash
python scripts/handoff.py archive --root <project-root>
```

By default, `archive` keeps the latest 20 archived copies for the current handoff filename. Use `--keep <n>` to change the limit, or `--keep 0` to disable cleanup.

Print a blank handoff template:

```bash
python scripts/handoff.py template --root <project-root>
```

Write a blank handoff template:

```bash
python scripts/handoff.py template --root <project-root> --write
```

Validate required headings and scan for likely secrets:

```bash
python scripts/handoff.py check --root <project-root>
```

`check` also reports unresolved template placeholders, incomplete required sections, empty `Next Steps`, and empty `Verification`. A blank template is a starter file, not a ready handoff.

`check` exit codes are: `0` OK, `1` missing handoff file, `2` validation problems.

Run the test suite:

```bash
python -m unittest discover -s tests
```

### Agent Workflow

#### Save Or Update

1. Inspect the current project state, including changed files and verification results when available.
2. Archive the existing `SESSION_HANDOFF.md`, if present.
3. Replace `SESSION_HANDOFF.md` with a concise, current handoff.
4. Run the helper check.
5. Fix missing sections, unresolved placeholders, incomplete next steps, incomplete verification, or possible secrets before ending the session.

#### Resume

Default to read-only mode unless the user explicitly asks the agent to continue, implement, proceed, or execute the next steps.

Read-only resume:

1. Read `SESSION_HANDOFF.md`.
2. Inspect local state only as needed to verify stale assumptions.
3. Restate the current goal, current state, risks/blockers, verification status, and recommended next action.
4. Do not edit files or run mutating commands.

Continue resume:

1. Read `SESSION_HANDOFF.md`.
2. Verify stale assumptions with local inspection.
3. Restate the current goal and planned first action.
4. Continue from the listed next step unless the user changes direction.

### Security

Do not put credentials in handoff files.

The validation helper scans for common secret-like patterns, including API keys, bearer tokens, private keys, passwords, and cookies. This check is useful, but it is not a complete secret scanner. Agents and users should still avoid writing raw credentials into project files.

Archived handoff files are ignored by this repository's `.gitignore` through `.codex/handoffs/`. If you use a different archive directory, add it to your own ignore rules before saving sensitive project context.

### Relationship To Larger Handoff Systems

Some projects need a full continuity runtime with project indexes, session logs, rule packs, upgrade tooling, and health checks.

`session-handoff` is for the smaller case: you want a low-friction handoff file that any agent can read and maintain without installing a full framework into every project.

### Documentation Sources

- Codex skills: https://developers.openai.com/codex/skills
- Claude Code skills: https://docs.anthropic.com/en/docs/claude-code/skills
- Claude Code memory and `CLAUDE.md`: https://docs.anthropic.com/en/docs/claude-code/memory

### License

MIT License. See [LICENSE](LICENSE).

## 中文

### 这是什么

`session-handoff` 是一个轻量、通用、跨 agent 的会话交接工作流。

它通过项目级 `SESSION_HANDOFF.md` 保存当前可继续执行的项目状态，让下一位 agent、下一个模型、下一个提供商或下一轮对话可以从真实状态继续，而不是依赖隐藏聊天历史。

这个项目最初是 Codex skill，但 handoff 文件格式足够简单，任何能读写本地项目文件的 coding agent 都可以使用。

### 为什么使用

当你遇到下面情况时，agent 很容易丢失上下文：

- 开启新对话。
- 切换模型或代理提供商。
- 在 CLI 和编辑器插件之间切换。
- 把工作从一个 agent 交给另一个 agent。
- 隔了一段时间后回到项目。

`session-handoff` 把真正需要延续的状态写进项目文件里，下一位 agent 可以直接读取。

文档默认语言是英文，并在本 README 中提供简体中文说明。handoff 文件本身使用固定英文标题，便于脚本和不同 agent 稳定解析；标题下面的正文应跟随当前会话或用户语言，除非仓库有更强的语言约定。命令、路径、代码标识符和引用的错误信息保持原文。

### 它不是什么

它不是：

- 聊天记录合并器。
- 长期记忆数据库。
- 自动 recall 引擎。
- 完整 agent runtime。
- 项目治理框架。
- 测试、Git 或项目文档的替代品。

它刻意保持很小：一个 handoff 文件、一个工作流、一个辅助脚本。

### 在 Codex 中安装

Codex skill 是包含 `SKILL.md` 的目录。你可以全局安装到用户目录，也可以安装到某个仓库中。

用户级安装：

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/guocfu/session-handoff-skill.git ~/.agents/skills/session-handoff
```

仓库级安装：

```bash
mkdir -p .agents/skills
git clone https://github.com/guocfu/session-handoff-skill.git .agents/skills/session-handoff
```

Windows PowerShell 用户级安装：

```powershell
New-Item -ItemType Directory -Force "$HOME\.agents\skills"
git clone https://github.com/guocfu/session-handoff-skill.git "$HOME\.agents\skills\session-handoff"
```

如果 Codex 没有立刻显示该 skill，重启 Codex。

只读读取 handoff：

```text
Use $session-handoff to read SESSION_HANDOFF.md in read-only mode.
```

保存当前会话：

```text
Use $session-handoff to save the current session handoff.
```

### 在 Claude Code 中使用

Claude Code 也支持基于 `SKILL.md` 的 skills。你可以安装到用户级 `~/.claude/skills/`，也可以安装到单个项目的 `.claude/skills/`。

用户级安装：

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/guocfu/session-handoff-skill.git ~/.claude/skills/session-handoff
```

仓库级安装：

```bash
mkdir -p .claude/skills
git clone https://github.com/guocfu/session-handoff-skill.git .claude/skills/session-handoff
```

Windows PowerShell 用户级安装：

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills"
git clone https://github.com/guocfu/session-handoff-skill.git "$HOME\.claude\skills\session-handoff"
```

在项目目录启动 Claude Code：

```bash
claude
```

直接调用 skill：

```text
/session-handoff read SESSION_HANDOFF.md in read-only mode.
```

```text
/session-handoff read SESSION_HANDOFF.md, verify local state, then continue from Next Steps.
```

Claude Code 也可以在请求匹配 skill 描述时自动选择该 skill。如果 Claude Code 没有识别新建的 skills 目录，重启 Claude Code。

可选的项目 `CLAUDE.md` 团队规则：

```md
## Session Handoff

When I ask to save, read, resume, or continue a session handoff, use the `session-handoff` skill.
Default to read-only mode after reading SESSION_HANDOFF.md unless I explicitly ask you to continue or execute next steps.
```

### 默认恢复模式

默认是**只读恢复**。新的 agent 读取 `SESSION_HANDOFF.md` 后，只复述当前目标、当前状态、风险/阻塞、验证状态和建议下一步，不修改文件。

只有用户明确要求“继续执行”“continue”“按 Next Steps 做”时，才进入继续执行模式。

### 辅助命令

辅助脚本使用 Python 3.9+，不需要第三方依赖。

查看 handoff 状态：

```bash
python scripts/handoff.py status --root <project-root>
```

归档当前 handoff：

```bash
python scripts/handoff.py archive --root <project-root>
```

默认保留当前 handoff 文件最近 20 个归档副本。可以用 `--keep <n>` 调整数量，或用 `--keep 0` 关闭自动清理。

打印模板：

```bash
python scripts/handoff.py template --root <project-root>
```

写入空模板：

```bash
python scripts/handoff.py template --root <project-root> --write
```

校验必备标题并扫描疑似密钥：

```bash
python scripts/handoff.py check --root <project-root>
```

`check` 也会报告未替换模板占位符、未完成的必填 section、空的 `Next Steps` 和空的 `Verification`。空模板只是起点，不是一份可交接的 handoff。

`check` 退出码：`0` 表示通过，`1` 表示缺少 handoff 文件，`2` 表示存在校验问题。

运行测试：

```bash
python -m unittest discover -s tests
```

### 安全

不要把 API key、token、cookie、密码、私钥或原始凭据写进 handoff 文件。

脚本会扫描常见 secret 形态，但它不是完整的 secret scanner。用户和 agent 仍然应避免把任何凭据写入项目文件。

本仓库的 `.gitignore` 已忽略 `.codex/handoffs/` 归档目录。如果你使用其他归档目录，应先把它加入自己的 ignore 规则，避免把敏感项目上下文提交进仓库。

历史决策或日志进入 handoff 前应先压缩成当前结论。只保留仍影响下个会话的决策、风险、验证结果或下一步；完整历史应留在归档、commit 或单独项目笔记中。

### 和大型记忆系统的关系

如果你需要长期记忆、自动 recall、向量检索、多用户隔离、session hooks 或项目治理 runtime，可以使用更大的系统。

`session-handoff` 面向更小的场景：你只需要一份低摩擦、可审阅、任何 agent 都能读取和维护的交接文件。

### 许可证

MIT License。见 [LICENSE](LICENSE)。
