#!/usr/bin/env python3
"""Persistent evaluation scheduling. Content scoring and research gates live elsewhere."""
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import time


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def digest(value):
    return 'sha256:' + hashlib.sha256(encoded(value).encode()).hexdigest()


def file_hash(path):
    return 'sha256:' + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runtime_files(root):
    root = Path(root).resolve()
    paths = [root / 'SKILL.md'] + sorted(p for p in (root / 'references').rglob('*') if p.is_file())
    result = {}
    for p in paths:
        if not p.resolve().is_relative_to(root):
            raise ValueError('runtime path escapes root')
        if p.is_file():
            result[p.relative_to(root).as_posix()] = file_hash(p)
    return result


class DispatchStopped(ValueError):
    pass


class Workflow:
    def __init__(self, path):
        self.path = Path(path).resolve()
        if not self.path.is_file():
            raise ValueError('initialize a workflow before evaluation dispatch')

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @classmethod
    def create(cls, path, runtime, scope, affected_modules, operation='upgrade', change_type='content',
               mode='standard', budget=None, authorization=None, deadline=None):
        if mode not in ('standard', 'research') or operation not in ('new', 'upgrade') or change_type not in ('content', 'formatting'):
            raise ValueError('invalid workflow mode, operation or change type')
        if not isinstance(scope, str) or not scope.strip() or not isinstance(affected_modules, list) or not affected_modules:
            raise ValueError('record scope and affected modules before editing')
        if mode == 'research' and (not authorization or budget is None):
            raise ValueError('research requires explicit user authorization and a fixed call budget')
        budget = 8 if budget is None else budget
        if type(budget) is not int or budget < 0 or (mode == 'standard' and budget > 8):
            raise ValueError('standard initial call budget must be 0..8; research needs a nonnegative integer')
        for rel in affected_modules:
            if not isinstance(rel, str) or Path(rel).is_absolute() or '..' in Path(rel).parts:
                raise ValueError('affected modules must be relative runtime paths')
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents a resume from silently replacing the budget.
        with path.open('x'):
            pass
        self = cls(path)
        with self.transaction() as db:
            db.executescript('''CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE calls (id INTEGER PRIMARY KEY, item TEXT, fingerprint TEXT, role TEXT,
                candidate TEXT, pass INTEGER, state TEXT, request TEXT, response TEXT, error TEXT);
                CREATE TABLE events (id INTEGER PRIMARY KEY, kind TEXT, value TEXT);
                CREATE TABLE runtime_blobs (hash TEXT PRIMARY KEY, content BLOB NOT NULL);
                CREATE TABLE imported_calls (item TEXT, fingerprint TEXT, role TEXT, response TEXT, lineage TEXT, PRIMARY KEY(item,fingerprint));''')
            config = dict(version=1, runtime=str(Path(runtime).resolve()), scope=scope,
                          affected_modules=affected_modules, operation=operation, change_type=change_type,
                          mode=mode, budget=budget, authorization=authorization, repair_pass=0, stopped=False,
                          initial_files=runtime_files(runtime), deadline=deadline if deadline is not None else time.time() + 600)
            db.executemany('INSERT INTO config VALUES (?,?)', [(k, encoded(v)) for k, v in config.items()])
            self.save_runtime(db, config['runtime'], config['initial_files'])
        return self

    @staticmethod
    def save_runtime(db, root, files):
        for rel, expected in files.items():
            raw = (Path(root) / rel).read_bytes()
            if 'sha256:' + hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError('runtime changed while checkpointing')
            db.execute('INSERT OR IGNORE INTO runtime_blobs VALUES (?,?)', (expected, raw))

    @staticmethod
    def config(db):
        return {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM config')}

    def status(self):
        with self.transaction() as db:
            result = self.config(db)
            result['calls'] = [dict(r) for r in db.execute('SELECT id,item,role,candidate,pass,state,error FROM calls ORDER BY id')]
            for call in result['calls']:
                call['output_usable'] = self.output_usable(db, call['id'])
            result['consumed'] = len(result['calls'])
            result['remaining'] = max(0, result['budget'] - result['consumed'])
            result['reuse_lineage'] = [json.loads(r[0]) for r in db.execute('SELECT lineage FROM imported_calls')] if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='imported_calls'").fetchone() else []
            result['events'] = [{'kind': r['kind'], 'value': json.loads(r['value'])} for r in db.execute('SELECT * FROM events ORDER BY id')]
            return result

    def note(self, kind, value):
        with self.transaction() as db:
            db.execute('INSERT INTO events(kind,value) VALUES (?,?)', (kind, encoded(value)))

    def import_calls(self, source):
        """Import matching successful outputs from separately scoped prior work, uncharged.

        Requests still match exact fingerprints at reuse time. Source records are read-only.
        """
        source = Path(source).resolve()
        if source == self.path:
            raise ValueError('resume this workflow directly')
        other = sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)
        other.row_factory = sqlite3.Row
        try:
            rows = [dict(r) for r in other.execute("SELECT * FROM calls WHERE state='completed'") if self.output_usable(other, r['id']) is not False]
        finally:
            other.close()
        source_hash = file_hash(source)
        with self.transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS imported_calls (item TEXT, fingerprint TEXT, role TEXT, response TEXT, lineage TEXT, PRIMARY KEY(item,fingerprint))')
            for row in rows:
                if digest(json.loads(row['request'])) != row['fingerprint']:
                    raise ValueError('historical request hash mismatch')
                prior = db.execute('SELECT response FROM imported_calls WHERE item=? AND fingerprint=?', (row['item'], row['fingerprint'])).fetchone()
                if prior and prior['response'] != row['response']:
                    raise ValueError('conflicting imported outputs; retain both source records')
                lineage = {'source_database_hash': source_hash, 'source_call_id': row['id']}
                db.execute('INSERT OR IGNORE INTO imported_calls VALUES (?,?,?,?,?)',
                           (row['item'], row['fingerprint'], row['role'], row['response'], encoded(lineage)))
            db.execute('INSERT INTO events(kind,value) VALUES (?,?)', ('import_calls', encoded({'source_database_hash': source_hash, 'completed_records': len(rows)})))

    def repair(self):
        with self.transaction() as db:
            cfg = self.config(db)
            if cfg['stopped'] or (cfg['mode'] == 'standard' and cfg['repair_pass'] >= 1):
                raise DispatchStopped('standard allows at most one repair pass; completion stops dispatch')
            db.execute('UPDATE config SET value=? WHERE key=?', (encoded(cfg['repair_pass'] + 1), 'repair_pass'))

    def stop(self):
        with self.transaction() as db:
            db.execute('UPDATE config SET value=? WHERE key=?', ('true', 'stopped'))

    def authorize_more(self, calls, authorization, deadline=None):
        if type(calls) is not int or calls <= 0 or not isinstance(authorization, str) or not authorization.strip():
            raise ValueError('additional calls require explicit authorization and a positive fixed allowance')
        if deadline is not None and (type(deadline) not in (int, float) or not time.time() < deadline < float('inf')):
            raise ValueError('explicit deadline extension must be finite and in the future')
        with self.transaction() as db:
            cfg = self.config(db)
            if deadline is not None:
                db.execute('UPDATE config SET value=? WHERE key=?', (encoded(deadline), 'deadline'))
            db.execute('UPDATE config SET value=? WHERE key=?', (encoded(cfg['budget'] + calls), 'budget'))
            db.execute('UPDATE config SET value=? WHERE key=?', ('false', 'stopped'))
            db.execute('INSERT INTO events(kind,value) VALUES (?,?)', ('authorization', encoded({'additional_calls': calls, 'authorization': authorization, 'deadline': deadline})))

    @staticmethod
    def output_usable(db, call_id):
        # Older ledgers have no content validation metadata; validate them on use.
        if not db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='output_checks'").fetchone():
            return None
        row = db.execute('SELECT usable FROM output_checks WHERE call_id=?', (str(call_id),)).fetchone()
        return bool(row[0]) if row else None

    def check_output(self, call_id, usable, reason=None):
        """Record content validity separately from receipt; original responses stay intact."""
        with self.transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS output_checks (call_id TEXT PRIMARY KEY, usable INTEGER, reason TEXT)')
            previous = db.execute('SELECT usable,reason FROM output_checks WHERE call_id=?', (str(call_id),)).fetchone()
            if previous is None or bool(previous['usable']) != usable or previous['reason'] != reason:
                db.execute('INSERT INTO events(kind,value) VALUES (?,?)', ('output_validation', encoded({'call_id': call_id, 'usable': usable, 'reason': reason})))
                db.execute('INSERT INTO output_checks VALUES (?,?,?) ON CONFLICT(call_id) DO UPDATE SET usable=excluded.usable, reason=excluded.reason', (str(call_id), int(usable), reason))

    def lookup(self, item, role, request):
        fingerprint = digest(request)
        with self.transaction() as db:
            rows = db.execute("SELECT id,response FROM calls WHERE item=? AND role=? AND fingerprint=? AND state='completed' ORDER BY id DESC", (item, role, fingerprint)).fetchall()
            for row in rows:
                if self.output_usable(db, row['id']) is not False:
                    return row['id'], json.loads(row['response'])
            if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='imported_calls'").fetchone():
                row = db.execute('SELECT response,lineage FROM imported_calls WHERE item=? AND role=? AND fingerprint=?', (item, role, fingerprint)).fetchone()
                if row:
                    call_id = 'import:' + digest(json.loads(row['lineage']))
                    if self.output_usable(db, call_id) is not False:
                        return call_id, json.loads(row['response'])
        return None

    def reserve(self, item, role, request, candidate=None, retry=False):
        if role not in ('candidate', 'control', 'judge', 'baseline', 'neighbor', 'grader', 'delegated') or not item:
            raise ValueError('record a stable evaluation item ID and role')
        fingerprint = digest(request)
        with self.transaction() as db:
            cfg = self.config(db)
            old = db.execute('SELECT * FROM calls WHERE item=? AND fingerprint=? ORDER BY id DESC LIMIT 1', (item, fingerprint)).fetchone()
            if old and old['state'] == 'completed' and self.output_usable(db, old['id']) is not False:
                return old['id'], json.loads(old['response'])
            if not old and db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='imported_calls'").fetchone():
                imported = db.execute('SELECT * FROM imported_calls WHERE item=? AND fingerprint=? AND role=?', (item, fingerprint, role)).fetchone()
                if imported:
                    call_id = 'import:' + digest(json.loads(imported['lineage']))
                    if self.output_usable(db, call_id) is not False:
                        return call_id, json.loads(imported['response'])
                    if not retry:
                        raise DispatchStopped('invalid imported output needs an explicit retry')
            if old and not retry:
                raise DispatchStopped('unfinished/failed attempt remains charged; inspect it before explicit retry')
            used = db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]
            if cfg['stopped'] or used >= cfg['budget'] or time.time() >= cfg.get('deadline', float('inf')):
                raise DispatchStopped('evaluation dispatch stopped or budget exhausted; report current artifact')
            if cfg['mode'] == 'standard':
                previous = db.execute('SELECT pass FROM calls WHERE item=? ORDER BY id DESC LIMIT 1', (item,)).fetchone()
                if previous and not old and previous['pass'] >= cfg['repair_pass']:
                    raise DispatchStopped('changed evaluation inputs require the bounded repair pass')
                if cfg['change_type'] == 'formatting':
                    raise DispatchStopped('formatting-only work reuses evidence; no new model evaluation')
                if role in ('baseline', 'neighbor', 'delegated'):
                    raise DispatchStopped('standard mode does not dispatch baseline or neighbor comparisons')
                # Delegation still consumes the same global ceiling; role-specific limits
                # apply when delegates reserve each candidate/grader call through this API.
                if role in ('candidate', 'control'):
                    if not candidate:
                        raise ValueError('candidate generations need a stable response ID')
                    current = {r[0] for r in db.execute('SELECT DISTINCT candidate FROM calls WHERE role=? AND pass=?', (role, cfg['repair_pass']))}
                    cap = 3
                    if candidate not in current and len(current) >= cap:
                        raise DispatchStopped('standard candidate response limit reached')
                if role in ('grader', 'judge'):
                    current = {r[0] for r in db.execute('SELECT DISTINCT item FROM calls WHERE role=? AND pass=?', (role, cfg['repair_pass']))}
                    if item not in current and len(current) >= 2:
                        raise DispatchStopped('standard permits two judges per pass')
            row = db.execute('INSERT INTO calls(item,fingerprint,role,candidate,pass,state,request) VALUES (?,?,?,?,?,?,?)',
                             (item, fingerprint, role, candidate, cfg['repair_pass'], 'reserved', encoded(request)))
            return row.lastrowid, None

    def finish(self, call_id, response=None, error=None):
        with self.transaction() as db:
            row = db.execute('SELECT state FROM calls WHERE id=?', (call_id,)).fetchone()
            if not row or row['state'] != 'reserved':
                raise ValueError('only a reserved call can be completed; prior records are retained')
            db.execute('UPDATE calls SET state=?,response=?,error=? WHERE id=?',
                       ('failed' if error else 'completed', None if error else encoded(response), error, call_id))

    def dispatch(self, item, role, endpoint, model, messages, temperature, client, candidate=None, dependencies=None, retry=False):
        request = dict(endpoint=endpoint, model=model, messages=messages, temperature=temperature, dependencies=dependencies or {})
        call_id, saved = self.reserve(item, role, request, candidate, retry)
        if saved is not None:
            return saved
        try:
            response = client(endpoint, model, messages, temperature)
            self.finish(call_id, response=response)
            return response
        except BaseException as exc:
            self.finish(call_id, error=type(exc).__name__)
            raise

    def checkpoint(self, remaining, source_processing=None):
        cfg = self.status()
        current = runtime_files(cfg['runtime'])
        value = {'time': time.time(), 'runtime_files': current, 'remaining_items': remaining,
                 'source_processing': source_processing or {}, 'consumed': cfg['consumed'], 'remaining_calls': cfg['remaining']}
        with self.transaction() as db:
            self.save_runtime(db, cfg['runtime'], current)
            db.execute('INSERT INTO events(kind,value) VALUES (?,?)', ('checkpoint', encoded(value)))
        return value


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init')
    p.add_argument('workflow', type=Path); p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--mode', choices=('standard', 'research'), default='standard')
    p.add_argument('--budget', type=int); p.add_argument('--authorization')
    for command in ('status', 'repair', 'stop', 'checkpoint', 'authorize-more', 'reserve', 'finish', 'import-calls'):
        p = sub.add_parser(command); p.add_argument('workflow', type=Path)
        if command == 'import-calls': p.add_argument('--source', type=Path, required=True)
        if command == 'checkpoint': p.add_argument('--record', type=Path, required=True)
        if command == 'authorize-more':
            p.add_argument('--calls', type=int, required=True); p.add_argument('--authorization', required=True); p.add_argument('--deadline', type=float)
        if command == 'reserve':
            p.add_argument('--item', required=True); p.add_argument('--role', required=True)
            p.add_argument('--request', type=Path, required=True); p.add_argument('--candidate'); p.add_argument('--retry', action='store_true')
        if command == 'finish':
            p.add_argument('--call-id', type=int, required=True)
            g=p.add_mutually_exclusive_group(required=True); g.add_argument('--response', type=Path); g.add_argument('--error')
    args = ap.parse_args()
    try:
        if args.command == 'init':
            plan = json.loads(args.plan.read_text())
            wf = Workflow.create(args.workflow, args.runtime, plan['scope'], plan['affected_modules'],
                                 plan.get('operation', 'upgrade'), plan.get('change_type', 'content'), args.mode, args.budget, args.authorization, plan.get('generation', {}).get('deadline'))
            wf.note('initial_inspection', plan)
        else:
            wf = Workflow(args.workflow)
            if args.command == 'import-calls': wf.import_calls(args.source)
            elif args.command == 'repair': wf.repair()
            elif args.command == 'stop': wf.stop()
            elif args.command == 'authorize-more': wf.authorize_more(args.calls, args.authorization, args.deadline)
            elif args.command == 'checkpoint':
                record = json.loads(args.record.read_text()); wf.checkpoint(record['remaining_items'], record.get('source_processing'))
            elif args.command == 'reserve':
                call_id, saved = wf.reserve(args.item, args.role, json.loads(args.request.read_text()), args.candidate, args.retry)
                print(encoded({'call_id': call_id, 'saved_response': saved})); return
            elif args.command == 'finish': wf.finish(args.call_id, json.loads(args.response.read_text()) if args.response else None, args.error)
        print(json.dumps(wf.status(), indent=2, ensure_ascii=False))
    except (ValueError, OSError, KeyError, sqlite3.Error) as exc:
        ap.error(str(exc))


if __name__ == '__main__':
    main()
