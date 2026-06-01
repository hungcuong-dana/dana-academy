#!/usr/bin/env python3
"""Create Lv0 'Xau' problems 6-10 with test data (stdin/stdout).

Each problem: 15 tests in 3 subtasks (5/5/5), per-case 6/6/8 -> 100 points.
solve() receives the RAW input (full file content minus trailing newline) so
multi-line inputs (Caesar) work too.

Run: /home/dana/dmojsite/bin/python manage.py shell -c "exec(open('_gen/build_xau_lv0_b.py').read())"
"""
import os
import random
import string

from django.db import transaction
from django.utils import timezone

from judge.models import (Language, Problem, ProblemData, ProblemGroup,
                          ProblemTestCase, ProblemType, Profile)
from judge.utils.problem_data import ProblemDataCompiler

random.seed(20260527)
ROOT = "/home/dana/online-judge/problems"
LANGS = ["C", "CPP17", "CPP20", "JAVA8", "PY3"]
PERCASE = [6, 6, 8]

LETL = string.ascii_lowercase
LETU = string.ascii_uppercase
LET = string.ascii_letters
DIG = string.digits


def rstr(length, charset):
    return "".join(random.choice(charset) for _ in range(max(1, length)))


def rline_sp(length, charset):
    """length chars from charset with spaces, no leading/trailing space."""
    length = max(1, length)
    pool = charset + " "
    s = [random.choice(pool) for _ in range(length)]
    if s[0] == " ":
        s[0] = random.choice(charset)
    if s[-1] == " ":
        s[-1] = random.choice(charset)
    return "".join(s)


# ----------------------------------------------------------------- bai 6
def gen_matkhaumanh():
    # STRONG iff len>=8 and has digit, upper, lower
    st1 = ["Chiruno9", "Abc1", "abcdefg1", "ABCDEFG1", "Abcdefgh"]
    st2 = ["Password123", "Abcde12", "abcABC123",
           "abcdefghij12345", "Xx9yyyyy"]
    st3 = ["A" + "a" * 498 + "1" + "b" * 500,          # STRONG len 1000
           "a" * 1000,                                  # WEAK
           "1" * 1000,                                  # WEAK
           "Ab" * 400,                                  # WEAK no digit
           "Z" + rstr(800, LETL) + "7" + rstr(198, DIG)]  # STRONG
    def solve(s):
        ok = (len(s) >= 8 and any(c.isdigit() for c in s)
              and any(c.isupper() for c in s) and any(c.islower() for c in s))
        return "STRONG" if ok else "WEAK"
    return [st1, st2, st3], solve


# ----------------------------------------------------------------- bai 7
def gen_thongkekitu():
    # count each of a..z in S (lowercase only); 26 ints space-separated
    st1 = ["abcda!", "z", "aaa", LETL, "hello123"]                  # |S|<=100
    st2 = [rstr(2000, LETL), rstr(5000, LETL + DIG),
           rstr(9999, LETL), "q" * 8000, rstr(1234, LETL + "!?.")]  # |S|<=1e4
    st3 = ["a" * 100000, rstr(100000, LETL),
           rstr(99999, LETL + DIG), "ab" * 50000,
           rstr(100000, LETL + "!?.#")]                             # |S|<=1e5
    def solve(s):
        cnt = [0] * 26
        for c in s:
            if "a" <= c <= "z":
                cnt[ord(c) - 97] += 1
        return " ".join(map(str, cnt))
    return [st1, st2, st3], solve


# ----------------------------------------------------------------- bai 8
def gen_xaupalindrome():
    st1 = ["abba", "abc", "a", "racecar", "ab"]                     # |S|<=20
    st2 = ["abacaba", rstr(150, "ab"), rstr(150, "ab")[::-1] + rstr(150, "ab"),
           ("xy" * 75) + ("xy" * 75)[::-1], rstr(200, LETL)]        # |S|<=200
    big = rstr(500, LETL)
    st3 = ["a" * 1000, big + big[::-1], rstr(1000, LETL),
           rstr(999, "ab"), ("abc" * 166) + "z"]                    # |S|<=1000
    def solve(s):
        return "YES" if s == s[::-1] else "NO"
    return [st1, st2, st3], solve


