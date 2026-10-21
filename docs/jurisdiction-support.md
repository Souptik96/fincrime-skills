# Jurisdiction support

A skill that names a jurisdiction without saying what it relies on there has
told a reviewer nothing, and the reviewer is the person who has to defend
the output to a regulator.

This file states, per jurisdiction, what is supported and what is not. It is
deliberately short: the supported content is a list, and the unsupported
content is a list, and everything else is the knowledge pack's job.

## United States

**Supported scope: BSA/AML transaction monitoring, Part V. Nothing else.**

| Area | Status | Note |
|---|---|---|
| Currency transaction reporting thresholds | Supported | The threshold value is a policy input, not a hard-coded number. |
| Structuring and threshold-proximity indicators | Supported | As a *measured pattern*, never as an assertion of intent. |
| Evidence requests and gap recording | Supported | |
| Escalation to a human decision | Supported | |
| SAR filing and drafting | **Not supported** | The project produces no filing, and no artifact that reads as one. A SAR narrative skill is out of scope for v1. |
| Sanctions and OFAC screening | **Not supported** | No sanctions list, no screening, no match handling. |
| Customer risk ratings and scoring | **Not supported** | The project does not produce numeric risk ratings. |
| Detection or monitoring configuration | **Not supported** | Skills structure what an analyst has already found. |
| Cross-border or multi-jurisdiction analysis | **Not supported** | A skill must declare a jurisdiction scope, and this one is the United States. |
| Tax, accounting or legal conclusions | **Not supported** | |

### Regulatory basis

The project's regulatory content lives in the knowledge pack, as dated and
cited records. This file does not restate it, because a restatement is
exactly the staleness trap the pack format exists to avoid: the pack
carries the `as_of`, `review_by` and `expires_at` dates, the citations and
the jurisdiction scope, and the expiry bot keeps it current.

### Adding a jurisdiction

Adding one is not a documentation change. It requires:

1. a knowledge pack for that jurisdiction, with records that carry the
   jurisdiction in their scope;
2. at least one skill whose `metadata.jurisdiction_scope` names it, and
   whose case suite carries cases scoped to it;
3. an entry in this file, stating what is supported and what is not.

Until all three exist, the jurisdiction is not supported, and a skill that
claims it is lies about its scope.
