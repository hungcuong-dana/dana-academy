#!/usr/bin/env python3
"""Generate test data for 4 string problems (Bai 9-12) of contest onthinbk_xau.
Writes loose NN.in / NN.out files into problems/<code>/ and prints a batch manifest.
Run with system python3 (no Django needed)."""
import os, random, sys

random.seed(20260520)
ROOT = "/home/dana/online-judge/problems"

# ---------------------------------------------------------------- solvers
def sol_rutgon(s):
    out = []
    for ch in s:
        if not out or out[-1] != ch:
            out.append(ch)
    return "".join(out)

def sol_kitu(n, k, s):
    from collections import Counter
    c = Counter(s)
    res = "".join(ch for ch in sorted(c) if c[ch] >= k)
    return res if res else "0"

def _longest_pos_subarray(arr):
    # longest subarray with sum > 0  (LeetCode 1124 technique)
    n = len(arr)
    pre = [0]*(n+1)
    for i in range(n):
        pre[i+1] = pre[i] + arr[i]
    stack = []
    for i in range(n+1):
        if not stack or pre[stack[-1]] > pre[i]:
            stack.append(i)
    ans = 0
    j = n
    while j >= 0:
        while stack and pre[stack[-1]] < pre[j]:
            if j - stack[-1] > ans:
                ans = j - stack[-1]
            stack.pop()
        j -= 1
    return ans

def sol_tanso(s):
    best = 0
    for c in set(s):
        arr = [1 if ch == c else -1 for ch in s]
        v = _longest_pos_subarray(arr)
        if v > best:
            best = v
    return best

def sol_tanso_brute(s):
    n = len(s)
    best = 0
    for i in range(n):
        cnt = {}
        mx = 0
        for j in range(i, n):
            cnt[s[j]] = cnt.get(s[j], 0) + 1
            if cnt[s[j]] > mx:
                mx = cnt[s[j]]
            length = j - i + 1
            if mx * 2 > length:        # strict majority
                if length > best:
                    best = length
    return best

def sol_daoxau(s, ks):
    n = len(s)
    half = n // 2
    diff = [0]*(half + 2)
    for k in ks:
        L = n + 1 - k          # 1-indexed left boundary of reflected segment
        if 1 <= L <= half:
            diff[L] += 1
        elif L < 1:
            diff[1] += 1
        # L > half  -> only centre touched, no effect
    a = list(s)
    run = 0
    for i in range(1, half + 1):
        run += diff[i]
        if run & 1:
            a[i-1], a[n-i] = a[n-i], a[i-1]
    return "".join(a)

def sol_daoxau_brute(s, ks):
    a = list(s)
    n = len(a)
    for k in ks:
        L = n - k            # 0-indexed left
        R = k - 1            # 0-indexed right
        a[L:R+1] = a[L:R+1][::-1]
    return "".join(a)

# ---------------------------------------------------------------- helpers
def rand_lower(n, alpha="abcdefghijklmnopqrstuvwxyz"):
    return "".join(random.choice(alpha) for _ in range(n))

def rand_upper(n):
    return "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(n))

def rand_runs(total, alpha, max_run):
    out = []
    while len(out) < total:
        ch = random.choice(alpha)
        r = random.randint(1, max_run)
        out.extend([ch]*min(r, total-len(out)))
    return "".join(out)

def write_case(code, idx, inp, out):
    d = os.path.join(ROOT, code)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "%02d.in" % idx), "w") as f:
        f.write(inp)
    with open(os.path.join(d, "%02d.out" % idx), "w") as f:
        f.write(out if out.endswith("\n") else out + "\n")

