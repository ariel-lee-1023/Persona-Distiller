#!/usr/bin/env python3
"""
discrimination_test.py — blind register-separation gate (Stage 3.5 / Stage 5).

The three existing checks all ask the same question from different angles: does this read like the
person? None asks whether the person's *registers can be told apart* — and for any persona whose
core claims internal variation, that is a separate and prior question.

It matters whenever the core says something like "in interviews I do X, in essays Y", "before 2015
I held Z", or "each work has its own vocabulary". Those claims are only worth carrying if the
registers are actually separable in the source. If they are not, the modulation section is
decoration: the host agent cannot act on a distinction the corpus does not support, and the
persona will average toward one voice no matter what the rules say. A style-match test cannot
catch this, because a passage can match the *aggregate* baseline perfectly while being
indistinguishable from every other register.

The test: sample passages from each cluster, strip the labels, classify them blind by register
signature alone, then score. High accuracy means the signatures carry real information and the
modulation rules can be trusted. Low accuracy means collapse the registers into one honest voice
and say so in the coverage report — do not ship a distinction you cannot make.

  ≥ 0.90  — signatures strongly separable; per-register rules are load-bearing. Keep them.
  0.70–0.90 — usable; name the confusable pairs in the coverage report and merge the worst.
  < 0.70  — the registers are not distinct in this corpus. Collapse them. A core that promises a
            distinction it cannot perform is worse than one that never claimed it.

Two-step, because the answers must be written before the key is seen:

    # 1 — sample. Prints unlabelled passages; the key goes to a file you do not open.
    python3 discrimination_test.py sample clusters/ --registers registers.json --per-cluster 2 --seed 42 --key key.json

    # 2 — classify from the printed passages, then score.
    python3 discrimination_test.py score key.json --answers R1 R2 R1 R2 ...
    python3 discrimination_test.py score key.json --answers-file answers.json

--mask-names replaces capitalised mid-sentence tokens with ◼. Use it when the clusters have
distinct casts: recognising a character name is not recognising a register, and an unmasked run
can score well on cues the persona will never see in a user's utterance.
"""

import argparse
import json
import os
import random
import re
import sys

WS = re.compile(r"\s+")
NOISE = re.compile(r"\[[^\]]{0,80}\]|\*+|#+|<!--.*?-->|\(#\)|_+")
CAP = re.compile(r"(?<![.!?]\s)(?<!^)\b([A-Z][a-z]{2,})\b")


def load_clusters(path):
    out = {}
    for root, directories, names in os.walk(path):
        directories.sort()
        for n in sorted(names):
            if not n.endswith((".txt", ".md")):
                continue
            cid = re.match(r"(c\d{2,})", n)
            key = cid.group(1) if cid else os.path.splitext(n)[0]
            text = open(os.path.join(root, n), encoding="utf-8", errors="replace").read()
            out.setdefault(key, []).append(WS.sub(" ", NOISE.sub("", text)))
    return {k: " ".join(v) for k, v in out.items()}


def family_mapping(registers):
    """Resolve units or their clusters to families; reject mixed-family clusters."""
    mapping = {}
    units = {u['unit_id']: u for u in registers['units']}
    for family in registers['families']:
        fid = family['family_id']
        for member in family['members']:
            if member not in units:
                raise ValueError('unknown register unit: ' + member)
            for source in [member] + units[member].get('clusters', []):
                if source in mapping and mapping[source] != fid:
                    raise ValueError('mixed-family source ' + source + '; sample homogeneous units or recut it')
                mapping[source] = fid
    return mapping


