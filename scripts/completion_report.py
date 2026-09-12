#!/usr/bin/env python3
"""Read-only package/source/recognition acceptance and truthful current delivery status."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from workflow import Workflow, digest, file_hash
from recognition import require, nonempty, delivery_status
from recognition_runner import execute, read, runtime_snapshot, save


def validate_package(package, fidelity=None, routes=None):
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / 'validation.json'
        command = [sys.executable, str(Path(__file__).with_name('validate_package.py')), str(package), '--json', str(output)]
        if routes is not None:
            route_file = Path(tmp) / 'routes.json'; route_file.write_text(json.dumps(routes))
            command += ['--routes', str(route_file)]
        if fidelity is not None:
            command += ['--release', '--fidelity', str(fidelity)]
        proc = subprocess.run(command, capture_output=True, text=True)
        if not output.exists():
            return {'verdict': 'FAIL', 'checks': [], 'detail': proc.stderr or proc.stdout}
        return json.loads(output.read_text())


def current_evidence(dependencies, current):
    return isinstance(dependencies, dict) and bool(dependencies) and all(current.get(p) == h for p, h in dependencies.items())


def report(package, workflow, review_path, run=None, fidelity=None):
    wf = workflow if isinstance(workflow, Workflow) else Workflow(workflow)
    state = wf.status()
    review = read(review_path)
    require(nonempty(review.get('summary')) and nonempty(review.get('reviewer')), 'summary and reviewer required')
    require(isinstance(review.get('limitations'), list), 'record material limitations')
    runtime_error = None
    try:
        contents = runtime_snapshot(state['runtime'])
    except (ValueError, OSError) as exc:
        contents = {}
        runtime_error = str(exc)
    modules = {p: digest(t) for p, t in contents.items()}
    routes = read(Path(run) / 'frozen.json')['plan'].get('runtime_routes') if run and (Path(run) / 'frozen.json').exists() else None
    structural = validate_package(package, routes=routes)
    root_matches = Path(structural.get('skill_root', '')).resolve() == Path(state['runtime']).resolve()
    package_gate = 'passed' if structural['verdict'] == 'PASS' and root_matches and runtime_error is None else 'failed'
    source_checks = review.get('source_checks', [])
    source_ok = review.get('reviewed_all_core_claims') is True and bool(source_checks)
    try:
        packet = read(Path(package) / 'transworld-identity/evidence.json')
    except (OSError, ValueError):
        packet = {'records': []}
        source_ok = False
    evidence = {e['id']: e for e in packet['records']}
    for row in source_checks:
        ok = row.get('outcome') == 'passed' and current_evidence(row.get('dependencies'), modules)
        ok = ok and all(nonempty(row.get(k)) for k in ('claim', 'assessment', 'condition_or_exception'))
        ok = ok and (row.get('implementation_safeguard') is True or (row.get('evidence_ids') and all(i in evidence for i in row['evidence_ids'])))
        source_ok = source_ok and bool(ok)
    covered = {p for row in source_checks for p in row.get('dependencies', {})}
    source_ok = source_ok and 'SKILL.md' in covered
    source_gate = 'passed' if source_ok else 'inconclusive'
    if review.get('verified_material_defect') is True:
        source_gate = 'failed'
    recognition = {'outcome': 'not_run', 'judges': []}
    assessment = None
    if run is not None:
        try:
            assessment = execute(run, wf.path, allow_dispatch=False)
            recognition = assessment['recognition']
            # The current source packet and profile must match the frozen judge inputs.
            frozen = read(Path(run) / 'frozen.json')
            if 'assessment_scope' in frozen and file_hash(Path(package) / frozen['assessment_scope']['path']) != frozen['assessment_scope']['hash']:
                recognition = {'outcome': 'inconclusive', 'reason': 'current assessment scope differs from frozen judge inputs'}
            if packet['records'] != frozen['plan']['evidence'] or file_hash(Path(package) / 'transworld-identity/recognition-profile.md') != frozen['plan'].get('profile_document_hash'):
                recognition = {'outcome': 'inconclusive', 'reason': 'current evidence/profile differs from frozen inputs'}
        except (OSError, ValueError, KeyError) as exc:
            recognition = {'outcome': 'inconclusive', 'reason': str(exc)}
    if source_gate == 'failed':
        recognition = {'outcome': 'failed', 'reason': 'separately verified material source/attribution defect'}
    research = validate_package(package, fidelity) if fidelity else None
    status = delivery_status(package_gate, source_gate, recognition['outcome'])
    budget = {k: state[k] for k in ('budget', 'consumed', 'remaining', 'calls', 'deadline', 'repair_pass', 'reuse_lineage') if k in state}
    # Drop machine-local validator paths from the publishable report.
    structural = {k: v for k, v in structural.items() if k not in ('package', 'skill_root')}
    return {'schema_version': 1, 'structure_revision': 2, 'run_id': Path(run).name if run else None, 'mode': state['mode'],
            'timestamp': time.time(), 'delivery_status': status, 'summary': review['summary'],
            'runtime_error': runtime_error, 'runtime_hash': digest(contents), 'module_hashes': modules,
            'revision': review.get('revision'), 'hashes': assessment['hashes'] if assessment else None,
            'gates': {'package': package_gate, 'source': source_gate, 'machine_recognition': recognition['outcome']},
            'package_checks': structural, 'source_review': review, 'recognition': recognition,
            'assessment_records': assessment['records'] if assessment else {},
            'assessment_errors': assessment['errors'] if assessment else [],
            'budget': budget, 'research': {'assessed': research is not None, 'outcome': research['verdict'] if research else 'not_run'},
            'claim': 'Package and source gates and bounded machine recognition passed.' if status == 'standard_accepted' else 'Candidate; required acceptance is incomplete, failed or inconclusive.',
            'limitations': review['limitations'] + ['Machine recognition is not a calibrated probability of human acceptance; generic control does not establish added value over a minimal persona prompt.']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('package', type=Path); ap.add_argument('--workflow', type=Path, required=True)
    ap.add_argument('--review', type=Path, required=True); ap.add_argument('--run', type=Path)
    ap.add_argument('--out', type=Path, required=True); ap.add_argument('--fidelity', type=Path)
    args = ap.parse_args()
    try:
        wf = Workflow(args.workflow)
        result = report(args.package, wf, args.review, args.run, args.fidelity)
        require(args.out.parent.resolve() == (args.package / 'transworld-identity').resolve(), 'new validation writes use canonical evidence directory')
        # Preserve the exact previous current report before updating its pointer.
        if args.out.exists():
            historical = args.out.parent / 'history' / (str(time.time_ns()) + '-' + args.out.name)
            historical.parent.mkdir(exist_ok=True)
            historical.write_bytes(args.out.read_bytes())
        temp = args.out.with_suffix('.tmp')
        temp.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
        temp.replace(args.out)
        wf.stop()
        print(result['delivery_status'])
    except (ValueError, OSError, KeyError, TypeError) as exc:
        ap.error(str(exc))


if __name__ == '__main__':
    main()
