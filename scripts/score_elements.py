#!/usr/bin/env python3
"""Class-specific admission first, deterministic ranking second. No universal cutoff."""
import argparse
import hashlib
import json
import math
from pathlib import Path

PRIORITY = ('procedure', 'cost_refusal', 'verdict', 'projectible_regularity',
            'interactional', 'variation', 'preoccupation', 'stable_style')
REQUIRED = {
    'procedure': ('precondition', 'on_fail', 'steps'),
    'cost_refusal': ('convenient_move', 'characteristic_move', 'stakes'),
    'verdict': ('object', 'judgment', 'period', 'conditions'),
    'projectible_regularity': ('method', 'conditions'),
    'interactional': ('trigger', 'move'),
    'variation': ('trigger', 'contrast'),
    'preoccupation': ('theme',),
    'stable_style': ('feature', 'contrast'),
}


def numeric(e, key, minimum=0, maximum=1):
    value = e.get('metrics', {}).get(key)
    if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError('invalid or missing metric: ' + key)
    if (key.endswith('_cases') or key in ('observations', 'corpus_hits')) and type(value) is not int:
        raise ValueError('observation counts must be integers: ' + key)
    return value


def admit(element):
    kind = element['class']
    if kind not in PRIORITY:
        raise ValueError('unknown element class: ' + str(kind))
    if element.get('flags'):
        return False, 0, 'excluded: ' + ', '.join(element['flags'])
    missing = [key for key in REQUIRED[kind] if not element.get(key)]
    for key in REQUIRED[kind]:
        if key in missing:
            continue
        if key == 'steps':
            if not isinstance(element[key], list) or not all(isinstance(step, str) and step.strip() for step in element[key]):
                missing.append('steps must be a list of nonempty execution steps')
        elif not isinstance(element[key], str) or not element[key].strip():
            missing.append(key + ' must be explicit text')
    clusters = element.get('clusters', [])
    locators = element.get('locators', [])
    if not isinstance(clusters, list) or not all(isinstance(c, str) and c.strip() for c in clusters) or len(set(clusters)) < 2 or not isinstance(locators, list) or len(locators) < 2 or not all(isinstance(c, str) and c.strip() for c in locators):
        missing.append('at least two independent clusters and source locators')
    if missing:
        return False, 0, 'missing: ' + ', '.join(missing)
    if kind in ('procedure', 'projectible_regularity'):
        transfer = numeric(element, 'transfer')
        reasoning = numeric(element, 'reasoning')
        cases = numeric(element, 'transfer_cases', 0, 100000)
        ok = transfer >= .7 and reasoning >= .5 and cases >= 2
        rank = .7 * transfer + .3 * reasoning
        reason = 'development transfer >= .70, method reproduction >= .50, at least two cases'
    elif kind == 'verdict':
        hits = numeric(element, 'corpus_hits', 0, 100000)
        ok = hits >= 2
        rank = .6 * min(len(set(clusters)) / 5, 1) + .4 * min(hits / 10, 1)
        reason = 'attested position with temporal scope and applicability conditions'
    elif kind in ('stable_style', 'variation'):
        discrimination = numeric(element, 'discrimination')
        observations = numeric(element, 'observations', 0, 100000)
        ok = discrimination >= .7 and observations >= 20
        rank = discrimination
        reason = 'discriminative evidence >= .70 with at least 20 observations'
    elif kind == 'cost_refusal':
        pressure = numeric(element, 'pressure')
        cases = numeric(element, 'pressure_cases', 0, 100000)
        ok = pressure >= .7 and cases >= 2
        rank = pressure
        reason = 'attested costly alternative and development pressure behavior >= .70'
    elif kind == 'interactional':
        transfer = numeric(element, 'transfer')
        cases = numeric(element, 'transfer_cases', 0, 100000)
        ok = transfer >= .7 and cases >= 2
        rank = transfer
        reason = 'triggered interactional move transfers on at least two cases'
    else:
        domains = element.get('domains', [])
        ok = len(set(clusters)) >= 3 and len(set(domains)) >= 2
        rank = min(len(set(clusters)) / 6, 1)
        reason = 'recurs in at least three clusters across two domains'
    return ok, round(rank, 6), reason


def score_elements(data):
    elements = data['elements']
    if not isinstance(elements, list) or len({e['id'] for e in elements}) != len(elements):
        raise ValueError('unique element IDs required')
    known = {e['id'] for e in elements}
    rows, candidates = [], []
    for e in elements:
        conflicts = e.get('conflicts_with', [])
        if any(c not in known or c == e['id'] for c in conflicts):
            raise ValueError('unresolved or self conflict for ' + e['id'])
        eligible, rank, reason = admit(e)
        row = {'id': e['id'], 'class': e['class'], 'eligible': eligible,
               'within_class_score': rank, 'decision': 'eligible' if eligible else 'cut', 'reason': reason}
        rows.append(row)
        if eligible:
            candidates.append((e, row))
    candidates.sort(key=lambda pair: (PRIORITY.index(pair[0]['class']), -pair[1]['within_class_score'], pair[0]['id']))
    retained = []
    for e, row in candidates:
        conflict = next((prior['id'] for prior in retained if prior['id'] in e.get('conflicts_with', [])
                         or e['id'] in prior.get('conflicts_with', [])), None)
        if conflict:
            row.update(decision='cut', reason='conflict loses by class/rank/ID precedence to ' + conflict)
        else:
            retained.append(e)
            row.update(decision='retain', rank=len(retained))
    return {'version': 2, 'scorer': 'score_elements.py', 'class_priority': list(PRIORITY),
            'decisions': rows, 'retained': [e['id'] for e in retained]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    try:
        raw = args.input.read_bytes()
        result = score_elements(json.loads(raw))
        result['input_hash'] = 'sha256:' + hashlib.sha256(raw).hexdigest()
        args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    except (ValueError, KeyError, TypeError, OSError) as exc:
        ap.error(str(exc))
    print('retained', len(result['retained']), 'of', len(result['decisions']))


if __name__ == '__main__':
    main()
