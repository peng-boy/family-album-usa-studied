const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { findActiveRange, attach } = require('../audio-sync.js');

const lines = [{ t: 2 }, { t: 4 }, { t: 4 }, { t: 7 }];
test('intro, boundaries, simultaneous lines, seeking backwards and final line', () => {
  for (const [time, expected] of [[0, [-1,-1]], [2,[0,1]], [3.99,[0,1]], [4,[1,3]], [6,[1,3]], [7,[3,4]], [100,[3,4]], [2,[0,1]]]) {
    assert.deepEqual(findActiveRange(lines, time), expected);
  }
  assert.deepEqual(findActiveRange([], 10), [-1,-1]);
  assert.deepEqual(findActiveRange(lines, NaN), [-1,-1]);
});

test('all shipped timestamps are ordered and binary search matches linear reference', () => {
  const data = JSON.parse(fs.readFileSync('episodes.json', 'utf8'));
  for (const ep of data.episodes) for (const act of ep.acts) {
    act.lines.forEach((line, i) => {
      assert.ok(Number.isFinite(line.t) && line.t >= 0);
      if (i) assert.ok(line.t >= act.lines[i - 1].t);
      for (const time of [line.t - 0.001, line.t, line.t + 0.001]) {
        const eligible = act.lines.filter(l => l.t <= time);
        const timestamp = eligible.at(-1)?.t;
        const start = act.lines.findIndex(l => l.t === timestamp);
        const end = start < 0 ? -1 : start + act.lines.filter(l => l.t === timestamp).length;
        assert.deepEqual(findActiveRange(act.lines, time), [start, end]);
      }
    });
  }
});

test('lesson one calibration stays within actual audio and preserves original timestamps', () => {
  const episode = JSON.parse(fs.readFileSync('episodes.json', 'utf8')).episodes[0];
  for (const act of episode.acts) {
    assert.ok(act.timingCalibration.offsetSeconds > 10);
    for (const line of act.lines) {
      assert.ok(Number.isFinite(line.originalT));
      assert.ok(line.t >= 0 && line.t < act.timingCalibration.audioDuration);
    }
  }
  assert.equal(episode.acts[0].lines[0].t, 13.04);
  assert.equal(episode.acts[1].lines[0].t, 1.38);
});

test('episode two uses separate offsets across the first-act scene edit', () => {
  const episode = JSON.parse(fs.readFileSync('episodes.json', 'utf8')).episodes[1];
  const act = episode.acts[0];
  assert.equal(act.timingCalibration.regions.length, 2);
  assert.equal(act.timingCalibration.offsetSeconds, null);
  assert.equal(act.lines[0].t, 2.08);
  assert.equal(act.lines[21].en, 'Who is it?');
  assert.ok(Math.abs(act.lines[21].t - 124.02) < .5);
  assert.deepEqual(findActiveRange(act.lines, 125), [21,22]);
  for (const a of episode.acts) for (const line of a.lines) {
    assert.ok(Number.isFinite(line.originalT));
    assert.ok(line.t >= 0 && line.t < a.timingCalibration.audioDuration);
  }
});

test('applied batch acts preserve text, original times and safe ordered bounds', () => {
  const data = JSON.parse(fs.readFileSync('episodes.json', 'utf8'));
  const receipt = JSON.parse(fs.readFileSync('diagnostics/batch/application-receipt.json', 'utf8'));
  assert.ok(receipt.appliedActs.length > 0);
  for (const key of receipt.appliedActs) {
    const act = data.episodes[Number(key.slice(1,3)) - 1].acts[Number(key.at(-1)) - 1];
    assert.equal(act.timingCalibration.method, 'batch-asr-text-alignment-v1');
    const report = JSON.parse(fs.readFileSync(`diagnostics/batch/${key}-alignment.json`, 'utf8'));
    assert.ok(report.eligible);
    act.lines.forEach((line, i) => {
      assert.equal(line.t, report.lines[i].t);
      assert.equal(line.en, report.lines[i].en);
      assert.equal(line.originalT, report.lines[i].originalT);
      assert.ok(line.t >= 0 && line.t < report.duration);
      if (i) assert.ok(line.t >= act.lines[i-1].t);
    });
  }
});

test('media events, pause retention, ended reset and cleanup', () => {
  const frames = new Map(); let id = 0;
  global.requestAnimationFrame = callback => { frames.set(++id, callback); return id; };
  global.cancelAnimationFrame = key => frames.delete(key);
  const audio = new EventTarget();
  Object.assign(audio, { currentTime: 0, paused: true, ended: false });
  const changes = [];
  const dispose = attach(audio, lines, range => changes.push(range));
  assert.deepEqual(changes.at(-1), [-1,-1]);
  audio.currentTime = 4; audio.dispatchEvent(new Event('seeking'));
  assert.deepEqual(changes.at(-1), [1,3]);
  audio.paused = false; audio.dispatchEvent(new Event('play'));
  assert.equal(frames.size, 1);
  audio.playbackRate = 1.5;
  audio.currentTime = 7; audio.dispatchEvent(new Event('timeupdate'));
  assert.deepEqual(changes.at(-1), [3,4]);
  audio.paused = true; audio.dispatchEvent(new Event('pause'));
  assert.equal(frames.size, 0);
  assert.deepEqual(changes.at(-1), [3,4]);
  audio.ended = true; audio.dispatchEvent(new Event('ended'));
  assert.deepEqual(changes.at(-1), [-1,-1]);
  dispose(); const count = changes.length;
  audio.ended = false; audio.currentTime = 2; audio.dispatchEvent(new Event('seeked'));
  assert.equal(changes.length, count);
  delete global.requestAnimationFrame; delete global.cancelAnimationFrame;
});

test('follow resumes on play and when re-enabled within the same sentence', () => {
  const html = fs.readFileSync('index.html', 'utf8');
  const app = Array.from(html.matchAll(/<script>([\s\S]*?)<\/script>/g)).at(-1)[1].replace(/init\(\);\s*$/, '');
  let scrolls = 0;
  const line = { classList: { toggle() {} }, setAttribute() {}, removeAttribute() {},
    getBoundingClientRect: () => ({ top: 1200, bottom: 1250 }), scrollIntoView() { scrolls++; } };
  const audio = new EventTarget(); Object.assign(audio, { currentTime: 2, paused: true, ended: false });
  const context = { AudioLineSync: { attach }, window: { innerHeight: 800, matchMedia: () => ({ matches: true }), addEventListener() {} },
    document: { addEventListener() {}, querySelectorAll: () => [line], querySelector: () => line,
      getElementById: id => id === 'detail-wrap' ? { style: { display: '' } } : { classList: { contains: () => false } } } };
  vm.createContext(context); vm.runInContext(app, context);
  context.bindAudioSync(audio, { lines }, 0);
  assert.equal(scrolls, 0);
  audio.paused = false;
  // Stub frame scheduling: the assertion concerns the application's play listener.
  global.requestAnimationFrame = () => 1; global.cancelAnimationFrame = () => {};
  audio.dispatchEvent(new Event('play'));
  assert.equal(scrolls, 1);
  const btn = { classList: { toggle() {} }, setAttribute() {} };
  context.toggleFollowAudio(btn); context.toggleFollowAudio(btn);
  assert.equal(scrolls, 2);
  vm.runInContext('disposeAudioSync()', context);
  delete global.requestAnimationFrame; delete global.cancelAnimationFrame;
});

test('all inline application scripts compile', () => {
  const html = fs.readFileSync('index.html', 'utf8');
  for (const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) new vm.Script(match[1]);
});
