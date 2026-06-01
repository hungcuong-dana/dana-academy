"""AI-generated code detection — combines regex markers + stylometry vs user baseline.

Outputs a 0-100 suspicion score (higher = more likely AI-generated).
Designed to ASSIST admins, not auto-ban. Display only to staff.
"""
import math
import re
from typing import Optional


# ─────────────────────────── AI MARKERS ──────────────────────────────────
# (name, regex, weight). Weight contributes to marker_score when found ≥1 time.
MARKERS = [
    # Step-by-step explanatory comments — strongest AI tell
    ("step_comments",
     r"//\s*(Step\s*\d+|First[,:]|Now\s+(we|let|then)|Then[,:]|Finally|"
     r"Initialize|We\s+(can|will|need)|Read\s+(the|input)|Iterate|"
     r"Loop\s+through|Check\s+if|Calculate|Compute|Return\s+the)",
     25, re.IGNORECASE | re.MULTILINE),

    # Verbose variable names: snake_case with 3+ words
    ("verbose_snake",
     r"\b[a-z]+_[a-z]+_[a-z]+\w*\b", 8, 0),

    # Verbose camelCase 3+ words
    ("verbose_camel",
     r"\b[a-z]+[A-Z][a-z]+[A-Z][a-z]+\w*\b", 6, 0),

    # Mass usage of std:: prefix (when not paired with 'using namespace std')
    ("strict_std_prefix",
     r"std::", 5, 0),

    # while ((cin >> x)) — characteristic AI EOF reading style
    ("cin_while_eof",
     r"while\s*\(\s*\(?\s*(std::)?cin\s*>>\s*\w+", 15, 0),

    # if (!(cin >> x)) — explicit error check
    ("cin_if_not_eof",
     r"if\s*\(\s*!\s*\(\s*(std::)?cin\s*>>", 18, 0),

    # Fast I/O setup
    ("fast_io_full",
     r"ios_base::sync_with_stdio\s*\(\s*false\s*\)\s*;?\s*\n?\s*"
     r"(std::)?cin\.tie\s*\(\s*(NULL|nullptr|0)\s*\)", 15, 0),

    # nullptr instead of NULL (modern AI style)
    ("nullptr_usage", r"\bnullptr\b", 4, 0),

    # static_cast<T> instead of (T)
    ("static_cast", r"static_cast\s*<", 6, 0),

    # Lambda
    ("lambda", r"\[\s*[&=]?\s*\]\s*\([^)]*\)\s*(\->[^{]*)?\s*\{", 10, 0),

    # Range-based for with auto
    ("range_for_auto",
     r"for\s*\(\s*(const\s+)?auto\s*&?\s*\w+\s*:\s*", 8, 0),

    # Separate solve() function for trivial problems
    ("solve_function",
     r"^\s*(void|int|long\s+long|auto)\s+solve\s*\(\s*\)\s*\{", 12,
     re.MULTILINE),

    # Doxygen comments
    ("doxygen", r"@(brief|param|return|note)\b", 18, 0),

    # /** docstring */
    ("docstring", r"/\*\*\s*\n", 10, 0),

    # Time complexity comment
    ("complexity_comment",
     r"//.*(Time|Space)\s*[Cc]omplexity\s*[:=]?\s*O\(", 18, 0),
]


def detect_markers(code: str) -> tuple[float, list]:
    """Return (score 0-100, list of matched markers)."""
    found = []
    score = 0.0
    for entry in MARKERS:
        name, pattern, weight, flags = entry
        try:
            matches = re.findall(pattern, code, flags)
        except re.error:
            continue
        if matches:
            count = len(matches)
            # Cap repeat-marker contribution: weight + small per-match bonus
            contrib = weight + min(weight * 0.5, count * 0.5)
            score += contrib
            found.append({
                "marker": name,
                "count": count,
                "weight": round(contrib, 1),
            })

    # ── Comment density (not a regex marker) ──
    lines = code.split("\n")
    nonblank = [l for l in lines if l.strip()]
    if nonblank:
        comment_lines = sum(
            1 for l in lines if l.strip().startswith("//") or l.strip().startswith("/*")
        )
        density = comment_lines / len(nonblank)
        if density >= 0.4:
            score += 20
            found.append({"marker": "high_comment_density",
                          "count": comment_lines, "weight": 20})
        elif density >= 0.25:
            score += 10
            found.append({"marker": "moderate_comment_density",
                          "count": comment_lines, "weight": 10})

    # ── "Perfect boilerplate on trivial problem" heuristic ──
    has_fast_io = "ios_base::sync_with_stdio" in code
    short_code = len(nonblank) < 25
    if has_fast_io and short_code:
        score += 8
        found.append({"marker": "fast_io_on_short_code",
                      "count": 1, "weight": 8})

    return min(round(score, 1), 100.0), found


# ─────────────────────────── STYLOMETRY ──────────────────────────────────
_KEYWORDS = {
    "int", "long", "short", "char", "bool", "auto", "void", "double", "float",
    "string", "size_t", "uint64_t",
    "return", "if", "else", "for", "while", "do", "switch", "case", "default",
    "break", "continue", "true", "false", "const", "static", "struct", "class",
    "public", "private", "protected", "namespace", "using", "include", "define",
    "new", "delete", "this", "nullptr", "NULL", "main", "endl", "std",
    "cin", "cout", "cerr", "printf", "scanf", "size", "begin", "end", "push_back",
    "pop_back", "first", "second", "make_pair", "vector", "pair", "set", "map",
    "unordered_map", "unordered_set", "queue", "stack", "deque", "string",
    "sort", "reverse", "min", "max", "swap", "abs", "memset", "fill",
}


