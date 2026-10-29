#!/usr/bin/env python3
"""Generate every SVG illustration (cover + per-chapter figures) deterministically. Stdlib only.

各図は 1200px 幅、紙色の背景、見出し行（連載コード・回番号・図番号）、題と副題、本文、脚注の順で構成する。
色だけに意味を依存させず、ラベルでも区別する。フォントは閲覧環境のものを使い、同梱しない。

各回の図は CHAPTERS に本文での登場順に登録する。枝番（a, b, c …）とファイル名はその順序から決まる。
`python scripts/draw_figures.py --list` で series.json の figures に入れる一覧を出力する。
"""
from __future__ import annotations
from html import escape
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'illustrations'
BG, INK, MUTED, LINE = '#f7f5ef', '#232a33', '#5d6873', '#d8d4c8'
TEAL, TERRA, INDIGO, SOFT, PALE = '#2b7a8c', '#d0693a', '#5a4fcf', '#ece9e0', '#dfe9eb'
FONT = 'system-ui, -apple-system, "Hiragino Kaku Gothic ProN", "Noto Sans CJK JP", Meiryo, sans-serif'
CODE = 'CONSCIOUSNESS'


class Figure:
    def __init__(self, number: int, title: str, subtitle: str, height: int = 640, part: str = ''):
        self.h = height
        self.n = number
        self.part = part
        self.title = title
        self.subtitle = subtitle
        self.gradients = 0
        self.defs: list[str] = [
            f'<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="{MUTED}" stroke-width="1.4"/></marker>',
            f'<marker id="arrow-teal" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="{TEAL}" stroke-width="1.6"/></marker>',
            f'<marker id="arrow-terra" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="{TERRA}" stroke-width="1.6"/></marker>',
            f'<marker id="arrow-indigo" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="{INDIGO}" stroke-width="1.6"/></marker>',
            f'<marker id="arrow-ink" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="{INK}" stroke-width="1.6"/></marker>',
        ]
        self.body: list[str] = []
        shown = str(ord(part) - 96) if part.isalpha() and len(part) == 1 else part
        label = CODE if number == 0 else f'{CODE}     {number:02d}' + (f'     図{number}-{shown}' if part else '')
        self.text(50, 52, label, 18, TEAL, weight=700)
        self.text(50, 103, title, 34, weight=700)
        self.text(50, 141, subtitle, 21, MUTED)
        self.line(50, 166, 1150, 166, color=LINE, width=1)

    # --- primitives -------------------------------------------------------
    def text(self, x, y, s, size=24, color=INK, anchor='start', weight=400):
        self.body.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(s))}</text>')

    def lines(self, x, y, items, size=19, color=INK, anchor='start', gap=None, weight=400):
        gap = gap or size * 1.55
        for i, s in enumerate(items):
            self.text(x, y + i * gap, s, size, color, anchor, weight)

    @staticmethod
    def _marker(color):
        return {TEAL: 'arrow-teal', TERRA: 'arrow-terra', INDIGO: 'arrow-indigo', INK: 'arrow-ink'}.get(color, 'arrow')

    def line(self, x1, y1, x2, y2, color=MUTED, width=2, arrow=False, dash=False, both=False):
        extra = (f' marker-end="url(#{self._marker(color)})"' if arrow or both else '') + (f' marker-start="url(#{self._marker(color)})"' if both else '') + (' stroke-dasharray="8 7"' if dash else '')
        self.body.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"{extra}/>')

    def path(self, d, color=MUTED, width=2, arrow=False, dash=False, fill='none', both=False):
        extra = (f' marker-end="url(#{self._marker(color)})"' if arrow or both else '') + (f' marker-start="url(#{self._marker(color)})"' if both else '') + (' stroke-dasharray="8 7"' if dash else '')
        self.body.append(f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{width}"{extra}/>')

    def curve(self, x1, y1, cx, cy, x2, y2, color=MUTED, width=2, arrow=True, dash=False):
        self.path(f'M{x1:.1f},{y1:.1f} Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}', color, width, arrow, dash)

    def rect(self, x, y, w, h, fill='#ffffff', stroke=LINE, width=2, rx=14, dash=False, opacity=1.0):
        extra = (' stroke-dasharray="8 7"' if dash else '') + (f' opacity="{opacity}"' if opacity < 1 else '')
        self.body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"{extra}/>')

    def box(self, x, y, w, h, title, subtitle='', color=TEAL, size=22, dash=False, fill='#ffffff', sub_size=17):
        self.rect(x, y, w, h, fill=fill, stroke=color, width=2, dash=dash)
        if subtitle:
            self.text(x + w / 2, y + h / 2 - 5, title, size, color, anchor='middle', weight=700)
            self.text(x + w / 2, y + h / 2 + sub_size + 7, subtitle, sub_size, MUTED, anchor='middle')
        else:
            self.text(x + w / 2, y + h / 2 + size * 0.36, title, size, color, anchor='middle', weight=700)

    def pill(self, x, y, w, h, label, color=TEAL, size=18, text_color='#ffffff'):
        self.rect(x, y, w, h, fill=color, stroke=color, rx=h / 2)
        self.text(x + w / 2, y + h / 2 + size * 0.36, label, size, text_color, anchor='middle', weight=700)

    def tag(self, x, y, w, h, label, color=TEAL, size=17):
        """Outlined pill with colored text."""
        self.rect(x, y, w, h, fill='#ffffff', stroke=color, rx=h / 2)
        self.text(x + w / 2, y + h / 2 + size * 0.36, label, size, color, anchor='middle', weight=700)

    def circ(self, x, y, r=10, color=TEAL, fill=True, dash=False, width=2):
        if fill:
            self.body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}"/>')
        else:
            extra = ' stroke-dasharray="7 6"' if dash else ''
            self.body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="none" stroke="{color}" stroke-width="{width}"{extra}/>')

    def node(self, x, y, r, label, color=TEAL, size=17):
        """White disc with a colored ring and a one- or two-line label."""
        self.circ(x, y, r, '#ffffff')
        self.circ(x, y, r, color, fill=False, width=2.5)
        parts = label.split('\n')
        if len(parts) == 1:
            self.text(x, y + size * 0.36, label, size, color, anchor='middle', weight=700)
        else:
            self.text(x, y - 2, parts[0], size, color, anchor='middle', weight=700)
            self.text(x, y + size + 2, parts[1], size, color, anchor='middle', weight=700)

    def panel(self, x, y, w, h, label='', color='#c9c4b6'):
        self.body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="none" stroke="{color}" stroke-width="2" stroke-dasharray="7 7"/>')
        if label:
            self.text(x + w / 2, y + 34, label, 22, INK, anchor='middle', weight=700)

    def blob(self, cx, cy, r, color, opacity=0.5):
        self.gradients += 1
        gid = f'g{self.n:02d}{self.part}-{self.gradients}'
        self.defs.append(f'<radialGradient id="{gid}"><stop offset="0" stop-color="{color}" stop-opacity="{opacity}"/><stop offset="0.55" stop-color="{color}" stop-opacity="{opacity*0.45:.2f}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>')
        self.body.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="url(#{gid})"/>')

    def hgradient(self, x, y, w, h, color, start=0.95, end=0.05, rx=10):
        self.gradients += 1
        gid = f'g{self.n:02d}{self.part}-{self.gradients}'
        self.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{color}" stop-opacity="{start}"/><stop offset="1" stop-color="{color}" stop-opacity="{end}"/></linearGradient>')
        self.body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#{gid})"/>')

    def cross(self, x, y, size=12, color=TERRA, width=3):
        self.line(x - size, y - size, x + size, y + size, color, width)
        self.line(x - size, y + size, x + size, y - size, color, width)

    def check(self, x, y, size=26, color=TEAL):
        self.rect(x, y, size, size, fill='#ffffff', stroke=color, rx=6)
        self.path(f'M{x+6:.1f},{y+size/2:.1f} L{x+size*0.42:.1f},{y+size-7:.1f} L{x+size-5:.1f},{y+6:.1f}', color, 3)

    def bar(self, x, y_base, w, h, color, opacity=0.9):
        self.rect(x, y_base - h, w, h, fill=color, stroke=color, rx=4, opacity=opacity)

    def footer(self, s):
        if s:
            self.text(50, self.h - 28, s, 18, MUTED)

    def save(self, slug: str) -> str:
        OUT.mkdir(parents=True, exist_ok=True)
        name = f'{self.n:02d}-{self.part}-{slug}.svg' if self.part else f'{self.n:02d}-{slug}.svg'
        head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{self.h}" viewBox="0 0 1200 {self.h}" role="img" aria-labelledby="title desc">',
                f'<title id="title">{escape(self.title)}</title>', f'<desc id="desc">{escape(self.subtitle)}</desc>',
                '<defs>' + ''.join(self.defs) + '</defs>', f'<rect width="1200" height="{self.h}" rx="20" fill="{BG}"/>',
                f'<g font-family=\'{FONT}\'>']
        (OUT / name).write_text('\n'.join(head + self.body + ['</g>', '</svg>']) + '\n', encoding='utf-8')
        return name


def polar(cx, cy, r, deg, ry=None):
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + (ry if ry is not None else r) * math.sin(a)


def ring_arrows(f, pos: list[tuple[float, float]], trim: float, color=MUTED, width=2.2, cx=None, cy=None, bow=0):
    """Arrows between consecutive positions (closing the ring), trimmed by `trim` px at both ends."""
    for i in range(len(pos)):
        (x1, y1), (x2, y2) = pos[i], pos[(i + 1) % len(pos)]
        dx, dy = x2 - x1, y2 - y1
        d = math.hypot(dx, dy)
        ux, uy = dx / d, dy / d
        if bow and cx is not None:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            nd = math.hypot(mx - cx, my - cy) or 1
            f.curve(x1 + ux * trim, y1 + uy * trim, mx + (mx - cx) / nd * bow, my + (my - cy) / nd * bow, x2 - ux * trim, y2 - uy * trim, color, width)
        else:
            f.line(x1 + ux * trim, y1 + uy * trim, x2 - ux * trim, y2 - uy * trim, color, width, arrow=True)


# ---------------------------------------------------------------------------
# 表紙
# ---------------------------------------------------------------------------

def cover():
    f = Figure(0, '意識の再定義', '情報処理から「自分」の正体を考える', 680)
    cx, cy = 780, 410
    f.blob(cx, cy, 205, TEAL, 0.28)
    items = [('身体', 0, 0, 62, TEAL), ('記憶', -135, 128, 42, INDIGO), ('価値観', 135, 128, 44, INDIGO), ('感情', -45, 120, 38, INDIGO),
             ('道具', -165, 178, 36, TERRA), ('アバター', 45, 170, 42, TERRA), ('作品', 100, 182, 38, TERRA), ('所有物', -100, 190, 36, TERRA)]
    for label, deg, r, rr, color in items:
        x, y = polar(cx, cy, r, deg - 90)
        f.blob(x, y, rr * 1.6, color, 0.5)
        f.circ(x, y, rr, '#ffffff')
        f.circ(x, y, rr, color, fill=False, width=2)
        f.text(x, y + 7, label, 19 if len(label) <= 3 else 17, INK, anchor='middle', weight=700)
    f.circ(cx, cy, 228, TEAL, fill=False, dash=True, width=2.5)
    f.text(cx, cy - 188, '「自分」＝情報処理が引く境界', 17, TEAL, anchor='middle', weight=700)
    f.text(1120, 630, '外界', 18, MUTED, anchor='end')
    for i in range(14):
        x, y = polar(cx, cy, 262 + (i * 37) % 50, 20 + i * 24)
        if x < 1150 and 195 < y < 640:
            f.circ(x, y, 3, LINE)
    f.lines(50, 240, ['意識は「自分」を発見するのではなく、', '構築しているのかもしれない。'], 24, INK, weight=700, gap=38)
    f.lines(50, 330, ['現実とバーチャルの境界から出発し、', '目的関数、予測処理、情報統合、', '現象的意識、分人、物語を経て、', '「自分」を計算可能な構造として', '捉え直す。'], 19, MUTED, gap=32)
    f.footer('全9回　境界を問う ／ 自己のモデル ／ 体験と複数の自己 ／ 計算機で確かめる')
    return f.save('cover')


# ---------------------------------------------------------------------------
# 第1回
# ---------------------------------------------------------------------------

def perception_boundary(part):
    f = Figure(1, '現実とバーチャルは、知覚の手前で合流する', '脳が受け取るのは感覚情報だけである', 600, part)
    f.box(70, 225, 270, 90, '現実の光景', '撮影された人物や風景', TEAL)
    f.box(70, 395, 270, 90, '生成された映像', 'CG・生成AI', TERRA)
    f.line(400, 205, 400, 520, LINE, 2, dash=True)
    f.text(400, 548, '物理的な境界', 17, MUTED, anchor='middle')
    f.box(480, 310, 240, 90, '感覚情報', '光・音・圧力 → 神経信号', INK)
    f.curve(340, 270, 420, 290, 480, 345, TEAL, 2.5)
    f.curve(340, 440, 420, 420, 480, 375, TERRA, 2.5)
    f.line(720, 355, 790, 355, MUTED, 2, arrow=True)
    f.box(790, 310, 160, 90, '認識', '', INK)
    f.line(950, 355, 1010, 355, MUTED, 2, arrow=True)
    f.box(1010, 310, 140, 90, '体験', '', INK)
    f.text(815, 470, '源が異なっても、感覚情報が似ていれば体験は似る', 18, MUTED, anchor='middle')
    f.line(560, 440, 1070, 440, LINE, 1)
    f.footer('区別できなくなったのは物理的な実体ではなく、知覚による判別である。')
    return f.save('perception-boundary')


def shared_experience(part):
    f = Figure(1, '物語を支える共通体験の基盤が広がる', '物理的な世界の経験に、デジタル空間の経験が加わる', 650, part)
    f.panel(60, 205, 500, 260, '物理的な世界の共通体験')
    f.panel(640, 205, 500, 260, 'デジタル空間の共通体験')
    for i, (label, sub) in enumerate([('学校', '教室・部活・試験・文化祭'), ('職場', '人間関係・仕事上の葛藤'), ('恋愛', '対人関係の経験')]):
        f.box(90, 255 + i * 66, 440, 54, label, sub, TEAL, 18, sub_size=14)
    for i, (label, sub) in enumerate([('ゲーム世界', 'レベル・スキル・クエスト・アイテム'), ('SNS', 'アカウント・フォロワー・配信'), ('アバター', 'VTuber・仮想の姿での関係')]):
        f.box(670, 255 + i * 66, 440, 54, label, sub, TERRA, 18, sub_size=14)
    f.curve(310, 465, 400, 530, 500, 530, TEAL, 2.5)
    f.curve(890, 465, 800, 530, 700, 530, TERRA, 2.5)
    f.box(480, 500, 240, 60, '物語を理解する共通言語', '', INK, 18)
    f.text(600, 580, '置き換わる、あるいは拡張される', 15, MUTED, anchor='middle')
    f.footer('学校や職場が共通体験でなくなったわけではない。基盤が物理的な世界だけに限定されなくなった。')
    return f.save('shared-experience')


def self_score_gradient(part):
    f = Figure(1, '自己認識の強さには濃淡がある', '皮膚の位置と「自分」の境界は一致しない', 580, part)
    f.hgradient(80, 260, 1040, 64, TEAL, 0.95, 0.04)
    f.text(80, 240, '強い', 17, MUTED)
    f.text(1120, 240, '弱い', 17, MUTED, anchor='end')
    f.text(600, 240, '身体の内側', 18, INK, anchor='middle', weight=700)
    for x, label in [(140, '脳・心臓'), (340, '腕・脚'), (640, '髪・爪'), (960, '排泄物')]:
        f.circ(x, 292, 9, '#ffffff')
        f.circ(x, 292, 9, INK, fill=False, width=2)
        f.text(x, 350, label, 19, INK, anchor='middle', weight=700)
    f.text(80, 420, '皮膚の外側', 18, INK, weight=700)
    for x, w, label in [(230, 150, '自分の作品'), (400, 180, '愛着のある所有物'), (600, 230, 'アバター・キャラクター'), (850, 120, '熟練した道具')]:
        f.tag(x, 440, w, 36, label, TERRA, 16)
        f.line(x + w / 2, 440, x + w / 2, 330, TERRA, 1.5, arrow=True, dash=True)
    f.text(1120, 462, '位置は強さの目安', 15, MUTED, anchor='end')
    f.footer('「自分らしさスコア」は説明のための仮説であり、脳内に単一の数値があるという主張ではない。')
    return f.save('self-score-gradient')


def common_structure(part):
    f = Figure(1, '四つの現象に共通する構造', '物理的な境界ではなく、内部表象の一部が「自分」として認識される', 640, part)
    cases = [('現実と仮想の映像', '感覚情報が似ていれば区別できない'), ('仮想の対象への感情', '対象が存在しなくても感情は現実'),
             ('身体部位の自己認識の濃淡', '生物学的な所属と一致しない'), ('アバター・作品への投影', '身体の外側が自分の一部になる')]
    for i, (t, s) in enumerate(cases):
        y = 215 + i * 90
        f.box(70, y, 330, 70, t, s, MUTED, 17, sub_size=13)
        f.curve(400, y + 35, 470, y + 35, 520, 400, MUTED, 2)
    f.box(520, 330, 300, 140, '内部表象', '感覚情報・記憶・経験・予測から構築', TEAL, 24, sub_size=15)
    f.line(820, 400, 890, 400, TEAL, 2.5, arrow=True)
    f.box(890, 345, 250, 110, '「自分」', '表象の一部を自分として認識', INDIGO, 24, sub_size=14)
    f.text(1015, 495, '仮説：自分とは情報処理が設定する境界', 14, MUTED, anchor='middle')
    f.footer('自己の境界が構築されることと、主観的体験が情報処理だけで説明できることは同じではない。')
    return f.save('common-structure')


# ---------------------------------------------------------------------------
# 第2回
# ---------------------------------------------------------------------------

def three_layers(part):
    f = Figure(2, '人間を三層で捉える', '意識は構造そのものではなく、構造の上で動く処理である', 600, part)
    f.text(330, 215, '人間', 20, INK, anchor='middle', weight=700)
    f.text(870, 215, '計算機', 20, INK, anchor='middle', weight=700)
    rows = [(235, '意識', '自己や世界を認識するプロセス', '実行されるプロセス', TEAL),
            (345, '情報処理システム', '感覚・記憶・予測・判断・行動制御', 'ソフトウェア', INDIGO),
            (455, '生物学的基盤', '脳・神経系・感覚器官・身体', 'ハードウェア', MUTED)]
    for y, t, s, r, color in rows:
        f.box(120, y, 420, 88, t, s, color)
        f.box(660, y, 420, 88, r, '', color)
        f.line(560, y + 44, 640, y + 44, LINE, 2, dash=True, both=True)
    f.text(600, 215, '対応', 16, MUTED, anchor='middle')
    f.footer('対応は説明のためのモデルであり、脳と計算機が同じ仕組みで動くという主張ではない。')
    return f.save('three-layers')


def consciousness_and_self(part):
    f = Figure(2, '意識は認識する働き、「自分」は認識される対象', '意識は自己表象を構築し、認識し、更新する', 620, part)
    f.box(80, 250, 330, 150, '意識', '認識する働き', TEAL, 28, sub_size=19)
    f.rect(700, 225, 430, 230, fill='#ffffff', stroke=INDIGO)
    f.text(915, 262, '「自分」＝自己表象', 24, INDIGO, anchor='middle', weight=700)
    for i, label in enumerate(['身体', '感情', '能力', '記憶', '価値観']):
        x = 735 + (i % 3) * 125 if i < 3 else 800 + (i - 3) * 125
        y = 290 if i < 3 else 360
        f.tag(x, y, 105, 40, label, INDIGO, 18)
    f.text(915, 435, '統合された認識上の対象', 16, MUTED, anchor='middle')
    f.curve(410, 300, 555, 250, 700, 290, TEAL, 3)
    f.text(555, 240, '構築する', 18, TEAL, anchor='middle', weight=700)
    f.curve(700, 400, 555, 450, 410, 360, INDIGO, 3)
    f.text(555, 480, '認識する ／ 更新する', 18, INDIGO, anchor='middle', weight=700)
    f.text(245, 500, '感覚情報・記憶・予測', 17, MUTED, anchor='middle')
    f.line(245, 480, 245, 408, MUTED, 2, arrow=True)
    f.text(915, 520, '例：鏡の中の姿を「自分の姿」として認識する', 17, MUTED, anchor='middle')
    f.footer('意識のすべてが自己認識に還元できるわけではない。自己意識の成立に焦点を当てた機能的な仮説である。')
    return f.save('consciousness-and-self')


def conscious_unconscious(part):
    f = Figure(2, '意識的処理と無意識的処理', '膨大な処理の一部だけが意識的な認識や判断に関与する', 680, part)
    f.pill(60, 400, 150, 50, '感覚器官', INK, 19)
    f.text(135, 475, '外界の情報を受信', 14, MUTED, anchor='middle')
    f.panel(260, 200, 640, 180, '無意識的処理')
    f.panel(260, 440, 640, 180, '意識的処理')
    for i, label in enumerate(['信号の変換', '特徴の抽出', '習慣的な行動制御', '自動的な予測']):
        f.box(285 + i * 155, 255, 140, 56, label, '', TEAL, 15)
    for i, label in enumerate(['注意対象の選択', '情報の評価', '判断の検討', '自己表象との関連づけ']):
        f.box(285 + i * 155, 495, 140, 56, label, '', INDIGO, 14)
    f.text(580, 345, '歩行や熟練した読書：注意を向けずに進む', 14, MUTED, anchor='middle')
    f.text(580, 585, '理解できない文章：読み返し、意味を確認し、文脈を考える', 14, MUTED, anchor='middle')
    f.curve(210, 415, 235, 300, 260, 290, TEAL, 2.5)
    f.curve(210, 440, 235, 540, 260, 530, INDIGO, 2.5)
    for x in (430, 580, 730):
        f.line(x, 380, x, 440, MUTED, 1.8, both=True, dash=True)
    f.text(880, 415, '相互作用', 14, MUTED, anchor='end')
    f.box(960, 380, 180, 90, '行動・予測', '処理結果の反映', INK, 19, sub_size=13)
    f.curve(900, 290, 940, 300, 960, 400, TEAL, 2.5)
    f.curve(900, 530, 940, 520, 960, 450, INDIGO, 2.5)
    f.footer('意識がすべての情報処理を実行しているのではない。どの情報が意識的処理の対象になるかは第4回で扱う。')
    return f.save('conscious-unconscious')


