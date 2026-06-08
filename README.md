# Session Handoff Skill

Lightweight, agent-agnostic session handoff workflow for preserving actionable project state across AI agents, tools, models, and conversations.

## What It Is

`session-handoff` is a small workflow and helper script for AI-assisted project continuity.

It helps an agent save, validate, archive, and resume concise project state through a project-level `SESSION_HANDOFF.md` file. The goal is to make the next agent, model, provider, or conversation able to continue from the real current state without relying on hidden chat history.

This project started as a Codex skill, but the handoff format is intentionally simple enough for any local coding agent that can read and write project files.

## Why Use It

AI agents often lose context when you:

- Start a new conversation.
- Switch models or providers.
- Move between CLI and editor integrations.
- Hand work from one agent to another.
- Return to a project after a break.

`session-handoff` keeps the durable, actionable part of the session in the repository, where future agents can inspect it.

## What It Is Not

This is not:

- A transcript merger.
- A long-term memory database.
- An automatic recall engine.
- A full agent runtime.
- A project governance framework.
- A replacement for tests, source control, or documentation.

It is deliberately small: one handoff file, one workflow, and one helper script.

## Repository Contents

```text
SKILL.md
agents/openai.yaml
scripts/handoff.py
```

- `SKILL.md`: The agent-facing workflow for saving, resuming, and validating handoffs.
- `agents/openai.yaml`: Skill metadata for OpenAI/Codex-style skill installation.
- `scripts/handoff.py`: Deterministic helper for status, archive, template generation, and validation.

## Handoff File

By default, the workflow stores state in:

```text
SESSION_HANDOFF.md
```

The file uses stable headings so future agents can quickly scan the current goal, completed work, workspace state, key files, decisions, verification, open questions, next steps, and notes.

The default resume behavior is **read-only**. A new agent should read the handoff, restate the current state, and recommend the next action without editing files. Continuing execution requires an explicit continue instruction.

Minimal structure:

```md
# Session Handoff

Updated: YYYY-MM-DD HH:MM local time
Project: <repo or project name>
Branch: <branch name or unknown>

## Current Goal
- <active objective>

## Completed
- <completed work>

## Current State
- <workspace state>

## Key Files
- `<path>`: <why it matters>

## Decisions
- <decision and rationale>

## Verification
- <checks run and results>

## Open Questions
- <unknowns>

## Next Steps
- <ordered next actions>

## Next Session Opening Message

### Read Only
```text
Use session-handoff to read SESSION_HANDOFF.md in read-only mode. Do not modify files or run mutating commands. Restate the current goal, current state, risks/blockers, verification status, and recommended next action.
```

### Continue
```text
Use session-handoff to read SESSION_HANDOFF.md, verify local state, then continue from Next Steps. Before changing files, briefly restate the current goal and planned first action.
```

## Notes For Next Session
- <preferences or gotchas>
```

## Helper Commands

Run commands from the skill directory, or point to the script by path.

Show whether a handoff exists:

```bash
python scripts/handoff.py status --root <project-root>
```

Archive the current handoff before replacing it:

```bash
python scripts/handoff.py archive --root <project-root>
```

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

## Agent Workflow

### Save Or Update

1. Inspect the current project state, including changed files and verification results when available.
2. Archive the existing `SESSION_HANDOFF.md`, if present.
3. Replace `SESSION_HANDOFF.md` with a concise, current handoff.
4. Run the helper check.
5. Fix missing sections or possible secrets before ending the session.

### Resume

Default to read-only mode unless the user explicitly asks the agent to continue, implement, proceed, or execute the next steps.

#### Read Only

1. Read `SESSION_HANDOFF.md`.
2. Inspect local state only as needed to verify stale assumptions.
3. Restate the current goal, current state, risks/blockers, verification status, and recommended next action.
4. Do not edit files or run mutating commands.

#### Continue

1. Read `SESSION_HANDOFF.md`.
2. Verify stale assumptions with local inspection.
3. Restate the current goal and planned first action.
4. Continue from the listed next step unless the user changes direction.

## Security

Do not put credentials in handoff files.

The validation helper scans for common secret-like patterns, including API keys, bearer tokens, private keys, passwords, and cookies. This check is useful, but it is not a complete secret scanner. Agents and users should still avoid writing raw credentials into project files.

## Relationship To Larger Handoff Systems

Some projects need a full continuity runtime with project indexes, session logs, rule packs, upgrade tooling, and health checks.

`session-handoff` is for the smaller case: you want a low-friction handoff file that any agent can read and maintain without installing a full framework into every project.

## License

Add a license before publishing or distributing this project widely.
