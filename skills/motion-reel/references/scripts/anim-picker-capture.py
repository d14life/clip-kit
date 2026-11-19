#!/usr/bin/env python3
"""Damir 11-17: "use the picker's animation in the video, it was perfect". Captures the picker (index.html?cap) as transparent
1080x1920 PNG sequences for Final.tsx: out/raw/t3-lines/full/pk<line>/S_####.png + first.txt (line frame of S_0000).
  python3 docs/review/anim-picker/capture.py [lines...]      (default: all)   --frames 10,40 --out DIR = chosen frames only, --ink A|B|C = colour option
Word impact = spoken start (brief); exit start Te, Te fits before each cut. Damir 11-17 (later): no gravity fall; letters hold still from Te to the end
(Te + .41) and Final.tsx fades the whole layer (EXIT). exit.txt = 'ke cx cy': exit start in S_ frames (float) + the line's alpha-bbox centre (px)."""
import base64, os, sys, math, threading, functools, http.server, argparse
from playwright.sync_api import sync_playwright
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(H, '../../..'))
# line dir -> (picker line, anim, word impact times s, exit Te s, exit). Times = specs/p*.json anim.words (VO), Te = min(picker hold 1.5 s, cut - 0.45 s)
L = {
    '1': (1, 'F', [.05, .20, .79, 1.45, 2.11], 3.61, 'fall'),
    # v15 (REQUESTS #11): «чтобы» starts on the map cut (g352 = line t 1.233; starts 1.21 -> first visible frame 37) and lands in 0.1 s (was .22)
    # at 1.31 = on its stressed vowel (L3a.wav 10 ms envelope: «ш» noise 1.04-1.19, «то» vowel from 1.22). Others unchanged. 6th = per-word dur (None = anim's)
    '2': (2, 'F', [.05, .58, 1.31, 1.46, 1.76], 3.26, 'swept', [None, None, .10, None, None]),     # A part, out before 3b enters (L3b = L3a + 112 f)
    '2b': (9, 'F', [.07, .40, .64], 1.10, 'swept'),                 # «Чтобы вас заметили» (spec p2 anim.B, exit 145 - 112 f)
    '4': (4, 'F', [.05, .99, 1.43, 1.54], 2.85, 'swept'),
    '5': (5, 'F', [.05, .22, .38, .55, .57, .72], 1.15, 'swept'),   # lands after the odometer hits 1000 (b07 src ~51, layer at 676): «1000» 677, all in by 698, sweep 711-723
    '6': (6, 'F', [.05, .74, 1.30, 1.95], 2.35, 'swept'),
    '7': (7, 'F', [.45, .70, 1.20, 1.20], 2.18, 'fall'),           # hero, no voice (at 804): «Более» 817, «30» slam beat 825, «успешных клиентов» slam beat 840, gone by 882
    '11': (11, 'F', [.50, 1.0, 4.0], 7.6, 'fall'),                  # steps «Сайт → Google → Креативы» (at 270 = S3): 285 / 300 / 390, fall-out 498-510 (zoom out 506-514)
    # «Делаем решения и доводим до заявок» v2 (Damir 11-17 evening: big, flat, logo-style), at 884 = l9-24frame.wav t0: words on their spoken starts
    # (v2 voice l9-24frame-v2.wav, whisper-cli + 10 ms envelope: .095 .47 .71 1.016 1.97 s; line 10 = 5 words; продуктивной slam start .85 so it settles on its onset g899.5; Te 121 f = exit from g990 with at 869), held over the logo hold + WallToGrid, falls from the clinic-card frame (beat 990) = Te 106 f
    # v13: '10': (10, 'F', [.095, .47, .71, .85, 1.97], 121 / 30, 'fall'),  (l9-24frame-v2)
    # v14 (REQUESTS #9/#10, 2026-11-18): voice l9-24frame-v3C.wav «24FRAME — ваш выбор для продуктивной работы» (10 ms RMS/ZCR envelope, file s):
    # «24FRAME» .13, ваш 1.66, выбор 2.02, для 2.36 (д burst), продуктивной 2.50 (п closure), работы 3.15, voiced end 3.64. Layer at = the file's t0.
    '10': (10, 'F', [1.66, 2.02, 2.36, 2.50, 3.15], 3.65, 'fall'),
    '13': (13, 'F', [.13], .83, 'fall'),       # «24FRAME» logo + thick bar, one slam on the spoken word; held (Final.tsx clamps to the last frame)
    '10b': (12, 'F', [.14, .65, 1.48, 1.65, 2.31, 2.40], 106 / 30, 'fall'),   # option B: all grey + the logo's orange bar
}
# Damir 11-17: all lines entry F + straight + fall exit. Lines that were A/C started earlier; keep their old first frame (empty lead-in frames)
# so S_0000 / first.txt / frame count stay what Final.tsx's LAYERS n expects.
F0 = {'1': -15, '4': -8, '6': -15}
# review v4: '2' / '2b' 60 px lower (-386 / -374 before) to clear the steps line 11 at y 266-321. Final.tsx LAYERS dy, baked into the capture (view shift) so falling letters are not cut off where a shifted layer would end. Once re-captured, set dy: 0 for these in Final.tsx.
DY = {'1': -430, '2': -326, '2b': -314, '4': -330, '5': 130, '6': -381}
ap = argparse.ArgumentParser(); ap.add_argument('lines', nargs='*', default=list(L)); ap.add_argument('--frames'); ap.add_argument('--out'); ap.add_argument('--ink', choices='ABC')   # --ink: picker INK option override (colour tests)
A = ap.parse_args()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, '.html': 'text/html; charset=utf-8'}   # page has no <meta charset>
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as pw:
    HS = os.path.expanduser('~/Library/Caches/ms-playwright/chromium_headless_shell-1255/chrome-headless-shell-mac-arm64/chrome-headless-shell')   # bundled Chromium only (py playwright wants 1248, 1255 is installed)
    b = pw.chromium.launch(executable_path=HS if os.path.exists(HS) else None, args=['--use-angle=metal', '--ignore-gpu-blocklist'])
    try:
        pg = b.new_page(viewport={'width': 1200, 'height': 900})
        pg.route('**/InterTight-Bold.ttf', lambda r: r.fulfill(path=os.path.join(ROOT, 'blender/fonts/InterTight-Bold.ttf')))
        pg.goto('http://127.0.0.1:%d/docs/review/anim-picker/index.html?cap%s' % (srv.server_address[1], '&ink=' + A.ink if A.ink else '')); pg.wait_for_function('window.__ready', timeout=60000)
        for ln in A.lines:
            n, an, ts, te, ex, *du = L[ln]
            r = pg.evaluate('([n,a,t,te,ex,dy,du]) => api.cap(n,a,t,te,ex,dy,du)', [n, an, ts, te, ex, DY.get(ln, 0), du[0] if du else None])
            f0 = min(math.floor(r['first'] * 30), F0.get(ln, 1e9)); f1 = math.ceil(r['end'] * 30)   # F0 keeps the frame count Final.tsx expects (n)
            out = A.out or os.path.join(ROOT, 'out/raw/t3-lines/full/pk' + ln); os.makedirs(out, exist_ok=True)
            fr = [int(x) for x in A.frames.split(',')] if A.frames else range(f0, f1 + 1)
            for f in fr:
                d = pg.evaluate('t => api.shot(t)', f / 30)
                name = ('%s_%d.png' % (ln, f)) if A.frames else 'S_%04d.png' % (f - f0)
                open(os.path.join(out, name), 'wb').write(base64.b64decode(d.split(',', 1)[1]))
            if not A.frames:
                open(os.path.join(out, 'first.txt'), 'w').write('%d\n' % f0)
                ke = te * 30 - f0; bb = Image.open(os.path.join(out, 'S_%04d.png' % math.floor(ke))).getchannel('A').getbbox()   # rest pose at the exit start
                open(os.path.join(out, 'exit.txt'), 'w').write('%.2f %d %d\n' % (ke, (bb[0] + bb[2]) // 2, (bb[1] + bb[3]) // 2))
            print('line', ln, an, 'frames', f0, '..', f1, '=', f1 - f0 + 1, '->', out, flush=True)
    finally:
        b.close(); srv.shutdown()
