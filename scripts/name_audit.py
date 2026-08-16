#!/usr/bin/env python3
"""
name_audit.py — back-check package labels against literal corpus evidence.

A neat diagnostic label can be invented during distillation or inherited from an
editorial heading, then quietly acquire the authority of a firsthand coinage. This
tool prevents that drift by looking for each package name literally in the supplied
corpus, separating heading-like appearances from ordinary prose, and making thin
support impossible to overlook.

Usage:
    python3 name_audit.py --package PACKAGE --corpus CORPUS [--names FILE]
        [--json audit.json] [--min-hits N] [--editorial-markers FILE]

Notes:
- Without --names, candidates come from bold runs, quoted runs, book-title marks,
  and Markdown headings in package .md files. Candidates are deduplicated and kept
  only when their length is 2..20 characters and they are not pure punctuation or
  numbers.
- KWIC contexts use kwic.py's dependency-free convention: whitespace is normalised,
  with 250 characters left and 900 characters right of the first literal hit.
- Editorial markers are Python regexes, one per line. Without them, a short,
  unpunctuated line surrounded by blank lines is treated as heading-like.
"""

import argparse
import json
import os
import re
import sys

WS = re.compile(r"\s+")
END_PUNCT = re.compile(r"[。！？!?…]\s*$")


def iter_markdown(path):
    for root, _, names in os.walk(path):
        for name in sorted(names):
            if name.lower().endswith(".md"):
                yield os.path.join(root, name)


def iter_corpus(path):
    if os.path.isfile(path):
        yield path
        return
    for root, _, names in os.walk(path):
        for name in sorted(names):
            if name.lower().endswith((".txt", ".md", ".markdown")):
                yield os.path.join(root, name)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def usable(value):
    value = value.strip().strip("“”\"'「」《》")
    if not 2 <= len(value) <= 20:
        return None
    if not re.search(r"[^\W\d_]", value, re.UNICODE):
        return None
    return value


def harvest(package):
    found = []
    for path in iter_markdown(package):
        text = read(path)
        candidates = []
        candidates.extend(re.findall(r"\*\*([^*\n]+?)\*\*", text))
        candidates.extend(re.findall(r"「([^」\n]+)」", text))
        candidates.extend(re.findall(r"《([^》\n]+)》", text))
        candidates.extend(re.findall(r'(?<!\\)"([^"\n]+)"', text))
        candidates.extend(re.findall(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", text, re.M))
        for candidate in candidates:
            clean = usable(re.sub(r"[*`_]+", "", candidate))
            if clean:
                found.append(clean)
    return sorted(set(found), key=lambda value: (value.casefold(), value))


def load_names(path):
    return [line.strip() for line in read(path).splitlines() if usable(line.strip())]


def line_info(text, offset):
    starts = [0]
    for match in re.finditer("\n", text):
        starts.append(match.end())
    line_no = max(i for i, start in enumerate(starts) if start <= offset)
    lines = text.splitlines()
    line = lines[line_no] if line_no < len(lines) else ""
    before_blank = line_no > 0 and not lines[line_no - 1].strip()
    after_blank = line_no + 1 < len(lines) and not lines[line_no + 1].strip()
    return line, before_blank, after_blank


def suspicious(line, before_blank, after_blank, markers):
    if markers:
        return any(rx.search(line) for rx in markers)
    return len(line.strip()) < 30 and not END_PUNCT.search(line) and before_blank and after_blank


def first_kwic(text, offset, length):
    normalised = WS.sub(" ", text)
    # Convert the raw offset to a safe normalised offset by normalising the prefix.
    position = len(WS.sub(" ", text[:offset]))
    left, right = max(0, position - 250), min(len(normalised), position + length + 900)
    return "…%s…" % normalised[left:right]


def main():
    ap = argparse.ArgumentParser(description="Audit named package constructs against literal corpus hits.")
    ap.add_argument("--package", required=True, help="package directory")
    ap.add_argument("--corpus", required=True, help="corpus directory or file")
    ap.add_argument("--names", help="one literal name per line; omit to harvest package candidates")
    ap.add_argument("--json", help="write audit JSON here")
    ap.add_argument("--min-hits", type=int, default=2)
    ap.add_argument("--editorial-markers", help="file of line regexes that mark editorial material")
    args = ap.parse_args()
    if args.min_hits < 1:
        ap.error("--min-hits must be at least 1")
    if not os.path.isdir(args.package):
        ap.error("package directory not found: %s" % args.package)
    if not os.path.exists(args.corpus):
        ap.error("corpus path not found: %s" % args.corpus)
    try:
        names = load_names(args.names) if args.names else harvest(args.package)
        marker_patterns = []
        if args.editorial_markers:
            marker_patterns = [re.compile(line) for line in read(args.editorial_markers).splitlines()
                               if line.strip() and not line.lstrip().startswith("#")]
    except (OSError, re.error) as exc:
        ap.error(str(exc))
    names = sorted(set(names), key=lambda value: (value.casefold(), value))
    files = list(iter_corpus(args.corpus))
    if not files:
        ap.error("no .txt/.md/.markdown corpus files found")

    rows = []
    for name in names:
        hits = heading_hits = 0
        all_files, prose_files = set(), set()
        context = None
        for path in files:
            text = read(path)
            for match in re.finditer(re.escape(name), text):
                hits += 1
                all_files.add(os.path.basename(path))
                line, before_blank, after_blank = line_info(text, match.start())
                is_heading = suspicious(line, before_blank, after_blank, marker_patterns)
                if is_heading:
                    heading_hits += 1
                else:
                    prose_files.add(os.path.basename(path))
                if context is None:
                    context = first_kwic(text, match.start(), len(name))
        prose_hits = hits - heading_hits
        if hits == 0:
            verdict = "UNATTESTED"
        elif prose_hits == 0:
            verdict = "EDITORIAL"
        elif prose_hits >= args.min_hits and len(prose_files) >= 2:
            verdict = "ATTESTED"
        else:
            verdict = "THIN"
        rows.append({"name": name, "hits": hits, "heading_hits": heading_hits,
                     "files": sorted(all_files), "first_context": context,
                     "verdict": verdict})
    failures = [row for row in rows if row["verdict"] in ("UNATTESTED", "EDITORIAL")]
    artifact = {"package": os.path.abspath(args.package), "corpus": os.path.abspath(args.corpus),
                "min_hits": args.min_hits, "names": rows,
                "verdict": "FAIL" if failures else "PASS"}
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(artifact, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print("wrote %s" % args.json)
    print("\n=== name audit ===")
    print("name                 hits  heading  files  verdict")
    for row in rows:
        print("%-20s %4d  %7d  %5d  %s" % (row["name"][:20], row["hits"], row["heading_hits"],
                                              len(row["files"]), row["verdict"]))
        if row["first_context"]:
            print("  %s" % row["first_context"])
    if not rows:
        print("No candidate names found.")
    print("\n%s" % artifact["verdict"])
    if failures:
        print("Remedy: demote each label to a description in the subject's own words, or drop it.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