def substrate_independence(part):
    f = Figure(2, '意識は特定の物理的な基盤に依存するのか', '同じ手続きを別の基盤で動かせるとき、二つの問いが分かれる', 640, part)
    for x, title, sub in [(90, '脳', '生物学的な計算基盤'), (710, '計算機', '別の計算基盤')]:
        f.rect(x, 215, 400, 150, fill='#ffffff', stroke=INK)
        f.text(x + 200, 248, title, 22, INK, anchor='middle', weight=700)
        f.text(x + 200, 270, sub, 13, MUTED, anchor='middle')
        f.rect(x + 40, 290, 320, 50, fill=PALE, stroke=TEAL, rx=10)
        f.text(x + 200, 321, '自己認識の情報処理', 17, TEAL, anchor='middle', weight=700)
    f.line(490, 315, 710, 315, LINE, 2, dash=True, both=True)
    f.text(600, 305, '同じ手続き？', 15, MUTED, anchor='middle')
    f.box(90, 400, 480, 120, '問い1：機能を再現できるか', '状態の監視・記憶・行動選択を計算機で実装する', TEAL, 20, sub_size=14)
    f.text(330, 545, '→ 計算機実験で検証できる（第9回）', 15, TEAL, anchor='middle')
    f.box(630, 400, 480, 120, '問い2：主観的体験が生じるか', '「自分が存在している」と感じているか', TERRA, 20, sub_size=14)
    f.text(870, 545, '→ 別の問題として残る（第6回）', 15, TERRA, anchor='middle')
    f.footer('人間の脳は意識を実現する一つの計算基盤である、という仮説。機能の再現は現象的意識の証明にならない。')
    return f.save('substrate-independence')


def criteria_question(part):
    f = Figure(2, '何を基準に、ある対象を「自分」とするのか', '候補となる評価基準と、次回へ持ち越す問い', 600, part)
    for i, (t, s) in enumerate([('生命の維持に重要か', '脳・心臓・身体'), ('自分の行動で制御できるか', '腕・道具・アバター'), ('社会的な評価に関わるか', '作品・アカウント・地位')]):
        y = 215 + i * 95
        f.box(70, y, 360, 72, t, s, TEAL, 18, sub_size=14)
        f.curve(430, y + 36, 500, y + 36, 560, 358, TEAL, 2.2)
    f.box(560, 310, 220, 96, '「自分」として', '認識される対象', INK, 20, sub_size=16)
    f.text(250, 520, '近くにある、長く接している、だけでは決まらない', 14, MUTED, anchor='middle')
    f.rect(830, 240, 310, 240, fill='#ffffff', stroke=TERRA, rx=14, dash=True)
    f.text(985, 280, '持ち越す問い', 18, TERRA, anchor='middle', weight=700)
    f.lines(860, 322, ['基準は独立しているのか。', 'それとも相互に作用して、', '「自分」という共通の対象を', '形成しているのか。'], 16, INK, gap=30)
    f.text(985, 455, '→ 第3回：目的関数', 15, TERRA, anchor='middle', weight=700)
    f.line(780, 358, 830, 358, MUTED, 2, arrow=True, dash=True)
    f.footer('ここで挙げた基準は候補であり、網羅ではない。')
    return f.save('criteria-question')


# ---------------------------------------------------------------------------
# 第3回
# ---------------------------------------------------------------------------

def route_objectives(part):
    f = Figure(3, '評価基準が変われば最適な経路が変わる', '同じ三つの経路を、距離・時間・費用で評価する', 620, part)
    sx, sy, gx, gy = 110, 420, 560, 260
    f.circ(sx, sy, 12, INK)
    f.text(sx, sy + 38, '出発', 16, INK, anchor='middle', weight=700)
    f.circ(gx, gy, 12, INK)
    f.text(gx, gy - 24, '目的地', 16, INK, anchor='middle', weight=700)
    f.curve(sx, sy, 330, 215, gx, gy, TEAL, 3, arrow=False)
    f.text(300, 262, 'A：最短距離', 15, TEAL, anchor='middle', weight=700)
    f.path(f'M{sx},{sy} L260,{sy} L400,{gy} L{gx},{gy}', INDIGO, 3)
    f.text(330, 360, 'B：高速道路（最短時間）', 15, INDIGO, anchor='middle', weight=700)
    f.curve(sx, sy, 400, 520, gx, gy, TERRA, 3, arrow=False)
    f.text(330, 500, 'C：一般道（最小費用）', 15, TERRA, anchor='middle', weight=700)
    f.rect(680, 215, 460, 290, fill='#ffffff', stroke=LINE)
    f.text(910, 250, '評価基準ごとの最適解', 18, INK, anchor='middle', weight=700)
    cols = ['A', 'B', 'C']
    for j, c in enumerate(cols):
        f.text(840 + j * 90, 290, c, 16, [TEAL, INDIGO, TERRA][j], anchor='middle', weight=700)
    rows = [('距離を評価', [1, 0, 0]), ('時間を評価', [0, 1, 0]), ('費用を評価', [0, 0, 1])]
    for i, (label, best) in enumerate(rows):
        y = 335 + i * 52
        f.text(715, y + 6, label, 16, INK)
        for j, b in enumerate(best):
            x = 840 + j * 90
            if b:
                f.circ(x, y, 13, [TEAL, INDIGO, TERRA][j])
                f.text(x, y + 5, '◎', 13, '#ffffff', anchor='middle', weight=700)
            else:
                f.circ(x, y, 6, LINE)
    f.text(910, 545, '最適な x* = argmax f(x) は f の選び方で変わる', 14, MUTED, anchor='middle')
    f.footer('評価基準はひとつではない。人間には複数の評価基準が同時に存在する。')
    return f.save('route-objectives')


def go_ai_two_evaluators(part):
    f = Figure(3, '囲碁AIの二つの評価関数と「地」', '共通して重視する対象が、機能的な自己の原型になる', 600, part)
    f.box(70, 225, 300, 92, '局面評価関数', '現在の盤面はどの程度有利か', TEAL)
    f.box(70, 400, 300, 92, '着手評価関数', '次の手で生じる局面を比較する', INDIGO)
    bx, by, cell, n = 500, 235, 26, 9
    size = cell * (n - 1)
    f.rect(bx - 16, by - 16, size + 32, size + 32, fill='#f1e6c8', stroke=LINE, rx=6)
    for i in range(n):
        f.line(bx, by + i * cell, bx + size, by + i * cell, '#8a7f66', 1)
        f.line(bx + i * cell, by, bx + i * cell, by + size, '#8a7f66', 1)
    pts = [(bx + 3 * cell, by + 1 * cell), (bx + 7 * cell, by + 1 * cell), (bx + 8 * cell, by + 4 * cell), (bx + 6 * cell, by + 6 * cell), (bx + 3 * cell, by + 5 * cell), (bx + 2 * cell, by + 3 * cell)]
    f.path('M' + ' L'.join(f'{x},{y}' for x, y in pts) + ' Z', TEAL, 2, fill=TEAL + '55')
    for x, y in pts[:4]:
        f.circ(x, y, 8, INK)
    for x, y in [(bx + 1 * cell, by + 7 * cell), (bx + 5 * cell, by + 8 * cell), (bx + 2 * cell, by + 1 * cell)]:
        f.circ(x, y, 8, '#ffffff')
        f.circ(x, y, 8, INK, fill=False, width=1.5)
    f.text(bx + 5 * cell, by + 4 * cell + 6, '地', 22, TEAL, anchor='middle', weight=700)
    f.curve(370, 270, 440, 290, 560, 320, TEAL, 2.5)
    f.curve(370, 446, 440, 420, 560, 350, INDIGO, 2.5)
    f.text(620, 500, '盤面', 16, MUTED, anchor='middle')
    f.text(1000, 262, '共通して重視する対象', 20, INK, anchor='middle', weight=700)
    f.line(750, 270, 850, 270, MUTED, 2, arrow=True)
    f.line(1000, 285, 1000, 360, MUTED, 2, arrow=True)
    f.box(850, 365, 300, 90, '機能的な自己の原型', '独立した実体を先に置かない', TEAL, 20, dash=True)
    f.footer('実際の囲碁AIが「地」を自分だと認識しているという意味ではない。構造を示すための思考実験である。')
    return f.save('go-ai-two-evaluators')


def weighted_sum(part):
    f = Figure(3, '目的関数には重みがある', '休日の過ごし方を、複数の目的関数が異なる重みで評価する', 720, part)
    options = ['仕事をする', '休息を取る', '家族と過ごす', '新しい技術を学ぶ']
    objectives = [('社会的承認', 0.9, TEAL), ('健康の維持', 0.5, INDIGO), ('愛着・関係', 0.6, TERRA), ('知的好奇心', 0.4, MUTED)]
    vals = [[3, 0, 1, 2], [0, 3, 1, 1], [0, 1, 3, 0], [1, 0, 0, 3]]
    x0, y0, cw, rh = 330, 250, 190, 70
    for j, o in enumerate(options):
        f.text(x0 + j * cw + cw / 2, 225, o, 15, INK, anchor='middle', weight=700)
    for i, (label, w, color) in enumerate(objectives):
        y = y0 + i * rh
        f.text(70, y + 28, label, 16, INK, weight=700)
        f.rect(70, y + 38, 200, 10, fill=SOFT, stroke=SOFT, rx=5)
        f.rect(70, y + 38, 200 * w, 10, fill=color, stroke=color, rx=5)
        f.text(285, y + 48, f'w={w}', 13, MUTED)
        for j in range(4):
            v = vals[i][j]
            x = x0 + j * cw + cw / 2
            for k in range(3):
                f.circ(x - 22 + k * 22, y + 35, 8, color if k < v else LINE)
    f.line(60, y0 + 4 * rh + 10, 1140, y0 + 4 * rh + 10, LINE, 1.5)
    f.text(70, y0 + 4 * rh + 48, '総合評価 U(x) = Σ_i w_i・f_i(x)', 16, INK, weight=700)
    totals = [sum(objectives[i][1] * vals[i][j] for i in range(4)) for j in range(4)]
    best = max(range(4), key=lambda j: totals[j])
    for j, t in enumerate(totals):
        x = x0 + j * cw + cw / 2
        f.rect(x - 60, y0 + 4 * rh + 28, 120, 30, fill=PALE if j == best else '#ffffff', stroke=TEAL if j == best else LINE, rx=8)
        f.text(x, y0 + 4 * rh + 49, f'{t:.1f}', 15, TEAL if j == best else MUTED, anchor='middle', weight=700)
    f.text(600, y0 + 4 * rh + 90, '承認の重みが大きいこの例では仕事が選ばれる。健康の重みが増せば休息へ傾く。', 14, MUTED, anchor='middle')
    f.text(600, y0 + 4 * rh + 112, '倫理的に許されない行動は、重みに関係なく制約条件として選択肢から除外する。', 14, TERRA, anchor='middle')
    f.footer('人間がこの式を計算して行動を決めているという主張ではない。優先順位の変化を扱うための近似である。')
    return f.save('weighted-sum')


def intersection_of_objectives(part):
    f = Figure(3, '「自分」は目的関数の交差点に生まれる', '矢印の太さが重み。向きの異なる目的が同じ対象を評価する', 760, part)
    cx, cy = 600, 462
    f.blob(cx, cy, 150, TEAL, 0.45)
    f.circ(cx, cy, 64, '#ffffff')
    f.circ(cx, cy, 64, TEAL, fill=False, width=2.5)
    f.text(cx, cy + 9, '自分', 26, TEAL, anchor='middle', weight=700)
    objs = [('生存', -90, 6.0, TEAL, '重み：大 ／ 回避を促す'), ('社会的承認', -18, 4.5, INDIGO, '重み：中 ／ 期待に応える'), ('美的感覚', 54, 2.2, INDIGO, '重み：小'),
            ('倫理的整合性', 126, 3.0, TERRA, '重み：小 ／ 信念を守る'), ('知的好奇心', 198, 3.6, TERRA, '重み：中 ／ 挑戦を促す')]
    for label, deg, w, color, note in objs:
        x1, y1 = polar(cx, cy, 205, deg)
        x2, y2 = polar(cx, cy, 82, deg)
        f.line(x1, y1, x2, y2, color, w, arrow=True)
        lx, ly = polar(cx, cy, 240, deg)
        c = math.cos(math.radians(deg))
        anchor = 'middle' if abs(c) < 0.3 else ('start' if c > 0 else 'end')
        f.text(lx, ly + 7, label, 21, INK, anchor=anchor, weight=700)
        f.text(lx, ly + 30, note, 15, MUTED, anchor=anchor)
    f.text(1150, 215, '矢印の先：共通して参照される対象', 14, MUTED, anchor='end')
    f.footer('重みは状況で変わる。矛盾は統一された自己の失敗ではなく、複数の評価基準を持つ自己の通常の働きである。')
    return f.save('intersection-of-objectives')


def posthoc_narrative(part):
    f = Figure(3, '統一された「自分」は事後的に構築される', '複数の動機から生じた行動が、ひとつの物語で一貫した自己像に整理される', 640, part)
    for i, (label, color) in enumerate([('知的好奇心', TEAL), ('社会的承認欲求', INDIGO), ('現状への不満', TERRA)]):
        y = 225 + i * 80
        f.tag(70, y, 200, 44, label, color, 16)
        f.curve(270, y + 22, 320, y + 22, 360, 330, color, 2.2)
    f.text(170, 495, '複数の動機', 14, MUTED, anchor='middle')
    f.box(360, 290, 230, 80, '一つの行動', '安定した仕事を辞め、新しい分野へ', INK, 19, sub_size=13)
    f.line(590, 330, 650, 330, MUTED, 2.2, arrow=True)
    f.box(650, 275, 260, 110, 'ナラティブ', '「自分は昔から', TERRA, 19, sub_size=14)
    f.text(780, 365, '挑戦することが好きだった」', 14, MUTED, anchor='middle')
    f.line(910, 330, 970, 330, MUTED, 2.2, arrow=True)
    f.box(970, 285, 170, 90, '一貫した', '自己像', TERRA, 19, sub_size=17)
    f.rect(360, 430, 780, 90, fill='#ffffff', stroke=LINE, rx=12, dash=True)
    f.text(750, 462, '挑戦しなかった場合も「自分は慎重に判断する人間だから」と説明できる', 15, INK, anchor='middle')
    f.text(750, 490, '同じ人が、異なる行動のそれぞれに一貫した理由を与える', 14, MUTED, anchor='middle')
    f.footer('意図的な自己欺瞞ではない。記憶と物語が行動を結びつけ、時間的に連続した自己像を作る。')
    return f.save('posthoc-narrative')


def three_stages(part):
    f = Figure(3, '目的関数を持つことと、意識を持つことは同じではない', '三つの段階のうち、目的関数仮説が直接扱うのは前の二つ', 640, part)
    steps = [(70, 400, '① 目的関数に基づく行動選択', '囲碁AI・ロボット・最適化アルゴリズムにもある', TEAL),
             (430, 310, '② 共通対象についての自己表象の形成', '複数の目的関数が参照する対象を内部に表象する', TEAL),
             (790, 220, '③ 主観的な体験が伴うこと', 'なぜ「感じる」のか。目的関数モデルでは説明できない', TERRA)]
    for x, y, t, s, color in steps:
        f.box(x, y, 340, 92, t, s, color, 17, sub_size=12, dash=(color == TERRA))
    f.line(410, 446, 430, 446, MUTED, 2, arrow=True)
    f.line(770, 356, 790, 356, MUTED, 2, arrow=True)
    f.line(70, 520, 770, 520, TEAL, 3)
    f.text(420, 548, '本モデルの目的関数仮説が扱う範囲（計算機で検証できる）', 15, TEAL, anchor='middle', weight=700)
    f.line(790, 520, 1130, 520, TERRA, 3, dash=True)
    f.text(960, 548, '第5・6回で検討', 15, TERRA, anchor='middle', weight=700)
    f.footer('複数の評価関数で行動を選ぶプログラムが、自分自身を認識しているとは限らない。')
    return f.save('three-stages')


# ---------------------------------------------------------------------------
# 第4回
# ---------------------------------------------------------------------------

def ambiguous_input(part):
    f = Figure(4, '同じ感覚情報が、文脈によって違うものとして認識される', '認識は感覚情報と過去の経験を組み合わせた推測である', 600, part)
    f.rect(470, 230, 260, 140, fill='#ffffff', stroke=INK, rx=14)
    f.text(600, 262, '感覚情報', 18, INK, anchor='middle', weight=700)
    f.path('M510,330 Q560,290 610,330 T700,320', INK, 5)
    f.text(600, 355, '暗がりに細長いもの', 14, MUTED, anchor='middle')
    f.box(70, 230, 330, 70, '文脈：夜道', '過去に蛇を見た。蛇が出る場所だと知っている', TEAL, 18, sub_size=12)
    f.box(800, 230, 330, 70, '文脈：室内の机の近く', '電源コードがよく置かれている', INDIGO, 18, sub_size=12)
    f.curve(400, 265, 440, 265, 470, 300, TEAL, 2.2)
    f.curve(800, 265, 760, 265, 730, 300, INDIGO, 2.2)
    f.curve(500, 370, 380, 420, 320, 440, TEAL, 2.5)
    f.curve(700, 370, 820, 420, 880, 440, INDIGO, 2.5)
    f.box(150, 420, 300, 80, '推定：蛇', '危険の可能性を高く見積もる', TEAL, 22, sub_size=13)
    f.box(750, 420, 300, 80, '推定：電源コード', '特に注意を向けない', INDIGO, 22, sub_size=13)
    f.text(600, 470, '感覚情報は同じ', 15, MUTED, anchor='middle')
    f.text(600, 492, '解釈だけが変わる', 15, MUTED, anchor='middle')
    f.footer('脳は外界に直接アクセスできない。受け取るのは感覚器官が変換した信号であり、原因は一意に決まらない。')
    return f.save('ambiguous-input')


def prediction_loop(part):
    f = Figure(4, '予測処理の循環', '予測が先にあり、誤差が世界モデルを更新する', 640, part)
    f.box(90, 240, 230, 90, '世界モデル', '過去の経験から得た内部モデル', TEAL)
    f.box(430, 240, 170, 80, '予測', '', TEAL)
    f.box(700, 240, 170, 80, '比較', '', INK)
    f.box(700, 410, 170, 80, '感覚入力', '', INDIGO)
    f.box(430, 410, 170, 80, '予測誤差', '', TERRA)
    f.line(320, 285, 430, 280, TEAL, 2.5, arrow=True)
    f.line(600, 280, 700, 280, TEAL, 2.5, arrow=True)
    f.line(785, 410, 785, 320, INDIGO, 2.5, arrow=True)
    f.curve(700, 300, 650, 400, 600, 440, TERRA, 2.5)
    f.curve(430, 450, 250, 450, 205, 330, TERRA, 2.5)
    f.text(255, 470, '更新', 18, TERRA, anchor='middle', weight=700)
    f.text(1030, 232, '精度が高い入力ほど', 15, MUTED, anchor='middle')
    f.text(1030, 252, '更新への影響が大きい', 15, MUTED, anchor='middle')
    f.box(960, 410, 170, 80, '外界', '', MUTED)
    f.box(90, 500, 230, 80, '行動', '感覚入力の側を変える', INDIGO, 20)
    f.line(205, 330, 205, 500, INDIGO, 2, arrow=True, dash=True)
    f.text(260, 420, '能動的推論', 16, INDIGO, anchor='middle')
    f.path('M320,540 L1045,540 L1045,490', INDIGO, 2, arrow=True, dash=True)
    f.line(960, 450, 870, 450, INDIGO, 2.5, arrow=True)
    f.footer('予測誤差のすべてが同じ重さではない。信頼できる入力ほど（精度が高いほど）更新に大きく影響する。')
    return f.save('prediction-loop')