# ----------------------------------------------------------------- bai 9
def gen_xauconpalin():
    # count palindromic contiguous substrings (lowercase a-z)
    st1 = ["mima", "aaa", "abc", "a", "abba"]                       # |S|<=20
    st2 = [rstr(100, "ab"), rstr(150, "abc"), rstr(200, LETL),
           "ab" * 75, rstr(120, "abcde")]                           # |S|<=200
    st3 = ["a" * 1000, "ab" * 500, rstr(1000, LETL),
           rstr(1000, "abc"), rstr(999, "ab")]                      # |S|<=1000
    def solve(s):
        n = len(s)
        total = 0
        for c in range(n):
            for a, b in ((c, c), (c, c + 1)):
                while a >= 0 and b < n and s[a] == s[b]:
                    total += 1
                    a -= 1
                    b += 1
        return str(total)
    return [st1, st2, st3], solve


# ----------------------------------------------------------------- bai 10
def gen_caesar():
    # input: line1 = S (lowercase + spaces), line2 = k (0..25); shift letters
    def mk(s, k):
        return "%s\n%d" % (s, k)
    st1 = [mk("marisa", 3), mk("abc", 1), mk("hello world", 5),
           mk("z", 1), mk("a b c", 25)]                             # |S|<=20
    st2 = [mk(rline_sp(80, LETL), random.randint(0, 25)) for _ in range(4)]
    st2.append(mk(rline_sp(100, LETL), 0))                          # k=0 -> unchanged
    st3 = [mk(rline_sp(1000, LETL), random.randint(1, 25)) for _ in range(3)]
    st3.append(mk("z" * 1000, 25))
    st3.append(mk(rline_sp(999, LETL), 13))
    def solve(raw):
        line, ks = raw.split("\n")
        k = int(ks)
        out = []
        for c in line:
            if "a" <= c <= "z":
                out.append(chr((ord(c) - 97 + k) % 26 + 97))
            else:
                out.append(c)
        return "".join(out)
    return [st1, st2, st3], solve


