"""Fast audio length audit. Bounds alone never establish actual synchronization."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.tools' / 'speech'))
import av

data = json.loads((ROOT / 'episodes.json').read_text(encoding='utf-8'))
report = []
for episode in data['episodes']:
    for ai, act in enumerate(episode['acts'], 1):
        with av.open(str(ROOT / act['audio'])) as container:
            duration = container.duration / av.time_base
        invalid = [{'line': i, 't': line['t'], 'en': line['en']} for i, line in enumerate(act['lines']) if not 0 <= line['t'] < duration]
        report.append({'episode': episode['id'], 'act': ai, 'duration': round(duration, 3), 'invalidCount': len(invalid), 'invalidLines': invalid})
path = ROOT / 'diagnostics' / 'audio-bounds-audit.json'
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({'acts': len(report), 'actsWithInvalidTimes': sum(bool(r['invalidCount']) for r in report), 'invalidLines': sum(r['invalidCount'] for r in report)}, indent=2))