def prediction_meets_objectives(part):
    f = Figure(4, '予測処理と目的関数を接続する', '候補行動ごとに将来の状態を予測し、複数の目的関数が重み付きで評価する', 700, part)
    f.text(190, 215, '行動の候補', 16, MUTED, anchor='middle', weight=700)
    f.text(470, 215, '世界モデルが予測する状態', 16, MUTED, anchor='middle', weight=700)
    f.text(790, 215, '目的関数による評価（重み付き）', 16, MUTED, anchor='middle', weight=700)
    f.text(1060, 215, '総合評価 U', 16, MUTED, anchor='middle', weight=700)
    rows = [(260, 'a_1 建物に近づいて調べる', '新しい情報を得る。危険かもしれない', [(3, TEAL), (1, TERRA)], 2.2, True),
            (440, 'a_2 離れて先へ進む', '安全だが、何も分からない', [(0, TEAL), (3, TERRA)], 1.6, False)]
    for y, a, s, evals, u, chosen in rows:
        f.box(70, y, 240, 80, a, '', INK, 15)
        f.line(310, y + 40, 350, y + 40, MUTED, 2, arrow=True)
        f.box(350, y, 240, 80, "予測された状態 s′", s, TEAL, 15, sub_size=11)
        f.line(590, y + 40, 630, y + 40, MUTED, 2, arrow=True)
        f.rect(630, y, 320, 80, fill='#ffffff', stroke=LINE, rx=12)
        for k, ((v, color), name, w) in enumerate(zip(evals, ['知的好奇心', '安全'], ['w=0.5', 'w=0.8'])):
            yy = y + 24 + k * 32
            f.text(645, yy + 5, name, 13, color, weight=700)
            for i in range(3):
                f.circ(740 + i * 20, yy, 7, color if i < v else LINE)
            f.text(820, yy + 5, w, 12, MUTED)
            f.text(880, yy + 5, '× f_i(s′)', 12, MUTED)
        f.line(950, y + 40, 990, y + 40, MUTED, 2, arrow=True)
        f.rect(990, y + 15, 140, 50, fill=PALE if chosen else '#ffffff', stroke=TEAL if chosen else LINE, rx=10)
        f.text(1060, y + 46, f'{u:.1f}', 18, TEAL if chosen else MUTED, anchor='middle', weight=700)
    f.text(1060, 540, '安全の重み w が大きければ a_2 に傾く', 13, MUTED, anchor='middle')
    f.text(600, 580, 'U(a | s, c) = Σ_i w_i(s, c)・E[ f_i(s′) | s, a ]', 17, INK, anchor='middle', weight=700)
    f.text(600, 606, '評価は現在の感覚入力だけでなく、将来の状態の予測に依存する', 14, MUTED, anchor='middle')
    f.footer('目的関数の最大化と予測誤差の最小化は、一般には同じ操作ではない。予測が正確な状態が望ましいとは限らない。')
    return f.save('prediction-meets-objectives')


def attention_and_priority(part):
    f = Figure(4, '何が意識的な処理の対象になるのか', '予測誤差の大きさと、目的に照らした重要性の二段で選ばれる', 640, part)
    inputs = [('文章の内容', 240, TEAL, True), ('室温', 305, MUTED, False), ('身体の姿勢', 370, MUTED, False), ('周囲の物音', 435, MUTED, False), ('大きな音', 500, TERRA, True)]
    f.text(190, 215, '感覚器官からの入力', 17, MUTED, anchor='middle')
    f.panel(430, 200, 220, 350, '予測誤差は大きいか')
    f.panel(730, 200, 230, 350, '目的に照らして重要か')
    f.text(540, 262, '予測していた入力は', 14, MUTED, anchor='middle')
    f.text(540, 280, '誤差が小さい', 14, MUTED, anchor='middle')
    f.text(845, 262, '安全・生存に関わるなら', 14, MUTED, anchor='middle')
    f.text(845, 280, '優先度が上がる', 14, MUTED, anchor='middle')
    for label, y, color, passes in inputs:
        f.tag(80, y - 18, 220, 36, label, color, 17)
        if passes:
            f.line(300, y, 960, y, color, 2.5)
            f.curve(960, y, 1000, y, 1010, 365 if color == TERRA else 345, color, 2.5)
        else:
            f.line(300, y, 470, y, LINE, 2, dash=True)
            f.cross(485, y, 7, MUTED, 2)
    f.text(540, 520, '誤差が小さい入力は', 14, MUTED, anchor='middle')
    f.text(540, 538, 'ここで止まる', 14, MUTED, anchor='middle')
    f.text(845, 520, '誤差が大きくても', 14, MUTED, anchor='middle')
    f.text(845, 538, '目的に無関係なら弱い', 14, MUTED, anchor='middle')
    f.box(1010, 310, 150, 80, '注意の配分', '', INK, 19)
    f.line(1085, 390, 1085, 440, TERRA, 2, arrow=True)
    f.box(1010, 440, 150, 70, '行動の変更', '', TERRA, 18)
    f.text(1085, 560, '読書を中断し、音の原因を確認する', 14, MUTED, anchor='middle')
    f.footer('重要な情報とは予測誤差が大きい情報ではなく、現在の目的や状況に照らして処理する価値が高い情報である。')
    return f.save('attention-and-priority')


def meta_arbitration(part):
    f = Figure(4, '意識を、目的の優先順位を調整するメタ処理として考える', '個別の目的を達成する処理の上位で、どの情報と目的を優先するかを決める', 660, part)
    f.rect(250, 215, 700, 130, fill=PALE, stroke=TEAL, rx=16)
    f.text(600, 255, 'メタ処理：どの情報と目的を優先するか', 22, TEAL, anchor='middle', weight=700)
    f.text(600, 285, '現在の状態を認識し、将来の結果を予測し、競合する目的を調停する', 15, INK, anchor='middle')
    f.text(600, 312, '不確実性や目的間の競合が生じたときに関与する', 14, MUTED, anchor='middle')
    f.box(130, 440, 320, 100, '食欲', '短期：空腹という刺激が食事を促す', TERRA, 22, sub_size=13)
    f.box(750, 440, 320, 100, '健康の維持', '長期：食事を制限したい', INDIGO, 22, sub_size=13)
    f.line(290, 440, 420, 345, TERRA, 2.5, arrow=True, dash=True)
    f.line(910, 440, 780, 345, INDIGO, 2.5, arrow=True, dash=True)
    f.text(600, 420, '競合', 18, INK, anchor='middle', weight=700)
    f.line(450, 490, 750, 490, MUTED, 2, both=True, dash=True)
    f.line(600, 345, 600, 560, TEAL, 3, arrow=True)
    f.box(520, 560, 160, 50, '行動', '', TEAL, 18)
    f.text(1100, 600, 'すべての調停が意識的に行われるわけではない', 13, MUTED, anchor='end')
    f.footer('意識がすべての意思決定を統括しているという主張ではなく、複雑な状況での統合と調停に関与するという機能的な仮説。')
    return f.save('meta-arbitration')


def self_representation_cycle(part):
    f = Figure(4, '自己表象は予測処理と目的関数を結びつける', '三つの要素が循環し、行動の結果が三つを更新する', 660, part)
    wm = (150, 240, 250, 90)
    ob = (800, 240, 250, 90)
    sr = (475, 490, 250, 90)
    f.box(*wm, '世界モデル', '外界を推定し将来を予測する', TEAL)
    f.box(*ob, '目的関数群', '予測された状態や行動を評価する', INDIGO)
    f.box(*sr, '自己表象', '状態・能力・価値観を表現する', TERRA)
    f.line(400, 275, 800, 275, TEAL, 2.5, arrow=True)
    f.text(600, 262, '行動の結果を予測する', 17, TEAL, anchor='middle', weight=700)
    f.line(900, 330, 650, 490, INDIGO, 2.5, arrow=True)
    f.text(830, 420, '評価が自己像を変える', 17, INDIGO, anchor='end', weight=700)
    f.line(550, 490, 300, 330, TERRA, 2.5, arrow=True)
    f.text(370, 420, '予測に影響する', 17, TERRA, anchor='start', weight=700)
    f.line(700, 490, 950, 330, TERRA, 1.8, arrow=True, dash=True)
    f.text(905, 470, '重みに影響する', 15, TERRA, anchor='middle')
    f.circ(600, 400, 46, '#ffffff')
    f.circ(600, 400, 46, MUTED, fill=False, width=2, dash=True)
    f.text(600, 395, '行動の', 16, INK, anchor='middle', weight=700)
    f.text(600, 415, '結果', 16, INK, anchor='middle', weight=700)
    f.footer('一度形成された自己表象は、その後の情報処理を制約し方向づける。この循環で「自分」は維持され、更新される。')
    return f.save('self-representation-cycle')


def exploration_uncertainty(part):
    f = Figure(4, '不確実性を減らすことだけが目的ではない', '探索は短期的に不確実性を増やし、長期的に予測精度を上げる', 650, part)
    x0, x1, y0, y1 = 120, 1000, 520, 240
    f.line(x0, y0, x1, y0, INK, 1.5, arrow=True)
    f.line(x0, y0, x0, y1, INK, 1.5, arrow=True)
    f.text(x1 + 10, y0 + 6, '時間', 15, INK)
    f.text(x0 - 10, y1 - 8, '不確実性', 15, INK, anchor='end')
    base = 400
    f.line(x0, base, x1 - 40, base, MUTED, 2.5, dash=True)
    f.text(x1 - 30, base + 6, '回避：不確実性は変わらない', 14, MUTED)
    f.path(f'M{x0},{base} C300,{base - 130} 420,{base - 150} 520,{base - 40} S760,{base + 60} {x1 - 40},{base + 70}', TEAL, 3.5)
    f.text(1030, base + 76, '探索', 15, TEAL, weight=700)
    f.circ(380, 270, 8, TEAL)
    f.text(380, 250, '未知の場所へ進む：一時的に増大', 14, TEAL, anchor='middle', weight=700)
    f.circ(560, 362, 8, TEAL)
    f.text(560, 345, '情報を獲得する', 14, TEAL, anchor='middle', weight=700)
    f.circ(900, 465, 8, TEAL)
    f.text(900, 495, '将来の予測精度が改善する', 14, TEAL, anchor='middle', weight=700)
    f.text(600, 575, '安全を優先すべきときもあれば、好奇心を優先すべきときもある。その判断が目的関数の調停である。', 14, MUTED, anchor='middle')
    f.footer('意識は不確実性を単純に排除するのではなく、不確実性とどのように向き合うかを調整する働きとして考えられる。')
    return f.save('exploration-uncertainty')


# ---------------------------------------------------------------------------
# 第5回
# ---------------------------------------------------------------------------

def independent_vs_integrated(part):
    f = Figure(5, '集約することと、相互依存することは違う', '左は分割しても働きが変わらない。右は分割すると因果構造が失われる', 640, part)
    f.panel(60, 205, 520, 350, '独立した処理の集合')
    for i, (label, color) in enumerate([('安全性', TEAL), ('効率', INDIGO), ('情報獲得', TERRA)]):
        x = 95 + i * 160
        f.box(x, 265, 130, 70, label, '', color, 19)
        f.line(x + 65, 335, x + 65, 420, color, 2, arrow=True)
    f.box(170, 425, 300, 60, '重み付き和  U = Σ w_i f_i', '', INK, 18)
    f.text(320, 525, '分割しても各部分の働きは変わらない', 16, MUTED, anchor='middle')
    f.panel(620, 205, 520, 350, '相互依存する処理の集合')
    nodes = {'安全性': (700, 290, TEAL), '効率': (960, 290, INDIGO), '情報獲得': (830, 400, TERRA)}
    for label, (x, y, color) in nodes.items():
        f.box(x, y - 30, 130, 60, label, '', color, 19)
    f.line(830, 260, 960, 260, TEAL, 2.2, arrow=True)
    f.line(995, 320, 920, 372, INDIGO, 2.2, arrow=True)
    f.line(830, 372, 760, 320, TERRA, 2.2, arrow=True)
    f.text(880, 345, '互いの評価を変える', 14, MUTED, anchor='middle')
    f.box(730, 455, 200, 56, '自己表象', '', INK, 18, dash=True)
    f.line(830, 430, 830, 455, MUTED, 1.5, arrow=True)
    f.curve(930, 480, 1060, 440, 1030, 320, MUTED, 1.5, arrow=True, dash=True)
    f.curve(730, 480, 600, 440, 700, 320, MUTED, 1.5, arrow=True, dash=True)
    f.text(880, 540, '分割すると因果的な関係が失われる', 16, MUTED, anchor='middle')
    f.footer('Φは情報の量ではなく、全体に固有の因果構造が部分へどの程度還元できないかを問う。')
    return f.save('independent-vs-integrated')


def phi_partition(part):
    f = Figure(5, '分割によって失われる因果構造を測る', '統合情報量Φの考え方を、概念的な近似式で示す', 640, part)

    def triad(cx, cy, cut=False):
        pts = [polar(cx, cy, 70, -90), polar(cx, cy, 70, 30), polar(cx, cy, 70, 150)]
        for (x1, y1), (x2, y2) in [(pts[0], pts[1]), (pts[1], pts[2]), (pts[2], pts[0])]:
            crosses = cut and ((x1 < cx) != (x2 < cx))
            if crosses:
                f.line(x1, y1, x2, y2, LINE, 2, dash=True)
            else:
                f.line(x1, y1, x2, y2, TEAL, 2.5, arrow=True)
        for x, y in pts:
            f.circ(x, y, 18, '#ffffff')
            f.circ(x, y, 18, TEAL, fill=False, width=2.5)
    f.text(250, 230, 'システム S', 20, INK, anchor='middle', weight=700)
    triad(250, 350)
    f.text(250, 470, 'C(S)：分割前の因果構造', 15, MUTED, anchor='middle')
    f.text(600, 230, '分割 P', 20, INK, anchor='middle', weight=700)
    f.line(600, 260, 600, 440, TERRA, 3, dash=True)
    f.cross(600, 350, 10, TERRA, 3)
    f.text(600, 470, '要素間の相互作用を切る', 15, MUTED, anchor='middle')
    f.text(950, 230, '分割後', 20, INK, anchor='middle', weight=700)
    triad(950, 350, cut=True)
    f.text(950, 470, 'C(P)：失われた因果関係は破線', 15, MUTED, anchor='middle')
    f.line(340, 350, 520, 350, MUTED, 2, arrow=True)
    f.line(680, 350, 860, 350, MUTED, 2, arrow=True)
    f.rect(150, 510, 900, 70, fill='#ffffff', stroke=LINE, rx=12)
    f.text(600, 538, 'Φ_approx(S) = min_P  D( C(S), C(P) )', 18, INK, anchor='middle', weight=700)
    f.text(600, 564, '最も統合の弱い分割を探し、それでも失われる構造の大きさを統合の程度とみなす', 14, MUTED, anchor='middle')
    f.footer('この式はIITの正式なΦの定義ではない。情報の量ではなく、全体に固有の因果構造を問うという考え方を表す。')
    return f.save('phi-partition')


def coupled_objectives(part):
    f = Figure(5, '目的関数の内部状態は、互いの更新に影響する', '時間に沿って展開すると、ある目的の状態が次の時刻の他の目的の状態を変える', 660, part)
    cols = [('時刻 t', 300), ('時刻 t+1', 600), ('時刻 t+2', 900)]
    rows = [('f_1 安全性', 280, TEAL), ('f_2 効率', 400, INDIGO), ('f_3 情報獲得', 520, TERRA)]
    for label, x in cols:
        f.text(x, 225, label, 17, INK, anchor='middle', weight=700)
    for label, y, color in rows:
        f.text(120, y + 6, label, 16, color, weight=700)
    for ci in range(len(cols) - 1):
        x1, x2 = cols[ci][1], cols[ci + 1][1]
        for _, y1, c1 in rows:
            for _, y2, _ in rows:
                f.line(x1 + 24, y1, x2 - 24, y2, c1, 1.6 if y1 == y2 else 1.1, arrow=True, dash=(y1 != y2))
    for _, x in cols:
        for _, y, color in rows:
            f.circ(x, y, 20, '#ffffff')
            f.circ(x, y, 20, color, fill=False, width=2.5)
    f.pill(1000, 250, 130, 40, 's(t) 外界', MUTED, 15)
    f.text(1065, 318, '外界や身体の状態も', 12, MUTED, anchor='middle')
    f.text(1065, 334, '各更新に入る', 12, MUTED, anchor='middle')
    f.text(600, 590, 'f_i(t+1) = g_i( f_1(t), f_2(t), …, f_n(t), s(t) )', 17, INK, anchor='middle', weight=700)
    f.footer('実線は自分自身の更新、破線は他の目的への影響。厳密には目的関数と、それを評価する内部状態を区別する。')
    return f.save('coupled-objectives')


def self_objective_cycle(part):
    f = Figure(5, '自己表象を核とする循環', '「自分」は結果であり、同時に次の処理に影響する内部状態である', 640, part)
    cx, cy, rx, ry = 600, 405, 400, 140
    steps = [('目的関数の相互作用', -90, TEAL), ('自己表象の形成', -18, TERRA), ('重み・評価への影響', 54, INDIGO), ('行動の選択', 126, INK), ('経験の蓄積', 198, MUTED)]
    pos = []
    for label, deg, color in steps:
        x, y = polar(cx, cy, rx, deg, ry)
        pos.append((x, y))
        f.box(x - 115, y - 32, 230, 64, label, '', color, 19)
    for i in range(len(pos)):
        (x1, y1), (x2, y2) = pos[i], pos[(i + 1) % len(pos)]
        dx, dy = x2 - x1, y2 - y1
        d = math.hypot(dx, dy)
        ux, uy = dx / d, dy / d
        f.line(x1 + ux * 125, y1 + uy * 48, x2 - ux * 125, y2 - uy * 48, MUTED, 2.2, arrow=True)
    f.text(cx, cy - 10, '「自分」は情報処理の出力であると同時に、', 16, INK, anchor='middle')
    f.text(cx, cy + 14, '将来の情報処理に影響する内部状態である', 16, INK, anchor='middle')
    f.text(cx, cy + 44, '循環が続くことで自己は構築され続ける', 14, MUTED, anchor='middle')
    f.footer('目的関数の統合とIITの因果的な情報統合は同一ではない。両者の対応は本連載の仮説である。')
    return f.save('self-objective-cycle')


def integrated_subset(part):
    f = Figure(5, '最も統合された部分集合は、状況によって入れ替わる', '目的関数の集合 F の中で、強く相互作用する組 F* を考える', 660, part)
    names = ['生存', '安全', '身体', '承認', '倫理', '愛着', '好奇心', '美意識']
    scenes = [(320, '危険な状況', {0, 1, 2}, TERRA), (880, '親しい人と過ごす時間', {3, 4, 5}, INDIGO)]
    for cx, label, strong, color in scenes:
        f.text(cx, 225, label, 18, INK, anchor='middle', weight=700)
        pts = [polar(cx, 400, 120, -90 + i * 45) for i in range(8)]
        members = sorted(strong)
        for i in members:
            for j in members:
                if i < j:
                    f.line(*pts[i], *pts[j], color, 2.5)
        for i, (x, y) in enumerate(pts):
            on = i in strong
            if on:
                f.blob(x, y, 40, color, 0.45)
            f.circ(x, y, 22, '#ffffff')
            f.circ(x, y, 22, color if on else LINE, fill=False, width=2.5 if on else 1.5)
            f.text(x, y + 5, names[i], 12, INK if on else MUTED, anchor='middle', weight=700 if on else 400)
        f.text(cx, 560, 'F*：強く結びつく組', 14, color, anchor='middle', weight=700)
    f.text(600, 400, '状況が変わると', 14, MUTED, anchor='middle')
    f.line(560, 420, 640, 420, MUTED, 2, both=True)
    f.text(600, 600, 'F* = argmax_(F′ ⊆ F) J(F′)　　J は本モデル独自の統合度の評価関数', 15, INK, anchor='middle')
    f.footer('J は IIT のΦと同一ではない。最も統合された組がそのまま自己になるとも限らず、機能的な条件が別に要る。')
    return f.save('integrated-subset')


def conflict_adjustment(part):
    f = Figure(5, '矛盾は排除されるのではなく、調整される', '競合する目的を同じシステムの中で扱い続ける', 620, part)
    f.box(70, 300, 260, 100, '安全性', '未知の環境への進入を避ける', TEAL, 22, sub_size=13)
    f.box(870, 300, 260, 100, '知的好奇心', 'その環境を探索する', TERRA, 22, sub_size=13)
    f.text(600, 230, '競合', 18, INK, anchor='middle', weight=700)
    f.line(330, 350, 420, 350, TEAL, 2.5, arrow=True)
    f.line(870, 350, 780, 350, TERRA, 2.5, arrow=True)
    f.rect(420, 255, 360, 190, fill='#ffffff', stroke=INK, rx=14)
    f.text(600, 288, '調整された行動', 17, INK, anchor='middle', weight=700)
    f.lines(445, 325, ['・危険性を調べながら探索する', '・安全が確認できるまで延期する', '・一方を優先する（他方を消さない）'], 15, INK, gap=32)
    f.cross(600, 480, 10, LINE, 2.5)
    f.text(630, 486, 'どちらかを完全に排除する、ではない', 14, MUTED)
    f.line(600, 445, 600, 520, MUTED, 2, arrow=True)
    f.box(500, 520, 200, 50, '自己表象へ反映', '', INK, 16)
    f.footer('心理的な矛盾と因果的な情報統合は異なる概念である。矛盾が多いほどΦが大きい、という主張ではない。')
    return f.save('conflict-adjustment')


# ---------------------------------------------------------------------------
# 第6回
# ---------------------------------------------------------------------------

def functional_and_phenomenal(part):
    f = Figure(6, '機能的意識と現象的意識', 'システムが何を行うかと、主体にどう感じられるかは別の問いである', 660, part)
    f.rect(90, 215, 400, 350, fill='#ffffff', stroke=TEAL)
    f.text(290, 255, '機能的意識', 24, TEAL, anchor='middle', weight=700)
    f.lines(130, 300, ['情報を認識する', '注意を配分する', '状態を評価する', '行動を選択する', '経験を記憶する', '自己表象を形成する'], 19, INK, gap=40)
    f.rect(710, 215, 400, 350, fill='#ffffff', stroke=TERRA)
    f.text(910, 255, '現象的意識', 24, TERRA, anchor='middle', weight=700)
    f.lines(750, 300, ['赤い色を見るという体験', '痛みを感じるという体験', '音楽を美しいと感じる体験', '不安や喜びを感じる体験', '自分が存在しているという感覚'], 19, INK, gap=40)
    f.line(490, 390, 710, 390, TERRA, 2.5, arrow=True, dash=True)
    f.text(600, 372, '？', 30, TERRA, anchor='middle', weight=700)
    f.text(600, 430, 'ハードプロブレム', 18, TERRA, anchor='middle', weight=700)
    f.text(600, 455, 'なぜ処理に体験が伴うのか', 14, MUTED, anchor='middle')
    f.text(290, 595, 'システムが何を行うか', 17, MUTED, anchor='middle')
    f.text(910, 595, '主体にどう感じられるか', 17, MUTED, anchor='middle')
    f.footer('機能的意識は計算機で近似できる。近似できても、現象的意識の存在が証明されたことにはならない。')
    return f.save('functional-and-phenomenal')


