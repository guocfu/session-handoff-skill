---
name: session-handoff
description: Save, update, archive, and resume concise project handoff notes across AI agents, tools, models, providers, editor integrations, and conversations. Use when Codex needs to create or update SESSION_HANDOFF.md, read a previous handoff, resume in read-only mode, continue from a handoff, summarize progress before switching sessions/providers, or prepare context for another agent.
---

# Session Handoff

## Overview

Use this skill to preserve only the actionable project state needed to continue work in a new session. Store the handoff in the project as `SESSION_HANDOFF.md` by default.

This skill is not a transcript merger, long-term memory database, automatic recall engine, or full agent runtime. Keep the file short, current, and useful for the next agent.

## Workflow

### Save Or Update

1. Inspect the current conversation state and, when useful, local project state such as `git status`, changed files, relevant plans, and recent verification results.
2. If `SESSION_HANDOFF.md` already exists, archive it first with:

   ```bash
   python <skill-dir>/scripts/handoff.py archive --root .
   ```

3. Write a complete replacement `SESSION_HANDOFF.md` using the template below.
4. Run:

   ```bash
   python <skill-dir>/scripts/handoff.py check --root .
   ```

5. If the check reports likely secrets or missing required sections, fix the file before finishing.

### Resume

Default to **Read Only** unless the user explicitly asks to continue, implement, proceed, or execute next steps.

#### Read Only

1. Read `SESSION_HANDOFF.md`.
2. Inspect local state only as needed to verify stale assumptions, such as branch, changed files, and relevant file existence.
3. Restate the current goal, current state, risks/blockers, verification status, and recommended next action.
4. Do not edit files or run mutating commands.

#### Continue

1. Read `SESSION_HANDOFF.md`.
2. Verify stale assumptions with local inspection, especially changed files, test status, branch state, and key files.
3. Briefly restate the current goal and planned first action before changing anything.
4. Continue from `## Next Steps` unless the user's latest instruction changes direction.

### Status

Use this to inspect whether a handoff exists and when it was last updated:

```bash
python <skill-dir>/scripts/handoff.py status --root .
```

## Handoff Template

Use these exact headings so future sessions can parse and scan the file consistently:

```md
# Session Handoff

Updated: YYYY-MM-DD HH:MM local time
Project: <repo or project name>
Branch: <branch name or unknown>

## Current Goal
- <one to three bullets describing the active objective>

## Completed
- <what is done and safe to rely on>

## Current State
- <workspace state, partial changes, active files, important constraints>

## Key Files
- `<path>`: <why it matters>

## Decisions
- <decision and rationale>

## Verification
- <commands/checks run and results>
- <checks not run and why>

## Open Questions
- <unknowns or decisions still needed>

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
- <user preferences, gotchas, provider/model context, or agent instructions>
```

## Writing Rules

- Keep the handoff under about 150 lines unless the task genuinely needs more.
- Prefer facts over narrative. Do not paste full command logs or full chat transcripts.
- Use concrete file paths and exact commands where they help continuation.
- Record failed or skipped verification honestly.
- Keep current state separate from historical evidence. Do not let old logs, old validation, or long-term decisions masquerade as the next action.
- Use `Next Session Opening Message` to separate safe read-only resume from explicit continue-and-execute resume.
- Do not include API keys, tokens, cookies, passwords, private keys, or raw credentials.
- If a section has nothing to say, write `- None`.
- Use the user's language unless the repository conventions clearly require another language.
- Overwrite `SESSION_HANDOFF.md` on each save; rely on `.codex/handoffs/` archives for older versions.

## Tool Notes

`scripts/handoff.py` only handles deterministic support tasks: status, archive, template printing, and safety checks. The agent still writes the actual project summary because it has the task context.
