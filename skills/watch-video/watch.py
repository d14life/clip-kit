#!/usr/bin/env python3
"""Turn any video URL into things Claude can actually read: a transcript plus
de-duplicated frames.

    watch.py <url> [--out DIR] [--fps 1] [--mode auto|captions|whisper]
                   [--max-frames 40] [--cookies FILE]

Prints a short report ending with the paths Claude should open.

Strategy:
  captions -> free + instant, right for long talks (YouTube auto-subs)
  whisper  -> local transcription, right for anything without captions (Reels,
              TikTok, short clips)
  auto     -> try captions, fall back to whisper
Long videos default to captions because downloading and transcribing an hour of
lecture costs a lot and buys nothing the words don't already carry.
"""
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path

WHISPER_PY = Path(__import__('os').environ.get('WHISPER_PY', 'YOUR_WHISPER_PYTHON_PATH'))
VIDEO_EXTS = ('.mp4', '.mkv', '.webm', '.mov')
# Past this, try captions first: anything longer is almost always a talk or
# tutorial that already ships captions, and whisper would burn minutes of CPU
# reproducing them. Short clips (reels/shorts) usually have no captions and need
# exact wording, so they go straight to whisper. Captions always fall back.
LONG_SECONDS = 5 * 60


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def need(tool):
    if not shutil.which(tool):
        sys.exit(f'ERROR: {tool} not installed. Install with: brew install {tool}')


def auth(cookies, browser):
    """yt-dlp auth flags. --browser pulls a live session straight from the
    installed browser, which is what gets past YouTube's bot-check."""
    if browser:
        return ['--cookies-from-browser', browser]
    if cookies:
        return ['--cookies', cookies]
    return []


def probe(url, cookies, browser):
    """Title + duration without downloading anything."""
    cmd = ['yt-dlp', '--no-warnings', '--skip-download', '--socket-timeout', '30',
           '--print', '%(title)s|%(duration)s|%(id)s'] + auth(cookies, browser)
    r = run(cmd + [url], timeout=120)
    line = (r.stdout or '').strip().splitlines()
    if not line or '|' not in line[0]:
        err = (r.stderr or '').strip().splitlines()
        blob = '\n'.join(err[-3:]) if err else 'no output'
        hint = ('\n\nFIX: YouTube is bot-checking this one. Retry with '
                '--browser chrome (or safari/firefox).'
                if 'not a bot' in blob or 'Sign in to confirm' in blob
                else '\n\nFIX: if this is private/Instagram, pass '
                     '--cookies cookies.txt (or --browser chrome).')
        sys.exit('ERROR: could not read video metadata.\n' + blob + hint)
    # titles routinely contain '|' ("Topic | Channel"), so parse from the right:
    # duration and id are always the last two fields
    parts = line[0].rsplit('|', 2)
    if len(parts) < 3:
        return line[0].strip(), 0, ''
    title, dur, vid = parts
    try:
        dur = int(float(dur))
    except ValueError:
        dur = 0
    return title.strip(), dur, vid.strip()


