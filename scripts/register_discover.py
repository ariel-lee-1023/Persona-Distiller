#!/usr/bin/env python3
"""
register_discover.py — test whether corpus units may share one style baseline.

A whole-corpus average can hide a sharp division between, for example, spoken and
formal units. Once those unlike units are pooled, the resulting baseline describes
neither one and gives a later comparison a misleadingly easy target. This tool
makes a single-register conclusion evidence-led: it measures every supplied unit,
compares all pairs, prevents forced-incompatible pairs from merging, and leaves a
visible record of the decision.

Usage:
    python3 register_discover.py <dir-or-spec> [--json registers.json]
        [--lang zh|en|auto] [--min-chars N] [--ratio-threshold R]
        [--dims-threshold K] [--terms FILE] [--flagship-terms FILE]

Notes:
- Directory input treats each .txt, .md, or .markdown file as one unit. A JSON
  input has {"units": [{"unit_id": "...", "label": "...", "path": "..."}]}.
- The default Chinese connective list is copied from zh_metrics.py. English
  connectives are a small generic discourse list. Both are measurement defaults,
  not a claim about any subject.
- The simple dependency-free tokenisers match zh_metrics.py and style_metrics.py:
  Chinese sentence lengths are Han characters; English sentence lengths are
  Latin-word tokens. This is robust-enough signal, not linguistic ground truth.
"""

import argparse
import datetime as dt
import json
import math
import os
import re
import statistics
import sys
from register_evidence import analyze_units

HAN = re.compile(r"[一-鿿]")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
ZH_SENT_END = re.compile(r"[。！？!?…]+")
EN_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[\"'(A-Z0-9])")

HEDGES_ZH = ["也许", "也許", "或许", "或許", "可能", "大概", "似乎", "恐怕", "我觉得", "我覺得",
             "我认为", "我認為", "个人认为", "個人認為", "在我看来", "在我看來", "差不多",
             "基本上", "多半", "大体", "大體", "一般来说", "一般來說", "某种程度", "某種程度"]
BOOSTERS_ZH = ["一定", "必然", "肯定", "绝对", "絕對", "根本", "完全", "毫无疑问", "毫無疑問",
               "当然", "當然", "显然", "顯然", "无非", "無非", "从来", "從來", "永远", "永遠",
               "只能", "必定"]
# Copied, rather than imported, so this script remains independently runnable.
CONNECTIVES_ZH = ["首先", "其次", "综上所述", "綜上所述", "总而言之", "總而言之", "总的来说",
                  "總的來說", "值得注意的是", "众所周知", "眾所周知", "不可否认", "不可否認",
                  "笔者", "筆者", "本文", "客观地说", "客觀地說", "坦率地说", "坦率地說",
                  "从某种意义上说", "從某種意義上說", "需要指出的是", "换句话说", "換句話說",
                  "也就是说", "也就是說", "实际上", "實際上", "事实上", "事實上"]
FIRST_ZH = ["我们", "我們", "我", "咱们", "咱們"]
SECOND_ZH = ["你们", "你們", "你", "您"]
HEDGES_EN = {"perhaps", "maybe", "possibly", "arguably", "seemingly", "apparently", "roughly",
             "somewhat", "fairly", "rather", "quite", "presumably", "supposedly", "probably",
             "likely", "seems", "seem", "seemed", "suggests", "suggest", "tends", "tend",
             "might", "could", "may", "conceivably", "ostensibly", "sort", "kind"}
BOOSTERS_EN = {"obviously", "clearly", "certainly", "undoubtedly", "definitely", "surely",
               "plainly", "evidently", "indeed", "absolutely", "always", "never", "must",
               "unquestionably", "manifestly"}
CONNECTIVES_EN = {"first", "second", "therefore", "however", "moreover", "furthermore", "thus",
                  "hence", "indeed", "otherwise", "meanwhile", "nevertheless", "consequently"}
FIRST_EN = {"i", "me", "my", "we", "us", "our"}
SECOND_EN = {"you", "your", "yours"}

DIMENSIONS = [
    "mean_sentence_len", "median_sentence_len", "p90_sentence_len", "long_sentence_share",
    "question_rate", "connective_rate", "hedge_rate", "booster_rate", "second_person_rate",
    "first_person_rate", "title_mark_rate", "core_term_density", "flagship_term_density",
]


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def load_terms(path):
    if not path:
        return []
    with open(path, encoding="utf-8", errors="replace") as fh:
        return [line.strip() for line in fh if line.strip()]


