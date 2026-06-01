#!/usr/bin/env python3
"""Create 5 Lv0 'Xau' (string) problems with test data.

Each problem: stdin/stdout, 15 tests in 3 subtasks (5/5/5), weights 30/30/40,
total 100 points. Per-case points encode subtask weight (this judge scores by
per-case points; batch points are display-only).

Run with the site venv python:
    /home/dana/dmojsite/bin/python manage.py shell -c "exec(open('_gen/build_xau_lv0.py').read())"
"""
import os
import random
import string

from django.db import transaction
from django.utils import timezone

from judge.models import (Language, Problem, ProblemData, ProblemGroup,
                          ProblemTestCase, ProblemType, Profile)
from judge.utils.problem_data import ProblemDataCompiler

random.seed(20260526)
ROOT = "/home/dana/online-judge/problems"
LANGS = ["C", "CPP17", "CPP20", "JAVA8", "PY3"]
PERCASE = [6, 6, 8]          # ST1/ST2/ST3 per-case points -> 5*6+5*6+5*8 = 100
BATCH_NAMES = ["Subtask 1", "Subtask 2", "Subtask 3"]

LETL = string.ascii_lowercase
LETU = string.ascii_uppercase
LET = string.ascii_letters
DIG = string.digits


# ----------------------------------------------------------------- helpers
def rline(length, charset, spaces=False):
    """Random line of exactly `length` chars, no leading/trailing space."""
    length = max(1, length)
    pool = charset + (" " if spaces else "")
    s = [random.choice(pool) for _ in range(length)]
    if s[0] == " ":
        s[0] = random.choice(charset)
    if s[-1] == " ":
        s[-1] = random.choice(charset)
    return "".join(s)


def rwords(nwords, wmin, wmax, charset):
    return [rline(random.randint(wmin, wmax), charset) for _ in range(nwords)]


# ----------------------------------------------------------------- problems
def gen_dodai():
    # solve: length of the whole line (spaces count)
    st1 = ["a", "abc", "hello", "ab cd", "abcdefghij"]                 # |S|<=10
    st2 = ["Kirisame Marisa",                                          # sample, 15
           rline(40, LET, True), rline(70, LET, True),
           rline(90, LET, True), rline(100, LET, True)]                # |S|<=100
    st3 = [rline(200, LET, True), rline(500, LET, True),
           rline(800, LET, True), rline(999, LET, True),
           rline(1000, LET, True)]                                     # |S|<=1000
    return [st1, st2, st3], (lambda line: str(len(line)))


def gen_demtu():
    # solve: number of whitespace-separated words
    st1 = ["hello", "Master Spark", "a b c",
           "one two three four", "alpha beta"]
    st2 = ["   Master    Spark",                                       # sample -> 2
           "  " + "  ".join(rwords(5, 2, 6, LET)) + "   ",
           " ".join(rwords(8, 1, 5, LET)),
           "   ".join(rwords(10, 2, 4, LET)),
           " ".join(rwords(12, 3, 6, LET))]
    st3 = [" ".join(rwords(80, 3, 8, LET)),
           "  ".join(rwords(60, 5, 10, LET)),
           " ".join(rwords(100, 1, 6, LET)),
           " ".join(rwords(50, 8, 12, LET)),
           "   " + " ".join(rwords(90, 2, 7, LET)) + "  "]
    return [st1, st2, st3], (lambda line: str(len(line.split())))


def gen_chuthuong():
    # solve: lowercase the whole line
    st1 = ["MaRisA", "ABC", "Hello", "a B c", "XyZ"]
    st2 = [rline(20, LET, True), rline(40, LET, True),
           rline(60, LET, True), rline(80, LET, True),
           rline(100, LET, True)]
    st3 = [rline(250, LET, True), rline(500, LET, True),
           rline(750, LET, True), rline(999, LET, True),
           rline(1000, LET, True)]
    return [st1, st2, st3], (lambda line: line.lower())


def gen_nguyenam():
    # solve: count vowels a e i o u (case-insensitive)
    st1 = ["mArisA", "aeiou", "bcd", "Hello", "AEIOU"]
    st2 = [rline(20, LET, True), rline(40, LET, True),
           rline(60, LET, True), rline(80, LET, True),
           rline(100, LET, True)]
    st3 = [rline(250, LET, True), rline(500, LET, True),
           rline(750, LET, True), rline(999, LET, True),
           rline(1000, LET, True)]
    solve = lambda line: str(sum(1 for c in line.lower() if c in "aeiou"))
    return [st1, st2, st3], solve


def gen_tongchuso():
    # solve: sum of digits
    st1 = ["12345", "0", "9", "1111", "5050"]
    st2 = [rline(20, DIG), rline(40, DIG), rline(60, DIG),
           rline(80, DIG), rline(100, DIG)]
    st3 = ["9" * 1000, rline(250, DIG), rline(500, DIG),
           rline(800, DIG), rline(1000, DIG)]
    solve = lambda line: str(sum(int(c) for c in line))
    return [st1, st2, st3], solve


