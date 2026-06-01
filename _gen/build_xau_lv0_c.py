#!/usr/bin/env python3
"""Create Lv0 'Xau' problems 11-15 with test data (stdin/stdout).

15 tests / 3 subtasks (5/5/5), per-case 6/6/8 -> 100 points. solve() gets the
RAW input (full content minus one trailing newline).

Run: /home/dana/dmojsite/bin/python manage.py shell -c "exec(open('_gen/build_xau_lv0_c.py').read())"
"""
import os
import random
import re
import string

from django.db import transaction
from django.utils import timezone

from judge.models import (Language, Problem, ProblemData, ProblemGroup,
                          ProblemTestCase, ProblemType, Profile)
from judge.utils.problem_data import ProblemDataCompiler

random.seed(20260528)
ROOT = "/home/dana/online-judge/problems"
LANGS = ["C", "CPP17", "CPP20", "JAVA8", "PY3"]
PERCASE = [6, 6, 8]

LETL = string.ascii_lowercase
LET = string.ascii_letters
DIG = string.digits


def rstr(n, cs):
    return "".join(random.choice(cs) for _ in range(max(1, n)))


def rruns(total, alpha, max_run):
    out = []
    while len(out) < total:
        ch = random.choice(alpha)
        r = random.randint(1, max_run)
        out.extend([ch] * min(r, total - len(out)))
    return "".join(out)


# ----------------------------------------------------------------- bai 11
def gen_demxau():
    # count occurrences of T in S (overlapping)
    def cnt(s, t):
        return sum(1 for i in range(len(s) - len(t) + 1) if s[i:i + len(t)] == t)
    st1 = ["asasa\nasa", "aaaa\naa", "abcabc\nabc", "a\na", "abc\nd"]
    st2 = []
    for _ in range(5):
        s = rstr(random.randint(50, 200), "ab")
        t = rstr(random.randint(1, 3), "ab")
        st2.append("%s\n%s" % (s, t))
    st3 = ["%s\n%s" % ("a" * 1000, "aa"),
           "%s\n%s" % (rruns(1000, "ab", 5), "ab"),
           "%s\n%s" % (rstr(1000, "abc"), rstr(3, "abc")),
           "%s\n%s" % (rstr(999, "ab"), "aba"),
           "%s\n%s" % (rstr(1000, "ab"), rstr(1000, "ab"))]  # |T|==|S|
    def solve(raw):
        s, t = raw.split("\n")
        return str(cnt(s, t))
    return [st1, st2, st3], solve


# ----------------------------------------------------------------- bai 12
def gen_tongso():
    # delete letters, sum the numbers (digit runs separated by spaces)
    def tok(maxdig):
        kind = random.random()
        if kind < 0.5:
            return rstr(random.randint(1, 5), LETL)            # word
        # number possibly with letters glued inside (digits total <= maxdig)
        nd = random.randint(1, maxdig)
        s = rstr(nd, DIG)
        if random.random() < 0.4:
            pos = random.randint(0, len(s))
            s = s[:pos] + rstr(1, LETL) + s[pos:]
        return s
    def build(maxlen, maxdig):
        out = ""
        while True:
            t = tok(maxdig)
            sep = "" if not out else " " * random.randint(1, 3)
            if len(out) + len(sep) + len(t) > maxlen:
                break
            out += sep + t
        if not out:
            out = rstr(min(maxdig, maxlen), DIG)
        if random.random() < 0.5:
            pad = " " * random.randint(1, 3)
            if len(out) + 2 * len(pad) <= maxlen:
                out = pad + out + pad
        return out
    st1 = ["  t1tt23 45 2e30   57 3qq3", "abc", "  12  34 ", "5", "x9y8z7"]
    st2 = [build(200, 5) for _ in range(5)]
    st3 = [build(1000, 6) for _ in range(5)]
    def solve(s):
        return str(sum(int(x) for x in re.sub(r"[A-Za-z]", "", s).split()))
    return [st1, st2, st3], solve


