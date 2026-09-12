"""Release evidence checks. Hashes bind records to bytes, not to their truthfulness."""
import hashlib
import json
from pathlib import Path
import math
from behavioral_checks import check_behavioral


def file_hash(path):
    return 'sha256:' + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runtime_hash(skill_root):
    root = Path(skill_root).resolve()
    files = [root / 'SKILL.md'] + sorted(p for p in (root / 'references').rglob('*') if p.is_file())
    manifest = []
    for path in files:
        if not path.resolve().is_relative_to(root):
            raise ValueError('runtime file escapes skill root: ' + str(path))
        manifest.append([path.relative_to(root).as_posix(), file_hash(path)])
    return 'sha256:' + hashlib.sha256(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, low=0, high=1):
    if type(value) not in (float, int):
        return False
    try:
        return math.isfinite(value) and low <= value <= high
    except OverflowError:
        return False


def load_evidence(path):
    """Reject non-JSON constants and float overflow before schema validation."""
    def reject_constant(value):
        raise ValueError('non-finite number in ' + str(path) + ': ' + value)

    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            reject_constant(value)
        return result

    return json.loads(Path(path).read_text(), parse_constant=reject_constant, parse_float=finite_float)


def validate_declared_schema(data, name):
    # Import only for release checks; structure-only validation needs no dependency.
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError
    except ImportError as exc:
        raise ValueError('release validation requires jsonschema; install with '
                         'python3 -m pip install -r requirements-release.txt') from exc
    path = Path(__file__).resolve().parents[1] / 'references' / 'schemas' / (name + '.schema.json')
    schema = load_evidence(path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ValueError('invalid declared schema ' + str(path) + ': ' + exc.message) from exc
    error = next(Draft202012Validator(schema).iter_errors(data), None)
    if error is not None:
        location = '/'.join(str(part) for part in error.absolute_path) or '<root>'
        raise ValueError(name + '.json at ' + location + ': ' + error.message)


def validate_register_evidence(registers):
    """Cross-field invariants that JSON Schema cannot express."""
    require(registers['verdict'] != 'INSUFFICIENT_EVIDENCE', 'register discovery lacks sufficient stable evidence')
    if 'stability' in registers:
        require(registers['stability']['stable'] is True and registers['stability']['adequate'] is True
                and registers['stability']['family_agreement'] >= registers['stability']['minimum_agreement'], 'unstable register discovery cannot support release')
    units = registers['units']
    unit_ids = [u['unit_id'] for u in units]
    require(len(unit_ids) == len(set(unit_ids)) == registers['n_units'],
            'recorded unit IDs must be unique and match n_units')
    matrix_ids = registers['distance_matrix']['units']
    require(len(matrix_ids) == len(unit_ids) and len(set(matrix_ids)) == len(matrix_ids)
            and set(matrix_ids) == set(unit_ids),
            'distance_matrix.units must name every recorded unit exactly once')
    size = len(matrix_ids)
    for name in ('z_distance', 'ratio_exceedances'):
        if name not in registers['distance_matrix']:
            continue
        matrix = registers['distance_matrix'][name]
        require(len(matrix) == size and all(len(row) == size for row in matrix),
                name + ' dimensions must correspond to distance_matrix.units')
        for row in matrix:
            for value in row:
                require(number(value, 0, math.inf), name + ' values must be finite nonnegative numbers')
                if name == 'ratio_exceedances':
                    require(type(value) is int, 'ratio_exceedances values must be integers')
        for i, row in enumerate(matrix):
            for j, value in enumerate(row):
                require(i != j or value == 0, name + ' diagonal must be zero')
                require(math.isclose(value, matrix[j][i], rel_tol=1e-9, abs_tol=1e-12),
                        name + ' must be symmetric')
    families = registers['families']
    family_ids = [family['family_id'] for family in families]
    require(len(family_ids) == len(set(family_ids)) == registers['n_registers'],
            'unique family IDs must match n_registers')
    expected_verdict = 'SINGLE_REGISTER' if len(families) == 1 else 'MULTI_REGISTER'
    require(registers['verdict'] == expected_verdict, 'register verdict disagrees with family count')
    assignment = {}
    for family in families:
        for member in family['members']:
            require(member in unit_ids, 'family contains an unknown unit: ' + member)
            require(member not in assignment, 'unit assigned more than once: ' + member)
            assignment[member] = family['family_id']
    require(set(assignment) == set(unit_ids), 'families must partition all recorded units')
    for unit in units:
        require('family' not in unit or unit['family'] == assignment[unit['unit_id']],
                'unit family mirror disagrees with family membership: ' + unit['unit_id'])


def projection_rows(result, expected):
    rows = result['items']
    require(isinstance(rows, list) and bool(rows), 'projection items required')
    require(len({r['id'] for r in rows}) == len(rows) and {r['id'] for r in rows} == set(expected),
            'projection IDs must exactly cover the assigned partition')
    for r in rows:
        require(all(isinstance(r.get(k), str) and r[k].strip() for k in ('prompt', 'answer', 'baseline_answer', 'rationale')), 'record prompts, both answers and grading rationale')
        require(all(type(r.get(k)) is int and r[k] in (0, 1, 2) for k in ('score', 'baseline_score')), 'projection item scores must be 0, 1 or 2')
    score = sum(r['score'] for r in rows) / (2 * len(rows))
    baseline = sum(r['baseline_score'] for r in rows) / (2 * len(rows))
    require(number(result.get('overall')) and abs(result['overall'] - score) < 1e-8, 'projection aggregate disagrees with items')
    require(number(result.get('baseline')) and abs(result['baseline'] - baseline) < 1e-8, 'baseline aggregate disagrees with items')
    for level in (1, 2):
        value = sum(r['score'] == level for r in rows) / len(rows)
        require(number(result.get('hit_' + str(level))) and abs(result['hit_' + str(level)] - value) < 1e-8, 'projection hit rates disagree with items')
    require(result.get('fresh_context') is True, 'projection requires a fresh prediction context')
    require(all(isinstance(result.get(k), str) and result[k].strip() for k in ('model', 'settings', 'baseline_prompt')), 'record shared model/settings and minimal baseline prompt')
    require(score >= 0.5, 'projection below 0.50 release threshold')
    require(score >= baseline, 'persona regresses against minimal role baseline')


def release_checks(skill_root, fidelity_path):
    checks = []
    def run(label, fn):
        try:
            result = fn()
            checks.append({'check': label, 'level': 'error', 'ok': True,
                           'detail': json.dumps(result, ensure_ascii=False) if result is not None else 'release evidence verified'})
        except (KeyError, TypeError, ValueError, OSError, AttributeError) as exc:
            checks.append({'check': label, 'level': 'error', 'ok': False, 'detail': str(exc)})
    try:
        fidelity_path = Path(fidelity_path)
        f = load_evidence(fidelity_path)
        require(isinstance(f, dict), 'fidelity must be an object')
        digest = runtime_hash(skill_root)
        split_path = fidelity_path.parent / 'split.json'
        registers_path = fidelity_path.parent / 'registers.json'
        split = load_evidence(split_path)
        registers = load_evidence(registers_path)
    except (ValueError, OSError) as exc:
        return [{'check': 'R0', 'level': 'error', 'ok': False, 'detail': str(exc)}]

    # Do not interpret malformed evidence to decide which release gates apply.
    run('R0.fidelity-schema', lambda: validate_declared_schema(f, 'fidelity'))
    run('R0.registers-schema', lambda: validate_declared_schema(registers, 'registers'))
    if any(not check['ok'] for check in checks):
        return checks
    run('R0.register-evidence', lambda: validate_register_evidence(registers))
    if not checks[-1]['ok']:
        return checks

    def freshness():
        require(f.get('content_hash') == digest, 'package hash missing or stale')
        require(f.get('split_hash') == file_hash(split_path), 'split hash missing or stale')
        require(f.get('registers_hash') == file_hash(registers_path), 'register mapping hash missing or stale')
        require(isinstance(f.get('stale'), list) and set(f['stale']) <= {'style'}, 'release requires all gating results current')
        if f['stale']:
            require(isinstance(f.get('style_staleness_note'), str) and f['style_staleness_note'].strip(), 'stale style needs a coverage note')
    run('R1', freshness)

    def independence():
        require(split.get('version') == 2, 'need grouped split version 2 made before extraction')
        parts = split['partitions']
        require(set(parts) == {'train', 'development', 'test'}, 'need train/development/test partitions')
        ids = [i for values in parts.values() for i in values]
        require(all(isinstance(v, list) and v for v in parts.values()), 'every partition must be nonempty')
        require(len(ids) == len(set(ids)) and set(ids) == set(split['passage_groups']), 'partition IDs overlap or inventory is incomplete')
        used = {}
        for part, values in parts.items():
            for pid in values:
                g = split['passage_groups'][pid]
                require(g not in used or used[g] == part, 'work/episode leaks across partitions: ' + g)
                require(split['group_assignments'][g] == part, 'group assignment mismatch')
                used[g] = part
        require(set(used) == set(split['group_assignments']), 'unused group assignment')
        require(f['isolation']['split_before_extraction'] is True and type(f['isolation']['test_exposures']) is int and f['isolation']['test_exposures'] == 1,
                'final test must be reserved before extraction and used once')
        require(f['isolation']['construction_partitions'] == ['train'], 'construction may use train only')
    run('R2', independence)

    for phase, part in (('gate', 'development'), ('final', 'test')):
        def projection(phase=phase, part=part):
            result = f['projection'][phase]
            require(result.get('content_hash') == digest, 'projection.' + phase + ' hash stale')
            projection_rows(result, split['partitions'][part])
            require(result.get('passed') is True, 'projection.' + phase + ' not passed')
        run('R3.' + phase, projection)

    def cost():
        c = f['cost']
        require(c.get('content_hash') == digest, 'cost hash stale')
        keys = ('total_divergences', 'slated_for_core', 'in_core_final', 'logged_out', 'missing_unlogged')
        require(all(type(c.get(k)) is int and c[k] >= 0 for k in keys), 'cost counts must be nonnegative integers')
        require(c['presence_assertion'] == 'pass' and c['missing_unlogged'] == 0, 'cost presence gate failed')
        require(c['in_core_final'] + c['logged_out'] == c['total_divergences'], 'cost inventory does not reconcile')
        require(c['in_core_final'] <= c['slated_for_core'] <= c['total_divergences'], 'cost counts inconsistent')
        require(c['total_divergences'] == 0 or c['in_core_final'] > 0, 'nonempty divergence inventory needs a core refusal')
    run('R4', cost)

    def families():
        ids = [x['family_id'] for x in registers['families']]
        require(len(ids) == len(set(ids)) == registers['n_registers'] and len(ids) > 0, 'invalid register family count')
        require(set(f['register_families']) == set(ids), 'fidelity family IDs disagree with mapping')
        if len(ids) == 1:
            if f.get('merge_triggered', False):
                require(isinstance(f.get('merge_review'), str) and f['merge_review'].strip(), 'single-family merge needs a recorded matrix review')
            return
        d = f['discrimination']
        require(d.get('content_hash') == digest and d.get('label_type') == 'register_family', 'discrimination must be current and score families')
        require(d.get('mask_names') is True and type(d.get('n')) is int and d['n'] >= 2 and number(d.get('score'), .7), 'discrimination gate failed')
    run('R5', families)

    def routing():
        ids = {x['family_id'] for x in registers['families']}
        if len(ids) == 1:
            return
        r = f['register_selection']
        require(r.get('content_hash') == digest, 'register selection hash stale')
        cases = r['cases']
        require(isinstance(cases, list) and len(cases) >= len(ids), 'need behavioral register selection cases')
        require({c['expected'] for c in cases} == ids, 'selection cases must cover every family')
        for c in cases:
            require(all(isinstance(c.get(k), str) and c[k].strip() for k in ('audience', 'task', 'stakes', 'answer', 'rationale')), 'selection cases need audience, task, stakes, generated answer and rationale')
            require(c['selected'] in ids and c['observed'] in ids, 'unknown selected/observed register')
        score = sum(c['selected'] == c['expected'] == c['observed'] for c in cases) / len(cases)
        require(number(r.get('score')) and abs(r['score'] - score) < 1e-8 and score >= .7, 'behavioral register selection gate failed')
    run('R6', routing)

    def style():
        s = f['style']
        if 'style' in f.get('stale', []):
            require(isinstance(s.get('content_hash'), str), 'old style hash required')
            return
        require(s.get('content_hash') == digest, 'style hash stale')
        require(s.get('modulation_reproduced') is True and s.get('avoid_list_violations') == 0, 'style gate failed')
    run('R7', style)

    def scope():
        root = Path(skill_root)
        contract = root / 'references' / 'scope.md'
        require(contract.is_file() and len(contract.read_text().strip()) >= 80, 'need operational references/scope.md')
        require('references/scope.md' in (root / 'SKILL.md').read_text(), 'core must load scope contract')
    run('R8', scope)
    for kind in ('reasoning', 'commitment', 'scope', 'identity'):
        run('R9.' + kind, lambda kind=kind: check_behavioral(f['behavioral'], digest, kind))
    return checks
