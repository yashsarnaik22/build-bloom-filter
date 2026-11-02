import math
import sys


MASK32 = 0xFFFFFFFF
LN2 = math.log(2.0)
LN2_SQUARED = LN2 * LN2

bit_count = 0
hash_count = 0
bits = bytearray()
cache = {}
hits = 0
misses = 0
bloom_misses = 0
bloom_fp = 0
out = []


def rotate_left_32(value, amount):
    value &= MASK32
    return ((value << amount) | (value >> (32 - amount))) & MASK32


def murmur3_32(value, seed):
    data = value.encode("utf-8")
    result = seed & MASK32
    c1 = 0xCC9E2D51
    c2 = 0x1B873593

    complete_length = len(data) - len(data) % 4
    for offset in range(0, complete_length, 4):
        block = int.from_bytes(data[offset:offset + 4], "little")
        block = (block * c1) & MASK32
        block = rotate_left_32(block, 15)
        block = (block * c2) & MASK32
        result ^= block
        result = rotate_left_32(result, 13)
        result = (result * 5 + 0xE6546B64) & MASK32

    tail = data[complete_length:]
    if tail:
        block = int.from_bytes(tail, "little")
        block = (block * c1) & MASK32
        block = rotate_left_32(block, 15)
        block = (block * c2) & MASK32
        result ^= block

    result ^= len(data)
    result ^= result >> 16
    result = (result * 0x85EBCA6B) & MASK32
    result ^= result >> 13
    result = (result * 0xC2B2AE35) & MASK32
    result ^= result >> 16
    return result & MASK32


def positions(value):
    if bit_count <= 0:
        return []
    first_hash = murmur3_32(value, 0)
    second_hash = murmur3_32(value, 0x9747B28C)
    return [
        (first_hash + index * second_hash) % bit_count
        for index in range(hash_count)
    ]


def insert(value):
    for position in positions(value):
        bits[position] = 1


def contains(value):
    return all(bits[position] for position in positions(value))


def current_fill():
    return sum(bits) / bit_count if bit_count else 0.0


for raw in sys.stdin:
    line = raw.rstrip("\r\n")
    if not line.strip():
        continue

    parts = line.split(maxsplit=2)
    command = parts[0]

    if command == "INIT" and len(parts) >= 3:
        expected_items = int(parts[1])
        target_fp = float(parts[2])
        if expected_items <= 0 or not 0.0 < target_fp < 1.0:
            continue

        bit_count = math.ceil(
            -expected_items * math.log(target_fp) / LN2_SQUARED
        )
        hash_count = max(1, round((bit_count / expected_items) * LN2))
        bits = bytearray(bit_count)
        cache = {}
        hits = 0
        misses = 0
        bloom_misses = 0
        bloom_fp = 0
        out.append(f"OK m={bit_count} k={hash_count}")

    elif command == "PUT_CACHE" and len(parts) >= 2:
        key = parts[1]
        value = parts[2] if len(parts) > 2 else ""
        cache[key] = value
        insert(key)
        out.append("OK")

    elif command == "GET" and len(parts) >= 2:
        key = parts[1]
        if not contains(key):
            bloom_misses += 1
            out.append("BLOOM_MISS")
        elif key in cache:
            hits += 1
            out.append(f"HIT {cache[key]}")
        else:
            misses += 1
            bloom_fp += 1
            out.append("MISS_BLOOM_FP")

    elif command == "INVALIDATE" and len(parts) >= 2:
        cache.pop(parts[1], None)
        out.append("OK")

    elif command == "REBUILD":
        bits = bytearray(bit_count)
        for key in cache:
            insert(key)
        out.append(f"OK rebuilt={len(cache)}")

    elif command == "FILL":
        out.append(f"{current_fill():.4f}")

    elif command == "STATS":
        out.append(
            f"hits={hits} misses={misses} "
            f"bloom_misses={bloom_misses} bloom_fp={bloom_fp}"
        )

sys.stdout.write("\n".join(out) + ("\n" if out else ""))
