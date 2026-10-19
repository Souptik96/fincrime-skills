# ADR-0008: v1 Scope — Six Skills, One Jurisdiction, Part V Only

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** core maintainers
- **Supersedes:** none

## Context

The project could launch with 30 skills across AML, KYC, sanctions, and fraud
across multiple jurisdictions, or with a small number of excellent ones. The
blueprint's analysis was unambiguous: the binding constraint is the **evaluation
corpus**, not the skill count. Each skill needs ≥ 60 cases, of which ≥ 40% must
be benign, adversarial, missing-data, or contradictory — roughly 360 hand-built,
expert-reviewed cases for six skills. Thirty skills would require ~1,800 cases
and three cohorts of domain maintainers, none of which exist.

Multiple jurisdictions multiply this further and add a legal-review burden that a
volunteer project cannot sustain responsibly.

There is also a scope limit inside the highest-value skill. FinCEN SAR filing has
structured electronic fields (Parts I–IV) and an unstructured narrative
(Part V). The narrative is where hallucination actually occurs; the structured
fields are mechanically mapped and carry low risk.

## Decision

**v1 ships exactly six skills, one jurisdiction (US), and Part V only for SAR.**

| Skill | Risk | Cohort |
|---|---|---|
| `investigation-qa` | Low | 1 — low domain risk |
| `case-summarize` | Low-med | 1 — low domain risk |
| `evidence-request` | Low | 1 — low domain risk |
| `alert-triage` | Medium | 2 — high domain risk |
| `sar-narrative-draft` | High | 2 — high domain risk |
| `sanctions-alert` | High | 2 — high domain risk |

**Jurisdiction:** every knowledge record and skill manifest carries
`jurisdictions: ["US"]`. No "global" regulatory record is permitted.

**SAR scope:** `sar-narrative-draft` produces the **Part V narrative** and
pre-populates mapped structured fields. It **must not** construct, serialize, or
validate an electronic filing artifact (e.g. a BSA E-Filing batch `.xml`), and no
code path in the repository emits one.

**Cohort split (a sequencing rule, not a scope reduction):**
- **Cohort 1** — `investigation-qa`, `case-summarize`, `evidence-request`. These
  concern evidence linking, schema validation, chronology, and formatting. They are
  buildable and evaluable by applied AI engineers using public FinCEN guidance.
- **Cohort 2** — `alert-triage`, `sar-narrative-draft`, `sanctions-alert`. These
  require real-world grounding in benign twins and must be reviewed by an FCR/AML
  practitioner.
- **If a domain practitioner cannot be secured by Week 4, v1 ships Cohort 1 plus
  `alert-triage`** (whose typologies are public FATF/FinCEN material) and
  `sar-narrative-draft` and `sanctions-alert` move to v1.1. The fallback reduces
  scope; it never ships Cohort 2 unreviewed.

**The cut rule:** a capability ships when it has (a) a contract, (b) a case suite
with a benign population, (c) a deterministic gate it passes, and (d) a named owner
who can maintain its knowledge. Not when it is written; not when it is
interesting; not when it fills a category in a taxonomy.

## Consequences

**Positive**
- Six skills at 60+ cases each is a corpus a real domain maintainer can sustain
  and a contributor can extend.
- The safety architecture is exercised across low, medium, and high risk
  profiles rather than merely asserted.
- The US-only scope makes the regulatory content dateable, citable, and
  reviewable — the thing the expiry machinery is designed for.
- Part V-only keeps the highest-value SAR capability while removing the
  lowest-value, highest-liability surface (filing artifact construction).

**Negative**
- Non-US users get nothing in v1. `docs/jurisdiction-support.md` must state this
  prominently, and non-US demand is the discovery signal for v1.1.
- The repository will look "narrow" next to a 19-skill vendor pack. The
  conformance report is the answer to that objection, not the skill count.
- Six skills is fewer than the taxonomy's ambition. Deliberate.

**Neutral**
- The taxonomy in the blueprint ranks 35 capabilities; the taxonomy is a roadmap,
  not a v1 manifest.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| 20+ skills at launch | Requires ~1,200 cases and multiple domain maintainer cohorts. Quality collapse. |
| Multi-jurisdiction v1 | Multiplies the corpus and adds a legal-review burden that cannot be sustained. |
| Full SAR filing artifact generation | The lowest-value, highest-liability surface. Excluded permanently. |
| Cohort 2 without a practitioner | Ships unverifiable benign-twin plausibility — exactly the harm the project exists to prevent. |
| An "experimental" tier for unreviewed skills | Creates a path to ship Cohort 2 unreviewed. A skill is either reviewed or not shipped. |
