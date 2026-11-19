"""Bounded, opt-in family-mesh quantities, independent of the installed CAD CLI."""
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adapters import bimcraft
import material_calculations as calculations
import materials


def box_mesh(offset=(0, 0, 0)):
    points = [[x + offset[0], y + offset[1], z + offset[2]] for x, y, z in
              ((0, 0, 0), (1000, 0, 0), (1000, 500, 0), (0, 500, 0),
               (0, 0, 100), (1000, 0, 100), (1000, 500, 100), (0, 500, 100))]
    faces = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
             (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
             (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    return [[points[i][:] for i in face] for face in faces]


def ring_mesh():
    # Rectangular through-hole: four connected walls, not nested solid shells.
    outer = [(0, 0), (1000, 0), (1000, 800), (0, 800)]
    inner = [(300, 300), (700, 300), (700, 500), (300, 500)]
    mesh = []
    def quad(points):
        mesh.extend([[points[0], points[1], points[2]], [points[0], points[2], points[3]]])
    for i in range(4):
        j = (i + 1) % 4
        a, b = outer[i], outer[j]
        c, d = inner[i], inner[j]
        quad([[*a, 0], [*b, 0], [*b, 300], [*a, 300]])
        quad([[*d, 0], [*c, 0], [*c, 300], [*d, 300]])
        quad([[*a, 300], [*b, 300], [*d, 300], [*c, 300]])
        quad([[*c, 0], [*d, 0], [*b, 0], [*a, 0]])
    return mesh


def row():
    return {'id': 1, 'guid': 'element-guid', 'category': 'component',
            'family': 'Imported body', 'type': 'Imported', 'values': {},
            'at': [500, 250], 'angle': 90, 'offset': -50, 'mirrored': True}


def family():
    return {'name': 'Imported body', 'family': {
        'category': 'generic', 'parameters': [], 'types': {'Imported': {}},
        'planes': [{'guid': bimcraft.DEFAULT_MESH_PLANE, 'start': [-1000, 0, 0],
                    'end': [1000, 0, 0], 'up': [0, 1000, 0], 'defines_origin': True, 'level': True}],
        'forms': [{'id': 22, 'guid': 'form-guid', 'host': {'plane': bimcraft.DEFAULT_MESH_PLANE},
                   'from': 0, 'to': 0, 'material': 'Explicit timber', 'mesh': box_mesh()}]},
        'values': {'Imported': {}}, 'warnings': []}


def normalize(reply=None, element=None, enabled=True):
    return bimcraft.normalize({'types': {}}, [element or row()], {}, 'test', [],
                             mesh_quantities=enabled, family_replies={'Imported body': reply or family()})


class MeshVolumeTests(unittest.TestCase):
    def test_analytic_box_translation_and_global_reversed_winding(self):
        for mesh in (box_mesh(), box_mesh((1e9, -2e9, 3e9)), [list(reversed(t)) for t in box_mesh()]):
            self.assertAlmostEqual(bimcraft._mesh_volume(mesh), .05, places=14)

    def test_through_hole_is_integrated_in_one_connected_shell(self):
        self.assertAlmostEqual(bimcraft._mesh_volume(ring_mesh()), .216, places=14)

    def test_open_nonmanifold_inconsistent_and_disconnected_meshes_rejected(self):
        cases = [(box_mesh()[:-1], 'open or nonmanifold'),
                 (box_mesh() + [box_mesh()[0]], 'open or nonmanifold'),
                 ([list(reversed(box_mesh()[0]))] + box_mesh()[1:], 'inconsistent'),
                 (box_mesh() + box_mesh((3000, 0, 0)), 'disconnected')]
        for mesh, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                bimcraft._mesh_volume(mesh)

    def test_nonfinite_and_degenerate_faces_are_rejected(self):
        for value in (float('nan'), float('inf'), True):
            mesh = box_mesh(); mesh[0][0][0] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'finite'):
                bimcraft._mesh_volume(mesh)
        mesh = box_mesh(); mesh[0][1] = mesh[0][0][:]
        with self.assertRaisesRegex(ValueError, 'degenerate'):
            bimcraft._mesh_volume(mesh)

    def test_weld_tolerance_is_tight_and_exposed(self):
        mesh = box_mesh(); mesh[0][0][0] += bimcraft.MESH_WELD_TOLERANCE_MM / 2
        self.assertAlmostEqual(bimcraft._mesh_volume(mesh), .05, places=8)
        mesh[0][0][0] += .01
        with self.assertRaisesRegex(ValueError, 'open or nonmanifold'):
            bimcraft._mesh_volume(mesh)


class FamilyMeshTests(unittest.TestCase):
    def test_opt_in_uses_form_material_and_records_method_without_area_guess(self):
        out = normalize(); element = out['elements'][0]
        self.assertAlmostEqual(element['volume_m3'], .05)
        self.assertEqual(element['material_name'], 'Explicit timber')
        self.assertIsNone(element['area_m2'])
        source = element['source_ref']
        self.assertEqual(source['quantity_api'], 'bimcraft-cli family mesh')
        self.assertEqual(source['source_form_guid'], 'form-guid')
        self.assertEqual(source['triangle_count'], 12)
        self.assertEqual(source['vertex_welding_tolerance_mm'], bimcraft.MESH_WELD_TOLERANCE_MM)
        self.assertFalse(source['self_intersection_checked'])
        self.assertIsNone(source['volume_rounding_increment_m3'])
        self.assertEqual({w['code'] for w in out['warnings']}, {'mesh_quantity_limits'})
        self.assertEqual(out['warnings'][0]['severity'], 'notice')

    def test_default_unchanged_and_api_volume_not_replaced(self):
        out = normalize(enabled=False)
        self.assertIsNone(out['elements'][0]['volume_m3'])
        self.assertEqual({w['code'] for w in out['warnings']}, {'missing_material', 'missing_volume'})
        element = row(); element.update(volume_m3=.07, area_m2=2, material='API material')
        out = normalize(element=element)
        self.assertEqual(out['elements'][0]['volume_m3'], .07)
        self.assertEqual(out['elements'][0]['area_m2'], 2)
        self.assertEqual(out['elements'][0]['material_name'], 'API material')
        self.assertEqual(out['warnings'], [])

    def test_missing_form_material_is_not_guessed_from_body_or_instance_name(self):
        reply = family(); del reply['family']['forms'][0]['material']
        element = row(); element['material'] = 'Instance shortcut'
        out = normalize(reply, element)
        self.assertIsNone(out['elements'][0]['material_name'])
        self.assertAlmostEqual(out['elements'][0]['volume_m3'], .05)
        self.assertIn('missing_material', {w['code'] for w in out['warnings']})

    def test_unsupported_family_form_and_instance_context_stay_unresolved(self):
        for change in ('parameters', 'category', 'types', 'extra_form', 'void', 'visibility', 'host', 'plane', 'instance_scale', 'instance_values'):
            reply, element = family(), row()
            if change == 'parameters': reply['family']['parameters'] = ['Width']
            if change == 'category': reply['family']['category'] = 'furniture'
            if change == 'types': reply['family']['types']['Imported'] = {'Width': 100}
            if change == 'extra_form': reply['family']['forms'].append(copy.deepcopy(reply['family']['forms'][0]))
            if change == 'void': reply['family']['forms'][0]['void'] = True
            if change == 'visibility': reply['family']['forms'][0]['visible'] = 'Visible parameter'
            if change == 'host': reply['family']['forms'][0]['host'] = {'plane': 'custom'}
            if change == 'plane': reply['family']['planes'][0]['up'] = [0, 2000, 0]
            if change == 'instance_scale': element['scale'] = 2
            if change == 'instance_values': element['values'] = {'Width': 100}
            with self.subTest(change=change):
                out = normalize(reply, element)
                self.assertIsNone(out['elements'][0]['volume_m3'])
                self.assertIn('unsupported_mesh_quantity', {w['code'] for w in out['warnings']})

    def test_family_lookup_failure_is_retained(self):
        out = bimcraft.normalize({'types': {}}, [row()], {}, 'test', [], mesh_quantities=True,
                                 family_lookup_errors={'Imported body': 'family command failed'})
        self.assertIsNone(out['elements'][0]['volume_m3'])
        self.assertTrue(any('family command failed' in w['message'] for w in out['warnings']))


class RoutingTests(unittest.TestCase):
    def test_calculation_wrapper_opts_in_only_for_bimcraft(self):
        response = {'schema_version': 1, 'software': 'bimcraft'}
        with patch('adapters.bimcraft.extract', return_value=response) as adapter:
            self.assertEqual(calculations.extract('model.bimc', 'bimcraft', mesh_quantities=True), response)
            adapter.assert_called_once_with('model.bimc', mesh_quantities=True)
        with self.assertRaisesRegex(ValueError, 'only for BIMcraft'):
            calculations.extract('model.solidcraft', 'solidcraft', mesh_quantities=True)

    def test_cli_threads_flag_for_all_model_commands(self):
        response = {'schema_version': 1, 'software': 'bimcraft', 'model': {}, 'elements': []}
        with tempfile.TemporaryDirectory() as temporary:
            binding = Path(temporary) / 'bindings.json'; binding.write_text('{}')
            for command in ('extract', 'suggest', 'assess'):
                argv = [command, 'model.bimc', '--software', 'bimcraft', '--mesh-quantities']
                if command == 'assess': argv += ['--bindings', str(binding)]
                with self.subTest(command=command), patch('material_calculations.extract', return_value=response) as adapter, \
                        patch.object(materials, 'connect') as database, \
                        patch('material_calculations.suggestions', return_value={}), \
                        patch('material_calculations.assess', return_value={}), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(materials.main(argv), 0)
                    adapter.assert_called_once_with(Path('model.bimc'), 'bimcraft', mesh_quantities=True)

    def test_family_reads_are_batched_once_and_only_when_needed(self):
        element = row(); element.pop('mirrored')
        other = dict(element, id=2)
        native = dict(element, id=3, family='Already quantified', volume_m3=.12)
        page = {'count': 3, 'returned': 3, 'elements': [element, other, native]}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'model.bimc'; path.write_text('fixture')
            with patch.object(bimcraft.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'bimcraft-cli 0.12.0\n', '')), \
                    patch.object(bimcraft, '_run', side_effect=[[{'types': {}}, page], [family()]]) as run:
                out = bimcraft.extract(path, mesh_quantities=True)
                self.assertEqual(run.call_count, 2)
                command = run.call_args_list[1].args[0]
                self.assertEqual(command.count('--cmd'), 1)
                self.assertIn('family {"name":"Imported body"}', command)
                self.assertEqual(out['extraction']['commands'][-1], command)
                self.assertAlmostEqual(out['elements'][0]['volume_m3'], .05)
            with patch.object(bimcraft.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'bimcraft-cli 0.12.0\n', '')), \
                    patch.object(bimcraft, '_run', side_effect=[[{'types': {}}, page], ValueError('lookup broken')]):
                out = bimcraft.extract(path, mesh_quantities=True)
                self.assertIn('unsupported_mesh_quantity', {w['code'] for w in out['warnings']})
                self.assertTrue(any('lookup broken' in w['message'] for w in out['warnings']))
            with patch.object(bimcraft.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'bimcraft-cli 0.12.0\n', '')), \
                    patch.object(bimcraft, '_run', return_value=[{'types': {}}, page]) as run:
                out = bimcraft.extract(path)
                self.assertEqual(run.call_count, 1)
                self.assertIsNone(out['elements'][0]['volume_m3'])


if __name__ == '__main__': unittest.main()
