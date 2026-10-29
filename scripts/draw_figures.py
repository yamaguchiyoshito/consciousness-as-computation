#!/usr/bin/env python3
"""Generate every SVG illustration (cover + per-chapter figures) deterministically. Stdlib only.

各図は 1200px 幅、紙色の背景、見出し行（連載コード・回番号・図番号）、題と副題、本文、脚注の順で構成する。
色だけに意味を依存させず、ラベルでも区別する。フォントは閲覧環境のものを使い、同梱しない。
"""
from __future__ import annotations
from html import escape
import math
from pathlib import Path

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
        return {TEAL: 'arrow-teal', TERRA: 'arrow-terra', INDIGO: 'arrow-indigo'}.get(color, 'arrow')

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

    def footer(self, s):
        if s:
            self.text(50, self.h - 28, s, 18, MUTED)

    def save(self, name: str) -> str:
        OUT.mkdir(parents=True, exist_ok=True)
        head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{self.h}" viewBox="0 0 1200 {self.h}" role="img" aria-labelledby="title desc">',
                f'<title id="title">{escape(self.title)}</title>', f'<desc id="desc">{escape(self.subtitle)}</desc>',
                '<defs>' + ''.join(self.defs) + '</defs>', f'<rect width="1200" height="{self.h}" rx="20" fill="{BG}"/>',
                f'<g font-family=\'{FONT}\'>']
        (OUT / name).write_text('\n'.join(head + self.body + ['</g>', '</svg>']) + '\n', encoding='utf-8')
        return name


def polar(cx, cy, r, deg, ry=None):
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + (ry if ry is not None else r) * math.sin(a)


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
    return f.save('00-cover.svg')


# ---------------------------------------------------------------------------
# 第1回
# ---------------------------------------------------------------------------

def fig01a():
    f = Figure(1, '現実とバーチャルは、知覚の手前で合流する', '脳が受け取るのは感覚情報だけである', 600, 'a')
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
    return f.save('01-a-perception-boundary.svg')


def fig01b():
    f = Figure(1, '自己認識の強さには濃淡がある', '皮膚の位置と「自分」の境界は一致しない', 580, 'b')
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
    return f.save('01-b-self-score-gradient.svg')


# ---------------------------------------------------------------------------
# 第2回
# ---------------------------------------------------------------------------

def fig02a():
    f = Figure(2, '人間を三層で捉える', '意識は構造そのものではなく、構造の上で動く処理である', 600, 'a')
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
    return f.save('02-a-three-layers.svg')


def fig02b():
    f = Figure(2, '意識は認識する働き、「自分」は認識される対象', '意識は自己表象を構築し、認識し、更新する', 620, 'b')
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
    return f.save('02-b-consciousness-and-self.svg')


# ---------------------------------------------------------------------------
# 第3回
# ---------------------------------------------------------------------------

def fig03a():
    f = Figure(3, '囲碁AIの二つの評価関数と「地」', '共通して重視する対象が、機能的な自己の原型になる', 600, 'a')
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
    return f.save('03-a-go-ai-two-evaluators.svg')


def fig03b():
    f = Figure(3, '「自分」は目的関数の交差点に生まれる', '矢印の太さが重み。向きの異なる目的が同じ対象を評価する', 760, 'b')
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
    return f.save('03-b-intersection-of-objectives.svg')


# ---------------------------------------------------------------------------
# 第4回
# ---------------------------------------------------------------------------

def fig04a():
    f = Figure(4, '予測処理の循環', '予測が先にあり、誤差が世界モデルを更新する', 640, 'a')
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
    return f.save('04-a-prediction-loop.svg')


def fig04b():
    f = Figure(4, '何が意識的な処理の対象になるのか', '予測誤差の大きさと、目的に照らした重要性の二段で選ばれる', 640, 'b')
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
            f.line(300, y, 430, y, color, 2.5, arrow=False)
            f.line(430, y, 650, y, color, 2.5)
            f.line(650, y, 730, y, color, 2.5)
            f.line(730, y, 960, y, color, 2.5)
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
    return f.save('04-b-attention-and-priority.svg')