# ================================================================ RUTGON
def gen_rutgon():
    code = "rutgon"
    cases = []  # (inp_string)
    low = "abcdefghijklmnopqrstuvwxyz"
    # ST1: len 2..20  (10 tests)
    st1 = ["aa", "ab", "aaaaaaaaaaaaaaaaaaaa", "abababababababab",
           "aaabbbaac", "xxyyzzx", "abcde", "zzzaaazzz",
           rand_runs(20, "abc", 4), rand_runs(15, low, 3)]
    # ST2: len up to ~120 (10 tests)
    st2 = [rand_runs(random.randint(40, 120), "abcde", 5) for _ in range(7)]
    st2 += ["q"*120, rand_runs(120, low, 1), rand_runs(120, "ab", 8)]
    # ST3: len up to 250 (10 tests)
    st3 = ["m"*250,                                   # all same -> 1 char
           rand_runs(250, low, 1),                    # no consecutive dup -> unchanged
           "ab"*125,                                  # alternating
           rand_runs(250, "abc", 10),
           rand_runs(250, low, 6),
           rand_runs(249, "abcdef", 4),
           rand_runs(250, "ab", 12),
           rand_runs(248, low, 2),
           rand_runs(250, "xyz", 9),
           rand_runs(250, low, 25)]
    groups = [("ST1 len<=20", 30, st1), ("ST2 len<=120", 30, st2), ("ST3 len<=250", 40, st3)]
    return code, groups, lambda inp: sol_rutgon(inp)

