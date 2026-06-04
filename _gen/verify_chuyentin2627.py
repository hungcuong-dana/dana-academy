"""Smoke-test grading for the Chuyen tin contest problems.

Submits a correct PY3 solution to each problem (expect AC, full points) plus one
partial solution to prime (expect ~50% from subtask 1 only). Run AFTER judges are
online. Outside-contest submissions by admin.

Run: /home/dana/dmojsite/bin/python manage.py shell -c "exec(open('_gen/verify_chuyentin2627.py').read())"
"""
import time

from judge.models import Language, Problem, Profile, Submission, SubmissionSource

admin = Profile.objects.get(user__username="admin")
PY3 = Language.objects.get(key="PY3")

SOL = {
    "arr_maxprod": "a,b,c=map(int,input().split())\nprint(max(a*b,b*c,c*a))\n",
    "ct2627_sum2max": "n=input().strip()\nd=sorted(n,reverse=True)\nprint(int(d[0])+int(d[1]))\n",
    "ct2627_leap": ("y=int(input())\n"
                    "print('INVALID' if not(0<y<=100000) else ('YES' if (y%4==0 and y%100!=0) or y%400==0 else 'NO'))\n"),
    "ct2627_replace": ("import sys\nd=sys.stdin.buffer.read().split()\nt=int(d[0])\n"
                       "import sys as s\ns.stdout.write('\\n'.join(d[1+i].decode().replace('0','5') for i in range(t))+'\\n')\n"),
    "ct2627_age": "a,b=map(int,input().split())\nx=a-2*b\nprint(x if x>=0 else -1)\n",
    "ct2627_prime": ("import sys\nn=int(input())\nL=1300010\ns=bytearray([1])*(L+1)\ns[0]=s[1]=0\n"
                     "for i in range(2,int(L**0.5)+1):\n    if s[i]:\n        s[i*i::i]=bytearray(len(s[i*i::i]))\n"
                     "c=0\nfor i in range(2,L+1):\n    if s[i]:\n        c+=1\n        if c==n:\n            print(i)\n            break\n"),
}

# partial: only correct for small n (subtask 1), wrong/slow elsewhere -> trial division capped
PARTIAL_PRIME = ("n=int(input())\nc=0\nx=1\n"
                 "while c<n:\n    x+=1\n    if x>8000:\n        print(-1)\n        break\n"
                 "    p=all(x%d for d in range(2,int(x**0.5)+1))\n"
                 "    if p:\n        c+=1\n        if c==n:\n            print(x)\n")


def submit(code, src):
    p = Problem.objects.get(code=code)
    sub = Submission(user=admin, problem=p, language=PY3)
    sub.save()
    SubmissionSource(submission=sub, source=src).save()
    sub.source  # noqa
    sub.judge(rejudge=False)
    return sub.id


def wait(sid, timeout=90):
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = Submission.objects.get(id=sid)
        if s.status in ("D", "IE", "CE", "AB"):
            return s
        time.sleep(1.5)
    return Submission.objects.get(id=sid)


print("Submitting correct solutions...")
ids = {code: submit(code, src) for code, src in SOL.items()}
pid = submit("ct2627_prime", PARTIAL_PRIME)

print("\n--- correct solutions (expect AC, points == case_total) ---")
allok = True
for code, sid in ids.items():
    s = wait(sid)
    ok = s.result == "AC" and abs((s.points or 0) - (s.case_total or 0)) < 1e-6 and s.case_total
    allok = allok and ok
    print("%-16s sub#%d  status=%s result=%s  points=%.2f/%.2f  %s" % (
        code, sid, s.status, s.result, s.points or 0, s.case_total or 0,
        "OK" if ok else "*** CHECK ***"))

s = wait(pid)
frac = (s.points or 0) / (s.case_total or 1)
print("\n--- partial prime (expect subtask1 only ~50%%) ---")
print("ct2627_prime    sub#%d  status=%s result=%s  points=%.2f/%.2f (%.0f%%)" % (
    pid, s.status, s.result, s.points or 0, s.case_total or 0, frac * 100))

print("\nALL CORRECT == AC&FULL:", allok)
