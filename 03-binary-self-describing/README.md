# 3. Binary Self-Describing Formats (Schema-Optional Flexibility)

These formats need **no external schema, registry, or codegen**. Like JSON,
every payload carries its own structure — but the type tags and lengths are
encoded in **compact binary** instead of text. Think of them as "JSON, but
smaller and faster," with extra types (raw bytes, dates) that JSON lacks.

**Trade-off in one line:** you gain drop-in binary efficiency and total schema
freedom, but you lose the enforced contract — nothing stops a producer from
silently changing the shape of the data.

---

## Formats at a Glance

| Format | Standardized by | Extra types over JSON | Sweet spot |
|---|---|---|---|
| MessagePack | Community spec | bin, ext, timestamps | Caches, sockets, log shipping |
| CBOR | IETF (RFC 8949) | bin, tags, bignums, dates | IoT, security tokens (COSE) |
| BSON | MongoDB | ObjectId, Date, Decimal128, bin | MongoDB storage/wire |

---

## MessagePack

- **How it works:** "binary JSON." Each value is prefixed with a compact type
  tag; small integers and short strings fit in a single byte of overhead.
  Typically 15–50% smaller than JSON and much faster to parse. API-wise it's a
  drop-in: `packb(obj)` / `unpackb(bytes)` — your app code doesn't change.
- **Implementation fit:**
  - ✅ **Real-time streaming between your own services** — websocket frames,
    Redis values, RPC where both ends are yours and a schema registry is
    overkill (Fluentd ships logs as MessagePack).
  - ✅ Caching serialized objects compactly.
  - ⚠️ No contract: producers and consumers must agree by convention.
- **Schema volatility:** structures can change **as freely as JSON** — ideal
  when shape changes frequently, but pair it with tests/validation because the
  format itself won't catch drift.

## CBOR (Concise Binary Object Representation)

- **How it works:** an **IETF internet standard** (RFC 8949) with goals of a
  tiny encoder/decoder footprint and no need for schema negotiation. Adds a
  *semantic tag* system (dates, bignums, URIs) and canonical/deterministic
  encoding modes — important for cryptographic signing.
- **Implementation fit:**
  - ✅ **Low-power IoT / constrained devices** — the payload format of CoAP;
    encoders fit in a few KB of flash on microcontrollers.
  - ✅ **Security envelopes** — COSE (CBOR Object Signing and Encryption),
    WebAuthn/FIDO2 credentials, ISO mobile driver's licenses.
  - ✅ Anywhere you'd use MessagePack but want an official standard behind it.
  - 📝 Optional contracts exist via **CDDL** (a schema language for CBOR/JSON)
    if you later want validation without leaving the ecosystem.
- **Schema volatility:** schema-free like MessagePack — flexible by default,
  with CDDL available when parts of the structure settle down.

## BSON (Binary JSON)

- **How it works:** MongoDB's storage and wire format. Unlike
  MessagePack/CBOR, it optimizes for **traversability, not minimal size**:
  documents embed length prefixes and field names so the database can skip to
  a field or update in place without decoding everything. Adds types JSON
  lacks: `ObjectId`, UTC datetime, `Decimal128`, raw binary, regex.
- **Implementation fit:**
  - ✅ **Document database workloads** — you use BSON implicitly whenever you
    use MongoDB; drivers convert your objects to/from BSON.
  - ⚠️ Rarely the right choice as a general-purpose interchange format —
    payloads can be *larger* than JSON (field names + length prefixes), and
    the ecosystem outside MongoDB is thin. Prefer MessagePack/CBOR there.
- **Schema volatility:** schema-free (that's the point of document stores);
  MongoDB optionally layers **JSON Schema validation** on collections when you
  want guardrails — a nice example of categories 2 and 3 combining.

---

## Choosing Within This Category

```text
Drop-in binary replacement for JSON between your services?   → MessagePack
Constrained devices, or payloads that get signed/encrypted?  → CBOR
Working with MongoDB?                                        → BSON (implicitly)
Need a contract after all?                                   → CDDL (CBOR) or move to category 1
```