# ----------------------------------------------------------------- bai 13
def gen_chuanhoaxau():
    # trim, single spaces, Title Case each word
    def norm(s):
        return " ".join(w.capitalize() for w in s.split())
    def rwords(maxlen):
        out = ""
        while True:
            w = rstr(random.randint(1, 8), LET)
            sep = "" if not out else " " * random.randint(1, 3)
            if len(out) + len(sep) + len(w) > maxlen:
                break
            out += sep + w
        if not out:
            out = rstr(min(8, maxlen), LET)
        if random.random() < 0.6:
            pad = " " * random.randint(1, 3)
            if len(out) + 2 * len(pad) <= maxlen:
                out = pad + out + pad
        return out
    st1 = ["  A qUick BRown fOX", "hello", " a b c ", "ABC def", "X"]
    st2 = [rwords(200) for _ in range(5)]
    st3 = [rwords(1000) for _ in range(5)]
    def solve(s):
        return norm(s)
    return [st1, st2, st3], solve


# ----------------------------------------------------------------- bai 14
def gen_rle():
    # line1: compress; line2: decode. Output: compressed\ndecoded
    def compress(s):
        out = []
        i = 0
        while i < len(s):
            j = i
            while j < len(s) and s[j] == s[i]:
                j += 1
            out.append("%d%s" % (j - i, s[i]))
            i = j
        return "".join(out)
    def decode(e):
        out = []
        num = 0
        for c in e:
            if c.isdigit():
                num = num * 10 + int(c)
            else:
                out.append(c * num)
                num = 0
        return "".join(out)
    def mk(comp_src, dec_src):
        return "%s\n%s" % (comp_src, compress(dec_src))
    st1 = ["aabbbbccccc\n1a1b1c",
           mk("aaa", "abc"),
           mk("abc", "aaa"),
           mk(rruns(20, "ab", 6), rruns(20, "abc", 4)),
           mk("z", rruns(15, "ab", 5))]
    st2 = [mk(rruns(random.randint(500, 2000), "abc", 12),
              rruns(random.randint(500, 2000), "abcd", 10)) for _ in range(5)]
    st3 = [mk(rruns(100000, "abc", 30), rruns(100000, "ab", 50)),
           mk("a" * 100000, "b" * 100000),
           mk(rruns(99999, "abcde", 15), rruns(99999, "abc", 20)),
           mk(rruns(100000, "ab", 100), rruns(50000, "abcdef", 7)),
           mk(rruns(80000, "abc", 9), "a" * 100000)]
    def solve(raw):
        a, b = raw.split("\n")
        return "%s\n%s" % (compress(a), decode(b))
    return [st1, st2, st3], solve


# ----------------------------------------------------------------- bai 15
def gen_pheptinh():
    # evaluate +,-,* (no spaces, no parentheses), * has precedence
    def evaluate(s):
        stack = []
        num = 0
        op = "+"
        for i, c in enumerate(s):
            if c.isdigit():
                num = num * 10 + int(c)
            if (not c.isdigit()) or i == len(s) - 1:
                if op == "+":
                    stack.append(num)
                elif op == "-":
                    stack.append(-num)
                elif op == "*":
                    stack.append(stack.pop() * num)
                op = c
                num = 0
        return sum(stack)

    def build(maxlen, fac_max):
        # each additive term is a product of 1-3 factors (each <= fac_max) so the
        # value stays well within 64-bit; append terms until length budget is hit
        parts = []
        cur = 0
        while True:
            nf = random.randint(1, 3)
            term = "*".join(str(random.randint(1, fac_max)) for _ in range(nf))
            piece = term if not parts else random.choice("+-") + term
            if cur + len(piece) > maxlen:
                break
            parts.append(piece)
            cur += len(piece)
        if not parts:
            parts.append(str(random.randint(1, fac_max)))
        return "".join(parts)

    st1 = ["1-2*3+4*5", "2*3", "10-3-2", "7", "1+2+3"]
    st2 = [build(100, 1000) for _ in range(5)]
    st3 = [build(1000, 1000) for _ in range(5)]
    return [st1, st2, st3], (lambda s: str(evaluate(s)))


