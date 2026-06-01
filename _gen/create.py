import os, json
from django.db import transaction
from judge.models import Problem, ProblemData, ProblemTestCase
from judge.utils.problem_data import ProblemDataCompiler

ROOT = "/home/dana/online-judge/problems"
GEN = "/home/dana/online-judge/_gen"
manifest = json.load(open(os.path.join(GEN, "manifest.json")))

# code -> fileio base name
FBASE = {"rutgon": "RUTGON", "kitu": "KITU", "tanso": "TANSO", "daoxau": "DAOXAU"}
# tanso & daoxau statements still say CAU4 -> rename to their own file names
RENAME = {"tanso": ("CAU4", "TANSO"), "daoxau": ("CAU4", "DAOXAU")}

# This deployment's judge scores each case by its OWN `points` (batch points are
# ignored). Test counts are split EVENLY across subtasks ("chia deu"); per-case
# points encode each subtask's rubric weight so the total matches the statement.
#   code -> per-case points for each subtask (in batch order)
PERCASE = {
    "rutgon": [3, 3, 4],   # 10/10/10 cases -> 30/30/40
    "kitu":   [2, 4, 4],   # 10/10/10 cases -> 20/40/40
    "tanso":  [3, 3, 4],   # 10/10/10 cases -> 30/30/40
    "daoxau": [1, 1],      # 15/15 cases    -> 50/50
}

with transaction.atomic():
    for code, fbase in FBASE.items():
        p = Problem.objects.get(code=code)

        # 1) fix file name in statement where it collides on CAU4
        if code in RENAME:
            old, new = RENAME[code]
            if old in (p.description or ""):
                p.description = p.description.replace(old, new)
                p.save(update_fields=["description"])
                print("%-7s: statement %s -> %s" % (code, old, new))

        # 2) ProblemData with freopen file_io
        data, _ = ProblemData.objects.get_or_create(problem=p)
        data.fileio_input = "%s.INP" % fbase
        data.fileio_output = "%s.OUT" % fbase
        data.checker = "standard"
        data.save()

        # 3) rebuild batched test cases
        p.cases.all().delete()
        files = []
        order = 0
        batches = manifest[code]            # [name, pts, first, last]
        percase = PERCASE[code]
        for bi, (bname, bpts, first, last) in enumerate(batches):
            ncase = last - first + 1
            pc = percase[bi]
            ProblemTestCase.objects.create(
                dataset=p, order=order, type="S", points=pc * ncase, is_pretest=False)
            order += 1
            for n in range(first, last + 1):
                infile, outfile = "%02d.in" % n, "%02d.out" % n
                assert os.path.exists(os.path.join(ROOT, code, infile)), infile
                ProblemTestCase.objects.create(
                    dataset=p, order=order, type="C",
                    input_file=infile, output_file=outfile,
                    points=pc, is_pretest=False)
                order += 1
                files.extend([infile, outfile])
            ProblemTestCase.objects.create(
                dataset=p, order=order, type="E", is_pretest=False)
            order += 1

        # 4) compile init.yml + notify judges
        ProblemDataCompiler.generate(p, data, p.cases.order_by("order"), files)
        print("%-7s: fileio=%s/%s  batches=%d  cases=%d  feedback=%r"
              % (code, data.fileio_input, data.fileio_output,
                 len(batches), p.cases.filter(type="C").count(), data.feedback))

print("DONE")
