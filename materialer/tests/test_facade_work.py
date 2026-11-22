"""Work visibility changes independently of CAD and never certifies an engineering result."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import facade
import facade_live
import work_overview
from test_facade import sample, FakeClimate


class Control:
    revision = {'document_id': 'test-facade', 'revision': 1}

    def call(self, method, params=None):
        return self.revision


class IntegratedWorkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'proof.txt'
        self.source.write_text('Fiktivt bilag, ingen ingeniørgodkendelse')
        self.registry_path = self.root / 'work.json'
        self.registry = {
            'schema': 1, 'project_id': 'TEST-BUILDING', 'scope': 'Hele testprojektet, ikke facadeprøvens målinger',
            'sources': {'proof': {'path': 'proof.txt', 'sha256': facade.file_hash(self.source)}},
            'items': [{
                'id': 'own', 'title': 'TESTmaterialeliste udarbejdet', 'scope': 'Kun testlisten',
                'work_by': 'us', 'responsible_role': 'Egen projekterende', 'requirement': 'work',
                'state': 'completed', 'basis': 'Kun afgrænset dokumentproduktion',
                'next_action': 'Genvurder ved ændring', 'sources': ['proof'], 'completion': None,
            }],
        }
        item = self.registry['items'][0]
        item['completion'] = {'by': 'TESTregistrering', 'date': '2026-11-22', 'reference': 'Fiktivt testbilag',
                              'context_key': work_overview.context_key(self.registry, item), 'evidence': ['proof']}
        self.save_registry()
        self.config = {'project_directory': str(self.root), 'project_id': 'test-facade', 'engine': {},
                       'work_overview': {'path': 'work.json', 'project_id': 'TEST-BUILDING', 'label': 'Fiktivt projekt'}}
        self.config_path = self.root / 'project.json'

    def save_registry(self):
        self.registry_path.write_text(json.dumps(self.registry))

    def live(self):
        self.config_path.write_text(json.dumps(self.config))
        live = facade_live.LiveFacade(self.config_path, control=Control(), climate=FakeClimate())
        live.state = {'status': 'current'}
        live.version = Control.revision
        live.input_key = 'same-CAD-revision'
        live.result = facade.evaluate(sample(), FakeClimate())
        live.reference = copy.deepcopy(live.result)
        live.snapshot_data = {'text': '{}'}
        return live

    def test_project_scope_is_explicit_and_no_approval_is_created(self):
        v = self.live().view()
        self.assertEqual(v['work_overview']['label'], 'Fiktivt projekt')
        self.assertEqual(v['work_overview']['overview']['project_id'], 'TEST-BUILDING')
        self.assertNotIn('approved', v)
        self.assertEqual(v['work_overview']['overview']['recorded_completions'], 1)

    def test_changed_work_basis_updates_without_a_CAD_change_or_recalculation(self):
        live = self.live()
        before = live.view()
        self.source.write_text('Ændret bilag')
        after = live.view()
        self.assertEqual(after['input_key'], before['input_key'])
        self.assertEqual(after['result'], before['result'])
        self.assertEqual(after['work_overview']['status'], 'recheck')
        self.assertNotEqual(before['work_overview']['key'], after['work_overview']['key'])
        self.assertEqual(after['work_overview']['overview']['recorded_completions'], 0)

    def test_work_is_available_when_CAD_is_disconnected(self):
        live = self.live()
        live.state = {'status': 'unavailable', 'message': 'TEST CAD ikke forbundet'}
        v = live.view()
        self.assertIsNone(v['result'])
        self.assertEqual(v['work_overview']['status'], 'current')

    def test_wrong_project_replaces_work_with_error_not_other_projects_items(self):
        live = self.live()
        self.registry['project_id'] = 'ANOTHER-PROJECT'
        self.save_registry()
        w = live.view()['work_overview']
        self.assertEqual(w['status'], 'unavailable')
        self.assertNotIn('overview', w)

    def test_missing_invalid_and_unconfigured_registry_never_mean_zero_gaps(self):
        live = self.live()
        self.registry_path.write_text('{ invalid')
        w = live.view()['work_overview']
        self.assertNotIn('overview', w)
        self.assertIn('ugyldigt format', w['message'])
        self.assertNotIn('Expecting', w['message'])
        self.registry_path.unlink()
        self.assertEqual(live.view()['work_overview']['status'], 'unavailable')
        del self.config['work_overview']
        w = self.live().view()['work_overview']
        self.assertEqual(w['status'], 'not_configured')
        self.assertNotIn('overview', w)

    def test_config_change_cannot_silently_redirect_project_work(self):
        live = self.live()
        self.config['work_overview']['project_id'] = 'OTHER'
        self.config_path.write_text(json.dumps(self.config))
        self.assertEqual(live.view()['work_overview']['status'], 'unavailable')

    def test_snapshot_includes_current_work_and_does_not_write_registry(self):
        live = self.live()
        before = self.registry_path.read_bytes()
        live.save(live.input_key)
        snapshot = json.loads((self.root / 'gemt-regnskab.json').read_text())
        self.assertEqual(snapshot['work_overview']['overview']['project_id'], 'TEST-BUILDING')
        self.assertEqual(self.registry_path.read_bytes(), before)
        self.assertNotIn('approval', snapshot)


if __name__ == '__main__':
    unittest.main()
