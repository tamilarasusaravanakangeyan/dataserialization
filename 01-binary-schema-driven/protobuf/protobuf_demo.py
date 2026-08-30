"""Protobuf demo: serialize, deserialize, compare size with JSON, and show
forward compatibility (unknown fields are preserved, not fatal).

Setup (once):
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python -m grpc_tools.protoc -I. --python_out=. user.proto

Run:
    python protobuf_demo.py
"""

import json
import time

import user_pb2  # generated from user.proto by protoc


def build_user() -> "user_pb2.User":
    user = user_pb2.User(
        id=42,
        username="tamil",
        email="tamilarasu.saravana@gmail.com",
        active=True,
        role=user_pb2.User.Role.ADMIN,
        tags=["engineer", "learner"],
        created_at_ms=int(time.time() * 1000),
    )
    user.address.street = "1 Marina Beach Rd"
    user.address.city = "Chennai"
    user.address.country = "IN"
    user.address.zip = "600001"
    return user


def main() -> None:
    user = build_user()

    # --- 1. Serialize to the compact binary wire format -------------------
    wire_bytes = user.SerializeToString()
    print(f"Protobuf wire size : {len(wire_bytes)} bytes")
    print(f"Wire bytes (hex)   : {wire_bytes.hex()[:80]}...")

    # --- 2. Compare with the equivalent JSON payload ----------------------
    as_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "active": user.active,
        "role": "ADMIN",
        "address": {
            "street": user.address.street,
            "city": user.address.city,
            "country": user.address.country,
            "zip": user.address.zip,
        },
        "tags": list(user.tags),
        "created_at_ms": user.created_at_ms,
    }
    json_bytes = json.dumps(as_dict).encode()
    print(f"JSON size          : {len(json_bytes)} bytes")
    print(f"Savings            : {100 - 100 * len(wire_bytes) // len(json_bytes)}% smaller than JSON")

    # --- 3. Deserialize: the consumer side ---------------------------------
    received = user_pb2.User()
    received.ParseFromString(wire_bytes)
    assert received == user
    print(f"\nRound-trip OK      : id={received.id} username={received.username} "
          f"role={user_pb2.User.Role.Name(received.role)} city={received.address.city}")

    # --- 4. Schema evolution: old consumer reads a NEWER message -----------
    # Simulate a v2 producer that added a field this consumer doesn't know:
    # field number 100, wire type 2 (length-delimited), value b"dark-mode".
    # Tag byte = (100 << 3) | 2 encoded as varint, then length, then bytes.
    unknown_field = b"\xa2\x06" + bytes([9]) + b"dark-mode"
    v2_payload = wire_bytes + unknown_field

    old_consumer = user_pb2.User()
    old_consumer.ParseFromString(v2_payload)  # does NOT crash
    print("Forward compat     : v2 payload parsed by v1 consumer, "
          f"username={old_consumer.username!r} (unknown field skipped & preserved)")

    # The unknown field survives re-serialization (proto3 >= 3.5), so this
    # consumer can proxy messages without destroying data it doesn't understand.
    reserialized = old_consumer.SerializeToString()
    print(f"Unknown field kept : {b'dark-mode' in reserialized}")

    # --- 5. Batch message ---------------------------------------------------
    batch = user_pb2.UserBatch()
    for i in range(3):
        u = batch.users.add()
        u.CopyFrom(user)
        u.id = i + 1
    batch_bytes = batch.SerializeToString()
    print(f"\nBatch of 3 users   : {len(batch_bytes)} bytes "
          f"({len(batch_bytes) // 3} bytes/user amortized)")


if __name__ == "__main__":
    main()
