import re

with open("index.html", "r") as f:
    html = f.read()

# Replace the tryBrowserSTT function with one that calls /stt on the bridge
old = """// Browser SpeechRecognition (fallback STT)
function tryBrowserSTT() {
  return new Promise(resolve => {
    const SR = window.SpeechRecognition||window.webkitSpeechRecognition;
    if (!SR) { resolve(''); return; }
    const r = new SR();
    r.lang='en-US'; r.interimResults=false; r.maxAlternatives=1;
    r.onresult = e => resolve(e.results[0]?.[0]?.transcript||'');
    r.onerror  = () => resolve('');
    r.onend    = () => {};
    r.start();
    // Short timeout
    setTimeout(()=>r.abort(), 8000);
  });
}"""

new = """// Whisper STT via bridge
async function tryBrowserSTT() {
  // collect chunks from mediaRec — but since we already have the blob
  // we use a global lastBlob set in stopRecording
  if (!window._lastAudioBlob || window._lastAudioBlob.size < 500) return '';
  try {
    const buf = await window._lastAudioBlob.arrayBuffer();
    const u8 = new Uint8Array(buf);
    let bin = '';
    for (let i = 0; i < u8.length; i++) bin += String.fromCharCode(u8[i]);
    const b64 = btoa(bin);
    const res = await fetch(CFG.url + '/stt', {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ base64audio: b64, mimetype: 'audio/webm' })
    });
    if (!res.ok) throw new Error('stt failed');
    const data = await res.json();
    return data.text || '';
  } catch(e) {
    console.warn('Whisper STT failed:', e);
    // fallback to browser SR
    return new Promise(resolve => {
      const SR = window.SpeechRecognition||window.webkitSpeechRecognition;
      if (!SR) { resolve(''); return; }
      const r = new SR();
      r.lang='en-US'; r.interimResults=false; r.maxAlternatives=1;
      r.onresult = e => resolve(e.results[0]?.[0]?.transcript||'');
      r.onerror = () => resolve('');
      r.start();
      setTimeout(()=>{ try{r.abort()}catch{} }, 8000);
    });
  }
}"""

html = html.replace(old, new)

# Also save the blob when recording stops
old2 = """      mr.onstop = async () => {
      stream.getTracks().forEach(t=>t.stop());
      broadcastAudio('none');
      setRecording(false);
      const blob = new Blob(chunks, { type:'audio/webm' });
      if (blob.size<1000) return;
      // Try browser SpeechRecognition as fallback (no server upload)
      const text = await tryBrowserSTT();"""

new2 = """      mr.onstop = async () => {
      stream.getTracks().forEach(t=>t.stop());
      broadcastAudio('none');
      setRecording(false);
      const blob = new Blob(chunks, { type:'audio/webm' });
      window._lastAudioBlob = blob;
      if (blob.size<1000) return;
      updateChatStatus('TRANSCRIBING');
      const text = await tryBrowserSTT();"""

html = html.replace(old2, new2)

# Fix browser TTS — use window.speechSynthesis
old3 = """function toggleMute() {
  muted = !muted;
  localStorage.setItem(MUTE_KEY, muted?'1':'0');"""

new3 = """function speakText(text) {
  if (muted) return;
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.rate = 1.0;
  utt.pitch = 1.0;
  utt.volume = 1.0;
  // Try to pick a good voice
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => v.lang.startsWith('en') && v.name.toLowerCase().includes('female'))
    || voices.find(v => v.lang.startsWith('en-GB'))
    || voices.find(v => v.lang.startsWith('en'))
    || voices[0];
  if (preferred) utt.voice = preferred;
  utt.onstart = () => setMatrixActive(true);
  utt.onend   = () => setMatrixActive(false);
  window.speechSynthesis.speak(utt);
}

function toggleMute() {
  muted = !muted;
  if (muted) window.speechSynthesis?.cancel();
  localStorage.setItem(MUTE_KEY, muted?'1':'0');"""

html = html.replace(old3, new3)

# Hook speakText into the AI reply — after streaming finishes speak the full reply
old4 = """    messages[aiIdx].streaming = false;
    streamCtrl = null;
    setStreaming(false);
    setMatrixActive(false);
    updateChatStatus('READY');
    renderMsgs();"""

new4 = """    messages[aiIdx].streaming = false;
    streamCtrl = null;
    setStreaming(false);
    updateChatStatus('READY');
    renderMsgs();
    // Speak the reply
    const reply = messages[aiIdx].content;
    if (reply && reply.length > 0 && !muted) {
      speakText(reply);
    } else {
      setMatrixActive(false);
    }"""

html = html.replace(old4, new4)

with open("index.html", "w") as f:
    f.write(html)

print("Done! index.html patched successfully.")
