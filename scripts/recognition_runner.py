#!/usr/bin/env python3
"""Eight-call recognition runner with frozen inputs, fresh contexts and resumable records."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request

from workflow import Workflow, DispatchStopped, digest, file_hash, runtime_files, encoded
from recognition import DIMENSIONS, assess, delivery_status, require, nonempty

RUBRIC = {
    'dimensions': list(DIMENSIONS),
    'anchors': {'0': 'Contradicts relevant evidence in these circumstances',
                '1': 'Mostly generic, superficial imitation, or substantial mismatch',
                '2': 'Plausible but weakly diagnostic, incomplete, or mixed',
                '3': 'Clearly supported and recognizable, with minor limitations',
                '4': 'Strongly supported, distinctive, and well adapted'},
    'instructions': 'Score each anonymous answer on all five dimensions. Each dimension record needs score (integer 0..4 or "unassessed"), passage (exact answer excerpt), evidence_ids and reason. Conditional coherence also needs pair_reason explaining the changed-condition pair and each answer contribution. Missing evidence is unassessed. Names and catchphrases earn no credit alone. Return JSON {"material_issues":[],"cases":[{"id":"...","A":{dimension:record},"B":{dimension:record},"preference":"A|B|tie","reason":"diagnostic comparison","evidence_ids":["..."]}]}. Judge target-person recognizability, not general answer quality.'
}


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(json.loads(path.read_text()) == value, 'immutable run record differs: ' + path.name)
        return
    with path.open('x') as f:
        f.write(encoded(value) + '\n')


def read(path):
    return json.loads(Path(path).read_text())


def runtime_snapshot(root):
    root = Path(root).resolve()
    require((root / 'SKILL.md').is_file(), 'runtime SKILL.md missing')
    result = {}
    for rel in runtime_files(root):
        p = root / rel
        require('transworld-identity' not in p.resolve().parts and 'fidelity-ledger' not in p.resolve().parts, 'runtime symlink exposes hidden assessment')
        require(p.suffix == '.md', 'standard runtime references must be Markdown; keep assessment JSON outside runtime')
        require(p.name not in ('provenance.md', 'recognition-profile.md', 'episodic.md'), 'assessment artifact in runtime')
        text = p.read_text()
        require(not re.search(r'transworld-identity/|fidelity-ledger/', text), 'runtime routes to hidden assessment artifacts')
        result[rel] = text
    return result


def validate_plan(plan):
    contract = plan.get('contract', {})
    for key in ('subject', 'intended_use', 'period_domains', 'supplied_sources', 'output_location', 'delivery_target'):
        require(bool(contract.get(key)), 'build contract missing ' + key)
    boundary = contract.get('source_boundary', {})
    require(nonempty(boundary.get('priority_materials')), 'finite source priorities required')
    for key in ('reading_units', 'ocr_pages'):
        require(type(boundary.get(key)) is int and boundary[key] >= 0, 'finite source boundary missing ' + key)
    cases = plan.get('cases')
    require(isinstance(cases, list) and len(cases) == 3, 'exactly three cases required')
    require(len({c['id'] for c in cases}) == 3, 'distinct case IDs required')
    require([c.get('kind') for c in cases] == ['characteristic', 'changed_condition', 'interpersonal'], 'case types/order must cover characteristic, changed condition, interpersonal')
    for c in cases:
        for key in ('id', 'task', 'fixed_background', 'stipulated_changes'):
            require(nonempty(c.get(key)), 'scenario missing ' + key)
        require(re.fullmatch(r'[a-zA-Z0-9_-]+', c['id']) is not None, 'unsafe case ID')
    evidence = plan.get('evidence')
    require(isinstance(evidence, list) and evidence, 'source-backed evidence packet required')
    ids = [e['id'] for e in evidence]
    require(len(set(ids)) == len(ids), 'evidence IDs must be unique')
    for e in evidence:
        for key in ('id', 'source', 'locator', 'attribution', 'group_id', 'situation', 'audience', 'available_information', 'constraints', 'observation'):
            require(nonempty(e.get(key)), 'situated evidence missing ' + key)
        require(e.get('claim_type') in ('observed_event', 'recurring_pattern', 'editorial_synthesis', 'new_application'), 'evidence claim type required')
        require(isinstance(e.get('curation'), dict) and e['curation'].get('decision') in ('preserve', 'contextualize', 'correct_or_remove', 'unresolved') and nonempty(e['curation'].get('reason')), 'curation decision and reason required')
        for key in ('conditions', 'exceptions', 'conflicts', 'runtime_support'):
            require(isinstance(e.get(key), list), 'evidence list missing ' + key)
    profile = plan.get('profile')
    require(isinstance(profile, list) and 3 <= len(profile) <= 5, 'freeze three to five diagnostic patterns')
    for p in profile:
        require(p.get('evidence_ids') and all(i in ids for i in p['evidence_ids']), 'pattern evidence IDs must resolve')
        for key in ('pattern', 'circumstances', 'observable_behavior', 'acceptable_variation', 'mismatch', 'diagnostic_reason'):
            require(nonempty(p.get(key)), 'recognition pattern missing ' + key)
        require(set(p.get('scoring_anchors', {})) == set('01234') and all(nonempty(v) for v in p['scoring_anchors'].values()), 'profile-specific anchors 0..4 required')
    config = plan.get('generation', {})
    require(nonempty(config.get('endpoint')) and nonempty(config.get('model')), 'configure generator endpoint/model')
    require(isinstance(config.get('judge_models'), list) and len(config['judge_models']) == 2 and all(nonempty(m) for m in config['judge_models']), 'configure two judge models (same model allowed, recorded)')
    for key in ('answer_max_tokens', 'judge_max_tokens', 'input_token_limit', 'timeout_seconds'):
        require(type(config.get(key)) is int and config[key] > 0, 'finite positive limit required: ' + key)
    require(type(config.get('deadline')) in (int, float) and 0 < config['deadline'] < float('inf'), 'fixed Unix dispatch deadline required')
    require(type(config.get('temperature')) in (int, float) and 0 <= config['temperature'] <= 2, 'finite temperature required')
    require(config.get('max_words') == 250, 'standard answers have a maximum of 250 words')
    require(isinstance(plan.get('identity_labels', []), list) and all(nonempty(x) for x in plan.get('identity_labels', [])), 'identity labels must be literal nonempty strings')


def freeze(runtime, plan, run, workflow):
    validate_plan(plan)
    wf = Workflow(workflow)
    state = wf.status()
    require(Path(state['runtime']).resolve() == Path(runtime).resolve(), 'workflow runtime differs')
    contents = runtime_snapshot(runtime)
    routes = plan.get('runtime_routes', {'scope': 'references/scope.md'})
    require(routes.get('scope') in contents, 'runtime scope contract required')
    for case in plan['cases']:
        refs = case.get('references', [p for p in contents if p.startswith('references/')])
        require(isinstance(refs, list) and all(p in contents and p.startswith('references/') for p in refs), 'case references must resolve inside runtime')
    plan = json.loads(encoded(plan))
    run = Path(run)
    require(run.parent.name == 'runs' and run.parent.parent.name == 'transworld-identity', 'new runs belong in transworld-identity/runs/<run-id>')
    identity = run.parent.parent
    identity.mkdir(parents=True, exist_ok=True)
    evidence_path = identity / 'evidence.json'
    if evidence_path.exists():
        require(read(evidence_path)['records'] == plan['evidence'], 'current evidence packet differs from plan')
    else:
        save(evidence_path, {'schema_version': 1, 'records': plan['evidence']})
    profile_path = identity / 'recognition-profile.md'
    if not profile_path.exists():
        profile_path.write_text('# Recognition profile\n\n' + '\n\n'.join(
            '## ' + p['pattern'] + '\n\n' + '\n'.join(k + ': ' + (encoded(v) if not isinstance(v, str) else v) for k, v in p.items() if k != 'pattern')
            for p in plan['profile']) + '\n')
    plan['profile_document_hash'] = file_hash(profile_path)
    plan['profile_document'] = profile_path.read_text()
    cfg = plan['generation']
    frozen = {'schema_version': 1, 'plan': plan, 'runtime': contents, 'rubric': RUBRIC,
              'hashes': {'runtime': digest(contents), 'modules': {p: digest(t) for p, t in contents.items()},
                         'profile': digest({'patterns': plan['profile'], 'document': plan['profile_document']}), 'source_packet': digest(plan['evidence']),
                         'scenarios': digest(plan['cases']), 'rubric': digest(RUBRIC), 'generation': digest(cfg)}}
    run = Path(run)
    require(run.parent.name == 'runs' and run.parent.parent.name == 'transworld-identity', 'new runs belong in transworld-identity/runs/<run-id>')
    save(run / 'frozen.json', frozen)
    save(run / 'freeze-manifest.json', {'frozen_hash': file_hash(run / 'frozen.json')})
    wf.note('recognition_freeze', {'run_id': run.name, 'hashes': frozen['hashes']})
    return frozen


def request_for(frozen, case, condition):
    plan, contents = frozen['plan'], frozen['runtime']
    cfg = plan['generation']
    common = 'Answer competently using the supplied facts. Make the required choice and explain it. Do not explicitly identify yourself or name the person being represented. Maximum 250 words. Return only the answer. No tools are available.'
    deps = {}
    system = common
    if condition == 'persona':
        paths = sorted(set(['SKILL.md', plan.get('runtime_routes', {}).get('scope', 'references/scope.md')] + case.get('references', [p for p in contents if p.startswith('references/')])) )
        system += '\nRuntime perspective:\n' + '\n'.join(contents[p] for p in paths)
        deps = {p: digest(contents[p]) for p in paths}
    facts = {k: case[k] for k in ('task', 'fixed_background', 'stipulated_changes')}
    return {'endpoint': cfg['endpoint'], 'model': cfg['model'], 'temperature': cfg['temperature'],
            'max_tokens': cfg['answer_max_tokens'], 'timeout_seconds': cfg['timeout_seconds'],
            'input_token_limit': cfg['input_token_limit'], 'max_words': 250,
            'dependencies': deps, 'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': encoded(facts)}]}


def http_client(request, timeout):
    # A child process provides a total wall-time bound, including trickling HTTP responses.
    proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), '_http'],
                          input=encoded(request), capture_output=True, text=True, timeout=timeout)
    require(proc.returncode == 0, 'provider request failed; inspect charged attempt')
    return json.loads(proc.stdout)


def http_child():
    request = json.load(sys.stdin)
    payload = {k: request[k] for k in ('model', 'temperature', 'max_tokens', 'messages')}
    headers = {'Content-Type': 'application/json'}
    if os.environ.get('PERSONA_API_KEY'):
        headers['Authorization'] = 'Bearer ' + os.environ['PERSONA_API_KEY']
    req = urllib.request.Request(request['endpoint'], data=encoded(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=request['timeout_seconds']) as response:
        raw = response.read(2_000_001)
    require(len(raw) <= 2_000_000, 'provider response exceeds transport cap')
    data = json.loads(raw)
    choice = data['choices'][0]
    require(choice.get('finish_reason') != 'length', 'provider output was truncated')
    print(encoded({'text': choice['message']['content'], 'usage': data.get('usage'), 'model': data.get('model')}))


def dispatch(wf, item, role, request, case_id, client, deadline, retry):
    # UTF-8 byte count is a conservative token upper bound for the configured context.
    require(len(encoded(request['messages']).encode()) <= request['input_token_limit'], 'input exceeds conservative token allowance')
    cached = wf.lookup(item, role, request)
    if cached is not None:
        call_id, saved = cached
        return {'call_id': call_id, 'request_hash': digest(request), 'response': saved}
    if time.time() >= deadline:
        raise DispatchStopped('dispatch deadline expired')
    call_id, saved = wf.reserve(item, role, request, case_id, retry)
    if saved is not None:
        return {'call_id': call_id, 'request_hash': digest(request), 'response': saved}
    try:
        remaining = min(request['timeout_seconds'], deadline - time.time())
        if remaining <= 0:
            raise DispatchStopped('deadline expired after reservation')
        response = client(request, remaining)
        wf.finish(call_id, response=response)
        return {'call_id': call_id, 'request_hash': digest(request), 'response': response}
    except BaseException as exc:
        wf.finish(call_id, error=type(exc).__name__)
        raise


def verify_saved(wf, record, request):
    require(record['request_hash'] == digest(request), 'saved request hash differs')
    with wf.transaction() as db:
        if isinstance(record['call_id'], int):
            row = db.execute("SELECT fingerprint,response FROM calls WHERE id=? AND state='completed'", (record['call_id'],)).fetchone()
        else:
            rows = db.execute('SELECT fingerprint,response,lineage FROM imported_calls WHERE fingerprint=?', (record['request_hash'],)).fetchall()
            row = next((r for r in rows if 'import:' + digest(json.loads(r['lineage'])) == record['call_id']), None)
        require(row is not None and row['fingerprint'] == digest(request) and json.loads(row['response']) == record['response'],
                'saved output differs from its completed persistent call')


def usable_record(run, wf, key, role, request, case_id, client, deadline, retry, allow_dispatch, validate):
    """Validate receipt before reuse; one explicit replacement, never retry-until-pass."""
    path = run / (key + '.json')
    had_output = path.exists() or wf.lookup('recognition/' + key, role, request) is not None
    if path.exists():
        record = read(path)
    else:
        require(allow_dispatch, 'missing output; read-only assessment cannot dispatch')
        record = dispatch(wf, 'recognition/' + key, role, request, case_id, client, deadline, retry)
        save(path, record)
    # A tampered mirror or changed input is not a malformed provider output.
    verify_saved(wf, record, request)

    def checked(record):
        try:
            response = record['response']
            require(isinstance(response, dict) and nonempty(response.get('text')), 'provider text missing')
            value = validate(response['text'])
        except (ValueError, TypeError, KeyError) as exc:
            if allow_dispatch:
                wf.check_output(record['call_id'], False, str(exc))
            raise
        if allow_dispatch:
            wf.check_output(record['call_id'], True)
        return value

    try:
        return path, record, checked(record)
    except (ValueError, TypeError, KeyError) as exc:
        if not (allow_dispatch and retry and had_output):
            raise
        # Archive exact mirror bytes and its relocation before changing the current pointer.
        archive = run / 'attempts' / key / (digest(record).split(':')[1] + '.json')
        archive.parent.mkdir(parents=True, exist_ok=True)
        raw = path.read_bytes()
        if archive.exists():
            require(archive.read_bytes() == raw, 'conflicting archived attempt')
        else:
            with archive.open('xb') as out:
                out.write(raw)
        save(archive.with_suffix('.meta.json'), {'original_path': path.name, 'original_hash': file_hash(path),
                                               'call_id': record['call_id'], 'reason': str(exc)})
        # No successful outputs are removed or regenerated by --retry.
        path.unlink()
        record = dispatch(wf, 'recognition/' + key, role, request, case_id, client, deadline, True)
        save(path, record)
        verify_saved(wf, record, request)
        return path, record, checked(record)


def valid_answer(text):
    require(words(text) <= 250, 'generated answer exceeds 250-word bound')
    return text


def valid_judge(text, index, cases, evidence_ids):
    judge = json.loads(text)
    # Run the complete structural/citation checks for this judge before caching it as usable.
    assess([judge] if index == 0 else [None, judge], cases, evidence_ids)
    return judge


def conceal(text, labels):
    changes = []
    for label in sorted(set(labels), key=len, reverse=True):
        # Exact explicit labels only; originals and replacement counts are retained.
        count = text.count(label)
        if count:
            text = text.replace(label, '[identity concealed]')
            changes.append({'literal': label, 'replacement': '[identity concealed]', 'count': count})
    return text, changes


def words(text):
    return len(re.findall(r'[\u3400-\u9fff]|[^\W_]+(?:[’\x27-][^\W_]+)*', text))


def execute(run, workflow, client=http_client, retry=False, allow_dispatch=True):
    run = Path(run)
    require(read(run / 'freeze-manifest.json')['frozen_hash'] == file_hash(run / 'frozen.json'), 'frozen inputs changed')
    frozen = read(run / 'frozen.json')
    validate_plan(frozen['plan'])
    wf = Workflow(workflow)
    state = wf.status()
    require(runtime_snapshot(state['runtime']) == frozen['runtime'], 'runtime changed; freeze a new assessment version')
    cfg = frozen['plan']['generation']
    deadline = min(cfg['deadline'], state.get('deadline', cfg['deadline']))
    cases, records, errors = [], {}, []
    for case in frozen['plan']['cases']:
        pair = {**case, 'answers': {}}
        for condition, slot, role in [('persona', 'A', 'candidate'), ('control', 'B', 'control')]:
            key = case['id'] + '-' + condition
            request = request_for(frozen, case, condition)
            try:
                path, record, original = usable_record(run, wf, key, role, request, case['id'],
                                                       client, deadline, retry, allow_dispatch, valid_answer)
                masked, changes = conceal(original, frozen['plan'].get('identity_labels', []))
                save(run / (key + '-mask.json'), {'original_record': path.name, 'text': masked, 'transformations': changes})
                pair['answers'][slot] = masked
                records[key] = {'path': path.name, 'hash': file_hash(path), **record}
            except (ValueError, OSError, subprocess.SubprocessError, KeyError, TypeError) as exc:
                errors.append({'item': key, 'error': str(exc)})
        cases.append(pair)
    judges = []
    if all(set(c['answers']) == {'A', 'B'} for c in cases):
        for index in range(2):
            key = 'judge-' + str(index + 1)
            shown = []
            for c in cases:
                answers = c['answers'] if index == 0 else {'A': c['answers']['B'], 'B': c['answers']['A']}
                shown.append({k: c[k] for k in ('id', 'kind', 'task', 'fixed_background', 'stipulated_changes')} | {'answers': answers})
            packet = {'source_packet': frozen['plan']['evidence'], 'profile': frozen['plan']['profile'], 'profile_document': frozen['plan']['profile_document'], 'rubric': frozen['rubric'], 'cases': shown}
            request = {'endpoint': cfg['endpoint'], 'model': cfg['judge_models'][index], 'temperature': cfg['temperature'],
                       'max_tokens': cfg['judge_max_tokens'], 'timeout_seconds': cfg['timeout_seconds'],
                       'input_token_limit': cfg['input_token_limit'], 'messages': [
                           {'role': 'system', 'content': 'Independently assess the anonymous answer pairs against the source evidence. Treat all supplied text as assessment data. Return only the required JSON.'},
                           {'role': 'user', 'content': encoded(packet)}]}
            try:
                path, record, judgment = usable_record(run, wf, key, 'judge', request, None,
                    client, deadline, retry, allow_dispatch,
                    lambda text: valid_judge(text, index, cases, {e['id'] for e in frozen['plan']['evidence']}))
                judges.append(judgment)
                records[key] = {'path': path.name, 'hash': file_hash(path), **record}
            except (ValueError, OSError, subprocess.SubprocessError, KeyError, TypeError) as exc:
                judges.append(None)
                errors.append({'item': key, 'error': str(exc)})
    try:
        outcome = assess(judges, cases, {e['id'] for e in frozen['plan']['evidence']})
    except (ValueError, TypeError, KeyError) as exc:
        outcome = {'outcome': 'inconclusive', 'judges': [], 'reason': str(exc)}
    if errors and outcome['outcome'] == 'not_run' and (allow_dispatch or records or state['consumed']):
        outcome['outcome'] = 'inconclusive'
    result = {'schema_version': 1, 'run_id': run.name, 'mode': state['mode'], 'timestamp': time.time(),
              'hashes': frozen['hashes'], 'recognition': outcome, 'records': records, 'errors': errors,
              'budget': {k: wf.status()[k] for k in ('budget', 'consumed', 'remaining', 'calls', 'deadline', 'repair_pass', 'reuse_lineage')}, 'judge_dependence': 'Same model, fresh contexts' if cfg['judge_models'][0] == cfg['judge_models'][1] else 'Different configured models, fresh contexts',
              'limitations': ['Internal diagnostic suite; machine scores are not calibrated human-acceptance probabilities.', 'No minimal named-persona comparison or comprehensive research claim.']}
    # A new status record on each resume retains prior partial outcomes.
    if allow_dispatch:
        save(run / ('result-' + str(time.time_ns()) + '.json'), result)
    return result


def main():
    if len(sys.argv) == 2 and sys.argv[1] == '_http':
        http_child()
        return
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('example-plan')
    p.add_argument('--out', type=Path, required=True)
    p = sub.add_parser('freeze')
    p.add_argument('--runtime', type=Path, required=True); p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True); p.add_argument('--workflow', type=Path, required=True)
    p = sub.add_parser('run')
    p.add_argument('--run', type=Path, required=True); p.add_argument('--workflow', type=Path, required=True)
    p.add_argument('--retry', action='store_true')
    args = ap.parse_args()
    try:
        if args.command == 'example-plan':
            example = read(Path(__file__).resolve().parents[1] / 'assets/standard-plan.example.json')
            example['generation']['deadline'] = time.time() + 600
            save(args.out, example)
            return
        result = freeze(args.runtime, read(args.plan), args.run, args.workflow) if args.command == 'freeze' else execute(args.run, args.workflow, retry=args.retry)
        print(encoded(result))
    except (ValueError, OSError, KeyError) as exc:
        ap.error(str(exc))


if __name__ == '__main__':
    main()