# ================================================================ KITU
def gen_kitu():
    code = "kitu"
    def mk(n, k):
        s = rand_upper(n)
        return "%d %d\n%s\n" % (n, k, s), (n, k, s)
    cases_meta = []
    # ST1: 1<=k<=n<100 (10)
    st1_raw = [(10, 3, "CABADDABDD"),               # sample
               (5, 1, "AAAAA"),
               (26, 1, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
               (50, 49, rand_upper(50)),            # likely "0"
               (99, 2, rand_upper(99)),
               (60, 5, rand_upper(60)),
               (30, 10, ("AB"*15)),                 # A15 B15
               (40, 40, "A"*40),
               (8, 3, "AABBBCCC"),
               (99, 99, rand_upper(99))]
    # ST2: 100<=k<=n<10^4 (10)
    st2_raw = []
    for _ in range(8):
        n = random.randint(1000, 9999)
        k = random.randint(100, n)
        st2_raw.append((n, k, rand_upper(n)))
    st2_raw.append((9999, 100, rand_upper(9999)))
    st2_raw.append((5000, 5000, "Z"*5000))
    # ST3: 10^4<=k<=n<=10^6 (10)
    st3_raw = []
    for _ in range(7):
        n = random.randint(100000, 1000000)
        k = random.randint(10000, n)
        st3_raw.append((n, k, rand_upper(n)))
    st3_raw.append((1000000, 10000, rand_upper(1000000)))
    st3_raw.append((1000000, 1000000, "A"*1000000))  # answer A
    st3_raw.append((500000, 499999, rand_upper(500000)))
    def fmt(t):
        n, k, s = t
        return "%d %d\n%s\n" % (n, k, s)
    groups = [("ST1 n<100", 20, [fmt(t) for t in st1_raw]),
              ("ST2 n<1e4", 40, [fmt(t) for t in st2_raw]),
              ("ST3 n<=1e6", 40, [fmt(t) for t in st3_raw])]
    def solve(inp):
        lines = inp.split("\n")
        n, k = map(int, lines[0].split())
        s = lines[1]
        return sol_kitu(n, k, s)
    return code, groups, solve

# ================================================================ TANSO
def gen_tanso():
    code = "tanso"
    # ST1: alphabet abc, len<=2000 (10)
    st1 = ["aaa", "ababab",
           rand_lower(2000, "abc"),
           rand_lower(1999, "abc"),
           "abc"*666,
           "a"*2000,
           rand_runs(2000, "abc", 7),
           rand_lower(500, "abc"),
           "aabbcc"*333,
           rand_lower(1234, "ab")]
    # ST2: a-z, len<=2000 (10)
    st2 = [rand_lower(2000) for _ in range(6)]
    st2 += ["abcdefghijklmnopqrstuvwxyz"*76,
            rand_runs(2000, "abcdefghij", 9),
            "z"*1999,
            rand_lower(1500, "abcde")]
    # ST3: a-z, len<=2e5 (10)
    st3 = [rand_lower(200000) for _ in range(4)]
    st3 += ["a"*200000,
            "ab"*100000,
            rand_runs(200000, "abcdefghijklmnopqrstuvwxyz", 11),
            rand_lower(200000, "abcdefghij"),
            rand_lower(199999),
            rand_runs(200000, "ab", 13)]
    groups = [("ST1 abc<=2000", 30, st1), ("ST2 az<=2000", 30, st2), ("ST3 az<=2e5", 40, st3)]
    return code, groups, lambda s: str(sol_tanso(s))

# ================================================================ DAOXAU
def gen_daoxau():
    code = "daoxau"
    def mk(s, ks):
        return "%s\n%d\n%s\n" % (s, len(ks), " ".join(map(str, ks))), (s, ks)
    def randks(n, m):
        lo = n // 2 + 1
        return [random.randint(lo, n) for _ in range(m)]
    # ST1: n<=1000, m<=1000 (15)
    st1 = []
    st1.append(("abcdef", [5, 6, 4]))   # sample -> fbdcea
    for _ in range(9):
        n = random.randint(2, 1000)
        m = random.randint(1, 1000)
        st1.append((rand_lower(n), randks(n, m)))
    st1.append(("ab", [2]))
    st1.append(("aaaaa", randks(5, 10)))      # all same -> unchanged
    st1.append((rand_lower(1000), randks(1000, 1)))   # single op
    st1.append((rand_lower(999), randks(999, 999)))
    st1.append((rand_lower(7), [7,7,7,4,4,5,6]))
    # ST2: n<=2e5, m<=1e5 (15)
    st2 = []
    for _ in range(9):
        n = random.randint(50000, 200000)
        m = random.randint(50000, 100000)
        st2.append((rand_lower(n), randks(n, m)))
    st2.append(("z"*200000, randks(200000, 100000)))
    st2.append((rand_lower(200000), [200000]*100000))   # full reverse repeated
    st2.append((rand_lower(200000), randks(200000, 1)))
    st2.append((rand_lower(199999), randks(199999, 100000)))
    st2.append((rand_lower(200000), [100001]*100000))   # smallest k repeated (even -> no change)
    st2.append((rand_lower(123456), randks(123456, 100000)))
    groups_raw = [("ST1 n<=1e3,m<=1e3", 50, st1), ("ST2 n<=2e5,m<=1e5", 50, st2)]
    def fmt(t):
        s, ks = t
        return "%s\n%d\n%s\n" % (s, len(ks), " ".join(map(str, ks)))
    groups = [(name, pts, [fmt(t) for t in lst]) for name, pts, lst in groups_raw]
    def solve(inp):
        lines = inp.split("\n")
        s = lines[0]
        m = int(lines[1])
        ks = list(map(int, lines[2].split()))
        assert len(ks) == m
        return sol_daoxau(s, ks)
    return code, groups, solve, groups_raw

# ================================================================ validation
def validate():
    # TANSO: fast vs brute on random small abc / az
    for _ in range(2000):
        n = random.randint(1, 14)
        s = rand_lower(n, random.choice(["abc", "ab", "abcde"]))
        if sol_tanso(s) != sol_tanso_brute(s):
            print("TANSO MISMATCH", repr(s), sol_tanso(s), sol_tanso_brute(s)); sys.exit(1)
    # DAOXAU: fast vs brute
    for _ in range(2000):
        n = random.randint(2, 12)
        s = rand_lower(n)
        m = random.randint(1, 8)
        lo = n // 2 + 1
        ks = [random.randint(lo, n) for _ in range(m)]
        if sol_daoxau(s, ks) != sol_daoxau_brute(s, ks):
            print("DAOXAU MISMATCH", repr(s), ks, sol_daoxau(s, ks), sol_daoxau_brute(s, ks)); sys.exit(1)
    print("validation OK")

# ================================================================ main
def emit(code, groups, solve):
    idx = 1
    manifest = []
    for name, pts, inputs in groups:
        first = idx
        for inp in inputs:
            out = solve(inp)
            write_case(code, idx, inp, out)
            idx += 1
        manifest.append((name, pts, first, idx-1))
    print("== %s : %d tests ==" % (code, idx-1))
    for name, pts, a, b in manifest:
        print("   batch %-22s pts=%-3d cases %02d..%02d" % (name, pts, a, b))
    return manifest

if __name__ == "__main__":
    validate()
    import json
    full = {}
    c, g, s = gen_rutgon();           full["rutgon"] = emit(c, g, s)
    c, g, s = gen_kitu();             full["kitu"] = emit(c, g, s)
    c, g, s = gen_tanso();            full["tanso"] = emit(c, g, s)
    res = gen_daoxau(); c, g, s = res[0], res[1], res[2]; full["daoxau"] = emit(c, g, s)
    with open("/home/dana/online-judge/_gen/manifest.json", "w") as f:
        json.dump(full, f, indent=2)
    print("manifest written")
