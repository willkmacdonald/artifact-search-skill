Load project context and confirm understanding before starting work.

## Step 1: Load Context Files
Read these files (skip any that don't exist):
- .claude/CLAUDE.md (project rules)
- current-sprint.md (active work)
- docs/specs/implementation-plan.md (full migration plan)
- docs/specs/backend-design.md (backend architecture)
- docs/specs/frontend-design.md (frontend architecture)

## Step 2: Summarize Understanding
After reading, state:

**Sprint Focus**: [Current sprint goal]

**Active Tasks**: [List tasks with status]

**Working On**: [Which specific task we'll tackle]

**Code Goes In**: [Specific files/modules for this task]

**Constraints**:
- Business logic → src/ only
- Tests → only call src/ functions, no feature implementation
- Frozen decisions that apply to this task

**Blockers/Decisions Needed**: [Any unclear items]

## Step 3: Confirm
Ask: "Does this match your understanding? Which task should we start with?"

Wait for my response before writing any code.
