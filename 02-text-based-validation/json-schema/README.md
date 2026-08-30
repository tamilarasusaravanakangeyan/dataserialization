# JSON Schema Code Example (Python)

Validating JSON payloads against a schema — the pattern you'd run at the edge
of a REST API, in a CI config check, or inside a form backend.

## Files

| File | Purpose |
|---|---|
| [user.schema.json](user.schema.json) | The schema — types, constraints, nested `$defs`, enum, `if/then/else` |
| [validate_demo.py](validate_demo.py) | Validates one good payload and five differently-broken ones |
| [requirements.txt](requirements.txt) | `jsonschema` with format validators (email, date-time) |

## The JSON Schema Workflow

```text
 user.schema.json ──(loaded at runtime)──► validator ──► accept / reject + errors
        │
        └── no codegen, no compile step: the payload is still plain JSON.
            The schema is a gate, not a wire format.
```

Contrast with Protobuf: nothing about the payload changes. JSON Schema doesn't
make data smaller or faster — it makes it **trustworthy at the boundary** while
staying human-readable.

## Run It

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

```bash
python validate_demo.py
```

Expected output:

```text
✅ VALID  well-formed admin user

❌ INVALID  wrong types and missing required field
    at (root)               'email' is a required property
    at id                   '42' is not of type 'integer'

❌ INVALID  constraint violations
    at email                'not-an-email' is not a 'email'
    at id                   0 is less than the minimum of 1
    at role                 'superuser' is not one of ['viewer', 'editor', 'admin']
    at username             'Tamil Arasu!' does not match '^[a-z0-9_]+$'

❌ INVALID  nested object rules
    at address/city         '' should be non-empty
    at address/country      'India' does not match '^[A-Z]{2}$'

❌ INVALID  conditional rule: admin_note on a non-admin
    at (root)               {...} should not be valid under {'required': ['admin_note']}

❌ INVALID  typo caught by additionalProperties:false
    at (root)               Additional properties are not allowed ('usernme' was unexpected)
```

## What the Demo Teaches

1. **Structural validation** — required properties, type checks, and clear
   per-field error paths you can return straight to an API client.
2. **Constraints beyond types** — `minimum`, `pattern`, `enum`, `format`
   (email/date-time), array `uniqueItems`/`maxItems`.
3. **Reusable sub-schemas** — the address lives in `$defs` and is referenced
   with `$ref`, exactly how larger schema suites are composed.
4. **Conditional logic** — `if/then/else` expresses "only admins may carry an
   `admin_note`," a rule type-systems alone can't state.
5. **Typo defense** — `additionalProperties: false` turns a silently ignored
   misspelled key into a hard validation error.

## Where JSON Schema Fits (from the decision map)

- **Processing pattern:** human-facing request/response — public REST APIs,
  webhooks, config files, form backends. Not a fit for high-volume internal
  streaming (payloads stay as text JSON; use a binary format there).
- **Schema volatility:** friendly to frequent change — adding optional
  properties never breaks existing valid documents, and validation catches
  breaking drift at the boundary instead of deep inside your system.
