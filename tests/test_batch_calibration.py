import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('batch', Path(__file__).resolve().parents[1] / 'tools' / 'batch-calibrate.py')
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


def fixture(offsets, missing=()):
    lines, words = [], []
    for i, offset in enumerate(offsets):
        text = f'phrase{i} alpha{i} beta{i} gamma{i}'
        old = 20 + i * 10
        lines.append({'t': old, 'en': text})
        if i not in missing:
            for j, word in enumerate(text.split()):
                start = old - offset + j * .2
                words.append({'word': word, 'start': start, 'end': start + .15, 'probability': .95})
    return lines, {'duration': 300, 'segments': [{'words': words}]}


class AlignmentTests(unittest.TestCase):
    def test_constant_offset(self):
        lines, audio = fixture([5] * 12)
        report = batch.align(lines, audio)
        self.assertTrue(report['eligible'])
        self.assertEqual(report['lines'][0]['t'], 15)
        self.assertEqual(lines[0]['t'], 20, 'alignment must not mutate source')

    def test_scene_discontinuity_preserved(self):
        lines, audio = fixture([5] * 6 + [-15] * 6)
        report = batch.align(lines, audio)
        self.assertFalse(report['eligible'], 'unreviewed scene jump must not auto-apply')
        self.assertEqual(report['lines'][6]['t'], 95)
        self.assertTrue(report['discontinuities'])

    def test_isolated_silence_outlier_is_not_anchor(self):
        offsets = [5] * 12
        offsets[5] = 14
        lines, audio = fixture(offsets)
        report = batch.align(lines, audio)
        self.assertFalse(report['eligible'])
        self.assertTrue(report['lines'][5]['needsReview'])
        self.assertIsNone(report['lines'][5]['t'])
        self.assertEqual(report['lines'][5]['source'], 'offset-conflict')

    def test_missing_middle_is_flagged_interpolation(self):
        lines, audio = fixture([5] * 12, missing=(5,))
        # Compact this synthetic gap to satisfy the conservative 15-second limit.
        for line in lines:
            line['t'] /= 2
        for word in audio['segments'][0]['words']:
            word['start'] /= 2
            word['end'] /= 2
        report = batch.align(lines, audio)
        self.assertTrue(report['eligible'])
        self.assertEqual(report['lines'][5]['source'], 'interpolated-review')
        self.assertEqual(report['reviewCount'], 1)

    def test_insufficient_anchors_reject_entire_act(self):
        lines, audio = fixture([5] * 12, missing=tuple(range(2, 12)))
        self.assertFalse(batch.align(lines, audio)['eligible'])

    def test_short_real_scene_must_not_be_erased_as_an_outlier(self):
        lines, audio = fixture([5,5,5,5,8,8,5,5,5,5,5,5])
        report = batch.align(lines, audio)
        self.assertFalse(report['eligible'])
        self.assertEqual(report['lines'][4]['source'], 'offset-conflict')
        self.assertIsNone(report['lines'][4]['t'])

    def test_three_consistent_outliers_still_require_scene_review(self):
        lines, audio = fixture([5]*4 + [9]*3 + [5]*5)
        report = batch.align(lines, audio)
        self.assertFalse(report['eligible'])
        self.assertTrue(report['discontinuities'])

    def test_repeated_long_phrase_is_not_a_unique_anchor(self):
        lines, audio = fixture([5] * 12)
        lines[3]['en'] = lines[2]['en']
        report = batch.align(lines, audio)
        self.assertTrue(report['lines'][2]['needsReview'])
        self.assertTrue(report['lines'][3]['needsReview'])

    def test_alignment_is_deterministic_and_does_not_accumulate_offsets(self):
        lines, audio = fixture([5] * 12)
        first = batch.align(lines, audio)
        calibrated = [dict(line, originalT=line['t'], t=row['t']) for line, row in zip(lines, first['lines'])]
        second = batch.align(calibrated, audio)
        self.assertEqual(first, second)

    def test_missing_sentence_across_scene_edit_stays_unresolved(self):
        lines, audio = fixture([5] * 6 + [-15] * 6, missing=(5, 6))
        report = batch.align(lines, audio)
        self.assertFalse(report['eligible'])
        self.assertIsNone(report['lines'][5]['t'])
        self.assertIsNone(report['lines'][6]['t'])

    def test_long_word_cannot_be_a_trusted_anchor(self):
        lines, audio = fixture([5] * 12)
        audio['segments'][0]['words'][20]['end'] += 4
        report = batch.align(lines, audio)
        self.assertTrue(report['lines'][5]['needsReview'])

    def test_out_of_bounds_is_rejected(self):
        lines, audio = fixture([5] * 12)
        audio['duration'] = 25
        self.assertFalse(batch.align(lines, audio)['eligible'])


if __name__ == '__main__':
    unittest.main()
