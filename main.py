import sys
import math

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

filters = {}  # name -> (m, k, bits)
out = []

def h_a(s):
    return sum(b * (i + 1) for i, b in enumerate(s.encode())) & 0xFFFFFFFF

def h_b(s):
    return sum(b ^ (i + 1) for i, b in enumerate(s.encode())) & 0xFFFFFFFF

def positions(s, m, k):
    return [(h_a(s) + i * h_b(s)) % m for i in range(k)]

def key_after_name(line):
    """Return the exact key text after the command and filter name."""
    i = 0
    while i < len(line) and line[i].isspace():
        i += 1
    while i < len(line) and not line[i].isspace():
        i += 1
    while i < len(line) and line[i].isspace():
        i += 1
    while i < len(line) and not line[i].isspace():
        i += 1
    return line[i + 1:] if i < len(line) else ""


for raw in sys.stdin:
    line = raw.rstrip("\r\n")
    if not line.strip():
        continue

    # Preserve the complete key after the command and filter name.
    parts = line.split(maxsplit=2)
    cmd = parts[0]

    if cmd == "INIT":
        args = line.split()

        if len(args) != 4:
            continue

        name = args[1]
        m = int(args[2])
        k = int(args[3])

        if m <= 0 or k <= 0:
            continue

        # Reinitializing a name replaces its existing filter.
        filters[name] = (m, k, [0] * m)
        out.append("OK")

    elif cmd == "ADD":
        if len(parts) < 2:
            continue

        name = parts[1]
        key = key_after_name(line)

        if name not in filters:
            out.append("ERR NOFILTER")
            continue

        m, k, bits = filters[name]

        for p in positions(key, m, k):
            bits[p] = 1

        out.append("OK")

    elif cmd == "CHECK":
        if len(parts) < 2:
            continue

        name = parts[1]
        key = key_after_name(line)

        if name not in filters:
            out.append("ERR NOFILTER")
            continue

        m, k, bits = filters[name]
        pos = positions(key, m, k)

        out.append(
            "MAYBE" if all(bits[p] for p in pos) else "NO"
        )

    elif cmd == "UNION" or cmd == "INTERSECT":
        args = line.split()

        if len(args) != 4:
            continue

        out_name, a_name, b_name = args[1], args[2], args[3]

        # Missing filters must be checked before compatibility.
        if a_name not in filters or b_name not in filters:
            out.append("ERR NOFILTER")
            continue

        m_a, k_a, bits_a = filters[a_name]
        m_b, k_b, bits_b = filters[b_name]

        if m_a != m_b or k_a != k_b:
            out.append("ERR MISMATCH")
            continue

        # Build a new list so the output never aliases either input.
        if cmd == "UNION":
            result = [x | y for x, y in zip(bits_a, bits_b)]
        else:
            result = [x & y for x, y in zip(bits_a, bits_b)]

        filters[out_name] = (m_a, k_a, result)
        out.append("OK")

    elif cmd == "POPCOUNT":
        if len(parts) < 2:
            continue

        name = parts[1]

        if name not in filters:
            out.append("ERR NOFILTER")
            continue

        m, k, bits = filters[name]
        out.append(str(sum(bits)))

    elif cmd == "BITS":
        if len(parts) < 2:
            continue

        name = parts[1]

        if name not in filters:
            out.append("ERR NOFILTER")
            continue

        m, k, bits = filters[name]

        # Bit 0 comes first.
        out.append("".join(map(str, bits)))

    elif cmd == "ESTIMATE":
        if len(parts) < 2:
            continue

        name = parts[1]

        if name not in filters:
            out.append("ERR NOFILTER")
            continue

        m, k, bits = filters[name]
        ones = sum(bits)

        if ones == m:
            out.append("FULL")
        else:
            estimate = -(m / k) * math.log(1 - ones / m)
            out.append(str(math.floor(estimate + 0.5)))

sys.stdout.write("\n".join(out) + ("\n" if out else ""))