def collect_units(path):
    if os.path.isdir(path):
        result = []
        for root, _, names in os.walk(path):
            for name in sorted(names):
                if name.lower().endswith((".txt", ".md", ".markdown")):
                    full = os.path.join(root, name)
                    result.append({"unit_id": os.path.splitext(name)[0], "label": name, "path": full})
        return result
    with open(path, encoding="utf-8") as fh:
        spec = json.load(fh)
    if not isinstance(spec.get("units"), list) or not spec["units"]:
        raise ValueError("JSON spec needs a non-empty 'units' array")
    base = os.path.dirname(os.path.abspath(path))
    result = []
    for i, raw in enumerate(spec["units"], 1):
        if not isinstance(raw, dict) or not raw.get("path"):
            raise ValueError("every unit needs a path")
        item = dict(raw)
        item["unit_id"] = str(item.get("unit_id") or "u%02d" % i)
        item["label"] = str(item.get("label") or item["unit_id"])
        if not os.path.isabs(item["path"]):
            item["path"] = os.path.join(base, item["path"])
        result.append(item)
    return result


def percentile_90(values):
    if not values:
        return 0.0
    ordered = sorted(values)
    return float(ordered[min(len(ordered) - 1, int(0.9 * len(ordered)))])


def detect_lang(text, requested):
    if requested != "auto":
        return requested
    nonspace = [ch for ch in text if not ch.isspace()]
    share = len(HAN.findall(text)) / len(nonspace) if nonspace else 0.0
    return "zh" if share > 0.3 else "en"


def count_phrases(text, terms, lowercase=False):
    source = text.lower() if lowercase else text
    return sum(source.count(term.lower() if lowercase else term) for term in terms)


def features_zh(text, terms, flagship):
    n = len(HAN.findall(text))
    sents = [s for s in ZH_SENT_END.split(text) if HAN.search(s)]
    lengths = [len(HAN.findall(s)) for s in sents if HAN.search(s)]
    per_10k = lambda count: 10000.0 * count / n if n else 0.0
    return {
        "mean_sentence_len": statistics.mean(lengths) if lengths else 0.0,
        "median_sentence_len": float(statistics.median(lengths)) if lengths else 0.0,
        "p90_sentence_len": percentile_90(lengths),
        "long_sentence_share": sum(x > 40 for x in lengths) / len(lengths) if lengths else 0.0,
        "question_rate": per_10k(text.count("？") + text.count("?")),
        "connective_rate": per_10k(count_phrases(text, CONNECTIVES_ZH)),
        "hedge_rate": per_10k(count_phrases(text, HEDGES_ZH)),
        "booster_rate": per_10k(count_phrases(text, BOOSTERS_ZH)),
        "second_person_rate": per_10k(count_phrases(text, SECOND_ZH)),
        "first_person_rate": per_10k(count_phrases(text, FIRST_ZH)),
        "title_mark_rate": per_10k(text.count("《")),
        "core_term_density": per_10k(count_phrases(text, terms)),
        "flagship_term_density": per_10k(count_phrases(text, flagship)),
    }


def features_en(text, terms, flagship):
    words = [word.lower() for word in WORD_RE.findall(text)]
    n = len(words)
    sents = [s.strip() for s in EN_SENT_SPLIT.split(text.strip()) if s.strip()]
    lengths = [len(WORD_RE.findall(s)) for s in sents if WORD_RE.findall(s)]
    counts = {word: words.count(word) for word in set(words)}
    per_10k = lambda count: 10000.0 * count / n if n else 0.0
    term_text = text.lower()
    return {
        "mean_sentence_len": statistics.mean(lengths) if lengths else 0.0,
        "median_sentence_len": float(statistics.median(lengths)) if lengths else 0.0,
        "p90_sentence_len": percentile_90(lengths),
        "long_sentence_share": sum(x > 30 for x in lengths) / len(lengths) if lengths else 0.0,
        "question_rate": per_10k(text.count("?")),
        "connective_rate": per_10k(sum(counts.get(w, 0) for w in CONNECTIVES_EN)),
        "hedge_rate": per_10k(sum(counts.get(w, 0) for w in HEDGES_EN)),
        "booster_rate": per_10k(sum(counts.get(w, 0) for w in BOOSTERS_EN)),
        "second_person_rate": per_10k(sum(counts.get(w, 0) for w in SECOND_EN)),
        "first_person_rate": per_10k(sum(counts.get(w, 0) for w in FIRST_EN)),
        "title_mark_rate": 0.0,
        "core_term_density": per_10k(count_phrases(term_text, terms, lowercase=True)),
        "flagship_term_density": per_10k(count_phrases(term_text, flagship, lowercase=True)),
    }