def inverted_qualia(part):
    f = Figure(6, '逆転クオリア', '外から見える行動が同じでも、体験の質が入れ替わっている可能性を問う思考実験', 640, part)
    f.rect(540, 230, 120, 200, fill='#3a3f47', stroke='#3a3f47', rx=16)
    f.circ(600, 285, 36, '#d9453a')
    f.circ(600, 375, 36, '#3aa65a')
    f.text(600, 460, '同じ信号機', 15, MUTED, anchor='middle')
    for x, name, red_exp, green_exp in [(230, '人物 A', ('#d9453a', '赤の体験'), ('#3aa65a', '緑の体験')), (970, '人物 B', ('#3aa65a', '緑の体験'), ('#d9453a', '赤の体験'))]:
        f.circ(x, 280, 30, '#ffffff')
        f.circ(x, 280, 30, INK, fill=False, width=2.5)
        f.text(x, 240, name, 17, INK, anchor='middle', weight=700)
        f.rect(x - 110, 330, 220, 110, fill='#ffffff', stroke=LINE, rx=14)
        f.text(x, 352, '主観的な体験', 13, MUTED, anchor='middle')
        f.circ(x - 55, 395, 18, red_exp[0])
        f.text(x - 55, 428, red_exp[1], 12, INK, anchor='middle')
        f.circ(x + 55, 395, 18, green_exp[0])
        f.text(x + 55, 428, green_exp[1], 12, INK, anchor='middle')
        f.text(x, 480, '赤で止まり、緑で進む', 15, INK, anchor='middle', weight=700)
        f.text(x, 502, '色の名前も同じように使う', 13, MUTED, anchor='middle')
    f.text(600, 545, '行動は完全に同じ。体験の質が入れ替わっていても、外部からは確認できない', 15, INK, anchor='middle', weight=700)
    f.text(600, 570, '左の「赤を見たときの体験」が、右では「緑を見たときの体験」にあたる', 13, MUTED, anchor='middle')
    f.footer('実際に逆転している証拠があるわけではない。機能だけで体験の質を特定できるのか、という概念上の隔たりを示す。')
    return f.save('inverted-qualia')


def iit_reframing(part):
    f = Figure(6, 'IITは問いを置き換える', '「なぜ処理に体験が伴うか」から「どの因果構造がどの体験に対応するか」へ', 600, part)
    f.panel(60, 205, 500, 320, '従来の問いの立て方')
    f.box(100, 300, 180, 80, '情報処理', '', INK, 20)
    f.box(340, 300, 180, 80, '意識体験', '', TERRA, 20)
    f.line(280, 340, 340, 340, TERRA, 2.5, arrow=True, dash=True)
    f.text(310, 325, '？', 22, TERRA, anchor='middle', weight=700)
    f.text(310, 430, '二つを別のものとして置き、', 15, MUTED, anchor='middle')
    f.text(310, 452, '間の関係を説明しようとする', 15, MUTED, anchor='middle')
    f.panel(640, 205, 500, 320, 'IITの立場')
    f.rect(700, 270, 380, 150, fill=PALE, stroke=TEAL, rx=16)
    f.text(890, 305, '統合的な因果構造', 20, TEAL, anchor='middle', weight=700)
    f.text(800, 360, '因果構造として記述', 14, INK, anchor='middle')
    f.text(980, 360, '体験として記述', 14, INK, anchor='middle')
    f.line(880, 350, 900, 350, LINE, 1)
    f.text(890, 395, '同じ現象の二つの記述', 14, TEAL, anchor='middle', weight=700)
    f.text(890, 450, '問い：どのような因果構造が、', 15, INK, anchor='middle')
    f.text(890, 472, 'どのような意識体験に対応するのか', 15, INK, anchor='middle')
    f.footer('IITはハードプロブレムへの一つの理論的回答であり、問題を最終的に解決したわけではない。')
    return f.save('iit-reframing')


def functional_love(part):
    f = Figure(6, 'AIが「愛している」と言うことと、愛を感じることは違う', '機能的な側面は実装できる。現象的な側面はそれだけでは結論できない', 640, part)
    f.rect(70, 215, 560, 330, fill='#ffffff', stroke=TEAL)
    f.text(350, 252, '機能的な愛（実装できる）', 20, TEAL, anchor='middle', weight=700)
    f.lines(110, 300, ['相手の好みを記憶する', '相手の状態を予測する', '関係の維持を高く評価する目的関数を持つ', '相手に配慮した行動を選択する', '経験によって関係の表象を更新する'], 16, INK, gap=36)
    f.rect(100, 480, 500, 44, fill=PALE, stroke=TEAL, rx=22)
    f.text(350, 508, '「あなたを愛している」と発言する', 16, TEAL, anchor='middle', weight=700)
    f.line(630, 380, 720, 380, TERRA, 2.5, arrow=True, dash=True)
    f.text(675, 360, '？', 24, TERRA, anchor='middle', weight=700)
    f.rect(720, 215, 410, 330, fill='#ffffff', stroke=TERRA)
    f.text(925, 252, '現象的な愛', 20, TERRA, anchor='middle', weight=700)
    f.text(925, 330, '相手を愛しているという', 17, INK, anchor='middle')
    f.text(925, 356, '主観的な体験を持つ', 17, INK, anchor='middle')
    f.text(925, 420, '左の仕組みを実装しただけでは、', 14, MUTED, anchor='middle')
    f.text(925, 442, '右が実現されたとは結論できない', 14, MUTED, anchor='middle')
    f.text(925, 500, '倫理的判断や自己認識も同じ構造', 14, MUTED, anchor='middle')
    f.footer('人間では両者が密接に関係している。計算機による実装でも、この区別を維持する。')
    return f.save('functional-love')


def feedforward_vs_recurrent(part):
    f = Figure(6, '入出力が同じでも、内部の因果構造は異なり得る', 'IITはこの違いを意識の成立に関係づける', 620, part)
    for px, label, recurrent in [(60, 'フィードフォワード型', False), (620, '再帰型', True)]:
        f.panel(px, 205, 520, 300, label)
        f.pill(px + 20, 335, 90, 40, '入力', MUTED, 17)
        f.pill(px + 410, 335, 90, 40, '出力', MUTED, 17)
        if not recurrent:
            xs = [px + 160, px + 265, px + 370]
            for x in xs:
                f.circ(x, 355, 24, '#ffffff')
                f.circ(x, 355, 24, TEAL, fill=False, width=2.5)
            f.line(px + 110, 355, xs[0] - 26, 355, TEAL, 2.2, arrow=True)
            f.line(xs[0] + 26, 355, xs[1] - 26, 355, TEAL, 2.2, arrow=True)
            f.line(xs[1] + 26, 355, xs[2] - 26, 355, TEAL, 2.2, arrow=True)
            f.line(xs[2] + 26, 355, px + 410, 355, TEAL, 2.2, arrow=True)
            f.text(px + 260, 460, '処理は一方向に進む', 16, MUTED, anchor='middle')
        else:
            a, b, c = (px + 185, 300), (px + 335, 300), (px + 260, 410)
            for x, y in (a, b, c):
                f.circ(x, y, 24, '#ffffff')
                f.circ(x, y, 24, INDIGO, fill=False, width=2.5)
            f.line(a[0] + 28, a[1] - 6, b[0] - 28, b[1] - 6, INDIGO, 2.2, arrow=True)
            f.line(b[0] - 28, b[1] + 6, a[0] + 28, a[1] + 6, INDIGO, 2.2, arrow=True)
            f.line(b[0] - 10, b[1] + 26, c[0] + 16, c[1] - 24, INDIGO, 2.2, arrow=True)
            f.line(c[0] + 4, c[1] - 26, b[0] - 22, b[1] + 22, INDIGO, 2.2, arrow=True)
            f.line(c[0] - 16, c[1] - 24, a[0] + 10, a[1] + 26, INDIGO, 2.2, arrow=True)
            f.line(a[0] + 22, a[1] + 22, c[0] - 4, c[1] - 26, INDIGO, 2.2, arrow=True)
            f.line(px + 110, 355, a[0] - 20, a[1] + 16, INDIGO, 2.2, arrow=True)
            f.line(b[0] + 20, b[1] + 16, px + 410, 355, INDIGO, 2.2, arrow=True)
            f.text(px + 260, 460, '要素が互いの状態に影響し合う', 16, MUTED, anchor='middle')
    f.text(600, 545, '入出力は同じ。内部の因果構造だけが異なる。', 17, INK, anchor='middle', weight=700)
    f.footer('再帰的な構造を持てば必ず意識が成立するわけではない。循環して見えることと因果的な統合は別である。')
    return f.save('feedforward-vs-recurrent')


def three_axes(part):
    f = Figure(6, 'AIに意識を問うときの三つの評価軸', '似ていることは、次の段が同じであることを意味しない', 620, part)
    steps = [(70, 430, '行動上の類似性', '同じように判断・応答できるか', TEAL),
             (450, 320, '機能的な構造', '自己表象・予測・記憶・調停があるか', INDIGO),
             (830, 210, '現象的意識の理論的条件', 'IITなどが求める内部構造があるか', TERRA)]
    for x, y, t, s, color in steps:
        f.box(x, y, 300, 92, t, s, color, 20, sub_size=14)
        f.line(x, y + 92, x + 300, y + 92, color, 4)
    for (x1, y1, *_), (x2, y2, *_) in zip(steps, steps[1:]):
        f.line(x1 + 300, y1 + 15, x2, y2 + 77, TERRA, 2, arrow=True, dash=True)
        f.text(x1 + 340, y1 - 38, '必ずしも', 13, TERRA, anchor='middle')
        f.text(x1 + 340, y1 - 20, '意味しない', 13, TERRA, anchor='middle')
    f.text(600, 565, '行動が似ている → 機能が同じ、とは限らない。機能が似ている → 因果構造が同じ、とも限らない。', 15, MUTED, anchor='middle')
    f.footer('因果構造の類似を確認できても、それが体験の存在を証明するかどうかは採用する意識理論に依存する。')
    return f.save('three-axes')


def three_theories(part):
    f = Figure(6, '三つの理論は、異なる対象を説明する', '接続はできるが、どれも単独で主観的体験の存在を導かない', 640, part)
    cols = [(70, '目的関数モデル', ['自己表象の形成', '目的関数の調停', '意思決定'], TEAL), (430, '予測処理', ['世界の状態の推定', '感覚情報の解釈', '予測誤差による更新'], INDIGO), (790, '統合情報理論（IIT）', ['意識体験と', '因果的な情報統合の関係'], TERRA)]
    for x, title, items, color in cols:
        f.rect(x, 215, 340, 220, fill='#ffffff', stroke=color)
        f.text(x + 170, 252, title, 20, color, anchor='middle', weight=700)
        f.text(x + 170, 282, '説明する対象', 12, MUTED, anchor='middle')
        f.lines(x + 170, 318, items, 16, INK, anchor='middle', gap=32)
    f.line(410, 325, 430, 325, MUTED, 2, both=True, dash=True)
    f.line(770, 325, 790, 325, MUTED, 2, both=True, dash=True)
    f.text(600, 470, '接続', 14, MUTED, anchor='middle')
    f.line(240, 480, 960, 480, LINE, 1)
    f.rect(150, 500, 900, 70, fill='#ffffff', stroke=TERRA, rx=12, dash=True)
    f.text(600, 528, '機能的な説明をどれほど詳細にしても、主観的体験の存在はそこから論理的に導かれるとは限らない', 15, TERRA, anchor='middle', weight=700)
    f.text(600, 553, '逆に、現象的意識の理論を採用しても、自己表象の形成や目的の調停は自動的には説明されない', 13, MUTED, anchor='middle')
    f.footer('両者の問題を区別したまま接続する。これが本連載全体の前提である。')
    return f.save('three-theories')


# ---------------------------------------------------------------------------
# 第7回
# ---------------------------------------------------------------------------

def true_self_vs_dividual(part):
    f = Figure(7, '「本当の自分」モデルと分人モデル', '役割の内側に唯一の自分があるのか、複数の自分の集合が個人なのか', 660, part)
    f.panel(60, 205, 500, 390, '「本当の自分」モデル')
    cx, cy = 310, 410
    for r, label, color in [(150, '役割：職場', LINE), (105, '役割：家庭', LINE), (60, '本当の自分', TERRA)]:
        f.circ(cx, cy, r, '#ffffff')
        f.circ(cx, cy, r, color, fill=False, width=2.5, dash=(color == LINE))
        if r > 60:
            f.text(cx, cy - r + 22, label, 13, MUTED, anchor='middle')
    f.text(cx, cy + 6, '本当の自分', 15, TERRA, anchor='middle', weight=700)
    f.text(cx, 575, '役割を剥がせば、本来の自己が残るという前提', 14, MUTED, anchor='middle')
    f.panel(640, 205, 500, 390, '分人モデル')
    cx2, cy2 = 890, 400
    for label, deg, color in [('職場の分人', -90, TEAL), ('家庭の分人', 0, TERRA), ('友人との分人', 90, INDIGO), ('趣味の分人', 180, MUTED)]:
        x, y = polar(cx2, cy2, 70, deg)
        f.blob(x, y, 95, color, 0.35)
        f.circ(x, y, 62, color, fill=False, width=2.2)
        lx, ly = polar(cx2, cy2, 108, deg)
        f.text(lx, ly + 5, label, 13, color, anchor='middle', weight=700)
    f.text(cx2, cy2 + 6, '個人', 16, INK, anchor='middle', weight=700)
    f.text(cx2, 575, 'どれも偽物ではない。分人の集合がひとりの個人を構成する', 14, MUTED, anchor='middle')
    f.footer('分人は平野啓一郎の概念である。これを目的関数の重みとして表すのは本連載独自の解釈。')
    return f.save('true-self-vs-dividual')


def dividual_weights(part):
    f = Figure(7, '分人は目的関数の重みベクトルである', '軸は共通で、相対的な重みだけが異なる', 660, part)
    axes = ['達成', '効率', '承認', '愛着', '安定', '好奇心', '快楽']
    data = {'職場の分人': ([190, 170, 150, 60, 70, 80, 40], TEAL), '家庭の分人': ([60, 50, 70, 190, 170, 60, 90], TERRA), '趣味の分人': ([70, 40, 50, 70, 60, 190, 170], INDIGO)}
    base, left, step, bw = 520, 150, 140, 26
    f.line(left - 40, base, left + step * 7, base, INK, 1.5)
    for i, ax in enumerate(axes):
        gx = left + i * step
        f.text(gx + bw * 1.5, base + 30, ax, 18, INK, anchor='middle', weight=700)
        for j, (name, (vals, color)) in enumerate(data.items()):
            x = gx + j * (bw + 4)
            f.rect(x, base - vals[i], bw, vals[i], fill=color, stroke=color, rx=4, opacity=0.9)
    f.text(left - 50, 330, '重み', 16, MUTED, anchor='end')
    f.line(left - 40, 300, left - 40, base, INK, 1.5, arrow=True)
    for j, (name, (vals, color)) in enumerate(data.items()):
        y = 215 + j * 32
        f.rect(880, y - 14, 22, 22, fill=color, stroke=color, rx=4)
        f.text(915, y + 4, name, 18, INK)
    f.text(600, 590, '同じ人の中で、文脈によってこの重みの組み合わせが切り替わる', 16, MUTED, anchor='middle')
    f.footer('職場に愛着がないわけではない。どれかが本物で残りが偽物というわけでもない。重みの違いが行動傾向の違いになる。')
    return f.save('dividual-weights')


def context_mixture(part):
    f = Figure(7, '文脈が分人を選び、基盤は共有される', '切り替えと共有の両方があるから、同じ「自分」として認識できる', 680, part)
    f.pill(60, 300, 150, 50, '文脈 c', INK, 20)
    f.text(135, 375, '状況・相手・環境', 14, MUTED, anchor='middle')
    f.line(210, 325, 275, 325, MUTED, 2.2, arrow=True)
    f.box(275, 285, 220, 80, '混合係数 π(c)', 'どの分人をどの程度', INK, 20)
    f.line(495, 325, 560, 325, MUTED, 2.2, arrow=True)
    f.rect(560, 200, 340, 290, fill='none', stroke=LINE, rx=16, dash=True)
    f.text(730, 222, '分人 Person_j（目的関数の重み w^(j)）', 14, MUTED, anchor='middle')
    persons = [('職場の分人 w^(1)', 232, TEAL, 'π_1(c) = 0.7'), ('家庭の分人 w^(2)', 320, TERRA, 'π_2(c) = 0.2'), ('趣味の分人 w^(3)', 408, INDIGO, 'π_3(c) = 0.1')]
    f.line(592, 545, 592, 268, TEAL, 1.5, dash=True)
    for label, y, color, coef in persons:
        f.box(625, y, 240, 64, label, coef, color, 18, sub_size=14)
        f.line(592, y + 48, 622, y + 48, TEAL, 1.5, arrow=True, dash=True)
        f.curve(865, y + 32, 905, (y + 32 + 340) / 2, 940, 340 + (y - 320) / 4.4, color, 2.2)
    f.text(1045, 288, '式7-2を重みで書くと', 14, MUTED, anchor='middle')
    f.box(940, 300, 210, 80, '重みの合成 w(c)', 'w(c) = Σ_j π_j(c)・w^(j)', INK, 18, sub_size=14)
    f.line(1045, 380, 1045, 430, MUTED, 2.2, arrow=True)
    f.box(940, 430, 210, 60, '行動の選択', '', INK, 19)
    f.rect(60, 545, 1090, 80, fill=PALE, stroke=TEAL, rx=14)
    f.text(605, 580, '分人が共有する基盤', 20, TEAL, anchor='middle', weight=700)
    f.text(605, 606, '記憶 ／ 身体 ／ 自己表象 ── どの分人の経験も、同じ個人の履歴として蓄積される', 15, INK, anchor='middle')
    f.footer('混合エキスパートモデルと形式的に似ているが、数学的な類似性が心理的な分人の仕組みを証明するわけではない。')
    return f.save('context-mixture')


def narrative_cycle(part):
    f = Figure(7, 'ナラティブは異なる分人をひとつの人生に結びつける', '六つの段階が循環し、自己は変化しながら連続性を保つ', 720, part)
    cx, cy, r = 600, 430, 190
    labels = ['文脈に応じた\n分人が現れる', '分人の重み付けで\n行動を選ぶ', '結果が経験として\n記憶される', '記憶がナラティブ\nに整理される', 'ナラティブが\n自己表象を更新', '自己表象が次の\n分人と行動へ']
    colors = [TEAL, TEAL, INDIGO, TERRA, TERRA, INDIGO]
    pos = [polar(cx, cy, r, -90 + i * 60) for i in range(6)]
    ring_arrows(f, pos, 58, MUTED, 2.2, cx, cy, bow=22)
    for (x, y), label, color in zip(pos, labels, colors):
        f.node(x, y, 54, label, color, 13)
    f.text(cx, cy - 6, '仕事では挑戦、家庭では安定。', 14, INK, anchor='middle')
    f.text(cx, cy + 16, '矛盾を消さずに、同じ人生の中に配置する', 14, INK, anchor='middle')
    f.footer('自己の一貫性とは、あらゆる状況で同じ行動を取ることではなく、異なる行動を同じ個人の経験として理解できることである。')
    return f.save('narrative-cycle')


def tool_incorporation(part):
    f = Figure(7, '道具やアバターは、どのように自分の一部になるのか', '操作と結果の対応が学習され、予測が成立すると、身体図式へ取り込まれ得る', 620, part)
    stages = [(70, '習熟前', '道具の先端の位置を意識して計算する', False, 0.0), (430, '繰り返しの操作', '操作と結果の対応を学習し、予測が成立する', False, 0.5), (790, '習熟後', '道具の動きを身体運動と結びつけて制御する', True, 1.0)]
    for x, title, sub, merged, k in stages:
        f.panel(x, 205, 340, 270, title)
        bx, by = x + 110, 325
        f.circ(bx, by, 26, '#ffffff')
        f.circ(bx, by, 26, TEAL, fill=False, width=2.5)
        f.text(bx, by + 5, '身体', 14, TEAL, anchor='middle', weight=700)
        tx = x + 230
        f.rect(tx - 40, by - 16, 80, 32, fill='#ffffff', stroke=TERRA if not merged else TEAL, rx=8, dash=not merged)
        f.text(tx, by + 5, '道具', 14, TERRA if not merged else TEAL, anchor='middle', weight=700)
        if merged:
            f.blob((bx + tx) / 2, by, 120, TEAL, 0.35)
            f.line(bx + 26, by, tx - 40, by, TEAL, 3)
        else:
            f.line(bx + 26, by, tx - 40, by, TERRA, 2, dash=True, both=True)
            f.text((bx + tx) / 2, by - 26, '予測の精度' if k else '結果を予測できない', 14, MUTED, anchor='middle')
            if k:
                f.rect((bx + tx) / 2 - 40, by + 26, 80, 8, fill=SOFT, stroke=SOFT, rx=4)
                f.rect((bx + tx) / 2 - 40, by + 26, 80 * k, 8, fill=TERRA, stroke=TERRA, rx=4)
        f.text(x + 170, 425, sub, 14, INK, anchor='middle')
    f.line(410, 325, 430, 325, MUTED, 2, arrow=True)
    f.line(770, 325, 790, 325, MUTED, 2, arrow=True)
    f.text(600, 515, '例：職人の道具、自動車の車幅感覚、ゲームキャラクターやアバターの操作', 14, MUTED, anchor='middle')
    f.text(600, 540, '第4回の予測処理：行動によってどの感覚入力が生じるかを予測できることが鍵になる', 14, MUTED, anchor='middle')
    f.footer('制御できる対象がすべて自己になるわけではない。記憶・感情・価値判断・社会的な関係も関係する。')
    return f.save('tool-incorporation')


