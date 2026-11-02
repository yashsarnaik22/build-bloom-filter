import math
import sys

MASK32 = 0xFFFFFFFF
LN2 = 0.6931471805599453
LN2SQ = 0.4804530139182014
MAX_FILTER_BYTES = 36000
MAX_HASHES = 50
SEED_STEP = 0xFBA4C795

filter_bytes = bytearray()
hash_count = 0
tweak = 0
flags = 0
out = []


def rotl32(value, amount):
    value &= MASK32
    return ((value << amount) | (value >> (32 - amount))) & MASK32


def murmur3_32(data, seed):
    """MurmurHash3 x86_32 over bytes, with all arithmetic kept to 32 bits."""
    h = seed & MASK32
    c1 = 0xCC9E2D51
    c2 = 0x1B873593

    complete_length = len(data) - len(data) % 4
    for offset in range(0, complete_length, 4):
        block = int.from_bytes(data[offset:offset + 4], "little")
        block = (block * c1) & MASK32
        block = rotl32(block, 15)
        block = (block * c2) & MASK32
        h ^= block
        h = rotl32(h, 13)
        h = (h * 5 + 0xE6546B64) & MASK32

    tail = data[complete_length:]
    if tail:
        block = int.from_bytes(tail, "little")
        block = (block * c1) & MASK32
        block = rotl32(block, 15)
        block = (block * c2) & MASK32
        h ^= block

    h ^= len(data)
    h ^= h >> 16
    h = (h * 0x85EBCA6B) & MASK32
    h ^= h >> 13
    h = (h * 0xC2B2AE35) & MASK32
    h ^= h >> 16
    return h & MASK32


def indexes(element):
    bit_count = len(filter_bytes) * 8
    if bit_count == 0:
        return []

    result = []
    for i in range(hash_count):
        seed = (i * SEED_STEP + tweak) & MASK32
        result.append(murmur3_32(element, seed) % bit_count)
    return result


def insert(element):
    for bit_index in indexes(element):
        filter_bytes[bit_index // 8] |= 1 << (bit_index % 8)


def contains(element):
    return all(
        filter_bytes[bit_index // 8] & (1 << (bit_index % 8))
        for bit_index in indexes(element)
    )


def compact_size(value):
    if value < 253:
        return bytes((value,))
    return b"\xfd" + value.to_bytes(2, "little")


def filterload_payload():
    return (
        compact_size(len(filter_bytes))
        + bytes(filter_bytes)
        + hash_count.to_bytes(4, "little")
        + tweak.to_bytes(4, "little")
        + bytes((flags,))
    )


def element_after_command(line):
    command_end = 0
    while command_end < len(line) and not line[command_end].isspace():
        command_end += 1
    return bytes.fromhex(line[command_end:].strip()) if command_end < len(line) else b""


for raw in sys.stdin:
    line = raw.rstrip("\r\n")
    if not line.strip():
        continue

    parts = line.split()
    command = parts[0]

    if command == "INIT":
        if len(parts) != 5:
            continue

        n = int(parts[1])
        error_rate = float(parts[2])
        tweak = int(parts[3]) & MASK32
        flags = int(parts[4]) & 0xFF

        bit_count = min(
            math.trunc((-1.0 / LN2SQ) * n * math.log(error_rate)),
            MAX_FILTER_BYTES * 8,
        )
        byte_count = bit_count // 8
        hash_count = min(
            math.trunc(((byte_count * 8) // n) * LN2),
            MAX_HASHES,
        )
        filter_bytes = bytearray(byte_count)
        out.append(f"OK bytes={byte_count} hashes={hash_count}")

    elif command in ("INSERT", "CONTAINS", "INDEXES"):
        element = element_after_command(line)
        if command == "INSERT":
            insert(element)
            out.append("OK")
        elif command == "CONTAINS":
            out.append("MAYBE" if contains(element) else "NO")
        else:
            out.append(",".join(map(str, indexes(element))))

    elif command == "FILTERLOAD":
        out.append(filterload_payload().hex())

sys.stdout.write("\n".join(out) + ("\n" if out else ""))
