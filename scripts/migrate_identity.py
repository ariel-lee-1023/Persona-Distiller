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
        text = p.read_text()
        updated = text.replace(LEGACY + '/', CANONICAL + '/')
        for quote in ('\"', "'", '`'):
            updated = updated.replace(quote + LEGACY + quote, quote + CANONICAL + quote)
        if updated != text:
            p.write_text(updated)
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('repository', type=Path)
    ap.add_argument('--import-from', type=Path)
    args = ap.parse_args()
    try:
        print(json.dumps(migrate(args.repository, args.import_from), indent=2))
    except (OSError, ValueError) as exc:
        ap.error(str(exc))


if __name__ == '__main__':
    main()