def extended_self(part):
    f = Figure(7, '自己の境界は距離として現れる', '皮膚の内外ではなく、情報処理上の関係が結びつきの強さを決める', 740, part)
    cx, cy = 480, 460
    for r in (100, 175, 250):
        f.circ(cx, cy, r, LINE, fill=False, dash=True, width=1.5)
    f.text(cx + 252, cy - 6, '弱い', 14, MUTED)
    f.text(cx + 102, cy - 6, '強い', 14, MUTED)
    f.blob(cx, cy, 110, TEAL, 0.5)
    f.circ(cx, cy, 56, '#ffffff')
    f.circ(cx, cy, 56, TEAL, fill=False, width=2.5)
    f.text(cx, cy + 7, '自己表象', 20, TEAL, anchor='middle', weight=700)
    items = [('身体', -90, 80), ('作品', 95, 130), ('熟練した道具', -155, 160), ('自動車', -35, 170), ('ゲームキャラクター', 150, 205), ('SNSアカウント', 20, 215), ('見知らぬ物', -120, 240)]
    for label, deg, r in items:
        x, y = polar(cx, cy, r, deg)
        f.blob(x, y, 48, TEAL, 0.4)
        f.circ(x, y, 9, TEAL)
        anchor = 'start' if math.cos(math.radians(deg)) > 0.3 else ('end' if math.cos(math.radians(deg)) < -0.3 else 'middle')
        off = 16 if anchor == 'start' else (-16 if anchor == 'end' else 0)
        f.text(x + off, y + (26 if anchor == 'middle' and deg > 0 else (-18 if anchor == 'middle' else 6)), label, 17, INK, anchor=anchor, weight=700)
    f.rect(840, 225, 300, 300, fill='#ffffff', stroke=LINE)
    f.text(990, 262, '距離を決める要素', 20, INK, anchor='middle', weight=700)
    f.lines(870, 310, ['制御：対象を制御できる程度', '予測：変化を予測できる程度', '記憶：経験と記憶の結びつき', '価値：目的や価値観との関係', '関係：対象を通じた他者との関係'], 16, INK, gap=38)
    f.text(990, 508, 'SelfScore(x, c) = h(…, c)', 14, MUTED, anchor='middle')
    f.footer('スコアは説明のための工学的な仮説であり、脳内に単一の数値が存在するという主張ではない。')
    return f.save('extended-self')


def unified_update(part):
    f = Figure(7, '分人の切り替えも、自己の拡張も、同じ自己表象の更新である', '変化する変数が違うだけで、どちらも S(t) = G(F, W, M, R, C) の更新になる', 580, part)
    f.rect(350, 225, 500, 150, fill=PALE, stroke=TEAL, rx=16)
    f.text(600, 265, '自己表象  S(t) = G( F, W(t), M(t), R(t), C(t) )　（式7-4）', 19, TEAL, anchor='middle', weight=700)
    f.text(600, 297, 'F：目的関数の集合　W：重み　M：記憶', 14, INK, anchor='middle')
    f.text(600, 321, 'R：他者・外部対象との関係　C：文脈', 14, INK, anchor='middle')
    f.text(600, 353, 'G：これらを統合する処理', 14, MUTED, anchor='middle')
    f.box(70, 245, 230, 110, '分人の切り替え', '主に W(t) と C(t) が変わる', TERRA, 20, sub_size=14)
    f.box(900, 245, 230, 110, '自己の拡張', '主に R(t) が変わる', INDIGO, 20, sub_size=14)
    f.line(300, 300, 350, 300, TERRA, 2.5, arrow=True)
    f.line(900, 300, 850, 300, INDIGO, 2.5, arrow=True)
    f.text(185, 395, '文脈で目的関数の', 14, MUTED, anchor='middle')
    f.text(185, 415, '重み付けが変わる', 14, MUTED, anchor='middle')
    f.text(1015, 395, '外部対象が自己表象と', 14, MUTED, anchor='middle')
    f.text(1015, 415, '結びつく程度が変わる', 14, MUTED, anchor='middle')
    f.text(600, 450, '共通点：固定的な自己を前提とせず、自己表象の構成が動的に更新される', 15, INK, anchor='middle', weight=700)
    f.text(600, 480, '例：あるゲームでは大胆な分人が現れ、そのキャラクターが自己の延長として認識される', 14, MUTED, anchor='middle')
    f.footer('両者は独立ではなく、相互に関係しながら変化する。')
    return f.save('unified-update')


# ---------------------------------------------------------------------------
# 第8回
# ---------------------------------------------------------------------------

def narrative_as_learning(part):
    f = Figure(8, '物語は目的関数を学習させる', '現実とは別の経路から、価値判断と結びついた経験を渡す', 620, part)
    f.box(70, 225, 250, 92, '現実の経験', '身体的な危険や責任が伴う', TEAL)
    f.box(70, 400, 250, 92, '物語体験', '追体験・代替的な経験', TERRA)
    f.text(195, 525, '行動と結果の関係を示す', 15, MUTED, anchor='middle')
    f.curve(320, 271, 370, 300, 420, 340, TEAL, 2.5)
    f.curve(320, 446, 370, 420, 420, 376, TERRA, 2.5)
    f.box(420, 315, 220, 90, '価値判断の学習', '何が望ましいかの更新', INK)
    f.line(640, 360, 700, 360, MUTED, 2.2, arrow=True)
    f.box(700, 315, 260, 90, '目的関数・自己表象', 'の更新', INDIGO, 20)
    f.line(960, 360, 1010, 360, MUTED, 2.2, arrow=True)
    f.box(1010, 315, 140, 90, '行動選択', 'の変化', INDIGO, 19)
    f.text(690, 470, '例：利己的な行動が信頼を壊し、協力が信頼を生む様子を追体験する', 15, MUTED, anchor='middle')
    f.footer('物語の内容がそのまま目的関数として取り込まれるわけではない。現実とは異なる経路で評価基準に影響し得る。')
    return f.save('narrative-as-learning')


def repair_flow(part):
    f = Figure(8, '物語は傷ついた自己評価を再較正する', '現実の出来事は変えずに、出来事への評価と解釈を変える', 640, part)
    chain = ['現実での失敗', '自己評価の低下', '将来の予測が悪化', '挑戦を避ける']
    for i, label in enumerate(chain):
        x = 70 + i * 275
        f.box(x, 230, 230, 70, label, '', MUTED, 17)
        if i < 3:
            f.line(x + 230, 265, x + 275, 265, MUTED, 2, arrow=True)
    f.text(460, 325, '「自分には能力がない」「努力しても報われない」', 14, MUTED, anchor='middle')
    f.box(70, 420, 420, 90, '物語による代替的な経験', '評価者が誤っていた／成功以外にも価値がある', TERRA, 18, sub_size=13)
    f.line(490, 465, 540, 465, TERRA, 2.5, arrow=True)
    f.box(540, 420, 260, 90, '評価基準の再構成', '出来事の解釈が変わる', TERRA, 18, sub_size=13)
    f.tag(720, 335, 320, 40, '予測と行動が変わり得る', TERRA, 15)
    f.curve(800, 465, 880, 450, 880, 377, TERRA, 2.5)
    f.text(600, 565, '現実での失敗 → 自己評価の低下 → 物語による代替的な経験 → 評価基準の再構成', 14, INK, anchor='middle')
    f.footer('「修復」は比喩であり、医学的な治療と同等の効果を主張するものではない。')
    return f.save('repair-flow')


def genre_isekai(part):
    f = Figure(8, '異世界転生もの：社会的制約を取り除いた評価環境', '現実で成立しなかった能力と評価の対応を、物語の中で再構成する', 650, part)
    f.panel(60, 205, 1080, 175, '現実社会')
    f.tag(110, 290, 140, 44, '能力・努力', TEAL)
    f.rect(420, 262, 340, 86, fill=SOFT, stroke=MUTED, rx=10, dash=True)
    f.text(590, 296, '社会的な制約', 15, INK, anchor='middle', weight=700)
    f.text(590, 320, '地位・所属組織・人間関係・経済的条件', 13, MUTED, anchor='middle')
    f.line(250, 312, 420, 312, TEAL, 2.5)
    f.line(760, 312, 920, 312, LINE, 2.5, arrow=True, dash=True)
    f.tag(930, 290, 140, 44, '評価', MUTED)
    f.text(590, 368, '能力と評価が必ずしも対応しない', 13, MUTED, anchor='middle')
    f.panel(60, 405, 1080, 175, '異世界')
    f.tag(110, 490, 140, 44, '能力・努力', TEAL)
    f.rect(420, 462, 340, 86, fill='none', stroke=LINE, rx=10, dash=True)
    f.cross(590, 505, 18, TERRA, 3.5)
    f.text(590, 568, '制約が取り除かれる', 13, MUTED, anchor='middle')
    f.line(250, 512, 920, 512, TEAL, 3, arrow=True)
    f.tag(930, 490, 140, 44, '評価', TEAL)
    f.footer('修復されるのは能力そのものではなく、自分の能力が社会でどう評価されるべきかという認識である。')
    return f.save('genre-isekai')


def genre_exile(part):
    f = Figure(8, '追放もの：低い評価の原因を評価者の側へ帰属させる', '他者評価と自己評価の結びつきを切り離す構造', 600, part)
    f.panel(60, 205, 520, 330, '従来の結びつき')
    f.tag(110, 330, 180, 44, '低い他者評価', MUTED)
    f.line(290, 352, 380, 352, MUTED, 2.5, arrow=True)
    f.tag(390, 330, 160, 44, '自己評価の低下', MUTED)
    f.text(320, 430, '周囲に能力が低いと言われ続け、', 13, MUTED, anchor='middle')
    f.text(320, 450, '自分でもそう考えるようになる', 13, MUTED, anchor='middle')
    f.panel(640, 205, 500, 330, '追放ものが提示する解釈')
    f.tag(670, 330, 180, 44, '低い他者評価', MUTED)
    f.line(850, 340, 930, 290, LINE, 2, arrow=True, dash=True)
    f.cross(890, 315, 8, MUTED, 2)
    f.tag(940, 262, 170, 44, '自分の能力', MUTED)
    f.line(850, 364, 930, 410, TERRA, 2.5, arrow=True)
    f.tag(940, 392, 170, 44, '評価者の誤り', TERRA)
    f.text(1025, 470, '→ 自己評価は維持される', 14, TERRA, anchor='middle', weight=700)
    f.text(890, 505, '評価の原因について、ひとつの代替的な物語を示す', 13, MUTED, anchor='middle')
    f.footer('現実のすべての低評価が不当だという主張ではない。他者評価と自分の価値を同一視しなくてよい、という解釈に触れさせる。')
    return f.save('genre-exile')


def genre_slice_of_life(part):
    f = Figure(8, '日常系：競争という評価軸を相対化する', '達成を否定するのではなく、重み付けに別の選択肢を提示する', 600, part)
    base = 480
    f.text(300, 225, '現実社会', 18, INK, anchor='middle', weight=700)
    f.text(900, 225, '日常系の物語世界', 18, INK, anchor='middle', weight=700)
    for cx, vals in [(300, [(200, '競争・達成', MUTED), (70, '会話・食事', TEAL), (60, '季節の変化', TEAL), (50, '何もない時間', TEAL)]), (900, [(70, '競争・達成', MUTED), (200, '会話・食事', TEAL), (190, '季節の変化', TEAL), (180, '何もない時間', TEAL)])]:
        f.line(cx - 220, base, cx + 220, base, INK, 1.5)
        for i, (h, label, color) in enumerate(vals):
            x = cx - 180 + i * 110
            f.bar(x, base, 60, h, color)
            f.text(x + 30, base + 24, label, 13, INK, anchor='middle', weight=700)
    f.line(560, 360, 640, 360, TERRA, 3, arrow=True)
    f.text(600, 340, '重みの相対化', 13, TERRA, anchor='middle', weight=700)
    f.text(600, 540, '競争に勝たなくてもよい。成果を残さなくてもよい。そのような環境を物語の中に構築する', 13, MUTED, anchor='middle')
    f.footer('達成という目的関数を完全に否定するわけではない。重視する場面とそうでない場面がある。')
    return f.save('genre-slice-of-life')


def genre_villainess(part):
    f = Figure(8, '悪役令嬢もの：決められた未来を予測して書き換える', '自分の置かれた物語の構造を認識し、現在の行動を変える', 600, part)
    f.circ(130, 400, 10, INK)
    f.text(130, 440, '現在', 15, INK, anchor='middle', weight=700)
    f.line(140, 400, 920, 400, MUTED, 2.5, arrow=True, dash=True)
    f.text(935, 406, '既定の結末（不幸）', 15, MUTED)
    f.curve(420, 400, 650, 400, 920, 270, TEAL, 3)
    f.text(935, 276, '別の未来', 15, TEAL, weight=700)
    f.circ(420, 400, 9, TERRA)
    f.rect(260, 455, 320, 80, fill='#ffffff', stroke=TERRA, rx=12)
    f.text(420, 482, '物語の構造を認識する（メタ認知）', 14, TERRA, anchor='middle', weight=700)
    f.text(420, 508, '自分が悪役として位置づけられていると知る', 13, MUTED, anchor='middle')
    f.line(420, 455, 420, 412, TERRA, 2, arrow=True)
    f.text(650, 330, '結末を予測し、行動を変更する', 14, TEAL, anchor='middle', weight=700)
    f.text(650, 350, '世界モデルで未来を再構成する（第4回）', 13, MUTED, anchor='middle')
    f.footer('現実でも、環境・地位・過去の失敗・与えられた役割によって未来が決まっているように感じる。その既定の展開を書き換えられる可能性を示す。')
    return f.save('genre-villainess')


def immersion(part):
    f = Figure(8, '没入を構成する五つの処理', '処理が強く結びつくほど、物語の経験が自己表象や目的関数へ影響しやすい', 680, part)
    cx, cy, r = 600, 430, 170
    labels = ['物語世界への\n注意の集中', '登場人物の状態\nや行動の予測', '登場人物への\n感情的な反応', '自己の経験との\n関連づけ', '物語の情報による\n価値判断の更新']
    pos = [polar(cx, cy, r, -90 + i * 72) for i in range(5)]
    for i in range(5):
        for j in range(i + 1, 5):
            f.line(*pos[i], *pos[j], LINE, 1.5)
    for (x, y), label in zip(pos, labels):
        f.node(x, y, 58, label, TEAL, 13)
    f.blob(cx, cy, 70, TERRA, 0.4)
    f.text(cx, cy + 6, '没入', 20, TERRA, anchor='middle', weight=700)
    f.text(1050, 400, '結びつきが強いほど', 13, MUTED, anchor='middle')
    f.text(1050, 418, '自己表象・目的関数へ', 13, MUTED, anchor='middle')
    f.text(1050, 436, '影響しやすい', 13, MUTED, anchor='middle')
    f.footer('没入は自己と物語世界の境界の消失ではない。読者は登場人物に共感しながらも、自分と登場人物を区別できる。')
    return f.save('immersion')


def self_narrative_loop(part):
    f = Figure(8, '自己を更新する循環と、外から入る物語', '物語はナラティブと自己表象の段に作用し、自分の物語は他者へ共有される', 780, part)
    cx, cy, r = 600, 430, 195
    nodes = [('経験', -90, TEAL), ('行動', -30, TEAL), ('予測・目的関数', 30, INDIGO), ('自己表象', 90, TERRA), ('ナラティブ', 150, TERRA), ('記憶', 210, INDIGO)]
    order = ['経験', '記憶', 'ナラティブ', '自己表象', '予測・目的関数', '行動']
    pos = {}
    for label, deg, color in nodes:
        x, y = polar(cx, cy, r, deg)
        pos[label] = (x, y)
        f.circ(x, y, 50, '#ffffff')
        f.circ(x, y, 50, color, fill=False, width=2.5)
        if len(label) > 5:
            f.text(x, y - 2, label[:3], 16, color, anchor='middle', weight=700)
            f.text(x, y + 18, label[3:], 16, color, anchor='middle', weight=700)
        else:
            f.text(x, y + 7, label, 18, color, anchor='middle', weight=700)
    for a, b in zip(order, order[1:] + order[:1]):
        (x1, y1), (x2, y2) = pos[a], pos[b]
        dx, dy = x2 - x1, y2 - y1
        d = math.hypot(dx, dy)
        ux, uy = dx / d, dy / d
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        nx, ny = (mx - cx) / math.hypot(mx - cx, my - cy), (my - cy) / math.hypot(mx - cx, my - cy)
        f.curve(x1 + ux * 54, y1 + uy * 54, mx + nx * 22, my + ny * 22, x2 - ux * 56, y2 - uy * 56, MUTED, 2.2)
    f.box(60, 590, 200, 80, '物語', '他者が作った物語', TERRA, 22)
    f.curve(260, 612, 330, 600, pos['ナラティブ'][0] - 36, pos['ナラティブ'][1] + 36, TERRA, 2.5)
    f.curve(260, 650, 420, 720, pos['自己表象'][0], pos['自己表象'][1] + 52, TERRA, 2.5)
    f.text(160, 700, '価値判断・解釈を', 14, MUTED, anchor='middle')
    f.text(160, 719, '外から更新する', 14, MUTED, anchor='middle')
    f.box(60, 380, 210, 80, '他者への共有', '別の人の目的関数へ', INDIGO, 20)
    f.curve(pos['ナラティブ'][0] - 44, pos['ナラティブ'][1] - 26, 330, 470, 270, 425, INDIGO, 2.5)
    f.text(cx, cy - 8, '自分についての物語が', 15, INK, anchor='middle')
    f.text(cx, cy + 14, '次の行動を方向づける', 15, INK, anchor='middle')
    f.footer('私たちは物語を読むだけでなく、自分を物語として構築し、その物語に従って行動している可能性がある。')
    return f.save('self-narrative-loop')


def social_propagation(part):
    f = Figure(8, '物語は個人の内部と社会の間を循環する', '自分についての物語が共有され、他者の目的関数に影響し、新しい共通体験になる', 760, part)
    cx, cy, r = 600, 455, 195
    labels = ['個人の経験', '自分についての\n物語', '共有\n（会話・SNS・映像）', '他者の解釈\n（受け手で異なる）', '他者の目的関数\nへの影響', '新しい社会的な\n共通体験']
    colors = [TEAL, TEAL, INDIGO, INDIGO, TERRA, TERRA]
    pos = [polar(cx, cy, r, -90 + i * 60) for i in range(6)]
    ring_arrows(f, pos, 68, MUTED, 2.2, cx, cy, bow=22)
    for (x, y), label, color in zip(pos, labels, colors):
        f.node(x, y, 64, label, color, 13)
    f.text(cx, cy - 6, '第1回の共通体験の変化へ戻る：', 13, MUTED, anchor='middle')
    f.text(cx, cy + 14, '学習データは物理的な現実に限定されない', 13, MUTED, anchor='middle')
    f.footer('価値観はプログラムのようにコピーされない。どう解釈し、どの程度取り入れるかは受け手の記憶・価値観・状況で異なる。')
    return f.save('social-propagation')


def integrated_model(part):
    f = Figure(8, '意識・自己・物語の情報処理モデル', '本連載が組み立てた五つのブロックと、その間の循環', 800, part)
    blocks = {
        '外界との相互作用': (70, 215, ['感覚情報の受信', '世界モデルによる予測', '予測誤差による更新'], TEAL),
        '目的関数による評価': (790, 215, ['生存・愛着・承認', '好奇心・倫理・美意識', '相互作用と重みの変化'], INDIGO),
        '自己の形成': (430, 400, ['目的関数間の相互作用', '自己表象の形成', '分人の表出・肉体外への拡張'], TERRA),
        '時間的な自己の維持': (70, 585, ['エピソード記憶', 'ナラティブの生成', '自己表象の更新'], INDIGO),
        '社会的な拡張': (790, 585, ['物語の共有', '他者の経験からの学習', '新しい共通体験の形成'], TEAL),
    }
    for title, (x, y, items, color) in blocks.items():
        f.rect(x, y, 340, 150, fill=PALE if title == '自己の形成' else '#ffffff', stroke=color)
        f.text(x + 170, y + 32, title, 18, color, anchor='middle', weight=700)
        f.lines(x + 170, y + 66, items, 13, INK, anchor='middle', gap=26)
    f.line(410, 290, 790, 290, MUTED, 2.2, arrow=True)
    f.text(600, 280, '予測された状態を評価する', 13, MUTED, anchor='middle')
    f.line(960, 365, 770, 420, INDIGO, 2.2, arrow=True)
    f.line(430, 420, 240, 365, TERRA, 2.2, arrow=True, dash=True)
    f.text(240, 438, '自己表象が予測に影響', 13, TERRA, anchor='start')
    f.line(430, 530, 240, 585, TERRA, 2.2, arrow=True)
    f.line(410, 660, 430, 548, INDIGO, 2.2, arrow=True)
    f.text(440, 612, '更新', 13, INDIGO, anchor='start')
    f.line(960, 585, 770, 530, TEAL, 2.2, arrow=True, dash=True)
    f.text(945, 548, '物語が価値判断を更新', 13, TEAL, anchor='middle')
    f.line(410, 660, 790, 660, MUTED, 2.2, both=True)
    f.text(600, 650, '自分の物語を共有し、他者から学ぶ', 13, MUTED, anchor='middle')
    f.footer('自己の機能的な形成と変化を説明する仮説である。主観的な意識体験そのものが、なぜ存在するのかは未解決のまま残る。')
    return f.save('integrated-model')