def fig04c():
    f = Figure(4, '自己表象は予測処理と目的関数を結びつける', '三つの要素が循環し、行動の結果が三つを更新する', 660, 'c')
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
    return f.save('04-c-self-representation-cycle.svg')


# ---------------------------------------------------------------------------
# 第5回
# ---------------------------------------------------------------------------

def fig05a():
    f = Figure(5, '集約することと、相互依存することは違う', '左は分割しても働きが変わらない。右は分割すると因果構造が失われる', 640, 'a')
    f.panel(60, 205, 520, 350, '独立した処理の集合')
    for i, (label, color) in enumerate([('安全性', TEAL), ('効率', INDIGO), ('情報獲得', TERRA)]):
        x = 95 + i * 160
        f.box(x, 265, 130, 70, label, '', color, 19)
        f.line(x + 65, 335, x + 65, 420, color, 2, arrow=True)
    f.box(170, 425, 300, 60, '重み付き和  U = Σ wᵢ fᵢ', '', INK, 18)
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
    return f.save('05-a-independent-vs-integrated.svg')


def fig05b():
    f = Figure(5, '自己表象を核とする循環', '「自分」は結果であり、同時に次の処理に影響する内部状態である', 640, 'b')
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
        # shorten to box edges (approximate by trimming fixed lengths)
        f.line(x1 + ux * 125, y1 + uy * 48, x2 - ux * 125, y2 - uy * 48, MUTED, 2.2, arrow=True)
    f.text(cx, cy - 10, '「自分」は情報処理の出力であると同時に、', 16, INK, anchor='middle')
    f.text(cx, cy + 14, '将来の情報処理に影響する内部状態である', 16, INK, anchor='middle')
    f.text(cx, cy + 44, '循環が続くことで自己は構築され続ける', 14, MUTED, anchor='middle')
    f.footer('目的関数の統合とIITの因果的な情報統合は同一ではない。両者の対応は本連載の仮説である。')
    return f.save('05-b-self-objective-cycle.svg')


# ---------------------------------------------------------------------------
# 第6回
# ---------------------------------------------------------------------------

def fig06a():
    f = Figure(6, '機能的意識と現象的意識', 'システムが何を行うかと、主体にどう感じられるかは別の問いである', 660, 'a')
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
    return f.save('06-a-functional-and-phenomenal.svg')


def fig06b():
    f = Figure(6, '入出力が同じでも、内部の因果構造は異なり得る', 'IITはこの違いを意識の成立に関係づける', 620, 'b')
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
    return f.save('06-b-feedforward-vs-recurrent.svg')


def fig06c():
    f = Figure(6, 'AIに意識を問うときの三つの評価軸', '似ていることは、次の段が同じであることを意味しない', 620, 'c')
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
    return f.save('06-c-three-axes.svg')


# ---------------------------------------------------------------------------
# 第7回
# ---------------------------------------------------------------------------

def fig07a():
    f = Figure(7, '分人は目的関数の重みベクトルである', '軸は共通で、相対的な重みだけが異なる', 660, 'a')
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
    return f.save('07-a-dividual-weights.svg')


