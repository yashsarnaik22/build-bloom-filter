import sys

# Bloom filters compose elegantly under bitwise operations
# (only when m, k, and the hash family are IDENTICAL).
#
#   UNION(A, B)         = A | B          # exact: matches "in A or in B"
#   INTERSECT(A, B)     = A & B          # APPROXIMATE: matches "probably in A AND probably in B"
#                                         # FP rate of intersection is HIGHER than each operand.
#
# Commands:
#   INIT <name> <m> <k>                  -> "OK"
#   ADD <name> <string>                  -> "OK"
#   CHECK <name> <string>                -> "MAYBE"|"NO"
#   UNION <out> <a> <b>                  -> "OK"   (bitwise OR of bit arrays)
#   INTERSECT <out> <a> <b>              -> "OK"   (bitwise AND of bit arrays)
#   POPCOUNT <name>                      -> total bits set
#   BITS <name>                          -> the bit array as a "0101..." string
#   ESTIMATE <name>                      -> estimated number of distinct keys

table = []
m = 0
k = 0
out = []

MASK32 = 0xFFFFFFFF
MAXC = 15

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

def key_positions(key):
    return positions(key, m, k)


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

        m = int(args[1])
        k = int(args[2])

        if m <= 0 or k <= 0:
            continue

        table = [0] * m
        out.append("OK")

    elif cmd == "ADD":
        if not table:
            continue

        key = argument_after_command(line)
        for p in key_positions(key):
            table[p] = min(table[p] + 1, 15)

        out.append("OK")

    elif cmd == "CHECK":
        if not table:
            continue

        key = argument_after_command(line)
        out.append("MAYBE" if all(table[p] > 0 for p in key_positions(key)) else "NO")

    elif cmd == "REMOVE":
        if not table:
            continue

        key = argument_after_command(line)
        pos = key_positions(key)
        if any(table[p] == 0 for p in pos):
            out.append("WAS_ABSENT")
            continue

        for p in pos:
            if table[p] < 15:
                table[p] -= 1
        out.append("OK")

    elif cmd == "COUNT":
        if not table:
            continue

        key = argument_after_command(line)
        out.append(str(min(table[p] for p in key_positions(key))))

    elif cmd == "DUMP":
        if table:
            out.append("".join(format(value, "x") for value in table))

sys.stdout.write("\n".join(out) + ("\n" if out else ""))
