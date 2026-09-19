import sys
import math as math

# A basic Bloom filter with two hand-computable hashes.
# Parameters fixed: m = 64 bits, k = 2 hash functions.

m = 64
k = 2
bits = [0] * m

def h1(s):
    # TODO: return sum of bytes mod m
    bytes_s = s.encode('utf-8')
    byte_sum = sum(bytes_s)
    return byte_sum%m

def h2(s):
    # TODO: return sum of (byte * (position+1)) mod m
    #   for "apple"  ->  97*1 + 112*2 + 112*3 + 108*4 + 101*5  mod 64
    i = 0
    total_sum = 0
    for position, char_byte in enumerate(s.encode('utf-8')):
        total_sum += (char_byte * (position + 1))
    return total_sum%m
def optimal(p, n):
    n = int(n)
    p = float(p)
    m_opt = math.ceil((-n) * math.log(p) / (math.log(2)**2))
    k_opt = round((m_opt/n) * math.log(2))
    print(f"m={m_opt} k={k_opt}")
    return

def fp(m, n , k) :

    return (1 - math.exp(-k*n/m))**k

def bpi(target_fp):
    target_fp = float(target_fp)
    return -(math.log(target_fp)/(math.log(2)**2))

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
        # TODO: set bits[h1(arg)] and bits[h2(arg)] to 1, then output "OK"
        bits[h1(arg1)] = 1
        bits[h2(arg1)] = 1
        print("OK")
        pass
    elif cmd == "CHECK":
        # TODO: if BOTH bits are 1, output "MAYBE"; otherwise output "NO"
        if(bits[h1(arg1)] == 1 and bits[h2(arg1)] == 1):
            print("MAYBE")
        else: print("NO")
        pass
    elif cmd == "BITS":
        # TODO: output the bit array as a 64-character string
        print(*bits, sep="")
        pass
    elif cmd == "OPTIMAL":
        # print("fp" ,arg1, sep="")
        # print("n:",arg2)
        optimal(arg1, arg2)
        pass
    elif cmd == "FP":
        print(math.trunc(fp(int(arg1), int(arg2), int(arg3))*1_000_000)/1_000_000)
        pass
    elif cmd == "BPI":
        print((math.ceil(bpi(arg1)*10000))/10000)
        pass


sys.stdout.write("\n".join(out) + "\n")
