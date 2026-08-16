#!/usr/bin/env python3
"""
token_count.py — estimate package token use when no BPE tokenizer is available.

Budgets expressed in tokens silently become unreliable when they are measured with
word counts, especially for CJK material. This is a deliberately explicit
estimator, NOT a real BPE tokenizer: it makes the approximation visible, reports
the constants used, and gives a package a reproducible budget signal without a
third-party dependency.

Usage:
    python3 token_count.py <file-or-dir> [--json counts.json] [--per-file]
        [--model heuristic] [--calibrate HAN,LATIN]

Notes:
- Han and Kana characters use 1/0.6 (about 1.67) estimated tokens each. Latin
  words use 1.3 tokens each. Digit runs contribute 1.2 plus their total length/3;
  punctuation and whitespace runs contribute one token per run.
- --calibrate HAN,LATIN replaces the Han/Kana and Latin-word constants when a real
  tokenizer is available. Record that calibration in the package provenance ledger
  so the next budget can reproduce it.
- The result is a planning estimate, not a model-specific token count.
"""

import argparse
import json
import os
import re
import sys

HAN_RE = re.compile(r"[一-鿿]")
KANA_RE = re.compile(r"[\u3040-\u30ff]")
LATIN_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
DIGIT_RE = re.compile(r"\d+")
WHITESPACE_RUN_RE = re.compile(r"\s+")
PUNCT_RUN_RE = re.compile(r"[^\sA-Za-z0-9一-鿿\u3040-\u30ff]+")


def iter_files(path):
    if os.path.isfile(path):
        yield path
        return
    for root, _, names in os.walk(path):
        for name in sorted(names):
            if name.lower().endswith((".md", ".markdown", ".txt")):
                yield os.path.join(root, name)


def count(path, han_constant, latin_constant):
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    han = len(HAN_RE.findall(text))
    kana = len(KANA_RE.findall(text))
    words = len(LATIN_RE.findall(text))
    digit_runs = DIGIT_RE.findall(text)
    punctuation_runs = len(PUNCT_RUN_RE.findall(text))
    whitespace_runs = len(WHITESPACE_RUN_RE.findall(text))
    estimate = ((han + kana) * han_constant + words * latin_constant + len(digit_runs) * 1.2 +
                sum(len(run) for run in digit_runs) / 3.0 + punctuation_runs + whitespace_runs)
    return {"file": path, "chars": len(text), "chars_han": han, "chars_kana": kana, "words_latin": words,
            "digit_runs": len(digit_runs), "punctuation_runs": punctuation_runs,
            "whitespace_runs": whitespace_runs, "tokens_est": round(estimate, 2)}


def total(rows):
    keys = ("chars", "chars_han", "chars_kana", "words_latin", "digit_runs", "punctuation_runs", "whitespace_runs", "tokens_est")
    return {key: round(sum(row[key] for row in rows), 2) if key == "tokens_est" else sum(row[key] for row in rows)
            for key in keys}


def main():
    ap = argparse.ArgumentParser(description="Explicit heuristic token estimator for package budgets.")
    ap.add_argument("path", help="text file or directory")
    ap.add_argument("--json", help="write JSON artifact here")
    ap.add_argument("--per-file", action="store_true", help="print each file as well as the total")
    ap.add_argument("--model", default="heuristic", choices=("heuristic",), help="estimator model (only heuristic is available)")
    ap.add_argument("--calibrate", metavar="HAN,LATIN", help="override estimated tokens per Han/Kana char and Latin word")
    args = ap.parse_args()
    if not os.path.exists(args.path):
        ap.error("path not found: %s" % args.path)
    han_constant, latin_constant = 1.0 / 0.6, 1.3
    if args.calibrate:
        try:
            left, right = args.calibrate.split(",", 1)
            han_constant, latin_constant = float(left), float(right)
        except ValueError:
            ap.error("--calibrate must be HAN,LATIN, for example 1.67,1.30")
        if han_constant <= 0 or latin_constant <= 0:
            ap.error("calibration constants must be positive")
    files = list(iter_files(args.path))
    if not files:
        ap.error("no .txt/.md/.markdown files found")
    rows = [count(path, han_constant, latin_constant) for path in files]
    aggregate = total(rows)
    artifact = {"model": "heuristic", "constants": {"tokens_per_han_char": han_constant,
                "tokens_per_latin_word": latin_constant}, "files": rows, "total": aggregate}
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(artifact, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print("wrote %s" % args.json)
    print("\n=== heuristic token estimate (not a real BPE tokenizer) ===")
    print("constants: tokens_per_han_char=%.6g  tokens_per_latin_word=%.6g" % (han_constant, latin_constant))
    if args.per_file or len(rows) == 1:
        print("file                              chars  han  latin-words  tokens-est")
        for row in rows:
            print("%-32s %6d %4d %12d %11.2f" % (os.path.basename(row["file"])[:32], row["chars"],
                                                   row["chars_han"], row["words_latin"], row["tokens_est"]))
    print("TOTAL: chars %(chars)d  chars_han %(chars_han)d  words_latin %(words_latin)d  tokens_est %(tokens_est).2f" % aggregate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
