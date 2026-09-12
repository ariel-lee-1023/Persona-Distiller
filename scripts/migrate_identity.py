#!/usr/bin/env python3
"""Lossless legacy import/relocation. No model calls or historical-record rewrites."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
from workflow import runtime_files

CANONICAL = 'transworld-identity'
LEGACY = 'fidelity-ledger'


def inventory(root):
    if not root.exists():
        return {}
    result = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise ValueError('evidence symlink requires explicit reconciliation: ' + str(p.relative_to(root)))
        if p.is_file():
            result[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
        elif p.is_dir():
            result[p.relative_to(root).as_posix() + '/'] = 'directory'
        else:
            raise ValueError('unsupported evidence entry')
    return result


def resolve_record(root, relative):
    """Read canonical records first; legacy fallback is read-only."""
    root = Path(root).resolve()
    rel = Path(relative)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('record path must stay inside repository')
    candidates = [root / rel]
    if rel.parts and rel.parts[0] in (LEGACY, CANONICAL):
        tail = Path(*rel.parts[1:])
        candidates = [root / CANONICAL / tail, root / LEGACY / tail]
        if rel.parts[0] == LEGACY:
            for record in sorted((root / CANONICAL / 'migrations').glob('*.json')):
                for change in json.loads(record.read_text()).get('operational_updates', []):
                    if change['path'] == (Path(CANONICAL) / tail).as_posix():
                        original = (root / change['original']).resolve()
                        if not original.is_relative_to(root) or hashlib.sha256(original.read_bytes()).hexdigest() != change['before_hash']:
                            raise ValueError('preserved operational script no longer matches its migration record')
                        return original

    present = [p for p in candidates if p.is_file()]
    if not present:
        raise FileNotFoundError(relative)
    if any(not p.resolve().is_relative_to(root) for p in present):
        raise ValueError('record escapes repository')
    if len(present) > 1 and present[0].read_bytes() != present[1].read_bytes():
        raise ValueError('conflicting legacy and canonical records')
    return present[0]


# These subtrees are immutable evidence even when they contain executable files.
HISTORICAL_TREES = {'runs', 'history', 'migrations', 'archive', 'archives', 'snapshots'}
SCRIPT_SUFFIXES = {'.py', '.sh', '.bash', '.zsh', '.js', '.mjs', '.cjs', '.rb', '.ps1'}


def relocate_paths(raw):
    old, new = LEGACY.encode(), CANONICAL.encode()
    raw = raw.replace(old + b'/', new + b'/')
    for quote in (b'"', b"'", b'`'):
        raw = raw.replace(quote + old + quote, quote + new + quote)
    return raw


def update_operational_scripts(root, evidence, migration_id):
    """Relink operational copies, preserving byte-identical originals and path history."""
    updates = []
    for path in sorted(evidence.rglob('*')):
        rel = path.relative_to(evidence)
        if any(part in HISTORICAL_TREES for part in rel.parts[:-1]):
            continue
        if not path.is_file() or path.is_symlink() or path.suffix not in SCRIPT_SUFFIXES:
            continue
        original = path.read_bytes()
        updated = relocate_paths(original)
        if updated == original:
            continue
        backup = evidence / 'migrations' / migration_id / 'originals' / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        with backup.open('xb') as out:
            out.write(original)
        shutil.copystat(path, backup)
        path.write_bytes(updated)
        updates.append({'path': path.relative_to(root).as_posix(),
                        'original': backup.relative_to(root).as_posix(),
                        'before_hash': hashlib.sha256(original).hexdigest(),
                        'after_hash': hashlib.sha256(updated).hexdigest()})
    return updates


def migrate(root, import_from=None):
    root = Path(root).resolve()
    source = Path(import_from).resolve() if import_from else root
    old, new = source / LEGACY, root / CANONICAL
    if import_from and not old.exists():
        old = source / CANONICAL
    if import_from and source == root:
        raise ValueError('import source must be a separate read-only repository')
    if old.is_symlink() or new.is_symlink():
        raise ValueError('evidence root cannot be a symlink')
    before, destination = inventory(old), inventory(new)
    # Preflight the entire merge, including directory/file collisions, before any write.
    conflicts = []
    for rel, value in before.items():
        other = rel.rstrip('/') + ('' if rel.endswith('/') else '/')
        if (rel in destination and destination[rel] != value) or other in destination:
            conflicts.append(rel)
    if conflicts:
        raise ValueError('destination conflicts; nothing changed: ' + ', '.join(conflicts))
    migration_id = str(time.time_ns())
    if not old.exists():
        updates = update_operational_scripts(root, new, migration_id) if new.exists() else []
        result = {'schema_version': 1, 'status': 'updated_operational' if updates else ('already_canonical' if new.exists() else 'no_evidence'),
                  'operational_updates': updates, 'model_calls': 0}
        if updates:
            with (new / 'migrations' / (migration_id + '.json')).open('x') as out:
                json.dump(result, out, indent=2)
        return result
    runtime_root = source
    if not (source / 'SKILL.md').is_file():
        found = [p for p in (source / '.agents/skills').glob('*') if (p / 'SKILL.md').is_file()]
        if len(found) == 1:
            runtime_root = found[0].resolve()
    baseline = {'runtime_files': runtime_files(runtime_root),
                'runtime_layout': runtime_root.relative_to(source).as_posix() if runtime_root.is_relative_to(source) else 'external_unresolved',
                'evaluation_record': {'path': LEGACY + '/validation.json', 'hash': before.get('validation.json')} if 'validation.json' in before else None}
    for key, args in [('revision', ['rev-parse', 'HEAD']), ('working_tree', ['status', '--porcelain=v1'])]:
        proc = subprocess.run(['git', '-C', str(source), *args], capture_output=True, text=True)
        baseline[key] = proc.stdout.strip() if proc.returncode == 0 else None
    if not new.exists() and not import_from:
        old.rename(new)
    else:
        new.mkdir(parents=True, exist_ok=True)
        for rel, value in before.items():
            src, dst = old / rel, new / rel
            if value == 'directory':
                dst.mkdir(parents=True, exist_ok=True)
            elif not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        after = inventory(new)
        if any(after.get(rel) != value for rel, value in before.items()):
            raise ValueError('copy verification failed; source retained')
        if not import_from:
            shutil.rmtree(old)
    if any(inventory(new).get(rel) != value for rel, value in before.items()):
        raise ValueError('relocation verification failed')
    operational_updates = update_operational_scripts(root, new, migration_id)
    # Historical artifacts are untouched. Only operational text/configuration is relinked.
    active = [root / n for n in ('SKILL.md', 'README.md', 'AGENTS.md')]
    for directory in ('references', 'scripts', 'tests', '.github', '.agents', '.claude-plugin'):
        active.extend((root / directory).rglob('*'))
    edits = []
    for p in active:
        if p.is_symlink() or not p.is_file() or p.suffix not in {'.md', '.py', '.json', '.yaml', '.yml', '.sh'}:
            continue
        # Preserve prose, encoding and line endings outside the relocated paths.
        original = p.read_bytes()
        updated = relocate_paths(original)
        if updated != original:
            p.write_bytes(updated)
            edits.append(p.relative_to(root).as_posix())
    result = {'schema_version': 1, 'status': 'imported' if import_from else 'migrated',
              'baseline': baseline, 'files': before, 'relocation': {LEGACY + '/': CANONICAL + '/'},
              'active_files_updated': edits, 'operational_updates': operational_updates, 'model_calls': 0,
              'assessment': 'Historical outcomes retain original inputs; no new acceptance inferred.'}
    records = new / 'migrations'
    records.mkdir(exist_ok=True)
    with (records / (migration_id + '.json')).open('x') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return result


def migrate_scope(root, plan, apply=False):
    """Preview/apply an editorially specified patch, preserving all original bytes."""
    from output_structure import SCOPE, inside, structure_issues
    from workflow import digest, file_hash
    from recognition_runner import request_for, runtime_snapshot, validate_plan
    import tempfile

    root = Path(root).resolve()
    if plan.get('structure_revision') != 2 or not plan.get('reviewer'):
        raise ValueError('reviewed structure_revision 2 mapping and reviewer required')
    changes = plan.get('changes', [])
    if not changes or len({c['path'] for c in changes}) != len(changes):
        raise ValueError('distinct reviewed file changes required')
    migration_id = 'scope-' + digest(plan).split(':')[1]
    record_path = root / CANONICAL / 'migrations' / (migration_id + '.json')
    paths = {}
    for change in changes:
        path = inside(root, change['path'])
        rel = path.relative_to(root)
        if any(part in {'.git', 'runs', 'history', 'migrations', 'archive', 'archives', 'snapshots'} for part in rel.parts):
            raise ValueError('historical or repository metadata cannot be edited: ' + str(rel))
        if rel.parts[0] == CANONICAL and rel.as_posix() != SCOPE and not rel.name.endswith('plan.json'):
            raise ValueError('assessment records stay immutable: ' + str(rel))
        if any(parent.is_symlink() for parent in [path, *path.parents] if parent != root and parent.is_relative_to(root)):
            raise ValueError('reviewed changes cannot traverse symlinks: ' + str(rel))
        if path.exists() and not path.is_file():
            raise ValueError('file/directory collision: ' + str(rel))
        if 'content' not in change:
            raise ValueError('each change needs explicit content; null means deletion')
        content = change['content']
        if content is not None and not isinstance(content, str):
            raise ValueError('content must be reviewed UTF-8 text or null for deletion')
        paths[change['path']] = path
    after_hashes = {c['path']: ('sha256:' + hashlib.sha256(c['content'].encode()).hexdigest() if c.get('content') is not None else None) for c in changes}
    current = {rel: file_hash(p) if p.exists() else None for rel, p in paths.items()}
    if record_path.exists() and current == after_hashes:
        return {'status': 'already_applied', 'record': record_path.relative_to(root).as_posix(), 'model_calls': 0}
    for change in changes:
        if 'before_hash' not in change or current[change['path']] != change['before_hash']:
            raise ValueError('destination conflict or stale reviewed bytes; nothing changed: ' + change['path'])
        if change['path'] == SCOPE and current[SCOPE] and current[SCOPE] != after_hashes[SCOPE] and not change.get('reconciliation_reason'):
            raise ValueError('existing reconstruction scope needs an explicit reconciliation_reason; nothing changed')
    source_name = plan.get('legacy_scope')
    if source_name not in paths or source_name not in after_hashes or after_hashes[source_name] is not None:
        raise ValueError('reviewed migration must remove its legacy scope after redistribution')
    source = paths[source_name]
    lines = source.read_text().splitlines()
    required_lines = {i for i, line in enumerate(lines, 1) if line.strip()}
    covered = set()
    for passage in plan.get('passages', []):
        start, end = passage['start_line'], passage['end_line']
        if not (type(start) is int and type(end) is int and 1 <= start <= end <= len(lines)) or not passage.get('reason') or not passage.get('destinations'):
            raise ValueError('each passage needs valid source lines, destinations and editorial reason')
        for dest in passage['destinations']:
            inside(root, dest.split('#')[0])
        covered.update(range(start, end + 1))
    if not required_lines <= covered:
        raise ValueError('reviewed passage mapping must account for every material source line')
    original_runtime = runtime_files(root)
    applicability = []
    with tempfile.TemporaryDirectory() as temp:
        staged = Path(temp) / 'persona'
        shutil.copytree(root, staged, symlinks=True, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        for change in changes:
            path = staged / change['path']
            if change.get('content') is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(change['content'])
        issues = structure_issues(staged)
        from validate_package import local_targets
        for path in [staged / 'SKILL.md', *list((staged / 'references').rglob('*.md'))]:
            for target in local_targets(path.read_text()):
                dest = path.parent / target
                if not dest.exists():
                    issues.append('unresolved runtime link: ' + str(target))
        for passage in plan['passages']:
            for dest in passage['destinations']:
                if not (staged / dest.split('#')[0]).is_file():
                    issues.append('missing passage destination: ' + dest)
        if issues:
            raise ValueError('; '.join(issues))
        updated_runtime = runtime_files(staged)
        contents = runtime_snapshot(staged)
        new_plan = plan.get('recognition_plan')
        if new_plan:
            validate_plan(new_plan)
            for case in new_plan['cases']:
                if not all(p in contents and p.startswith('references/') for p in case['references']):
                    raise ValueError('reviewed recognition references do not resolve')
        for frozen_path in sorted((root / CANONICAL / 'runs').glob('*/frozen.json')):
            frozen = json.loads(frozen_path.read_text())
            for case in frozen['plan']['cases']:
                selected = next((c for c in new_plan['cases'] if c['id'] == case['id']), None) if new_plan else None
                for condition in ('persona', 'control'):
                    before = request_for(frozen, case, condition)
                    after = request_for({'plan': new_plan, 'runtime': contents}, selected, condition) if selected else None
                    applicability.append({'record': frozen_path.relative_to(root).as_posix(), 'record_hash': file_hash(frozen_path),
                        'case': case['id'], 'condition': condition, 'before_request_hash': digest(before),
                        'after_request_hash': digest(after) if after else None,
                        'before_dependencies': before['dependencies'], 'after_dependencies': after['dependencies'] if after else None,
                        'outcome': 'reusable_if_valid' if before == after else ('superseded' if after else 'requires_input_comparison')})
    result = {'schema_version': 1, 'structure_revision': 2, 'status': 'applied' if apply else 'preview',
              'reviewer': plan['reviewer'], 'passages': plan['passages'], 'changes': changes,
              'before_hashes': current, 'after_hashes': after_hashes,
              'before_runtime': original_runtime, 'after_runtime': updated_runtime,
              'assessment_applicability': applicability, 'model_calls': 0,
              'assessment': 'Historical reports unchanged. Layout migration grants no behavioral pass. Judgments require comparison of complete judge inputs.'}
    if not apply:
        return result
    # All conflicts and staged links have been checked before touching the repository.
    originals = root / CANONICAL / 'migrations' / migration_id / 'originals'
    originals.mkdir(parents=True, exist_ok=False)
    for rel, path in paths.items():
        if path.exists():
            backup = originals / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
    for change in changes:
        path = paths[change['path']]
        if change.get('content') is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(change['content'])
    with record_path.open('x') as out:
        json.dump(result, out, ensure_ascii=False, indent=2)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('repository', type=Path)
    ap.add_argument('--import-from', type=Path)
    ap.add_argument('--scope-plan', type=Path, help='reviewed passage mapping and exact replacement contents')
    ap.add_argument('--apply', action='store_true', help='apply scope plan; default is read-only preview')
    args = ap.parse_args()
    if (args.scope_plan and args.import_from) or (args.apply and not args.scope_plan):
        ap.error('--scope-plan cannot import; --apply requires --scope-plan')
    try:
        result = migrate_scope(args.repository, json.loads(args.scope_plan.read_text()), args.apply) if args.scope_plan else migrate(args.repository, args.import_from)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        ap.error(str(exc))


if __name__ == '__main__':
    main()
