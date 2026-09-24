import sys
import math as math

# A basic Bloom filter with two hand-computable hashes.
# Parameters fixed: m = 64 bits, k = 2 hash functions.

m = 0
k = 0
bits = []
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

def h_a(s): 
    #TODO
    total_sum = 0
    for position, char_byte in enumerate(s.encode('utf-8')):
        total_sum += (char_byte * (position + 1))
    
    return total_sum

def h_b(s):
    #TODO
    total_sum = 0
    for position, char_byte in enumerate(s.encode('utf-8')):
        total_sum += (char_byte ^ (position + 1))
    return total_sum

def hash(s, m, k):
    m = int(m)
    k = int(k)

    positions = []

    ha = h_a(s)
    hb = h_b(s)

    for i in range(k):
        pi = (ha + i * hb) % m
        positions.append(pi)

    return positions


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

    if cmd == "ADD":
        pos = hash(arg1, m, k)

        for pi in pos:
            bits[pi] = 1

        n_added += 1
        load = n_added / expected_n

        print("OK")
        pass
    elif cmd == "CHECK":
        # TODO: if all bits are 1, output "MAYBE"; otherwise output "NO"
        pos = hash(arg1, m, k)

        if all(bits[pi] == 1 for pi in pos):
            print("MAYBE")
        else:
            print("NO")
        pass
    elif cmd == "BITS":
        # TODO: output the bit array as a 64-character string
        print(*bits, sep="")
        pass
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
    elif cmd == "INIT":
        expected_n = int(arg1)

        m, k = optimal(arg2, arg1)

        bits = [0] * m

        n_added = 0
        load = 0

        print(f"OK m={m} k={k}")
        pass
    elif cmd =="STATS":
        print(f"m={m} k={k} n={n_added} load={load:.4f}")
        pass


sys.stdout.write("\n".join(out) + "\n")
