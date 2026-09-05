#!/usr/bin/env python3
"""
validate_package.py — machine-check the structural safety rails of a package.

A package can read plausibly while still putting ledger material in a runtime
reference, leaving a cluster load-list dead, or exposing implementation language in
the core description. Those are mechanical failures, but a prose-only checklist
makes them easy to miss. This tool checks the mechanical subset consistently and
leaves judgment calls visible as warnings rather than pretending they are solved.

Usage:
    python3 validate_package.py <persona-project-dir> [--json validation.json] [--strict]
        [--headings FILE]

Notes:
- YAML frontmatter uses a deliberately small key: value reader; no YAML dependency
  is required. It is sufficient for the name and description fields this check uses.
- C3 is skipped with a warning unless --headings supplies one required heading
  anchor per line. This is deliberate: cores may be written in the subject's own
  language, so the checker must not impose English headings by default.
- The episodic near-empty size floor is 80 non-whitespace characters. A heading
  containing "why" or "为什么" explains a legitimate small file.
"""

import argparse
import json
import os
import re
import sys

AUDIT_WORDS = ("token", "budget", "cluster", "probe", "corpus", "distill", "score")
BAN_STRINGS = ("provenance", "episodic.md", "extraction", "holdout", "Stage ",
               "token budget", "composite score", "probe")
IMPERATIVES = {"add", "avoid", "choose", "consider", "do", "ensure", "keep", "make", "note", "prefer",
               "remove", "remember", "use", "write"}
EPISODIC_FLOOR = 80
SCORE_PATTERN = re.compile(
    r"(?:composite|projectibility|cost_refusal|expressive_match|interactional|preoccupation)\s*"
    r"(?:score)?\s*[:=]?\s*[-+]?\d+(?:\.\d+)?", re.I)
CITATION_RE = re.compile(r"\bc\d{2}\b", re.I)
MODULE_UID_RE = re.compile(r"^\s*(?:uid|cluster_id)\s*:\s*(c\d{2})\b", re.I | re.M)


def markdown_files(root):
    for directory, _, names in os.walk(root):
        for name in sorted(names):
            if name.lower().endswith(".md"):
                yield os.path.join(directory, name)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def rel(path, root):
    return os.path.relpath(path, root).replace(os.sep, "/")


def frontmatter(text):
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        match = re.match(r"^([^:#][^:]*):\s*(.*?)\s*$", line)
        if match:
            key, value = match.groups()
            fields[key.strip()] = value.strip().strip("'\"")
    return None


def first_section_heading(text):
    """Return the first H2-or-deeper section, ignoring a document-title H1."""
    fallback = ""
    for line in text.splitlines():
        match = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match:
            if not fallback:
                fallback = match.group(2).strip()
            if len(match.group(1)) >= 2:
                return match.group(2).strip()
    return fallback


def check(check_id, level, ok, detail):
    return {"check": check_id, "level": level, "ok": bool(ok), "detail": detail}


def resolve_module_ids(module_paths):
    ids = set()
    for path in module_paths:
        name = os.path.splitext(os.path.basename(path))[0].lower()
        match = re.match(r"(c\d{2})\b", name, re.I)
        if match:
            ids.add(match.group(1).lower())
        # A non-prefixed module can declare a UID explicitly. Do not infer IDs
        # from ordinary citations in its body: that would make a dead link appear
        # resolved merely because another module mentioned the same cNN token.
        for token in MODULE_UID_RE.findall(read(path)):
            ids.add(token.lower())
    return ids


