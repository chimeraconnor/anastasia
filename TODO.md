# TODO - Tasks for Anastasia & Mr. Grey

---

## 📋 General Todos

| Priority | Task | Added | Notes |
|----------|------|-------|-------|
| High | Give Anastasia Vercel access | 2026-02-25 | Setup Vercel project access |
| Medium | Set up coordinator pattern for Anastasia | 2026-02-25 | Have Anastasia use subagents for complex tasks |

---

## 💡 Ideas to Consider

### Coordinator Pattern
Instead of doing everything directly, Anastasia could spawn subagents for:
- **Complex coding tasks** — Build features, refactor code
- **PR reviews** — Analyze code, provide feedback
- **Background research** — Independent investigation without blocking main session
- **Parallel work** — Multiple subtasks simultaneously

**Benefits:**
- Anastasia stays responsive for direct questions
- Complex work happens in isolated contexts
- Different models/thinking levels per subagent
- Work continues even if session resets (use cron for persistence)

**Current note:** Anastasia already has access to `sessions_spawn` and can create subagents. The coordinator pattern is about *when* and *how* to use them effectively.

---

**Last Updated:** 2026-02-25
