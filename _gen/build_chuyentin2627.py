#!/usr/bin/env python3
"""Build the 'Chuyen tin 2026-2027 — Kiem tra 03/06/2026' contest.

6 problems, each 20 tests / 2 subtasks (10+10, weighted 50/50 via per-case
points). All stdin/stdout (NO file IO, no freopen). New problems are hidden
(is_public=False); Bai 1 reuses the existing public arr_maxprod (data
regenerated). Contest is org-private to 'Chuyen tin 2026-2027', visible,
max_submissions=1 per problem, partial subtask scoring.

Run: /home/dana/dmojsite/bin/python manage.py shell -c "exec(open('_gen/build_chuyentin2627.py').read())"
"""
import os
import random
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from judge.models import (Contest, ContestProblem, Language, Organization,
                          Problem, ProblemData, ProblemGroup, ProblemTestCase,
                          ProblemType, Profile)
from judge.utils.problem_data import ProblemDataCompiler

random.seed(20260603)
ROOT = "/home/dana/online-judge/problems"
LANGS = ["C", "CPP17", "CPP20", "JAVA8", "PY3"]


# ============================================================ generators
# Each returns [subtask1, subtask2]; each subtask is a list of (inp, out) str.

def g_tichmax():
    def out(a, b, c):
        return str(max(a * b, b * c, c * a))
    st1 = [(2, 4, 6), (1, 2, -3), (1, 1, 1), (10, 5, 3), (100, 100, 100),
           (7, 2, 9), (-8, 4, -2), (50, 50, 1), (-9, -9, -9), (20, 10, 30)]
    st2 = [(-10**9, -10**9, 1), (10**9, 10**9, 10**9), (-5, -6, -7),
           (0, 0, 0), (-10**9, 10**9, 0), (10**9, -10**9, 10**9),
           (-3, 4, -5), (0, -7, 8), (-1, -1, -1), (123456789, 987654321, -500000000)]
    f = lambda t: ("%d %d %d" % t, out(*t))
    return [[f(t) for t in st1], [f(t) for t in st2]]


def g_sum2max():
    def out(n):
        ds = sorted(str(n), reverse=True)
        return str(int(ds[0]) + int(ds[1]))
    st1 = [16, 99, 10, 45, 88, 23, 100, 57, 31, 64]
    st2 = [2402, 999999999, 1000000000, 123456789, 100000000,
           555555555, 987654321, 102030405, 900000009, 246813579]
    f = lambda n: (str(n), out(n))
    return [[f(n) for n in st1], [f(n) for n in st2]]


def g_leap():
    def out(y):
        if not (0 < y <= 100000):
            return "INVALID"
        if (y % 4 == 0 and y % 100 != 0) or y % 400 == 0:
            return "YES"
        return "NO"
    st1 = [2020, 2021, 2000, 1900, 2400, 1, 4, 100, 2024, 99999]
    st2 = [0, -4, 100000, 100001, -2020, 2147483647, -1, 1000000, 200, -100]
    f = lambda y: (str(y), out(y))
    return [[f(y) for y in st1], [f(y) for y in st2]]


def g_replace():
    def out(ns):
        return "\n".join(s.replace("0", "5") for s in ns)
    def inp(ns):
        return str(len(ns)) + "\n" + "\n".join(ns)
    def rnd_block(T, hi):
        return [str(random.randint(0, hi)) for _ in range(T)]
    # subtask 1: T <= 100, n <= 1e6  (first case = the worked example)
    st1 = [["1005", "1234"]]
    for T in (1, 5, 10, 20, 35, 50, 70, 90, 100):
        st1.append(rnd_block(T, 10**6))
    # subtask 2: T up to 1e5, n up to 1e12 (incl. n=0 edge + a big stress case)
    st2 = [["0", "10", "100", "1000", "10000"]]
    for T in (200, 500, 1000, 2000, 5000, 10000, 30000, 70000):
        st2.append(rnd_block(T, 10**12))
    st2.append(rnd_block(100000, 10**12))      # stress: max T
    f = lambda ns: (inp(ns), out(ns))
    return [[f(ns) for ns in st1], [f(ns) for ns in st2]]


def g_age():
    def out(a, b):
        x = a - 2 * b
        return str(x if x >= 0 else -1)
    st1 = [(40, 10), (30, 20), (100, 40), (50, 25), (60, 20),
           (21, 10), (99, 50), (10, 4), (80, 30), (45, 20)]
    st2 = [(10**9, 1), (10**9, 600000000), (999999999, 500000000),
           (10**9, 400000000), (123456789, 60000000), (10**9, 500000000),
           (10**9, 499999999), (777777777, 100000000), (888888888, 500000000),
           (10**9, 999999999)]
    f = lambda t: ("%d %d" % t, out(*t))
    return [[f(t) for t in st1], [f(t) for t in st2]]


