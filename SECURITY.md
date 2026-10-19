# Security

## Reporting a vulnerability

**Do not open a public issue for a security problem.**

Report privately to **<maintainers@fincrime.dev>**, or use GitHub's private
vulnerability reporting on this repository. We acknowledge within 3 business
days and aim to triage within 10.

We will coordinate disclosure with you, with a **90-day window** by default.
We will credit you in the changelog and release notes unless you prefer
anonymity.

## What is in scope

| Class | Examples |
|---|---|
| Validation bypass | A malformed or adversarial artifact that passes `fincrime validate` when it should not |
| Evidence forgery | A reference that resolves to a value the claim does not match, in a way the validator fails to catch |
| Prompt injection into the contract | Text in an evidence artifact that changes the validator's behaviour |
| PII leakage | Case data leaving the process, or appearing in a report that should not contain it |
| Knowledge poisoning | A tampered knowledge record or a pack whose contents do not match its manifest checksum |
| Supply chain | A compromised dependency, a malicious skill, or a poisoned dataset |

## What is out of scope

| Report | Why |
|---|---|
| "The agent gave a wrong answer" | That is a product-quality issue, not a vulnerability. Please open an issue — it is valuable. |
| "The model hallucinated" | Model behaviour is a quality concern, measured by the evaluation suite, not a security boundary. |
| A skill that is missing a guardrail | An enhancement. Open an issue. |
| Denial of service via a hostile artifact | The validator is designed to be total, and we will fix it, but report it as a robustness bug. |

## Security properties of this project

These are **designed properties**, not aspirations, and each is enforced in CI.

### The core has no network capability

`fincrime-core` has **zero required runtime dependencies** and the CI suite
runs with **sockets disabled**
([ADR-0002](docs/adr/0002-zero-dependency-core.md)). A validator that cannot
open a socket cannot exfiltrate case data, regardless of intent. This is
checkable, not a promise.

### The project never collects customer data

There is no ingestion path from customer data anywhere in this repository. All
datasets are synthetic and generated from a recorded seed. The PII scanner
(`scripts/check_no_pii.py`) is a merge gate.

### Safety constraints are structural, not instructional

A safeguard a model can choose to omit is not a safeguard. Every non-filing
notice, human-approval marker, and jurisdiction statement is a **tool-generated
artifact field**, not model-authored prose
([ADR-0009](docs/adr/0009-tool-generated-safety-notices.md)). The agent cannot
remove what it never writes.

### No capability to file, freeze, close, or decline

There is no code path in this repository that constructs, serializes, transmits,
or queues a regulatory filing artifact, or that takes a customer-affecting
action. The absence of the capability is the control.

### The closed world

An artifact can only cite evidence that was in the supplied evidence set. A
reference to anything else is unresolvable by construction, and a claim that
depends on it cannot validate.

## Threat model

The full threat model is in `docs/threat-model.md` (Phase 1). The primary
adversaries considered are:

1. **A malicious or compromised skill** in the ecosystem. Mitigated by the
   contract, the manifest schema, and the fact that a skill cannot relax a
   guardrail.
2. **Prompt injection through evidence.** A transaction memo, a customer
   document, or a web page containing instructions aimed at the agent.
   Mitigated by the closed world and the typed-claim structure; the evidence
   boundary is the main defence.
3. **A supply-chain compromise of a knowledge pack.** Mitigated by pack
   immutability, manifest checksums, and the requirement that every record
   carries sources and a named maintainer.
4. **Deliberate misuse** — using the skills to build a system that makes
   accusations about people without human review. Mitigated by the structural
   constraints, and by the project's stated position that these are
   risk-reduction tools and not compliance tools.

## Out of scope by design

This project does **not** provide compliance assurance. It produces the
artifacts that a model's own risk-management function needs — validation
evidence, benchmark baselines, outcome analysis on a defined population,
decision rationales, and audit trails. Regulatory compliance remains the
responsibility of the deploying institution.