def vtt_to_text(p: Path) -> str:
    """Strip WebVTT timing/markup and collapse the duplicate rolling lines
    YouTube emits for auto-captions."""
    out, seen_tail = [], ''
    for raw in p.read_text(encoding='utf-8', errors='ignore').splitlines():
        s = raw.strip()
        if (not s or s == 'WEBVTT' or '-->' in s or s.isdigit()
                or s.startswith(('Kind:', 'Language:', 'NOTE'))):
            continue
        s = re.sub(r'<[^>]+>', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        if not s or s == seen_tail:
            continue
        # auto-captions repeat the previous line as a prefix of the next
        if seen_tail and s.startswith(seen_tail):
            s = s[len(seen_tail):].strip()
        if s:
            out.append(s)
            seen_tail = out[-1]
    return ' '.join(out)


def get_captions(url, out: Path, cookies, browser):
    cmd = ['yt-dlp', '--no-warnings', '--skip-download',
           '--write-auto-subs', '--write-subs', '--sub-langs', 'en.*,en',
           '--sub-format', 'vtt', '--socket-timeout', '30',
           '-o', str(out / 'sub.%(ext)s')] + auth(cookies, browser)
    run(cmd + [url], timeout=300)
    vtts = sorted(out.glob('sub*.vtt'))
    if not vtts:
        return None
    text = vtt_to_text(vtts[0])
    return text or None


def download(url, out: Path, cookies, browser):
    cmd = ['yt-dlp', '--no-warnings', '--socket-timeout', '30',
           '-f', 'best[ext=mp4]/best',
           '-o', str(out / 'video.%(ext)s')] + auth(cookies, browser)
    r = run(cmd + [url], timeout=1800)
    vids = [v for v in out.glob('video.*') if v.suffix in VIDEO_EXTS]
    if not vids:
        err = (r.stderr or '').strip().splitlines()
        sys.exit('ERROR: download failed.\n' + '\n'.join(err[-3:]))
    return vids[0]


def transcribe(video: Path, out: Path):
    if not WHISPER_PY.exists():
        sys.exit(f'ERROR: whisper env missing at {WHISPER_PY}\n'
                 'Create it: python3 -m venv .venv-whisper && '
                 '.venv-whisper/bin/pip install faster-whisper')
    code = (
        'import sys\n'
        'from faster_whisper import WhisperModel\n'
        'm = WhisperModel("base", device="cpu", compute_type="int8")\n'
        'segs, info = m.transcribe(sys.argv[1], language=None, vad_filter=True)\n'
        'print(info.language)\n'
        'print(" ".join(s.text.strip() for s in segs).strip())\n')
    r = run([str(WHISPER_PY), '-c', code, str(video)], timeout=7200)
    parts = (r.stdout or '').split('\n', 1)
    if len(parts) < 2:
        return '', '?'
    return parts[1].strip(), parts[0].strip()


def frames(video: Path, out: Path, fps, max_frames):
    fdir = out / 'frames'
    fdir.mkdir(exist_ok=True)
    # mpdecimate drops near-duplicate frames, so a talking head doesn't
    # produce 600 identical jpgs
    run(['ffmpeg', '-loglevel', 'error', '-i', str(video),
         '-vf', f'fps={fps},mpdecimate=hi=64*12:lo=64*5:frac=0.33',
         '-vsync', 'vfr', str(fdir / 'f%04d.jpg')], timeout=3600)
    got = sorted(fdir.glob('*.jpg'))
    if len(got) > max_frames:                      # keep an even spread
        keep = {got[round(i * (len(got) - 1) / (max_frames - 1))]
                for i in range(max_frames)}
        for f in got:
            if f not in keep:
                f.unlink()
        got = sorted(fdir.glob('*.jpg'))
    return fdir, len(got)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('url')
    ap.add_argument('--out', default=None)
    ap.add_argument('--fps', type=float, default=1)
    ap.add_argument('--mode', choices=['auto', 'captions', 'whisper'], default='auto')
    ap.add_argument('--max-frames', type=int, default=40)
    ap.add_argument('--cookies', default=None)
    ap.add_argument('--browser', default=None,
                    help='pull cookies from an installed browser '
                         '(chrome/safari/firefox/edge/brave) - fixes YouTube bot-checks')
    ap.add_argument('--no-frames', action='store_true')
    a = ap.parse_args()

    need('yt-dlp')
    need('ffmpeg')

    title, dur, vid = probe(a.url, a.cookies, a.browser)
    out = Path(a.out) if a.out else Path.cwd() / 'watched' / (vid or 'video')
    out.mkdir(parents=True, exist_ok=True)

    mins = f'{dur // 60}m{dur % 60:02d}s' if dur else 'unknown length'
    print(f'TITLE   : {title}\nDURATION: {mins}\nOUT     : {out}\n')

    mode = a.mode
    if mode == 'auto':
        mode = 'captions' if dur and dur > LONG_SECONDS else 'whisper'
        print(f'mode    : auto -> {mode}'
              f'{" (long video: captions are far cheaper)" if mode == "captions" else ""}')

    text, lang, src = '', '', ''
    if mode == 'captions':
        text = get_captions(a.url, out, a.cookies, a.browser)
        src = 'captions'
        if not text:
            print('no captions found -> falling back to whisper')
            mode, src = 'whisper', 'whisper'

    video = None
    if mode == 'whisper' or not a.no_frames:
        video = download(a.url, out, a.cookies, a.browser)

    if mode == 'whisper':
        print('transcribing locally (no API cost)...')
        text, lang = transcribe(video, out)
        src = 'whisper'

    tpath = out / 'transcript.txt'
    tpath.write_text(text or '(no speech detected)', encoding='utf-8')

    fdir, nframes = (None, 0)
    if not a.no_frames and video:
        fdir, nframes = frames(video, out, a.fps, a.max_frames)

    json.dump({'title': title, 'duration_s': dur, 'url': a.url, 'id': vid,
               'transcript_source': src, 'language': lang,
               'transcript_chars': len(text or ''), 'frames': nframes},
              open(out / 'meta.json', 'w'), indent=1)

    print(f'\n--- READY ---')
    print(f'transcript ({src}, {len(text or "")} chars): {tpath}')
    if nframes:
        print(f'frames ({nframes}): {fdir}/f0001.jpg ...')
    print('\nNEXT: Read the transcript, then Read frames evenly spaced across '
          'the folder (and any frame showing text, charts, code, or UI).')


if __name__ == '__main__':
    main()
