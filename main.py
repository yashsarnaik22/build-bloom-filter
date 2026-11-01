import sys

# Cuckoo filter: buckets contain four 8-bit fingerprints each.
buckets = []
out = []

MASK32 = 0xFFFFFFFF
SLOTS_PER_BUCKET = 4
MAX_KICKS = 500

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

def fingerprint_and_buckets(key):
    fingerprint = h_b(key) & 0xFF
    if fingerprint == 0:
        fingerprint = 1
    first = h_a(key) & (len(buckets) - 1)
    second = alternate_bucket(first, fingerprint)
    return fingerprint, first, second

def alternate_bucket(index, fingerprint):
    displacement = (fingerprint * 0x5BD1E995) % len(buckets)
    return index ^ displacement

def first_empty_slot(bucket):
    for slot, value in enumerate(bucket):
        if value == 0:
            return slot
    return None

def insert_fingerprint(fingerprint, first, second):
    for index in (first, second):
        slot = first_empty_slot(buckets[index])
        if slot is not None:
            buckets[index][slot] = fingerprint
            return True

    # Save the table so a failed 500-kick insertion can be rolled back exactly.
    before = [bucket[:] for bucket in buckets]
    current_bucket = first
    current = fingerprint

    for kick in range(MAX_KICKS):
        slot = kick % SLOTS_PER_BUCKET
        evicted = buckets[current_bucket][slot]
        buckets[current_bucket][slot] = current
        current = evicted

        current_bucket = alternate_bucket(current_bucket, current)
        empty_slot = first_empty_slot(buckets[current_bucket])
        if empty_slot is not None:
            buckets[current_bucket][empty_slot] = current
            return True

    buckets[:] = before
    return False


def contains_fingerprint(fingerprint, first, second):
    return fingerprint in buckets[first] or fingerprint in buckets[second]


def remove_fingerprint(fingerprint, first, second):
    for index in (first, second):
        try:
            slot = buckets[index].index(fingerprint)
        except ValueError:
            continue
        buckets[index][slot] = 0
        return True
    return False


for raw in sys.stdin:
    line = raw.rstrip("\r\n")
    if not line.strip():
        continue

    parts = line.split(maxsplit=1)
    cmd = parts[0]

    if cmd == "INIT":
        args = line.split()
        if len(args) != 2:
            continue

        bucket_count = int(args[1])
        if bucket_count <= 0 or bucket_count & (bucket_count - 1):
            out.append("ERR BUCKETS")
            continue

        buckets = [[0] * SLOTS_PER_BUCKET for _ in range(bucket_count)]
        out.append(f"OK buckets={bucket_count} slots={bucket_count * SLOTS_PER_BUCKET}")

    elif cmd in ("ADD", "CHECK", "REMOVE", "FP", "POSITIONS"):
        if not buckets:
            continue

        key = argument_after_command(line)
        fingerprint, first, second = fingerprint_and_buckets(key)

        if cmd == "ADD":
            out.append("OK" if insert_fingerprint(fingerprint, first, second) else "FULL")
        elif cmd == "CHECK":
            out.append("MAYBE" if contains_fingerprint(fingerprint, first, second) else "NO")
        elif cmd == "REMOVE":
            out.append("OK" if remove_fingerprint(fingerprint, first, second) else "WAS_ABSENT")
        elif cmd == "FP":
            out.append(str(fingerprint))
        else:  # POSITIONS
            out.append(f"fp={fingerprint} i1={first} i2={second}")

    elif cmd == "COUNT":
        if buckets:
            out.append(str(sum(value != 0 for bucket in buckets for value in bucket)))

    elif cmd == "LOAD":
        if buckets:
            occupied = sum(value != 0 for bucket in buckets for value in bucket)
            capacity = len(buckets) * SLOTS_PER_BUCKET
            out.append(f"{occupied / capacity:.4f}")

    elif cmd == "DUMP":
        if buckets:
            out.append("".join(format(value, "02x") for bucket in buckets for value in bucket))

sys.stdout.write("\n".join(out) + ("\n" if out else ""))
