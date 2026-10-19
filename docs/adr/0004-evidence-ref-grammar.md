# ADR-0004: RFC 6901 Evidence-Reference Grammar

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** core maintainers
- **Supersedes:** none

## Context

The entire evidence-attribution guarantee rests on one thing: a claim's evidence
reference must resolve, deterministically, to a specific value in the supplied
evidence set. If the grammar is ambiguous, "evidence attribution accuracy" is
unmeasurable, and the project's headline metric becomes a matter of interpretation.

Three specific ambiguities had to be closed:

1. **Pointer syntax.** A bespoke syntax would make the project unable to consume
   or be consumed by tools that already speak JSON Pointer.
2. **Whole-item vs. sub-item citation.** A ref that omits a pointer could mean
   "the whole record" or "the list of transactions generally". The second is
   *not* evidence attribution, and it is exactly the failure mode we need to
   exclude.
3. **Range citation.** "These seven transactions" must be seven refs, not one
   range token, otherwise per-item attribution is lost.

## Decision

An `evidence_ref` is an **RFC 6901 URI Fragment Identifier**:

```text
<source_id> "#" <json-pointer>
```

- `source_id` — `[A-Za-z][A-Za-z0-9_-]*:[A-Za-z0-9._:-]+`, resolving to exactly
  one item in the evidence set's source index.
- `#` — exactly one RFC 6901 fragment separator. **Required.** Omitting it is an
  invalid ref, not a whole-item ref.
- `<json-pointer>` — an RFC 6901 JSON Pointer: the empty string (the whole item)
  or a sequence of `/`-prefixed reference tokens, URI-fragment-escaped per
  RFC 6901 §3 (`~0` → `~`, `~1` → `/`; escape order matters).

**No range syntax.** A claim spanning multiple items carries one ref per item.

**Resolution is a total, pure function:** `(evidence_set, ref) → (value | error)`.
It never raises. A malformed or dangling ref is a *result*, not an exception —
because an exception in the validator would be a denial-of-service on exactly the
malformed artifacts we most need to inspect.

**Over-broad citations are rejected.** A pointer resolving to an array of length
> 20 is `over_broad_citation` — citing "the whole transaction list" is not
  evidence attribution.

The canonical machine-readable form is `contracts/evidence-ref-grammar.schema.json`,
encoding the ABNF.

## Consequences

**Positive**
- Evidence attribution is fully deterministic and language-agnostic: any
  implementation of RFC 6901 reproduces our verdicts.
- Tooling that already speaks JSON Pointer can consume our artifacts.
- Dangling refs degrade a claim to `unsupported_claim` rather than crashing the
  validator — the right failure mode for a security-relevant component.

**Negative**
- The strictness (`#` required, no ranges) means a model must emit refs
  precisely. This is a real capability requirement on the model, and the
  `evidence_attribution_accuracy` metric is exactly the measure of it. A model
  that cites loosely is correctly penalized.
- Escaping rules (`~0`/`~1`) are easy to get wrong and require careful test
  coverage.

**Neutral**
- We implement a small RFC 6901 subset resolver (pointer resolution only — no
  patch/merge operations) rather than depending on a library, per ADR-0002.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| A bespoke ref syntax (`txn:8842.amount`) | Not interoperable; no existing tooling understands it. |
| Whole-item refs with an implicit pointer | Creates the "cited the list generally" loophole. |
| Range refs (`txn:8841..txn:8847`) | Loses per-item attribution; encourages one ref for many items. |
| Allowing a ref without `#` | Ambiguous with the whole-item case. |
| XPath | Unnecessarily heavy for JSON; different ecosystem. |
| A database-style locator (`table.column[pk=…]`) | Couples the contract to a storage model the project does not own. |