# ---------------------------------------------------------------------------
# 第9回
# ---------------------------------------------------------------------------

def virtual_environment(part):
    f = Figure(9, '計算機にとっての「世界」を小さく定義する', '資源・危険・未知領域・他のエージェントを持つ格子世界と、部分的な観測', 680, part)
    gx, gy, cell = 90, 215, 44
    cols, rows = 14, 8
    for i in range(rows):
        for j in range(cols):
            f.rect(gx + j * cell, gy + i * cell, cell, cell, fill='#ffffff', stroke=LINE, width=1, rx=0)
    ax, ay = 4, 4
    for i in range(rows):
        for j in range(cols):
            if abs(i - ay) + abs(j - ax) <= 2:
                f.rect(gx + j * cell, gy + i * cell, cell, cell, fill=PALE, stroke=LINE, width=1, rx=0)
    for i in range(rows):
        for j in range(9, cols):
            x, y = gx + j * cell, gy + i * cell
            f.rect(x, y, cell, cell, fill=SOFT, stroke=LINE, width=1, rx=0)
            f.text(x + cell / 2, y + cell / 2 + 5, '?', 14, MUTED, anchor='middle')
    for (i, j) in [(1, 2), (6, 6), (2, 7)]:
        f.rect(gx + j * cell + 10, gy + i * cell + 10, cell - 20, cell - 20, fill=TEAL, stroke=TEAL, rx=4)
    for (i, j) in [(5, 1), (3, 6)]:
        x, y = gx + j * cell + cell / 2, gy + i * cell + cell / 2
        f.path(f'M{x},{y-14} L{x+14},{y+12} L{x-14},{y+12} Z', TERRA, 2, fill=TERRA)
    f.circ(gx + ax * cell + cell / 2, gy + ay * cell + cell / 2, 14, INK)
    f.circ(gx + 7 * cell + cell / 2, gy + 7 * cell + cell / 2, 14, INDIGO)
    lx = 760
    f.text(lx, 245, '凡例', 18, INK, weight=700)
    f.circ(lx + 12, 285, 12, INK)
    f.text(lx + 40, 290, 'エージェント（エネルギーを消費して行動）', 14, INK)
    f.rect(lx, 315, 24, 24, fill=PALE, stroke=LINE, width=1, rx=0)
    f.text(lx + 40, 333, '観測できる範囲（部分観測）', 14, INK)
    f.rect(lx + 2, 360, 20, 20, fill=TEAL, stroke=TEAL, rx=4)
    f.text(lx + 40, 376, '資源：獲得するとエネルギーが回復', 14, INK)
    f.path(f'M{lx+12},{398} L{lx+24},{420} L{lx},{420} Z', TERRA, 2, fill=TERRA)
    f.text(lx + 40, 418, '危険：損失が生じる', 14, INK)
    f.rect(lx, 445, 24, 24, fill=SOFT, stroke=LINE, width=1, rx=0)
    f.text(lx + 12, 462, '?', 13, MUTED, anchor='middle')
    f.text(lx + 40, 463, '未知の領域：探索すると情報が得られる', 14, INK)
    f.circ(lx + 12, 500, 12, INDIGO)
    f.text(lx + 40, 505, '他のエージェント：協力や競争ができる', 14, INK)
    f.text(lx, 560, 'エネルギー', 13, MUTED)
    f.rect(lx + 90, 550, 260, 12, fill=SOFT, stroke=SOFT, rx=6)
    f.rect(lx + 90, 550, 170, 12, fill=TEAL, stroke=TEAL, rx=6)
    f.text(600, 605, '観測できない部分は過去の経験から推測し、行動の結果を観測して世界モデルを更新する', 14, MUTED, anchor='middle')
    f.footer('現実世界のすべてを再現する必要はない。自己の形成に関係する要素だけを取り出した小さな環境から始める。')
    return f.save('virtual-environment')


def belief_state(part):
    f = Figure(9, '信念状態：確実でないまま行動し、観測で更新する', '部分観測マルコフ決定過程（POMDP）による世界モデルの近似', 640, part)

    def belief(x, title, res, dan, color):
        f.rect(x, 225, 290, 190, fill='#ffffff', stroke=color, rx=14)
        f.text(x + 145, 258, title, 17, color, anchor='middle', weight=700)
        for k, (label, v) in enumerate([('資源がある', res), ('危険がある', dan)]):
            y = 295 + k * 50
            f.text(x + 26, y + 5, label, 14, INK)
            f.rect(x + 118, y - 8, 116, 16, fill=SOFT, stroke=SOFT, rx=8)
            f.rect(x + 118, y - 8, 116 * v, 16, fill=TEAL if k == 0 else TERRA, stroke=TEAL if k == 0 else TERRA, rx=8)
            f.text(x + 246, y + 5, f'{v:.2f}', 13, MUTED)
        f.text(x + 145, 395, 'b_t(s)：状態 s にあると考える確率', 13, MUTED, anchor='middle')
    belief(60, '移動前の信念', 0.7, 0.2, INK)
    f.line(350, 320, 410, 320, MUTED, 2.2, arrow=True)
    f.box(410, 285, 170, 70, '行動：移動する', '', INK, 15)
    f.line(580, 320, 640, 320, MUTED, 2.2, arrow=True)
    f.box(640, 285, 170, 70, '観測：資源を発見', '', TEAL, 15)
    f.line(810, 320, 850, 320, MUTED, 2.2, arrow=True)
    belief(850, '更新後の信念', 0.95, 0.05, TEAL)
    f.text(495, 390, '資源の確率が高く、', 13, MUTED, anchor='middle')
    f.text(495, 408, '危険の確率が低ければ選びやすい', 13, MUTED, anchor='middle')
    f.text(600, 458, 'b_t(s) = P( s_t = s | o_1:t, a_1:t-1 )　（式9-1）', 17, INK, anchor='middle', weight=700)
    f.text(600, 484, '観測 o と過去の行動 a から、直接は見えない環境の状態を推定する', 13, MUTED, anchor='middle')
    f.curve(995, 415, 600, 660, 205, 415, LINE, 1.5, arrow=True, dash=True)
    f.text(600, 575, '次の行動へ', 13, MUTED, anchor='middle')
    f.footer('POMDPは部分観測下の意思決定の枠組みであり、人間の神経活動そのものを説明するものではない。')
    return f.save('belief-state')


def objective_conflicts(part):
    f = Figure(9, '目的関数の競合を意図的に発生させる', '同じ行動が、目的関数によって高くも低くも評価される', 690, part)
    objs = ['生存', '効率', '好奇心', '承認', '倫理']
    acts = [('未知の場所を探索する', ['↓', '↓', '↑', '・', '・']), ('資源を他者に分配する', ['↓', '・', '・', '↑', '↑']), ('危険な近道を通る', ['↓', '↑', '・', '・', '・']), ('協力して危険を避ける', ['↑', '↓', '・', '↑', '・']), ('禁止された行動', ['↑', '↑', '・', '・', '×'])]
    x0, y0, cw, rh = 420, 240, 130, 60
    for j, o in enumerate(objs):
        f.text(x0 + j * cw + cw / 2, 222, o, 16, INK, anchor='middle', weight=700)
    for i, (a, cells) in enumerate(acts):
        y = y0 + i * rh
        forbidden = i == len(acts) - 1
        f.rect(70, y + 6, 1070, rh - 12, fill=SOFT if forbidden else '#ffffff', stroke=LINE, rx=8)
        f.text(90, y + 36, a, 15, MUTED if forbidden else INK, weight=700)
        for j, c in enumerate(cells):
            x = x0 + j * cw + cw / 2
            color = TEAL if c == '↑' else (TERRA if c in ('↓', '×') else LINE)
            f.text(x, y + 38, c, 20, color, anchor='middle', weight=700)
        if forbidden:
            f.line(80, y + 30, 1130, y + 30, TERRA, 2)
    f.text(600, 575, '例：↑ 高く評価　↓ 低く評価　・ ほぼ無関係（表の評価は説明のための例）', 14, MUTED, anchor='middle')
    f.text(600, 604, 'U(s, a, c) = Σ_i w_i(s, c)・f_i(s, a)　（式9-2）', 16, INK, anchor='middle', weight=700)
    f.text(600, 630, '制約条件：禁止行動は選択対象から除外する（式9-2の重み付き和には含めない）', 14, TERRA, anchor='middle')
    f.footer('目的関数を複数用意することが目的ではない。競合が生じたとき、どう優先順位を決めるかを観測できる構造にする。')
    return f.save('objective-conflicts')


def self_state_update(part):
    f = Figure(9, '自己表象を、行動に影響する内部状態として実装する', 'S_t が方針に入り、行動の結果で更新される', 680, part)
    f.rect(70, 225, 320, 230, fill=PALE, stroke=TERRA, rx=16)
    f.text(230, 260, '自己表象 S_t（式9-3）', 20, TERRA, anchor='middle', weight=700)
    for i, (k, v) in enumerate([('Ability', '探索の成功率・協力の能力'), ('Value', '安全・好奇心・関係の重視度'), ('Experience', '成功・失敗・他者からの評価'), ('Tendency', '危険時や未知の状況での選び方')]):
        y = 295 + i * 38
        f.text(95, y, k, 14, TERRA, weight=700)
        f.text(185, y, v, 13, INK)
    f.line(390, 340, 450, 340, TERRA, 2.5, arrow=True)
    f.box(450, 290, 290, 100, '方針 Policy', 'a_t = Policy(b_t, S_t, F, W_t)', INK, 18, sub_size=13)
    f.text(595, 420, '信念状態 b_t・目的関数 F・重み W_t も入る（式9-5）', 13, MUTED, anchor='middle')
    f.line(740, 340, 790, 340, MUTED, 2.5, arrow=True)
    f.box(790, 300, 150, 80, '行動 a_t', '', INK, 18)
    f.line(940, 340, 1000, 340, MUTED, 2.5, arrow=True)
    f.box(1000, 300, 140, 80, '環境', '', MUTED, 18)
    f.path('M1070,380 L1070,520 L680,520', MUTED, 2.2, arrow=True, dash=True)
    f.text(875, 510, '観測 o_t・結果の評価 r_t', 13, MUTED, anchor='middle')
    f.box(520, 490, 160, 60, 'Update', '', TERRA, 16)
    f.path('M520,520 L230,520 L230,455', TERRA, 2.5, arrow=True)
    f.text(600, 580, 'S_(t+1) = Update(S_t, o_t, a_t, r_t)　（式9-4）', 14, TERRA, anchor='middle', weight=700)
    f.text(600, 615, '例：探索に失敗し続けて自分の探索能力を低く評価すると、同じ環境でも以前とは異なる行動を選ぶ', 13, MUTED, anchor='middle')
    f.footer('本モデルで実装する「自分」とは、自身の状態を表現し、その表現が将来の行動を変える情報処理上の構造である。')
    return f.save('self-state-update')


def three_agents(part):
    f = Figure(9, '自己表象の効果は比較でしか測れない', '構成要素を一つずつ足した三つのモデルを同じ環境に置く', 640, part)
    base = 500
    models = [(90, 'モデルA', ['目的関数']), (430, 'モデルB', ['目的関数', '記憶']), (770, 'モデルC', ['目的関数', '記憶', '自己表象'])]
    colors = {'目的関数': TEAL, '記憶': INDIGO, '自己表象': TERRA}
    for x, name, blocks in models:
        f.text(x + 140, 225, name, 22, INK, anchor='middle', weight=700)
        for i, b in enumerate(blocks):
            y = base - (i + 1) * 72
            f.box(x, y + 4, 280, 64, b, '', colors[b], 20)
        if name == 'モデルC':
            f.rect(x - 12, base - 3 * 72 - 8, 304, 76, fill='none', stroke=TERRA, rx=12, dash=True)
            f.text(x + 140, base - 3 * 72 - 18, 'これだけ無効化して比較（アブレーション）', 14, TERRA, anchor='middle', weight=700)
    f.line(60, base + 8, 1140, base + 8, INK, 2)
    f.text(600, base + 36, '同じ環境・同じ初期条件', 17, MUTED, anchor='middle')
    for x in (380, 720):
        f.line(x, 440, x + 40, 440, MUTED, 2, arrow=True)
        f.text(x + 20, 425, '＋1要素', 13, MUTED, anchor='middle')
    f.text(600, 580, '観測：同じ失敗の回数 ／ 適応の速さ ／ 目的が競合したときの判断 ／ 行動の一貫性 ／ 環境変化への柔軟性', 15, INK, anchor='middle')
    f.footer('モデルCの性能が高いだけでは証明にならない。記憶容量・計算量・パラメータ数も揃える必要がある。')
    return f.save('three-agents')


def memory_and_narrative(part):
    f = Figure(9, '三種類の記憶からナラティブを生成し、行動へ戻す', '出来事・知識・自分についての認識を分け、物語として関係づける', 680, part)
    mems = [('エピソード記憶', '経験した具体的な出来事', '「ある場所を探索して失敗した」', TEAL), ('意味記憶', '経験から得た一般的な知識', '「協力は探索の成功率を高める」', INDIGO), ('自己記憶', '自分自身に関する情報', '「自分は協力した探索に向いている」', TERRA)]
    for i, (t, s, ex, color) in enumerate(mems):
        y = 215 + i * 100
        f.box(70, y, 360, 80, t, s, color, 18, sub_size=13)
        f.text(250, y + 95, ex, 13, MUTED, anchor='middle')
        f.curve(430, y + 40, 480, y + 40, 520, 340 + i * 30, color, 2.2)
    f.rect(520, 300, 340, 140, fill='#ffffff', stroke=INK, rx=14)
    f.text(690, 332, 'ナラティブの生成', 18, INK, anchor='middle', weight=700)
    f.text(690, 362, '「単独で探索すると失敗しやすいが、', 13, INK, anchor='middle')
    f.text(690, 382, '他者と協力することで成功できる」', 13, INK, anchor='middle')
    f.text(690, 415, '出来事の列挙ではなく、自分についての意味', 13, MUTED, anchor='middle')
    f.line(860, 370, 920, 370, MUTED, 2.2, arrow=True)
    f.box(920, 320, 220, 100, '能力評価・行動傾向', 'の抽出', TERRA, 16, sub_size=13)
    f.box(70, 540, 200, 50, '次の意思決定', '', INK, 16)
    f.path('M1030,420 L1030,565 L270,565', TERRA, 2.2, arrow=True, dash=True)
    f.text(650, 553, '次の意思決定に利用する（文章として保存するだけでは機能が限定的）', 13, TERRA, anchor='middle')
    f.text(600, 625, '実際の行動履歴と、生成されたナラティブは区別して保持する。後からの説明が本当の原因と異なることがある', 13, MUTED, anchor='middle')
    f.footer('第7回と第8回の、記憶とナラティブが自己の連続性を形成するという仮説の計算機上での近似。')
    return f.save('memory-and-narrative')


def measuring_integration(part):
    f = Figure(9, '情報統合をどのように測定するのか', '工学的な指標で内部の相互依存を調べる。相関は因果的統合ではなく、指標はΦではない', 660, part)
    methods = [('相互情報量', ['ある目的関数の状態を知ると、', '別の目的関数の状態が', 'どの程度分かるか'], TEAL),
               ('無効化', ['一つの目的関数を止め、', '他の目的関数や行動選択が', 'どれだけ変わるかを測る'], INDIGO),
               ('フィードバック除去', ['自己表象へ戻る経路を切り、', '内部状態や行動の変化を', '比較する'], TERRA)]
    for i, (t, items, color) in enumerate(methods):
        x = 70 + i * 360
        f.rect(x, 215, 340, 230, fill='#ffffff', stroke=color)
        f.text(x + 170, 255, t, 20, color, anchor='middle', weight=700)
        f.lines(x + 170, 300, items, 14, INK, anchor='middle', gap=26)
        if i == 0:
            f.circ(x + 120, 405, 14, TEAL)
            f.line(x + 134, 405, x + 206, 405, TEAL, 2, both=True)
            f.circ(x + 220, 405, 14, TEAL)
        elif i == 1:
            f.circ(x + 120, 405, 14, LINE)
            f.cross(x + 120, 405, 8, INDIGO, 2.5)
            f.line(x + 134, 405, x + 206, 405, INDIGO, 2, arrow=True)
            f.circ(x + 220, 405, 14, INDIGO)
        else:
            f.rect(x + 100, 390, 140, 30, fill='#ffffff', stroke=TERRA, rx=8)
            f.text(x + 170, 410, '自己表象', 13, TERRA, anchor='middle', weight=700)
            f.cross(x + 170, 375, 8, TERRA, 2.5)
    f.rect(150, 480, 900, 110, fill='#ffffff', stroke=TERRA, rx=12, dash=True)
    f.text(600, 510, '注意', 15, TERRA, anchor='middle', weight=700)
    f.text(600, 538, '相関があっても、共通の入力で同時に変化しているだけかもしれない（因果的な統合とは別）', 13, INK, anchor='middle')
    f.text(600, 562, '工学的な指標が大きくても、IITのΦが大きいとは限らない。Φの厳密な評価は小規模な系から行う', 13, INK, anchor='middle')
    f.footer('情報処理の統合と、現象的意識の存在は区別する。')
    return f.save('measuring-integration')


def narrative_input(part):
    f = Figure(9, '物語による自己の更新を計算機で検証する', '構造化した代替経験を入力し、自己評価と行動方針の変化を測定する', 680, part)
    f.rect(60, 205, 1080, 110, fill='none', stroke=LINE, rx=16, dash=True)
    for i, label in enumerate(['失敗の繰り返し', '自己評価の低下', '挑戦を避ける']):
        x = 90 + i * 200
        f.box(x, 230, 180, 60, label, '', MUTED, 15)
        if i < 2:
            f.line(x + 180, 260, x + 200, 260, MUTED, 2, arrow=True)
    f.text(890, 266, 'エージェントの状態（測定の出発点）', 15, INK, anchor='middle', weight=700)
    f.line(350, 360, 350, 318, TERRA, 2.5, arrow=True)
    f.text(365, 345, '入力', 13, TERRA, anchor='start', weight=700)
    f.rect(70, 360, 560, 200, fill='#ffffff', stroke=TERRA, rx=14)
    f.text(350, 392, '物語に相当する構造化データ', 16, TERRA, anchor='middle', weight=700)
    cells = [('初期状態', '別のエージェントが失敗している'), ('行動', '別の戦略を試す'), ('結果', '以前より高い成果を得る'), ('解釈', '失敗は能力の欠如ではなく戦略の不適合')]
    for i, (k, v) in enumerate(cells):
        y = 420 + i * 32
        f.text(100, y, k, 13, TERRA, weight=700)
        f.text(180, y, v, 13, INK)
    f.line(630, 460, 700, 460, TERRA, 2.5, arrow=True)
    f.rect(700, 390, 430, 140, fill='#ffffff', stroke=INK, rx=14)
    f.text(915, 418, '測定', 17, INK, anchor='middle', weight=700)
    f.lines(730, 450, ['・失敗に対する解釈が変わるか', '・自分の能力への評価が変わるか', '・同じ状況で異なる行動を選ぶか'], 13, INK, gap=26)
    f.text(600, 600, '入力すれば必ず重みが変わる設計では、結果が最初から決まっている。検証すべきは、物語から何を抽出し、どう反映するかの処理', 13, TERRA, anchor='middle')
    f.text(600, 624, '最初は文章ではなく構造化データで与えるほうが、効果を検証しやすい', 13, MUTED, anchor='middle')
    f.footer('物語から得た情報が実際の環境で有効とは限らない。どの条件で適応的な行動につながるかも検証する。')
    return f.save('narrative-input')


def architecture(part):
    f = Figure(9, '実装アーキテクチャ', '外周は観測から行動までの循環、中央は自己表象を核とする層', 780, part)
    outer = {'環境': (150, 460, MUTED), '観測処理': (330, 240, TEAL), '世界モデル': (600, 240, TEAL), '目的関数群': (870, 240, INDIGO), '調停処理': (1050, 460, INDIGO), '行動選択': (600, 690, INK)}
    for label, (x, y, color) in outer.items():
        f.box(x - 90, y - 32, 180, 64, label, '', color, 20)
    f.line(200, 428, 290, 272, MUTED, 2.2, arrow=True)
    f.line(420, 240, 510, 240, MUTED, 2.2, arrow=True)
    f.line(690, 240, 780, 240, MUTED, 2.2, arrow=True)
    f.line(910, 272, 1000, 428, MUTED, 2.2, arrow=True)
    f.line(1000, 492, 690, 668, MUTED, 2.2, arrow=True)
    f.line(510, 668, 230, 492, MUTED, 2.2, arrow=True)
    f.box(500, 407, 200, 66, '自己表象', '', TERRA, 20, fill=PALE)
    f.box(625, 315, 150, 50, '分人', '', TERRA, 18)
    f.box(355, 532, 150, 56, '記憶', '', INDIGO, 18)
    f.box(695, 532, 150, 56, 'ナラティブ', '', INDIGO, 18)
    f.line(470, 532, 560, 473, INDIGO, 2, arrow=True)
    f.line(730, 532, 640, 473, INDIGO, 2, arrow=True)
    f.line(505, 560, 695, 560, INDIGO, 2, arrow=True)
    f.text(600, 552, '整理', 13, MUTED, anchor='middle')
    f.line(665, 365, 645, 407, TERRA, 2, both=True)
    f.text(672, 392, '共有', 13, TERRA, anchor='start')
    f.line(775, 340, 960, 440, TERRA, 2, arrow=True, dash=True)
    f.line(700, 440, 960, 455, TERRA, 2, arrow=True, dash=True)
    f.text(830, 418, '重みと優先順位に影響', 13, TERRA, anchor='middle')
    f.line(560, 407, 590, 272, TERRA, 2, arrow=True, dash=True)
    f.text(548, 345, '予測に影響', 13, TERRA, anchor='end')
    f.line(530, 672, 450, 590, INDIGO, 2, arrow=True, dash=True)
    f.text(450, 650, '結果を記録', 13, INDIGO, anchor='end')
    f.footer('各要素が相互に影響し循環する構造が必要になる。自己表象→世界モデルの破線は第8回の循環（図8-11）に対応する。')
    return f.save('architecture')


