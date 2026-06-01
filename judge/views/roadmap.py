from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.http import Http404

from judge.models import Problem, ProblemGroup, ProblemType
from judge.utils.problems import user_completed_ids, user_attempted_ids


LEVELS = {
    "lv0": {
        "title": "Mức 0", "subtitle": "Cơ bản", "icon": "🌱",
        "blurb": "Mục tiêu: Làm quen với ngôn ngữ lập trình bằng cách giải các bài toán đơn giản.",
        "color": "#22d3ee", "color2": "#0891b2", "accent": "#a5f3fc",
    },
    "lv1": {
        "title": "Mức 1", "subtitle": "Vét cạn", "icon": "🔥",
        "blurb": "Mục tiêu: Các thuật toán đơn giản, nhưng cũng rất quan trọng.",
        "color": "#34d399", "color2": "#059669", "accent": "#6ee7b7",
    },
    "lv2": {
        "title": "Mức 2", "subtitle": "Tìm kiếm nhị phân & STL", "icon": "🎯",
        "blurb": "“Ngừng học các thuật toán vô dụng, hãy luyện tập, học cách dùng tìm kiếm nhị phân” — Um_nik. Tìm kiếm nhị phân là chìa khóa để tiến bộ.",
        "color": "#fbbf24", "color2": "#d97706", "accent": "#fcd34d",
    },
    "lv3": {
        "title": "Mức 3", "subtitle": "Nền tảng nâng cao", "icon": "🧠",
        "blurb": "Mục tiêu là các kiến thức nền tảng sẽ có ích cho sau này. Tất cả các học phần đều rất quan trọng, không thể bỏ qua.",
        "color": "#fb923c", "color2": "#ea580c", "accent": "#fed7aa",
    },
    "lv4": {
        "title": "Mức 4", "subtitle": "Cây & Đồ thị nâng cao", "icon": "🌳",
        "blurb": "Mức này khó hơn và bao gồm nhiều kiến thức nâng cao hơn. Bạn sẽ học Cây phân đoạn và Cây chỉ số nhị phân.",
        "color": "#a78bfa", "color2": "#7c3aed", "accent": "#c4b5fd",
    },
    "lv5": {
        "title": "Mức 5", "subtitle": "Cấu trúc dữ liệu", "icon": "⚡",
        "blurb": "Một số kiến thức nâng cao để đạt giải cao trong các kì thi.",
        "color": "#f472b6", "color2": "#db2777", "accent": "#fbcfe8",
    },
    "lv6": {
        "title": "Mức 6", "subtitle": "Siêu nâng cao", "icon": "👑",
        "blurb": "Các kỹ thuật chuyên sâu: luồng, heuristic, định lý Sprague-Grundy, hình học nâng cao.",
        "color": "#f43f5e", "color2": "#be123c", "accent": "#fda4af",
    },
}

