#!/usr/bin/env python3
"""Create a NEW GitHub repository from this checkout with gh. Dry-run and private by default."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def command(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    process = subprocess.run(args, cwd=ROOT, text=True, encoding='utf-8', capture_output=True)
    if check and process.returncode:
        raise RuntimeError(f'{args[0]} {args[1]} failed:\n{process.stderr.strip()}')
    return process


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--name', default='consciousness-as-computation')
    parser.add_argument('--visibility', choices=['private', 'public'], default='private')
    parser.add_argument('--execute', action='store_true', help='実際にリポジトリを作成してpushする。省略時は計画だけ表示する。')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*', args.owner) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', args.name):
        parser.error('owner/nameの形式が不正である。')
    target = f'{args.owner}/{args.name}'
    print(f'対象: {target}\n公開範囲: {args.visibility}\n原本: {ROOT}\n生成物 _site/ は除外\n既存リポジトリの変更・force push・Pages設定の変更はしない。')
    if not args.execute:
        print('\nDRY RUN: 変更していない。実行する場合のみ --execute を付ける。')
        return 0
    try:
        for executable in ['git', 'gh']:
            if not shutil.which(executable):
                raise RuntimeError(f'{executable} が見つからない。guides/PUBLISHING.md を参照。')
        if not (ROOT / '.git').exists():
            raise RuntimeError('このディレクトリはGitリポジトリではない。git init と初期コミットを先に行うこと。')
        if command(['git', 'status', '--porcelain'], check=False).stdout.strip():
            raise RuntimeError('未コミットの変更がある。コミットしてから実行すること。')
        if command(['git', 'remote'], check=False).stdout.strip():
            raise RuntimeError('既にリモートが設定されている。通常のGit操作で管理すること。')
        command(['gh', 'auth', 'status'])
        lookup = command(['gh', 'api', f'repos/{target}'], check=False)
        if lookup.returncode == 0:
            raise RuntimeError('同名の既存リポジトリがあるため停止した。変更しない。')
        check = command([sys.executable, 'scripts/validate.py'])
        print(check.stdout)
        branch = command(['git', 'branch', '--show-current']).stdout.strip() or 'main'
        command(['gh', 'repo', 'create', target, f'--{args.visibility}', '--source', str(ROOT), '--remote', 'origin', '--push', '--description', '意識の再定義 — 情報処理から「自分」の正体を考える、全9回'])
        url = command(['gh', 'repo', 'view', target, '--json', 'url', '--jq', '.url']).stdout.strip()
        print(f'作成・push完了（{branch}）: {url}\nPagesはまだ設定していない。guides/PUBLISHING.md の手順で Source を GitHub Actions にする。')
        return 0
    except (RuntimeError, OSError) as exc:
        print(f'停止: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