STATEMENTS = {
    "matkhaumanh": """Một mật khẩu được xem là **mạnh** nếu nó chứa:
- Ít nhất $1$ chữ số.
- Ít nhất $1$ chữ cái hoa.
- Ít nhất $1$ chữ cái thường.

và có độ dài ít nhất $8$ kí tự.

## Input
- Một dòng gồm xâu $S$.

## Output
- In ra `STRONG` nếu xâu $S$ là mật khẩu mạnh, ngược lại in ra `WEAK`.

## Ràng buộc
- $1 \\le |S| \\le 1000$.
- $S$ chỉ gồm chữ cái tiếng Anh và chữ số.
- Subtask 1 ($30\\%$ số điểm): $|S| \\le 10$.
- Subtask 2 ($30\\%$ số điểm): $|S| \\le 100$.
- Subtask 3 ($40\\%$ số điểm): $|S| \\le 1000$.

## Ví dụ
| Input | Output |
|---|---|
| `Chiruno9` | `STRONG` |
""",
    "thongkekitu": """Với mỗi kí tự tiếng Anh từ $a$ đến $z$, hãy đếm số lần xuất hiện của nó trong $S$.

## Input
- Một dòng gồm xâu $S$.

## Output
- $26$ số nguyên, lần lượt là số lần xuất hiện của các kí tự từ $a$ đến $z$.

## Ràng buộc
- $1 \\le |S| \\le 10^5$.
- Subtask 1 ($30\\%$ số điểm): $|S| \\le 100$.
- Subtask 2 ($30\\%$ số điểm): $|S| \\le 10^4$.
- Subtask 3 ($40\\%$ số điểm): $|S| \\le 10^5$.

## Ví dụ
| Input | Output |
|---|---|
| `abcda!` | `2 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0` |
""",
    "xaupalindrome": """Kiểm tra xem xâu $S$ có phải palindrome không?

## Input
- Một dòng gồm xâu $S$.

## Output
- In ra `YES` nếu xâu $S$ là palindrome, ngược lại in ra `NO`.

## Ràng buộc
- $1 \\le |S| \\le 1000$.
- Subtask 1 ($30\\%$ số điểm): $|S| \\le 20$.
- Subtask 2 ($30\\%$ số điểm): $|S| \\le 200$.
- Subtask 3 ($40\\%$ số điểm): $|S| \\le 1000$.

## Ví dụ
| Input | Output |
|---|---|
| `abba` | `YES` |
""",
    "xauconpalin": """Đếm số lượng xâu con của $S$ là palindrome.

Xâu con của $S$ là một chuỗi các kí tự liên tiếp trong $S$.

## Input
- Một dòng gồm xâu $S$.

## Output
- Số lượng xâu con palindrome của $S$.

## Ràng buộc
- $1 \\le |S| \\le 1000$.
- $S$ chỉ gồm các chữ cái tiếng Anh viết thường.
- Subtask 1 ($30\\%$ số điểm): $|S| \\le 20$.
- Subtask 2 ($30\\%$ số điểm): $|S| \\le 200$.
- Subtask 3 ($40\\%$ số điểm): $|S| \\le 1000$.

## Ví dụ
| Input | Output |
|---|---|
| `mima` | `5` |
""",
    "caesar": """Caesar Cipher là một kỹ thuật mã hóa đơn giản, dịch chuyển mỗi ký tự trong văn bản gốc một số vị trí cố định.

Ví dụ, khi dịch chuyển $3$ vị trí:
- `a` trở thành `d`.
- `b` trở thành `e`.
- `hello` trở thành `khoor`.
- `zoo` trở thành `crr`.

Cho xâu $S$ và một giá trị dịch chuyển $k$, và thực hiện mã hóa trên xâu $S$.

## Input
- Dòng đầu tiên là xâu $S$ gồm các chữ cái viết thường và dấu cách.
- Dòng thứ hai gồm một số nguyên $k$.

## Output
- In ra xâu $S$ sau khi mã hóa.

## Ràng buộc
- $1 \\le |S| \\le 1000$.
- $0 \\le k \\le 25$.
- Subtask 1 ($30\\%$ số điểm): $|S| \\le 20$.
- Subtask 2 ($30\\%$ số điểm): $|S| \\le 100$.
- Subtask 3 ($40\\%$ số điểm): $|S| \\le 1000$.

## Ví dụ
| Input | Output |
|---|---|
| `marisa`<br>`3` | `pdulvd` |
""",
}

PROBLEMS = [
    ("matkhaumanh", "Mật khẩu mạnh", gen_matkhaumanh),
    ("thongkekitu", "Thống kê kí tự", gen_thongkekitu),
    ("xaupalindrome", "Xâu palindrome", gen_xaupalindrome),
    ("xauconpalin", "Xâu con palindrome", gen_xauconpalin),
    ("caesar", "Mã hóa Caesar", gen_caesar),
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
    ptype = ProblemType.objects.get(name="string")
    langs = list(Language.objects.filter(key__in=LANGS))
    admin = Profile.objects.get(user__username="admin")
    assert len(langs) == len(LANGS), langs

    with transaction.atomic():
        for code, name, gen in PROBLEMS:
            subtasks, solve = gen()
            assert len(subtasks) == 3 and all(len(s) == 5 for s in subtasks), code

            p, created = Problem.objects.get_or_create(code=code, defaults={
                "name": name, "time_limit": 1.0, "memory_limit": 262144,
                "points": 100.0, "partial": True})
            p.name = name
            p.description = STATEMENTS[code]
            p.time_limit = 1.0
            p.memory_limit = 262144
            p.points = 100.0
            p.partial = True
            p.short_circuit = False
            p.is_public = True
            p.is_manually_managed = False
            p.summary = ""
            p.og_image = ""
            p.group = group
            if not p.date:
                p.date = timezone.now()
            p.save()
            p.types.set([ptype])
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
                pc = PERCASE[si]
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
            print("%-14s created=%s cases=%d" % (
                code, created, p.cases.filter(type="C").count()))

    print("DONE")


main()
