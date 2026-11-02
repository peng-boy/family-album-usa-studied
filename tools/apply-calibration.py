"""Validate and explicitly apply eligible batch candidates, preserving other episodes."""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Without this flag only validate and report')
    args = parser.parse_args()
    source = ROOT / 'episodes.json'
    original_bytes = source.read_bytes()
    current = json.loads(original_bytes)
    candidate = json.loads((ROOT / 'diagnostics' / 'episodes-calibrated.json').read_text(encoding='utf-8'))
    summary = json.loads((ROOT / 'diagnostics' / 'batch' / 'summary.json').read_text(encoding='utf-8'))
    output = copy.deepcopy(current)
    applied, skipped = [], []
    for report in summary['acts']:
        key = report['key']
        ei, ai = int(key[1:3]) - 1, int(key[-1]) - 1
        if not report['eligible']:
            skipped.append(key)
            continue
        src = current['episodes'][ei]['acts'][ai]
        dst = candidate['episodes'][ei]['acts'][ai]
        detail = json.loads((ROOT / 'diagnostics' / 'batch' / f'{key}-alignment.json').read_text(encoding='utf-8'))
        if report != {k: v for k, v in detail.items() if k != 'lines'}:
            raise ValueError(f'{key}: summary/detail differ; finish rerun before applying')
        algorithm = hashlib.sha256((ROOT / 'tools' / 'batch-calibrate.py').read_bytes()).hexdigest()
        transcript = hashlib.sha256(json.dumps([(l['en'], l.get('originalT', l['t'])) for l in src['lines']], ensure_ascii=False).encode('utf-8')).hexdigest()
        if detail.get('algorithmSha256') != algorithm or detail.get('transcriptSha256') != transcript:
            raise ValueError(f'{key}: stale algorithm or transcript; rerun --align-only')
        digest = hashlib.sha256((ROOT / src['audio']).read_bytes()).hexdigest()
        if digest != detail['audioSha256']:
            raise ValueError(f'{key}: audio changed')
        if len(src['lines']) != len(dst['lines']) or len(dst['lines']) != len(detail['lines']):
            raise ValueError(f'{key}: line count mismatch')
        previous = -1
        for before, after, row in zip(src['lines'], dst['lines'], detail['lines']):
            if before['en'] != after['en'] or before.get('cn') != after.get('cn') or after['en'] != row['en']:
                raise ValueError(f'{key}: transcript changed')
            if before.get('originalT', before['t']) != after['originalT'] or row['originalT'] != after['originalT']:
                raise ValueError(f'{key}: original time mismatch')
            t = after['t']
            if not math.isfinite(t) or not 0 <= t < detail['duration'] or t < previous or t != row['t']:
                raise ValueError(f'{key}: unsafe timestamp')
            previous = t
        output['episodes'][ei]['acts'][ai] = dst
        applied.append(key)
    print(json.dumps({'eligibleActs': len(applied), 'unchangedActs': skipped, 'apply': args.apply}, indent=2))
    if not args.apply:
        return
    backup = ROOT / 'diagnostics' / f'episodes-before-batch-{time.time_ns()}.json'
    backup.write_bytes(original_bytes)
    temporary = ROOT / 'episodes.json.tmp'
    temporary.write_text(json.dumps(output, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    if source.read_bytes() != original_bytes:
        raise ValueError('Source changed during apply; leaving original untouched')
    os.replace(temporary, source)
    receipt = {'appliedActs': applied, 'skippedActs': skipped, 'backup': str(backup.relative_to(ROOT)),
               'beforeSha256': hashlib.sha256(original_bytes).hexdigest(),
               'afterSha256': hashlib.sha256(source.read_bytes()).hexdigest()}
    (ROOT / 'diagnostics' / 'batch' / 'application-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('APPLIED', len(applied), 'acts. Backup:', backup)


if __name__ == '__main__':
    main()
