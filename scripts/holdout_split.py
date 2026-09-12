#!/usr/bin/env python3
"""Split a metadata-only passage inventory by work/episode BEFORE extraction.

Input: {"passages": [{"id": "p1", "group": "work-a", "domain": "ethics"}, ...]}.
Related works, translations, excerpts and retellings must share a group. The
construction context sees train only; development can guide revisions; test is
reserved for one final assessment in a fresh context. A seed ensures reproducibility,
not independence from prior model knowledge or accidental exposure.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random


def split_items(items, seed=42, frac=0.12, dev_frac=0.15, stratify=False):
    if not (0 < frac < 1 and 0 < dev_frac < 1 and frac + dev_frac < 1):
        raise ValueError('test/dev fractions must be positive and sum to less than 1')
    if not isinstance(items, list) or not items:
        raise ValueError('passages must be a nonempty list of objects with id and group')
    groups, seen = {}, set()
    for item in items:
        if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip() for k in ('id', 'group')):
            raise ValueError('every passage needs nonempty id and group strings')
        if item['id'] in seen:
            raise ValueError('duplicate passage id: ' + item['id'])
        seen.add(item['id'])
        groups.setdefault(item['group'], []).append(item)
    if len(groups) < 3:
        raise ValueError('need at least three independent works/episodes; obtain more material or report no independent test')
    strata = {}
    for group, rows in sorted(groups.items()):
        domains = {r.get('domain') for r in rows}
        if stratify and (len(domains) != 1 or not all(domains)):
            raise ValueError('stratification needs one consistent domain per group; use a broader group domain or omit --stratify')
        strata.setdefault(next(iter(domains)) if stratify else 'all', []).append(group)
    rng = random.Random(seed)
    parts = {k: [] for k in ('train', 'development', 'test')}
    notes = []
    for domain, members in sorted(strata.items()):
        rng.shuffle(members)
        if len(members) < 3:
            parts['train'].extend(members)
            notes.append(f'{domain}: fewer than three groups; train only, no evaluation coverage')
            continue
        ntest = min(math.ceil(len(members) * frac), len(members) - 2)
        ndev = min(math.ceil(len(members) * dev_frac), len(members) - ntest - 1)
        parts['test'].extend(members[:ntest])
        parts['development'].extend(members[ntest:ntest + ndev])
        parts['train'].extend(members[ntest + ndev:])
    if not parts['test'] or not parts['development']:
        raise ValueError('no independent evaluation groups available; omit stratification or obtain more groups')
    assignments = {g: part for part, members in parts.items() for g in members}
    return {'version': 2, 'seed': seed, 'frac': frac, 'dev_frac': dev_frac,
            'stratified': stratify, 'group_assignments': assignments,
            'passage_groups': {r['id']: r['group'] for r in sorted(items, key=lambda r: r['id'])},
            'partitions': {part: sorted(r['id'] for g in members for r in groups[g]) for part, members in parts.items()},
            'notes': notes}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('infile', type=Path)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--frac', type=float, default=0.12, help='final test fraction of groups')
    ap.add_argument('--dev-frac', type=float, default=0.15)
    ap.add_argument('--stratify', action='store_true')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    try:
        raw = args.infile.read_bytes()
        data = json.loads(raw)
        result = split_items(data.get('passages') if isinstance(data, dict) else data,
                             args.seed, args.frac, args.dev_frac, args.stratify)
        result['inventory_hash'] = 'sha256:' + hashlib.sha256(raw).hexdigest()
        args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    except (ValueError, OSError) as exc:
        ap.error(str(exc))
    print('wrote', args.out)
    for part, ids in result['partitions'].items():
        print(part, len(ids), 'passages')
    print('Keep final test text and answers out of construction and development contexts.')


if __name__ == '__main__':
    main()
