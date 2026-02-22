# ERRORS.md

Command failures, exceptions, and unexpected issues.

Format:
```markdown
## [ERR-YYYYMMDD-XXX] skill_or_command_name

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending | in_progress | resolved | wont_fix
**Area**: frontend | backend | infra | tests | docs | config

### Summary
Brief description of what failed

### Error
```
Actual error message or output
```

### Context
- Command/operation attempted
- Input or parameters used
- Environment details

### Suggested Fix
If identifiable, what might resolve this

### Metadata
- Reproducible: yes | no | unknown
- Related Files: path/to/file
- See Also: ERR-20250110-001

### Resolution (if resolved)
- **Resolved**: ISO-8601 timestamp
- **Commit/PR**: abc123
- **Notes**: What was done
```
