import sys
import math

# Scalable Bloom filter commands:
#   INIT <capacity> <target-error>
#   ADD <key>, CHECK <key>
#   FILTERS, TOTAL, SHAPE, COMPOUND

filters = []
total = 0
out = []

MASK32 = 0xFFFFFFFF

def rotl32(value, amount):
    value &= MASK32
    return ((value << amount) | (value >> (32 - amount))) & MASK32

def murmur3_32(s, seed):
    data = s.encode()
    h = seed & MASK32
    c1 = 0xCC9E2D51
    c2 = 0x1B873593

    for offset in range(0, len(data) - len(data) % 4, 4):
        block = int.from_bytes(data[offset:offset + 4], "little")
        block = (block * c1) & MASK32
        block = rotl32(block, 15)
        block = (block * c2) & MASK32
        h ^= block
        h = rotl32(h, 13)
        h = (h * 5 + 0xE6546B64) & MASK32

    tail = data[len(data) - len(data) % 4:]
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

def h_a(s):
    return murmur3_32(s, 0)

def h_b(s):
    return murmur3_32(s, 0x9747B28C)

def positions(s, m, k):
    return [(h_a(s) + i * h_b(s)) % m for i in range(k)]

def argument_after_command(line):
    """Return the exact argument text after the command and one space."""
    i = 0
    while i < len(line) and line[i].isspace():
        i += 1
    while i < len(line) and not line[i].isspace():
        i += 1
    return line[i + 1:] if i < len(line) else ""

def size_filter(capacity, target):
    m = math.ceil(-capacity * math.log(target) / (math.log(2) ** 2))
    k = max(1, round((m / capacity) * math.log(2)))
    return m, k

def make_filter(capacity, target):
    m, k = size_filter(capacity, target)
    return {
        "capacity": capacity,
        "target": target,
        "m": m,
        "k": k,
        "bits": [0] * m,
        "count": 0,
    }

def add_to_filter(filter_state, key):
    for p in positions(key, filter_state["m"], filter_state["k"]):
        filter_state["bits"][p] = 1

def contains_in_filter(filter_state, key):
    bits = filter_state["bits"]
    return all(bits[p] for p in positions(key, filter_state["m"], filter_state["k"]))


for raw in sys.stdin:
    line = raw.rstrip("\r\n")
    if not line.strip():
        continue

    parts = line.split(maxsplit=1)
    cmd = parts[0]

    if cmd == "INIT":
        args = line.split()
        if len(args) != 3:
            continue

        capacity = int(args[1])
        target = float(args[2])
        if capacity <= 0 or not 0 < target < 1:
            continue

        filters = [make_filter(capacity, target)]
        total = 0
        newest = filters[0]
        out.append(f"OK m={newest['m']} k={newest['k']}")

    elif cmd == "ADD":
        if not filters:
            continue

        key = argument_after_command(line)
        newest = filters[-1]
        if newest["count"] >= newest["capacity"]:
            filters.append(make_filter(newest["capacity"] * 2, newest["target"] * 0.5))
            newest = filters[-1]
        add_to_filter(newest, key)
        newest["count"] += 1
        total += 1

        out.append("OK")

    elif cmd == "CHECK":
        if not filters:
            continue

        key = argument_after_command(line)
        out.append("MAYBE" if any(contains_in_filter(f, key) for f in reversed(filters)) else "NO")

    elif cmd == "FILTERS":
        out.append(str(len(filters)))

    elif cmd == "TOTAL":
        out.append(str(total))

    elif cmd == "SHAPE":
        for filter_state in filters:
            out.append(
                f"m={filter_state['m']} k={filter_state['k']} "
                f"cap={filter_state['capacity']} n={filter_state['count']}"
            )

    elif cmd == "COMPOUND":
        probability_not_found = 1.0
        for filter_state in filters:
            p = filter_state["target"]
            probability_not_found *= 1.0 - p
        out.append(f"{1.0 - probability_not_found:.6f}")

sys.stdout.write("\n".join(out) + ("\n" if out else ""))
