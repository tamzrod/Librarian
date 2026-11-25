# Librarian agent instructions

Canonical repository: https://github.com/tamzrod/Librarian
Project identity: Librarian — bounded-collection evidence retrieval and context reconstruction.

## Single command
When the user types `operation cwal` (case-insensitive), read `active_work/OPERATION-CWAL.md` first and execute the current authorized bounded task according to that document. Do not treat the phrase as permission for unrelated work.

## Source of truth
- `active_work/OPERATION-CWAL.md`: current mission, scope, gates, and stop conditions.
- `active_work/CWAL-LOG.md`: decisions, evidence, tests, and handoff notes.
- Repository files and observed test results override guesses or unsupported claims.
- Preserve the README principles: filesystem as source of truth, original artifacts unchanged, extracted evidence traceable, and derived indexes rebuildable.

## Guardrails
Work on the authorized development branch; never silently change `main`. Check branch and working-tree status before editing. Do not merge, release, deploy, delete user data, rewrite branch history, or modify external services unless a later mission explicitly authorizes that action. Never claim gates passed without evidence. Redact secrets and sensitive artifact contents from logs. Stop on ambiguous authority or destructive operation.

## Invocation
In an agent workspace checked out to this repository, the entire user instruction can be just:

```text
operation cwal
```
