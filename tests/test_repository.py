from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build import parse_markdown, render, map_url, build, site_index_text
from validate import validate, svg_errors, walk
from check_html import check, Document

SERIES = json.loads((ROOT / 'series.json').read_text(encoding='utf-8'))
CHAPTERS = len(SERIES['chapters'])
FIGURES = sum(len(c['figures']) for c in SERIES['chapters'])


class RepositoryTests(unittest.TestCase):
    def test_entire_repository(self):
        result, errors = validate()
        self.assertEqual(errors, [])
        self.assertEqual(result.chapters, CHAPTERS)
        self.assertEqual(result.svg_files, 1 + FIGURES)

    def test_footnotes_render_as_notes(self):
        output = render('本文[^a]。\n\n[^a]: 出典。\n')
        self.assertIn('class="footnotes', output)
        self.assertNotIn('<script', output)

    def test_caption_paragraph_becomes_figcaption(self):
        output = render('![代替テキスト](../assets/illustrations/00-cover.svg)\n\n*図1-1：説明。*\n\n次の段落。\n')
        self.assertEqual(output.count('<figcaption'), 1)
        self.assertIn('<figcaption>図1-1：説明。</figcaption>', output)
        self.assertNotIn('<p><em>図1-1', output)
        self.assertIn('alt="代替テキスト"', output)

    def test_alt_only_figure_has_no_caption(self):
        output = render('![表紙の説明](../assets/illustrations/00-cover.svg)\n')
        self.assertEqual(output.count('<figcaption'), 0)
        self.assertIn('alt="表紙の説明"', output)

    def test_tables_are_wrapped_and_unsized(self):
        output = render('| 回 | 文章 |\n| --- | --- |\n| 01 | 本文 |\n')
        self.assertIn('<div class="table-wrap"><table', output)
        self.assertIn('</table></div>', output)
        self.assertNotIn('<col style', output)

    def test_inline_code_formulas_stay_code(self):
        output = render('評価は `U(x) = Σᵢ wᵢ・fᵢ(x)` で表す。\n')
        self.assertIn('<code>U(x) = Σᵢ wᵢ・fᵢ(x)</code>', output)

    def test_formula_block_and_subscripts(self):
        output = render('`U(x) = Σ_i w_i・f_i(x)`　（式3-2）\n\n重み `w_1^(j)` と `S_(t+1)` と `a_1:t-1`。\n', math=True)
        self.assertIn('<div class="formula"><code class="math">U(x) = Σ<sub>i</sub> w<sub>i</sub>・f<sub>i</sub>(x)</code><span class="formula-label">（式3-2）</span></div>', output)
        self.assertIn('<code class="math">w<sub>1</sub><sup>(j)</sup></code>', output)
        self.assertIn('<code class="math">S<sub>t+1</sub></code>', output)
        self.assertIn('<code class="math">a<sub>1:t-1</sub></code>', output)

    def test_flow_lines_and_non_math_pages(self):
        output = render('`物語体験 → 価値判断の学習`\n', math=True)
        self.assertIn('<div class="formula"><code class="flow">物語体験 → 価値判断の学習</code></div>', output)
        output = render('ファイル `_site/index.html` を開く。\n', math=False)
        self.assertIn('<code>_site/index.html</code>', output)

    def test_nav_markers_become_nav_cards(self):
        text = '<!-- NAV:TOP -->\n[← 第4回](a.md) | [連載目次](../README.md) | [第6回 →](b.md)\n<!-- /NAV -->\n\n本文\n\n<!-- NAV:BOTTOM -->\n---\n\n[← 第4回](a.md) | [連載目次](../README.md)\n<!-- /NAV -->\n'
        output = render(text, next_note='次回　第6回「題名」')
        self.assertEqual(output.count('<nav class="chapter-nav'), 2)
        self.assertIn('chapter-nav-next">次回　第6回「題名」', output)
        self.assertNotIn('<!-- NAV:', output)
        self.assertNotIn('<h2', output)
        self.assertIn('class="sep"', output)

    def test_figures_get_scroll_container_and_full_size_link(self):
        output = render('![説明](../assets/illustrations/00-cover.svg)\n\n*図1-1：説明。*\n')
        self.assertIn('<div class="figure-scroll"><a class="figure-link" href="../assets/illustrations/00-cover.svg"', output)
        self.assertEqual(output.count('<figcaption'), 1)

    def test_parts_tile_the_series(self):
        covered = [n for p in SERIES['parts'] for n in range(p['chapters'][0], p['chapters'][1] + 1)]
        self.assertEqual(covered, list(range(1, CHAPTERS + 1)))

    def test_dollar_signs_are_not_math(self):
        ast = parse_markdown('価格は $5 と $7 です。\n')
        self.assertFalse(any(n.get('t') == 'Math' for n in walk(ast)))

    def test_site_index_stops_at_marker(self):
        text = '# T\n\n本文\n\n<!-- SITE-INDEX-END -->\n\n## GitHubで読む\n\n運用\n'
        self.assertEqual(site_index_text(text), '# T\n\n本文\n')
        self.assertEqual(site_index_text('# T\n\n本文\n'), '# T\n\n本文\n')
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertIn(f'## 全{CHAPTERS}回の目次', site_index_text(readme))
        self.assertNotIn('## GitHubで読む', site_index_text(readme))

    def test_relative_links(self):
        self.assertEqual(map_url('../README.md'), '../index.html')
        self.assertEqual(map_url('one.md#test'), 'one.html#test')
        self.assertEqual(map_url('https://example.org/a.md'), 'https://example.org/a.md')
        self.assertEqual(map_url('../assets/a.svg'), '../assets/a.svg')

    def test_svg_rejects_executable_content(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.svg'
            p.write_text('<svg viewBox="0 0 10 10" role="img"><title>X</title><desc>Y</desc><script>alert(1)</script></svg>')
            self.assertTrue(any('forbidden SVG' in x for x in svg_errors(p)))

    def test_svg_rejects_external_href(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.svg'
            p.write_text('<svg viewBox="0 0 10 10" role="img"><title>X</title><desc>Y</desc><a href="https://example.org"/></svg>')
            self.assertTrue(any('external href' in x for x in svg_errors(p)))

    def test_svg_allows_internal_gradient(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.svg'
            p.write_text('<svg viewBox="0 0 10 10" role="img" aria-labelledby="t d"><title id="t">X</title><desc id="d">Y</desc><defs><radialGradient id="g"/></defs><circle fill="url(#g)" r="1"/></svg>')
            self.assertEqual(svg_errors(p), [])

    def test_svg_rejects_malformed_xml(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.svg'
            p.write_text('<svg>')
            self.assertTrue(svg_errors(p))

    def test_figures_are_reproducible(self):
        before = {str(p): p.read_bytes() for p in (ROOT / 'assets/illustrations').rglob('*.svg')}
        subprocess.run([sys.executable, str(ROOT / 'scripts/draw_figures.py')], check=True, capture_output=True)
        after = {str(p): p.read_bytes() for p in (ROOT / 'assets/illustrations').rglob('*.svg')}
        self.assertEqual(before, after)

    def test_publish_defaults_to_dry_run(self):
        p = subprocess.run([sys.executable, str(ROOT / 'scripts/publish.py'), '--owner', 'example'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertIn('DRY RUN', p.stdout)
        self.assertIn('private', p.stdout)

    def test_publish_rejects_path_injection(self):
        p = subprocess.run([sys.executable, str(ROOT / 'scripts/publish.py'), '--owner', '../bad'], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)

    def test_build_refuses_source_overwrite(self):
        with self.assertRaises(RuntimeError):
            build(ROOT)

    def test_chapter_ids_and_figures_are_unique(self):
        self.assertEqual(len({c['slug'] for c in SERIES['chapters']}), CHAPTERS)
        for c in SERIES['chapters']:
            self.assertGreaterEqual(len(c['figures']), 1)
            self.assertLessEqual(len(c["figures"]), 11)
            self.assertEqual(len(c['figures']), len(set(c['figures'])))
            self.assertEqual(len(c['sources']), len(set(c['sources'])))

    def test_complete_reader_links_and_figures(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / 'reader'
            build(output)
            report = check(output)
            self.assertEqual(report['errors'], [])
            self.assertEqual(report['chapter_pages'], CHAPTERS)
            self.assertEqual(report['chapter_images'], FIGURES)

    def test_combined_footnote_ids_are_namespaced(self):
        text = 'A[^a].\n\n[^a]: A source.\n'
        doc = Document(render(text, prefix='a-') + render(text, prefix='b-'))
        self.assertEqual(len(doc.ids), len(set(doc.ids)))

    def test_html_checker_detects_missing_target(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)
            (output / 'index.html').write_text('<html><a href="missing.html">Link</a></html>')
            self.assertTrue(any('missing target' in e for e in check(output)['errors']))

    def test_html_checker_rejects_network_images(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)
            (output / 'index.html').write_text('<html><img src="https://example.org/image.svg"></html>')
            self.assertTrue(any('external resource' in e for e in check(output)['errors']))


if __name__ == '__main__':
    unittest.main()
