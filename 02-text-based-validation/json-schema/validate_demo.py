"""JSON Schema demo: validate good and bad payloads against user.schema.json.

Setup (once):
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt

Run:
    python validate_demo.py
"""

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA = json.loads(Path(__file__).with_name("user.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def check(label: str, payload: dict) -> None:
    errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: list(e.path))
    verdict = "✅ VALID" if not errors else "❌ INVALID"
    print(f"\n{verdict}  {label}")
    for err in errors:
        location = "/".join(str(p) for p in err.path) or "(root)"
        print(f"    at {location:<20} {err.message}")


def main() -> None:
    valid_user = {
        "id": 42,
        "username": "tamil_arasu",
        "email": "tamilarasu.saravana@gmail.com",
        "active": True,
        "role": "admin",
        "address": {"street": "1 Marina Beach Rd", "city": "Chennai", "country": "IN", "zip": "600001"},
        "tags": ["engineer", "learner"],
        "created_at": "2026-08-30T09:00:00Z",
        "admin_note": "granted full access",
    }
    check("well-formed admin user", valid_user)

    # Each payload below violates a different kind of constraint.
    check("wrong types and missing required field", {
        "id": "42",                      # string, schema wants integer
        "username": "tamil_arasu",
        "role": "admin",                 # 'email' (required) is missing
    })

    check("constraint violations", {
        "id": 0,                          # minimum is 1
        "username": "Tamil Arasu!",       # violates ^[a-z0-9_]+$
        "email": "not-an-email",          # fails format: email
        "role": "superuser",              # not in the enum
    })

    check("nested object rules", {
        "id": 7,
        "username": "priya",
        "email": "priya@example.com",
        "role": "viewer",
        "address": {"city": "", "country": "India"},  # empty city, country not ISO-2
    })

    check("conditional rule: admin_note on a non-admin", {
        "id": 8,
        "username": "arjun",
        "email": "arjun@example.com",
        "role": "viewer",
        "admin_note": "should not be here",  # if/then/else forbids this
    })

    check("typo caught by additionalProperties:false", {
        "id": 9,
        "username": "kavya",
        "email": "kavya@example.com",
        "role": "editor",
        "usernme": "kavya",               # misspelled key is rejected, not ignored
    })


if __name__ == "__main__":
    main()
