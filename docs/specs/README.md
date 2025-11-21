# Software Specifications

This directory contains software specifications and technical documentation, largely created by Large Language Models (LLMs) to guide development and maintain project context.

## Directory layout

- `proposed/`: New or in-discussion specs start here (including in-progress drafts).
- `accepted/`: Specs that have been approved and/or implemented; move documents here once decisions are made.
- `obsolete/`: Superseded or abandoned specs; add a short note in the document about why it was moved.
- `_TEMPLATE.md` and this README stay at the directory root for easy copying and reference.

When a spec changes status, move the file to the corresponding subfolder in the same PR that updates its `Status` field and content.

## Marking a spec done

- Set any remaining tasks in the backlog to their final state (e.g., ✅ done or ⏸️ deferred) and refresh status notes/lessons to reflect completion.
- Update the document's status section (`Latest completed task`/`Next up` or similar) so it no longer implies active work.
- Move the file from `proposed/` to `accepted/` (or from `accepted/` to `obsolete/` if being retired) in the same change.
- Keep the filename unchanged when moving; only adjust the directory.
- Add a status banner near the top of the document using the established emoji style (e.g., `**Status:** ✅ Done (...)` for completed specs).

## Purpose

These specifications serve as:

- **Design blueprints** for features and components
- **Context repositories** for AI-assisted development
- **Knowledge checkpoints** for incremental progress tracking
- **Communication artifacts** between human developers and AI agents

## Document Naming Scheme

To maintain organization and enable chronological sorting, follow this naming convention for specification documents:

### Format

```plaintext
YYYY-MM-DD_descriptive-name.md
```

- **Date prefix**: ISO 8601 format (`YYYY-MM-DD`) ensures alphabetical sorting equals chronological sorting
- **Underscore separator**: Separates date from description
- **Descriptive name**: Lowercase, hyphen-separated, meaningful description
- **Extension**: `.md` for Markdown documents

### Examples

- [2025-11-19_github-actions-ci.md](accepted/2025-11-19_github-actions-ci.md) - Full CI bootstrap with matrices and guardrails; good pattern for automation specs.
- [2025-11-19_python-package-structure.md](accepted/2025-11-19_python-package-structure.md) - Cross-language package/API layout; shows how to capture public surface and type expectations.
- [2025-11-19_pyo3-integration-plan.md](accepted/2025-11-19_pyo3-integration-plan.md) - Rust/Python binding strategy; example of dependency and tooling alignment details.
- [2025-11-19_rust-mvp-algorithm.md](accepted/2025-11-19_rust-mvp-algorithm.md) - Kernel-level algorithm spec with risks/backlog; blueprint for core logic work.
- [2025-11-20_witness-points-hausdorff.md](accepted/2025-11-20_witness-points-hausdorff.md) - Feature spec covering behavior, tests, and follow-on perf work; good model for end-to-end additions.

### Benefits

- **Sortable**: Files automatically sort chronologically in file explorers
- **Traceable**: Easy to see when a specification was created
- **Discoverable**: Descriptive names make content obvious at a glance
- **Version-friendly**: Date prefix prevents name collisions for evolving specs

## Specification Template

To bootstrap new documents quickly, copy [`_TEMPLATE.md`](_TEMPLATE.md) into `proposed/` with a dated filename that matches
the naming scheme above, then replace the placeholders with project-specific details. The template mirrors the structure of
our existing plans, including purpose, constraints, backlog, risk tracking, and a space for lessons learned.

## Intentional Context Compaction

When working with LLM agents on complex tasks, we recommend a practice called **intentional context compaction**. This approach significantly improves outcomes by:

### Key Principles

1. **Incremental Steps**: Break down large tasks into smaller, manageable steps

   - Request the agent to complete one logical unit of work at a time
   - Verify each step before proceeding to the next
   - Prevent context drift and accumulating errors

2. **Regular Checkpointing**: Have the agent periodically save its progress

   - Document what has been accomplished
   - Record key decisions and rationale
   - Note any challenges or blockers encountered

3. **Lessons Learned**: Capture insights for future agents
   - Summarize what worked well
   - Identify patterns that should be followed
   - Document pitfalls to avoid
   - Record useful techniques or approaches

### Benefits

- **Continuity**: New agents can quickly understand project state
- **Efficiency**: Reduces redundant work and context rebuilding
- **Quality**: Enables review and course-correction at each step
- **Knowledge Transfer**: Preserves institutional knowledge across sessions

### Example Workflow

```plaintext
1. Agent completes initial research → checkpoint created
2. Agent designs architecture → checkpoint updated with design decisions
3. Agent implements component A → checkpoint with implementation notes
4. Agent tests component A → checkpoint with test results and lessons
5. Next agent reviews checkpoints → continues with component B
```

By practicing intentional context compaction, you create a self-documenting development process that scales across multiple sessions and agent interactions.
