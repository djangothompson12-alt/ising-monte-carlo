"""Keep the main GitHub reading path short and free of local-only links."""
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('README.md', 'EXTERNAL_REVIEW.md', 'docs/README.md',
         'docs/START_HERE.md', 'docs/REVIEWER_START_HERE.md',
         'docs/ACADEMIC_REVIEW_BRIEF_2026-09-20.md', 'manuscript/README.md',
         'research/README.md', 'research/results/README.md')


class PublicNavigationTests(unittest.TestCase):
    def test_local_reading_links_exist(self):
        for name in PAGES:
            page = ROOT/name
            for destination in re.findall(r'\]\(([^)]+)\)', page.read_text()):
                if destination.startswith(('https://', 'http://', '#', 'mailto:')):
                    continue
                path = unquote(destination.split('#')[0])
                with self.subTest(page=name, link=path):
                    self.assertTrue((page.parent/path).exists(), path)

    def test_no_private_artifacts_in_main_navigation(self):
        for name in PAGES:
            for link in re.findall(r'\]\(([^)]+)\)', (ROOT/name).read_text()):
                with self.subTest(page=name, link=link):
                    self.assertNotIn('/Users/', link)
                    self.assertNotIn('output/', link)
                    self.assertNotIn('admissions_and_external', link)
                    self.assertNotIn('OUTREACH_DRAFTS', link)

    def test_front_page_stays_short_and_discloses_assistance(self):
        text = (ROOT/'README.md').read_text()
        self.assertLess(len(text.split()), 850)
        self.assertIn('AI_USE_AND_CONTRIBUTIONS.md', text)
        self.assertIn('not a calibrated model', text)


if __name__ == '__main__':
    unittest.main()