def _avg_var_length(code: str) -> float:
    ids = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", code)
    user_ids = [
        i for i in ids
        if i not in _KEYWORDS and not i.startswith("_") and not i.isupper()
    ]
    if not user_ids:
        return 0.0
    return sum(len(i) for i in user_ids) / len(user_ids)


def extract_features(code: str) -> dict:
    """Numeric fingerprint of code style — used for cosine similarity."""
    lines = code.split("\n")
    nonblank = [l for l in lines if l.strip()]
    total = max(1, len(nonblank))
    comment_lines = sum(
        1 for l in lines if l.strip().startswith("//") or l.strip().startswith("/*")
    )
    return {
        "n_lines": float(total),
        "avg_line_len": sum(len(l) for l in nonblank) / total,
        "comment_ratio": comment_lines / total,
        "auto_per_line": len(re.findall(r"\bauto\b", code)) / total,
        "std_prefix_per_line": len(re.findall(r"std::", code)) / total,
        "using_ns_std": 1.0 if "using namespace std" in code else 0.0,
        "bits_stdc": 1.0 if "<bits/stdc++.h>" in code else 0.0,
        "uses_printf_scanf": 1.0 if re.search(r"\b(printf|scanf)\b", code) else 0.0,
        "uses_cin_cout": 1.0 if re.search(r"\b(cin|cout)\b", code) else 0.0,
        "endl_per_line": len(re.findall(r"\bendl\b", code)) / total,
        "long_long_per_line": len(re.findall(r"\blong\s+long\b", code)) / total,
        "lambda_count": float(len(re.findall(r"\[\s*[&=]?\s*\]\s*\(", code))),
        "var_avg_length": _avg_var_length(code),
        "single_letter_vars": len([
            m for m in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", code)
            if len(m) == 1 and m not in _KEYWORDS
        ]) / total,
        "uses_2space_indent": 1.0 if re.search(r"^  \S", code, re.M) and not re.search(r"^    \S", code, re.M) else 0.0,
        "uses_4space_indent": 1.0 if re.search(r"^    \S", code, re.M) else 0.0,
        "uses_tab_indent": 1.0 if re.search(r"^\t\S", code, re.M) else 0.0,
        "function_count": float(len(re.findall(
            r"^\s*(void|int|long\s+long|auto|double|bool|string)\s+\w+\s*\([^)]*\)\s*\{",
            code, re.M))),
    }


def _cosine_distance(a: dict, b: dict) -> float:
    keys = set(a.keys()) | set(b.keys())
    va = [a.get(k, 0.0) for k in keys]
    vb = [b.get(k, 0.0) for k in keys]
    dot = sum(x * y for x, y in zip(va, vb))
    na = math.sqrt(sum(x * x for x in va))
    nb = math.sqrt(sum(x * x for x in vb))
    if na == 0 or nb == 0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - dot / (na * nb)))


def compute_baseline(user_id: int, exclude_id: Optional[int] = None,
                     n_recent: int = 30) -> Optional[dict]:
    """Average feature vector of user's recent AC C/C++ submissions (excluding `exclude_id`).

    Returns None when there's < 3 baseline submissions.
    """
    from judge.models import Submission
    qs = (Submission.objects
          .filter(user_id=user_id, result="AC")
          .filter(language__key__in=["C", "CPP03", "CPP11", "CPP14", "CPP17", "CPP20"])
          .select_related("source")
          .order_by("-id"))
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    subs = list(qs[:n_recent])
    feats = []
    for s in subs:
        try:
            src = s.source.source
        except Exception:
            continue
        if not src or len(src) < 30:
            continue
        feats.append(extract_features(src))
    if len(feats) < 3:
        return None
    keys = feats[0].keys()
    return {k: sum(f[k] for f in feats) / len(feats) for k in keys}


def stylometry_score(features: dict, baseline: Optional[dict]) -> Optional[float]:
    """0-100: how DIFFERENT submission is from user's baseline. None if no baseline."""
    if baseline is None:
        return None
    d = _cosine_distance(features, baseline)
    # cosine distance is 0..1; amplify and clip.
    return min(100.0, d * 100.0 * 2.2)


# ─────────────────────────── COMBINED SCORE ──────────────────────────────
def compute_ai_score(submission) -> dict:
    """Compute combined suspicion score for a submission.

    Returns dict {score, stylometry, markers_score, markers_found, baseline_size}.
    """
    try:
        code = submission.source.source
    except Exception:
        return {"score": 0.0, "stylometry": None,
                "markers_score": 0.0, "markers_found": [], "baseline_size": 0}

    markers_score, markers_found = detect_markers(code)
    feats = extract_features(code)
    baseline = compute_baseline(submission.user_id, exclude_id=submission.id)
    sty = stylometry_score(feats, baseline)

    if sty is None:
        combined = markers_score
    else:
        combined = round(0.6 * markers_score + 0.4 * sty, 1)

    return {
        "score": round(min(combined, 100.0), 1),
        "stylometry": round(sty, 1) if sty is not None else None,
        "markers_score": markers_score,
        "markers_found": markers_found,
        "baseline_size": 0 if baseline is None else 1,
    }
