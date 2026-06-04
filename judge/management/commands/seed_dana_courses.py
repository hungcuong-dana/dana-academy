"""
Seed the Dana Academy "billiards-level" course roadmap.

Creates:
  * Level B  — the first real course, with its 8 modules + 1 advanced module as a
    sequentially-unlocked lesson chain (finish a module to unlock the next).
  * Level K / C / A / H — locked "coming soon" placeholders for the level roadmap.

Idempotent: safe to run repeatedly. Pass --reset-lessons to rewrite Level B's
lesson content/prerequisites from this file.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from judge.models import Profile
from judge.models.course import (
    Course,
    CourseLesson,
    CourseLessonPrerequisite,
    CourseLessonSection,
    CourseRole,
    RoleInCourse,
)

# Grade % a student must reach in a module before the next one unlocks.
UNLOCK_THRESHOLD = 80.0
LESSON_POINTS = 100

LEVEL_B_ABOUT = """\
## Level B — Giỏi (đấu giải nghiêm túc)

Hệ cấp độ kiểu bida: **K → C → B → A → Pro**. Tương ứng hạng **B / B+ (Giỏi)**: đã làm chủ
kỹ thuật (áp-phê, cu-lê, retro), đánh hết bàn và xử lý được hình bi khó — thường đi cơ 6–7 bi.

Quy ra lập trình, **Level B** là mốc bạn nắm vững **toàn bộ thuật toán & cấu trúc dữ liệu
"xương sống"** hay xuất hiện ở vòng tỉnh / vòng 1 HSG Quốc gia và phần lớn đề mức khá. Học
xong B, bạn tự tin cày được **60–80% đề** và đủ nền để leo lên Level A (flow, FFT/NTT,
suffix automaton, link-cut tree…).

