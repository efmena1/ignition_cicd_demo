# -*- coding: utf-8 -*-
"""Behavior tests, runnable with CPython and Ignition's installed Jython."""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = os.path.join(HERE, 'project', 'ignition', 'script-python', 'atsThemeLibrary')
sys.path.insert(0, MODULE)
import code as lib


class ThemeTests(unittest.TestCase):
    def setUp(self):
        self.sandbox = tempfile.mkdtemp(prefix='test-', dir=HERE)
        self.original_dir = lib.data_dir
        lib.data_dir = lambda: self.sandbox
        self.theme_path = os.path.join(self.sandbox, 'config', 'resources', 'core',
                                       'com.inductiveautomation.perspective', 'themes')
        os.makedirs(self.theme_path)

    def tearDown(self):
        lib.data_dir = self.original_dir
        sandbox = os.path.realpath(self.sandbox)
        assert os.path.dirname(sandbox) == os.path.realpath(HERE)
        assert os.path.basename(sandbox).startswith('test-')
        shutil.rmtree(sandbox)

    def changed(self, base, changes):
        rows = lib.rows_for(base)
        for row in rows:
            if row['name'] in changes:
                row['value'] = changes[row['name']]
        return rows

    def test_catalog_complete_for_six_themes(self):
        all_names = set()
        for theme in lib.BUILTINS:
            rows = lib.rows_for(theme)
            self.assertEqual(len(rows), 120)
            self.assertEqual(sum(r['selector'] == ':root' for r in rows), 118)
            self.assertFalse(any(r['changed'] for r in rows))
            self.assertFalse(any('var(' in r['resolved'] for r in rows))
            all_names.update(r['name'] for r in rows)
        self.assertEqual(len(all_names), 121)

    def test_aliases_recalculate_without_flattening(self):
        rows = lib.decorate(self.changed('light', {'--neutral-10': '#112233'}))
        root = next(r for r in rows if r['name'] == '--containerRoot')
        self.assertEqual(root['value'], 'var(--neutral-10)')
        self.assertEqual(root['resolved'], '#112233')
        css = lib.css_for('light', rows)
        self.assertIn('--neutral-10: #112233;', css)
        self.assertNotIn('--containerRoot:', css)

    def test_cycles_and_unknown_references_rejected(self):
        rows = self.changed('light', {'--neutral-10': 'var(--containerRoot)'})
        self.assertRaises(ValueError, lib.css_for, 'light', rows)
        rows = self.changed('light', {'--neutral-10': 'var(--unknown)'})
        self.assertRaises(ValueError, lib.css_for, 'light', rows)

    def test_fallbacks_and_nested_functions(self):
        rows = lib.decorate(self.changed('light', {'--neutral-10': 'var(--unknown, rgb(1, 2, 3))'}))
        self.assertEqual(next(r['resolved'] for r in rows if r['name'] == '--containerRoot'), 'rgb(1, 2, 3)')
        rows = lib.decorate(self.changed('light', {'--neutral-10': 'var(--unknown, var(--white))'}))
        self.assertEqual(next(r['resolved'] for r in rows if r['name'] == '--containerRoot'), '#FFFFFF')

    def test_scope_of_slider_is_preserved(self):
        rows = self.changed('dark', {'--defaultSliderFocusColor': '#AABBCC'})
        css = lib.css_for('dark', rows)
        self.assertIn('.ia_slider__handle:focus {', css)
        self.assertNotIn(':root {', css)

    def test_invalid_values_and_paths_rejected(self):
        for name in ('light', 'dark', '../escape', 'C:/escape', 'ats/x', 'nul', 'com1', 'ATS', ''):
            self.assertRaises(ValueError, lib.validate_name, name)
        for value in ('red; color: blue', '} body {', 'url(http://x)', 'var(--x', '/*x*/red', ''):
            self.assertRaises(ValueError, lib.validate_value, value)

    def test_theme_inherits_full_base_and_only_changes(self):
        rows = self.changed('dark-warm', {'--callToAction': '#ABCDEF'})
        files = lib.files_for('ats-brand-dark', 'dark-warm', rows)
        self.assertEqual(files['index.css'], '@import "../dark-warm/index.css";\n@import "./overrides.css";\n')
        self.assertEqual(files['overrides.css'].count('--callToAction:'), 1)
        self.assertNotIn('--neutral-10:', files['overrides.css'])
        self.assertFalse(json.loads(files['config.json'])['isPrivate'])
        resource = json.loads(files['resource.json'])
        self.assertEqual(set(resource['files']), set(files) - {'resource.json'})

    def test_manifest_round_trip_and_version_guard(self):
        rows = self.changed('light-cool', {'--callToAction': '#ABCDEF'})
        data = lib.manifest_for('ats-brand', 'light-cool', rows)
        base, loaded, name = lib.decode_manifest(json.dumps(data))
        self.assertEqual(base, 'light-cool')
        self.assertEqual(name, 'ats-brand')
        self.assertEqual(lib.css_for(base, loaded), lib.css_for(base, rows))
        data['catalogSha256'] = 'other-version'
        self.assertRaises(ValueError, lib.decode_manifest, json.dumps(data))

    def test_save_new_and_reopen_without_overwriting(self):
        rows = self.changed('dark', {'--callToAction': '#AABBCC'})
        path = lib.save_new('ats-test', 'dark', rows)
        self.assertEqual(os.path.dirname(path), self.theme_path)
        self.assertEqual(set(os.listdir(path)), set(lib.files_for('ats-test', 'dark', rows)))
        self.assertEqual(lib.load_theme('ats-test')[0], 'dark')
        self.assertEqual(len(lib.theme_options()), 7)
        self.assertRaises(ValueError, lib.save_new, 'ats-test', 'light', lib.rows_for('light'))
        self.assertEqual(lib.load_theme('ats-test')[0], 'dark')

    def test_zip_round_trip(self):
        rows = lib.rows_for('light')
        data = lib.export_zip('ats-test', 'light', rows)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertEqual(len(archive.namelist()), 5)
            self.assertEqual(json.loads(archive.read('ats-test/config.json').decode('utf-8'))['entrypoint'], 'index.css')

    def test_partial_write_does_not_publish(self):
        original = lib.os.rename
        def fail(*args):
            raise OSError('simulated publication failure')
        lib.os.rename = fail
        try:
            self.assertRaises(OSError, lib.save_new, 'ats-failed', 'light', lib.rows_for('light'))
        finally:
            lib.os.rename = original
        self.assertFalse(os.path.exists(os.path.join(self.theme_path, 'ats-failed')))
        self.assertEqual(os.listdir(os.path.join(self.sandbox, 'var')), [])

    def test_all_view_event_scripts_compile(self):
        path = os.path.join(HERE, 'project', 'com.inductiveautomation.perspective', 'views',
                            'ATS Global', 'Tools', 'Theme Library', 'view.json')
        with io.open(path, encoding='utf-8') as handle:
            view = json.load(handle)
        count = [0]
        def visit(node):
            for group in node.get('events', {}).values():
                for action in group.values():
                    script = action['config']['script']
                    wrapped = 'def runAction(self, event):\n' + '\n'.join('    ' + line for line in script.splitlines())
                    compile(wrapped, node['meta']['name'], 'exec')
                    count[0] += 1
            for child in node.get('children', []):
                visit(child)
        visit(view['root'])
        self.assertEqual(count[0], 9)


if __name__ == '__main__':
    unittest.main(verbosity=2)
