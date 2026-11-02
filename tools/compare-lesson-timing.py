"""Compare known transcript to locally recognized words, without modifying source data."""
import argparse
import difflib
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower().replace("’", "'"))
data = json.loads((ROOT / 'episodes.json').read_text(encoding='utf-8'))
parser = argparse.ArgumentParser()
parser.add_argument('--episode', type=int, default=1)
args = parser.parse_args()
episode = next(e for e in data['episodes'] if e['id'] == args.episode)
for ai, act in enumerate(episode['acts'], 1):
    source = ROOT / 'diagnostics' / f'e{args.episode:02d}_a{ai}-recognition.json'
    if not source.exists():
        continue
    recognized = json.loads(source.read_text(encoding='utf-8'))
    ref, owners, hyp, timings = [], [], [], []
    for li, line in enumerate(act['lines']):
        parts = tokens(line['en'])
        ref.extend(parts)
        owners.extend([li] * len(parts))
    for segment in recognized['segments']:
        for word in segment['words']:
            parts = tokens(word['word'])
            hyp.extend(parts)
            timings.extend([word] * len(parts))
    mapped = {}
    for block in difflib.SequenceMatcher(None, ref, hyp, autojunk=False).get_matching_blocks():
        for i in range(block.size):
            mapped[block.a + i] = timings[block.b + i]
    output = []
    for li, line in enumerate(act['lines']):
        indexes = [i for i, owner in enumerate(owners) if owner == li]
        matched = [mapped[i] for i in indexes if i in mapped]
        start = mapped.get(indexes[0]) if indexes else None
        item = {'line': li, 'old': line.get('originalT', line['t']), 'en': line['en'], 'matched': len(matched), 'tokens': len(indexes),
                'recognizedStart': start['start'] if start else None,
                'recognizedEnd': matched[-1]['end'] if matched else None,
                'delta': round(line.get('originalT', line['t']) - start['start'], 3) if start else None}
        output.append(item)
        print(ai, li, line.get('originalT', line['t']), item['recognizedStart'], item['delta'], f"{len(matched)}/{len(indexes)}", line['en'])
    (ROOT / 'diagnostics' / f'e{args.episode:02d}_a{ai}-comparison.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
