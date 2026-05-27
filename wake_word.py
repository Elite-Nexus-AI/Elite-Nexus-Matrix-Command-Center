#!/usr/bin/env python3
# Matrix OS Wake Word Listener - uses faster-whisper on CPU
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['PULSE_RUNTIME_PATH'] = '/run/user/1000/pulse'
os.environ['OMP_NUM_THREADS'] = '4'

import pyaudio, numpy as np, time, requests, sys
from faster_whisper import WhisperModel

WAKE_WORDS = ['hermes', 'matrix', 'nexus']
BRIDGE_URL = 'http://localhost:8765'
SAMPLE_RATE = 16000
CHUNK = 1024
LISTEN_SECONDS = 2
COOLDOWN = 3

print('Loading Whisper tiny model on CPU...')
model = WhisperModel('tiny', device='cpu', compute_type='int8')
print('Wake word listener ready. Say: Hermes / Matrix / Nexus')

def transcribe_chunk(frames):
    audio = np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32) / 32768.0
    segments, _ = model.transcribe(audio, language='en', beam_size=1)
    text = ' '.join([s.text for s in segments]).strip().lower()
    return text

def notify_bridge(wake_word):
    try:
        requests.post(f'{BRIDGE_URL}/wake/trigger',
            json={'word': wake_word, 'ts': time.time()}, timeout=3)
    except: pass

def listen_loop():
    pa = pyaudio.PyAudio()
    # C922 webcam mic = device 13, confirmed working
    input_device = 13
    stream = pa.open(format=pyaudio.paInt16, channels=1,
        rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK,
        input_device_index=input_device)
    last_trigger = 0
    print('Listening...')
    while True:
        frames = [stream.read(CHUNK, exception_on_overflow=False)
                  for _ in range(int(SAMPLE_RATE / CHUNK * LISTEN_SECONDS))]
        text = transcribe_chunk(frames)
        if not text: continue
        for ww in WAKE_WORDS:
            if ww in text and time.time() - last_trigger > COOLDOWN:
                print(f'WAKE WORD: {ww} ({text})')
                notify_bridge(ww)
                last_trigger = time.time()
                break

if __name__ == '__main__':
    try:
        listen_loop()
    except KeyboardInterrupt:
        print('Stopped')
