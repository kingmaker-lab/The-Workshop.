"""Testes offline do conteúdo importado do Ruby Protocol CLI.
Executa APENAS as soluções conhecidas, incluídas pelo autor no source/lessons.rb.
"""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ExportIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lessons = json.loads((ROOT / 'data' / 'lessons.json').read_text())

    def test_twelve_lessons(self):
        self.assertEqual(len(self.lessons), 12)
        self.assertEqual([v['id'] for v in self.lessons], list(range(1, 13)))

    def test_all_have_teaching_content(self):
        for item in self.lessons:
            for key in ('act', 'title', 'theory', 'example', 'task', 'hint', 'solution'):
                self.assertTrue(item[key].strip(), f'Faltando {key} em {item["id"]}')
            self.assertGreater(len(item['cases']), 0)

    def test_canonical_ruby_solutions(self):
        count = 0
        for lesson in self.lessons:
            for case in lesson['cases']:
                proc = subprocess.run(['ruby', '--disable-gems', '-e', lesson['solution']],
                    input=case['input'], text=True, capture_output=True, timeout=5)
                self.assertEqual(proc.returncode, 0, (lesson['id'], proc.stderr))
                self.assertEqual(proc.stdout.replace('\r\n','\n').rstrip('\n'),
                    case['output'].replace('\r\n','\n').rstrip('\n'), lesson['id'])
                count += 1
        print(f'\nSoluções Ruby verificadas: {count} casos de teste.')

    def test_assets_present(self):
        for path in ('index.html', 'assets/styles.css', 'js/app.js', 'js/ruby-worker.js', 'downloads/wolfpack-ruby-protocol-v0.1.zip'):
            self.assertTrue((ROOT / path).is_file(), path)

if __name__ == '__main__':
    unittest.main()
