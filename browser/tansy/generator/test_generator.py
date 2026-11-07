#!/usr/bin/env python3
"""Focused regression checks for case isolation and displayed precision."""
import importlib.util
import sys
import unittest
from pathlib import Path
import openpyxl

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent

def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

build, check = module('build'), module('check')

class GeneratorTests(unittest.TestCase):
    def test_numeric_formats_remain_numeric_and_display_exactly(self):
        for value, style, text in [(0.8455, 'dec4', '0.8455'), (2.84, 'ratio', '2.84:1'), (6.1, 'ratio', '6.10:1'), (609.8, 'dec1', '609.8')]:
            self.assertEqual(build.render_text('{{value|' + style + '}}', {'value': value}), text)
            actual, fmt = build.table_cell('{{value|' + style + '}}', {'value': value})
            cell = openpyxl.Workbook().active['A1']
            cell.value, cell.number_format = actual, fmt
            self.assertEqual(actual, value)
            self.assertEqual(check.displayed_cell(cell), text)

    def test_checker_rejects_wrong_workbook_precision(self):
        check.DIST = ROOT / 'dist/pub-tansy'
        room = check.Room(ROOT / 'cases/pub-tansy')
        fact = {'xlsx': '4.1', 'version': 2, 'sheet': 'Census', 'row': 'Total', 'col': 'FTE', 'value': 609.8, 'text': '609.8'}
        self.assertEqual(room.value(fact), 609.8)
        ws = room.book(room.resolve('4.1', 2))['Census']
        ws['C9'].number_format = '0.00'
        with self.assertRaisesRegex(KeyError, 'displays'):
            room.value(fact)

    def test_checker_rejects_rounded_pdf_and_html_text(self):
        check.DIST = ROOT / 'dist/pub-tansy'
        room = check.Room(ROOT / 'cases/pub-tansy')
        for index, value, text, bad in [('2.2', .8455, '0.8455', '0.8'), ('2.7', 3.0, '3.00:1', '3.0:1')]:
            doc = room.resolve(index)
            fact = {'doc': index, 'value': value, 'text': text}
            self.assertEqual(room.value(fact), value)
            room._text[doc['id']] = room.text(doc).replace(text, bad)
            with self.assertRaises(KeyError):
                room.value(fact)

    def test_non_food_series_and_mismatched_months(self):
        series = {'derive_groups': ['services'], 'derived': {'revenue': ['+maintenance', '+monitoring']}, 'services': {'maintenance': [10, 12], 'monitoring': [3, 4]}}
        self.assertEqual(build.derive_series(series)['services']['revenue'], [13, 16])
        series['services']['monitoring'] = [3]
        with self.assertRaises(build.BuildError):
            build.derive_series(series)

    def test_revised_evidence_is_exact_and_still_verified(self):
        case = ROOT / 'cases/pub-tansy'
        check.DIST = ROOT / 'dist/pub-tansy'
        room = check.Room(case)
        for revision in check.load_json(case / 'evidence-revisions.json')['revisions']:
            original = revision['original']
            revised = check.revised_evidence(case, revision['request'], original)
            self.assertEqual(revised['value'], original['value'])
            self.assertEqual(check.revised_evidence(case, 999, original), original)
            if 'doc' in revised:
                self.assertEqual(room.value(revised), original['value'])
                doc = room.resolve(revised['doc'], revised.get('version'))
                room._text[doc['id']] = ''
                with self.assertRaises(KeyError):
                    room.value(revised)
                room._text.pop(doc['id'])
            else:
                doc = room.resolve(revised['index'], revised.get('version'))
                self.assertEqual(doc['file'], revised['file'])
                self.assertTrue((check.DIST / 'files' / revised['file']).is_file())

    def test_output_guard_fails_before_mutation(self):
        before = (ROOT / 'dist/pub-tansy/data/index.json').read_bytes()
        for case, out in [('pub-tansy', ROOT / 'verification/not-dist'), ('../pub-tansy', ROOT / 'dist')]:
            with self.assertRaises(build.BuildError):
                build.build(case, out)
        self.assertFalse((ROOT / 'verification/not-dist').exists())
        self.assertEqual((ROOT / 'dist/pub-tansy/data/index.json').read_bytes(), before)

if __name__ == '__main__':
    unittest.main()
