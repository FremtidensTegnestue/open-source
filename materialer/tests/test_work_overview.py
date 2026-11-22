import copy
import json
from pathlib import Path
import tempfile
import unittest

import work_overview as overview


class WorkOverviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'basis.txt'
        self.source.write_text('Afgrænset dokumentationsgrundlag')
        self.path = self.root / 'work.json'
        self.registry = {
            'schema': 1, 'project_id': 'test', 'scope': 'TEST, ingen byggetilladelse',
            'sources': {'basis': {'path': 'basis.txt', 'sha256': overview.sha(self.source)}},
            'items': [{
                'id': 'own-work', 'title': 'Udarbejd grundlag', 'scope': 'Én del',
                'work_by': 'us', 'responsible_role': 'Projekterende',
                'requirement': 'work', 'state': 'open', 'basis': 'Afgrænset opgave',
                'next_action': 'Dokumentér de manglende oplysninger', 'sources': ['basis'],
                'completion': None,
            }],
        }

    def save(self):
        self.path.write_text(json.dumps(self.registry))
        return overview.view(self.path)

    def close(self):
        item = self.registry['items'][0]
        item['state'] = 'completed'
        item['completion'] = {
            'by': 'TEST-registrering', 'date': '2026-11-22',
            'reference': 'Kontrol af angivet dokument, ikke formel erklæring',
            'context_key': overview.context_key(self.registry, item), 'evidence': ['basis'],
        }

    def test_open_work_does_not_become_external_or_approved(self):
        v = self.save()
        self.assertTrue(v['current'])
        self.assertEqual(v['open_items'], 1)
        self.assertEqual(v['items'][0]['work_by'], 'us')
        self.assertEqual(v['recorded_completions'], 0)
        self.assertNotIn('approved', v)

    def test_completion_needs_evidence(self):
        self.close()
        self.registry['items'][0]['completion']['evidence'] = []
        with self.assertRaises(ValueError):
            self.save()

    def test_changed_source_reopens_recorded_completion(self):
        self.close()
        self.assertEqual(self.save()['recorded_completions'], 1)
        self.source.write_text('Ændret grundlag')
        v = overview.view(self.path)
        self.assertFalse(v['current'])
        self.assertEqual(v['items'][0]['derived_state'], 'recheck')
        self.assertEqual(v['open_items'], 1)

    def test_repinning_source_does_not_revalidate_old_completion(self):
        self.close()
        self.source.write_text('Ny revision')
        self.registry['sources']['basis']['sha256'] = overview.sha(self.source)
        self.assertEqual(self.save()['items'][0]['derived_state'], 'recheck')

    def test_changed_scope_reopens_completion(self):
        self.close()
        self.registry['items'][0]['scope'] = 'Hele bygningen'
        self.assertFalse(self.save()['current'])

    def test_unrelated_source_change_does_not_reopen_other_item(self):
        other = self.root / 'other.txt'
        other.write_text('Andet dokument')
        self.registry['sources']['other'] = {'path': 'other.txt', 'sha256': overview.sha(other)}
        item = copy.deepcopy(self.registry['items'][0])
        item.update(id='other', sources=['other'], work_by='undecided', requirement='clarify')
        self.registry['items'].append(item)
        self.close()
        self.save()
        other.write_text('Ændret')
        v = overview.view(self.path)
        self.assertEqual([i['derived_state'] for i in v['items']], ['completed', 'recheck'])
        self.assertEqual(v['counts']['clarify'], 1)

    def test_missing_file_is_not_current(self):
        self.source.unlink()
        self.assertFalse(self.save()['current'])

    def test_invalid_empty_or_duplicate_records_are_rejected(self):
        for key, value in [('sources', {}), ('items', []), ('schema', True)]:
            bad = copy.deepcopy(self.registry)
            bad[key] = value
            with self.assertRaises(ValueError):
                overview.validate(bad)
        self.registry['items'].append(copy.deepcopy(self.registry['items'][0]))
        with self.assertRaises(ValueError):
            self.save()

    def test_render_escapes_input_and_live_failure_is_visible(self):
        self.registry['items'][0]['title'] = '<script>alert(1)</script>'
        v = self.save()
        static = overview.render(v)
        self.assertNotIn('<script>', static)
        self.assertIn('&lt;script&gt;', static)
        live = overview.render(v, live=True)
        self.assertIn(overview.state_key(v), live)
        self.assertIn('Kontrol afbrudt eller ugyldig registrering', live)
        self.assertIn('setInterval(check,2000)', live)

    def test_report_cannot_overwrite_input_or_sources(self):
        self.save()
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            overview.build(self.path, self.root / 'work.html')
        with self.assertRaises(ValueError):
            overview.build(self.path, self.source)
        html_source = self.root / 'proof.html'
        html_source.write_text('Original proof')
        self.registry['sources']['proof'] = {'path': 'proof.html', 'sha256': overview.sha(html_source)}
        self.save()
        with self.assertRaises(ValueError):
            overview.build(self.path, html_source)
        self.assertEqual(html_source.read_text(), 'Original proof')
        # The registry changed only by the deliberate source addition above.
        self.assertEqual(json.loads(before)['project_id'], json.loads(self.path.read_text())['project_id'])
        v = overview.build(self.path, self.root / 'report.html')
        self.assertTrue(v['current'])
        self.assertTrue((self.root / 'report.html').is_file())
        self.assertEqual(json.loads((self.root / 'report.json').read_text())['open_items'], 1)


if __name__ == '__main__':
    unittest.main()
