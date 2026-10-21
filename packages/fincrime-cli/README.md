# fincrime-cli

The `fincrime` command: scaffold a skill package, validate one, export a
policy set, evaluate a policy set against an artifact, and check a knowledge
pack's integrity and staleness.

```bash
pip install -e "packages/fincrime-cli"

fincrime new skill my-skill --outdir skills
fincrime validate skills/my-skill
fincrime policy check --set policies/default/policy-set.json \
    --artifact examples/01-alert-triage-structuring/artifact.json
fincrime knowledge check --pack knowledge/packs/core-2026-10 --as-of 2026-10-21
```

## Why it exists

A skill is a contract, and a contract nobody checks is a document. The CLI
is how a contributor checks their own work before anybody else does: it
validates the sidecar against `contracts/skill-manifest.schema.json`, checks
that the body and the sidecar agree, resolves every policy id the manifest
names, and enforces the case-mix requirements the suite declares.

## Zero dependencies, on purpose

The CLI uses the standard library only. It reads YAML with an in-house
parser restricted to a documented subset (`fincrime_cli.yamlite`), because
`yaml` is on the forbidden list in `scripts/check_imports.py`: a dependency
that can open a socket can exfiltrate a case file. The subset is verified
against PyYAML by a parity test, in the same spirit as the JSON Schema
parity check.

The CLI is a development and CI tool. It is not inside the trust boundary
that ADR-0002 protects; the validator in `fincrime-core` is.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Clean. |
| 1 | Findings were reported. |
| 2 | Usage error. |

## Documentation

The authoring guide is [`docs/skill-authoring.md`](../../docs/skill-authoring.md).
