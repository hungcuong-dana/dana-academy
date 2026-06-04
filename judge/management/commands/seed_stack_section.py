"""
Fill Level B · Module 1 · Section 1 (Stack, deque) with detailed theory and
create three judgeable exercises (loose test data) attached to that section.
"""
import os
import random
from collections import deque

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from judge.models import (
    Problem,
    ProblemGroup,
    ProblemType,
    Language,
    Profile,
    CourseLessonSection,
    CourseLessonProblem,
)

LANG_KEYS = ["C", "CPP17", "CPP20", "JAVA8", "PY3"]

THEORY = r"""
# Stack & Deque (+ Monotonic stack / deque)

## 1. Stack (ngăn xếp)

**Stack** là cấu trúc dữ liệu **LIFO** (*Last In – First Out*): phần tử vào sau cùng
sẽ ra trước. Hình dung như chồng đĩa — bạn chỉ thao tác ở **đỉnh (top)**.

**Các thao tác — tất cả $O(1)$:**

| Thao tác | Ý nghĩa |
|---|---|
| `push(x)` | thêm `x` lên đỉnh |
| `pop()` | lấy ra phần tử ở đỉnh |
| `top()` / `peek()` | xem phần tử đỉnh (không lấy ra) |
| `empty()` | kiểm tra rỗng |

```cpp
stack<int> st;
st.push(5);
st.push(7);
cout << st.top();   // 7
st.pop();           // bỏ 7
cout << st.top();   // 5
```

```python
st = []
st.append(5)        # push
st.append(7)
print(st[-1])       # top -> 7
st.pop()            # pop
```

**Khi nào dùng stack?** Bất cứ khi nào cần xử lý theo kiểu "lồng nhau / quay lui gần nhất":
- Kiểm tra **dãy ngoặc hợp lệ**.
- Tính biểu thức **hậu tố (postfix/RPN)**, chuyển trung tố → hậu tố.
- Khử đệ quy (DFS dùng stack tường minh).
- Bài toán **phần tử lớn/nhỏ hơn gần nhất** (→ monotonic stack).

---

## 2. Deque (hàng đợi hai đầu)

**Deque** (*double-ended queue*) cho phép **thêm/xoá ở CẢ hai đầu** trong $O(1)$.
Nó tổng quát hoá cả **stack** lẫn **queue**.

```cpp
deque<int> dq;
dq.push_back(1);    // thêm cuối
dq.push_front(2);   // thêm đầu
dq.front();         // 2
dq.back();          // 1
dq.pop_front();     // bỏ đầu
dq.pop_back();      // bỏ cuối
```

```python
from collections import deque
dq = deque()
dq.append(1)        # thêm cuối
dq.appendleft(2)    # thêm đầu
dq.popleft(); dq.pop()
```

> **Lưu ý hiệu năng:** trong Python **luôn dùng `collections.deque`** cho thao tác đầu danh
> sách — `list.pop(0)` là $O(n)$ còn `deque.popleft()` là $O(1)$.

---

## 3. Monotonic stack (ngăn xếp đơn điệu)

**Ý tưởng:** duy trì một stack mà các phần tử (theo giá trị) **luôn tăng hoặc luôn giảm**.
Khi phần tử mới phá vỡ tính đơn điệu, ta **pop** liên tục — và mỗi lần pop chính là lúc ta
"trả lời" được cho phần tử bị pop.

**Bài toán kinh điển — Phần tử lớn hơn tiếp theo (Next Greater Element):**
với mỗi `a[i]`, tìm phần tử **đầu tiên bên phải lớn hơn** nó.

```cpp
vector<int> nextGreater(vector<int>& a) {
    int n = a.size();
    vector<int> res(n, -1);
    stack<int> st;                 // lưu CHỈ SỐ, giá trị giảm dần từ đáy lên đỉnh
    for (int i = 0; i < n; i++) {
        while (!st.empty() && a[st.top()] < a[i]) {
            res[st.top()] = a[i];  // a[i] là phần tử lớn hơn tiếp theo của st.top()
            st.pop();
        }
        st.push(i);
    }
    return res;
}
```

Mỗi chỉ số được **push 1 lần, pop tối đa 1 lần** ⇒ tổng độ phức tạp **$O(n)$** (phân tích
khấu hao - *amortized*).

**Ứng dụng khác của monotonic stack:**
- **Largest Rectangle in Histogram** — hình chữ nhật lớn nhất trong biểu đồ cột.
- Đếm số đoạn con mà `a[i]` là min/max (đóng góp vào tổng).
- "Stock span", "trapping rain water", …

---

## 4. Monotonic deque (hàng đợi đơn điệu)

Khi cần truy vấn **min/max trên một cửa sổ trượt** kích thước `k`, ta dùng **deque đơn điệu**:
deque lưu **chỉ số**, giá trị tương ứng **giảm dần** (cho bài toán max).

**Sliding Window Maximum:** in ra max của mọi đoạn `a[i..i+k-1]`.

```cpp
vector<int> slidingMax(vector<int>& a, int k) {
    deque<int> dq;                 // chỉ số, a[dq] giảm dần
    vector<int> res;
    for (int i = 0; i < (int)a.size(); i++) {
        // 1) bỏ ở cuối các phần tử nhỏ hơn a[i] (không bao giờ là max nữa)
        while (!dq.empty() && a[dq.back()] <= a[i]) dq.pop_back();
        dq.push_back(i);
        // 2) bỏ ở đầu phần tử đã rời khỏi cửa sổ
        if (dq.front() <= i - k) dq.pop_front();
        // 3) khi cửa sổ đủ rộng, đầu deque chính là max
        if (i >= k - 1) res.push_back(a[dq.front()]);
    }
    return res;
}
```

Cũng là **$O(n)$** vì mỗi chỉ số vào/ra deque đúng một lần.

---

## 5. Tổng kết & mẹo

- **Stack** ⇒ xử lý "gần nhất chưa đóng" (ngoặc, biểu thức, NGE).
- **Deque** ⇒ thêm/xoá hai đầu $O(1)$; nền tảng của **monotonic deque** & **BFS 0/1**.
- Gặp cụm từ *"phần tử lớn/nhỏ hơn gần nhất"*, *"đoạn con với min/max"*, *"cửa sổ trượt
  min/max"* ⇒ nghĩ ngay tới **monotonic stack/deque**, lời giải thường là **$O(n)$**.
- Luôn để ý **lưu chỉ số thay vì giá trị** trong stack/deque để còn biết vị trí.

> Làm 3 bài tập bên dưới để chắc tay: **dãy ngoặc** (stack cơ bản), **NGE** (monotonic
> stack), **sliding window maximum** (monotonic deque).
""".strip()


