# 2. Text-Based Validation Formats (Human Readability)

These formats keep the **payload as human-readable text** (JSON or XML) and
layer a **schema on top as validation rules**. The schema doesn't change how
bytes go on the wire — it describes what a *valid* document looks like, so you
can reject bad data at the boundary and document your API contract.

**Trade-off in one line:** you pay in payload size and parse speed to gain
debuggability, universal tooling, and contracts that humans can read directly.

---

## Formats at a Glance

| Format | Validates | Payload it governs | Typical home |
|---|---|---|---|
| JSON Schema | Structure, types, constraints | JSON | REST APIs, configs, forms |
| XML Schema (XSD) | Structure, types, namespaces | XML | SOAP, enterprise B2B |
| OpenAPI (Swagger) | Request/response shapes + endpoints | HTTP + JSON/XML | REST API contracts |

---

## JSON Schema

➡️ **Runnable example:** [json-schema/](json-schema/README.md)

- **How it works:** a JSON document that describes other JSON documents —
  required properties, types, string patterns, numeric ranges, enums, nested
  objects, conditional rules (`if/then`), and composition (`allOf`, `oneOf`).
  Validators exist for every mainstream language.
- **Implementation fit:**
  - ✅ **Human-facing / public HTTP APIs** — validate inbound request bodies
    and document response shapes without forcing clients into codegen.
  - ✅ **Configuration files** — editors (VS Code) give autocomplete and inline
    errors from a schema; CI validates configs before deploy.
  - ✅ Form generation and low-code tools (schema drives the UI).
  - ⚠️ Not a wire-efficiency play: the payload is still text JSON. For
    high-volume internal streaming, prefer a binary schema-driven format.
- **Schema volatility:** ★★★★ — **additive changes are trivial** (new optional
  properties don't break old validators). Great when structures change
  frequently and consumers are many and external.

## XML Schema (XSD)

- **How it works:** the enterprise-era standard for describing XML documents:
  strict element ordering, rich built-in datatypes, namespaces, inheritance
  (type extension/restriction), and referential constraints.
- **Implementation fit:**
  - ✅ **Regulated, document-centric batch exchange** — banking (ISO 20022),
    healthcare, government filings, B2B EDI-replacements, SOAP web services.
    These domains value the rigidity: a document either conforms exactly or
    is rejected.
  - ✅ Long-lived archival documents where the contract must hold for decades.
  - ⚠️ Heavyweight for greenfield APIs — verbose payloads, complex tooling.
- **Schema volatility:** ★★ — rigid by design; evolving an XSD across partners
  is a coordinated (often contractual) event. Best where structures **stay
  static** for years.

## OpenAPI (Swagger)

- **How it works:** not a serialization format itself but the **contract layer
  for REST APIs**: it describes endpoints, methods, parameters, auth, and uses
  (a dialect of) JSON Schema for the request/response bodies. One YAML/JSON
  file drives docs (Swagger UI), client/server codegen, mock servers, and
  gateway validation.
- **Implementation fit:**
  - ✅ **Request/response microservices exposed over HTTP** — internal or
    public. The spec becomes the single source of truth for every consumer.
  - ✅ Design-first workflows: write the spec, generate stubs, then implement.
  - ⚠️ Doesn't cover event/streaming payloads — that's AsyncAPI's job (which
    reuses the same schema ideas for Kafka/MQTT/AMQP topics).
- **Schema volatility:** ★★★★ — versioned APIs (`/v1`, `/v2`) plus additive
  schema changes handle frequent evolution well; breaking changes get a new
  version rather than a silent mutation.

---

## Choosing Within This Category

```text
Validating JSON payloads or config files?                 → JSON Schema
Describing a whole REST API (endpoints + payloads)?       → OpenAPI
Async/event-driven APIs (Kafka, MQTT)?                    → AsyncAPI (JSON Schema inside)
Enterprise/regulated XML document exchange?               → XSD
```
