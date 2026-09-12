#!/usr/bin/env python3
"""Report working delivery separately from strict research release qualification."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from workflow import Workflow, runtime_files, file_hash
from evaluation_runner import verify


def require(ok, message):
    if not ok:
        raise ValueError(message)


def validate_package(package, fidelity=None):
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / 'validation.json'
        command = [sys.executable, str(Path(__file__).with_name('validate_package.py')), str(package), '--json', str(output)]
        if fidelity is not None:
            command += ['--release', '--fidelity', str(fidelity)]
        proc = subprocess.run(command, capture_output=True, text=True)
        if not output.exists():
            return {'verdict': 'FAIL', 'checks': [], 'detail': proc.stderr or proc.stdout}
        return json.loads(output.read_text())


def current_evidence(dependencies, current):
    return isinstance(dependencies, dict) and bool(dependencies) and all(current.get(p) == h for p, h in dependencies.items())


def response_record(entry, base):
    if 'prediction_run' in entry:
        run = (base / entry['prediction_run']).resolve()
        verify(run)
        rows = json.loads((run / 'predictions.json').read_text())
        matches = [r for r in rows if r['id'] == entry['id'] and r['condition'] == 'persona']
        require(len(matches) == 1, 'response ID must resolve to one persona answer')
        return matches[0]
    path = (base / entry['record']).resolve()
    require(entry.get('record_hash') == file_hash(path), 'saved response record changed')
    return json.loads(path.read_text())


def report(package, workflow, review_path, fidelity=None):
    wf = workflow if isinstance(workflow, Workflow) else Workflow(workflow)
    state = wf.status()
    review_path = Path(review_path)
    review = json.loads(review_path.read_text())
    require(isinstance(review.get('summary'), str) and review['summary'].strip(), 'change summary required')
    require(isinstance(review.get('reviewer'), str) and review['reviewer'].strip(), 'content reviewer required')
    require(isinstance(review.get('limitations'), list) and all(isinstance(v, str) for v in review['limitations']), 'record unresolved limitations')
    current = runtime_files(state['runtime'])
    changed = sorted(p for p in set(current) | set(state['initial_files']) if current.get(p) != state['initial_files'].get(p))
    unexpected = sorted(set(changed) - set(state['affected_modules']))
    checks = validate_package(package)
    root_matches = 'skill_root' in checks and Path(checks['skill_root']).resolve() == Path(state['runtime'])
    sources, responses, issues = [], [], []
    formatting = state['change_type'] == 'formatting'
    for entry in review.get('source_checks', []):
        ok = current_evidence(entry.get('dependencies'), current) and entry.get('passed') is True
        ok = ok and all(isinstance(entry.get(k), str) and entry[k].strip() for k in
                        ('claim', 'locator', 'source_excerpt', 'assessment', 'condition_or_exception'))
        sources.append({**entry, 'current_and_complete': bool(ok)})
    for entry in review.get('responses', []):
        try:
            saved = response_record(entry, review_path.parent)
            ok = current_evidence(saved.get('dependencies'), current)
            ok = ok and all(isinstance(saved.get(k), str) and saved[k].strip() for k in ('prompt', 'answer'))
            ok = ok and isinstance(entry.get('assessment'), str) and bool(entry['assessment'].strip())
            ok = ok and all(entry.get('checks', {}).get(k) is True for k in ('supported_claims', 'qualifications', 'method'))
            responses.append({**entry, 'saved': saved, 'current_and_complete': bool(ok)})
        except (ValueError, OSError, KeyError) as exc:
            responses.append({**entry, 'current_and_complete': False, 'error': str(exc)})
    if unexpected: issues.append('runtime changed outside recorded scope: ' + ', '.join(unexpected))
    if checks['verdict'] != 'PASS' or not root_matches: issues.append('structural/discovery/reference validation failed or targets another runtime')
    if formatting:
        if not review.get('formatting_only_rationale'):
            issues.append('formatting-only classification needs an explicit content-preservation rationale')
    else:
        if not sources or not all(x['current_and_complete'] for x in sources):
            issues.append('current source-fidelity review is missing, failed or stale')
        minimum = 2 if state['operation'] == 'new' else 1
        if len(responses) < minimum or not all(x['current_and_complete'] for x in responses):
            issues.append('representative saved responses and content review are missing, failed or stale')
        # Reviewed evidence must cover changed substantive files, not an unrelated easy claim.
        covered = {p for x in sources if x['current_and_complete'] for p in x['dependencies']}
        if set(changed) - covered:
            issues.append('source review does not cover every changed substantive runtime module')
    pending = review.get('pending_elements', [])
    require(isinstance(pending, list), 'pending elements must be recorded as a list')
    for item in pending:
        require(item.get('id') and item.get('missing_evidence') and item.get('operative_core') is False,
                'new elements lacking admission evidence must stay pending outside the operative core')
    # Compute strict status with the unchanged validator; never trust a supplied PASS label.
    evidence = Path(fidelity) if fidelity else Path(package) / 'fidelity-ledger/fidelity.json'
    research = validate_package(package, evidence) if fidelity is not None or evidence.exists() else None
    research_passed = research is not None and research['verdict'] == 'PASS' and root_matches
    attempted = state['mode'] == 'research' or research is not None or any(
        e.get('evaluation') == 'research' for e in review.get('existing_evidence', []))
    lightweight = not issues
    delivery = 'usable_working_version' if lightweight and review.get('usable') is True else 'incomplete_draft'
    evaluation = ('research_evaluation_passed' if research_passed else
                  'research_evaluation_incomplete' if attempted or not lightweight else 'lightweight_checks_completed')
    reusable = [{**e, 'current': current_evidence(e.get('dependencies'), current)} for e in review.get('existing_evidence', [])]
    result = {'delivery_status': delivery, 'evaluation_status': evaluation,
              'lightweight_checks_completed': lightweight, 'research_status': 'passed' if research_passed else ('failed_or_incomplete' if attempted else 'not_run'),
              'mode': state['mode'], 'scope': state['scope'], 'summary': review['summary'], 'changed_modules': changed,
              'runtime_files': current, 'structure': checks, 'source_checks': sources, 'responses': responses,
              'pending_elements': pending, 'existing_evidence': reusable, 'research_validation': research,
              'limitations': review['limitations'], 'completion_gaps': issues,
              'evaluation_budget': {'limit': state['budget'], 'consumed': state['consumed'], 'remaining': state['remaining'], 'calls': state['calls']},
              'source_processing': review.get('source_processing', {}),
              'note': 'Working delivery and structure do not establish persona fidelity. Research results and partial calls remain visible.'}
    wf.note('completion', {'delivery_status': delivery, 'evaluation_status': evaluation, 'review_hash': file_hash(review_path)})
    wf.checkpoint(review.get('remaining_items', []), review.get('source_processing'))
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('package', type=Path); ap.add_argument('--workflow', type=Path, required=True)
    ap.add_argument('--review', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--fidelity', type=Path)
    args = ap.parse_args()
    try:
        # Completion is a stop instruction. Reporting itself makes no model calls.
        wf = Workflow(args.workflow); wf.stop()
        result = report(args.package, wf, args.review, args.fidelity)
        with args.out.open('x') as out:
            json.dump(result, out, indent=2, ensure_ascii=False, allow_nan=False); out.write('\n')
        print(result['delivery_status'] + ' / ' + result['evaluation_status'])
    except (ValueError, OSError, KeyError, TypeError) as exc:
        ap.error(str(exc))


if __name__ == '__main__':
    main()