def explicit_vs_llm(part):
    f = Figure(9, '最初から大規模言語モデルを使う必要はない', '検証したい機能と、それを実現する技術を分ける', 660, part)
    f.rect(70, 215, 500, 300, fill='#ffffff', stroke=TEAL)
    f.text(320, 252, '明示的な状態遷移モデル', 20, TEAL, anchor='middle', weight=700)
    for i, t in enumerate(['どの目的関数がどの程度重視されたか', '自己表象がどのように更新されたか', '更新が行動選択にどう影響したか']):
        y = 300 + i * 48
        f.check(100, y - 18, 24, TEAL)
        f.text(140, y, t, 15, INK)
    f.text(320, 470, '内部状態を直接観測し、追跡できる', 14, TEAL, anchor='middle', weight=700)
    f.rect(630, 215, 500, 300, fill='#ffffff', stroke=TERRA)
    f.text(880, 252, '大規模言語モデルを中心に据える', 20, TERRA, anchor='middle', weight=700)
    f.rect(680, 280, 400, 40, fill=SOFT, stroke=SOFT, rx=20)
    f.text(880, 306, '「私は慎重な性格です」', 15, INK, anchor='middle', weight=700)
    for i, t in enumerate(['内部状態を反映しているのか', '過去の会話の表現を再利用しているのか', '文脈上もっともらしい文章を生成しただけか']):
        y = 360 + i * 36
        f.text(700, y, '？', 16, TERRA, weight=700)
        f.text(730, y, t, 14, INK)
    f.text(880, 480, '発言と内部の情報処理を区別しにくい', 14, TERRA, anchor='middle', weight=700)
    f.text(600, 570, 'LLMは、ナラティブの生成や自然言語による物語の理解など、後の段階で利用する', 15, INK, anchor='middle')
    f.footer('自己表象の成立条件を調べる目的に限れば、単純な計算モデルから始めるほうが適している。')
    return f.save('explicit-vs-llm')


def success_criteria(part):
    f = Figure(9, '自己表象が機能していると判断する五つの条件', 'すべて、自己表象が行動へ与える因果的な影響を問う', 690, part)
    rows = [('経験から更新される', '成功や失敗で能力・価値観の内部状態が変わる'),
            ('将来の行動へ影響する', '内部状態が変わると、同じ状況で異なる行動を選ぶ'),
            ('複数の目的関数を横断して使われる', '能力の自己評価が好奇心・安全・承認の判断に及ぶ'),
            ('分人が変わっても記憶と自己表象を共有する', '異なる文脈の行動が同じ履歴として関係づけられる'),
            ('無効化すると行動が観測可能に変わる', '付加情報なら変わらない。組み込まれていれば変わる')]
    for i, (t, s) in enumerate(rows):
        y = 225 + i * 62
        f.check(80, y - 20)
        f.text(130, y + 2, t, 20, INK, weight=700)
        f.text(600, y + 2, s, 16, MUTED)
    f.line(60, 545, 1140, 545, LINE, 1)
    f.rect(80, 565, 1040, 56, fill='#ffffff', stroke=TERRA, rx=12, dash=True)
    f.text(600, 600, '五つを満たしても、人間と同じ主観的な自己意識が成立したことの証明にはならない。', 17, TERRA, anchor='middle', weight=700)
    f.footer('「私は自分を持っています」と発言できることは、条件に含まれない。')
    return f.save('success-criteria')


# ---------------------------------------------------------------------------
# 連載の地図
# ---------------------------------------------------------------------------

def series_map(part):
    f = Figure(1, '連載の地図', '全9回・4部の流れ', 620, part)
    chapters = [(1, '境界', '現実と仮想、肉体と自分'), (2, '意識と自分', '認識する働きと表象'), (3, '目的関数', '交差点に生まれる自己'),
                (4, '予測', '何を優先するか'), (5, '統合', '関係の中の自分'), (6, '感じること', 'ハードプロブレム'),
                (7, '分人', '複数の自分と拡張'), (8, '物語', '目的関数の学習と修復'), (9, '計算機', '機能的近似と検証')]
    parts = [('第I部 境界を問う', [0, 1], TEAL), ('第II部 自己のモデル', [2, 3, 4], TERRA), ('第III部 体験と複数の自己', [5, 6, 7], INDIGO), ('第IV部 計算機で確かめる', [8], MUTED)]
    xs = [120 + i * 120 for i in range(9)]
    y = 360
    for label, idx, color in parts:
        x0, x1 = xs[idx[0]] - 50, xs[idx[-1]] + 50
        f.line(x0, y - 80, x1, y - 80, color, 4)
        f.text((x0 + x1) / 2, y - 92, label, 14, color, anchor='middle', weight=700)
    for i in range(8):
        f.line(xs[i] + 26, y, xs[i + 1] - 26, y, MUTED, 2, arrow=True)
    for (n, title, sub), x in zip(chapters, xs):
        color = next(c for _, idx, c in parts if n - 1 in idx)
        f.circ(x, y, 24, '#ffffff')
        f.circ(x, y, 24, color, fill=False, width=2.5)
        f.text(x, y + 6, str(n), 17, color, anchor='middle', weight=700)
        f.text(x, y + 50, title, 15, INK, anchor='middle', weight=700)
        f.text(x, y + 70, sub, 11, MUTED, anchor='middle')
    f.text(600, 500, '「自分」は発見されるのではなく、情報処理によって構築される', 17, INK, anchor='middle', weight=700)
    f.text(600, 528, '各回は独立した読み物であり、末尾の一段落が次回へつながる', 14, MUTED, anchor='middle')
    f.footer('第1回で仮説を立て、第3〜5回でモデルを組み、第6〜8回で体験と複数の自己を扱い、第9回で計算機に載せる。')
    return f.save('series-map')


# ---------------------------------------------------------------------------
# 追加の概念図
# ---------------------------------------------------------------------------

def emotion_quadrant(part):
    f = Figure(1, '対象の存在と、感情の現実性は別の問いである', '仮想の対象に対しても、現実の感情が生じる', 660, part)
    x0, y0, w, h = 260, 215, 680, 340
    f.rect(x0, y0, w / 2, h / 2, fill='#ffffff', stroke=LINE, rx=0)
    f.rect(x0 + w / 2, y0, w / 2, h / 2, fill=PALE, stroke=TEAL, rx=0)
    f.rect(x0, y0 + h / 2, w / 2, h / 2, fill='#ffffff', stroke=LINE, rx=0)
    f.rect(x0 + w / 2, y0 + h / 2, w / 2, h / 2, fill='#ffffff', stroke=LINE, rx=0)
    f.text(x0 + w / 4, y0 - 14, '対象が物理的に存在する', 15, INK, anchor='middle', weight=700)
    f.text(x0 + 3 * w / 4, y0 - 14, '対象は物理的に存在しない', 15, INK, anchor='middle', weight=700)
    f.text(x0 - 16, y0 + h / 4, '感情が', 15, INK, anchor='end', weight=700)
    f.text(x0 - 16, y0 + h / 4 + 20, '生じる', 15, INK, anchor='end', weight=700)
    f.text(x0 - 16, y0 + 3 * h / 4, '感情が', 15, MUTED, anchor='end')
    f.text(x0 - 16, y0 + 3 * h / 4 + 20, '生じない', 15, MUTED, anchor='end')
    f.lines(x0 + w / 4, y0 + 70, ['親しい人との別れ', '現実の対象・現実の感情'], 15, INK, anchor='middle', gap=26)
    f.lines(x0 + 3 * w / 4, y0 + 60, ['育てたキャラクターの喪失', 'SNSでの評価や批判', '仮想の対象・現実の感情'], 15, TEAL, anchor='middle', gap=26, weight=700)
    f.lines(x0 + w / 4, y0 + h / 2 + 80, ['通り過ぎる見知らぬ物体'], 15, MUTED, anchor='middle')
    f.lines(x0 + 3 * w / 4, y0 + h / 2 + 80, ['操作していない背景の人物'], 15, MUTED, anchor='middle')
    f.text(600, 595, '感情の現実性は、対象の存在ではなく、感覚情報・記憶・予測から構築された対象への反応で決まる', 14, MUTED, anchor='middle')
    f.footer('右上の象限が、意識は物理的な実体そのものではなく、構築された対象に反応することを示す。')
    return f.save('emotion-quadrant')


def score_dynamics(part):
    f = Figure(2, '自分らしさスコアは状況で動く', '痛みは部位への注意を跳ね上げ、習熟は道具を身体の延長にする', 660, part)
    x0, x1, y0, y1 = 110, 1000, 540, 240
    f.line(x0, y0, x1, y0, INK, 1.5, arrow=True)
    f.line(x0, y0, x0, y1, INK, 1.5, arrow=True)
    f.text(x1 + 10, y0 + 6, '時間', 15, INK)
    f.text(x0 + 12, y1 - 6, '自分らしさスコア', 15, INK)
    f.line(x0, 270, x1 - 40, 270, TEAL, 3.5)
    f.text(x1 - 30, 275, '脳・心臓：常に高い', 14, TEAL, weight=700)
    f.path(f'M{x0},480 L430,480 C440,480 445,330 470,330 L520,330 C545,330 550,470 560,472 L{x1 - 40},472', TERRA, 3.5)
    f.text(495, 312, '痛みが生じる', 14, TERRA, anchor='middle', weight=700)
    f.text(x1 - 30, 478, '普段は意識しない部位', 14, TERRA, weight=700)
    f.path(f'M{x0},520 C400,520 650,350 {x1 - 40},340', INDIGO, 3.5)
    f.text(x1 - 30, 345, '習熟した道具', 14, INDIGO, weight=700)
    f.text(600, 600, 'スコアは対象ごとに異なり、同じ対象でも状況で変わる。単一の数値が脳内にあるという主張ではない', 14, MUTED, anchor='middle')
    f.footer('第7回で、この考え方を肉体の外側の対象へ拡張し、五つの要素で説明する。')
    return f.save('score-dynamics')


def weight_drift(part):
    f = Figure(3, '目的関数の重みは、時間でも文脈でも変わる', '年齢に伴う推移と、同じ時点での状況による違い', 640, part)
    f.panel(60, 205, 640, 380, '年齢に伴う重みの推移')
    x0, x1, base, top = 110, 660, 520, 280
    f.line(x0, base, x1, base, INK, 1.5, arrow=True)
    f.line(x0, base, x0, top, INK, 1.5, arrow=True)
    for x, label in [(150, '20代'), (380, '40代'), (610, '60代')]:
        f.text(x, base + 24, label, 14, MUTED, anchor='middle')
    f.path(f'M{x0 + 20},300 C300,310 450,420 {x1 - 30},460', TERRA, 3.5)
    f.text(640, 488, '承認・競争', 14, TERRA, anchor='end', weight=700)
    f.path(f'M{x0 + 20},470 C300,460 450,350 {x1 - 30},305', TEAL, 3.5)
    f.text(640, 298, '健康・家族', 14, TEAL, anchor='end', weight=700)
    f.text(380, 560, '価値観の変化は、重み付けの変化と自己表象の更新として説明できる', 13, MUTED, anchor='middle')
    f.panel(740, 205, 400, 380, '同じ時点での文脈の違い')
    base2 = 500
    for i, (ctx, vals) in enumerate([('職場', [120, 40, 50]), ('家庭', [40, 130, 45]), ('趣味', [35, 45, 135])]):
        cx = 800 + i * 120
        for j, (v, color) in enumerate(zip(vals, [TERRA, TEAL, INDIGO])):
            f.bar(cx - 36 + j * 26, base2, 22, v, color)
        f.text(cx, base2 + 24, ctx, 14, INK, anchor='middle', weight=700)
    f.line(780, base2, 1120, base2, INK, 1.5)
    for j, (name, color) in enumerate([('効率・成果', TERRA), ('愛着・安定', TEAL), ('好奇心・楽しさ', INDIGO)]):
        f.rect(770, 245 + j * 24, 14, 14, fill=color, stroke=color, rx=3)
        f.text(792, 257 + j * 24, name, 12, INK)
    f.text(940, 560, 'どれか一つだけが本当の自分ではない', 13, MUTED, anchor='middle')
    f.footer('右の文脈による違いは、第7回の「分人」につながる。')
    return f.save('weight-drift')


def stairs(part):
    f = Figure(4, '予測が先にあり、感覚入力はそれと比べられる', '階段を下りる足は、次の段の高さを予測して動いている', 600, part)
    for px, label, match in [(60, '予測どおり', True), (620, '予測と違う', False)]:
        f.panel(px, 205, 520, 320, label)
        bx, by = px + 40, 450
        for i in range(4):
            x, y = bx + i * 80, by - i * 40
            f.rect(x, y, 80, 40 * (i + 1) + 10, fill=SOFT, stroke=LINE, rx=0)
        fx = bx + 80 * 3 + 40
        fy = by - 40 * 3
        f.rect(fx - 40, fy - 58, 30, 50, fill='#ffffff', stroke=INK, rx=8)
        f.text(fx - 25, fy - 30, '人', 14, INK, anchor='middle')
        tx, ty = fx + 70, fy + 40
        if match:
            f.rect(tx - 10, ty, 90, 50, fill=SOFT, stroke=LINE, rx=0)
            f.rect(tx - 10, ty, 90, 50, fill='none', stroke=TEAL, rx=0, dash=True)
            f.text(tx + 35, ty - 8, '予測した段', 12, TEAL, anchor='middle')
            f.text(px + 260, 505, '差がない → 意識せず歩き続ける', 14, TEAL, anchor='middle', weight=700)
        else:
            f.rect(tx - 10, ty, 90, 50, fill='none', stroke=TEAL, rx=0, dash=True)
            f.text(tx + 35, ty - 8, '予測した段', 12, TEAL, anchor='middle')
            f.cross(tx + 35, ty + 25, 12, TERRA, 3)
            f.text(tx + 35, ty + 70, '段がない', 12, TERRA, anchor='middle', weight=700)
            f.text(px + 260, 505, '予測誤差 → 身体が大きく反応する', 14, TERRA, anchor='middle', weight=700)
        f.curve(fx - 25, fy - 60, fx + 20, fy - 90, tx + 35, ty - 20, MUTED, 1.8, dash=True)
    f.footer('脳は感覚情報を受け取ってから世界を理解するのではなく、感覚入力に先立って予測を生成している。')
    return f.save('stairs')


def cold_room(part):
    f = Figure(4, '予測を変えるか、入力を変えるか', '寒い部屋の例。不整合を減らす方法は内部モデルの修正だけではない', 600, part)
    f.box(470, 215, 260, 80, '感覚入力：寒い', '予測との不整合', INK, 20, sub_size=13)
    f.curve(470, 255, 330, 255, 250, 320, TEAL, 2.5)
    f.curve(730, 255, 870, 255, 950, 320, TERRA, 2.5)
    f.box(90, 320, 320, 90, '内部モデルを修正する', '「室温は低い」と認識を更新する', TEAL, 19, sub_size=13)
    f.box(790, 320, 320, 90, '行動で入力を変える', '暖房をつける、衣服を足す', TERRA, 19, sub_size=13)
    f.line(250, 410, 250, 460, TEAL, 2, arrow=True)
    f.line(950, 410, 950, 460, TERRA, 2, arrow=True)
    f.text(250, 490, '予測は合うが、寒さは解消しない', 14, TEAL, anchor='middle', weight=700)
    f.text(950, 490, '身体が受け取る感覚入力そのものが変わる', 14, TERRA, anchor='middle', weight=700)
    f.text(600, 545, '知覚と行動を一体として扱う考え方が、能動的推論につながる', 14, MUTED, anchor='middle')
    f.footer('自由エネルギー原理の中心的な考え方。システムは世界への働きかけによって予測と観測の関係を変えられる。')
    return f.save('cold-room')


def unity_of_experience(part):
    f = Figure(5, '一つの体験は分割できない', 'IITは意識体験の統一性と不可分性から出発する', 680, part)
    f.text(190, 225, '異なる経路で処理される情報', 15, MUTED, anchor='middle')
    items = [('文字の形', TEAL), ('文章の意味', TEAL), ('周囲の音', INDIGO), ('身体の感覚', TERRA)]
    for i, (label, color) in enumerate(items):
        y = 265 + i * 70
        f.tag(80, y, 220, 44, label, color, 16)
        f.curve(300, y + 22, 420, y + 22, 520, 395, color, 2.2)
    f.blob(760, 395, 230, TEAL, 0.35)
    f.circ(760, 395, 170, TEAL, fill=False, width=2.5, dash=True)
    f.text(760, 300, '一つの体験', 22, TEAL, anchor='middle', weight=700)
    for (label, color), (dx, dy) in zip(items, [(-70, -40), (70, -40), (-70, 50), (70, 50)]):
        f.circ(760 + dx, 395 + dy, 34, '#ffffff')
        f.circ(760 + dx, 395 + dy, 34, color, fill=False, width=2)
        f.text(760 + dx, 395 + dy + 5, label, 12, INK, anchor='middle', weight=700)
    f.line(760, 240, 760, 550, TERRA, 3, dash=True)
    f.cross(760, 480, 12, TERRA, 3.5)
    f.text(760, 600, '独立した複数の体験には分割できない', 15, TERRA, anchor='middle', weight=700)
    f.footer('大量の情報を処理しているだけでは意識の成立条件を説明できない。IITは因果的な統合構造に注目する。')
    return f.save('unity-of-experience')


def weights_vs_structure(part):
    f = Figure(5, '重みの変化と、結合構造の変化は別の層にある', '重みが変わっても、因果的な構造が変わらなければΦが変わるとは限らない', 640, part)
    for px, title, change_struct in [(60, '重みだけが変わる', False), (620, '結合構造も変わる', True)]:
        f.panel(px, 205, 520, 350, title)
        base = 345
        f.text(px + 260, 272, '重みの層  w(t)', 13, MUTED, anchor='middle')
        for k, (vals, color) in enumerate([([70, 40, 55], TEAL), ([35, 75, 50], TERRA)]):
            ox = px + 110 + k * 230
            for j, v in enumerate(vals):
                f.bar(ox + j * 26, base, 20, v, color)
            f.text(ox + 36, base + 18, 't₁' if k == 0 else 't₂', 12, MUTED, anchor='middle')
        f.line(px + 230, base - 30, px + 290, base - 30, MUTED, 1.5, arrow=True)
        f.text(px + 260, 398, '結合構造の層  A(t)', 13, MUTED, anchor='middle')
        for k in range(2):
            ox = px + 140 + k * 230
            pts = [(ox, 428), (ox + 60, 428), (ox + 30, 478)]
            edges = [(0, 1), (1, 2), (2, 0)] if (k == 0 or not change_struct) else [(0, 1), (1, 2)]
            for a, b in edges:
                f.line(*pts[a], *pts[b], INDIGO, 2, both=True)
            if change_struct and k == 1:
                f.line(*pts[2], *pts[0], LINE, 2, dash=True)
            for x, y in pts:
                f.circ(x, y, 10, '#ffffff')
                f.circ(x, y, 10, INDIGO, fill=False, width=2)
        f.line(px + 230, 453, px + 290, 453, MUTED, 1.5, arrow=True)
        f.text(px + 260, 532, 'Φは変わるとは限らない' if not change_struct else 'Φが変わり得る', 15, TEAL if not change_struct else TERRA, anchor='middle', weight=700)
    f.footer('Φはシステムの因果的な構造に依存する。重みの変化が状態遷移や相互作用を変えるときに、統合構造が変わる。')
    return f.save('weights-vs-structure')


def sleep_anesthesia(part):
    f = Figure(5, '覚醒・睡眠・麻酔は、活動の量だけでは分けられない', '神経活動の量と、情報処理の統合の程度は別の軸である', 640, part)
    x0, x1, y0, y1 = 150, 1000, 530, 240
    f.line(x0, y0, x1, y0, INK, 1.5, arrow=True)
    f.line(x0, y0, x0, y1, INK, 1.5, arrow=True)
    f.text(x1 + 10, y0 + 6, '神経活動の量', 15, INK)
    f.text(x0 - 10, y1 - 8, '統合の程度', 15, INK, anchor='end')
    for x, y, label, color in [(820, 290, '覚醒', TEAL), (560, 470, '深い睡眠', INDIGO), (430, 490, '全身麻酔', TERRA), (700, 380, '夢を見る睡眠', INDIGO)]:
        f.blob(x, y, 60, color, 0.4)
        f.circ(x, y, 10, color)
        f.text(x + 18, y + 5, label, 15, INK, weight=700)
    f.line(430, 455, 760, 455, LINE, 1.5, dash=True)
    f.text(600, 445, '活動の量は近くても、統合の程度が違う', 13, MUTED, anchor='middle')
    f.text(600, 585, '脳は睡眠中にも活動している。活動が存在することと、覚醒時と同じ体験が成立することは同じではない', 13, MUTED, anchor='middle')
    f.footer('摂動複雑性指標（PCI）は応答の複雑さを測る指標であり、Φそのものではない。位置は概念的な目安である。')
    return f.save('sleep-anesthesia')


