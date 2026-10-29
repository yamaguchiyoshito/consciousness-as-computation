#!/usr/bin/env python3
"""Validate manuscripts, local references, footnotes/sources consistency and passive SVG assets."""
from __future__ import annotations
import argparse
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import ROOT, SERIES_FILES, parse_markdown  # noqa: E402

MIN_BODY_CHARS = 1500


@dataclass
class Result:
    chapters: int = 0
    svg_files: int = 0
    local_links: int = 0
    external_links: int = 0
    footnotes: int = 0
    manuscript_characters: int = 0


def walk(node: object):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


def svg_errors(path: Path) -> list[str]:
    errors = []
    try:
        root = ET.fromstring(path.read_text(encoding='utf-8'))
    except (OSError, ET.ParseError, UnicodeError) as exc:
        return [f'{path.name}: SVG parse error: {exc}']
    tag = lambda n: n.tag.rsplit('}', 1)[-1]
    if tag(root) != 'svg':
        errors.append(f'{path.name}: root must be svg')
    if not root.get('viewBox'):
        errors.append(f'{path.name}: missing viewBox')
    if root.get('role') != 'img':
        errors.append(f'{path.name}: missing role=img')
    names = {tag(n) for n in root.iter()}
    if not {'title', 'desc'} <= names:
        errors.append(f'{path.name}: missing title/desc')
    ids = [n.attrib['id'] for n in root.iter() if 'id' in n.attrib]
    if len(ids) != len(set(ids)):
        errors.append(f'{path.name}: duplicate id')
    for label_id in root.get('aria-labelledby', '').split():
        if label_id not in ids:
            errors.append(f'{path.name}: unresolved aria-labelledby')
    for n in root.iter():
        if tag(n).lower() in {'script', 'foreignobject', 'iframe', 'image', 'use', 'style', 'animate', 'set'}:
            errors.append(f'{path.name}: forbidden SVG element {tag(n)}')
        for key, value in n.attrib.items():
            k = key.rsplit('}', 1)[-1].lower()
            if k.startswith('on'):
                errors.append(f'{path.name}: forbidden event handler {k}')
            if k == 'href' and not value.startswith('#'):
                errors.append(f'{path.name}: external href')
            if re.search(r'url\(\s*["\']?(?!#)[^)]', value):
                errors.append(f'{path.name}: external url()')
    return errors


