#!/usr/bin/env python3
"""Create the Lv0 'Cac bai tap tong hop' (untyped) problems with test data.

These problems carry NO ProblemType (so the roadmap 'other' topic, which filters
types__isnull=True, picks them up) and have DIFFERENT point values. Each: 15
tests / 3 subtasks (5/5/5); per-case points encode 30/30/40 of the total.
Problems are dated in listing order (RoadmapLevelType sorts by date, id).

Run: /home/dana/dmojsite/bin/python manage.py shell -c "exec(open('_gen/build_misc_lv0.py').read())"
"""
import datetime
import math
import os
import random

from django.db import transaction
from django.utils import timezone

from judge.models import (Language, Problem, ProblemData, ProblemGroup,
                          ProblemTestCase, Profile)
from judge.utils.problem_data import ProblemDataCompiler

random.seed(20260529)
ROOT = "/home/dana/online-judge/problems"
LANGS = ["C", "CPP17", "CPP20", "JAVA8", "PY3"]


def percase_for(points):
    # 30/30/40 split over 5/5/5 cases -> integer per-case points
    unit = points // 10                      # 100->10, 200->20, 300->30
    return [unit * 3 // 5, unit * 3 // 5, unit * 4 // 5]  # e.g. 6/6/8, 12/12/16, 18/18/24


# ----------------------------------------------------------------- math utils
def divisor_sum(n):
    if n == 1:
        return 1
    total, m, p = 1, n, 2
    while p * p <= m:
        if m % p == 0:
            pk, s = 1, 1
            while m % p == 0:
                m //= p
                pk *= p
                s += pk
            total *= s
        p += 1 if p == 2 else 2
    if m > 1:
        total *= (1 + m)
    return total


def odd_divisor_count(n):
    while n % 2 == 0:
        n //= 2
    cnt, p = 1, 3
    while p * p <= n:
        if n % p == 0:
            e = 0
            while n % p == 0:
                n //= p
                e += 1
            cnt *= (e + 1)
        p += 2
    if n > 1:
        cnt *= 2
    return cnt


def g2jdn(y, m, d):
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return (d + (153 * mm + 2) // 5 + 365 * yy + yy // 4
            - yy // 100 + yy // 400 - 32045)


def jdn2g(j):
    a = j + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d2 = (4 * c + 3) // 1461
    e = c - (1461 * d2) // 4
    m2 = (5 * e + 2) // 153
    day = e - (153 * m2 + 2) // 5 + 1
    month = m2 + 3 - 12 * (m2 // 10)
    year = 100 * b + d2 - 4800 + m2 // 10
    return day, month, year


def days_in_month(m, y):
    if m == 2:
        return 29 if ((y % 4 == 0 and y % 100 != 0) or y % 400 == 0) else 28
    return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]


def rand_date():
    y = random.randint(1, 2023)
    m = random.randint(1, 12)
    d = random.randint(1, days_in_month(m, y))
    return d, m, y


def rand_word(maxlen=5):
    return "".join(random.choice("abcdefghijklmnopqrstuvwxyz")
                   for _ in range(random.randint(1, maxlen)))


# ----------------------------------------------------------------- generators
def gen_tonguoc():
    st1 = ["10", "1", "1000000", "999983", "720720"]                 # n<=1e6
    st2 = [str(999999937), str(10**9), str(536870912), str(617718022),
           str(923456789)]                                            # n<=1e9
    st3 = [str(10**12), str(549755813888), str(961380175077),
           str(999999999999), str(479001600000)]                     # n<=1e12
    return [st1, st2, st3], (lambda s: str(divisor_sum(int(s))))


def gen_capbangnhau():
    def arr(n, hi):
        a = [random.randint(1, hi) for _ in range(n)]
        return "%d\n%s" % (n, " ".join(map(str, a)))
    st1 = ["5\n1 2 2 1 1", "1\n7", "4\n3 3 3 3",
           arr(50, 10), arr(100, 100)]                               # n<=100
    st2 = [arr(2000, 100), arr(5000, 50), arr(9999, 1000),
           arr(8000, 5), arr(10000, 100000)]                         # n<=1e4
    st3 = [arr(100000, 100000), arr(100000, 5), arr(99999, 1000),
           arr(100000, 1), arr(100000, 50000)]                       # n<=1e5
    def solve(raw):
        lines = raw.split("\n")
        a = list(map(int, lines[1].split())) if lines[1] else []
        from collections import Counter
        return str(sum(c * (c - 1) // 2 for c in Counter(a).values()))
    return [st1, st2, st3], solve


def gen_uclnbcnn():
    def pair(hi):
        return "%d %d" % (random.randint(1, hi), random.randint(1, hi))
    st1 = ["4 6", "1 1", "7 13", "12 18", "100 75"]                  # <=1e3
    st2 = [pair(10**6) for _ in range(5)]                            # <=1e6
    st3 = [pair(10**9) for _ in range(4)] + ["1000000000 999999999"]  # <=1e9
    def solve(s):
        a, b = map(int, s.split())
        g = math.gcd(a, b)
        return "%d %d" % (g, a // g * b)
    return [st1, st2, st3], solve


def gen_so3():
    def arr(n, hi):
        a = [random.randint(1, hi) for _ in range(n)]
        return "%d\n%s" % (n, " ".join(map(str, a)))
    st1 = ["3\n1 2 3", "1\n5", "6\n3 6 9 12 15 18",
           arr(50, 100), arr(100, 1000)]                             # n<=100
    st2 = [arr(2000, 10**9), arr(5000, 100), arr(9999, 3),
           arr(8000, 10**9), arr(10000, 9)]                          # n<=1e4
    st3 = [arr(100000, 10**9), arr(100000, 3), arr(99999, 10),
           arr(100000, 1), arr(100000, 10**9)]                       # n<=1e5
    def solve(raw):
        lines = raw.split("\n")
        a = list(map(int, lines[1].split())) if lines[1] else []
        c = [0, 0, 0]
        for x in a:
            c[x % 3] += 1
        return str(c[0] * (c[0] - 1) // 2 + c[1] * c[2])
    return [st1, st2, st3], solve


def gen_truyvanxau():
    def case(n, q, hit_ratio=0.5):
        names = list({rand_word() for _ in range(n)})
        while len(names) < n:
            names.append(rand_word())
        names = names[:n]
        nameset = names if n else ["a"]
        queries = []
        for _ in range(q):
            if random.random() < hit_ratio and names:
                queries.append(random.choice(names))
            else:
                queries.append(rand_word())
        return "\n".join([str(n)] + names + [str(q)] + queries)
    st1 = ["2\nmaris\nreimu\n4\nmaris\nrei\nreimu\nmio",
           case(5, 5), case(10, 20), case(50, 50), case(100, 100)]   # small
    st2 = [case(2000, 2000), case(5000, 5000), case(1000, 9000),
           case(9000, 1000), case(10000, 10000)]                     # <=1e4
    st3 = [case(50000, 50000), case(100000, 100000), case(150000, 150000),
           case(200000, 200000), case(300000, 300000)]               # large
    def solve(raw):
        lines = raw.split("\n")
        n = int(lines[0])
        names = set(lines[1:1 + n])
        q = int(lines[1 + n])
        qs = lines[2 + n:2 + n + q]
        return "\n".join("YES" if x in names else "NO" for x in qs)
    return [st1, st2, st3], solve


def gen_lientiep():
    st1 = ["12", "1", "15", "16", "999983"]                          # n<=1e6
    st2 = [str(10**9), str(536870912), str(723456789),
           str(999999937), str(645000000)]                           # n<=1e9
    st3 = [str(10**12), str(549755813888), str(961380175077),
           str(999999999999), str(844800000000)]                     # n<=1e12
    return [st1, st2, st3], (lambda s: str(odd_divisor_count(int(s)) - 1))


def gen_ditu():
    def case(xmax):
        d, m, y = rand_date()
        x = random.randint(1, xmax)
        return "%d %d %d %d" % (x, d, m, y)
    st1 = ["5 27 1 2000", "1 31 12 2023", "30 15 6 1999",
           case(1000), case(1000)]                                   # x<=1e3
    st2 = [case(10**9) for _ in range(5)]                            # x<=1e9
    st3 = [case(10**15) for _ in range(4)] + ["1000000000000000 1 1 1"]  # x<=1e15
    def solve(s):
        x, d, m, y = map(int, s.split())
        dd, mm, yy = jdn2g(g2jdn(y, m, d) + x)
        return "%d %d %d" % (dd, mm, yy)
    return [st1, st2, st3], solve


STATEMENTS = {
    "tonguoc": """Tính tổng các ước dương của $n$.

## Input
- Số nguyên $n$.

## Output
- Kết quả bài toán.

## Ràng buộc
- $1 \\le n \\le 10^{12}$.
- Subtask 1 ($30\\%$ số điểm): $n \\le 10^6$.
- Subtask 2 ($30\\%$ số điểm): $n \\le 10^9$.
- Subtask 3 ($40\\%$ số điểm): $n \\le 10^{12}$.

## Ví dụ
| Input | Output |
|---|---|
| `10` | `18` |
""",
    "capbangnhau": """Cho mảng $A$ độ dài $n$. Đếm số cặp $(i, j)$ sao cho $A_i = A_j$ và $i \\ne j$.

## Input
- Dòng đầu tiên gồm số nguyên $n$.
- Dòng tiếp theo gồm $n$ số nguyên $A_i$.

## Output
- In ra một số nguyên là số cặp số bằng nhau.

## Ràng buộc
- $1 \\le n \\le 10^5$.
- $1 \\le A_i \\le 10^5$.
- Subtask 1 ($30\\%$ số điểm): $n \\le 100$.
- Subtask 2 ($30\\%$ số điểm): $n \\le 10^4$.
- Subtask 3 ($40\\%$ số điểm): $n \\le 10^5$.

## Ví dụ
| Input | Output |
|---|---|
| `5`<br>`1 2 2 1 1` | `4` |
""",
    "uclnbcnn": """Tính ước chung lớn nhất (UCLN) và bội chung nhỏ nhất (BCNN) của $a, b$.
- Ước chung lớn nhất của $2$ hay nhiều số nguyên là số nguyên dương lớn nhất là ước số chung của các số đó.
- Bội chung nhỏ nhất của hai số nguyên là số nguyên dương nhỏ nhất chia hết cho cả hai.

## Input
- Dòng đầu gồm $2$ số nguyên dương $a, b$.

## Output
- UCLN và BCNN của $2$ số $a, b$.

## Ràng buộc
- $1 \\le a, b \\le 10^9$.
- Subtask 1 ($30\\%$ số điểm): $a, b \\le 10^3$.
- Subtask 2 ($30\\%$ số điểm): $a, b \\le 10^6$.
- Subtask 3 ($40\\%$ số điểm): $a, b \\le 10^9$.

## Ví dụ
| Input | Output |
|---|---|
| `4 6` | `2 12` |
""",
    "so3": """Cho mảng $A$ gồm $n$ phần tử nguyên, đếm số cặp chỉ số $i < j$ sao cho $A_i + A_j$ chia hết cho $3$.

## Input
- Dòng đầu tiên gồm số nguyên $n$.
- Dòng thứ hai gồm $n$ số nguyên $A_i$.

## Output
- In ra một số nguyên là số lượng cặp chỉ số thỏa mãn.

## Ràng buộc
- $1 \\le n \\le 10^5$.
- $1 \\le A_i \\le 10^9$.
- Subtask 1 ($30\\%$ số điểm): $n \\le 100$.
- Subtask 2 ($30\\%$ số điểm): $n \\le 10^4$.
- Subtask 3 ($40\\%$ số điểm): $n \\le 10^5$.

## Ví dụ
| Input | Output |
|---|---|
| `3`<br>`1 2 3` | `1` |
""",
    "truyvanxau": """Cho $n$ xâu kí tự chỉ gồm chữ in thường, mỗi xâu có độ dài không quá $5$. Cho $q$ truy vấn, mỗi truy vấn là một xâu, hãy xác định xem xâu có tồn tại trong $n$ xâu đã cho ban đầu không.

## Input
- Dòng đầu tiên là số nguyên $n$.
- $n$ dòng tiếp theo, mỗi dòng là một xâu.
- Dòng tiếp theo là số nguyên $q$.
- $q$ dòng tiếp theo, mỗi dòng gồm một xâu, là một truy vấn.

## Output
- Với mỗi truy vấn, nếu xâu tồn tại trong $n$ xâu đã cho, in ra `YES`, ngược lại in ra `NO`.

## Ràng buộc
- $1 \\le n, q \\le 10^6$.
- Xâu chỉ gồm các kí tự in thường.
- Subtask 1 ($30\\%$ số điểm): $n, q \\le 100$.
- Subtask 2 ($30\\%$ số điểm): $n, q \\le 10^4$.
- Subtask 3 ($40\\%$ số điểm): $n, q$ lớn.

## Ví dụ
| Input | Output |
|---|---|
| `2`<br>`maris`<br>`reimu`<br>`4`<br>`maris`<br>`rei`<br>`reimu`<br>`mio` | `YES`<br>`NO`<br>`YES`<br>`NO` |
""",
    "lientiep": """Cho số nguyên $n$. Đếm số cách phân tích $n$ thành ít nhất hai số nguyên dương liên tiếp.

Ví dụ: $12 = 3 + 4 + 5$.

## Input
- Một dòng gồm số nguyên $n$.

## Output
- In ra một số nguyên là số cách phân tích.

## Ràng buộc
- $1 \\le n \\le 10^{12}$.
- Subtask 1 ($30\\%$ số điểm): $n \\le 10^6$.
- Subtask 2 ($30\\%$ số điểm): $n \\le 10^9$.
- Subtask 3 ($40\\%$ số điểm): $n \\le 10^{12}$.

## Ví dụ
| Input | Output |
|---|---|
| `12` | `1` |
""",
    "ditu": """Một phạm nhân lãnh bản án tù $x$ ngày và bắt đầu thời gian thi hành án từ ngày $d$, tháng $m$, năm $y$. Hãy cho biết phạm nhân được ra tù vào ngày nào.

## Input
- Một dòng gồm bốn số nguyên $x, d, m, y$.

## Output
- In ra ba số nguyên là ngày tháng năm mà phạm nhân ra tù.

## Ràng buộc
- Đảm bảo ngày hợp lệ.
- $1 \\le x \\le 10^{15}$.
- $1 \\le y \\le 2023$.
- Subtask 1 ($30\\%$ số điểm): $x \\le 10^3$.
- Subtask 2 ($30\\%$ số điểm): $x \\le 10^9$.
- Subtask 3 ($40\\%$ số điểm): $x \\le 10^{15}$.

## Ví dụ
| Input | Output |
|---|---|
| `5 27 1 2000` | `1 2 2000` |
""",
}

# (code, name, points, generator) in listing order
PROBLEMS = [
    ("tonguoc", "Tổng ước", 100, gen_tonguoc),
    ("capbangnhau", "Cặp số bằng nhau", 100, gen_capbangnhau),
    ("uclnbcnn", "UCLN và BCNN", 100, gen_uclnbcnn),
    ("so3", "3", 100, gen_so3),
    ("truyvanxau", "Truy vấn xâu", 100, gen_truyvanxau),
    ("lientiep", "Liên tiếp", 200, gen_lientiep),
    ("ditu", "Đi tù", 300, gen_ditu),
]


def write_case(code, idx, inp, out):
    d = os.path.join(ROOT, code)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "%02d.in" % idx), "w") as f:
        f.write(inp if inp.endswith("\n") else inp + "\n")
    with open(os.path.join(d, "%02d.out" % idx), "w") as f:
        f.write(out if out.endswith("\n") else out + "\n")


def main():
    group = ProblemGroup.objects.get(name="lv0")
    langs = list(Language.objects.filter(key__in=LANGS))
    admin = Profile.objects.get(user__username="admin")
    assert len(langs) == len(LANGS), langs
    base = timezone.now()

    with transaction.atomic():
        for i, (code, name, points, gen) in enumerate(PROBLEMS):
            subtasks, solve = gen()
            assert len(subtasks) == 3 and all(len(s) == 5 for s in subtasks), code
            percase = percase_for(points)
            assert sum(percase[k] * 5 for k in range(3)) == points, (code, percase)

            p, created = Problem.objects.get_or_create(code=code, defaults={
                "name": name, "time_limit": 1.0, "memory_limit": 262144,
                "points": points, "partial": True})
            p.name = name
            p.description = STATEMENTS[code]
            p.time_limit = 1.0
            p.memory_limit = 262144
            p.points = points
            p.partial = True
            p.short_circuit = False
            p.is_public = True
            p.is_manually_managed = False
            p.summary = ""
            p.og_image = ""
            p.group = group
            p.date = base + datetime.timedelta(seconds=i)
            p.save()
            p.types.clear()                       # untyped -> roadmap 'other'
            p.allowed_languages.set(langs)
            p.authors.set([admin])

            idx = 1
            for sub in subtasks:
                for inp in sub:
                    write_case(code, idx, inp, solve(inp))
                    idx += 1

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
            for si in range(3):
                pc = percase[si]
                ncase = len(subtasks[si])
                ProblemTestCase.objects.create(
                    dataset=p, order=order, type="S",
                    points=pc * ncase, is_pretest=False)
                order += 1
                for _ in range(ncase):
                    infile, outfile = "%02d.in" % n, "%02d.out" % n
                    ProblemTestCase.objects.create(
                        dataset=p, order=order, type="C",
                        input_file=infile, output_file=outfile,
                        points=pc, is_pretest=False)
                    order += 1
                    files.extend([infile, outfile])
                    n += 1
                ProblemTestCase.objects.create(
                    dataset=p, order=order, type="E", is_pretest=False)
                order += 1

            ProblemDataCompiler.generate(p, data, p.cases.order_by("order"), files)
            print("%-14s created=%s pts=%d percase=%s cases=%d" % (
                code, created, points, percase, p.cases.filter(type="C").count()))

    print("DONE")


main()
