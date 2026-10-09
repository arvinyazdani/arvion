const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('core/static/core/js/welcome-sound.js', 'utf8');
function run({prefs={},played=false,suspended=false,lang='fa'}={}) {
  const local = new Map(Object.entries(prefs)), session = new Map(played ? [['rvion-welcome-sound-played-v2','yes']] : []);
  const events = new Map(), timers=[], tones=[]; let contexts=0, resumes=0;
  const button = {dataset:{soundToggle:'notification'}, attrs:{}, textContent:'', setAttribute(k,v){this.attrs[k]=v;}, querySelector(){return null;}, addEventListener(k,fn){this[k]=fn;}};
  class AudioContext {
    constructor(){contexts++;this.state=suspended?'suspended':'running';this.currentTime=10;this.destination={};}
    async resume(){resumes++;this.state='running';}
    createOscillator(){const tone={};tones.push(tone);return {frequency:{setValueAtTime(v,t){tone.frequency=v;tone.start=t;}},connect(){return {connect(){}};},start(){},stop(t){tone.stop=t;}};}
    createGain(){return {gain:{setValueAtTime(){},exponentialRampToValueAtTime(v,t){if(v>0.0001){tones.at(-1).gain=v;tones.at(-1).ramp=t;}}}};}
  }
  const storage=m=>({getItem:k=>m.get(k)??null,setItem:(k,v)=>m.set(k,v)});
  const window={AudioContext,setTimeout:fn=>timers.push(fn),addEventListener:(k,fn)=>events.set(k,fn),removeEventListener:(k)=>events.delete(k)};
  const document={readyState:'complete',documentElement:{lang},querySelectorAll:()=>[button]};
  vm.runInNewContext(source,{window,document,localStorage:storage(local),sessionStorage:storage(session)});
  return {window,local,session,button,tones,timers,interact:(type='pointerdown')=>events.get(type)?.(),stats:()=>({contexts,resumes})};
}
async function checks(){
  let r=run();assert.equal(r.stats().contexts,0);
  assert.equal(await r.window.RvionSounds.playWelcome(),false);
  assert.equal(await r.window.RvionSounds.playNotification('high'),false);
  assert.equal(r.stats().contexts,0); // Even background notifications cannot initialize audio.
  r.interact();assert.equal(r.stats().contexts,1);
  assert.deepEqual(r.tones.map(t=>t.frequency),[523.25,659.25]);
  assert.deepEqual(r.tones.map(t=>t.gain),[0.032,0.025]);
  assert.equal(r.session.get('rvion-welcome-sound-played-v2'),'yes');
  r.interact('keydown');assert.equal(await r.window.RvionSounds.playWelcome(),false);
  assert.equal(r.tones.length,2);assert.equal(r.stats().contexts,1);
  await r.window.RvionSounds.playNotification();assert.equal(r.tones.at(-1).frequency,660);
  await r.window.RvionSounds.playNotification('critical');assert.deepEqual(r.tones.slice(-2).map(t=>t.frequency),[740,880]);
  r.button.click();assert.equal(r.local.get('rvion-sound-notification'),'off');assert.equal(r.button.attrs['aria-pressed'],'false');
  assert.equal(r.button.attrs['aria-label'],'روشن‌کردن صدا');
  const count=r.tones.length;assert.equal(await r.window.RvionSounds.playNotification(),false);assert.equal(r.tones.length,count);
  r.button.click();assert.equal(r.local.get('rvion-sound-notification'),'on');assert.equal(r.tones.at(-1).frequency,660);
  r=run({lang:'en'});r.timers[0]();r.interact('keydown');assert.equal(r.stats().contexts,0);assert.equal(r.tones.length,0);
  await r.window.RvionSounds.playNotification('high');assert.equal(r.stats().contexts,1);assert.deepEqual(r.tones.map(t=>t.frequency),[740,880]);
  assert.equal(r.button.attrs['aria-label'],'Turn sound off');
  r=run({prefs:{'rvion-sound-welcome':'off','rvion-sound-notification':'off'}});r.interact('click');assert.equal(r.stats().contexts,0);
  r.button.click();assert.equal(r.stats().contexts,1);assert.equal(r.tones.at(-1).frequency,660);assert.equal(r.local.get('rvion-sound-welcome'),'off');
  r=run({played:true});r.interact();assert.equal(r.stats().contexts,0);assert.equal(r.tones.length,0);
  r=run({suspended:true});r.interact();await new Promise(setImmediate);assert.equal(r.stats().resumes,1);assert.equal(r.tones.length,2);
  console.log('Sounds: no load-time AudioContext; first interaction, welcome window/session/mute, toggle localization and notification waveforms passed.');
}
checks().catch(error=>{console.error(error);process.exitCode=1;});
