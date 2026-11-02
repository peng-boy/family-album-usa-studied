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

  const api = { findActiveRange, attach };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.AudioLineSync = api;
})(typeof window !== 'undefined' ? window : globalThis);