def cmd_sample(args):
    clusters = load_clusters(args.path)
    if len(clusters) < 2:
        sys.exit("need at least 2 clusters — this test only applies to a persona claiming "
                 "more than one register")

    with open(args.registers, encoding="utf-8") as fh:
        registers = json.load(fh)
    try:
        mapping = family_mapping(registers)
        missing = sorted(set(clusters) - set(mapping))
        if missing:
            raise ValueError('unmapped sources: ' + ', '.join(missing))
        if len({mapping[c] for c in clusters}) < 2:
            raise ValueError('need at least two represented register families')
        if args.length < 1 or args.per_cluster < 1 or any(not t.strip() for t in clusters.values()):
            raise ValueError('length, per-cluster and source texts must be nonempty/positive')
    except ValueError as exc:
        sys.exit(str(exc))
    rng = random.Random(args.seed)
    items = []
    for cid, text in sorted(clusters.items()):
        words = text.split()
        if len(words) < args.length * 4:
            print(f"note: {cid} is short ({len(words)} words); sampling anyway", file=sys.stderr)
        for _ in range(args.per_cluster):
            lo = min(len(words) // 10, 500, max(0, len(words) - args.length))
            hi = max(lo + 1, len(words) - args.length + 1)
            i = rng.randrange(lo, hi)
            passage = " ".join(words[i:i + args.length])
            if args.mask_names:
                passage = CAP.sub("◼", passage)
            items.append((cid, passage))

    rng.shuffle(items)
    key = {}
    for n, (cid, passage) in enumerate(items, 1):
        key[str(n)] = mapping[cid]
        print(f"--- P{n}: {passage}\n")

    with open(args.key, "w", encoding="utf-8") as fh:
        json.dump({"seed": args.seed, "per_cluster": args.per_cluster,
                   "length": args.length, "mask_names": args.mask_names,
                   "label_type": "register_family", "families": sorted(set(mapping[c] for c in clusters)),
                   "labels": key}, fh, indent=2, ensure_ascii=False)

    print(f"{len(items)} passages from {len(clusters)} clusters. Key written to {args.key}.")
    print("Classify every passage by register signature BEFORE opening that file, then:")
    print(f"  python3 {os.path.basename(sys.argv[0])} score {args.key} --answers <R1 R2 ...>")


def cmd_score(args):
    with open(args.key, encoding="utf-8") as fh:
        blob = json.load(fh)
    if blob.get("label_type") != "register_family":
        sys.exit("legacy cluster-ID key: resample with --registers")
    labels = blob["labels"]
    if not labels:
        sys.exit("empty answer key")

    if args.answers_file:
        with open(args.answers_file, encoding="utf-8") as fh:
            data = json.load(fh)
        answers = {str(k): v for k, v in (data.get("answers", data)).items()}
    elif args.answers:
        answers = {str(i): a for i, a in enumerate(args.answers, 1)}
    else:
        sys.exit("provide --answers or --answers-file")

    if set(answers) != set(labels):
        sys.exit("answer IDs must match every key ID exactly")
    if any(a not in blob['families'] for a in answers.values()):
        sys.exit("answers must be register-family IDs from the key")

    ok = 0
    confusions = {}
    for n in sorted(labels, key=int):
        truth = labels[n]
        guess = answers.get(n, "—")
        hit = guess == truth
        ok += hit
        if not hit:
            confusions[(truth, guess)] = confusions.get((truth, guess), 0) + 1
        print(f"P{n:>3}  predicted={guess:<8s} actual={truth:<8s} {'OK' if hit else 'MISS'}")

    n_total = len(labels)
    score = ok / n_total if n_total else 0.0
    print(f"\ndiscrimination: {ok}/{n_total} = {score:.2f}  (seed {blob['seed']}, "
          f"{'names masked' if blob.get('mask_names') else 'names visible'})")

    if score >= 0.90:
        verdict = "separable — per-register rules are load-bearing, keep them"
    elif score >= 0.70:
        verdict = "usable — name the confusable pairs in the coverage report, merge the worst"
    else:
        verdict = ("NOT separable — collapse these registers into one honest voice and record "
                   "the decision; do not ship a distinction the corpus cannot support")
    print(f"verdict: {verdict}")

    if confusions:
        print("\nconfused pairs (actual → predicted):")
        for (t, g), c in sorted(confusions.items(), key=lambda kv: -kv[1]):
            print(f"  {t} → {g}   ×{c}")
        print("A pair confused repeatedly is one register, not two, whatever the labels say.")

    if not blob.get("mask_names"):
        print("\nNames were visible. Re-run with --mask-names before trusting this: recognising a "
              "cast is not recognising a register, and only the register survives into use.")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"score": score, "n": n_total, "seed": blob['seed'],
                       "mask_names": blob.get('mask_names', False), "label_type": "register_family",
                       "confusions": [{"actual": t, "predicted": g, "n": n} for (t, g), n in sorted(confusions.items())]}, fh, indent=2)
    print(f"\nRecord as fidelity.json → discrimination: "
          f'{{"score": {score:.2f}, "n": {n_total}, "seed": {blob["seed"]}, '
          f'"mask_names": {str(blob.get("mask_names", False)).lower()}}}')


def main():
    ap = argparse.ArgumentParser(description="Blind register-separation gate.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sample", help="print unlabelled passages and write the key")
    s.add_argument("path", help="clusters directory")
    s.add_argument("--registers", required=True, help="register_discover output with units[].clusters mappings")
    s.add_argument("--per-cluster", type=int, default=2)
    s.add_argument("--length", type=int, default=120, help="words per passage")
    s.add_argument("--seed", type=int, default=42)
    s.add_argument("--key", default="discrimination_key.json")
    s.add_argument("--mask-names", action="store_true",
                   help="replace capitalised mid-sentence tokens with ◼")
    s.set_defaults(func=cmd_sample)

    c = sub.add_parser("score", help="score answers against the key")
    c.add_argument("key")
    c.add_argument("--answers", nargs="+", help="register-family ids in passage order")
    c.add_argument("--answers-file", help='JSON {"1":"R1","2":"R2",...}')
    c.add_argument("--json", help="write machine-readable family score and confusions")
    c.set_defaults(func=cmd_score)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