def validate(root: Path = ROOT) -> tuple[Result, list[str]]:
    root = root.resolve()
    result = Result()
    errors: list[str] = []
    try:
        all_series = [json.loads((root / f).read_text(encoding='utf-8')) for f in SERIES_FILES]
        sources_path = root / 'references/sources.json'
        sources = json.loads(sources_path.read_text(encoding='utf-8')) if sources_path.exists() else {}
    except (OSError, ValueError) as exc:
        return result, [str(exc)]
    chapters = []
    for sf, s in zip(SERIES_FILES, all_series):
        cs = s.get('chapters', [])
        count = len(cs)
        if count == 0 or [c.get('number') for c in cs] != list(range(1, count + 1)):
            errors.append(f'{sf}: expected chapters numbered 1..N in order')
        if len({c['path'] for c in cs}) != count or len({c['slug'] for c in cs}) != count:
            errors.append(f'{sf}: chapter paths and slugs must be unique')
        if not (root / s['index']).exists():
            errors.append(f'{sf}: index page {s["index"]} is missing')
        covered = [n for part in s.get('parts', []) for n in range(part['chapters'][0], part['chapters'][1] + 1)]
        if covered != list(range(1, count + 1)):
            errors.append(f'{sf}: parts must cover chapters 1..N exactly once, in order')
        chapters += cs
    md_paths = [root / 'README.md', *sorted((root / 'guides').glob('*.md')), *[p for p in [root / 'CHANGELOG.md'] if p.exists()]]
    for s in all_series:
        md_paths += [root / s['index'], *sorted((root / s['index']).parent.glob('*.md')), *(root / c['path'] for c in s['chapters'])]
    md_paths = list(dict.fromkeys(md_paths))
    asts = {}
    anchors = {}
    for path in md_paths:
        if not path.exists():
            errors.append(f'{path.relative_to(root)}: missing markdown')
            continue
        text = path.read_text(encoding='utf-8')
        name = path.relative_to(root).as_posix()
        if any(t in text for t in ['', '', '', ':::writing', '```svg', '<svg']):
            errors.append(f'{name}: unsupported conversation artifact or inline SVG')
        try:
            ast = parse_markdown(text)
        except (RuntimeError, ValueError) as exc:
            errors.append(f'{name}: {exc}')
            continue
        asts[path.resolve()] = ast
        anchors[path.resolve()] = {n['c'][1][0] for n in walk(ast) if n.get('t') == 'Header'}
        if path.parent.name == 'chapters':
            result.manuscript_characters += len(text)
            result.footnotes += sum(n.get('t') == 'Note' for n in walk(ast))
    for c in chapters:
        path = root / c['path']
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8')
        result.chapters += 1
        if not text.startswith(f'# 第{c["number"]}回　{c["title"]}\n\n## {c["subtitle"]}\n'):
            errors.append(f'{c["path"]}: title or subtitle mismatch with series.json')
        body = text.split('## 参考文献・注記')[0]
        if len(re.sub(r'\s', '', body)) < MIN_BODY_CHARS:
            errors.append(f'{c["path"]}: article is too short for a complete essay')
        if text.count('<!-- NAV:') != 2:
            errors.append(f'{c["path"]}: top/bottom navigation missing')
        for fig in c['figures']:
            if fig.split('/')[-1] not in text:
                errors.append(f'{c["path"]}: assigned figure {fig} is not referenced')
        captions = re.findall(r'^\*図(\d+)-(\d+)：.+\*$', text, re.M)
        if [(int(a), int(b)) for a, b in captions] != [(c['number'], i) for i in range(1, len(c['figures']) + 1)]:
            errors.append(f'{c["path"]}: figure captions must be 図{c["number"]}-1 .. 図{c["number"]}-{len(c["figures"])} in order')
        if len(re.findall(r'^!\[[^\]]*\]\([^)]*assets/illustrations/', text, re.M)) != len(c['figures']):
            errors.append(f'{c["path"]}: number of figure references differs from series.json')
        references = set(re.findall(r'^\[\^([^\]]+)\]:', text, re.M))
        uses = set(re.findall(r'\[\^([^\]]+)\](?!:)', text))
        if references != set(c['sources']):
            errors.append(f'{c["path"]}: source list mismatch')
        if references != uses:
            errors.append(f'{c["path"]}: unused or undefined footnote')
        if not references <= set(sources):
            errors.append(f'{c["path"]}: unknown source identifier')
        if bool(c['sources']) != ('## 参考文献・注記' in text):
            errors.append(f'{c["path"]}: references section must exist exactly when sources are listed')
    for path, ast in asts.items():
        for n in walk(ast):
            if n.get('t') not in {'Link', 'Image'}:
                continue
            url = n['c'][-1][0]
            parsed = urlsplit(url)
            if parsed.scheme:
                result.external_links += 1
                if parsed.scheme not in {'https', 'mailto'}:
                    errors.append(f'{path.name}: unsupported URL scheme {parsed.scheme}')
                if parsed.scheme == 'https' and not parsed.netloc:
                    errors.append(f'{path.name}: invalid HTTPS URL')
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            result.local_links += 1
            if not target.is_relative_to(root):
                errors.append(f'{path.name}: path escapes repository: {url}')
                continue
            if not target.exists():
                errors.append(f'{path.name}: broken local link: {url}')
                continue
            if n.get('t') == 'Image' and not n['c'][1]:
                errors.append(f'{path.name}: missing image alt text')
            if parsed.fragment and target.suffix == '.md' and unquote(parsed.fragment) not in anchors.get(target, set()):
                errors.append(f'{path.name}: unknown anchor: {url}')
    for sid, s in sources.items():
        if urlsplit(s.get('url', 'https://x')).scheme != 'https':
            errors.append(f'sources.json: {sid}: url must be https')
    for svg in sorted((root / 'assets').rglob('*.svg')):
        result.svg_files += 1
        errors += svg_errors(svg)
    expected_svgs = 1 + sum(len(c['figures']) for c in chapters)
    if result.svg_files != expected_svgs:
        errors.append(f'expected exactly {expected_svgs} SVG illustrations (cover + chapter figures listed in series.json)')
    for c in chapters:
        for fig in c['figures']:
            if not (root / fig).exists():
                errors.append(f'missing figure: {fig}')
    for p in root.rglob('*'):
        if '_site' in p.parts or '.git' in p.parts:
            continue
        if p.suffix.lower() in {'.ttf', '.otf', '.woff', '.woff2'}:
            errors.append(f'font files must not be bundled: {p.name}')
    return result, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    parser.parse_args()
    result, errors = validate()
    report = {**asdict(result), 'errors': errors, 'external_url_reachability': 'not checked', 'editorial_correctness': 'requires editorial review'}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
