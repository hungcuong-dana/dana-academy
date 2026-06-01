import time
from judge.models import Problem, Submission, SubmissionSource, Language, Profile

admin = Profile.objects.filter(user__username="admin").first()
lang = Language.objects.get(key="CPP17")
GEN = "/home/dana/online-judge/_gen/sol"

subs = {}
for code in ["rutgon", "kitu", "tanso", "daoxau"]:
    p = Problem.objects.get(code=code)
    src = open("%s/%s.cpp" % (GEN, code)).read()
    s = Submission.objects.create(user=admin, problem=p, language=lang)
    SubmissionSource.objects.create(submission=s, source=src)
    s.source = s.source  # noop
    s.judge(rejudge=False)
    subs[code] = s.id
    print("submitted %-7s -> submission #%d" % (code, s.id))

print("waiting for grading...")
deadline = time.time() + 120
done = {}
while time.time() < deadline and len(done) < 4:
    time.sleep(4)
    for code, sid in subs.items():
        if code in done:
            continue
        s = Submission.objects.get(id=sid)
        if s.status in ("D",):  # Done
            done[code] = s
            print("  %-7s #%d  result=%s  points=%.1f/%.1f  time=%ss  case_pts=%s"
                  % (code, sid, s.result, s.points or 0, s.problem.points,
                     s.time, s.case_points))
for code, sid in subs.items():
    if code not in done:
        s = Submission.objects.get(id=sid)
        print("  %-7s #%d  STILL status=%s result=%s" % (code, sid, s.status, s.result))
print("VERIFY DONE")
