import sys
import math as math

# A basic Bloom filter with two hand-computable hashes.
# Parameters fixed: m = 64 bits, k = 2 hash functions.

m = 0
k = 0
bits = []
a = []
b = []
u = []
i = []
n_added = 0
expected_n = 0
load = 0

def h1(s):
    # TODO: return sum of bytes mod m
    bytes_s = s.encode('utf-8')
    byte_sum = sum(bytes_s)
    return byte_sum%m

def h2(s):
    # TODO: return sum of (byte * (position+1)) mod m
    #   for "apple"  ->  97*1 + 112*2 + 112*3 + 108*4 + 101*5  mod 64
    total_sum = 0
    for position, char_byte in enumerate(s.encode('utf-8')):
        total_sum += (char_byte * (position + 1))
    return total_sum%m
def optimal(p, n):
    n = int(n)
    p = float(p)

    m_opt = math.ceil((-n) * math.log(p) / (math.log(2) ** 2))
    k_opt = round((m_opt / n) * math.log(2))

    return m_opt, k_opt

def fp(m, n , k) :

    return (1 - math.exp(-k*n/m))**k

def bpi(target_fp):
    target_fp = float(target_fp)
    return -(math.log(target_fp)/(math.log(2)**2))

# Kirsch-Mitzenmacher: derive K hashes from just TWO base hashes.
#   h_i(x) = (h_a(x) + i * h_b(x)) mod m       for i = 0..k-1
#
# Base hashes (kept simple so you can hand-trace):
#   h_a(s) = sum_i (byte_i * (i+1))   mask to 32 bits
#   h_b(s) = sum_i (byte_i XOR (i+1)) mask to 32 bits
#
# Commands:
#   HASH <s> <m> <k>   -> k positions, comma-separated, e.g. "94,19,44,69,94"
#   HA   <s>           -> just h_a(s)
#   HB   <s>           -> just h_b(s)


def h_a(s): return sum(b * (i + 1) for i, b in enumerate(s.encode())) & 0xFFFFFFFF 
    # total_sum = 0
    # for position, char_byte in enumerate(s.encode('utf-8')):
    #     total_sum += (char_byte * (position + 1))
    
    # return total_sum

def h_b(s): return sum(b ^ (i + 1) for i, b in enumerate(s.encode())) & 0xFFFFFFFF
    # total_sum = 0
    # for position, char_byte in enumerate(s.encode('utf-8')):
    #     total_sum += (char_byte ^ (position + 1))
    # return total_sum

def positions(s, m, k):
    return [(h_a(s) + i * h_b(s)) % m for i in range(k)]
    # m = int(m)
    # k = int(k)

    # positions = []

    # ha = h_a(s)
    # hb = h_b(s)

    # for i in range(k):
    #     pi = (ha + i * hb) % m
    #     positions.append(pi)

    # return positions


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

def union(u, a, b) :
    filters[u] = [x|y for x,y in zip(a,b)]
def intersection(i, a, b) : 
    filters[i] = [x & y for x, y in zip(a, b)]


def bloom_positions(s, m):
    return [h1(s), h2(s)]
filters = {}

def get_filter(name):
    return filters.get(name)

def compatible(a, b):
    return a["m"] == b["m"] and a["k"] == b["k"]

def add(name, s):
    f = get_filter(name)
    if f is None:
        print("ERR NOFILTER")
        return

    for p in positions(s, f["m"], f["k"]):
        f["bits"][p] = 1
    print("OK")

def check(name, s):
    f = get_filter(name)
    if f is None:
        print("ERR NOFILTER")
        return

    pos = positions(s, f["m"], f["k"])
    print("MAYBE" if all(f["bits"][p] for p in pos) else "NO")

def combine(out_name, a_name, b_name, operation):
    a = get_filter(a_name)
    b = get_filter(b_name)

    if a is None or b is None:
        print("ERR NOFILTER")
        return

    if not compatible(a, b):
        print("ERR MISMATCH")
        return

    if operation == "UNION":
        bits = [x | y for x, y in zip(a["bits"], b["bits"])]
    else:
        bits = [x & y for x, y in zip(a["bits"], b["bits"])]

    filters[out_name] = {
        "m": a["m"],
        "k": a["k"],
        "bits": bits
    }
    print("OK")

def popcount(name):
    f = get_filter(name)
    if f is None:
        print("ERR NOFILTER")
        return
    print(sum(f["bits"]))

out = []
for raw in sys.stdin:
    line = raw.rstrip("\n")
    if not line:
        continue
    parts = line.split(" ")
    # print("parts : "+ parts)
    cmd = parts[0]
    # print(parts)
    arg1 = parts[1] if len(parts) > 1 else ""
    arg2 = parts[2] if len(parts) > 2 else ""
    arg3 = parts[3] if len(parts) > 3 else ""

    
    if cmd == "INIT":
        name = arg1
        m_value = int(arg2)
        k_value = int(arg3)

        filters[name] = {
            "m": m_value,
            "k": k_value,
            "bits": [0] * m_value
        }
        print("OK")

    elif cmd == "ADD":
        add(arg1, arg2)

    elif cmd == "CHECK":
        check(arg1, arg2)

    elif cmd == "UNION":
        combine(arg1, arg2, arg3, "UNION")

    elif cmd == "INTERSECT":
        combine(arg1, arg2, arg3, "INTERSECT")

    elif cmd == "POPCOUNT":
        popcount(arg1)

    elif cmd == "BITS":
        f = get_filter(arg1)
        if f is None:
            print("ERR NOFILTER")
        else:
            print("".join(map(str, f["bits"])))
    elif cmd == "OPTIMAL":
        # print("fp" ,arg1, sep="")
        # print("n:",arg2)
        m,k = optimal(arg1, arg2)
        print(f"m={m} k={k}")
        pass
    elif cmd == "FP":
        # Calculate the raw false positive rate
        fp_rate = fp(int(arg1), int(arg2), int(arg3))
        # Print using an f-string formatted to exactly 6 decimal places
        print(f"{fp_rate:.6f}")
        pass
    elif cmd == "BPI":
        # Calculate the raw BPI value
        bpi_rate = bpi(float(arg1))

        # Print with standard rounding to exactly 4 decimal places
        print(f"{bpi_rate:.4f}")
        pass
    elif cmd == "HASH":
        #derive k positions and join with comma
        pos = hash(arg1, arg2, arg3)
        print(*pos, sep=",")
        pass
    elif cmd == "HA" :
        print(h_a(arg1))
        pass
    elif cmd == "HB" : 
        print(h_b(arg1))
        pass
    elif cmd =="STATS":
        print(f"m={m} k={k} n={n_added} load={load:.4f}")
        pass
 #to implement  --
 # -union/intersection
 # - counting bloom filter
 # - scalable bloom filter
 # - Cuckoo filter
sys.stdout.write("\n".join(out) + "\n")