def g_prime():
    LIMIT = 1300010
    sieve = bytearray([1]) * (LIMIT + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, int(LIMIT ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = bytearray(len(sieve[i * i::i]))
    primes = [i for i in range(2, LIMIT + 1) if sieve[i]]
    def out(n):
        return str(primes[n - 1])          # 1-indexed
    st1 = [1, 2, 3, 7, 10, 25, 100, 168, 500, 1000]
    st2 = [1500, 5000, 9999, 25000, 50000, 75000, 88888, 99998, 99999, 60000]
    f = lambda n: (str(n), out(n))
    return [[f(n) for n in st1], [f(n) for n in st2]]


# ============================================================ statements
S_TICHMAX = r"""Cho ba số nguyên $A, B, C$. Hãy in ra số lớn nhất trong ba số $A \cdot B$, $B \cdot C$, $C \cdot A$.

## Dữ liệu
- Một dòng duy nhất gồm ba số nguyên $A, B, C$ ($-10^9 \le A, B, C \le 10^9$).

## Kết quả
- Một dòng duy nhất gồm kết quả bài toán.

## Ràng buộc
- Subtask 1 ($50\%$ số điểm): $|A|, |B|, |C| \le 1000$.
- Subtask 2 ($50\%$ số điểm): $-10^9 \le A, B, C \le 10^9$.

## Ví dụ
| Input | Output |
|---|---|
| `2 4 6` | `24` |
| `1 2 -3` | `2` |
"""

S_SUM2MAX = r"""Cho một số nguyên dương $N$ có ít nhất $2$ chữ số. Hãy tính tổng hai chữ số lớn nhất của $N$.

## Dữ liệu
- Một dòng duy nhất gồm một số nguyên dương $N$ ($10 \le N \le 10^9$).

## Kết quả
- Một dòng duy nhất gồm tổng hai chữ số lớn nhất của $N$.

## Ràng buộc
- Subtask 1 ($50\%$ số điểm): $10 \le N \le 100$.
- Subtask 2 ($50\%$ số điểm): $10 \le N \le 10^9$.

## Ví dụ
| Input | Output |
|---|---|
| `16` | `7` |
| `2402` | `6` |
"""

S_LEAP = r"""Trái Đất của chúng ta cần $365.25$ ngày để quay hết một vòng quanh mặt trời. Phần dư $0.25$ thực ra đã làm tròn, con số thực tế là $365.2425$ ngày. Do đó, để lịch của ta chính xác, các chu kỳ $100, 200$ và $300$ chỉ có $24$ năm nhuận thay vì $25$; riêng chu kỳ thứ $400$ sẽ có $25$ năm nhuận. Như vậy, cứ $400$ năm sẽ có $97$ năm nhuận.

Hãy viết chương trình kiểm tra giá trị nguyên $year$ nhập vào có phải là năm nhuận không (theo dương lịch).

**Lưu ý**: Giá trị năm $year$ được coi là hợp lệ nếu $0 < year \le 100000$. Bộ test của đề bài có thể nằm ngoài giới hạn hợp lệ này, hãy chú ý kiểm tra kỹ.

## Dữ liệu
- Một số nguyên $year$ là giá trị cần kiểm tra.

## Kết quả
- Nếu $year$ là năm nhuận, in ra `YES`.
- Nếu $year$ là năm không nhuận, in ra `NO`.
- Nếu giá trị $year$ không hợp lệ, in ra `INVALID`.

## Ràng buộc
- Subtask 1 ($50\%$ số điểm): $year$ luôn hợp lệ ($0 < year \le 100000$).
- Subtask 2 ($50\%$ số điểm): $year$ có thể không hợp lệ.

## Ví dụ
| Input | Output |
|---|---|
| `2020` | `YES` |
"""

S_REPLACE = r"""Cho số nguyên $n$, hãy thay thế tất cả các chữ số $0$ trong biểu diễn thập phân của $n$ thành chữ số $5$ và in ra kết quả.

Ví dụ: với $n = 1005$ thì sau khi thực hiện thay thế ta thu được số $1555$. Còn với $n = 1234$, không có chữ số nào bị thay thế và kết quả vẫn là số $1234$.

## Dữ liệu
- Dòng đầu tiên chứa số nguyên $T$ — số bộ dữ liệu cần kiểm tra.
- $T$ dòng tiếp theo, mỗi dòng chứa một số nguyên $n$.

## Kết quả
- Ứng với mỗi bộ dữ liệu, in ra số $n$ sau khi thay thế, mỗi kết quả trên một dòng.

## Ràng buộc
- $1 \le T \le 10^5$; $0 \le n \le 10^{12}$.
- Subtask 1 ($50\%$ số điểm): $T \le 100$; $n \le 10^6$.
- Subtask 2 ($50\%$ số điểm): $T \le 10^5$; $n \le 10^{12}$.

## Ví dụ
| Input | Output |
|---|---|
| `2`<br>`1005`<br>`1234` | `1555`<br>`1234` |
"""

S_AGE = r"""Cho tuổi của cha là $a$ và tuổi của con là $b$ ($a > b$). Hãy cho biết **sau bao nhiêu năm nữa** thì tuổi cha bằng đúng **hai lần** tuổi con. Nếu không tìm thấy, in ra $-1$.

Gọi $x$ là số năm cần tìm, ta có $a + x = 2 \cdot (b + x)$, suy ra $x = a - 2b$. Nếu $x \ge 0$ thì đáp án là $x$, ngược lại in ra $-1$.

## Dữ liệu
- Một dòng duy nhất gồm hai số nguyên dương $a$ và $b$ ($1 \le b < a \le 10^9$), cách nhau một dấu cách.

## Kết quả
- Một dòng duy nhất gồm số năm cần tìm, hoặc $-1$ nếu không tồn tại.

## Ràng buộc
- Subtask 1 ($50\%$ số điểm): $a, b \le 100$.
- Subtask 2 ($50\%$ số điểm): $a, b \le 10^9$.

## Ví dụ
| Input | Output |
|---|---|
| `40 10` | `20` |
| `30 20` | `-1` |

Với ví dụ thứ nhất: sau $20$ năm, cha $60$ tuổi và con $30$ tuổi, đúng gấp đôi. Với ví dụ thứ hai: không có thời điểm nào trong tương lai thỏa mãn nên in ra $-1$.
"""

S_PRIME = r"""Cho dãy số nguyên tố $Prime = (2, 3, 5, 7, 11, 13, \ldots)$. Hãy in ra số nguyên tố thứ $n$ trong dãy này.

## Dữ liệu
- Một dòng duy nhất gồm số nguyên dương $n$ ($1 \le n < 10^5$).

## Kết quả
- Một dòng duy nhất gồm số nguyên tố thứ $n$ trong dãy $Prime$.

## Ràng buộc
- Subtask 1 ($50\%$ số điểm): $n \le 1000$.
- Subtask 2 ($50\%$ số điểm): $n < 10^5$.

## Ví dụ
| Input | Output |
|---|---|
| `7` | `17` |
"""

# (code, name, statement_or_None, generator, is_public)
# statement None => keep existing (Bai 1 reuses arr_maxprod's current statement)
PROBLEMS = [
    ("ct2627_tichmax", "Tích lớn nhất trong 3 số", S_TICHMAX, g_tichmax, False),
    ("ct2627_sum2max", "Tổng 2 chữ số lớn nhất", S_SUM2MAX, g_sum2max, False),
    ("ct2627_leap", "Kiểm tra năm nhuận", S_LEAP, g_leap, False),
    ("ct2627_replace", "Thay chữ số", S_REPLACE, g_replace, False),
    ("ct2627_age", "Tuổi cha con", S_AGE, g_age, False),
    ("ct2627_prime", "Prime", S_PRIME, g_prime, False),
]

POINTS = 100               # Problem.points (contest overrides via ContestProblem)
TL = 2.0                   # seconds (lenient for Python)
ML = 262144                # 256 MB


def write_case(code, idx, inp, out):
    d = os.path.join(ROOT, code)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "%02d.in" % idx), "w") as f:
        f.write(inp if inp.endswith("\n") else inp + "\n")
    with open(os.path.join(d, "%02d.out" % idx), "w") as f:
        f.write(out if out.endswith("\n") else out + "\n")


