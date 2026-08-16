#!/usr/bin/env python3
"""
holdout_split.py — reproducible masked split for the held-out projection test.

Given a list of qualifying passage IDs, deterministically selects ~10–15% to mask, using a fixed
seed so the split is auditable and repeatable. The distiller then predicts the persona's
stance/move on the masked IDs using only the un-masked evidence, and scores alignment.

Random masking over an uneven corpus concentrates the mask in the corpus's largest domain, so the
resulting score describes that domain and is silently read as describing the persona. Pass
--stratify to spread the mask across domains proportionally instead; it needs a domain label per
passage.

Usage:
    # flat: {"passages": ["p001", "p002", ...]}  or a bare list
    python3 holdout_split.py passages.json --seed 42 --frac 0.12 --out split.json

    # stratified: {"passages": {"p001": "economics", "p002": "political philosophy", ...}}
    #         or: {"passages": [{"id": "p001", "domain": "economics"}, ...]}
    python3 holdout_split.py passages.json --stratify --seed 42 --out split.json

    # IDs directly (no stratification possible)
    python3 holdout_split.py --ids p001 p002 p003 --seed 42
"""

import argparse
import json
import math
import random
import sys
from collections import OrderedDict


def load_items(args):
    """Return an OrderedDict id -> domain (domain may be None)."""
    if args.ids:
        return OrderedDict((i, None) for i in args.ids)
    if not args.infile:
        sys.exit("provide a JSON file or --ids")
    with open(args.infile, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "passages" in data:
        data = data["passages"]
    items = OrderedDict()
    if isinstance(data, dict):
        for k, v in data.items():
            items[k] = v if isinstance(v, str) else None
    elif isinstance(data, list):
        for entry in data:
            if isinstance(entry, str):
                items[entry] = None
            elif isinstance(entry, dict) and "id" in entry:
                items[entry["id"]] = entry.get("domain")
            else:
                sys.exit("list entries must be IDs or objects with an 'id' field")
    else:
        sys.exit('JSON must be a list, a mapping, or {"passages": ...}')
    return items


def stratified_sample(items, k, rng):
    """Largest-remainder allocation across domains, then sample within each."""
    groups = OrderedDict()
    for pid, dom in items.items():
        groups.setdefault(dom or "(unlabelled)", []).append(pid)
    n = len(items)
    quotas, remainders = {}, []
    for dom, members in groups.items():
        exact = k * len(members) / n
        quotas[dom] = min(len(members), int(exact))
        remainders.append((exact - int(exact), dom))
    # distribute the leftover slots to the largest fractional parts, deterministically
    short = k - sum(quotas.values())
    for _, dom in sorted(remainders, key=lambda t: (-t[0], t[1])):
        if short <= 0:
            break
        if quotas[dom] < len(groups[dom]):
            quotas[dom] += 1
            short -= 1
    masked, per_domain = [], OrderedDict()
    for dom, members in groups.items():
        take = quotas[dom]
        picked = sorted(rng.sample(members, take)) if take else []
        masked.extend(picked)
        per_domain[dom] = {"n_total": len(members), "n_masked": take}
    return sorted(masked), per_domain


def main():
    ap = argparse.ArgumentParser(description="Reproducible held-out split for the projection test.")
    ap.add_argument("infile", nargs="?", help='JSON: {"passages":[...]}, a bare list, or id->domain')
    ap.add_argument("--ids", nargs="+", help="pass passage IDs directly")
    ap.add_argument("--seed", type=int, default=42, help="fixed seed for reproducibility")
    ap.add_argument("--frac", type=float, default=0.12, help="fraction to mask (0.10–0.15 typical)")
    ap.add_argument("--stratify", action="store_true",
                    help="spread the mask across domain labels instead of sampling uniformly")
    ap.add_argument("--out", help="write split JSON here")
    args = ap.parse_args()

    items = load_items(args)
    ids = list(items)
    n = len(ids)
    if n < 4:
        sys.exit(f"need at least 4 qualifying passages to hold out a meaningful set (got {n})")

    k = max(1, math.ceil(args.frac * n))
    rng = random.Random(args.seed)

    per_domain = None
    if args.stratify:
        labelled = sum(1 for d in items.values() if d)
        if labelled == 0:
            sys.exit("--stratify needs a domain label per passage; none of the input carries one")
        if labelled < n:
            print(f"warning: {n - labelled} passage(s) have no domain label; "
                  "they are pooled as '(unlabelled)'", file=sys.stderr)
        masked, per_domain = stratified_sample(items, k, rng)
    else:
        masked = sorted(rng.sample(ids, k))

    kept = [i for i in ids if i not in set(masked)]

    result = {"seed": args.seed, "frac": args.frac, "n_total": n, "n_masked": len(masked),
              "stratified": bool(args.stratify), "masked": masked, "kept": kept}
    if per_domain is not None:
        result["by_domain"] = per_domain

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print(f"wrote {args.out}")

    mode = "stratified" if args.stratify else "uniform"
    print(f"total {n}  masked {len(masked)} ({mode}, seed {args.seed}, frac {args.frac})")
    if per_domain:
        for dom, d in per_domain.items():
            print(f"  {dom}: {d['n_masked']}/{d['n_total']}")
        thin = [d for d in per_domain.values() if d["n_masked"] == 0]
        if thin:
            print(f"  note: {len(thin)} domain(s) received no masked item — the score will not "
                  "describe them; say so in the coverage report.")
    else:
        print("note: uniform sampling concentrates the mask in the largest domain. Record the "
              "distribution, or re-run with --stratify.")
    print("masked:", ", ".join(masked))
    print("\nPredict the persona's stance/move on each masked ID using ONLY the kept evidence,")
    print("then score alignment against the true masked passage (2=stance+reasoning, 1=direction, 0=miss).")
    print("Report hit_2 and hit_1 separately, not only the aggregate.")


if __name__ == "__main__":
    main()
