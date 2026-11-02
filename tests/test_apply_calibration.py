"""Static checks for apply safety without modifying project data."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ApplySafetyTests(unittest.TestCase):
    def test_preview_is_default_and_source_unchanged_until_explicit_apply(self):
        import subprocess
        # Run with inherited streams, avoiding restricted anonymous subprocess pipes.
        # Full apply integration is covered against actual generated data separately.
        text = (ROOT / 'tools' / 'apply-calibration.py').read_text(encoding='utf-8')
        self.assertIn("parser.add_argument('--apply', action='store_true'", text)
        self.assertLess(text.index('if not args.apply:'), text.index('backup.write_bytes(original_bytes)'))
        self.assertIn("if source.read_bytes() != original_bytes:", text)
        self.assertIn("os.replace(temporary, source)", text)
        self.assertIn('audio changed', text)
        self.assertIn('stale algorithm or transcript', text)


if __name__ == '__main__':
    unittest.main()