def fig07b():
    f = Figure(7, '文脈が分人を選び、基盤は共有される', '切り替えと共有の両方があるから、同じ「自分」として認識できる', 680, 'b')
    f.pill(60, 300, 150, 50, '文脈 c', INK, 20)
    f.text(135, 375, '状況・相手・環境', 14, MUTED, anchor='middle')
    f.line(210, 325, 280, 325, MUTED, 2.2, arrow=True)
    f.box(280, 285, 220, 80, '混合係数 π(c)', 'どの分人をどの程度', INK, 20)
    persons = [('職場の分人 w⁽¹⁾', 215, TEAL, '0.7'), ('家庭の分人 w⁽²⁾', 305, TERRA, '0.2'), ('趣味の分人 w⁽³⁾', 395, INDIGO, '0.1')]
    for label, y, color, coef in persons:
        f.box(620, y, 230, 64, label, '', color, 19)
        f.curve(500, 325, 560, (325 + y + 32) / 2, 620, y + 32, color, 2.2)
        f.text(560, (325 + y + 32) / 2 - 8, coef, 15, color, anchor='middle', weight=700)
        f.curve(850, y + 32, 900, (y + 32 + 350) / 2, 940, 350, color, 2.2)
    f.box(940, 310, 210, 80, '重みの合成 w(c)', 'w(c) = Σ πⱼ(c) w⁽ʲ⁾', INK, 19, sub_size=14)
    f.line(1045, 390, 1045, 440, MUTED, 2.2, arrow=True)
    f.box(940, 440, 210, 60, '行動の選択', '', INK, 19)
    f.rect(60, 545, 1090, 80, fill=PALE, stroke=TEAL, rx=14)
    f.text(605, 580, '分人が共有する基盤', 20, TEAL, anchor='middle', weight=700)
    f.text(605, 606, '記憶 ／ 身体 ／ 自己表象 ── どの分人の経験も、同じ個人の履歴として蓄積される', 15, INK, anchor='middle')
    for x in (690, 735, 780):
        f.line(x, 545, x, 462, TEAL, 1.5, arrow=True, dash=True)
    f.footer('混合エキスパートモデルと形式的に似ているが、数学的な類似性が心理的な分人の仕組みを証明するわけではない。')
    return f.save('07-b-context-mixture.svg')


def fig07c():
    f = Figure(7, '自己の境界は距離として現れる', '皮膚の内外ではなく、情報処理上の関係が結びつきの強さを決める', 740, 'c')
    cx, cy = 480, 460
    for r in (100, 175, 250):
        f.circ(cx, cy, r, LINE, fill=False, dash=True, width=1.5)
    f.text(cx + 252, cy - 6, '弱い', 14, MUTED)
    f.text(cx + 102, cy - 6, '強い', 14, MUTED)
    f.blob(cx, cy, 110, TEAL, 0.5)
    f.circ(cx, cy, 56, '#ffffff')
    f.circ(cx, cy, 56, TEAL, fill=False, width=2.5)
    f.text(cx, cy + 7, '自己表象', 20, TEAL, anchor='middle', weight=700)
    items = [('身体', -90, 80, TEAL), ('作品', 95, 130, INDIGO), ('熟練した道具', -155, 160, INDIGO), ('自動車', -35, 170, INDIGO), ('ゲームキャラクター', 150, 205, TERRA), ('SNSアカウント', 20, 215, TERRA), ('見知らぬ物', -120, 240, MUTED)]
    for label, deg, r, color in items:
        x, y = polar(cx, cy, r, deg)
        f.blob(x, y, 48, color, 0.4)
        f.circ(x, y, 9, color)
        anchor = 'start' if math.cos(math.radians(deg)) > 0.3 else ('end' if math.cos(math.radians(deg)) < -0.3 else 'middle')
        off = 16 if anchor == 'start' else (-16 if anchor == 'end' else 0)
        f.text(x + off, y + (26 if anchor == 'middle' and deg > 0 else (-18 if anchor == 'middle' else 6)), label, 17, INK, anchor=anchor, weight=700)
    f.rect(840, 225, 300, 300, fill='#ffffff', stroke=LINE)
    f.text(990, 262, '距離を決める要素', 20, INK, anchor='middle', weight=700)
    f.lines(870, 310, ['制御：対象を制御できる程度', '予測：変化を予測できる程度', '記憶：経験と記憶の結びつき', '価値：目的や価値観との関係', '関係：対象を通じた他者との関係'], 16, INK, gap=38)
    f.text(990, 508, 'SelfScore(x, c) = h(…, c)', 14, MUTED, anchor='middle')
    f.footer('スコアは説明のための工学的な仮説であり、脳内に単一の数値が存在するという主張ではない。')
    return f.save('07-c-extended-self.svg')


# ---------------------------------------------------------------------------
# 第8回
# ---------------------------------------------------------------------------