def ratios(a, b):
    out = {}
    for dim in DIMENSIONS:
        x, y = a[dim], b[dim]
        if x == 0 and y == 0:
            out[dim] = 1.0
        elif x == 0 or y == 0:
            out[dim] = None
        else:
            out[dim] = max(x, y) / max(min(x, y), 1e-12)
    return out


def z_distance_matrix(units):
    values = {dim: [u["features"][dim] for u in units] for dim in DIMENSIONS}
    means = {dim: statistics.mean(vals) for dim, vals in values.items()}
    sds = {dim: statistics.pstdev(vals) for dim, vals in values.items()}
    z = []
    for unit in units:
        z.append({dim: (unit["features"][dim] - means[dim]) / sds[dim] if sds[dim] else 0.0
                  for dim in DIMENSIONS})
    matrix = []
    for i in range(len(units)):
        matrix.append([sum(abs(z[i][d] - z[j][d]) for d in DIMENSIONS) / len(DIMENSIONS)
                       for j in range(len(units))])
    return z, matrix


def cluster(units, distance, forced):
    groups = [{i} for i in range(len(units))]
    merges = []
    while True:
        candidates = []
        for a in range(len(groups)):
            for b in range(a + 1, len(groups)):
                if any(tuple(sorted((i, j))) in forced for i in groups[a] for j in groups[b]):
                    continue
                pairs = [distance[i][j] for i in groups[a] for j in groups[b]]
                candidates.append((sum(pairs) / len(pairs), a, b))
        if not candidates:
            break
        height, a, b = min(candidates, key=lambda item: (item[0], sorted(item[1:])) )
        merged = groups[a] | groups[b]
        merges.append((height, [set(x) for x in groups], a, b))
        groups = [g for idx, g in enumerate(groups) if idx not in (a, b)] + [merged]

    # Only supported incompatible pairs prevent pooling. A gap in standardized
    # distances alone can amplify a single sparse event into a false family.
    return [set(x) for x in groups], [m[0] for m in merges]


def rank(values):
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    result = [0.0] * len(values)
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and ordered[j + 1][1] == ordered[i][1]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            result[ordered[k][0]] = avg
        i = j + 1
    return result


def spearman(a, b):
    ra, rb = rank(a), rank(b)
    ma, mb = statistics.mean(ra), statistics.mean(rb)
    numerator = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    denom = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return numerator / denom if denom else 0.0


def gradient(member_indices, units):
    if len(member_indices) < 3:
        return None
    best = None
    for dim in DIMENSIONS:
        values = [units[i]["features"][dim] for i in member_indices]
        consistent = sum(
            1 for other in DIMENSIONS if other != dim and
            abs(spearman(values, [units[i]["features"][other] for i in member_indices])) >= 0.9
        )
        candidate = (consistent, dim, values)
        if best is None or candidate[:2] > best[:2]:
            best = candidate
    if best and best[0] >= 3:
        return {"axis": best[1], "order": [units[i]["unit_id"] for i in sorted(
            member_indices, key=lambda x: (units[x]["features"][best[1]], units[x]["unit_id"]))]}
    return None


def printable_ratio(value):
    return "undefined (zero denominator)" if value is None else "%.2f" % value


