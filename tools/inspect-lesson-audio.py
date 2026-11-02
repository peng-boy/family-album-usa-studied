"""Local-only recognition for checking transcript timestamps against shipped MP3s."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.tools' / 'speech'))
os.environ['HF_HOME'] = str(ROOT / '.tools' / 'huggingface')
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
from faster_whisper import WhisperModel
import av

parser = argparse.ArgumentParser()
parser.add_argument('--model', default='base.en')
parser.add_argument('--act', type=int, default=1)
parser.add_argument('--episode', type=int, default=1)
args = parser.parse_args()
audio = ROOT / 'audio-acts' / f'e{args.episode:02d}_a{args.act}.mp3'
with av.open(str(audio)) as container:
    print('Audio duration:', container.duration / av.time_base, flush=True)
model = WhisperModel(args.model, device='cpu', compute_type='int8', download_root=str(ROOT / '.tools' / 'models'))
# Decode explicitly: PyAV 19 removed the metadata_errors argument used by faster-whisper.
import numpy as np
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
output = []
for segment in segments:
    item = {'start': round(segment.start, 3), 'end': round(segment.end, 3), 'text': segment.text,
            'words': [{'start': round(w.start, 3), 'end': round(w.end, 3), 'word': w.word, 'probability': round(w.probability, 3)} for w in segment.words or []]}
    output.append(item)
    print(f"{segment.start:.2f}-{segment.end:.2f} {segment.text}", flush=True)
dest = ROOT / 'diagnostics' / f'e{args.episode:02d}_a{args.act}-recognition.json'
dest.parent.mkdir(exist_ok=True)
dest.write_text(json.dumps({'model': args.model, 'audio': str(audio.relative_to(ROOT)), 'duration': info.duration, 'segments': output}, indent=2, ensure_ascii=False), encoding='utf-8')
print('Saved', dest, flush=True)
