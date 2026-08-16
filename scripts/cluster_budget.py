#!/usr/bin/env python3
"""Cluster-module budget (Stage 4).

Sizes each `clusters/*.md` module the way `scoring.md` sizes the core: from what
actually survived curation, not from a flat band. A band is a guess that a rich
cluster under-uses and a thin one is invited to pad, and it gets worse as the
corpus gets better -- because the cost of fencing a module off from its siblings
scales with how many siblings there are.

    supply = 600
           +  90 * min(n_apparatus,    12)
           +  90 * min(n_moves,        12)
           +  85 * min(n_applications,  8)
           +  30 * min(n_fragments,    24)
           +  80 +  15 * min(n_siblings, 9)
           + 400 * sqrt(words / words_firsthand)

    budget = clamp(supply, 1800, 6000)

Module length tracks conceptual density, not word count: across the calibration
set, length correlated +0.82 with retained fragments and +0.70 with the cluster's
own constructs, but only +0.30 with cluster word count. The mass term is a damped
corrective, never the driver.

Two flags matter more than the number:

  FLOOR  supply < 1800 -- the cluster has not earned a module. Fold it into its
         nearest sibling, or demote its material to episodic.md. Do not pad.
  RECUT  n_apparatus > 12 or n_moves > 12 -- the cluster needs a new cut.
         Re-cut it at Stage 1 with segment.py. Do not buy the space back by
         deleting evidence.
  SPLIT_IN_MODULE  the same overflow, but registers > 1 and shared_domain is true.
         Keep one module, declare an internal A/B register split and a no-pooling
         header, then give style guidance separately for each register.

Registers cost 220 tokens for each register after the first, capped at three. The
cost pays for the declared split, no-pooling fence, and duplicated style guidance.
Coefficients can be loaded from a JSON file and emitted as JSON so a run's exact
calibration can be recorded in its provenance ledger.

Stdlib only. Reads a JSON spec (see --example), or takes one cluster on the
command line. Writes a `cluster_budgets` array shaped for scores.json with
--json.

Calibration: ten modules, one 630k-word corpus. Mean error 3.8%, max 6.0%
against hand-written lengths. Structure settled, coefficients provisional --
record realised sizes so the next calibration has more than one corpus.
"""

import argparse
import json
import math
import sys

FIXED_FRAME = 600
PROHIB_BASE = 80
PER_SIBLING = 15
MASS_COEF = 400
FLOOR = 1800
CEILING = 6000

# name -> (unit price, cap)
TERMS = {
    "apparatus": (90, 12),
    "moves": (90, 12),
    "applications": (85, 8),
    "fragments": (30, 24),
}
SIBLING_CAP = 9
RECUT_TERMS = ("apparatus", "moves")
REGISTER_PRICE = 220
REGISTER_CAP = 3

EXAMPLE = {
    "words_firsthand": 630298,
    "clusters": [
        {
            "cluster_id": "c01",
            "words": 79282,
            "apparatus": 10,
            "moves": 9,
            "applications": 7,
            "fragments": 24,
        },
        {
            "cluster_id": "c02",
            "words": 55861,
            "apparatus": 5,
            "moves": 9,
            "applications": 6,
            "fragments": 14,
        },
        {
            "cluster_id": "c12",
            "words": 25212,
            "apparatus": 3,
            "moves": 2,
            "applications": 2,
            "fragments": 4,
        },
    ],
}


def coefficient_set():
    """Return the active, JSON-shaped calibration constants."""
    return {
        "FIXED_FRAME": FIXED_FRAME, "PROHIB_BASE": PROHIB_BASE,
        "PER_SIBLING": PER_SIBLING, "MASS_COEF": MASS_COEF,
        "FLOOR": FLOOR, "CEILING": CEILING, "SIBLING_CAP": SIBLING_CAP,
        "REGISTER_PRICE": REGISTER_PRICE, "REGISTER_CAP": REGISTER_CAP,
        "TERMS": {name: {"price": price, "cap": cap} for name, (price, cap) in TERMS.items()},
    }


def apply_coefficients(path):
    """Override recognised module constants and return the source label."""
    global FIXED_FRAME, PROHIB_BASE, PER_SIBLING, MASS_COEF, FLOOR, CEILING, SIBLING_CAP
    global REGISTER_PRICE, REGISTER_CAP, TERMS
    with open(path, encoding="utf-8") as fh:
        values = json.load(fh)
    if not isinstance(values, dict):
        raise ValueError("coefficient file must contain a JSON object")
    scalar_names = ("FIXED_FRAME", "PROHIB_BASE", "PER_SIBLING", "MASS_COEF", "FLOOR", "CEILING",
                    "SIBLING_CAP", "REGISTER_PRICE", "REGISTER_CAP")
    overridden = []
    for name in scalar_names:
        if name in values:
            value = values[name]
            if not isinstance(value, (int, float)):
                raise ValueError("%s must be numeric" % name)
            globals()[name] = value
            overridden.append(name)
    if "TERMS" in values:
        raw_terms = values["TERMS"]
        if not isinstance(raw_terms, dict):
            raise ValueError("TERMS must be an object")
        updated = dict(TERMS)
        for name, value in raw_terms.items():
            if name not in updated:
                raise ValueError("unknown TERMS entry: %s" % name)
            if isinstance(value, dict):
                price, cap = value.get("price"), value.get("cap")
            elif isinstance(value, (list, tuple)) and len(value) == 2:
                price, cap = value
            else:
                raise ValueError("TERMS.%s must be {price, cap} or [price, cap]" % name)
            if not isinstance(price, (int, float)) or not isinstance(cap, (int, float)):
                raise ValueError("TERMS.%s price and cap must be numeric" % name)
            updated[name] = (price, int(cap))
            overridden.append("TERMS.%s" % name)
        TERMS = updated
    return path, overridden


