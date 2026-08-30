# Data Serialization Formats — Learning Guide

Serialization is the process of converting in-memory data structures into a byte
stream (for storage or transmission) and back again (deserialization). The format
you choose affects payload size, CPU cost, human readability, schema evolution,
and how safely independent services can talk to each other.

This repository organizes the major formats by **design philosophy**:

| Folder | Category | Formats covered |
|---|---|---|
| [01-binary-schema-driven](01-binary-schema-driven/README.md) | Binary Schema-Driven | Avro, Protobuf, FlatBuffers, Cap'n Proto, Thrift |
| [02-text-based-validation](02-text-based-validation/README.md) | Text-Based Validation | JSON Schema, XML Schema (XSD), OpenAPI (Swagger) |
| [03-binary-self-describing](03-binary-self-describing/README.md) | Binary Self-Describing | MessagePack, CBOR, BSON |

Runnable code examples live in
[01-binary-schema-driven/protobuf](01-binary-schema-driven/protobuf/) and
[02-text-based-validation/json-schema](02-text-based-validation/json-schema/).

---

## 🗺️ Conceptual Mind Map

```text
                  ┌──────────────────────────────────────────────┐
                  │          DATA SERIALIZATION FORMATS          │
                  └──────────────────────┬───────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
┌───────────────┐                ┌───────────────┐                ┌───────────────┐
│ BINARY SCHEMA │                │  TEXT-BASED   │                │ BINARY SELF-  │
│    DRIVEN     │                │  VALIDATION   │                │  DESCRIBING   │
└───────┬───────┘                └───────┬───────┘                └───────┬───────┘
        │                                │                                │
        ├─► Avro                         ├─► JSON Schema                  ├─► MessagePack
        ├─► Protobuf                     ├─► XML Schema (XSD)             ├─► CBOR
        ├─► FlatBuffers                  └─► OpenAPI (Swagger)            └─► BSON
        ├─► Cap'n Proto
        └─► Thrift
```

### 1. Binary Schema-Driven (Performance & Contracts)

These formats require a strict schema definition before data can be read or
written. They generate tiny, highly optimized binary payloads.

- **Avro** — stores the schema with the data (or in a registry). No field tags
  or IDs in the payload; relies on reader/writer schema resolution. Great for
  big data (Hadoop, Kafka).
- **Protobuf** — uses sequential field numbers to match data fields. Requires
  code generation. Highly optimized for network RPCs (gRPC).
- **FlatBuffers / Cap'n Proto** — zero-copy formats. The binary structure on
  the wire matches the structure in RAM. You can read a single field without
  parsing the whole file.
- **Thrift** — similar to Protobuf but tightly coupled with its own
  multi-language RPC layer.

### 2. Text-Based Validation (Human Readability)

These formats are designed for human readability and web APIs. The schemas
function as validation rules overlaid on top of text structures.

- **JSON Schema** — validates the structure, types, and constraints of
  standard, readable JSON text payloads.
- **XML Schema (XSD)** — the legacy enterprise standard. Provides strict
  structural and type validation for XML documents.
- **OpenAPI (Swagger)** — validates the request and response shapes
  specifically for HTTP REST API endpoints.

### 3. Binary Self-Describing (Schema-Optional Flexibility)

These formats do not require a separate schema registry or file. They take
human-readable formats (like JSON) and compress them into a binary format by
tagging data types directly inside the payload.

- **MessagePack** — essentially "binary JSON." Much smaller payloads than raw
  text without changing how your app handles data.
- **CBOR** — an IETF internet standard similar to MessagePack, optimized for
  low-power IoT devices.
- **BSON** — used by MongoDB. Extends JSON with extra types like raw binary,
  dates, and object IDs.

---

## 🧭 Implementation Map — Which Format for Which Workload?

The two questions that decide the format faster than any benchmark:

1. **What is the processing pattern?** Analytical batch (data lakes, ETL) vs.
   real-time streaming (microservices, events, RPC) vs. human-facing APIs.
2. **How volatile is the schema?** Do data structures change frequently
   (weekly evolving product events) or stay static (a fixed telemetry packet)?

