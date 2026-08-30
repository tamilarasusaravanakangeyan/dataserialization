# 1. Binary Schema-Driven Formats (Performance & Contracts)

These formats require a **strict schema definition** before data can be read or
written. The schema is the contract: producers and consumers compile against it,
and the wire payload carries little or no self-description — which is exactly
why the payloads are tiny and fast to parse.

**Trade-off in one line:** you give up human readability and ad-hoc flexibility
to gain compactness, speed, and compile-time-checked contracts between systems.

---

## Formats at a Glance

| Format | Wire identification | Codegen required | Zero-copy | Killer feature |
|---|---|---|---|---|
| Avro | None — reader/writer schema resolution | Optional | No | Best schema evolution |
| Protobuf | Field numbers (tags) | Yes | No | gRPC ecosystem |
| FlatBuffers | Offsets/vtables | Yes | **Yes** | Read without parsing |
| Cap'n Proto | Fixed offsets | Yes | **Yes** | "Infinitely fast" decode |
| Thrift | Field IDs | Yes | No | Bundled RPC framework |

---

## Avro

- **How it works:** the payload contains raw values only — no field tags at
  all. To decode, the reader must know the *writer's schema* (embedded in the
  file header, or fetched from a Schema Registry by ID) and resolves it against
  its own *reader schema* (fields matched by name, defaults filled in,
  promotions applied).
- **Why big data loves it:** an Avro file stores the schema once, then millions
  of rows with zero per-record overhead. Files are splittable, so Spark/Hadoop
  can parallelize over blocks.
- **Implementation fit:**
  - ✅ **Analytical batch processing** — the canonical row-based data-lake
    format (raw/landing zones, ETL handoffs, Kafka topic archival).
  - ✅ **Streaming with evolving schemas** — Kafka + Confluent Schema Registry
    is the industry-standard pattern; producers upgrade schemas without
    breaking consumers.
  - ⚠️ Not ideal for request/response RPC — resolving schemas per message is
    overhead when a compiled contract (Protobuf) is simpler.
- **Schema volatility:** ★★★★★ — designed for **frequently changing**
  structures. Add/remove fields with defaults and old data stays readable.

## Protobuf (Protocol Buffers)

➡️ **Runnable example:** [protobuf/](protobuf/README.md)

- **How it works:** each field gets a permanent **field number**; the wire
  format is a sequence of `(field_number, wire_type, value)` records. Unknown
  fields are skipped, which is what makes forward compatibility work. You run
  `protoc` to generate typed classes for your language.
- **Implementation fit:**
  - ✅ **Real-time streaming / microservices** — the default choice for
    service-to-service RPC (gRPC), mobile↔backend traffic, and
    latency-sensitive event payloads.
  - ✅ Static-ish contracts owned by teams that coordinate via `.proto` files
    in a shared repo.
  - ⚠️ Weaker fit for data lakes: payloads aren't self-describing, so batch
    tooling needs the `.proto` files distributed out-of-band.
- **Schema volatility:** ★★★★ — evolves safely **if you follow the rules**:
  never change or reuse a field number, only add new fields, `reserve` the
  numbers of deleted fields.

## FlatBuffers

- **How it works:** the serialized buffer *is* the data structure — vtables
  and offsets let you access any field directly in the byte array without a
  decode step (zero-copy). Reading one field from a 100 MB buffer costs
  nanoseconds, not a full parse.
- **Implementation fit:**
  - ✅ **Real-time, read-heavy, latency-critical** — games (Unity), AR/VR,
    mobile apps reading bundled asset files, ML model files (TensorFlow Lite).
  - ✅ Memory-mapped files: `mmap` the file and read fields in place.
  - ⚠️ Writing/mutating is awkward (builder API, buffers built back-to-front).
- **Schema volatility:** ★★ — best when structures **stay static**; evolution
  is possible (deprecated fields, new fields at the end) but far more
  constrained than Avro/Protobuf.

## Cap'n Proto

- **How it works:** same zero-copy philosophy as FlatBuffers — the wire format
  matches the in-memory layout, so "decoding" is a no-op. Written by the
  original author of Protobuf v2. Comes with a capability-based RPC system
  featuring *promise pipelining* (chain calls without waiting for round trips).
- **Implementation fit:**
  - ✅ **Ultra-low-latency IPC/RPC** between processes on the same machine or
    datacenter (used heavily in Cloudflare Workers).
  - ✅ Sandboxed/security-conscious IPC — messages are usable without a parse
    step that could be attacked.
  - ⚠️ Smaller ecosystem than Protobuf; fewer language implementations.
- **Schema volatility:** ★★ — like FlatBuffers, favors **static structures**.

## Thrift

- **How it works:** conceptually Protobuf's sibling (field IDs + codegen), but
  it ships as a **complete RPC stack**: IDL, multiple binary/compact protocols,
  transports, and server implementations for dozens of languages.
- **Implementation fit:**
  - ✅ Cross-language internal RPC where you adopt the whole Thrift framework
    (historically Facebook, Twitter, Uber; today mostly legacy estates and
    Apache ecosystem projects like Cassandra's old interface).
  - ⚠️ For new systems, gRPC+Protobuf has largely won this niche — choose
    Thrift mainly when joining an existing Thrift shop.
- **Schema volatility:** ★★★★ — same field-ID evolution rules as Protobuf.

---

## Choosing Within This Category

```text
Need it for analytics / data lake / Kafka archive?        → Avro
Need service-to-service RPC with strong contracts?        → Protobuf (gRPC)
Need to read fields without deserializing at all?         → FlatBuffers / Cap'n Proto
Already inside a Thrift-based codebase?                   → Thrift
Schema changes every sprint?                              → Avro (registry) or Protobuf (rules)
Schema frozen, reads must be nanosecond-fast?             → FlatBuffers / Cap'n Proto
```