def main():
    ap = argparse.ArgumentParser(description="Machine-check a distilled package's structural rules.")
    ap.add_argument("package_dir", help="persona project root containing .agents/skills/<name>/")
    ap.add_argument("--json", help="write check artifact here")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--headings", help="file of required core heading anchors, one per line")
    args = ap.parse_args()
    root = os.path.abspath(args.package_dir)
    if not os.path.isdir(root):
        ap.error("package directory not found: %s" % args.package_dir)

    skills_home = os.path.join(root, ".agents", "skills")
    skill_roots = []
    if os.path.isdir(skills_home):
        for name in sorted(os.listdir(skills_home)):
            candidate = os.path.join(skills_home, name)
            if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, "SKILL.md")):
                skill_roots.append(candidate)

    # Keep checking after a layout failure so one run reports all useful findings.
    skill_root = skill_roots[0] if len(skill_roots) == 1 else os.path.join(skills_home, "<skill-name>")
    skill = os.path.join(skill_root, "SKILL.md")
    references = os.path.join(skill_root, "references")
    clusters_dir = os.path.join(references, "clusters")
    provenance = os.path.join(root, "fidelity-ledger", "provenance.md")
    episodic = os.path.join(root, "fidelity-ledger", "episodic.md")
    results = []

    layout_ok = len(skill_roots) == 1
    layout_detail = (
        "one discoverable skill exists under .agents/skills/"
        if layout_ok else
        "expected exactly one .agents/skills/<name>/SKILL.md; found %d" % len(skill_roots)
    )
    results.append(check("S1", "error", layout_ok, layout_detail))
    results.append(check("S2", "error", os.path.isfile(skill),
                         "SKILL.md exists inside the discovered skill directory"
                         if os.path.isfile(skill) else
                         "missing .agents/skills/<name>/SKILL.md"))
    refs_ok = os.path.isdir(references) and os.path.isfile(os.path.join(references, "voice.md")) and os.path.isfile(os.path.join(references, "frameworks.md"))
    results.append(check("S3", "error", refs_ok,
                         "references/, voice.md, and frameworks.md present" if refs_ok else "need references/ with voice.md and frameworks.md"))
    prov_ok = os.path.isfile(provenance)
    results.append(check("S4", "error", prov_ok, "fidelity-ledger/provenance.md present outside .agents/" if prov_ok else "missing project-level fidelity-ledger/provenance.md"))
    results.append(check("S4", "warn", os.path.isfile(episodic),
                         "fidelity-ledger/episodic.md present" if os.path.isfile(episodic) else "episodic.md absent (permitted but expected when episodic material exists)"))
    misplaced = []
    if os.path.isdir(references):
        for path in markdown_files(references):
            if os.path.basename(path) in ("provenance.md", "episodic.md"):
                misplaced.append(rel(path, root))
    results.append(check("S5", "error", not misplaced,
                         "no ledger files under references/" if not misplaced else "ledger file(s) wrongly under references/: " + ", ".join(misplaced)))
    modules = list(markdown_files(clusters_dir)) if os.path.isdir(clusters_dir) else []
    results.append(check("S6", "error", os.path.isdir(clusters_dir),
                         "cluster modules directory is references/clusters/" if os.path.isdir(clusters_dir) else "missing references/clusters/"))

    core = read(skill) if os.path.isfile(skill) else ""
    fields = frontmatter(core) if core else None
    c1_ok = fields is not None and bool(fields.get("name")) and bool(fields.get("description"))
    results.append(check("C1", "error", c1_ok,
                         "frontmatter has name and description" if c1_ok else "frontmatter needs non-empty name and description"))
    path_name = os.path.basename(skill_root)
    declared_name = fields.get("name", "") if fields else ""
    results.append(check("C1b", "error", bool(declared_name) and declared_name == path_name,
                         "frontmatter name matches .agents/skills directory"
                         if declared_name == path_name else
                         "frontmatter name '%s' must match skill directory '%s'" % (declared_name or "<missing>", path_name)))
    description = fields.get("description", "") if fields else ""
    found_audit = [word for word in AUDIT_WORDS if re.search(r"\b%s\b" % re.escape(word), description, re.I)]
    c2_ok = bool(description.strip()) and not found_audit
    results.append(check("C2", "error", c2_ok,
                         "description is non-empty and runtime-facing" if c2_ok else
                         "description empty or contains audit/meta vocabulary: " + ", ".join(found_audit)))
    if args.headings:
        try:
            anchors = [line.strip() for line in read(args.headings).splitlines() if line.strip() and not line.lstrip().startswith("#")]
        except OSError as exc:
            ap.error(str(exc))
        heading_text = "\n".join(re.findall(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", core, re.M))
        absent = [anchor for anchor in anchors if anchor.casefold() not in heading_text.casefold()]
        results.append(check("C3", "error", bool(anchors) and not absent,
                             "all configured heading anchors present" if anchors and not absent else
                             ("headings file contained no anchors" if not anchors else "missing heading anchors: " + ", ".join(absent))))
    else:
        results.append(check("C3", "warn", True,
                             "skipped: no --headings file supplied (subject-language cores need supplied anchors)"))
    found_bans = [value for value in BAN_STRINGS if value.casefold() in core.casefold()]
    results.append(check("C4", "error", not found_bans,
                         "no banned implementation strings in core" if not found_bans else "banned strings in core: " + ", ".join(found_bans)))
    on_disk = {os.path.basename(path) for path in modules}
    # A core may use full references/clusters paths or a compact code-form filename
    # after an earlier fully-qualified path in the same load-list sentence.
    referenced = {name for name in on_disk if re.search(
        r"(?:references/clusters/)?%s\b" % re.escape(name), core, re.I)}
    missing = sorted(referenced - on_disk)
    unreferenced = sorted(on_disk - referenced)
    c5_ok = not missing and not unreferenced
    details = []
    if missing:
        details.append("referenced but missing: " + ", ".join(missing))
    if unreferenced:
        details.append("on disk but not in core: " + ", ".join(unreferenced))
    results.append(check("C5", "error", c5_ok, "cluster load-list and disk agree" if c5_ok else "; ".join(details)))
    known_ids = resolve_module_ids(modules)
    cited = set()
    for path in markdown_files(root):
        cited.update(token.lower() for token in CITATION_RE.findall(read(path)))
    unresolved = sorted(cited - known_ids)
    results.append(check("C6", "error", not unresolved,
                         "all cNN citations resolve to a module" if not unresolved else "unresolved cluster citations: " + ", ".join(unresolved)))

    if os.path.isfile(provenance):
        bad_lines = []
        for number, line in enumerate(read(provenance).splitlines(), 1):
            stripped = line.strip()
            first = re.match(r"^([A-Za-z]+)\b", stripped)
            imperative = first and first.group(1).lower() in IMPERATIVES
            second_person = bool(re.search(r"\byou\b", line, re.I) or "你" in line)
            if imperative or second_person:
                bad_lines.append(str(number))
        results.append(check("L1", "warn", not bad_lines,
                             "no second-person or bare-English-imperative lines found" if not bad_lines else
                             "possible second-person/imperative line(s): " + ", ".join(bad_lines)))
        heading = first_section_heading(read(provenance))
        l2_ok = "weights" in heading.casefold() or "权重" in heading
        results.append(check("L2", "error", l2_ok,
                             "first provenance heading identifies weights" if l2_ok else
                             "first provenance heading must contain 'weights' or '权重' (found: %s)" % (heading or "none")))
    else:
        results.append(check("L1", "warn", True, "skipped: provenance.md is missing (reported by S3)"))
        results.append(check("L2", "error", False, "cannot check first provenance heading because provenance.md is missing"))
    if os.path.isfile(episodic):
        content = read(episodic)
        meaningful = len(re.sub(r"\s+", "", content)) > EPISODIC_FLOOR
        explains = bool(re.search(r"^\s{0,3}#{1,6}\s+.*(?:why|为什么)", content, re.I | re.M))
        results.append(check("L3", "error", meaningful or explains,
                             "episodic.md exceeds near-empty floor" if meaningful else
                             ("episodic.md explains its small size" if explains else "episodic.md is near-empty without a why/为什么 section")))
    else:
        results.append(check("L3", "error", True, "not applicable: episodic.md is absent"))
    score_files = []
    if os.path.isdir(references):
        for path in markdown_files(references):
            if SCORE_PATTERN.search(read(path)):
                score_files.append(rel(path, root))
    results.append(check("X1", "error", not score_files,
                         "references contain no numeric composite/probe score pattern" if not score_files else
                         "numeric score pattern under references/: " + ", ".join(score_files)))

    effective = [{**item, "effective_level": "error" if args.strict and item["level"] == "warn" else item["level"]}
                 for item in results]
    failed = [item for item in effective if not item["ok"] and item["effective_level"] == "error"]
    artifact = {"package": root, "skill_root": skill_root, "strict": args.strict, "checks": effective,
                "errors": len(failed), "warnings": sum(not x["ok"] and x["level"] == "warn" for x in effective),
                "verdict": "FAIL" if failed else "PASS"}
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(artifact, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print("wrote %s" % args.json)
    print("\n=== package validation ===")
    print("check  level  result  detail")
    for item in effective:
        outcome = "OK" if item["ok"] else "FAIL"
        level = item["effective_level"]
        print("%-5s %-6s %-6s %s" % (item["check"], level, outcome, item["detail"]))
    print("\n%s — %d error(s), %d warning(s)%s" % (
        artifact["verdict"], artifact["errors"], artifact["warnings"], " (warnings promoted by --strict)" if args.strict else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