> **Triết lý khoá B:** rộng + chắc nền. Lộ trình đi từ nền tảng → toán → DP → đồ thị →
> cây → cấu trúc dữ liệu → xâu → kỹ thuật nâng cao, **độ khó tăng dần**. Hoàn thành một
> module (đạt ≥ {threshold:.0f}%) sẽ **mở khoá** module kế tiếp.
""".format(threshold=UNLOCK_THRESHOLD)

# Each module: (title, intro, [section titles]). Sections become CourseLessonSection
# rows (theory + exercises filled in later).
LEVEL_B_MODULES = [
    (
        "Module 1 — Nền tảng & kỹ thuật cơ bản",
        "Ôn và chốt nền trước khi vào sâu.",
        [
            "Stack, deque (+ monotonic stack / deque)",
            "Chia để trị (divide & conquer)",
            "Chặt tam phân (ternary search)",
        ],
    ),
    (
        "Module 2 — Toán & số học",
        "Nền toán hay rơi vào bài 1 của đề.",
        [
            "Tổ hợp, Bao hàm – loại trừ",
            "Phi hàm Euler",
            "Nhân ma trận (matrix exponentiation)",
        ],
    ),
    (
        "Module 3 — Quy hoạch động cổ điển",
        "Các dạng DP nền tảng phải thuộc nằm lòng.",
        [
            "DP classic: LIS, LCS, knapsack, đường đi trên lưới, game",
            "DP bitmask",
            "DP digit",
        ],
    ),
    (
        "Module 4 — Đồ thị",
        "Duyệt, đường đi, hợp nhất, cây khung.",
        [
            "Duyệt đồ thị: DFS / BFS",
            "Topo sort & DP on DAG",
            "Đường đi ngắn nhất: Dijkstra, Floyd, BFS 0/1, Dial, Dijkstra đa luồng",
            "DSU (cấu trúc các tập rời nhau)",
            "MST (Kruskal / Prim)",
        ],
    ),
    (
        "Module 5 — Cây (trees)",
        "Kỹ thuật chuyên sâu trên cây.",
        [
            "Euler tour",
            "LCA",
            "Đường kính của cây",
            "DFS tree (back-edge, cầu / khớp)",
            "DSU on tree / small-to-large / sack",
            "HLD (heavy-light decomposition)",
            "Centroid decomposition (phân tách trọng tâm)",
            "Virtual tree",
            "Kruskal reconstruction tree",
        ],
    ),
    (
        "Module 6 — Cấu trúc dữ liệu",
        "Bộ công cụ truy vấn & cập nhật nhanh.",
        [
            "Sparse table, Binary lifting",
            "Chia căn (sqrt decomposition) + thuật toán Mo",
            "Segment tree nâng cao (lazy, merge sort tree)",
            "Fenwick tree 2D",
        ],
    ),
    (
        "Module 7 — Xâu (strings)",
        "Xử lý chuỗi cho đấu giải.",
        [
            "Hashing, KMP",
            "Trie",
            "XOR hash, Sum hash",
        ],
    ),
    (
        "Module 8 — DP & kỹ thuật nâng cao",
        "DP tối ưu và các kỹ thuật phối hợp.",
        [
            "DP trên cây: on tree, đảo nhãn, reroot",
            "DP range",
            "DP tối ưu: CHT, DP D&C, Li Chao tree",
            "Meet in the middle",
            "Sweepline",
            "Chặt nhị phân song song (parallel binary search)",
        ],
    ),
    (
        "Nâng cao (B+) — chủ đề khó & ít gặp",
        "Phần bắc cầu lên Level A. Có thể học sau cùng.",
        [
            "Segment tree beats — ít gặp",
            "DP SOS (sum over subsets) — khá khó",
            "DP broken profile — khó",
            "Cấu trúc dữ liệu Persistent (persistent segment tree) — ít gặp",
            "Bignum — ít gặp",
            "Bitset — ít gặp",
            "Bellman – Ford — ít gặp",
        ],
    ),
]

# (slug, name, level label, level_order, about, is_coming_soon, is_open)
LEVEL_COURSES = [
    ("level-k", "Level K — Mới chơi", "K", 0,
     "Hạng **Mới chơi**: lực đánh & tư thế chưa ổn định, đánh được 1–2 bi mỗi lượt. "
     "Lập trình nhập môn: I/O, mảng, sort, đệ quy, tham lam.", True, False),
    ("level-c", "Level C — Khá", "C", 1,
     "Hạng **Khá**: kiểm soát lực và hướng bi ổn định, trung bình 4–6 bi mỗi lượt. "
     "Lập trình: cấu trúc dữ liệu cơ bản, DFS/BFS, DP nhập môn.", True, False),
    ("level-b", "Level B — Giỏi", "B", 2, LEVEL_B_ABOUT, False, True),
    ("level-a", "Level A — Bán chuyên", "A", 3,
     "Hạng **Bán chuyên**: cơ thủ xuất sắc, tâm lý vững, đọc hình bi và dọn bàn cực ổn định. "
     "Lập trình heavy: flow, FFT/NTT, suffix automaton, link-cut tree…", True, False),
    ("level-pro", "Level Pro — Chuyên nghiệp", "PRO", 4,
     "Hạng **Chuyên nghiệp**: đẳng cấp cao nhất, VĐV quốc gia thi đấu các giải vô địch lớn. "
     "Lập trình đỉnh cao, research-level.", True, False),
]


class Command(BaseCommand):
    help = "Seed the Dana Academy billiards-level course roadmap (Level B + coming-soon levels)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-lessons",
            action="store_true",
            help="Rewrite Level B's lesson content and prerequisite chain from this file.",
        )
        parser.add_argument(
            "--teacher",
            type=str,
            default=None,
            help="Username to enrol as TEACHER of Level B (defaults to first superuser).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # --- Level courses (incl. coming-soon placeholders) ---
        for slug, name, level, order, about, coming_soon, is_open in LEVEL_COURSES:
            course, created = Course.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "about": about,
                    "level": level,
                    "level_order": order,
                    "is_public": True,
                    "is_open": is_open,
                    "is_coming_soon": coming_soon,
                },
            )
            if not created:
                course.name = name
                course.level = level
                course.level_order = order
                course.is_public = True
                course.is_coming_soon = coming_soon
                # don't stomp is_open/about for the live Level B unless coming-soon
                if coming_soon:
                    course.is_open = is_open
                    course.about = about
                course.save()
            self.stdout.write(
                f"{'Created' if created else 'Updated'} {slug} "
                f"({'coming soon' if coming_soon else 'live'})"
            )

        # Remove obsolete coming-soon level placeholders (e.g. old level-h).
        valid_slugs = [row[0] for row in LEVEL_COURSES]
        stale = Course.objects.filter(
            is_coming_soon=True, slug__startswith="level-"
        ).exclude(slug__in=valid_slugs)
        for c in stale:
            self.stdout.write(f"Removing obsolete level course {c.slug}")
            c.delete()

        level_b = Course.objects.get(slug="level-b")

        # --- Level B modules as a sequentially-unlocked lesson chain ---
        if options["reset_lessons"]:
            level_b.lessons.all().delete()
            CourseLessonPrerequisite.objects.filter(course=level_b).delete()

        for idx, (title, intro, sections) in enumerate(LEVEL_B_MODULES):
            lesson, created = CourseLesson.objects.get_or_create(
                course=level_b,
                title=title,
                defaults={
                    "content": intro,
                    "points": LESSON_POINTS,
                    "order": idx + 1,  # 1-based: save() reassigns any order < 1
                    "is_visible": True,
                },
            )
            if not created:
                lesson.content = intro
                lesson.points = LESSON_POINTS
                lesson.is_visible = True
                lesson.save()

            # Sections inside the module (theory filled in later).
            for s_idx, s_title in enumerate(sections):
                CourseLessonSection.objects.update_or_create(
                    lesson=lesson,
                    title=s_title,
                    defaults={"order": s_idx + 1, "is_visible": True},
                )

        # Build the prerequisite chain across consecutive lessons (by actual order).
        lessons = list(level_b.lessons.order_by("order"))
        for prev, nxt in zip(lessons, lessons[1:]):
            CourseLessonPrerequisite.objects.update_or_create(
                course=level_b,
                source_order=prev.order,
                target_order=nxt.order,
                defaults={"required_percentage": UNLOCK_THRESHOLD},
            )
        self.stdout.write(
            f"Level B: {len(lessons)} modules, "
            f"{max(len(lessons) - 1, 0)} unlock links @ {UNLOCK_THRESHOLD:.0f}%"
        )

        # --- Enrol a teacher so the course is viewable/editable ---
        teacher_profile = None
        if options["teacher"]:
            teacher_profile = Profile.objects.filter(
                user__username=options["teacher"]
            ).first()
            if not teacher_profile:
                self.stdout.write(self.style.WARNING(
                    f"No user '{options['teacher']}'; falling back to first superuser."
                ))
        if not teacher_profile:
            teacher_profile = Profile.objects.filter(
                user__is_superuser=True
            ).order_by("id").first()

        if teacher_profile:
            CourseRole.make_role(level_b, teacher_profile, RoleInCourse.TEACHER)
            self.stdout.write(
                f"Enrolled {teacher_profile.user.username} as TEACHER of Level B"
            )
        else:
            self.stdout.write(self.style.WARNING(
                "No superuser found — Level B has no teacher yet."
            ))

        self.stdout.write(self.style.SUCCESS("Done seeding Dana course roadmap."))