# ----- exercises: (code, name, type, description, gen) ---------------------
def gen_brackets():
    cases = ["()", "([])", "([)]", "(((", ")(", "{[()]}", "(]", "[](){}"]
    rnd = random.Random(11)
    opens, close = "([{", {"(": ")", "[": "]", "{": "}"}
    while len(cases) < 10:
        # build a balanced string then maybe corrupt it
        s, st = [], []
        for _ in range(rnd.randint(2, 30)):
            if st and rnd.random() < 0.5:
                s.append(close[st.pop()])
            else:
                o = rnd.choice(opens)
                st.append(o)
                s.append(o)
        while st:
            s.append(close[st.pop()])
        s = "".join(s)
        if rnd.random() < 0.5 and len(s) >= 2:  # corrupt
            i = rnd.randrange(len(s))
            s = s[:i] + rnd.choice("()[]{}") + s[i + 1 :]
        cases.append(s)

    def solve(s):
        st, pair = [], {")": "(", "]": "[", "}": "{"}
        for c in s:
            if c in "([{":
                st.append(c)
            elif c in pair:
                if not st or st[-1] != pair[c]:
                    return "NO"
                st.pop()
        return "YES" if not st else "NO"

    return [(s + "\n", solve(s) + "\n") for s in cases]


def gen_nge():
    rnd = random.Random(22)
    arrays = [[4, 5, 2, 25], [13, 7, 6, 12], [1, 2, 3, 4], [5, 4, 3, 2, 1], [2, 2, 2]]
    while len(arrays) < 10:
        n = rnd.randint(1, 12)
        arrays.append([rnd.randint(1, 20) for _ in range(n)])

    def solve(a):
        n = len(a)
        res = [-1] * n
        st = []
        for i in range(n):
            while st and a[st[-1]] < a[i]:
                res[st.pop()] = a[i]
            st.append(i)
        return res

    out = []
    for a in arrays:
        inp = f"{len(a)}\n{' '.join(map(str, a))}\n"
        outp = " ".join(map(str, solve(a))) + "\n"
        out.append((inp, outp))
    return out


def gen_slidemax():
    rnd = random.Random(33)
    cases = [([1, 3, -1, -3, 5, 3, 6, 7], 3), ([9, 11], 2), ([4, 4, 4, 4], 2), ([1], 1)]
    while len(cases) < 10:
        n = rnd.randint(1, 14)
        k = rnd.randint(1, n)
        cases.append(([rnd.randint(-10, 30) for _ in range(n)], k))

    def solve(a, k):
        dq, res = deque(), []
        for i, x in enumerate(a):
            while dq and a[dq[-1]] <= x:
                dq.pop()
            dq.append(i)
            if dq[0] <= i - k:
                dq.popleft()
            if i >= k - 1:
                res.append(a[dq[0]])
        return res

    out = []
    for a, k in cases:
        inp = f"{len(a)} {k}\n{' '.join(map(str, a))}\n"
        outp = " ".join(map(str, solve(a, k))) + "\n"
        out.append((inp, outp))
    return out


