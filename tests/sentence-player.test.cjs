const { test } = require('node:test');
const assert = require('node:assert/strict');
const { sentenceBounds, createSentencePlayer } = require('../audio-sync.js');
const lines = [{t:2},{t:4},{t:4},{t:7}];

function fixture() {
  const frames = new Map(); let id=0;
  global.requestAnimationFrame = fn => { frames.set(++id,fn); return id; };
  global.cancelAnimationFrame = n => frames.delete(n);
  const audio = new EventTarget();
  Object.assign(audio,{currentTime:2,duration:10,paused:true,ended:false,playbackRate:.5});
  audio.pause = () => { audio.paused=true; audio.dispatchEvent(new Event('pause')); };
  audio.play = () => { audio.paused=false; audio.ended=false; audio.dispatchEvent(new Event('play')); return Promise.resolve(); };
  const player = createSentencePlayer(audio,lines);
  return {audio,player,frames,cleanup(){player.dispose();delete global.requestAnimationFrame;delete global.cancelAnimationFrame;}};
}

test('sentence range skips duplicate timestamps and bounds final sentence by duration',()=>{
  assert.deepEqual(sentenceBounds(lines,1,10),{start:4,end:7});
  assert.deepEqual(sentenceBounds(lines,3,10),{start:7,end:10});
  assert.equal(sentenceBounds(lines,3,6),null);
});

test('once pauses at boundary and resets for replay at half speed',()=>{
  const f=fixture(); f.player.setMode('once'); f.audio.play();
  f.audio.currentTime=4; f.audio.dispatchEvent(new Event('timeupdate'));
  assert.equal(f.audio.paused,true); assert.equal(f.audio.currentTime,2);
  assert.equal(f.audio.playbackRate,.5); assert.equal(f.frames.size,0);
  f.cleanup();
});

test('loop restarts selected sentence without stopping',()=>{
  const f=fixture(); f.player.setMode('loop'); f.player.select(1); f.audio.currentTime=4; f.audio.play();
  f.audio.currentTime=7; f.audio.dispatchEvent(new Event('timeupdate'));
  assert.equal(f.audio.currentTime,4); assert.equal(f.audio.paused,false);
  f.cleanup(); assert.equal(f.frames.size,0);
});

test('continuous mode does not stop and seeking selects another loop sentence',()=>{
  const f=fixture(); f.audio.play(); f.audio.currentTime=7; f.audio.dispatchEvent(new Event('timeupdate'));
  assert.equal(f.audio.currentTime,7);
  f.player.setMode('loop'); f.audio.currentTime=4.5; f.audio.dispatchEvent(new Event('seeking'));
  f.audio.currentTime=7; f.audio.dispatchEvent(new Event('timeupdate'));
  assert.equal(f.audio.currentTime,4); f.cleanup();
});

test('A-B validates points, loops arbitrary sub-sentence range and clears safely',()=>{
  const f=fixture();
  assert.equal(f.player.setAB(4,3),false);
  assert.equal(f.player.setAB(-1,3),false);
  assert.equal(f.player.setAB(3,3.1),false);
  assert.equal(f.player.setAB(3,11),false);
  assert.equal(f.player.setAB(3.25,5.75),true);
  f.player.setMode('ab'); assert.equal(f.audio.currentTime,3.25);
  f.audio.play(); f.audio.currentTime=5.75; f.audio.dispatchEvent(new Event('timeupdate'));
  assert.equal(f.audio.currentTime,3.25); assert.equal(f.audio.paused,false);
  f.audio.currentTime=1;f.audio.dispatchEvent(new Event('timeupdate'));
  assert.equal(f.audio.currentTime,3.25);
  f.audio.pause();f.audio.currentTime=6;f.audio.dispatchEvent(new Event('timeupdate'));
  assert.equal(f.audio.currentTime,6,'paused seeking is not forced back');
  f.player.clearAB();f.audio.play();f.audio.currentTime=8;f.audio.dispatchEvent(new Event('timeupdate'));
  assert.equal(f.audio.currentTime,8);f.cleanup();
});

test('A-B ending at audio duration restarts after ended',()=>{
  const f=fixture();f.player.setAB(8,10);f.player.setMode('ab');f.audio.play();
  f.audio.ended=true;f.audio.paused=true;f.audio.dispatchEvent(new Event('ended'));
  assert.equal(f.audio.currentTime,8);assert.equal(f.audio.paused,false);f.cleanup();
});

test('last sentence loops on ended and once stays paused',()=>{
  const f=fixture(); f.audio.currentTime=7; f.player.setMode('loop'); f.audio.play();
  f.audio.currentTime=10; f.audio.paused=true; f.audio.ended=true; f.audio.dispatchEvent(new Event('ended'));
  assert.equal(f.audio.currentTime,7); assert.equal(f.audio.paused,false);
  f.player.setMode('once'); f.audio.currentTime=10; f.audio.paused=true; f.audio.ended=true; f.audio.dispatchEvent(new Event('ended'));
  assert.equal(f.audio.currentTime,7); assert.equal(f.audio.paused,true); f.cleanup();
});
