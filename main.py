import math
import sys


MASK32 = 0xFFFFFFFF
LN2 = math.log(2.0)
LN2_SQUARED = LN2 * LN2

bit_count = 0
hash_count = 0
capacity = 0
target_fp = 0.0
bits = []
added_count = 0
probe_count = 0
false_positive_count = 0
out = []


def rotate_left_32(value, amount):
    value &= MASK32
    return ((value << amount) | (value >> (32 - amount))) & MASK32


def murmur3_32(value, seed):
    """MurmurHash3 x86_32, with arithmetic kept to 32 bits."""
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
    base_a = murmur3_32(value, 0)
    base_b = murmur3_32(value, 0x9747B28C)
    return [
        (base_a + index * base_b) % bit_count
        for index in range(hash_count)
    ]


def add(value):
    global added_count
    for position in positions(value):
        bits[position] = 1
    added_count += 1


def contains(value):
    return all(bits[position] for position in positions(value))


def current_fill():
    return (sum(bits) / bit_count) if bit_count else 0.0


def theoretical_fp():
    if bit_count <= 0 or hash_count <= 0:
        return 0.0
    return (1.0 - math.exp(-hash_count * added_count / bit_count)) ** hash_count


def estimated_keys():
    fill = current_fill()
    if fill >= 1.0:
        return None
    if fill <= 0.0 or hash_count <= 0:
        return 0
    return round(-(bit_count / hash_count) * math.log1p(-fill))


def argument_after_command(line):
    split_at = line.find(" ")
    return line[split_at + 1:].strip() if split_at >= 0 else ""


for raw in sys.stdin:
    line = raw.rstrip("\r\n")
    if not line.strip():
        continue

    parts = line.split()
    command = parts[0]

    if command == "INIT" and len(parts) == 3:
        capacity = int(parts[1])
        target_fp = float(parts[2])
        if capacity <= 0 or not 0.0 < target_fp < 1.0:
            continue

        bit_count = math.ceil(-capacity * math.log(target_fp) / LN2_SQUARED)
        hash_count = max(1, round((bit_count / capacity) * LN2))
        bits = [0] * bit_count
        added_count = 0
        probe_count = 0
        false_positive_count = 0
        out.append(f"OK m={bit_count} k={hash_count}")

    elif command == "ADD" and len(parts) >= 2:
        add(argument_after_command(line))
        out.append("OK")

    elif command == "PROBE" and len(parts) >= 2:
        value = argument_after_command(line)
        probe_count += 1
        if contains(value):
            false_positive_count += 1
        out.append("OK")

    elif command == "LOAD":
        load = added_count / capacity if capacity else 0.0
        out.append(f"{load:.4f}")

    elif command == "FILL":
        out.append(f"{current_fill():.4f}")

    elif command == "ACTUAL_FP":
        measured = false_positive_count / probe_count if probe_count else 0.0
        out.append(f"{measured:.4f}")

    elif command == "THEORETICAL_FP":
        out.append(f"{theoretical_fp():.4f}")

    elif command == "ESTIMATE":
        estimate = estimated_keys()
        out.append("FULL" if estimate is None else str(estimate))

    elif command == "HEALTHY":
        reasons = []
        load = added_count / capacity if capacity else 0.0
        if load > 1.0:
            reasons.append("OVER_CAPACITY")
        measured = false_positive_count / probe_count if probe_count else 0.0
        if probe_count >= 10 and measured > 2.0 * target_fp:
            reasons.append("FP_TOO_HIGH")
        if not reasons:
            out.append("HEALTHY")
        elif len(reasons) == 1:
            out.append(f"DEGRADED {reasons[0]}")
        else:
            out.append("DEGRADED " + ",".join(reasons))

sys.stdout.write("\n".join(out) + ("\n" if out else ""))