# Curriculum: per-level list of categories, each containing topics.
# Each topic has a slug (URL), label, optional ptype name to filter problems by.
LEVEL_CURRICULUM = {
    "lv0": [
        {"name": "Cơ bản", "topics": [
            {"slug": "io_cond", "label": "Nhập xuất và điều kiện", "ptype": "io_cond"},
            {"slug": "loop",    "label": "Vòng lặp",                "ptype": "loop"},
            {"slug": "array",   "label": "Mảng",                    "ptype": "array"},
            {"slug": "matrix",  "label": "Mảng hai chiều",          "ptype": "matrix"},
            {"slug": "string",  "label": "Xâu",                     "ptype": "string"},
        ]},
        {"name": "Khác", "topics": [
            {"slug": "other",   "label": "Các bài tập tổng hợp", "ptype": "uncategorized"},
        ]},
    ],
    "lv1": [
        {"name": "Vét cạn", "topics": [
            {"slug": "backtrack", "label": "Quay lui", "ptype": None},
            {"slug": "permute",   "label": "Hoán vị", "ptype": None},
        ]},
        {"name": "Tổng tiền tố", "topics": [
            {"slug": "prefix-intro", "label": "Làm quen với Tổng tiền tố", "ptype": None},
            {"slug": "diff-array",   "label": "Mảng hiệu", "ptype": None},
        ]},
        {"name": "Sắp xếp", "topics": [
            {"slug": "sort", "label": "Sắp xếp", "ptype": None},
        ]},
    ],
    "lv2": [
        {"name": "Tìm kiếm nhị phân", "topics": [
            {"slug": "binsearch-intro",  "label": "Giới thiệu tìm kiếm nhị phân", "ptype": None},
            {"slug": "binsearch-answer", "label": "Tìm kiếm nhị phân kết quả",    "ptype": None},
        ]},
        {"name": "Hai con trỏ", "topics": [
            {"slug": "twopointer", "label": "Giới thiệu hai con trỏ", "ptype": None},
        ]},
        {"name": "Toán", "topics": [
            {"slug": "math-basic", "label": "Số học cơ bản",   "ptype": None},
            {"slug": "binpow",     "label": "Lũy thừa nhị phân", "ptype": None},
        ]},
        {"name": "Chia đôi tập", "topics": [
            {"slug": "mitm", "label": "Giới thiệu về chia đôi tập", "ptype": None},
        ]},
        {"name": "STL", "topics": [
            {"slug": "stl", "label": "Container trong thư viện mẫu chuẩn C++ (STL)", "ptype": None},
        ]},
    ],
    "lv3": [
        {"name": "Đồ thị", "topics": [
            {"slug": "bfsdfs", "label": "BFS / DFS", "ptype": None},
        ]},
        {"name": "Cây", "topics": [
            {"slug": "tree-intro", "label": "Giới thiệu về cây", "ptype": None},
        ]},
        {"name": "Quy hoạch động", "topics": [
            {"slug": "dp-intro1",  "label": "Giới thiệu về quy hoạch động",            "ptype": "dp"},
            {"slug": "dp-intro2",  "label": "Giới thiệu về quy hoạch động (Phần hai)", "ptype": None},
            {"slug": "dp-tree",    "label": "Quy hoạch động trên cây",                "ptype": None},
        ]},
        {"name": "Cấu trúc dữ liệu", "topics": [
            {"slug": "dsu", "label": "Cấu trúc các tập không giao nhau (DSU)", "ptype": None},
        ]},
        {"name": "Bitmasks", "topics": [
            {"slug": "bitmask", "label": "Phép toán thao tác bit", "ptype": None},
        ]},
    ],
    "lv4": [
        {"name": "Đồ thị", "topics": [
            {"slug": "shortest-path", "label": "Đường đi ngắn nhất",        "ptype": None},
            {"slug": "01-bfs",        "label": "0-1 BFS / Thuật toán Dial", "ptype": None},
            {"slug": "multi-source",  "label": "BFS / Dijkstra đa luồng",   "ptype": None},
            {"slug": "topo",          "label": "DAG / Sắp xếp topo",        "ptype": None},
        ]},
        {"name": "Xâu", "topics": [
            {"slug": "string-hash", "label": "So khớp xâu - Băm", "ptype": None},
        ]},
        {"name": "Cấu trúc dữ liệu", "topics": [
            {"slug": "segtree",     "label": "Giới thiệu về Cây phân đoạn và Cây chỉ số nhị phân", "ptype": None},
            {"slug": "sparse",      "label": "Bảng thưa",       "ptype": None},
            {"slug": "mono-queue",  "label": "Hàng đợi đơn điệu", "ptype": None},
        ]},
        {"name": "Cây", "topics": [
            {"slug": "lca",   "label": "Tổ tiên chung gần nhất (LCA)", "ptype": None},
            {"slug": "euler", "label": "Euler tour", "ptype": None},
        ]},
        {"name": "Quy hoạch động", "topics": [
            {"slug": "dp-bitmask",  "label": "Quy hoạch động bitmask",  "ptype": None},
            {"slug": "dp-relabel",  "label": "Quy hoạch động đảo nhãn", "ptype": None},
            {"slug": "dp-game",     "label": "Quy hoạch động trò chơi", "ptype": None},
        ]},
        {"name": "Toán", "topics": [
            {"slug": "combi-intro", "label": "Giới thiệu về tổ hợp", "ptype": None},
            {"slug": "incl-excl",   "label": "Bao hàm - Loại trừ",    "ptype": None},
        ]},
    ],
    "lv5": [
        {"name": "Cấu trúc dữ liệu", "topics": [
            {"slug": "sweep",       "label": "Sweep Line",        "ptype": None},
            {"slug": "trie",        "label": "Giới thiệu về Trie", "ptype": None},
            {"slug": "sqrt-decomp", "label": "Chia căn",           "ptype": None},
        ]},
        {"name": "Cây", "topics": [
            {"slug": "rerooting",     "label": "Đảo gốc",                 "ptype": None},
            {"slug": "small-to-large","label": "Small-to-large",          "ptype": None},
            {"slug": "hld",           "label": "Heavy-light decomposition", "ptype": None},
        ]},
        {"name": "Đồ thị", "topics": [
            {"slug": "scc",       "label": "Thành phần liên thông mạnh",       "ptype": None},
            {"slug": "bridge",    "label": "Khớp và cầu",                       "ptype": None},
            {"slug": "bipartite", "label": "Cặp ghép trên đồ thị hai phía",     "ptype": None},
        ]},
        {"name": "Quy hoạch động", "topics": [
            {"slug": "dp-digit",  "label": "Quy hoạch động chữ số", "ptype": None},
            {"slug": "matrix-mul","label": "Nhân ma trận",          "ptype": None},
        ]},
        {"name": "Băm", "topics": [
            {"slug": "hashset", "label": "Băm một tập hợp", "ptype": None},
        ]},
        {"name": "Khác", "topics": [
            {"slug": "divide-conquer", "label": "Chia để trị", "ptype": None},
        ]},
        {"name": "Hình học", "topics": [
            {"slug": "geometry", "label": "Hình học", "ptype": None},
        ]},
        {"name": "Tìm kiếm nhị phân", "topics": [
            {"slug": "parallel-binsearch", "label": "Tìm kiếm nhị phân song song", "ptype": None},
        ]},
        {"name": "Khác (bổ sung)", "topics": [
            {"slug": "extra-lv5", "label": "Bài tập bổ sung (Mức 5)", "ptype": None},
        ]},
    ],
    "lv6": [
        {"name": "Đồ thị",         "topics": [{"slug": "flow",      "label": "Luồng",                       "ptype": None}]},
        {"name": "Heuristic",      "topics": [{"slug": "heuristic", "label": "Giới thiệu về Heuristic",     "ptype": None}]},
        {"name": "Quy hoạch động", "topics": [{"slug": "dp-opt",    "label": "Tối ưu hoá quy hoạch động",   "ptype": None}]},
        {"name": "Cây",            "topics": [{"slug": "centroid",  "label": "Phân tách trọng tâm cây (centroid)", "ptype": None}]},
        {"name": "Toán",           "topics": [
            {"slug": "sprague", "label": "Định lý Sprague - Grundy", "ptype": None},
            {"slug": "number-theory", "label": "Số học",             "ptype": None},
            {"slug": "group-theory",  "label": "Lý thuyết nhóm",     "ptype": None},
        ]},
        {"name": "Hình học",       "topics": [{"slug": "li-chao",   "label": "Quy hoạch động bao lồi / Cây Li Chao", "ptype": None}]},
    ],
}


