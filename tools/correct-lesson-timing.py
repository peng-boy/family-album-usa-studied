"""Apply conservative, auditable correction to one explicitly selected episode."""
import argparse
import json
import statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'episodes.json'
data = json.loads(path.read_text(encoding='utf-8'))
report = []
parser = argparse.ArgumentParser()
parser.add_argument('--episode', type=int, default=1)
args = parser.parse_args()
episode = next(e for e in data['episodes'] if e['id'] == args.episode)
for ai, act in enumerate(episode['acts'], 1):
    comparisons = json.loads((ROOT / 'diagnostics' / f'e{args.episode:02d}_a{ai}-comparison.json').read_text(encoding='utf-8'))
    recognition = json.loads((ROOT / 'diagnostics' / f'e{args.episode:02d}_a{ai}-recognition.json').read_text(encoding='utf-8'))
    reliable = [x['delta'] for x in comparisons if x['delta'] is not None and x['tokens'] >= 4 and x['matched'] / x['tokens'] >= .8]
    if len(reliable) < 5:
        raise ValueError(f'Act {ai}: insufficient matched sentences for calibration')
    offset = round(statistics.median(reliable), 3)
    residual = statistics.median(abs(value - offset) for value in reliable)
    if residual > 1.5:
        raise ValueError(f'Act {ai}: inconsistent offsets (MAD={residual:.2f}s); inspect edits/drift manually')
    # Episode 2 Act I has a confirmed scene-edit discontinuity before line 21.
    boundaries = [0, 21, len(act['lines'])] if args.episode == 2 and ai == 1 else [0, len(act['lines'])]
    regions = []
    for begin, end in zip(boundaries, boundaries[1:]):
        deltas = [x['delta'] for x in comparisons[begin:end] if x['delta'] is not None and x['tokens'] >= 4 and x['matched'] / x['tokens'] >= .8]
        if len(deltas) < 5:
            raise ValueError('Insufficient regional anchors')
        region_offset = round(statistics.median(deltas), 3)
        if statistics.median(abs(x - region_offset) for x in deltas) > 1.5:
            raise ValueError('Regional offsets inconsistent')
        regions.append({'startLine': begin, 'endLineExclusive': end, 'offsetSeconds': region_offset})
    corrections = []
    candidates = []
    for li, (line, comparison) in enumerate(zip(act['lines'], comparisons)):
        offset = next(r['offsetSeconds'] for r in regions if r['startLine'] <= li < r['endLineExclusive'])
        original = line.get('originalT', line['t'])
        baseline = round(max(0, original - offset), 3)
        # Recognition can swallow pauses or omit words: never accept a large outlier automatically.
        refined = (comparison['delta'] is not None and comparison['tokens'] >= 3
                   and comparison['matched'] / comparison['tokens'] >= .8
                   and abs(comparison['delta'] - offset) <= .8)
        start = comparison['recognizedStart'] if refined else baseline
        candidates.append({'original': original, 'baseline': baseline, 'start': start, 'source': 'recognized-near-offset' if refined else 'offset-estimate'})
    # Fall back to the original ordered time axis if a local refinement crosses a neighbour.
    for i in range(len(candidates) - 1):
        if candidates[i]['start'] > candidates[i + 1]['start']:
            for j in (i, i + 1):
                candidates[j]['start'] = candidates[j]['baseline']
                candidates[j]['source'] = 'offset-estimate'
    for li, (line, candidate) in enumerate(zip(act['lines'], candidates)):
        line['originalT'] = candidate['original']
        line['t'] = candidate['start']
        corrections.append({'line': li, 'en': line['en'], 'originalT': candidate['original'], 't': line['t'], 'source': candidate['source']})
    assert all(a['t'] <= b['t'] for a, b in zip(act['lines'], act['lines'][1:]))
    assert all(0 <= line['t'] < recognition['duration'] for line in act['lines'])
    offset = regions[0]['offsetSeconds'] if len(regions) == 1 else None
    act['timingCalibration'] = {'method': 'local-whisper-base.en-with-conservative-offset', 'offsetSeconds': offset, 'regions': regions,
                                'audioDuration': recognition['duration'], 'precision': 'approximate; not manually verified',
                                'report': f'diagnostics/e{args.episode:02d}_a{ai}-timing-correction.json'}
    (ROOT / 'diagnostics' / f'e{args.episode:02d}_a{ai}-timing-correction.json').write_text(json.dumps({'offsetSeconds': offset, 'regions': regions, 'lines': corrections}, indent=2, ensure_ascii=False), encoding='utf-8')
    report.append({'act': ai, 'offset': offset, 'refined': sum(x['source'] == 'recognized-near-offset' for x in corrections), 'estimated': sum(x['source'] == 'offset-estimate' for x in corrections)})
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