EXERCISES = [
    (
        "lb-brackets",
        "Dãy ngoặc hợp lệ",
        "string",
        """Cho một xâu `S` chỉ gồm các ký tự ngoặc `()[]{}`. Hãy kiểm tra xâu có **hợp lệ** không:
mỗi ngoặc mở phải được đóng đúng loại và đúng thứ tự lồng nhau.

### Input
- Một dòng duy nhất chứa xâu `S` ($1 \\le |S| \\le 10^5$).

### Output
- In ra `YES` nếu hợp lệ, ngược lại in `NO`.

### Ví dụ
```
Input
{[()]}
Output
YES
```
```
Input
([)]
Output
NO
```

> **Gợi ý:** dùng **stack** — gặp ngoặc mở thì push, gặp ngoặc đóng thì so với đỉnh stack.""",
        gen_brackets,
    ),
    (
        "lb-nge",
        "Phần tử lớn hơn tiếp theo",
        "array",
        """Cho mảng `a` gồm `n` số nguyên dương. Với mỗi phần tử, hãy tìm **phần tử đầu tiên ở
bên phải lớn hơn nó**; nếu không có thì ghi `-1`.

### Input
- Dòng 1: số nguyên `n` ($1 \\le n \\le 10^5$).
- Dòng 2: `n` số nguyên `a[i]` ($1 \\le a[i] \\le 10^9$).

### Output
- Một dòng gồm `n` số: phần tử lớn hơn tiếp theo của từng `a[i]` (cách nhau dấu cách).

### Ví dụ
```
Input
4
4 5 2 25
Output
5 25 25 -1
```

> **Gợi ý:** **monotonic stack** lưu chỉ số, độ phức tạp $O(n)$.""",
        gen_nge,
    ),
    (
        "lb-slidemax",
        "Giá trị lớn nhất trên cửa sổ trượt",
        "array",
        """Cho mảng `a` gồm `n` số nguyên và số `k`. Với mỗi cửa sổ liên tiếp độ dài `k`
(`a[i..i+k-1]`), hãy in ra giá trị **lớn nhất** của cửa sổ đó.

### Input
- Dòng 1: hai số `n` và `k` ($1 \\le k \\le n \\le 10^5$).
- Dòng 2: `n` số nguyên `a[i]` ($-10^9 \\le a[i] \\le 10^9$).

### Output
- Một dòng gồm `n - k + 1` số là max của các cửa sổ từ trái sang phải.

### Ví dụ
```
Input
8 3
1 3 -1 -3 5 3 6 7
Output
3 3 5 5 6 7
```

> **Gợi ý:** **monotonic deque** lưu chỉ số, giá trị giảm dần; $O(n)$.""",
        gen_slidemax,
    ),
]


class Command(BaseCommand):
    help = "Fill Level B Module 1 Section 1 theory + create stack/deque exercises."

    @transaction.atomic
    def handle(self, *args, **options):
        section = (
            CourseLessonSection.objects.filter(
                lesson__course__slug="level-b", lesson__order=1
            )
            .order_by("order")
            .first()
        )
        if not section:
            self.stderr.write("Section not found. Run seed_dana_courses first.")
            return
        lesson = section.lesson

        # 1) theory
        section.theory = THEORY
        section.save(update_fields=["theory"])
        self.stdout.write(f"Filled theory for section: {section.title}")

        # 2) exercises
        admin = Profile.objects.filter(user__is_superuser=True).order_by("id").first()
        langs = list(Language.objects.filter(key__in=LANG_KEYS))
        group = ProblemGroup.objects.get(name="lv2")
        data_root = settings.DMOJ_PROBLEM_DATA_ROOT

        for order, (code, name, type_name, desc, gen) in enumerate(EXERCISES, start=1):
            problem, created = Problem.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": desc,
                    "time_limit": 1.0,
                    "memory_limit": 262144,
                    "points": 100.0,
                    "partial": True,
                    "group": group,
                    "is_public": True,
                    "is_manually_managed": False,
                    "date": timezone.now(),
                },
            )
            if not created:
                problem.name = name
                problem.description = desc
                problem.save()
            problem.allowed_languages.set(langs)
            problem.authors.set([admin] if admin else [])
            ptype = ProblemType.objects.filter(name=type_name).first()
            if ptype:
                problem.types.set([ptype])

            # write loose test data
            pdir = os.path.join(data_root, code)
            os.makedirs(pdir, exist_ok=True)
            cases = gen()
            yml = ["test_cases:"]
            per = 100 // len(cases)
            rem = 100 - per * len(cases)
            for i, (inp, outp) in enumerate(cases, start=1):
                with open(os.path.join(pdir, f"{i:02d}.in"), "w") as f:
                    f.write(inp)
                with open(os.path.join(pdir, f"{i:02d}.out"), "w") as f:
                    f.write(outp)
                pts = per + (1 if i <= rem else 0)
                yml.append(f"  - in: {i:02d}.in")
                yml.append(f"    out: {i:02d}.out")
                yml.append(f"    points: {pts}")
            with open(os.path.join(pdir, "init.yml"), "w") as f:
                f.write("\n".join(yml) + "\n")

            CourseLessonProblem.objects.update_or_create(
                lesson=lesson,
                section=section,
                problem=problem,
                defaults={"order": order, "score": 100},
            )
            self.stdout.write(
                f"{'Created' if created else 'Updated'} exercise {code} "
                f"({len(cases)} cases) -> attached to section"
            )

        self.stdout.write(self.style.SUCCESS("Done. Restart judges to make them judgeable."))
