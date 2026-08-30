# Protobuf Code Example (Python)

A minimal end-to-end Protobuf workflow: define a schema, generate code,
serialize/deserialize, compare size with JSON, and demonstrate the schema
evolution behavior that makes Protobuf safe for microservices.

## Files

| File | Purpose |
|---|---|
| [user.proto](user.proto) | The schema (contract) — with evolution rules annotated |
| [protobuf_demo.py](protobuf_demo.py) | Serialize, deserialize, size comparison, forward compatibility |
| [requirements.txt](requirements.txt) | `protobuf` runtime + `grpcio-tools` (bundles the `protoc` compiler) |

## The Protobuf Workflow

```text
 user.proto ──(protoc code generator)──► user_pb2.py ──(import)──► your app
   schema                                 typed classes              serialize /
   (contract)                                                        deserialize
```

Unlike JSON, you can't just "write a dict." The schema comes first, code is
generated from it, and both sides of the wire compile against the same
contract. That's the price — and the guarantee.

## Run It

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

Generate the Python classes from the schema (`grpcio-tools` bundles `protoc`,
so no system install is needed):

```bash
python -m grpc_tools.protoc -I. --python_out=. user.proto
```

Then run the demo:

```bash
python protobuf_demo.py
```

Expected output (sizes vary slightly with the timestamp):

```text
Protobuf wire size : 112 bytes
Wire bytes (hex)   : 082a120574616d696c1a1d...
JSON size          : 268 bytes
Savings            : 59% smaller than JSON

Round-trip OK      : id=42 username=tamil role=ADMIN city=Chennai
Forward compat     : v2 payload parsed by v1 consumer, username='tamil' (unknown field skipped & preserved)
Unknown field kept : True

Batch of 3 users   : 342 bytes (114 bytes/user amortized)
```

## What the Demo Teaches

1. **Compactness** — field *numbers* go on the wire, not field *names*, and
   integers are varint-encoded. The same record is roughly half the size of
   its JSON form (before any compression).
2. **Round-trip fidelity** — the generated classes are typed; a decoded
   message compares equal to the original.
3. **Forward compatibility** — a v1 consumer parsing a v2 message doesn't
   crash on the unknown field; it skips it *and preserves it* on
   re-serialization, so intermediaries don't corrupt data.
4. **Why the rules matter** — `user.proto` shows `reserved`, the guard rail
   that stops a deleted field number from ever being reused with a new
   meaning (which would silently mis-decode archived payloads).

## Where Protobuf Fits (from the decision map)

- **Processing pattern:** real-time streaming and RPC — gRPC microservices,
  mobile↔backend, event payloads where every byte and microsecond counts.
  For analytical batch/data lakes, prefer Avro (self-describing files).
- **Schema volatility:** handles frequent change well *provided the field
  number rules are followed*; breaking the rules breaks compatibility
  silently, which is why teams keep `.proto` files in a shared, reviewed repo.