def fig08a():
    f = Figure(8, '物語は目的関数を学習させる', '現実とは別の経路から、価値判断と結びついた経験を渡す', 620, 'a')
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
    return f.save('08-a-narrative-as-learning.svg')


def fig08b():
    f = Figure(8, '四つのジャンルが再構成する評価環境', '現実で強く働く評価基準や制約に対して、別の評価環境を提示する', 760, 'b')
    panels = [(60, 200, '異世界転生もの', '社会的制約を取り除いた評価環境'), (620, 200, '追放もの', '評価者の誤りによる自己評価の回復'),
              (60, 460, '日常系', '競争以外の価値基準の提示'), (620, 460, '悪役令嬢もの', '既定の未来を書き換える可能性')]
    for x, y, label, note in panels:
        f.panel(x, y, 520, 230, label)
        f.text(x + 260, y + 210, note, 15, MUTED, anchor='middle')
    # 異世界転生: 能力 → [制約 ×] → 評価
    x, y = 60, 200
    f.tag(x + 40, y + 95, 110, 40, '能力', TEAL)
    f.rect(x + 215, y + 70, 30, 90, fill=SOFT, stroke=MUTED, rx=4, dash=True)
    f.cross(x + 230, y + 115, 16, TERRA, 3.5)
    f.text(x + 230, y + 185, '社会的制約', 14, MUTED, anchor='middle')
    f.line(x + 150, y + 115, x + 210, y + 115, TEAL, 2.5)
    f.line(x + 250, y + 115, x + 350, y + 115, TEAL, 2.5, arrow=True)
    f.tag(x + 360, y + 95, 110, 40, '評価', TEAL)
    # 追放: 低い評価 → 自分（×） / → 評価者の誤り
    x, y = 620, 200
    f.tag(x + 40, y + 95, 150, 40, '低い他者評価', MUTED)
    f.line(x + 190, y + 108, x + 330, y + 85, LINE, 2, arrow=True, dash=True)
    f.cross(x + 262, y + 92, 9, MUTED, 2)
    f.tag(x + 340, y + 62, 140, 40, '自分の能力', MUTED)
    f.line(x + 190, y + 122, x + 330, y + 150, TERRA, 2.5, arrow=True)
    f.tag(x + 340, y + 130, 150, 40, '評価者の誤り', TERRA)
    f.text(x + 260, y + 185, '原因の帰属先を評価者側へ', 14, MUTED, anchor='middle')
    # 日常系: bars
    x, y = 60, 460
    f.rect(x + 120, y + 55, 70, 110, fill=SOFT, stroke=MUTED, rx=4, dash=True)
    f.rect(x + 120, y + 115, 70, 50, fill=MUTED, stroke=MUTED, rx=4)
    f.line(x + 155, y + 45, x + 155, y + 105, TERRA, 2.5, arrow=True)
    f.text(x + 155, y + 185, '競争・達成', 15, INK, anchor='middle', weight=700)
    f.rect(x + 310, y + 55, 70, 110, fill=TEAL, stroke=TEAL, rx=4)
    f.text(x + 345, y + 185, '関係・日常', 15, INK, anchor='middle', weight=700)
    f.text(x + 440, y + 110, '重みの', 14, MUTED, anchor='middle')
    f.text(x + 440, y + 130, '相対化', 14, MUTED, anchor='middle')
    # 悪役令嬢: branch
    x, y = 620, 460
    f.circ(x + 70, y + 130, 9, INK)
    f.text(x + 70, y + 165, '現在', 15, INK, anchor='middle', weight=700)
    f.line(x + 80, y + 130, x + 420, y + 130, MUTED, 2.5, arrow=True, dash=True)
    f.text(x + 430, y + 136, '既定の結末', 15, MUTED)
    f.curve(x + 200, y + 130, x + 300, y + 130, x + 420, y + 70, TEAL, 2.5)
    f.text(x + 430, y + 76, '別の未来', 15, TEAL, weight=700)
    f.text(x + 200, y + 100, '結末を予測し', 14, TEAL, anchor='middle')
    f.text(x + 200, y + 118, '行動を変える', 14, TEAL, anchor='middle')
    f.footer('ジャンルの流行を単一の社会心理で説明することはできない。機能を読むための分析モデルである。')
    return f.save('08-b-four-genres.svg')


