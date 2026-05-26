#!/usr/bin/env python3
# Matrix OS Semantic Screen Awareness
# Captures active window every 30s, OCRs text, posts to bridge
import subprocess, time, requests, os, json, tempfile
from pathlib import Path

BRIDGE_URL = 'http://localhost:8765'
INTERVAL = 30
DISPLAY = os.environ.get('DISPLAY', ':1')
last_text = ''

def capture_screen():
    tmp = tempfile.mktemp(suffix='.png')
    try:
        subprocess.run(['scrot', '-u', tmp],
            env={**os.environ,'DISPLAY':DISPLAY},
            timeout=5, capture_output=True)
        if Path(tmp).exists() and Path(tmp).stat().st_size > 1000:
            return tmp
    except Exception as e:
        print(f'Screen capture error: {e}')
    return None

def ocr_image(img_path):
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        results = reader.readtext(img_path, detail=0, paragraph=True)
        text = ' '.join(results).strip()
        return text[:2000]
    except Exception as e:
        print(f'OCR error: {e}')
        return ''

def post_context(text, window_title=''):
    try:
        requests.post(f'{BRIDGE_URL}/screen/context',
            json={'text': text, 'window': window_title, 'ts': time.time()},
            timeout=5)
    except: pass

def get_active_window():
    try:
        r = subprocess.run(['xdotool','getactivewindow','getwindowname'],
            capture_output=True, text=True, timeout=3,
            env={**os.environ,'DISPLAY':DISPLAY})
        return r.stdout.strip()[:100]
    except: return 'unknown'

def run():
    global last_text
    print(f'Screen OCR daemon started. Interval: {INTERVAL}s')
    while True:
        try:
            window = get_active_window()
            img = capture_screen()
            if img:
                text = ocr_image(img)
                Path(img).unlink(missing_ok=True)
                if text and text != last_text:
                    print(f'OCR: {len(text)} chars from [{window}]')
                    post_context(text, window)
                    last_text = text
        except Exception as e:
            print(f'OCR loop error: {e}')
        time.sleep(INTERVAL)

if __name__ == '__main__':
    run()