"""Mechanical revision-2 boundaries; semantic preservation requires source review."""
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

STRUCTURE_REVISION = 2
SCOPE = 'transworld-identity/scope.md'
ASSESSMENT = {'transworld-identity', 'fidelity-ledger'}


def local_targets(text):
    targets = set(re.findall(r'\[[^\]]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)', text))
    targets.update(re.findall(r'^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)', text, re.M))
    targets.update(re.findall(r'`([^`\s]+)`', text))
    targets.update(re.findall(r'(?<![\w/])(?:references|transworld-identity|fidelity-ledger)/[\w./%-]+', text))
    result = set()
    for target in targets:
        parsed = urlsplit(target.strip('<>'))
        if not parsed.scheme and not parsed.netloc and parsed.path and ('/' in parsed.path or parsed.path.endswith('.md')):
            result.add(unquote(parsed.path).rstrip('.'))
    return result


def inside(root, relative):
    root = Path(root).resolve()
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or not (root / path).resolve().is_relative_to(root):
        raise ValueError('path escapes repository: ' + str(relative))
    return root / path


def boundary_issues(root):
    root = Path(root).resolve()
    issues = []
    files = [root / 'SKILL.md'] + list((root / 'references').rglob('*'))
    for path in files:
        if not path.is_file():
            continue
        if not path.resolve().is_relative_to(root) or ASSESSMENT.intersection(path.resolve().parts):
            issues.append('runtime symlink exposes assessment or external content: ' + str(path.relative_to(root)))
            continue
        if path.suffix == '.md':
            text = path.read_text()
            if re.search(r'transworld-identity/|fidelity-ledger/', text):
                issues.append('hidden assessment route in runtime: ' + str(path.relative_to(root)))
            for target in local_targets(text):
                dest = (path.parent / target).resolve()
                if ASSESSMENT.intersection(dest.parts) or not dest.is_relative_to(root):
                    issues.append('runtime link escapes runtime: ' + target)
    # Host instructions may link assessment for maintenance or an explicit inspection.
    # Inspect linked host instructions too; a benign-looking symlink is still a route.
    pending = [root / name for name in ('AGENTS.md', 'CLAUDE.md')]
    seen = set()
    while pending:
        path = pending.pop()
        if not path.is_file() or path.resolve() in seen:
            continue
        seen.add(path.resolve())
        if not path.resolve().is_relative_to(root) or ASSESSMENT.intersection(path.resolve().parts):
            issues.append('automatic host file exposes assessment or external content: ' + path.name)
            continue
        maintenance = False
        for block in re.split(r'\n\s*\n', path.read_text()):
            if block.startswith('#'):
                maintenance = bool(re.search(r'maintenan|explicit.*inspect', block.splitlines()[0], re.I))
            targets = local_targets(block)
            targets.update(re.findall(r'(?<![\w-])(?:transworld-identity|fidelity-ledger)(?![\w/-])', block))
            qualified = maintenance or bool(re.search(r'(?:for|during) maintenance|explicit(?:ly)? (?:request|inspect)|maintenance.only', block, re.I))
            automatic = bool(re.search(r'always|every (?:answer|conversation)|before (?:answering|every)|automatically', block, re.I))
            for target in targets:
                dest = (path.parent / target).resolve()
                hidden = bool(ASSESSMENT.intersection(dest.parts))
                if hidden and (not qualified or automatic):
                    issues.append('automatic host assessment route: ' + target)
                elif not hidden and dest.suffix == '.md' and dest.is_file() and dest.name != 'SKILL.md' and 'references' not in dest.parts:
                    pending.append(dest)
    return issues


def structure_issues(root):
    root = Path(root).resolve()
    issues = boundary_issues(root)
    scope = root / SCOPE
    if (root / 'transworld-identity').is_symlink() or not scope.is_file() or scope.is_symlink() or not scope.resolve().is_relative_to(root) or not scope.read_text().strip():
        issues.append('need reconstruction account at ' + SCOPE + '; source review checks its responsibilities')
    if not (root / 'SKILL.md').is_file():
        issues.append('need canonical root SKILL.md')
    for name in ('README.md', 'AGENTS.md', 'CLAUDE.md'):
        path = root / name
        if path.is_file():
            for target in local_targets(path.read_text()):
                if not (path.parent / target).exists():
                    issues.append(name + ': missing local link ' + target)
    return issues
