"""Behavioral release gates, distinct from position recall and style metrics."""
from collections import defaultdict


def require(ok, message):
    if not ok:
        raise ValueError(message)


CRITERIA = {'reasoning': ('method', 'conditions'),
            'commitment': ('costly_choice', 'resisted_pressure'),
            'scope': ('period', 'conditions', 'attribution')}
METADATA = {'reasoning': ('method',),
            'commitment': ('attested_choice', 'convenient_alternative', 'pressure'),
            'scope': ('scope_case',)}


def check_behavioral(data, content_hash, section=None):
    require(data['content_hash'] == content_hash, 'behavioral evidence is stale')
    report = {}
    for kind in CRITERIA:
        if section is not None and kind != section:
            continue
        cases = data[kind]
        require(isinstance(cases, list) and len(cases) >= (3 if kind == 'scope' else 2), kind + ' needs multiple new-situation cases')
        require(len({c['id'] for c in cases}) == len(cases), kind + ' case IDs must be unique')
        for c in cases:
            require(all(isinstance(c.get(k), str) and c[k].strip() for k in ('id', 'prompt', 'answer', 'rationale') + METADATA[kind]), kind + ' needs saved answers and scenario metadata')
            require(c.get('disputed') is False, 'disputed behavioral judgments require human review')
            require(all(type(c['criteria'].get(k)) is bool for k in CRITERIA[kind]), kind + ' criterion grades required')
        hits = sum(all(c['criteria'][k] for k in CRITERIA[kind]) for c in cases)
        value = hits / len(cases)
        if kind == 'scope':
            require({c['scope_case'] for c in cases} == {'attested_period', 'earlier_period', 'changed_conditions'}, 'scope cases must cover history and changed applicability')
            require(value == 1, 'historical-scope behavioral gate failed')
        else:
            require(value >= (.8 if kind == 'commitment' else .7), kind + ' behavioral gate failed')
        report[kind] = {'score': value, 'hits': hits, 'n': len(cases)}
    if section is not None and section != 'identity':
        return report
    identity = data['identity']
    candidates = identity['candidates']
    require(isinstance(candidates, list) and len(candidates) >= 3 and len(set(candidates)) == len(candidates), 'identity needs target and at least two plausible neighbors')
    by_task = defaultdict(list)
    totals = {candidate: [0, 0] for candidate in candidates}
    for trial in identity['cases']:
        require(trial['truth'] in candidates and all(isinstance(trial.get(k), str) and trial[k].strip() for k in ('id', 'prompt', 'answer')), 'identity trial missing facts, answer or target')
        by_task[trial['id']].append(trial)
        judgments = trial['judgments']
        require(len(judgments) >= 2 and len({j['reviewer'] for j in judgments}) == len(judgments), 'identity needs at least two distinct blind reviewers per answer')
        for j in judgments:
            require(j.get('blinded') is True and j.get('disputed') is False and j.get('rationale'), 'identity judgments must be blind, justified and resolved')
            require(j['choice'] in candidates, 'unknown identity choice')
            totals[trial['truth']][0] += j['choice'] == trial['truth']
            totals[trial['truth']][1] += 1
    require(by_task, 'identity trials required')
    for trials in by_task.values():
        require(len(trials) == len(candidates) and {t['truth'] for t in trials} == set(candidates), 'each identity task must test every candidate exactly once')
        require(len({t['prompt'] for t in trials}) == 1, 'identity candidates must receive the same task and facts')
    by_candidate = {candidate: hits / n for candidate, (hits, n) in totals.items()}
    macro = sum(by_candidate.values()) / len(candidates)
    require(macro >= .7 and min(by_candidate.values()) >= .5, 'blinded identity discrimination gate failed')
    report['identity'] = {'macro_accuracy': macro, 'by_candidate': by_candidate, 'baseline_accuracy': identity.get('baseline_accuracy')}
    return report
