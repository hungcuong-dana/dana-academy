import time
from judge.models import Problem, Submission, SubmissionSource, Language, Profile
admin = Profile.objects.filter(user__username="admin").first()
lang = Language.objects.get(key="CPP17")
GEN = "/home/dana/online-judge/_gen/sol"
tests = [("daoxau","daoxau_brute","expect ~50 (ST2 TLE)"),
         ("tanso","tanso_brute","expect ~60 (ST3 TLE)")]
subs={}
for code,fn,note in tests:
    p=Problem.objects.get(code=code)
    s=Submission.objects.create(user=admin,problem=p,language=lang)
    SubmissionSource.objects.create(submission=s,source=open("%s/%s.cpp"%(GEN,fn)).read())
    s.judge(rejudge=False); subs[code]=(s.id,note); print("submitted",code,"#%d"%s.id,note)
print("waiting...")
dl=time.time()+150; done=set()
while time.time()<dl and len(done)<len(subs):
    time.sleep(4)
    for code,(sid,note) in subs.items():
        if code in done: continue
        s=Submission.objects.get(id=sid)
        if s.status=="D":
            done.add(code)
            print("  %-7s #%d result=%s points=%.1f/100 case=%s/%s | %s"%(code,sid,s.result,s.points or 0,s.case_points,s.case_total,note))
print("DONE")