def compute(counts, words, words_firsthand, n_siblings, registers=1):
    """Return supply, budget, breakdown, floor and overflow flags for one module."""
    registers = min(max(int(registers), 1), int(REGISTER_CAP))
    breakdown = {"fixed_frame": FIXED_FRAME}
    supply = FIXED_FRAME

    for name, (price, cap) in TERMS.items():
        n = int(counts.get(name, 0))
        if n < 0:
            raise ValueError("%s cannot be negative" % name)
        part = price * min(n, cap)
        breakdown[name] = part
        supply += part

    sib = PROHIB_BASE + PER_SIBLING * min(int(n_siblings), SIBLING_CAP)
    breakdown["prohibitions"] = sib
    supply += sib

    if words_firsthand <= 0:
        raise ValueError("words_firsthand must be positive")
    share = max(0.0, words) / words_firsthand
    mass = round(MASS_COEF * math.sqrt(share))
    breakdown["mass"] = mass
    supply += mass

    register_cost = REGISTER_PRICE * max(registers - 1, 0)
    breakdown["registers"] = register_cost
    supply += register_cost

    supply = round(supply)
    budget = max(FLOOR, min(supply, CEILING))
    floor_triggered = supply < FLOOR
    recut = any(int(counts.get(t, 0)) > TERMS[t][1] for t in RECUT_TERMS)
    return supply, budget, breakdown, floor_triggered, recut, registers


def load_spec(path):
    with open(path, encoding="utf-8") as fh:
        spec = json.load(fh)
    clusters = spec.get("clusters")
    if not isinstance(clusters, list) or not clusters:
        raise SystemExit("spec needs a non-empty 'clusters' array (see --example)")
    total = spec.get("words_firsthand")
    if not total:
        total = sum(c.get("words", 0) for c in clusters)
        if not total:
            raise SystemExit("spec needs 'words_firsthand', or per-cluster 'words'")
    return clusters, total