STATEMENTS = {
    "dodai": """In ra độ dài xâu $S$.

## Input
- Một dòng gồm xâu $S$.

## Output
- In ra một số nguyên là độ dài xâu $S$.

## Ràng buộc
- $1 \\le |S| \\le 1000$.
- Subtask 1 ($30\\%$ số điểm): $|S| \\le 10$.
- Subtask 2 ($30\\%$ số điểm): $|S| \\le 100$.
- Subtask 3 ($40\\%$ số điểm): $|S| \\le 1000$.

## Ví dụ
| Input | Output |
|---|---|
| `Kirisame Marisa` | `15` |
""",
    "demtu": """In ra số lượng từ trong xâu $S$. Các từ được phân tách bởi một hoặc nhiều dấu cách.

## Input
- Một dòng gồm xâu $S$.

## Output
- In ra một số nguyên là số lượng từ trong xâu $S$.

## Ràng buộc
- $1 \\le |S| \\le 1000$.
- Subtask 1 ($30\\%$ số điểm): $|S| \\le 10$.
- Subtask 2 ($30\\%$ số điểm): $|S| \\le 100$.
- Subtask 3 ($40\\%$ số điểm): $|S| \\le 1000$.

## Ví dụ
| Input | Output |
|---|---|
| `Master    Spark` | `2` |
""",
    "chuthuong": """Cho một xâu $S$ gồm các kí tự và dấu cách, chuyển các kí tự về chữ thường.

## Input
- Một dòng gồm xâu $S$.

## Output
- In ra xâu $S$ với tất cả các chữ cái viết thường.

## Ràng buộc
- $1 \\le |S| \\le 1000$.
- Subtask 1 ($30\\%$ số điểm): $|S| \\le 10$.
- Subtask 2 ($30\\%$ số điểm): $|S| \\le 100$.
- Subtask 3 ($40\\%$ số điểm): $|S| \\le 1000$.

## Ví dụ
| Input | Output |
|---|---|
| `MaRisA` | `marisa` |
""",
    "nguyenam": """Cho một xâu $S$ gồm các kí tự, đếm số lượng các nguyên âm xuất hiện trong xâu $S$. Các nguyên âm là các kí tự `u`, `e`, `o`, `a`, `i` (không phân biệt chữ hoa, chữ thường).

## Input
- Một dòng gồm xâu $S$.

## Output
- In ra số lượng nguyên âm.

## Ràng buộc
- $1 \\le |S| \\le 1000$.
- Subtask 1 ($30\\%$ số điểm): $|S| \\le 10$.
- Subtask 2 ($30\\%$ số điểm): $|S| \\le 100$.
- Subtask 3 ($40\\%$ số điểm): $|S| \\le 1000$.

## Ví dụ
| Input | Output |
|---|---|
| `mArisA` | `3` |
""",
    "tongchuso": """Cho một xâu $S$ chỉ gồm các chữ số. Tính tổng các chữ số.

## Input
- Một dòng gồm xâu $S$.

## Output
- In ra tổng các chữ số trong xâu $S$.

## Ràng buộc
- $1 \\le |S| \\le 1000$.
- Subtask 1 ($30\\%$ số điểm): $|S| \\le 10$.
- Subtask 2 ($30\\%$ số điểm): $|S| \\le 100$.
- Subtask 3 ($40\\%$ số điểm): $|S| \\le 1000$.

## Ví dụ
| Input | Output |
|---|---|
| `12345` | `15` |
""",
}

# code -> (name, generator)
PROBLEMS = [
    ("dodai", "Độ dài", gen_dodai),
    ("demtu", "Đếm từ", gen_demtu),
    ("chuthuong", "Chữ thường", gen_chuthuong),
    ("nguyenam", "Nguyên âm", gen_nguyenam),
    ("tongchuso", "Tổng chữ số", gen_tongchuso),
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
                "name": name,
                "time_limit": 1.0,
                "memory_limit": 262144,
                "points": 100.0,
                "partial": True,
            })
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

            # write test files
            idx = 1
            for sub in subtasks:
                for inp in sub:
                    write_case(code, idx, inp, solve(inp))
                    idx += 1

            # ProblemData (stdin/stdout, standard checker)
            data, _ = ProblemData.objects.get_or_create(problem=p)
            data.zipfile = None
            data.fileio_input = None
            data.fileio_output = None
            data.checker = "standard"
            data.save()

            # batched test cases
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
            print("%-10s created=%s cases=%d total_pts=%d" % (
                code, created, p.cases.filter(type="C").count(),
                sum(PERCASE[i] * 5 for i in range(3))))

    print("DONE")


main()
