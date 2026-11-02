"""Resumable local ASR + conservative transcript alignment. No audio is uploaded.
Default writes a candidate dataset and reports, never overwrites episodes.json.
"""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = 1


def tokens(text):
    text = text.lower().replace('’', "'")
    return re.findall(r'[a-z0-9]+', text)


def align(lines, recognition):
    reference, owners, hypothesis, words = [], [], [], []
    spans = []
    for li, line in enumerate(lines):
        begin = len(reference)
        parts = tokens(line['en'])
        reference.extend(parts)
        owners.extend([li] * len(parts))
        spans.append((begin, len(reference)))
    for segment in recognition['segments']:
        for word in segment['words']:
            parts = tokens(word['word'])
            hypothesis.extend(parts)
            words.extend([word] * len(parts))
    from collections import Counter
    phrase_counts = Counter(tuple(tokens(line['en'])) for line in lines)
    mapped = {}
    for block in difflib.SequenceMatcher(None, reference, hypothesis, autojunk=False).get_matching_blocks():
        for i in range(block.size):
            mapped[block.a + i] = block.b + i
    result = []
    duration = recognition['duration']
    for li, (begin, end) in enumerate(spans):
        matches = [i for i in range(begin, end) if i in mapped]
        ratio = len(matches) / max(1, end - begin)
        first = words[mapped[begin]] if begin in mapped else None
        last = words[mapped[matches[-1]]] if matches else None
        # A short repeated reply is not a trustworthy anchor. Require consecutive opening words.
        opening = all(i in mapped for i in range(begin, min(end, begin + 3)))
        contiguous = opening and all(mapped[i] == mapped[begin] + i - begin for i in range(begin, min(end, begin + 3)))
        matched_words = [words[mapped[i]] for i in matches]
        acoustic_ok = all(0 < w['end'] - w['start'] <= 1.2 for w in matched_words)
        acoustic_ok = acoustic_ok and all(b['start'] - a['end'] <= 1.5 for a, b in zip(matched_words, matched_words[1:]))
        mean_probability = sum(w.get('probability', 0) for w in matched_words) / max(1, len(matched_words))
        unique = phrase_counts[tuple(reference[begin:end])] == 1
        credible = bool(first and last and end - begin >= 4 and ratio >= .85 and contiguous and acoustic_ok
                        and unique and end - 1 in mapped and mean_probability >= .8
                        and first.get('probability', 0) >= .6
                        and 0 <= first['start'] < last['end'] <= duration
                        and last['end'] - first['start'] <= max(8, (end - begin) * 1.4))
        result.append({'line': li, 'originalT': lines[li].get('originalT', lines[li]['t']),
                       'en': lines[li]['en'], 'coverage': round(ratio, 3),
                       'asrStart': first['start'] if first else None,
                       'asrEnd': last['end'] if last else None,
                       't': first['start'] if credible else None,
                       'source': 'matched-anchor' if credible else 'unresolved',
                       'needsReview': not credible})
    # ASR sometimes attaches the first word to preceding silence, even with a
    # perfect text match. Drop isolated offset outliers, but retain sustained jumps.
    import statistics
    initial = [i for i, row in enumerate(result) if row['t'] is not None]
    initial_offsets = {i: result[i]['originalT'] - result[i]['t'] for i in initial}
    for position, i in enumerate(initial):
        neighbours = initial[max(0, position - 3):position] + initial[position + 1:position + 4]
        if len(neighbours) < 3:
            continue
        offsets = [initial_offsets[j] for j in neighbours]
        own = initial_offsets[i]
        if abs(own - statistics.median(offsets)) > 2.5 and sum(abs(own - value) <= 1.5 for value in offsets) < 2:
            result[i].update(t=None, source='offset-conflict', needsReview=True)
    anchors = [i for i, row in enumerate(result) if row['t'] is not None]
    # Estimate only BETWEEN trusted anchors. Preserve original local spacing if both
    # offsets agree, otherwise interpolate within that single gap and flag for review.
    for left, right in zip(anchors, anchors[1:]):
        a, b = result[left], result[right]
        for i in range(left + 1, right):
            row = result[i]
            old_width = b['originalT'] - a['originalT']
            fraction = ((row['originalT'] - a['originalT']) / old_width if old_width > 0 else (i - left) / (right - left))
            fraction = min(1, max(0, fraction))
            left_offset = a['originalT'] - a['t']
            right_offset = b['originalT'] - b['t']
            # Never manufacture timing across a scene edit or a long unanchored gap.
            conflict = any(r['source'] == 'offset-conflict' for r in result[left + 1:right])
            if not conflict and abs(left_offset - right_offset) <= .75 and b['t'] - a['t'] <= 15 and right - left <= 3:
                row['t'] = round(a['t'] + (b['t'] - a['t']) * fraction, 3)
                row['source'] = 'interpolated-review'
    # Stable scene-wide offset is stronger evidence than interpolating individual
    # short replies. Allow a conservative baseline only if anchor offsets form one
    # tight cluster spanning the act; still label every estimate for review.
    anchor_offsets = [result[i]['originalT'] - result[i]['t'] for i in anchors]
    stable_region = None
    if len(anchors) >= 8 and result[anchors[-1]]['t'] - result[anchors[0]]['t'] >= 30:
        median = statistics.median(anchor_offsets)
        residuals = sorted(abs(value - median) for value in anchor_offsets)
        p90 = residuals[min(len(residuals) - 1, int(.9 * len(residuals)))]
        if statistics.median(residuals) <= .35 and p90 <= .8 and max(residuals) <= 1.5 and not any(r['source'] == 'offset-conflict' for r in result):
            stable_region = round(median, 3)
            for row in result:
                if row['t'] is not None:
                    continue
                proposed = round(row['originalT'] - stable_region, 3)
                if 0 <= proposed < duration:
                    row.update(t=proposed, source='stable-offset-review')
    # Do not silently shift an unbounded opening or tail. Extrapolate only a short
    # distance using a nearby anchor; out-of-file or distant items keep original t.
    for i, row in enumerate(result):
        if row['t'] is not None or not anchors or row['source'] == 'offset-conflict':
            continue
        # Interior gaps rejected above stay unresolved (especially across edits).
        if anchors[0] < i < anchors[-1]:
            continue
        nearest = min(anchors, key=lambda j: abs(j - i))
        anchor = result[nearest]
        distance = abs(row['originalT'] - anchor['originalT'])
        candidate = row['originalT'] - anchor['originalT'] + anchor['t']
        if abs(nearest - i) <= 2 and distance <= 8 and 0 <= candidate < duration:
            row['t'] = round(candidate, 3)
            row['source'] = 'extrapolated-review'
    # Reject an entire act if coverage is too poor or timestamps cross; partial
    # application would mix two incompatible axes.
    complete = all(row['t'] is not None and 0 <= row['t'] < duration for row in result)
    ordered = complete and all(a['t'] <= b['t'] for a, b in zip(result, result[1:]))
    coverage = len(anchors) / max(1, len(lines))
    anchor_span = (result[anchors[-1]]['t'] - result[anchors[0]]['t']) if anchors else 0
    evidence_ok = coverage >= .45 and len(anchors) >= 8
    # A tight offset cluster spanning >=70% of the audio is independently useful
    # even in dialogue-heavy scenes with many one-word replies.
    stable_evidence = stable_region is not None and len(anchors) >= 12 and coverage >= .2 and anchor_span >= duration * .7
    eligible = bool(complete and ordered and (evidence_ok or stable_evidence))
    offsets = [result[i]['originalT'] - result[i]['t'] for i in anchors]
    jumps = [{'afterLine': a, 'beforeLine': b, 'offsetChange': round(offsets[k + 1] - offsets[k], 3)}
             for k, (a, b) in enumerate(zip(anchors, anchors[1:])) if abs(offsets[k + 1] - offsets[k]) >= 2]
    # Scene changes may be genuine edits OR recognition misalignment. Report them
    # without silently applying them; review needs independent acoustic evidence.
    eligible = eligible and not jumps
    blocked = []
    if not complete: blocked.append('unresolved-lines')
    if complete and not ordered: blocked.append('non-monotonic')
    if not (evidence_ok or stable_evidence): blocked.append('insufficient-anchor-evidence')
    if jumps: blocked.append('unreviewed-scene-discontinuity')
    return {'version': VERSION, 'duration': duration, 'eligible': eligible, 'blockedReasons': blocked,
            'anchorCount': len(anchors), 'lineCount': len(lines), 'anchorRatio': round(coverage, 3),
            'reviewCount': sum(r['needsReview'] for r in result), 'discontinuities': jumps, 'stableOffsetSeconds': stable_region,
            'complete': complete, 'ordered': ordered, 'lines': result}


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', type=int, default=3)
    parser.add_argument('--end', type=int, default=26)
    parser.add_argument('--model', default='base.en')
    parser.add_argument('--align-only', action='store_true')
    parser.add_argument('--recognize-only', action='store_true', help='Populate caches only; do not write shared candidate/summary')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / '.tools' / 'speech'))
    os.environ['HF_HOME'] = str(ROOT / '.tools' / 'huggingface')
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    data = json.loads((ROOT / 'episodes.json').read_text(encoding='utf-8'))
    model = None
    reports, errors = [], []
    for episode in data['episodes']:
        if not args.start <= episode['id'] <= args.end:
            continue
        for ai, act in enumerate(episode['acts'], 1):
            key = f"e{episode['id']:02d}_a{ai}"
            print('START', key, flush=True)
            try:
                audio = ROOT / act['audio']
                digest = hashlib.sha256(audio.read_bytes()).hexdigest()
                cache = ROOT / 'diagnostics' / 'batch' / f'{key}-recognition.json'
                recognition = json.loads(cache.read_text(encoding='utf-8')) if cache.exists() else None
                if not recognition or recognition.get('sha256') != digest or recognition.get('model') != args.model:
                    if args.align_only:
                        raise ValueError('Missing or stale recognition cache')
                    import av
                    import numpy as np
                    from faster_whisper import WhisperModel
                    if model is None:
                        model = WhisperModel(args.model, device='cpu', compute_type='int8', cpu_threads=6,
                                             download_root=str(ROOT / '.tools' / 'models'))
                    samples = []
                    with av.open(str(audio)) as container:
                        resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)
                        for frame in container.decode(audio=0):
                            for converted in resampler.resample(frame):
                                samples.append(converted.to_ndarray().flatten())
                        for converted in resampler.resample(None):
                            samples.append(converted.to_ndarray().flatten())
                    waveform = np.concatenate(samples).astype(np.float32) / 32768.0
                    segments, info = model.transcribe(waveform, language='en', word_timestamps=True, beam_size=5, vad_filter=False)
                    recognition = {'model': args.model, 'sha256': digest, 'audio': act['audio'], 'duration': info.duration, 'segments': []}
                    for s in segments:
                        recognition['segments'].append({'start': s.start, 'end': s.end, 'text': s.text,
                            'words': [{'word': w.word, 'start': round(w.start, 3), 'end': round(w.end, 3), 'probability': round(w.probability, 3)} for w in s.words or []]})
                    atomic_json(cache, recognition)
                if args.recognize_only:
                    print('CACHED', key, flush=True)
                    continue
                report = align(act['lines'], recognition)
                report.update({'key': key, 'audioSha256': digest, 'model': args.model,
                               'algorithmSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                               'transcriptSha256': hashlib.sha256(json.dumps([(l['en'], l.get('originalT', l['t'])) for l in act['lines']], ensure_ascii=False).encode('utf-8')).hexdigest()})
                atomic_json(ROOT / 'diagnostics' / 'batch' / f'{key}-alignment.json', report)
                reports.append({k: v for k, v in report.items() if k != 'lines'})
                if report['eligible']:
                    for line, row in zip(act['lines'], report['lines']):
                        line['originalT'] = row['originalT']
                        line['t'] = row['t']
                        line['timingSource'] = row['source']
                        line['timingNeedsReview'] = row['needsReview']
                    act['timingCalibration'] = {'method': 'batch-asr-text-alignment-v1', 'audioDuration': recognition['duration'],
                        'anchorRatio': report['anchorRatio'], 'reviewCount': report['reviewCount'],
                        'precision': 'machine-aligned; not manually verified', 'report': f'diagnostics/batch/{key}-alignment.json'}
                print('DONE', key, 'eligible', report['eligible'], 'anchors', report['anchorCount'], '/', report['lineCount'], 'review', report['reviewCount'], flush=True)
            except Exception as exc:
                errors.append({'key': key, 'error': str(exc)})
                print('ERROR', key, repr(exc), flush=True)
            if args.recognize_only:
                continue
            # Checkpoint after every act: interruptions lose no completed inference.
            atomic_json(ROOT / 'diagnostics' / 'batch' / 'summary.json', {'version': VERSION, 'acts': reports, 'errors': errors})
            atomic_json(ROOT / 'diagnostics' / 'episodes-calibrated.json', data)
    print('FINISHED', len(reports), 'acts;', sum(r['eligible'] for r in reports), 'eligible;', len(errors), 'errors', flush=True)
    if errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