def main():
    ap = argparse.ArgumentParser(
        description="Cluster-module budget (Stage 4). Formula and counting rules: references/scoring.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="A cluster below the 1800 floor should be folded into a sibling module or\n"
        "demoted to episodic.md -- never padded up to it.",
    )
    ap.add_argument("spec", nargs="?", help="JSON spec file; omit to use --single")
    ap.add_argument("--single", action="store_true", help="score one cluster from the flags below")
    ap.add_argument("--apparatus", type=int, default=0)
    ap.add_argument("--moves", type=int, default=0)
    ap.add_argument("--applications", type=int, default=0)
    ap.add_argument("--fragments", type=int, default=0)
    ap.add_argument("--siblings", type=int, default=0, help="other clusters that also get a module")
    ap.add_argument("--words", type=int, default=0, help="this cluster's words")
    ap.add_argument("--words-firsthand", type=int, default=0, help="total firsthand words")
    ap.add_argument("--registers", type=int, default=None, help="incommensurable registers in this module (default 1; capped at 3)")
    ap.add_argument("--shared-domain", action="store_true", help="topic domain is shared, allowing SPLIT_IN_MODULE on overflow")
    ap.add_argument("--coefficients", help="JSON file overriding calibration constants")
    ap.add_argument("--emit-coefficients", action="store_true", help="print the active calibration constants as JSON")
    ap.add_argument("--json", metavar="OUT", help="write a scores.json 'cluster_budgets' array here")
    ap.add_argument("--example", action="store_true", help="print an example spec and exit")
    args = ap.parse_args()

    coefficients_source = "defaults"
    coefficient_overrides = []
    if args.coefficients:
        try:
            coefficients_source, coefficient_overrides = apply_coefficients(args.coefficients)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            ap.error(str(exc))
    if args.emit_coefficients:
        print(json.dumps(coefficient_set(), indent=2, sort_keys=True))
        if not args.example and not args.single and not args.spec:
            return 0

    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0

    if args.single:
        if not args.words_firsthand:
            ap.error("--single needs --words-firsthand")
        clusters = [
            {
                "cluster_id": "single",
                "words": args.words,
                "apparatus": args.apparatus,
                "moves": args.moves,
                "applications": args.applications,
                "fragments": args.fragments,
                "siblings": args.siblings,
                "registers": args.registers if args.registers is not None else 1,
                "shared_domain": args.shared_domain,
            }
        ]
        total = args.words_firsthand
    elif args.spec:
        clusters, total = load_spec(args.spec)
    else:
        ap.error("give a spec file, or --single with the count flags (or --example)")

    rows = []
    for c in clusters:
        cid = c.get("cluster_id") or c.get("id") or "?"
        # default: every other cluster in the spec is a sibling
        n_sib = c.get("siblings", len(clusters) - 1)
        requested_registers = args.registers if args.registers is not None else c.get("registers", 1)
        try:
            supply, budget, breakdown, floored, recut, registers = compute(
                c, c.get("words", 0), total, n_sib, requested_registers)
        except (TypeError, ValueError) as exc:
            ap.error("%s: %s" % (cid, exc))
        shared_domain = args.shared_domain or bool(c.get("shared_domain", False))
        split_in_module = recut and registers > 1 and shared_domain
        verdict = "SPLIT_IN_MODULE" if split_in_module else ("RECUT" if recut else ("FLOOR" if floored else "OK"))
        rows.append(
            {
                "cluster_id": cid,
                "supply": supply,
                "budget": budget,
                "counts": {
                    "apparatus": int(c.get("apparatus", 0)),
                    "moves": int(c.get("moves", 0)),
                    "applications": int(c.get("applications", 0)),
                    "fragments": int(c.get("fragments", 0)),
                    "siblings": int(n_sib),
                    "registers": registers,
                },
                "words": int(c.get("words", 0)),
                "words_firsthand": int(total),
                "floor_triggered": floored,
                "recut_flagged": recut,
                "split_in_module_flagged": split_in_module,
                "shared_domain": shared_domain,
                "verdict": verdict,
                "coefficients_source": coefficients_source,
                "_breakdown": breakdown,
            }
        )

    width = max(len(r["cluster_id"]) for r in rows)
    width = max(width, 7)
    print("%-*s %8s %8s %16s   %s" % (width, "cluster", "supply", "budget", "verdict", "breakdown"))
    print("coefficients source: %s" % coefficients_source)
    if coefficient_overrides:
        print("constants from file: %s" % ", ".join(coefficient_overrides))
    for r in rows:
        b = r["_breakdown"]
        parts = "frame %d + app %d + mov %d + apl %d + frg %d + prh %d + mass %d + reg %d" % (
            b["fixed_frame"], b["apparatus"], b["moves"], b["applications"],
            b["fragments"], b["prohibitions"], b["mass"], b["registers"],
        )
        print("%-*s %8d %8d %16s   %s" % (width, r["cluster_id"], r["supply"], r["budget"], r["verdict"], parts))

    floored = [r for r in rows if r["floor_triggered"]]
    recut = [r for r in rows if r["recut_flagged"] and not r["split_in_module_flagged"]]
    split_in_module = [r for r in rows if r["split_in_module_flagged"]]
    if floored or recut or split_in_module:
        print()
    for r in floored:
        print(
            "FLOOR  %s: supply %d < %d. This cluster has not earned a module.\n"
            "       Fold it into its nearest sibling module, or demote its material to\n"
            "       episodic.md. Do not pad it up to the floor."
            % (r["cluster_id"], r["supply"], FLOOR)
        )
    for r in split_in_module:
        over = [
            "%s=%d (cap %d)" % (t, r["counts"][t], TERMS[t][1])
            for t in RECUT_TERMS if r["counts"][t] > TERMS[t][1]
        ]
        print(
            "SPLIT_IN_MODULE  %s: %s. The shared topic has %d registers.\n"
            "                 Keep one module, declare an internal A/B register split with a\n"
            "                 no-pooling header, and give separate style guidance for each."
            % (r["cluster_id"], "; ".join(over), r["counts"]["registers"])
        )
    for r in recut:
        over = [
            "%s=%d (cap %d)" % (t, r["counts"][t], TERMS[t][1])
            for t in RECUT_TERMS
            if r["counts"][t] > TERMS[t][1]
        ]
        print(
            "RECUT  %s: %s. The cluster is carrying two registers.\n"
            "       Re-cut it at Stage 1 with segment.py by period or theme. Do not buy\n"
            "       the space back by deleting evidence."
            % (r["cluster_id"], "; ".join(over))
        )

    if len(rows) > 1:
        worst = max(r["budget"] for r in rows)
        print()
        print(
            "Runtime load, not package size: one module loads at a time (two on a close\n"
            "secondary ranking). Worst case = core_budget + 2 x %d + voice.md + frameworks.md."
            % worst
        )

    if args.json:
        out = [{k: v for k, v in r.items() if k != "_breakdown"} for r in rows]
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
            fh.write("\n")
        print("\nwrote %s (%d cluster%s) — paste as scores.json's 'cluster_budgets'"
              % (args.json, len(out), "" if len(out) == 1 else "s"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
