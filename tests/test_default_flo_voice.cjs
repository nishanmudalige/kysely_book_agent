/* Regression tests for Flo as the preferred default Finnish speech voice. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/speech.js'), 'utf8');

function makeOption() { return {value: '', textContent: ''}; }
function makeNode(id) {
  const events = {};
  const node = {
    id, value: '', textContent: '', disabled: false, hidden: false, checked: false,
    style: {}, options: [], events, classList: {contains: () => false},
    addEventListener(name, cb) { events[name] = cb; },
    setAttribute() {},
    appendChild(child) {this.options.push(child);},
    replaceChildren() {this.options = []; this.value = '';},
  };
  return node;
}
function setup(initialVoices) {
  let voices = initialVoices;
  const nodes = new Map();
  const get = id => {if (!nodes.has(id)) nodes.set(id, makeNode(id)); return nodes.get(id);};
  const speechEvents = {};
  const utterances = [];
  const speechSynthesis = {
    getVoices() { return voices; },
    addEventListener(name, handler) { speechEvents[name] = handler; },
    speak(u) { utterances.push(u); }, cancel() {}, resume() {}, pause() {},
  };
  class SpeechSynthesisUtterance { constructor(text) {this.text=text; this.voice=null;} }
  const document = {
    getElementById:get, createElement:()=>makeOption(),
    addEventListener() {},
    body:{classList:{contains:()=>false}},
  };
  const window = { speechSynthesis, SpeechSynthesisUtterance, addEventListener() {} };
  get('speech-player');
  get('speech-rate').value = '1';
  const context = {window, document, SpeechSynthesisUtterance, setTimeout, clearTimeout, Node:{TEXT_NODE:3}, Intl, console};
  vm.runInNewContext(source, context, {filename:'speech.js'});
  return {window, get, utterances,
    updateVoices(newVoices) {voices=newVoices;speechEvents.voiceschanged();},
  };
}
const english = {name:'Samantha', lang:'en-US', voiceURI:'sam-us',localService:true};
const genericFi = {name:'Suomi', lang:'fi-FI',voiceURI:'suomi-fi',localService:true};
const flo = {name:'Flo', lang:'fi-FI',voiceURI:'flo-fi',localService:true};
const defaultVoice = setup([english, genericFi, flo]);
assert.equal(defaultVoice.get('speech-voice').value, flo.voiceURI, 'Flo must be selected by default');
defaultVoice.window.KyselySpeech.readText('Miten validiteetti ja reliabiliteetti eroavat toisistaan?', 'fi');
assert.equal(defaultVoice.utterances.at(-1).voice.voiceURI, flo.voiceURI, 'Finnish spoken using Flo');
defaultVoice.window.KyselySpeech.readText('What is the difference between reliability and validity?', 'en');
assert.equal(defaultVoice.utterances.at(-1).voice.voiceURI, english.voiceURI, 'English still uses an English voice');
const delayed = setup([english]);
assert.equal(delayed.get('speech-voice').value, '', 'Fallback automatic when Flo not installed yet');
delayed.updateVoices([english, flo]);
assert.equal(delayed.get('speech-voice').value, flo.voiceURI, 'Select Flo after asynchronous voiceschanged');
delayed.get('speech-voice').value = '';
delayed.get('speech-voice').events.change();
delayed.updateVoices([english, flo]);
assert.equal(delayed.get('speech-voice').value, '', 'Do not override manual Automatic selection');
const explicit = setup([english, flo]);
explicit.get('speech-voice').value = english.voiceURI;
explicit.get('speech-voice').events.change();
explicit.updateVoices([english, flo, genericFi]);
assert.equal(explicit.get('speech-voice').value, english.voiceURI, 'Do not override a user-selected voice');
console.log('PASS: Flo default, multilingual playback, async loading and explicit overrides');