def fig08c():
    f = Figure(8, '自己を更新する循環と、外から入る物語', '物語はナラティブと自己表象の段に作用し、自分の物語は他者へ共有される', 720, 'c')
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
        # bow outward a little so the arrows read as a cycle
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        nx, ny = (mx - cx) / math.hypot(mx - cx, my - cy), (my - cy) / math.hypot(mx - cx, my - cy)
        f.curve(x1 + ux * 54, y1 + uy * 54, mx + nx * 22, my + ny * 22, x2 - ux * 56, y2 - uy * 56, MUTED, 2.2)
    f.box(60, 395, 200, 80, '物語', '他者が作った物語', TERRA, 22)
    f.curve(260, 415, 330, 390, pos['ナラティブ'][0] - 52, pos['ナラティブ'][1] - 10, TERRA, 2.5)
    f.curve(260, 455, 380, 540, pos['自己表象'][0] - 52, pos['自己表象'][1] + 8, TERRA, 2.5)
    f.text(160, 505, '価値判断・解釈を', 14, MUTED, anchor='middle')
    f.text(160, 523, '外から更新する', 14, MUTED, anchor='middle')
    f.box(940, 540, 210, 80, '他者への共有', '別の人の目的関数へ', INDIGO, 20)
    f.curve(pos['自己表象'][0] + 52, pos['自己表象'][1] + 10, 820, 600, 940, 580, INDIGO, 2.5)
    f.text(cx, cy - 8, '自分についての物語が', 15, INK, anchor='middle')
    f.text(cx, cy + 14, '次の行動を方向づける', 15, INK, anchor='middle')
    f.footer('私たちは物語を読むだけでなく、自分を物語として構築し、その物語に従って行動している可能性がある。')
    return f.save('08-c-self-narrative-loop.svg')


# ---------------------------------------------------------------------------
# 第9回
# ---------------------------------------------------------------------------

def fig09a():
    f = Figure(9, '自己表象の効果は比較でしか測れない', '構成要素を一つずつ足した三つのモデルを同じ環境に置く', 640, 'a')
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
    return f.save('09-a-three-agents.svg')


def fig09b():
    f = Figure(9, '実装アーキテクチャ', '外周は観測から行動までの循環、中央は自己表象を核とする層', 780, 'b')
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
    f.text(600, 552, '整理', 12, MUTED, anchor='middle')
    f.line(665, 365, 645, 407, TERRA, 2, arrow=True)
    f.line(775, 340, 960, 440, TERRA, 2, arrow=True, dash=True)
    f.line(700, 440, 960, 455, TERRA, 2, arrow=True, dash=True)
    f.text(830, 418, '重みと優先順位に影響', 13, TERRA, anchor='middle')
    f.line(560, 407, 590, 272, TERRA, 2, arrow=True, dash=True)
    f.text(548, 345, '予測に影響', 13, TERRA, anchor='end')
    f.line(530, 672, 450, 590, INDIGO, 2, arrow=True, dash=True)
    f.text(450, 650, '結果を記録', 13, INDIGO, anchor='end')
    f.footer('各要素を独立に実装するだけでは不十分で、相互に影響し循環する構造を形成する必要がある。')
    return f.save('09-b-architecture.svg')


def fig09c():
    f = Figure(9, '自己表象が機能していると判断する五つの条件', 'すべて、自己表象が行動へ与える因果的な影響を問う', 690, 'c')
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
    return f.save('09-c-success-criteria.svg')


def main() -> int:
    names = [cover(), fig01a(), fig01b(), fig02a(), fig02b(), fig03a(), fig03b(), fig04a(), fig04b(), fig04c(), fig05a(), fig05b(),
             fig06a(), fig06b(), fig06c(), fig07a(), fig07b(), fig07c(), fig08a(), fig08b(), fig08c(), fig09a(), fig09b(), fig09c()]
    print(f'{len(names)} illustrations written to {OUT.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