def build():
    group = ProblemGroup.objects.get(name="LV0")
    uncat = ProblemType.objects.get(name="uncategorized")
    langs = list(Language.objects.filter(key__in=LANGS))
    admin = Profile.objects.get(user__username="admin")
    antony = Profile.objects.get(user__username="antony")
    assert len(langs) == len(LANGS), langs

    with transaction.atomic():
        problem_objs = []
        for code, name, statement, gen, is_public in PROBLEMS:
            subtasks = gen()
            assert len(subtasks) == 2 and all(len(s) == 10 for s in subtasks), code

            p, created = Problem.objects.get_or_create(code=code, defaults={
                "name": name, "time_limit": TL, "memory_limit": ML,
                "points": POINTS, "partial": True})
            p.name = name
            if statement is not None:           # new problem -> set statement
                p.description = statement
            p.time_limit = TL
            p.memory_limit = ML
            p.points = POINTS
            p.partial = True
            p.short_circuit = False
            p.is_public = is_public
            p.is_manually_managed = False
            p.group = group
            p.save()
            if statement is not None:            # only touch types on new ones
                p.types.set([uncat])
            p.allowed_languages.set(langs)
            if not p.authors.exists():
                p.authors.set([admin])

            # ---- write loose test files (clean stale ones first)
            d = os.path.join(ROOT, code)
            os.makedirs(d, exist_ok=True)
            for fn in os.listdir(d):
                if fn.endswith(".in") or fn.endswith(".out") or fn == "init.yml":
                    os.remove(os.path.join(d, fn))
            idx = 1
            for sub in subtasks:
                for inp, out in sub:
                    write_case(code, idx, inp, out)
                    idx += 1

            # ---- ProblemData + batched ProblemTestCase rows (10pts each subtask)
            data, _ = ProblemData.objects.get_or_create(problem=p)
            data.zipfile = None
            data.fileio_input = None
            data.fileio_output = None
            data.checker = "standard"
            data.save()

            p.cases.all().delete()
            files = []
            order = 0
            n = 1
            for si in range(2):                  # 2 subtasks
                ncase = len(subtasks[si])        # 10
                ProblemTestCase.objects.create(
                    dataset=p, order=order, type="S",
                    points=ncase, is_pretest=False)   # batch header (50/50)
                order += 1
                for _ in range(ncase):
                    infile, outfile = "%02d.in" % n, "%02d.out" % n
                    ProblemTestCase.objects.create(
                        dataset=p, order=order, type="C",
                        input_file=infile, output_file=outfile,
                        points=1, is_pretest=False)
                    order += 1
                    files.extend([infile, outfile])
                    n += 1
                ProblemTestCase.objects.create(
                    dataset=p, order=order, type="E", is_pretest=False)
                order += 1

            ProblemDataCompiler.generate(p, data, p.cases.order_by("order"), files)
            problem_objs.append(p)
            print("%-16s created=%-5s public=%-5s cases=%d" % (
                code, created, is_public, p.cases.filter(type="C").count()))

        # ---------------------------------------------------- contest
        org = Organization.objects.get(slug="chuyentin2627")
        start = timezone.make_aware(datetime(2026, 6, 3, 19, 20, 0))
        end = timezone.make_aware(datetime(2026, 6, 3, 20, 50, 0))

        c, ccreated = Contest.objects.get_or_create(
            key="chuyentin2627_kt0306", defaults={
                "name": "Chuyên tin 2026-2027 — Kiểm tra 03/06/2026",
                "start_time": start, "end_time": end})
        c.name = "Chuyên tin 2026-2027 — Kiểm tra 03/06/2026"
        c.start_time = start
        c.end_time = end
        c.description = ""
        c.format_name = "default"
        c.format_config = None
        c.scoreboard_visibility = "C"      # hidden during contest (matches Koddy)
        c.is_visible = True
        c.is_rated = False
        c.is_organization_private = True
        c.is_private = False
        c.use_clarifications = True
        c.hide_problem_tags = True
        c.public_scoreboard = False
        c.run_pretests_only = False
        c.points_precision = 2
        c.is_in_course = False
        c.save()
        c.organizations.set([org])
        c.authors.set([antony, admin])

        # contest point values: all 100, except prime = 150
        CONTEST_POINTS = {"ct2627_prime": 150}
        c.contest_problems.all().delete()
        for i, p in enumerate(problem_objs, start=1):
            ContestProblem.objects.create(
                contest=c, problem=p, points=CONTEST_POINTS.get(p.code, 100),
                partial=True, is_pretested=False, order=i, max_submissions=1)

        print("\nContest %s created=%s" % (c.key, ccreated))
        print("  window:", start, "->", end)
        print("  orgs:", list(c.organizations.values_list("slug", flat=True)))
        print("  problems:", [cp.problem.code for cp in c.contest_problems.order_by("order")])
    print("DONE")


build()