def three_systems(part):
    f = Figure(5, '統合の仮説を検証する三つのシステム', '目的関数が独立している構成から、相互作用と自己表象を順に加える', 640, part)
    for px, title, mode in [(60, '独立', 0), (430, '相互作用あり', 1), (800, '相互作用と自己表象', 2)]:
        f.panel(px, 205, 340, 350, title)
        pts = [(px + 110, 300), (px + 230, 300), (px + 170, 390)]
        names = ['安全性', '効率', '好奇心']
        if mode >= 1:
            for a, b in [(0, 1), (1, 2), (2, 0)]:
                f.line(*pts[a], *pts[b], INDIGO, 2, both=True)
        for (x, y), n in zip(pts, names):
            f.circ(x, y, 26, '#ffffff')
            f.circ(x, y, 26, TEAL, fill=False, width=2.5)
            f.text(x, y + 5, n, 12, TEAL, anchor='middle', weight=700)
        if mode == 2:
            f.box(px + 95, 455, 150, 50, '自己表象', '', TERRA, 16, fill=PALE)
            f.line(px + 170, 416, px + 170, 455, TERRA, 2, both=True)
            f.curve(px + 245, 480, px + 300, 440, px + 250, 320, TERRA, 1.5, dash=True)
            f.curve(px + 95, 480, px + 40, 440, px + 90, 320, TERRA, 1.5, dash=True)
        else:
            f.text(px + 170, 480, '各目的関数は他の内部状態に影響しない' if mode == 0 else '安全性の評価が好奇心の重みを変える', 12, MUTED, anchor='middle')
        f.text(px + 170, 530, ['独立に計算', '相互作用を導入', '自己表象を導入'][mode], 14, INK, anchor='middle', weight=700)
    f.footer('行動の違いを観測する。行動の複雑さと因果的な情報統合は同じ指標ではない。第9回のモデルA/B/Cと対になる。')
    return f.save('three-systems')


def hypothesis_to_test(part):
    f = Figure(6, '仮説を、検証できる形に変換する', '理論の文章を実装し、比較実験で支持するか反証する', 640, part)
    steps = [('理論の文章', '「自己表象は行動の一貫性を高める」', TEAL), ('実装', '自己表象を内部状態 S_t として定義', INDIGO), ('比較実験', '自己表象あり／なしで同じ環境を走らせる', INDIGO)]
    for i, (t, s, color) in enumerate(steps):
        x = 70 + i * 300
        f.box(x, 250, 260, 100, t, s, color, 19, sub_size=12)
        if i < 2:
            f.line(x + 260, 300, x + 300, 300, MUTED, 2.2, arrow=True)
    f.line(930, 300, 970, 300, MUTED, 2.2, arrow=True)
    f.box(970, 215, 170, 70, '支持', '一貫性が上がる', TEAL, 17, sub_size=12)
    f.box(970, 315, 170, 70, '反証', '変わらない', TERRA, 17, sub_size=12)
    f.line(970, 300, 970, 250, MUTED, 1.5)
    f.line(970, 300, 970, 350, MUTED, 1.5)
    f.rect(150, 430, 900, 70, fill='#ffffff', stroke=TERRA, rx=12, dash=True)
    f.text(600, 458, 'どちらの結果でも、主観的な「私」という体験が成立したことの証明にはならない', 15, TERRA, anchor='middle', weight=700)
    f.text(600, 484, '検証できるのは、自己がどのような情報処理によって成立するかという機能的な条件である', 13, MUTED, anchor='middle')
    f.text(600, 560, '目的関数の競合の調停方法や、相互作用の変更が自己表象と行動に与える影響も同じ手順で調べられる', 13, MUTED, anchor='middle')
    f.footer('機能的な意識モデルの実装は、意識の存在を証明する試みではなく、仮説を動かして確かめる試みである。')
    return f.save('hypothesis-to-test')


def extension_routes(part):
    f = Figure(7, '自己の拡張には三つの経路がある', 'すべての拡張が同じ仕組みで成立しているわけではない', 660, part)
    cols = [('身体運動の制御', ['道具', '自動車', 'ゲームキャラクター'], '鍵：制御できる・結果を予測できる', TEAL),
            ('社会的な自己表象', ['SNSアカウント', 'VTuberのアバター'], '鍵：他者からの評価が自己評価に入る', INDIGO),
            ('記憶・価値観との結びつき', ['作品', '所有物'], '鍵：記憶・価値観・自己評価との結びつき', TERRA)]
    for i, (title, items, key, color) in enumerate(cols):
        x = 70 + i * 360
        f.rect(x, 215, 340, 250, fill='#ffffff', stroke=color)
        f.text(x + 170, 252, title, 19, color, anchor='middle', weight=700)
        for j, it in enumerate(items):
            f.tag(x + 60, 280 + j * 44, 220, 34, it, color, 15)
        f.text(x + 170, 440, key, 14, MUTED, anchor='middle')
        f.curve(x + 170, 465, x + 170, 520, 520 + i * 80, 540, color, 2.2)
    f.box(470, 540, 260, 60, '自己表象と結びつく', '', INK, 18)
    f.footer('目的関数モデルでは三つを「自己表象が肉体外の対象と結びつく現象」として統一的に扱い、仕組みの違いは図7-7の要素で表す。')
    return f.save('extension-routes')


def identity_band(part):
    f = Figure(7, '変わるものと、つなぐもの', '十年前の自分と現在の自分は、性質の一致ではなく情報処理の連続性でつながる', 640, part)
    f.text(160, 232, '十年前の自分', 17, INK, anchor='middle', weight=700)
    f.text(1040, 232, '現在の自分', 17, INK, anchor='middle', weight=700)
    f.text(70, 300, '変わるもの（例）', 15, TERRA, weight=700)
    for j, (label, a, b) in enumerate([('価値観', '承認・競争', '健康・家族'), ('能力', '未熟', '熟練'), ('人間関係・役割', '学生', '親・管理者'), ('関心の対象', '競技', '育てること')]):
        y = 300 + j * 36
        f.text(230, y + 4, label, 13, MUTED)
        f.rect(370, y - 12, 180, 26, fill='#ffffff', stroke=TERRA, rx=13)
        f.text(460, y + 5, a, 13, INK, anchor='middle')
        f.line(560, y, 630, y, TERRA, 1.5, arrow=True, dash=True)
        f.rect(640, y - 12, 180, 26, fill='#ffffff', stroke=TERRA, rx=13)
        f.text(730, y + 5, b, 13, INK, anchor='middle')
    f.text(70, 480, 'つなぐもの', 15, TEAL, weight=700)
    f.hgradient(230, 462, 820, 70, TEAL, 0.25, 0.25, rx=35)
    f.text(640, 492, '記憶 ／ ナラティブ ／ 身体の連続性 ／ 他者からの認識', 16, TEAL, anchor='middle', weight=700)
    f.text(640, 518, '過去の経験を現在の自己と結びつけ、将来の自分を予測する', 13, INK, anchor='middle')
    f.text(600, 580, '自己は、変化しないから連続しているのではない。変化した経験が次の自己の形成に影響し続けることで連続性を持つ', 13, MUTED, anchor='middle')
    f.footer('記憶の連続性と主観的な意識の連続性が同じものかどうかは、未解決の問題として残る。')
    return f.save('identity-band')


def explanation_vs_story(part):
    f = Figure(8, '説明が渡す情報と、物語が渡す情報', '命題一つと、状況・葛藤・結果の追体験', 600, part)
    f.panel(60, 205, 480, 320, '説明')
    f.rect(100, 290, 400, 50, fill=SOFT, stroke=SOFT, rx=25)
    f.text(300, 321, '「困っている人を助けることは望ましい」', 15, INK, anchor='middle', weight=700)
    f.line(300, 345, 300, 400, MUTED, 2, arrow=True)
    f.box(200, 400, 200, 56, '知識', '命題として保持', MUTED, 17, sub_size=13)
    f.text(300, 495, '短い文章で十分だが、価値判断には結びつきにくい', 13, MUTED, anchor='middle')
    f.panel(620, 205, 520, 320, '物語')
    for i, (label, color) in enumerate([('状況', TEAL), ('葛藤', TERRA), ('行動', INDIGO), ('結果', TEAL)]):
        x = 650 + i * 120
        f.tag(x, 285, 100, 40, label, color, 15)
        if i < 3:
            f.line(x + 100, 305, x + 120, 305, MUTED, 2, arrow=True)
    f.text(880, 360, '困っている人の状況、助けると何が起きるか、助ける側の葛藤を描く', 13, MUTED, anchor='middle')
    f.line(880, 372, 880, 400, MUTED, 2, arrow=True)
    f.box(760, 400, 240, 56, '経験', '価値判断・感情と結びつく', TEAL, 17, sub_size=13)
    f.text(880, 495, '読者は状況を想像し、登場人物の判断を追体験する', 13, MUTED, anchor='middle')
    f.footer('目的関数モデルでは、この働きを目的関数の学習として捉える。')
    return f.save('explanation-vs-story')


def shared_cognition(part):
    f = Figure(8, '現実の理解と物語の理解は、同じ処理を使う', '想像・予測・更新という認知的な処理が共通している', 620, part)
    f.box(70, 240, 230, 80, '現実の出来事', '身体的な危険や責任を伴う', TEAL, 18, sub_size=13)
    f.box(70, 400, 230, 80, '物語の出来事', '現実でないと分かっている', TERRA, 18, sub_size=13)
    f.curve(300, 280, 360, 300, 420, 345, TEAL, 2.5)
    f.curve(300, 440, 360, 420, 420, 375, TERRA, 2.5)
    f.rect(420, 280, 400, 160, fill='#ffffff', stroke=INK, rx=14)
    f.text(620, 312, '共通する処理', 17, INK, anchor='middle', weight=700)
    for i, label in enumerate(['状況を想像する', '次に何が起きるかを予測する', '予想外の出来事で理解を更新する']):
        f.text(620, 345 + i * 28, label, 14, INK, anchor='middle')
    f.line(820, 360, 880, 360, MUTED, 2.2, arrow=True)
    f.box(880, 315, 250, 90, '世界モデル・自己表象', '行動と結果の関係を学習', INDIGO, 17, sub_size=13)
    f.text(600, 530, '主人公が失敗を乗り越える物語から、失敗が最終的な結果ではないという行動と結果の関係を学習できる', 13, MUTED, anchor='middle')
    f.footer('物語の理解と現実の経験は完全に同じではない。目的関数モデルでは、これを経験の間接的な学習と呼ぶ。')
    return f.save('shared-cognition')


def dividual_shift(part):
    f = Figure(8, '物語は分人の重みを変える', '仕事の分人の重みが、物語の前後でどう変わるか', 620, part)
    axes = ['競争', '達成', '挑戦', '関係', '休息']
    before = [180, 160, 50, 60, 40]
    after = [110, 130, 140, 110, 90]
    base, left, step, bw = 480, 130, 170, 40
    f.line(left - 40, base, left + step * 5, base, INK, 1.5)
    for i, ax in enumerate(axes):
        gx = left + i * step
        f.bar(gx, base, bw, before[i], LINE, 1.0)
        f.bar(gx + bw + 6, base, bw, after[i], TEAL)
        f.text(gx + bw + 3, base + 26, ax, 15, INK, anchor='middle', weight=700)
    f.rect(960, 250, 18, 18, fill=LINE, stroke=LINE, rx=3)
    f.text(988, 264, '物語を読む前', 14, INK)
    f.rect(960, 280, 18, 18, fill=TEAL, stroke=TEAL, rx=3)
    f.text(988, 294, '物語を読んだ後', 14, INK)
    f.text(1050, 350, '例：失敗から立ち直る物語、', 13, MUTED, anchor='middle')
    f.text(1050, 368, '日常系の物語に触れたあと', 13, MUTED, anchor='middle')
    f.text(600, 555, '同じ状況に直面しても、以前とは異なる判断を行う可能性がある', 14, MUTED, anchor='middle')
    f.footer('物語を読めば必ず重みが変わるわけではない。変化は目的関数の重みと自己表象の更新として捉えられる。')
    return f.save('dividual-shift')


def two_routes(part):
    f = Figure(8, '環境を変えずに、行動を変える経路がある', '世界を評価し予測する内部モデルが変われば、同じ環境への行動も変わる', 620, part)
    f.box(70, 330, 220, 90, '同じ環境', '現実の制約・身体・関係', MUTED, 20, sub_size=13)
    f.line(290, 375, 400, 375, MUTED, 2.5, arrow=True)
    f.rect(400, 300, 300, 150, fill='#ffffff', stroke=INDIGO)
    f.text(550, 340, '内部モデル', 22, INDIGO, anchor='middle', weight=700)
    f.text(550, 385, '評価基準（目的関数の重み）', 13, INK, anchor='middle')
    f.text(550, 410, '予測（世界モデル・自己表象）', 13, INK, anchor='middle')
    f.line(700, 375, 810, 375, MUTED, 2.5, arrow=True)
    f.box(810, 330, 220, 90, '行動', '', INK, 22)
    f.box(70, 215, 300, 60, '経路A：環境を変える', '転職・転居・関係の変更', TEAL, 16, sub_size=13)
    f.curve(220, 275, 200, 310, 180, 330, TEAL, 2, dash=True)
    f.box(400, 480, 300, 60, '経路B：内部モデルを変える', '物語による解釈と予測の更新', TERRA, 16, sub_size=13)
    f.line(550, 480, 550, 450, TERRA, 2.5, arrow=True)
    f.text(1050, 480, '同じ環境でも', 14, TERRA, anchor='middle', weight=700)
    f.text(1050, 500, '行動が変わり得る', 14, TERRA, anchor='middle', weight=700)
    f.footer('環境を変えることが不要だという意味ではなく、物語であらゆる問題が解決するわけでもない。')
    return f.save('two-routes')


def dividual_impl(part):
    f = Figure(9, '分人を文脈依存の混合モデルとして実装する', '三つの文脈で重みを切り替えながら、記憶と自己表象を共有する', 740, part)
    ctx = [('競争環境', '効率・達成', TEAL), ('協力環境', '信頼・関係', TERRA), ('探索環境', '好奇心・情報', INDIGO)]
    for i, (c, k, color) in enumerate(ctx):
        x = 90 + i * 360
        f.box(x, 255, 300, 70, c, f'重視：{k}', color, 18, sub_size=13)
        f.line(x + 150, 325, x + 150, 370, color, 2, arrow=True)
        f.box(x + 60, 370, 180, 50, f'w^({i + 1})', '', color, 16)
        f.curve(x + 150, 420, x + 150, 450, 560 + i * 40, 470, color, 2, arrow=True)
    f.box(380, 470, 440, 64, 'w(c) = Σ_j π_j(c)・w^(j)', '混合係数 π_j(c) は文脈 c から計算する（式9-6）', INK, 17, sub_size=13)
    f.line(600, 534, 600, 580, INK, 2, arrow=True, dash=True)
    f.rect(90, 580, 1020, 80, fill=PALE, stroke=INK, rx=14)
    f.text(600, 612, '共有する記憶・自己表象', 18, INK, anchor='middle', weight=700)
    f.text(600, 638, '文脈ごとに独立したエージェントを用意するのではなく、同じ個人の中で行動方針が切り替わる', 13, MUTED, anchor='middle')
    f.curve(600, 252, 420, 170, 240, 252, TERRA, 2, dash=True)
    f.text(420, 198, '協力環境の成功が競争環境の判断へ影響するか', 13, TERRA, anchor='middle')
    f.text(600, 685, 'ある文脈での経験が別の文脈での判断に及ぶかを観測し、分人間の情報共有を検証する', 13, MUTED, anchor='middle')
    f.footer('第7回の混合モデル（式7-2）の実装。文脈 c から混合係数 π_j(c) を計算し、重みを合成する（式9-6）。')
    return f.save('dividual-impl')


def boundary_impl(part):
    f = Figure(9, '自己の境界を計算機上で表現する', '道具は予測誤差の低下で取り込まれ、成果物は目的関数との結びつきで自己に関わる', 640, part)
    f.panel(60, 205, 520, 360, '道具の取り込み')
    x0, x1, y0, y1 = 120, 520, 500, 270
    f.line(x0, y0, x1, y0, INK, 1.5, arrow=True)
    f.line(x0, y0, x0, y1, INK, 1.5, arrow=True)
    f.text(x1 + 6, y0 + 6, '操作回数', 13, INK)
    f.text(x0 + 12, y1 - 6, '装置の動作の予測誤差', 13, INK)
    f.path(f'M{x0 + 10},290 C200,300 300,440 {x1 - 40},470', TEAL, 3.5)
    f.text(400, 350, '行動と結果の対応を学習', 13, TEAL, anchor='middle', weight=700)
    f.text(320, 540, '装置の状態を自分の行動計画に組み込める', 13, MUTED, anchor='middle')
    f.panel(620, 205, 520, 360, '成果物との結びつき')
    f.box(660, 260, 200, 70, '作成した成果物', '内部資源ではない', INDIGO, 17, sub_size=13)
    f.line(860, 295, 930, 295, INDIGO, 2.5, arrow=True)
    f.box(930, 260, 180, 70, '目的関数', '喪失を大きな損失と評価', TERRA, 17, sub_size=13)
    f.line(1020, 330, 1020, 400, TERRA, 2.5, arrow=True)
    f.box(900, 400, 240, 60, '意思決定に強く影響', '', INK, 16)
    f.text(880, 500, '身体に相当する資源でなくても、', 13, MUTED, anchor='middle')
    f.text(880, 518, '目的関数と結びつけば自己の範囲に入る', 13, MUTED, anchor='middle')
    f.footer('結びつきの程度は第7回の自分らしさスコア（式7-3）で表す。外部対象との結びつきが変わると行動が変わるかを観測する。')
    return f.save('boundary-impl')


def support_refute(part):
    f = Figure(9, '仮説を支持するためだけでなく、反証するために実験する', '想定している構造を取り除いても同じ機能が成立するなら、仮説を再検討する', 640, part)
    f.box(380, 215, 440, 70, '自己表象を取り除く（アブレーション）', '', INK, 18)
    f.line(600, 285, 600, 330, MUTED, 2.2, arrow=True)
    f.box(400, 330, 400, 60, '機能は維持されたか？', '', INDIGO, 18)
    f.curve(400, 360, 300, 360, 250, 430, TEAL, 2.5)
    f.curve(800, 360, 900, 360, 950, 430, TERRA, 2.5)
    f.text(280, 345, '低下した', 14, TEAL, anchor='middle', weight=700)
    f.text(920, 345, '維持された', 14, TERRA, anchor='middle', weight=700)
    f.box(90, 430, 320, 90, '自己表象の機能を支持', '一貫性や適応性に寄与していた', TEAL, 18, sub_size=13)
    f.box(790, 430, 320, 90, '仮説を再検討', '同じ機能を別の構造で実現できる', TERRA, 18, sub_size=13)
    f.text(600, 560, '目的関数の相互作用、共有記憶、物語による更新についても同じ論理で検証する', 13, MUTED, anchor='middle')
    f.text(600, 585, '重要なのは、理論に合うようにシステムを作ることではない', 13, MUTED, anchor='middle')
    f.footer('どちらの結果でも、意識と自己の理解は前進する。')
    return f.save('support-refute')


# ---------------------------------------------------------------------------
# 登録順（本文での登場順）。枝番とファイル名はここから決まる。
# ---------------------------------------------------------------------------

CHAPTERS = {
    1: [series_map, perception_boundary, shared_experience, emotion_quadrant, self_score_gradient, common_structure],
    2: [three_layers, consciousness_and_self, conscious_unconscious, score_dynamics, substrate_independence, criteria_question],
    3: [route_objectives, go_ai_two_evaluators, weighted_sum, intersection_of_objectives, posthoc_narrative, weight_drift, three_stages],
    4: [ambiguous_input, stairs, prediction_loop, cold_room, prediction_meets_objectives, attention_and_priority, meta_arbitration, self_representation_cycle, exploration_uncertainty],
    5: [unity_of_experience, independent_vs_integrated, phi_partition, coupled_objectives, self_objective_cycle, integrated_subset, conflict_adjustment, weights_vs_structure, sleep_anesthesia, three_systems],
    6: [functional_and_phenomenal, inverted_qualia, iit_reframing, functional_love, feedforward_vs_recurrent, three_axes, hypothesis_to_test, three_theories],
    7: [true_self_vs_dividual, dividual_weights, context_mixture, narrative_cycle, extension_routes, tool_incorporation, extended_self, unified_update, identity_band],
    8: [explanation_vs_story, narrative_as_learning, repair_flow, genre_isekai, genre_exile, genre_slice_of_life, genre_villainess, shared_cognition, immersion, dividual_shift, self_narrative_loop, social_propagation, integrated_model, two_routes],
    9: [virtual_environment, belief_state, objective_conflicts, self_state_update, three_agents, memory_and_narrative, dividual_impl, boundary_impl, measuring_integration, narrative_input, architecture, explicit_vs_llm, success_criteria, support_refute],
}


def draw_all() -> dict[int, list[str]]:
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob('*.svg'):
        stale.unlink()
    cover()
    out: dict[int, list[str]] = {}
    for number, funcs in CHAPTERS.items():
        out[number] = [fn(chr(97 + i)) for i, fn in enumerate(funcs)]
    return out


def main() -> int:
    names = draw_all()
    if '--list' in sys.argv:
        for number, files in names.items():
            for name in files:
                print(f'{number}\t{name}')
        return 0
    total = 1 + sum(len(v) for v in names.values())
    print(f'{total} illustrations written to {OUT.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