STATEMENTS = {
    "demxau": """Cho $2$ xâu $S$ và $T$. Đếm số lần xuất hiện của $T$ trong $S$ (có bao nhiêu xâu con của $S$ bằng $T$).

## Input
- Dòng đầu tiên là xâu $S$.
- Dòng thứ hai là xâu $T$.

## Output
- Số lần xuất hiện của $T$ trong $S$.

## Ràng buộc
- $1 \\le |T| \\le |S| \\le 1000$.
- Subtask 1 ($30\\%$ số điểm): $|S| \\le 20$.
- Subtask 2 ($30\\%$ số điểm): $|S| \\le 200$.
- Subtask 3 ($40\\%$ số điểm): $|S| \\le 1000$.

## Ví dụ
| Input | Output |
|---|---|
| `asasa`<br>`asa` | `2` |
""",
    "tongso": """Cho một xâu $S$ chỉ gồm các chữ cái, chữ số và dấu cách, xóa các chữ cái và in ra tổng các số trong xâu. Xâu có thể gồm các dấu cách thừa.

## Input
- Một dòng gồm xâu $S$.

## Output
- In ra tổng các số trong xâu $S$. Đảm bảo đáp án không vượt quá $10^{18}$.

## Ràng buộc
- $1 \\le |S| \\le 1000$.
- Subtask 1 ($30\\%$ số điểm): $|S| \\le 30$.
- Subtask 2 ($30\\%$ số điểm): $|S| \\le 200$.
- Subtask 3 ($40\\%$ số điểm): $|S| \\le 1000$.

## Ví dụ
| Input | Output |
|---|---|
| `  t1tt23 45 2e30   57 3qq3` | `488` |
""",
    "chuanhoaxau": """Cho một xâu $S$ chỉ gồm các chữ cái và dấu cách. Thực hiện chuẩn hóa xâu:
- Không có dấu cách ở đầu và cuối xâu.
- Không có quá một dấu cách giữa các từ.
- Các chữ cái đầu tiên của các từ viết hoa, còn lại viết thường.

## Input
- Một dòng gồm xâu $S$.

## Output
- In ra xâu $S$ sau khi chuẩn hóa.

## Ràng buộc
- $1 \\le |S| \\le 1000$.
- Subtask 1 ($30\\%$ số điểm): $|S| \\le 20$.
- Subtask 2 ($30\\%$ số điểm): $|S| \\le 200$.
- Subtask 3 ($40\\%$ số điểm): $|S| \\le 1000$.

## Ví dụ
| Input | Output |
|---|---|
| `  A qUick BRown fOX` | `A Quick Brown Fox` |
""",
    "rle": """Sử dụng kĩ thuật nén xâu Run-length encoding, ta thay thế các kí tự lặp lại bằng số một kí tự duy nhất và số lượng lần xuất hiện của nó. Ví dụ `aabbbbccccc` sẽ được nén thành `2a4b5c`.

Hãy viết chương trình để nén xâu và giải mã xâu đã được nén.

## Input
- Dòng đầu tiên gồm một xâu cần được nén.
- Dòng thứ hai gồm một xâu cần được giải mã.

## Output
- Dòng đầu tiên in ra một xâu kết quả sau khi nén.
- Dòng thứ hai in ra một xâu kết quả sau khi giải mã.

## Ràng buộc
- Đảm bảo xâu cần được nén và xâu sau khi giải mã có độ dài không quá $10^5$. Các xâu chỉ gồm các chữ cái viết thường.
- Subtask 1 ($30\\%$ số điểm): độ dài $\\le 20$.
- Subtask 2 ($30\\%$ số điểm): độ dài $\\le 2000$.
- Subtask 3 ($40\\%$ số điểm): độ dài $\\le 10^5$.

## Ví dụ
| Input | Output |
|---|---|
| `aabbbbccccc`<br>`1a1b1c` | `2a4b5c`<br>`abc` |
""",
    "pheptinh": """Cho một biểu thức gồm các phép tính cộng, trừ, và nhân. Hãy thực hiện phép tính và in ra kết quả.

## Input
- Một dòng gồm phép tính. Các phép tính cộng, trừ, nhân tương ứng với `+`, `-`, `*`. Không có dấu cách xuất hiện trong phép tính.

## Output
- In ra một số nguyên là đáp án của phép tính.

## Giới hạn
- Đảm bảo phép tính có thể xử lí được với kiểu dữ liệu số nguyên có dấu 64-bit (`long long` trong C++).
- Độ dài phép tính không quá $1000$.
- Subtask 1 ($30\\%$ số điểm): độ dài $\\le 10$.
- Subtask 2 ($30\\%$ số điểm): độ dài $\\le 100$.
- Subtask 3 ($40\\%$ số điểm): độ dài $\\le 1000$.

## Ví dụ
| Input | Output |
|---|---|
| `1-2*3+4*5` | `15` |
""",
}

PROBLEMS = [
    ("demxau", "Đếm xâu", gen_demxau),
    ("tongso", "Tổng", gen_tongso),
    ("chuanhoaxau", "Chuẩn hóa xâu", gen_chuanhoaxau),
    ("rle", "Run-length encoding", gen_rle),
    ("pheptinh", "Phép tính", gen_pheptinh),
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