def _level_keys():
    return list(LEVELS.keys())


def _completed_attempted(request):
    if request.user.is_authenticated:
        completed = user_completed_ids(request.profile)
        attempted = set(user_attempted_ids(request.profile).keys())
        return completed, attempted
    return set(), set()


def _topic_problem_ids(level_key, topic):
    """Return list of Problem ids matching a curriculum topic, or empty if unmapped."""
    ptype_name = topic.get("ptype")
    if not ptype_name:
        return []
    try:
        group = ProblemGroup.objects.get(name=level_key)
    except ProblemGroup.DoesNotExist:
        return []
    if ptype_name == "uncategorized":
        # All public problems in this level without any ProblemType
        qs = Problem.objects.filter(group=group, is_public=True, types__isnull=True)
    else:
        try:
            ptype = ProblemType.objects.get(name=ptype_name)
        except ProblemType.DoesNotExist:
            return []
        qs = Problem.objects.filter(group=group, is_public=True, types=ptype)
    return list(qs.values_list("id", flat=True))


class RoadmapIndex(TemplateView):
    template_name = "roadmap/index.html"
    extra_context = {"layout": "no_wrapper"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        completed, attempted = _completed_attempted(self.request)

        groups = {g.name: g for g in ProblemGroup.objects.filter(name__in=_level_keys())}
        cards = []
        grand_total = grand_solved = grand_topics_total = grand_topics_done = 0

        for key, lv in LEVELS.items():
            group = groups.get(key)
            total = solved = 0
            if group:
                pub_ids = list(Problem.objects.filter(group=group, is_public=True).values_list("id", flat=True))
                total = len(pub_ids)
                solved = sum(1 for pid in pub_ids if pid in completed)

            # Collect topic chips & count topic completion (>=1 solved counts as started)
            chips = []
            topic_total = topic_started = 0
            for cat in LEVEL_CURRICULUM.get(key, []):
                for t in cat["topics"]:
                    topic_total += 1
                    chips.append(t["label"])
                    if t.get("ptype"):
                        ids = _topic_problem_ids(key, t)
                        if any(pid in completed for pid in ids):
                            topic_started += 1

            cards.append({
                "key": key,
                "title": lv["title"],
                "subtitle": lv["subtitle"],
                "blurb": lv["blurb"],
                "icon": lv["icon"],
                "color": lv["color"],
                "color2": lv["color2"],
                "accent": lv["accent"],
                "total": total,
                "solved": solved,
                "topic_chips": chips[:6],
                "topic_more": max(0, len(chips) - 6),
                "topic_total": topic_total,
                "topic_started": topic_started,
                "percent": int(round(solved * 100.0 / total)) if total else 0,
            })

            grand_total += total
            grand_solved += solved
            grand_topics_total += topic_total
            grand_topics_done += topic_started

        ctx["cards"] = cards
        ctx["grand"] = {
            "problems_total": grand_total,
            "problems_solved": grand_solved,
            "percent": int(round(grand_solved * 100.0 / grand_total)) if grand_total else 0,
            "topics_total": grand_topics_total,
            "topics_started": grand_topics_done,
            "levels_started": sum(1 for c in cards if c["solved"] > 0),
            "levels_total": len(cards),
        }
        return ctx


TOPIC_ICON_MAP = [
    ("nhập xuất", "fa-keyboard"),
    ("điều kiện", "fa-code-branch"),
    ("vòng lặp", "fa-arrows-rotate"),
    ("mảng hai chiều", "fa-table"),
    ("mảng", "fa-table-cells"),
    ("xâu", "fa-quote-right"),
    ("string", "fa-quote-right"),
    ("băm", "fa-fingerprint"),
    ("đồ thị", "fa-diagram-project"),
    ("bfs", "fa-diagram-project"),
    ("dfs", "fa-diagram-project"),
    ("đường đi", "fa-route"),
    ("topo", "fa-arrow-trend-up"),
    ("cây", "fa-tree"),
    ("euler", "fa-shoe-prints"),
    ("lca", "fa-tree"),
    ("quy hoạch", "fa-brain"),
    ("dp", "fa-brain"),
    ("dsu", "fa-cubes"),
    ("cấu trúc", "fa-cubes-stacked"),
    ("segment", "fa-grip-lines-vertical"),
    ("bảng thưa", "fa-table-list"),
    ("hàng đợi", "fa-list-ol"),
    ("bit", "fa-bug"),
    ("tổ hợp", "fa-calculator"),
    ("toán", "fa-calculator"),
    ("số học", "fa-divide"),
    ("nguyên tố", "fa-divide"),
    ("nhị phân", "fa-magnifying-glass-chart"),
    ("hai con trỏ", "fa-arrows-left-right"),
    ("chia đôi", "fa-scissors"),
    ("stl", "fa-layer-group"),
    ("sắp xếp", "fa-arrow-down-wide-short"),
    ("tiền tố", "fa-chart-column"),
    ("hiệu", "fa-minus"),
    ("vét cạn", "fa-shoe-prints"),
    ("quay lui", "fa-rotate-left"),
    ("hoán vị", "fa-shuffle"),
    ("trie", "fa-network-wired"),
    ("căn", "fa-square-root-variable"),
    ("ma trận", "fa-table-cells-large"),
    ("sweep", "fa-broom"),
    ("hình học", "fa-shapes"),
    ("luồng", "fa-water"),
    ("heuristic", "fa-lightbulb"),
    ("centroid", "fa-bullseye"),
    ("sprague", "fa-chess"),
    ("nhóm", "fa-users"),
    ("li chao", "fa-mountain"),
    ("decomposition", "fa-sitemap"),
    ("small-to-large", "fa-arrow-up-wide-short"),
    ("liên thông", "fa-circle-nodes"),
    ("khớp", "fa-link"),
    ("cặp ghép", "fa-people-arrows"),
]
DIFFICULTY_BY_LEVEL = {
    "lv0": ("Dễ", "#10b981"),
    "lv1": ("Dễ", "#10b981"),
    "lv2": ("Trung bình", "#f59e0b"),
    "lv3": ("Trung bình", "#f59e0b"),
    "lv4": ("Khó", "#ef4444"),
    "lv5": ("Khó", "#ef4444"),
    "lv6": ("Cực khó", "#a855f7"),
}


def _topic_icon(label):
    low = label.lower()
    for keyword, icon in TOPIC_ICON_MAP:
        if keyword in low:
            return icon
    return "fa-book-open"


def _est_minutes(total):
    if total <= 0:
        return "Sắp ra mắt"
    if total <= 3:
        return "~30 phút"
    if total <= 6:
        return "1–2 giờ"
    if total <= 12:
        return "3–5 giờ"
    return f"~{int(round(total * 0.4))} giờ"


class RoadmapLevel(TemplateView):
    template_name = "roadmap/level.html"
    extra_context = {"layout": "no_wrapper"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        level_key = self.kwargs["level"]
        if level_key not in LEVELS:
            raise Http404
        completed, attempted = _completed_attempted(self.request)
        lv = LEVELS[level_key]
        diff_label, diff_color = DIFFICULTY_BY_LEVEL.get(level_key, ("Trung bình", "#f59e0b"))

        categories = []
        level_total = level_solved = level_attempted_only = 0
        topic_count = topic_done = 0
        all_topics = []
        recommended = None

        for cat in LEVEL_CURRICULUM.get(level_key, []):
            topic_rows = []
            cat_total = cat_solved = 0
            for topic in cat["topics"]:
                ids = _topic_problem_ids(level_key, topic)
                total = len(ids)
                solved = sum(1 for pid in ids if pid in completed)
                topic_count += 1
                done = total > 0 and solved == total
                if done:
                    topic_done += 1
                cat_total += total
                cat_solved += solved
                row = {
                    "slug": topic["slug"],
                    "label": topic["label"],
                    "total": total,
                    "solved": solved,
                    "has_problems": total > 0,
                    "percent": int(round(solved * 100.0 / total)) if total else 0,
                    "icon": _topic_icon(topic["label"]),
                    "est_time": _est_minutes(total),
                    "difficulty": diff_label,
                    "difficulty_color": diff_color,
                    "category": cat["name"],
                    "is_done": done,
                    "is_started": solved > 0 and not done,
                    "is_upcoming": total == 0,
                }
                topic_rows.append(row)
                all_topics.append(row)
                if recommended is None and total > 0 and not done:
                    recommended = row
            categories.append({
                "name": cat["name"],
                "topics": topic_rows,
                "total": cat_total,
                "solved": cat_solved,
            })

        # Whole level stats
        try:
            group = ProblemGroup.objects.get(name=level_key)
            pub_ids = list(Problem.objects.filter(group=group, is_public=True).values_list("id", flat=True))
            level_total = len(pub_ids)
            level_solved = sum(1 for pid in pub_ids if pid in completed)
            level_attempted_only = sum(1 for pid in pub_ids if pid in attempted and pid not in completed)
        except ProblemGroup.DoesNotExist:
            pass

        # Related: other topics with problems (excluding recommended), shuffle-stable pick first 4
        related = [t for t in all_topics if t["has_problems"] and (not recommended or t["slug"] != recommended["slug"])][:4]

        ctx["level_key"] = level_key
        ctx["level"] = lv
        ctx["categories"] = categories
        ctx["recommended"] = recommended
        ctx["related"] = related
        ctx["difficulty_label"] = diff_label
        ctx["difficulty_color"] = diff_color
        ctx["stats"] = {
            "total": level_total,
            "solved": level_solved,
            "attempted_only": level_attempted_only,
            "untouched": max(0, level_total - level_solved - level_attempted_only),
            "percent": int(round(level_solved * 100.0 / level_total)) if level_total else 0,
            "topic_count": topic_count,
            "topic_done": topic_done,
            "is_complete": level_total > 0 and level_solved == level_total,
        }
        return ctx


class RoadmapLevelType(TemplateView):
    template_name = "roadmap/type.html"
    extra_context = {"layout": "no_wrapper"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        level_key = self.kwargs["level"]
        slug = self.kwargs["type"]
        if level_key not in LEVELS:
            raise Http404

        topic = None
        category_name = None
        for cat in LEVEL_CURRICULUM.get(level_key, []):
            for t in cat["topics"]:
                if t["slug"] == slug:
                    topic = t
                    category_name = cat["name"]
                    break
            if topic:
                break
        if topic is None:
            raise Http404

        completed, attempted = _completed_attempted(self.request)
        ids = _topic_problem_ids(level_key, topic)
        problems = list(Problem.objects.filter(id__in=ids).order_by("date", "id")) if ids else []

        rows = []
        for p in problems:
            if p.id in completed:
                status = "solved"
            elif p.id in attempted:
                status = "attempted"
            else:
                status = "unsolved"
            rows.append({"problem": p, "status": status})

        ctx["level_key"] = level_key
        ctx["level"] = LEVELS[level_key]
        ctx["category_name"] = category_name
        ctx["topic_label"] = topic["label"]
        ctx["topic_slug"] = slug
        ctx["rows"] = rows
        ctx["total"] = len(rows)
        ctx["solved"] = sum(1 for r in rows if r["status"] == "solved")
        return ctx


# --- Roadmap-aware navigation on problem pages ---

def _find_topic(level_key, topic_slug):
    """Return (topic_dict, category_name) for a given level/slug pair, or (None, None)."""
    if level_key not in LEVELS:
        return None, None
    for cat in LEVEL_CURRICULUM.get(level_key, []):
        for t in cat["topics"]:
            if t["slug"] == topic_slug:
                return t, cat["name"]
    return None, None


def parse_rm_param(value):
    """Parse '?rm=lv0/array' style param into (level_key, topic_slug) or (None, None)."""
    if not value or "/" not in value:
        return None, None
    level_key, _, slug = value.partition("/")
    level_key = level_key.strip()
    slug = slug.strip()
    if not level_key or not slug:
        return None, None
    if level_key not in LEVELS:
        return None, None
    return level_key, slug


def build_topic_nav(request, level_key, topic_slug, current_problem_id=None):
    """Return a dict describing the topic the user is working through, or None.

    Used by problem/submit/submission views to render an in-flow roadmap panel:
    breadcrumb, list of sibling problems with status, and the next unsolved one.
    """
    topic, category_name = _find_topic(level_key, topic_slug)
    if topic is None:
        return None

    completed, attempted = _completed_attempted(request)
    ids = _topic_problem_ids(level_key, topic)
    if not ids:
        return None

    problems = list(Problem.objects.filter(id__in=ids).order_by("date", "id"))
    rows = []
    current_index = None
    next_unsolved = None
    next_after_current = None
    solved_count = 0
    for i, p in enumerate(problems):
        if p.id in completed:
            status = "solved"
            solved_count += 1
        elif p.id in attempted:
            status = "attempted"
        else:
            status = "unsolved"
        is_current = (current_problem_id is not None and p.id == current_problem_id)
        if is_current:
            current_index = i
        row = {
            "problem": p,
            "status": status,
            "is_current": is_current,
        }
        rows.append(row)
        if status != "solved" and not is_current and next_unsolved is None:
            next_unsolved = row
        if current_index is not None and i > current_index and next_after_current is None and status != "solved":
            next_after_current = row

    # Prefer "next unsolved problem after the current one"; fall back to first unsolved overall.
    next_problem = next_after_current or next_unsolved

    lv = LEVELS[level_key]
    return {
        "level_key": level_key,
        "level": lv,
        "topic_slug": topic_slug,
        "topic_label": topic["label"],
        "category_name": category_name,
        "rm_param": "{}/{}".format(level_key, topic_slug),
        "rows": rows,
        "total": len(rows),
        "solved": solved_count,
        "percent": int(round(solved_count * 100.0 / len(rows))) if rows else 0,
        "current_index": current_index,
        "next_problem": next_problem,
    }
