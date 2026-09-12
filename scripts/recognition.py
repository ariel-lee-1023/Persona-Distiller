#!/usr/bin/env python3
"""Deterministic recognition scoring; no model calls and no human-probability claim."""
DIMENSIONS = ('reasoning', 'priorities', 'conditional_coherence', 'interaction', 'specificity')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def assess(judges, cases, evidence_ids, verified_material_defect=False):
    if verified_material_defect:
        return {'outcome': 'failed', 'reason': 'Separately verified material source/attribution defect', 'judges': []}
    require(len(cases) == 3 and len({c['id'] for c in cases}) == 3, 'exactly three distinct cases required')
    if not judges:
        return {'outcome': 'not_run', 'judges': []}
    require(len(judges) <= 2, 'only two judges belong to the standard protocol')
    results = []
    for index, judge in enumerate(judges):
        if judge is None:
            results.append({'accepted': None, 'reason': 'missing judgment'})
            continue
        require(isinstance(judge, dict), 'judge output must be an object')
        require(isinstance(judge.get('material_issues'), list) and all(nonempty(x) for x in judge['material_issues']), 'judge must report material issues, including an empty list when none found')
        rows = judge.get('cases')
        require(isinstance(rows, list) and len(rows) == 3 and all(isinstance(r, dict) for r in rows), 'judge needs three case records')
        require({r.get('id') for r in rows} == {c['id'] for c in cases}, 'case IDs must match')
        by_id = {r['id']: r for r in rows}
        totals, matrix, wins, complete = [], {}, 0, True
        comparisons = {}
        floors = True
        for case in cases:
            row = by_id[case['id']]
            candidate = 'A' if index == 0 else 'B'
            require(row.get('preference') in ('A', 'B', 'tie'), 'invalid pairwise decision')
            require(nonempty(row.get('reason')), 'pairwise diagnostic reason required')
            require(isinstance(row.get('evidence_ids'), list) and row['evidence_ids'] and
                    all(x in evidence_ids for x in row['evidence_ids']), 'pairwise evidence references required')
            scores = []
            # Both slots are assessed blind; only the mapped candidate enters the gate.
            for slot in ('A', 'B'):
                dims = row.get(slot)
                require(isinstance(dims, dict) and set(dims) == set(DIMENSIONS), 'five dimensions required for each anonymous answer')
                for dim in DIMENSIONS:
                    record = dims[dim]
                    require(isinstance(record, dict) and nonempty(record.get('reason')), 'dimension justification required')
                    score = record.get('score')
                    if score == 'unassessed':
                        if slot == candidate:
                            complete = False
                        if slot == candidate:
                            scores.append(None)
                        continue
                    require(type(score) is int and 0 <= score <= 4, 'scores must be integers 0..4 or unassessed')
                    require(nonempty(record.get('passage')) and record['passage'] in case['answers'][slot if index == 0 else ('B' if slot == 'A' else 'A')],
                            'score passage must occur in the assessed answer')
                    require(isinstance(record.get('evidence_ids'), list) and record['evidence_ids'] and
                            all(x in evidence_ids for x in record['evidence_ids']), 'dimension evidence references required')
                    if dim == 'conditional_coherence':
                        require(nonempty(record.get('pair_reason')), 'explain changed-condition pair and each answer contribution')
                    if slot == candidate:
                        scores.append(score)
                        floors = floors and score >= (2 if dim == 'interaction' else 3)
            matrix[case['id']] = dict(zip(DIMENSIONS, scores))
            totals.append(sum(scores) if None not in scores else None)
            identical = case['answers']['A'] == case['answers']['B']
            effective = 'tie' if identical else row['preference']
            comparisons[case['id']] = {'reported': row['preference'], 'effective': effective,
                                       'identical_presented_answers': identical}
            wins += effective == candidate
        aggregate = 100 * sum(totals) / 60 if None not in totals else None
        accepted = (aggregate >= 80 and min(totals) >= 15 and floors and wins >= 2 and not judge['material_issues']) if complete else None
        results.append({'accepted': accepted, 'recognition_score': aggregate, 'case_totals': totals,
                        'dimensions': matrix, 'comparisons': comparisons, 'persona_wins': wins, 'complete': complete})
    accepted = [r['accepted'] for r in results]
    outcome = 'passed' if accepted == [True, True] else 'failed' if accepted == [False, False] else 'inconclusive'
    return {'outcome': outcome, 'judges': results,
            'limitation': 'Provisional engineering thresholds, not probability of human acceptance; three internal diagnostic cases.'}


def delivery_status(package, source, recognition):
    return 'standard_accepted' if (package, source, recognition) == ('passed', 'passed', 'passed') else 'candidate'
