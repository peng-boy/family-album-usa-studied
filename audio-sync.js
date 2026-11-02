/* Audio-clock based transcript synchronization; no timers tied to playback speed. */
(function (root) {
  'use strict';

  // Equal timestamps represent simultaneous lines; keep the entire group active.
  function findActiveRange(lines, time) {
    if (!Number.isFinite(time) || !lines.length || time < lines[0].t) return [-1, -1];
    let low = 0;
    let high = lines.length;
    while (low < high) {
      const mid = (low + high) >>> 1;
      if (lines[mid].t <= time) low = mid + 1;
      else high = mid;
    }
    const end = low;
    const timestamp = lines[end - 1].t;
    high = end - 1;
    low = 0;
    while (low < high) {
      const mid = (low + high) >>> 1;
      if (lines[mid].t < timestamp) low = mid + 1;
      else high = mid;
    }
    return [low, end];
  }

  function attach(audio, lines, onChange) {
    let frame = null;
    let previous = '';
    let disposed = false;
    function update() {
      const range = audio.ended ? [-1, -1] : findActiveRange(lines, audio.currentTime);
      const key = range.join(':');
      if (key !== previous) {
        previous = key;
        onChange(range);
      }
    }
    function stop() {
      if (frame !== null) root.cancelAnimationFrame(frame);
      frame = null;
    }
    function tick() {
      frame = null;
      if (disposed) return;
      update();
      if (!audio.paused && !audio.ended) frame = root.requestAnimationFrame(tick);
    }
    function play() {
      stop();
      tick();
    }
    function pause() {
      stop();
      update();
    }
    const events = {
      timeupdate: update, seeking: update, seeked: update,
      loadedmetadata: update, play, pause, ended: pause, error: pause
    };
    Object.entries(events).forEach(([name, handler]) => audio.addEventListener(name, handler));
    update();
    return function dispose() {
      disposed = true;
      stop();
      Object.entries(events).forEach(([name, handler]) => audio.removeEventListener(name, handler));
    };
  }

  function sentenceBounds(lines, index, duration) {
    if (!lines[index] || !Number.isFinite(lines[index].t)) return null;
    const start = lines[index].t;
    const next = lines.find((line, i) => i > index && line.t > start);
    const end = Math.min(next ? next.t : Infinity, Number.isFinite(duration) ? duration : Infinity);
    return end > start ? { start, end } : null;
  }

  function createSentencePlayer(audio, lines) {
    let mode = 'continuous';
    let selected = -1;
    let ab = null;
    function boundsForMode() {
      return mode === 'ab' ? ab : sentenceBounds(lines, selected, audio.duration);
    }
    let frame = null;
    let disposed = false;
    function selectAtTime() {
      selected = findActiveRange(lines, audio.currentTime)[0];
      if (selected < 0 && lines.length) selected = 0;
    }
    function stopFrame() {
      if (frame !== null) root.cancelAnimationFrame(frame);
      frame = null;
    }
    function enforce() {
      if (mode === 'continuous' || (mode !== 'ab' && selected < 0) || audio.paused) return;
      const bounds = boundsForMode();
      if (!bounds) return;
      if (audio.currentTime >= bounds.end - 0.01 || audio.ended || (mode === 'ab' && audio.currentTime < bounds.start)) {
        if (mode === 'once') audio.pause();
        audio.currentTime = bounds.start;
        if ((mode === 'loop' || mode === 'ab') && audio.paused) audio.play().catch(() => {});
      }
    }
    function tick() {
      frame = null;
      if (disposed) return;
      enforce();
      if (!audio.paused && !audio.ended) frame = root.requestAnimationFrame(tick);
    }
    function onPlay() {
      stopFrame();
      if (mode !== 'continuous' && selected < 0) selectAtTime();
      tick();
    }
    function onSeek() {
      if (mode === 'continuous' || mode === 'ab') return;
      const bounds = sentenceBounds(lines, selected, audio.duration);
      if (!bounds || audio.currentTime < bounds.start || audio.currentTime >= bounds.end) selectAtTime();
    }
    function onEnded() {
      stopFrame();
      if (mode === 'continuous' || (mode !== 'ab' && selected < 0)) return;
      const bounds = boundsForMode();
      if (!bounds) return;
      audio.currentTime = bounds.start;
      if (mode === 'loop' || mode === 'ab') audio.play().catch(() => {});
    }
    const events = { play: onPlay, pause: stopFrame, seeking: onSeek, timeupdate: enforce, ended: onEnded };
    Object.entries(events).forEach(([name, fn]) => audio.addEventListener(name, fn));
    return {
      setMode(value) {
        if (!['continuous', 'once', 'loop', 'ab'].includes(value)) return;
        mode = value;
        if (mode !== 'continuous') {
          selectAtTime();
          const bounds = boundsForMode();
          if (bounds && (audio.currentTime < bounds.start || (mode === 'ab' && audio.currentTime >= bounds.end))) audio.currentTime = bounds.start;
        }
      },
      setAB(start, end) {
        if (!Number.isFinite(start) || !Number.isFinite(end) || start < 0 || end - start < 0.2 ||
            (Number.isFinite(audio.duration) && end > audio.duration)) return false;
        ab = { start, end };
        return true;
      },
      clearAB() { ab = null; if (mode === 'ab') mode = 'continuous'; },
      select(index) { selected = index; },
      dispose() {
        disposed = true;
        stopFrame();
        Object.entries(events).forEach(([name, fn]) => audio.removeEventListener(name, fn));
      }
    };
  }

  const api = { findActiveRange, attach, sentenceBounds, createSentencePlayer };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.AudioLineSync = api;
})(typeof window !== 'undefined' ? window : globalThis);