def main():
    ap = argparse.ArgumentParser(description="Discover incompatible style registers before pooling units.")
    ap.add_argument("path", help="directory of text units, or JSON unit spec")
    ap.add_argument("--json", help="write registers JSON artifact here")
    ap.add_argument("--lang", choices=("zh", "en", "auto"), default="auto")
    ap.add_argument("--min-chars", type=int, default=0, help="exclude units shorter than N characters (default 0)")
    ap.add_argument("--ratio-threshold", type=float, default=3.0)
    ap.add_argument("--dims-threshold", type=int, default=3)
    ap.add_argument("--terms", help="file with core terms, one per line")
    ap.add_argument("--flagship-terms", help="file with flagship terms, one per line")
    ap.add_argument("--min-tokens", type=int, default=600)
    ap.add_argument("--min-events", type=int, default=5)
    ap.add_argument("--min-rate-delta", type=float, default=10, help="minimum absolute difference per 10k tokens")
    ap.add_argument("--subsamples", type=int, default=3)
    ap.add_argument("--min-stability", type=float, default=.8)
    args = ap.parse_args()
    if (args.min_chars < 0 or not math.isfinite(args.ratio_threshold) or args.ratio_threshold <= 1 or args.dims_threshold < 1
            or args.min_tokens < 1 or args.min_events < 1 or not math.isfinite(args.min_rate_delta)
            or args.min_rate_delta <= 0 or args.subsamples < 3 or not .5 < args.min_stability <= 1):
        ap.error("thresholds must be positive (and --min-chars cannot be negative)")
    if not os.path.exists(args.path):
        ap.error("path not found: %s" % args.path)

    try:
        raw_units = collect_units(args.path)
        terms, flagship = load_terms(args.terms), load_terms(args.flagship_terms)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        ap.error(str(exc))
    units = []
    raw_texts = []
    for raw in raw_units:
        if not os.path.exists(raw["path"]):
            ap.error("unit path not found: %s" % raw["path"])
        text = read_text(raw["path"])
        if len(text) < args.min_chars:
            continue
        raw_texts.append(text)
        lang = detect_lang(text, args.lang)
        feats = features_zh(text, terms, flagship) if lang == "zh" else features_en(text, terms, flagship)
        units.append({"unit_id": raw["unit_id"], "label": raw["label"], "chars": len(text),
                      "lang": lang, "features": {key: round(value, 6) for key, value in feats.items()}})
    if not units:
        ap.error("no units remain after --min-chars filtering")
    if len({u["unit_id"] for u in units}) != len(units):
        ap.error("unit_id values must be unique")

    langs = sorted(set(u["lang"] for u in units))
    if len(langs) != 1:
        ap.error("mixed languages require separate comparable discovery runs")
    lang = langs[0]
    measure = lambda text: features_zh(text, terms, flagship) if lang == "zh" else features_en(text, terms, flagship)
    sentence_count = lambda text: len([x for x in (ZH_SENT_END.split(text) if lang == "zh" else EN_SENT_SPLIT.split(text)) if (HAN if lang == "zh" else WORD_RE).search(x)])
    observations, pairs, forced, stability, windows = analyze_units(raw_texts, measure, HAN if lang == "zh" else WORD_RE,
        sentence_count, DIMENSIONS, args.ratio_threshold, args.dims_threshold, args.min_tokens,
        args.min_events, args.min_rate_delta, args.subsamples, args.min_stability)
    for unit, observation in zip(units, observations):
        unit['observations'] = observation
    _, distance = z_distance_matrix(units)
    n = len(units)
    ratio_exceedances = [[0] * n for _ in range(n)]
    forced_splits = []
    for (i, j), exceeded in pairs.items():
        pair_ratios = ratios(units[i]["features"], units[j]["features"])
        ratio_exceedances[i][j] = ratio_exceedances[j][i] = len(exceeded)
        if (i, j) in forced:
            forced_splits.append({"a": units[i]["unit_id"], "b": units[j]["unit_id"],
                                  "dimensions": exceeded, "ratios": {d: pair_ratios[d] for d in exceeded}})
    groups, heights = cluster(units, distance, forced)
    def same_family(partition, i, j):
        return any(i in group and j in group for group in partition)
    agreements = []
    for features, sample_forced in windows:
        sample_units = [{'features': f} for f in features]
        _, sample_distance = z_distance_matrix(sample_units)
        sample_groups, _ = cluster(sample_units, sample_distance, sample_forced)
        agreements.append({(i, j): same_family(groups, i, j) == same_family(sample_groups, i, j)
                           for i in range(n) for j in range(i + 1, n)})
    family_agreement = min((sum(a[pair] for a in agreements) / len(agreements) for pair in pairs), default=0) if agreements else 0
    stability['family_agreement'] = family_agreement
    stability['stable'] = stability['stable'] and family_agreement >= args.min_stability
    groups = sorted(groups, key=lambda group: min(units[i]["unit_id"] for i in group))
    families = []
    for index, members in enumerate(groups, 1):
        member_indices = sorted(members, key=lambda i: units[i]["unit_id"])
        centroid = {dim: round(statistics.mean(units[i]["features"][dim] for i in member_indices), 6)
                    for dim in DIMENSIONS}
        family = {"family_id": "R%d" % index, "label": None,
                  "members": [units[i]["unit_id"] for i in member_indices], "centroid": centroid}
        found_gradient = gradient(member_indices, units)
        if found_gradient:
            family["gradient"] = found_gradient["order"]
            family["gradient_axis"] = found_gradient["axis"]
        families.append(family)
    gap_table = []
    for dim in DIMENSIONS:
        by_family = {family["family_id"]: round(statistics.mean(
            units[next(i for i, u in enumerate(units) if u["unit_id"] == member)]["features"][dim]
            for member in family["members"]), 6) for family in families}
        vals = list(by_family.values())
        if not vals or all(v == 0 for v in vals):
            maximum = 1.0
        elif any(v == 0 for v in vals):
            maximum = None
        else:
            maximum = max(vals) / max(min(vals), 1e-12)
        gap_table.append({"dimension": dim, "by_family": by_family, "max_ratio": maximum})
    gap_table.sort(key=lambda row: (row["max_ratio"] is not None, -(row["max_ratio"] or 0)))
    langs = sorted(set(u["lang"] for u in units))
    result = {
        "generated": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "lang": langs[0] if len(langs) == 1 else "mixed",
        "n_units": n, "n_registers": len(families),
        "thresholds": {"ratio": args.ratio_threshold, "dims": args.dims_threshold, "min_tokens": args.min_tokens,
                       "min_events": args.min_events, "min_rate_delta": args.min_rate_delta},
        "stability": stability,
        "units": [{k: v for k, v in u.items() if k != "lang"} for u in units],
        "distance_matrix": {"units": [u["unit_id"] for u in units], "z_distance": distance,
                            "ratio_exceedances": ratio_exceedances},
        "families": families, "gap_table": gap_table, "forced_splits": forced_splits,
        "verdict": "SINGLE_REGISTER" if len(families) == 1 else "MULTI_REGISTER",
    }
    if not stability['stable']:
        result.update(verdict='INSUFFICIENT_EVIDENCE', n_registers=0, families=[])
        result['notes'] = 'Too little comparable text or unstable equal-length subsamples; no register conclusion.'
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False, allow_nan=False)
            fh.write("\n")
        print("wrote %s" % args.json)

    print("\n=== register discovery ===")
    print("unit                 lang  chars  mean-sent  question/10k  hedge/10k  boost/10k")
    for unit in units:
        f = unit["features"]
        print("%-20s %-4s %6d %10.2f %13.2f %10.2f %10.2f" % (
            unit["unit_id"], unit["lang"], unit["chars"], f["mean_sentence_len"], f["question_rate"],
            f["hedge_rate"], f["booster_rate"]))
    print("\nFamily assignment:" if stability["stable"] else "\nProvisional families (insufficient evidence; not a release conclusion):")
    for family in families:
        print("  %s: %s" % (family["family_id"], ", ".join(family["members"])))
    print("\nFamily gap table (largest cross-family ratios first):")
    for row in gap_table:
        means = ", ".join("%s=%g" % (key, value) for key, value in row["by_family"].items())
        print("  %-25s max ratio %-6s  %s" % (row["dimension"], printable_ratio(row["max_ratio"]), means))
    if forced_splits:
        print("\nForced splits:")
        for item in forced_splits:
            dims = ", ".join("%s=%s" % (d, printable_ratio(item["ratios"][d])) for d in item["dimensions"])
            print("  %s <> %s: %s" % (item["a"], item["b"], dims))
    else:
        print("\nForced splits: none")
    gradients = [family for family in families if family.get("gradient")]
    if gradients:
        print("\nWithin-family gradients (these must NOT be split into separate families):")
        for family in gradients:
            g = family["gradient"]
            print("  %s: %s -> %s" % (family["family_id"], family["gradient_axis"], ", ".join(g)))
    if result["verdict"] == "SINGLE_REGISTER":
        print("\nRequired evidence for a single-family claim: full z-distance matrix")
        header = "          " + " ".join("%9s" % u["unit_id"] for u in units)
        print(header)
        for unit, row in zip(units, distance):
            print("%-9s %s" % (unit["unit_id"], " ".join("%9.3f" % value for value in row)))
    print("\nVERDICT: %s" % result["verdict"])
    if result["verdict"] == "MULTI_REGISTER":
        print("Families may not be pooled into one baseline. A discrimination test is now mandatory.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
