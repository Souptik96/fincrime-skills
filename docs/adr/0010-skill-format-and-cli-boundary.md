# ADR-0010 — The skill format and the CLI boundary

- **Status:** Accepted
- **Date:** 2026-10-21
- **Decides:** how a skill is described, who reads it, and where the boundary
  between the engine and the tooling that surrounds it lies.

## Context

Phase 0 froze the artifact contract: what an agent produces, and what makes it
checkable. It did not settle how a *skill* is described, and it could not:
there was no skill format to describe.

Three things have to be true at once.

1. **A skill must be portable.** A skill is installed into somebody else's
   agent host, from a package that contains the skill and nothing else. It
   cannot point at a path inside a repository the reader does not have.
2. **The contract must be checkable before the skill runs.** A contributor
   needs to know that their sidecar is valid, that their policy ids resolve,
   and that their case suite meets the mix, without a reviewer reading it.
3. **The toolchain must stay air-gap-installable.** The core's zero-dependency
   invariant ([ADR-0002](0002-zero-dependency-core.md)) exists because a bank
   deploys this in an environment with no package index. A contributor's
   tooling should not be the part that needs the network.

The sidecar format was YAML, and the core cannot use `yaml`: it is on the
forbidden-imports list, and rightly so, because a package that can open a
socket can exfiltrate a case file.

## Decision

### The format is a body and a sidecar

A skill package is a directory holding `SKILL.md` (frontmatter plus prose)
and `fincrime.skill.yaml` (the machine-readable contract). The sidecar is
**additive**: a host that knows nothing about FinCrime loads `SKILL.md` and
works. The sidecar is what lets a host that does know enforce anything.

The sidecar refers to contracts by **contract id** (`fincrime/finding/1.0.0`),
never by a path. A path does not exist inside a distributed skill package; an
id does.

### The engine stays a library; the command is a separate distribution

`fincrime-core` remains the engine: the validator, the policy evaluator, the
knowledge engine. `fincrime-cli` is a new distribution providing the
`fincrime` command. The CLI depends on the core; the core does not depend on
the CLI, and never will.

The split is deliberate. The core is a trust boundary: it runs inside a bank,
it validates a filing, and it has no business writing files. The CLI is a
development and CI tool: it scaffolds packages, writes exports, and reads
JSON off disk. Mixing them would either give the core a filesystem it does
not need, or make the CLI impossible to install without the engine.

### The YAML subset is parsed in-house, and the subset is written down

`fincrime_cli.yamlite` parses a restricted subset of YAML: block mappings and
sequences, flow sequences, plain and quoted scalars, block scalars, and
comments. Everything else — anchors, aliases, tags, merge keys, complex keys,
multiple documents, tab indentation — is a **hard error**.

The alternative was a dependency, and the alternative was rejected for the
reason the core rejects `yaml`. A parser that guesses is worse than a parser
that refuses: a misparsed sidecar becomes a skill whose contract nobody
checked.

The subset is not implied, it is specified, and it is verified against PyYAML
by a parity test — the same arrangement the JSON Schema subset validator has
with the reference `jsonschema` implementation.

### The policy layer separates enforceable rules from procedural policies

A skill names policy ids. Those ids were one flat namespace, and they were
two different things: rules the engine evaluates by code, and guards the agent
follows and the evaluation suite measures.

They are now separated in the policy set. A control a firm must be able to
defend to a regulator is enforced by code; a control that cannot be evaluated
by code does not belong in the enforceable list, and pretending otherwise
produces a control that does not do what it says. Every id a skill names must
resolve, and a skill may not depend on a control nobody can point at.

### The shipping gate is a property of the suite, not of the checker

The case-mix requirements — sixty cases, forty percent mixed, fifteen percent
with a negative expectation, a benign case per typology — live in the suite
manifest. A suite can be held to a stricter bar, and the bar is visible to
whoever writes the cases.

## Consequences

**Good.** A contributor can author, validate and test a skill from one
document. A distributed skill is self-describing. The toolchain installs
without a package index. The policy a firm is held to is in a file a
regulator can read.

**Bad.** The YAML subset is a second thing to keep correct, and a skill author
who reaches for an unsupported YAML feature gets an error instead of a
result. That is the intended trade: the error names the line.

**Bad.** The engine's contract and the CLI's contract are two artifacts that
have to agree, and the CLI's is checked by the CLI's tests rather than by the
engine's.

**Neutral.** A skill in `draft` status may fail the shipping gate; a skill in
`stable` status may not. The checker knows the difference from the manifest,
so a draft's gate failures are warnings. A draft that looks finished is a
draft nobody finished.

## Alternatives rejected

- **A YAML dependency in the CLI.** Simpler, and it would have worked. But
  the toolchain would then need a package index, and the air-gap story would
  have a hole in it at exactly the wrong place.
- **JSON for the sidecar.** No parser, no subset, no drift. Rejected because
  the sidecar is read and edited by humans, and because the format was
  published in the reference skill.
- **One distribution instead of two.** Fewer moving parts, one `pip install`.
  Rejected because it gives the engine a filesystem it must not have, and
  because Phase 6's `fincrime` command grows subcommands that are not engine
  work.
- **A `POL-` id namespace with no distinction between the two kinds of
  policy.** Simpler for the author. Rejected because a firm reading its
  control list must be able to tell which controls are enforced by code and
  which are merely instructions, and a single flat list cannot say that.
