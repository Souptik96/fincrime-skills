# ADR-0009: Tool-Generated Safety Notices (Non-Strippable Headers)

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** core maintainers
- **Supersedes:** none

## Context

The SAR narrative must carry a non-strippable header:

```text
*** DRAFT DOCUMENT FOR HUMAN COMPLIANCE REVIEW ONLY ***
*** NOT A LEGAL FILING — CONTAINS NO DISPOSITION ***
```

The obvious implementation is to instruct the model to include it. **That does not
work.** A header requested in a prompt is advisory: the model may omit it,
rephrase it, truncate it, or bury it. An instruction is a request, not a control.

A safeguard that the model can choose not to emit is not a safeguard. This applies
beyond the header: the non-filing notice, the human-approval-required marker, the
jurisdiction statement, the stale-knowledge marker, and the "no customer action"
constraint are all *model-authored prose* under the naive design, and all of them
are exactly the things a reader relies on and a model could omit.

The same class of error appears elsewhere: a skill instructed to "never file" is
not prevented from filing if a future adapter exposes a filing tool. The
constraint must be structural.

## Decision

**Safety notices and constraint markers are tool-generated artifact fields, never
model-authored prose.**

1. The contract defines them as required, structured fields (e.g.
   `draft_notice: { text: <exact string>, tool_generated: true }`).
2. `tool_generated: true` is set by the **renderer**, not by the model. The model
   produces the narrative *body*; the composition step inserts the notice.
   **A model cannot remove what it never writes.**
3. The validator rejects any artifact whose notice field does not exactly equal the
   canonical value, or whose `tool_generated` flag is not `true`. Violation code:
   `missing_draft_notice`, severity `error`.
4. Every downstream renderer (MCP tool, exporter, future adapter) **must** re-apply
   the notice. The contract test suite includes a renderer that attempts to emit a
   narrative without it and asserts the output is rejected.
5. **Capabilities are structurally absent, not merely forbidden.** There is no code
   path anywhere in the repository that constructs, serializes, or transmits a
   filing artifact. The absence of the capability is the control; the instruction
   not to use it is a comment.
6. The same principle extends to claims: a `decision` cannot validate without
   `decided_by`, and `human_approval_required` is a required field on
   consequential recommendations. These are contract requirements, not prompt text.

## Consequences

**Positive**
- The non-filing notice survives every path from model output to published
  artifact, including adapters we write later.
- The guarantee is testable: the contract suite asserts rejection of a
  header-less artifact.
- The general principle — *anything a model could omit is not a safeguard* —
  becomes a reusable design rule for the whole project, and a reviewable one.
- A reader can trust the header's presence and exact wording without inspecting
  the prose.

**Negative**
- The renderer becomes load-bearing: it is where notices are applied, so it must be
  correct and it must be tested as carefully as the validator.
- A model that sees the contract must still be told not to emit a competing
  notice in its body; a duplicated or contradictory notice is a lint target
  (`conflicting_draft_notice`).
- The contract is more complex, because notices are first-class fields rather than
  strings embedded in text.

**Neutral**
- The header appears in the rendered output, not in the model's raw output. The
  raw output remains a clean structured artifact. This separation is deliberate.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Instruct the model to include the header | Advisory, not a control. The model can omit it. This is the whole problem. |
| Post-process the model's text to prepend the header | **Close, and it is the implemented mechanism** — but it must be enforced at the *artifact* level (a required contract field), not by string-munging a text field, so that validation and rendering cannot disagree. |
| Validate the header by scanning free text | Fragile: rephrasing, unicode, and whitespace all break it. A structured field with an exact-match check does not. |
| Rely on the skill body ("never file") | A prompt cannot remove a capability. Only the absence of code can. |
| Strip notices in a "clean export" for internal use | Defeats the purpose. Any export carries the notice. If a consumer needs the raw body, they read the `body` field, which never contained the notice. |