```text
                        WORKLOAD → FORMAT MAP
                        ─────────────────────

 PROCESSING PATTERN
 ├─ Analytical / batch (data lakes, Hadoop, Spark, Kafka archive)
 │    └─► AVRO ............ schema travels with the file; millions of rows
 │                           share one schema header; splittable, compact.
 │
 ├─ Real-time streaming / microservice RPC (gRPC, event buses)
 │    ├─► PROTOBUF ........ tiny payloads, fast encode/decode, strict
 │    │                      contracts between teams; native to gRPC.
 │    └─► THRIFT .......... same niche, when you adopt its whole RPC stack.
 │
 ├─ Ultra-low latency reads (games, HFT, mobile, mmap'd files)
 │    └─► FLATBUFFERS / CAP'N PROTO ... zero-copy: read one field without
 │                           deserializing the message at all.
 │
 ├─ Public / human-facing HTTP APIs (browser clients, webhooks, config)
 │    ├─► JSON + JSON SCHEMA ... readable, debuggable, validated.
 │    ├─► OPENAPI ......... the contract layer for REST endpoints.
 │    └─► XSD ............. regulated / legacy enterprise XML (SOAP, finance).
 │
 └─ Bandwidth-constrained but schema-less (IoT, caches, doc stores)
      ├─► CBOR ............ IETF standard; tiny devices, COSE/CoAP.
      ├─► MESSAGEPACK ..... drop-in binary JSON for caches & sockets.
      └─► BSON ............ inside MongoDB (traversable, indexable docs).


 SCHEMA VOLATILITY
 ├─ Changes frequently, producers/consumers deploy independently
 │    ├─► AVRO ............ best-in-class evolution: reader schema vs
 │    │                      writer schema resolved at read time (Kafka +
 │    │                      Schema Registry pattern).
 │    ├─► PROTOBUF ........ safe evolution IF you follow the rules:
 │    │                      never reuse field numbers, only add optional
 │    │                      fields, reserve deleted ones.
 │    └─► JSON SCHEMA ..... loose evolution; additive changes are easy,
 │                           validation catches breakage at the edge.
 │
 └─ Stays static (fixed sensor packets, stable internal structs)
      ├─► FLATBUFFERS / CAP'N PROTO ... layout is baked into the binary;
      │                      renegotiating layout is costly, so they shine
      │                      when the structure is settled.
      └─► MESSAGEPACK / CBOR ... no schema to migrate at all — but also
                             no contract; discipline lives in your code.
```

### Decision Matrix

| Format | Best-fit workload | Batch or Streaming? | Schema volatility tolerance | Payload size | Human readable | Zero-copy | Typical ecosystem |
|---|---|---|---|---|---|---|---|
| **Avro** | Data lakes, Kafka pipelines, ETL | **Batch-first** (also Kafka streaming via registry) | ★★★★★ (reader/writer resolution) | Very small | No | No | Hadoop, Spark, Kafka, Flink |
| **Protobuf** | Microservice RPC, mobile↔backend | **Streaming / request-response** | ★★★★ (field-number rules) | Very small | No | No | gRPC, Kubernetes, Envoy |
| **FlatBuffers** | Games, AR/VR, mobile asset files | Real-time reads | ★★ (layout-sensitive) | Small | No | **Yes** | Unity, Android, TensorFlow Lite |
| **Cap'n Proto** | Low-latency IPC/RPC | Real-time reads | ★★ | Small | No | **Yes** | Cloudflare Workers, sandboxed IPC |
| **Thrift** | Cross-language internal RPC | Streaming / RPC | ★★★★ | Very small | No | No | Legacy Facebook/Apache stacks |
| **JSON Schema** | Public REST APIs, config validation | Request-response | ★★★★ (additive is easy) | Large (text) | **Yes** | No | Web APIs, form validation, CI checks |
| **XSD** | Enterprise/regulated document exchange | Batch documents | ★★ (rigid) | Very large | **Yes** | No | SOAP, banking, healthcare (HL7) |
| **OpenAPI** | REST endpoint contracts | Request-response | ★★★★ | n/a (spec layer) | **Yes** | n/a | Swagger UI, codegen, API gateways |
| **MessagePack** | Caches, websockets, Redis values | Streaming | ★★★ (schema-free) | Small | No | No | Redis, Fluentd, socket protocols |
| **CBOR** | IoT sensors, constrained devices | Streaming (tiny frames) | ★★★ (schema-free; CDDL optional) | Small | No | No | CoAP, COSE/WebAuthn, embedded |
| **BSON** | Document database storage | Storage engine | ★★★ | Medium (bigger than JSON sometimes) | No | Partial (traversable) | MongoDB |

### Rules of Thumb

- **Data lake / analytical batch** → **Avro** (row-based, self-contained files,
  splittable across workers; pair with Parquet/ORC for columnar analytics).
- **Service-to-service, latency-sensitive, contract-enforced** → **Protobuf + gRPC**.
- **Schema changes every sprint, many independent consumers** → **Avro with a
  Schema Registry** (streaming) or **JSON + JSON Schema** (HTTP edges).
- **Schema is frozen and reads must be instant** → **FlatBuffers / Cap'n Proto**.
- **Humans must read and debug the payload** → **JSON + JSON Schema / OpenAPI**.
- **Binary savings without adopting schemas** → **MessagePack / CBOR**.

---

## Repository Layout

```text
.
├── README.md                          ← you are here (mind map + decision maps)
├── 01-binary-schema-driven/
│   ├── README.md                      ← Avro, Protobuf, FlatBuffers, Cap'n Proto, Thrift
│   └── protobuf/                      ← 💻 runnable code example
│       ├── README.md
│       ├── user.proto
│       ├── protobuf_demo.py
│       └── requirements.txt
├── 02-text-based-validation/
│   ├── README.md                      ← JSON Schema, XSD, OpenAPI
│   └── json-schema/                   ← 💻 runnable code example
│       ├── README.md
│       ├── user.schema.json
│       ├── validate_demo.py
│       └── requirements.txt
└── 03-binary-self-describing/
    └── README.md                      ← MessagePack, CBOR, BSON
```
