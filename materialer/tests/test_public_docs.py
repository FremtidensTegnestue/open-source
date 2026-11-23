"""Regression checks for public navigation, including observed Unicode/case pitfalls."""
import tempfile
import unittest
from pathlib import Path
from scripts.check_public_docs import audit, heading_ids, markdown_links, prose


class PublicDocsTests(unittest.TestCase):
    def test_github_heading_symbols_and_duplicate_suffix(self):
        self.assertEqual(heading_ids('# CO₂ og træ\n# CO₂ og træ\n'),
                         {'co-og-træ', 'co-og-træ-1'})

    def test_balanced_parentheses_and_angle_destination(self):
        links = list(markdown_links('[A](https://example.org/a(b)) [B](<a b.md>)'))
        self.assertEqual([url for _, url in links], ['https://example.org/a(b)', 'a b.md'])

    def test_examples_in_fenced_and_inline_code_are_not_links(self):
        text = '```md\n[A](missing.md)\n```\n`[B](missing.md)`\n[C](real.md)'
        self.assertEqual(list(markdown_links(prose(text))), [(5, 'real.md')])

    def test_real_target_heading_and_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'README.md').write_text('[A](Guide.md#co)\n[B](guide.md)\n[C](Guide.md#missing)')
            (root / 'Guide.md').write_text('# CO₂\n')
            report = audit(root, ['README.md', 'Guide.md'])
            self.assertEqual(report['local_references'], 3)
            self.assertEqual([row['error'] for row in report['broken']],
                             ['file_or_directory_missing_or_wrong_case', 'Markdown_heading_missing'])

    def test_html_assets_and_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'index.html').write_text('<a href="book/">Book</a><img src="book/cover.svg"><img src="missing.svg">')
            report = audit(root, ['index.html', 'book/cover.svg'])
            self.assertEqual(len(report['broken']), 1)
            self.assertEqual(report['broken'][0]['target'], 'missing.svg')
