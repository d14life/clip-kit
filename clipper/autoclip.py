#!/usr/bin/env python3
"""
autoclip - fully automatic Twitch live clipper.

  1. waits for a channel to go live, then records it from the first second (streamlink)
  2. reads its chat anonymously - no account, no token (Twitch IRC as justinfan)
  3. scores chat every 10 s and marks the spikes against a rolling baseline
  4. cuts the moment around each spike (ffmpeg)
  5. writes captions (faster-whisper) and renders a 9:16 short + a 16:9 version

Run `python autoclip.py --help` for every option. Typical use:

  python autoclip.py kaicenat theburntpeanut
  python autoclip.py --game "Grand Theft Auto VI" --top 3 --lang en
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import math
import os
import queue
import re
import shutil
import socket
import ssl
import statistics
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:          # memes.py sits next to this file (also when run with python -P)
    sys.path.append(str(HERE))
import memes  # noqa: E402

# --------------------------------------------------------------------------- logging

_print_lock = threading.Lock()
_log_file = None


def log(tag: str, msg: str) -> None:
    line = f"{dt.datetime.now():%H:%M:%S} [{tag}] {msg}"
    with _print_lock:
        print(line, flush=True)
        if _log_file:
            _log_file.write(line + "\n")
            _log_file.flush()


# --------------------------------------------------------------------------- config


@dataclass
class Config:
    channels: list
    game: str | None
    top: int
    lang: str | None
    rescan: int
    out: Path
    work: Path
    quality: str
    poll: int
    bucket: int
    baseline_buckets: int
    warmup_buckets: int
    sensitivity: float
    min_score: float
    pre: float
    post: float
    cooldown: float
    segment: int
    buffer_minutes: float
    formats: list
    captions: bool
    whisper_model: str
    language: str | None
    encoder: str
    zoom: float
    layout: str
    only_game: str | None
    hook: bool
    tags: list
    channel_tags: dict
    censor: bool
    jumpcuts: bool
    teaser: bool
    fx: bool
    credit: bool
    max_clips_per_hour: int


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="autoclip",
        description="Fully automatic Twitch live clipper: record live, detect chat spikes, cut, caption, render shorts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("channels", nargs="*", help="Twitch channel names to watch (waits for them to go live); "
                   "add campaign hashtags per channel with a colon: lacy:LACY clix:Clix")
    p.add_argument("--game", help='auto mode: watch the top live streams in this game, e.g. "Grand Theft Auto VI"')
    p.add_argument("--top", type=int, default=2, help="auto mode: how many streams to watch at once")
    p.add_argument("--lang", help="auto mode: only streams in this language code, e.g. en, es, fr")
    p.add_argument("--rescan", type=int, default=300, help="auto mode: seconds between top-stream checks")
    p.add_argument("--out", type=Path, default=HERE / "clips", help="where finished clips go")
    p.add_argument("--work", type=Path, default=HERE / "work", help="recording buffer and chat logs")
    p.add_argument("--quality", default="1080p60,1080p,720p60,720p,best", help="streamlink quality list")
    p.add_argument("--poll", type=int, default=30, help="seconds between live checks for an offline channel")
    p.add_argument("--bucket", type=int, default=10, help="chat counting window in seconds")
    p.add_argument("--baseline-buckets", type=int, default=30, help="how many past windows make the baseline (30 x 10 s = 5 min)")
    p.add_argument("--warmup-buckets", type=int, default=6, help="windows of history needed before clipping starts")
    p.add_argument("--sensitivity", type=float, default=2.0,
                   help="a window is a spike when its chat score is this many times the baseline median (lower = more clips)")
    p.add_argument("--min-score", type=float, default=8.0, help="absolute floor: a spike window needs at least this chat score")
    p.add_argument("--pre", type=float, default=14.0, help="seconds kept before the chat reaction starts")
    p.add_argument("--post", type=float, default=14.0, help="seconds kept after the chat reaction starts")
    p.add_argument("--cooldown", type=float, default=45.0, help="minimum seconds between two clips on one channel")
    p.add_argument("--segment", type=int, default=10, help="recording segment length in seconds")
    p.add_argument("--buffer-minutes", type=float, default=30.0,
                   help="keep only this many minutes of recording on disk (0 = keep the whole stream)")
    p.add_argument("--formats", default="vertical,horizontal", help="outputs per clip: vertical (9:16 short), horizontal (16:9)")
    p.add_argument("--no-captions", action="store_true", help="skip whisper and burned captions")
    p.add_argument("--whisper-model", default="small", help="faster-whisper model: tiny, base, small, medium, large-v3")
    p.add_argument("--language", default=None, help="caption language code (default: auto-detect per clip)")
    p.add_argument("--encoder", default="amf", choices=["x264", "amf", "nvenc", "qsv"], help="video encoder")
    p.add_argument("--layout", default="auto", choices=["auto", "stack", "split", "fill", "fit"],
                   help="vertical: split = webcam on top + gameplay below, fill = gameplay full screen, "
                        "fit = whole 16:9 frame on a blurred background; auto = split when a webcam is found, else fill")
    p.add_argument("--no-fx", action="store_true",
                   help="no reaction effects (by default: boom + punch-in zoom + emoji on the streamer's reactions, about "
                        "one per 4 s; a light zoom pulse + tap on any longer stretch without one; whoosh on jump cuts; "
                        "all sounds are made locally, no copyrighted meme audio)")
    p.add_argument("--teaser", action="store_true",
                   help="cold open: the streamer's loudest shouted line also plays first (off by default: checked by eye "
                        "on 3 clips it repeated a later line and the hard cut confused more than it hooked)")
    p.add_argument("--no-jumpcuts", action="store_true",
                   help="keep the quiet stretches (by default gaps with no speech and quiet game audio are cut out)")
    # Damir 19 Nov: "i never asked for this only nudity" - swear words are never starred/bleeped by default
    p.add_argument("--censor", action="store_true", help="star swear words in burned captions (off by default)")
    p.add_argument("--tags", default="", help="campaign hashtags, first one is also the name the post text must mention, "
                   "e.g. --tags LACY (Reach / Content Rewards rules: name in the caption + #LACY)")
    p.add_argument("--hook", action="store_true", help="vertical: show a headline at the top for the first 3.6 s")
    p.add_argument("--credit", action="store_true", help="vertical: show twitch.tv/<channel> on the video "
                   "(the post caption always credits the channel)")
    p.add_argument("--zoom", type=float, default=1.0, help="vertical: crop the sides by this factor before fitting (1.0 = whole frame)")
    p.add_argument("--max-clips-per-hour", type=int, default=40, help="safety cap per channel")
    p.add_argument("--only-game", metavar="GAME",
                   help='clip only while this game is played, e.g. "Grand Theft Auto VI" (past streams: Twitch chapter '
                        "markers; live: the stream category, re-checked every minute)")
    p.add_argument("--max-minutes", type=float, default=0, help="stop by itself after this many minutes (0 = run until Ctrl+C)")
    p.add_argument("--analyze", type=Path, metavar="CHAT_JSONL",
                   help="replay a logged chat.jsonl through the detector and print where it would clip, then exit")
    p.add_argument("--vod", metavar="CHANNEL|VIDEO_URL|ID",
                   help="past-stream mode: find the best moments of a saved broadcast (a channel name = its latest one, "
                        "including the one live right now), using its chat replay and viewer-made clips")
    p.add_argument("--best", type=int, default=10, help="past-stream mode: how many top moments to render")
    p.add_argument("--crowd", action="store_true",
                   help="past-stream mode: pick ONLY moments viewers clipped themselves (an independent review found "
                        "this the only reliable signal), cut from the viewer's own start/end, no chat replay needed")
    p.add_argument("--clip-period", default="LAST_WEEK", choices=["LAST_DAY", "LAST_WEEK", "LAST_MONTH", "ALL_TIME"],
                   help="crowd mode: only viewer clips made in this period")
    p.add_argument("--min-views", type=int, default=100, help="crowd mode: a viewer clip needs at least this many views")
    p.add_argument("--range", metavar="START-END",
                   help="past-stream mode: render exactly this stretch as one clip, e.g. 6h10m30s-6h16m or 6:10:30-end")
    a = p.parse_args(argv)
    if not a.channels and not a.game and not a.analyze and not a.vod:
        p.error("give channel names, or --game for auto mode, or --vod for a past stream, or --analyze")
    cfg = Config(
        channels=[c.split(":")[0].lower().strip().lstrip("#").split("/")[-1] for c in a.channels],
        channel_tags={c.split(":")[0].lower().strip().lstrip("#").split("/")[-1]: [t for t in c.split(":")[1:] if t]
                      for c in a.channels if ":" in c},
        game=a.game, top=a.top, lang=(a.lang.lower() if a.lang else None), rescan=a.rescan,
        out=a.out.resolve(), work=a.work.resolve(), quality=a.quality, poll=a.poll,
        bucket=a.bucket, baseline_buckets=a.baseline_buckets, warmup_buckets=a.warmup_buckets,
        sensitivity=a.sensitivity, min_score=a.min_score, pre=a.pre, post=a.post, cooldown=a.cooldown,
        segment=a.segment, buffer_minutes=a.buffer_minutes,
        formats=[f.strip() for f in a.formats.split(",") if f.strip()],
        captions=not a.no_captions, whisper_model=a.whisper_model, language=a.language,
        encoder=a.encoder, zoom=max(1.0, a.zoom), layout=a.layout, only_game=a.only_game, hook=a.hook, credit=a.credit, tags=[t.strip().lstrip('#') for t in a.tags.split(',') if t.strip()], censor=a.censor, jumpcuts=not a.no_jumpcuts, teaser=a.teaser, fx=not a.no_fx, max_clips_per_hour=a.max_clips_per_hour,
    )
    return cfg, a


# --------------------------------------------------------------------------- Twitch public data

GQL_URL = "https://gql.twitch.tv/gql"
# Twitch's public web-player client id (the same one streamlink uses). No account or token involved.
GQL_CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"


def gql(query: str, variables: dict | None = None, timeout: float = 15):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(GQL_URL, data=body, headers={"Client-ID": GQL_CLIENT_ID, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    if d.get("errors"):
        raise RuntimeError(d["errors"])
    return d["data"]


def stream_info(login: str):
    """Returns the live stream dict, None when offline. Raises ValueError for a channel that does not exist."""
    d = gql("query($l:String!){ user(login:$l){ login displayName stream{ id title viewersCount createdAt game{name} } } }",
            {"l": login})
    if not d.get("user"):
        raise ValueError(f"Twitch channel '{login}' does not exist")
    return d["user"]["stream"]


def top_streams(game: str, n: int, lang: str | None):
    d = gql("query($g:String!){ game(name:$g){ streams(first:100){ edges{ node{ broadcaster{login} viewersCount language } } } } }",
            {"g": game})
    if not d.get("game"):
        raise ValueError(f"no Twitch category named '{game}'")
    out = []
    for e in d["game"]["streams"]["edges"]:
        node = e["node"]
        if lang and (node.get("language") or "").lower() != lang:
            continue
        out.append(node["broadcaster"]["login"])
    return out


# --------------------------------------------------------------------------- chat

BOTS = {"nightbot", "streamelements", "moobot", "fossabot", "streamlabs", "soundalerts", "wizebot",
        "sery_bot", "botrixoficial", "kofistreambot", "commanderroot", "pokemoncommunitygame", "own3d", "blerp"}

HYPE_RE = re.compile(
    # substrings on purpose: channel emotes are prefix + name (kaiLUL, azteBigLaugh, xqcPog)
    r"(kekw|lul|laugh|\blol+\b|lmao+|lmfao|pog|holy|\bwtf\b|\bomg\b|no ?way|insane|xdd|"
    r"let'?s ?go+|\bw{2,}\b|^w+$|\?{3,}|!{3,}|\bha(ha)+|icant|monka|bro what|\bnah+\b|"
    "\U0001F602|\U0001F923|\U0001F480|\U0001F525|\U0001F62D|\U0001F631)",
    re.I,
)
AD_RE = re.compile(r"\bads?\b|\bad break|commercial|\bpre-?roll", re.I)
POLL_ASK = re.compile(r"\b(type|spam|put|drop)\b[^.?!]{0,40}\b(in|into|the) (the )?chat\b" r"|\bchat,? (type|spam)\b", re.I)
CLIP_RE = re.compile(r"\bclip(ped| it|ping)?\b|\+2\b", re.I)


def chat_weight(text: str) -> float:
    w = 1.0
    if HYPE_RE.search(text):
        w += 0.5
    if CLIP_RE.search(text):
        w += 1.0
    return w


class ChatReader(threading.Thread):
    """Anonymous, read-only Twitch IRC client. Calls on_msg(t_local, user, text) for every chat message."""

    def __init__(self, channel: str, on_msg, stop: threading.Event):
        super().__init__(daemon=True, name=f"chat-{channel}")
        self.channel, self.on_msg, self.stop = channel, on_msg, stop
        self.connected = False

    def run(self):
        backoff = 2
        while not self.stop.is_set():
            try:
                self._session()
                backoff = 2
            except Exception as e:  # noqa: BLE001 - any network failure means reconnect
                self.connected = False
                if self.stop.is_set():
                    break
                log(self.channel, f"chat disconnected ({e}); reconnecting in {backoff}s")
            self.stop.wait(backoff)
            backoff = min(backoff * 2, 60)

    def _connect(self):
        try:
            raw = socket.create_connection(("irc.chat.twitch.tv", 6697), timeout=20)
            return ssl.create_default_context().wrap_socket(raw, server_hostname="irc.chat.twitch.tv")
        except (ssl.SSLError, OSError):
            return socket.create_connection(("irc.chat.twitch.tv", 6667), timeout=20)

    def _session(self):
        s = self._connect()
        try:
            nick = f"justinfan{int(time.time() * 1000) % 89999 + 10000}"
            s.sendall(f"CAP REQ :twitch.tv/tags twitch.tv/commands\r\nPASS SCHMOOPIIE\r\nNICK {nick}\r\nJOIN #{self.channel}\r\n".encode())
            s.settimeout(1.0)
            buf, last_rx = b"", time.time()
            while not self.stop.is_set():
                try:
                    data = s.recv(65536)
                except socket.timeout:
                    if time.time() - last_rx > 360:
                        raise TimeoutError("no data from chat for 6 minutes")
                    continue
                if not data:
                    raise ConnectionError("server closed the connection")
                last_rx = time.time()
                buf += data
                *lines, buf = buf.split(b"\r\n")
                for raw in lines:
                    self._handle(s, raw.decode("utf-8", "replace"), last_rx)
        finally:
            try:
                s.close()
            except OSError:
                pass

    def _handle(self, s, line: str, now: float):
        if line.startswith("PING"):
            s.sendall(b"PONG :tmi.twitch.tv\r\n")
            return
        if line.startswith("@"):
            _, _, line = line.partition(" ")
        prefix = ""
        if line.startswith(":"):
            prefix, _, line = line.partition(" ")
        head, _, text = line.partition(" :")
        cmd = head.split(" ", 1)[0]
        if cmd == "PRIVMSG":
            user = prefix[1:].split("!", 1)[0]
            self.on_msg(now, user, text)
        elif cmd == "JOIN" and not self.connected:
            self.connected = True
            log(self.channel, "chat connected (anonymous, read-only)")
        elif cmd == "RECONNECT":
            raise ConnectionError("Twitch asked chat clients to reconnect")


# --------------------------------------------------------------------------- spike detection


def spike_ratio(median_score: float, sensitivity: float) -> float:
    """How many times the baseline a window must reach. `sensitivity` is the ratio for a mid-size chat
    (median score 40 per 10 s, about 3 msg/s). Big chats saturate - slow mode, the per-chatter cap, everyone
    already typing - so their spikes are smaller ratios; small chats are noisy and need bigger ones.
    Measured on live GTA VI chats: the biggest 7-minute spike was 1.6x at 11.6 msg/s but 5.2x at 0.9 msg/s."""
    r = 1.0 + (sensitivity - 1.0) * (40.0 / max(median_score, 1.0)) ** 0.4
    return min(4.0, max(1.35, r))


@dataclass
class Spike:
    onset: float          # wall-clock time the chat reaction starts
    bucket_start: float
    score: float          # chat score of the spike window
    baseline: float       # median score of recent windows
    threshold: float
    ratio: float
    sample: list          # chat messages around the moment


class SpikeDetector:
    """Scores chat per fixed window and reports windows that jump well above the rolling median.

    Score of a window = sum of message weights, each chatter counted at most 3 times per window,
    known bots ignored, hype words +0.5, "clip it" +1. A spike fires once, then the detector
    re-arms only after chat falls back under the threshold, and never inside the cooldown.
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.b = cfg.bucket
        self.lock = threading.Lock()
        self.buckets: dict[int, list] = {}                # idx -> [score, n_msgs, Counter(users)]
        self.per_sec = collections.defaultdict(float)      # int(second) -> score
        self.recent = collections.deque()                  # (t, user, text) for samples
        self.history = collections.deque(maxlen=cfg.baseline_buckets)
        self.last_closed: int | None = None
        self.armed = True
        self.cooldown_until = 0.0
        self.last = {"score": 0.0, "baseline": None, "threshold": None, "msgs": 0}
        self.series: list[tuple] = []                      # (window start, score, baseline) for every closed window

    def add(self, t: float, user: str, text: str):
        if user in BOTS or text.startswith("!"):   # bots and bot commands (!gamble, !song) are not reactions
            return
        if AD_RE.search(text):                     # chat complaining about an ad break is not a moment
            return
        with self.lock:
            self.recent.append((t, user, text))
            while self.recent and self.recent[0][0] < t - 120:
                self.recent.popleft()
            idx = int(t // self.b)
            bk = self.buckets.setdefault(idx, [0.0, 0, collections.Counter(), collections.Counter()])
            bk[1] += 1
            norm = re.sub(r"(.)\1{2,}", r"\1\1", text.strip().lower())
            if len(norm) <= 12 and not HYPE_RE.search(norm) and not CLIP_RE.search(norm):
                bk[3][norm] += 1                   # short non-reaction replies, to spot "type X in chat" polls
            bk[2][user] += 1
            if bk[2][user] > 3:
                return
            w = chat_weight(text)
            bk[0] += w
            self.per_sec[int(t)] += w

    def tick(self, now: float) -> list[Spike]:
        """Close every window that ended at least 1 s ago. Returns spikes found."""
        out = []
        with self.lock:
            cur = int((now - 1.0) // self.b)          # windows with idx < cur are complete
            if self.last_closed is None:
                if not self.buckets:
                    return out
                self.last_closed = min(self.buckets) - 1
            for idx in range(self.last_closed + 1, cur):
                sp = self._close(idx)
                if sp:
                    out.append(sp)
                self.last_closed = idx
            for s in [s for s in self.per_sec if s < now - 300]:
                del self.per_sec[s]
        return out

    def _close(self, idx: int) -> Spike | None:
        score, n, _, replies = self.buckets.pop(idx, [0.0, 0, None, collections.Counter()])
        start = idx * self.b
        hist = list(self.history)
        self.history.append(score)
        if len(hist) < self.cfg.warmup_buckets:
            self.last = {"score": score, "baseline": None, "threshold": None, "msgs": n}
            return None
        med = statistics.median(hist)
        self.series.append((start, score, med))
        if len(self.series) > 20000:
            del self.series[:5000]
        thr = max(self.cfg.min_score, med * spike_ratio(med, self.cfg.sensitivity), med + 5.0 * math.sqrt(max(med, 1.0)))
        self.last = {"score": score, "baseline": med, "threshold": thr, "msgs": n}
        if score < thr:
            self.armed = True
            return None
        if not self.armed or start < self.cooldown_until:
            return None
        top = replies.most_common(1)
        if top and n and top[0][1] >= 0.25 * n:
            # the streamer asked chat to type something ("type ME if you've been up since 5"): a poll, not a moment
            self.last["poll"] = top[0][0]
            return None
        self.armed = False
        onset = self._onset(start, thr, med)
        self.cooldown_until = onset + self.cfg.cooldown
        sample = [m for m in self.recent if onset - 3 <= m[0] <= onset + 15]
        return Spike(onset=onset, bucket_start=start, score=score, baseline=med, threshold=thr,
                     ratio=score / max(med, 1.0), sample=[(round(t, 1), u, x) for t, u, x in sample[:40]])

    def _onset(self, start: float, thr: float, base: float) -> float:
        """Where the chat reaction starts: from the busiest 3 s of the spike window, walk back second by second
        while the 3 s rate stays above halfway between the baseline pace and the spike pace."""
        def rate(s):  # centred 3 s average
            return (self.per_sec.get(s - 1, 0) + self.per_sec.get(s, 0) + self.per_sec.get(s + 1, 0)) / 3.0
        level = (base + (thr - base) * 0.5) / self.b
        s_start = int(start)
        peak = max(range(s_start, s_start + self.b), key=rate)
        s = peak
        while s - 1 >= s_start - self.b and rate(s - 1) >= level:
            s -= 1
        return float(s)


# --------------------------------------------------------------------------- recording


@dataclass
class Segment:
    path: Path
    wall_start: float
    wall_end: float
    duration: float


class Recorder:
    """streamlink -> ffmpeg segment muxer. Each restart of the stream within a session is a new 'part'.

    Wall-clock mapping: a closed segment's last byte is written when its content has fully arrived, so
    its mtime is the wall time of its END; start = end - duration. (Anchoring on the end is what makes
    the first segment right: streamlink delivers the first few seconds in a burst.)
    """

    def __init__(self, channel: str, session_dir: Path, cfg: Config):
        self.channel, self.dir, self.cfg = channel, session_dir, cfg
        self.part = 0
        self.sl = self.ff = None
        self.started_at = 0.0
        self._cache: dict[str, Segment] = {}

    def start(self):
        self.part += 1
        prefix = f"p{self.part}_"
        sl_log = open(self.dir / f"{prefix}streamlink.log", "wb")
        ff_log = open(self.dir / f"{prefix}ffmpeg.log", "wb")
        sl_cmd = streamlink_cmd() + ["--twitch-low-latency", "--retry-open", "3", "--stdout",
                                     f"https://www.twitch.tv/{self.channel}", self.cfg.quality]
        self.sl = subprocess.Popen(sl_cmd, stdout=subprocess.PIPE, stderr=sl_log, stdin=subprocess.DEVNULL)
        ff_cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-i", "pipe:0",
                  "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy",
                  "-f", "segment", "-segment_time", str(self.cfg.segment), "-reset_timestamps", "1",
                  "-segment_list", f"{prefix}segments.csv", "-segment_list_type", "csv",
                  f"{prefix}seg_%06d.ts"]
        self.ff = subprocess.Popen(ff_cmd, stdin=self.sl.stdout, stdout=subprocess.DEVNULL, stderr=ff_log, cwd=self.dir)
        self.sl.stdout.close()
        self.started_at = time.time()

    def alive(self) -> bool:
        return self.ff is not None and self.ff.poll() is None

    def stop(self, timeout: float = 15):
        for p in (self.sl, self.ff):
            if p and p.poll() is None:
                if p is self.ff:
                    try:
                        p.wait(timeout=timeout)   # ffmpeg ends cleanly once streamlink closes the pipe
                        continue
                    except subprocess.TimeoutExpired:
                        pass
                p.terminate()
                try:
                    p.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    p.kill()

    def log_tail(self, n=6) -> str:
        f = self.dir / f"p{self.part}_streamlink.log"
        try:
            return " | ".join(f.read_text("utf-8", "replace").strip().splitlines()[-n:])
        except OSError:
            return ""

    def segments(self) -> list[Segment]:
        """All closed segments of this session, oldest first (deleted ones skipped)."""
        segs = []
        for csv_path in sorted(self.dir.glob("p*_segments.csv"), key=lambda p: int(p.name[1:].split("_")[0])):
            try:
                rows = list(csv.reader(csv_path.read_text("utf-8").splitlines()))
            except OSError:
                continue
            for row in rows:
                if len(row) < 3:
                    continue
                path = self.dir / row[0]
                seg = self._cache.get(row[0])
                if seg is None:
                    try:
                        end = path.stat().st_mtime
                    except FileNotFoundError:
                        continue
                    dur = float(row[2]) - float(row[1])
                    seg = Segment(path, end - dur, end, dur)
                    self._cache[row[0]] = seg
                elif not path.exists():
                    continue
                segs.append(seg)
        segs.sort(key=lambda s: s.wall_end)
        return segs


# --------------------------------------------------------------------------- clip production


@dataclass
class ClipJob:
    channel: str
    spike: Spike
    start: float
    end: float
    stream: dict
    session_dir: Path
    segments: list = field(default_factory=list)
    on_done: object = None
    extra: dict = field(default_factory=dict)       # merged into the clip's metadata record
    hook_sources: list = field(default_factory=list)  # human-written titles for this moment (viewer clips), best first
    react_end: float | None = None                  # when chat calmed down again (the clip ends on a sentence after it)


WIDE_PRE = 24.0      # a job's window opens this early, so the cut can start on a sentence
WIDE_POST = 8.0      # and stays open this long after chat calms down, so it can end on one
MAX_REACT = 46.0     # a reaction is followed for at most this long after it starts


def hot(per_sec, t0: float, t1: float, level: float) -> bool:
    """Is chat still at reaction pace (per second) between t0 and t1?"""
    secs = range(int(t0), int(t1) + 1)
    return sum(per_sec.get(s, 0) for s in secs) / max(1, len(secs)) >= level


def react_level(sp) -> float:
    """Chat pace (per second) that still counts as reacting: 40 % of the way from baseline to the spike threshold."""
    base = sp.baseline or 1.0
    thr = sp.threshold or base * 1.6
    return (base + 0.4 * (thr - base)) / 10.0


def ass_time(t: float) -> str:
    t = max(0.0, t)
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def srt_time(t: float) -> str:
    ms = int(round(max(0.0, t) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def ass_escape(s: str) -> str:
    return s.replace("\\", "").replace("{", "(").replace("}", ")")


HALLUCINATIONS = re.compile(r"(thank(s| you) for watching|subscribe|like and subscribe|subtitles by|amara\.org|"
                            r"see you (in the )?next (video|time)|\bmbc\b)", re.I)

# Safe zone on a 1080x1920 short: the apps cover the top bar, the bottom fifth (caption, username) and the right
# column (like / comment / share). Strictest of the editing-skill packs checked: x 120-960, y 210-1480.
SAFE = dict(x0=120, x1=960, y0=210, y1=1480)

LAYOUTS = {
    # caption: font size, outline, alignment, margins (left/right keep it inside SAFE x), top margin
    "vertical": dict(w=1080, h=1920, fs=80, outline=7, shadow=3, align=8, ml=SAFE["x0"], mr=1080 - SAFE["x1"], mv=1235,
                     tag_y=482, tag_fs=40, hook_y=250, hook_fs=78),
    "horizontal": dict(w=1920, h=1080, fs=66, outline=5, shadow=2, align=2, ml=120, mr=120, mv=70,
                       tag_y=None, tag_fs=0, hook_y=None, hook_fs=0),
}

# a line never ends on a word that leans into the next one
LEAN_IN = {"THE", "A", "AN", "TO", "OF", "AND", "OR", "BUT", "IS", "ARE", "WAS", "MY", "YOUR", "HIS", "HER", "OUR",
           "THEIR", "IN", "ON", "AT", "FOR", "WITH", "FROM", "BY", "I", "I'M", "YOU", "WE", "THEY", "IT'S", "THAT", "THIS",
           "SO", "IF", "AS", "DE", "LA", "EL", "LOS", "LAS", "UN", "UNA", "Y", "O", "E", "DO", "DA", "QUE", "EN", "LE", "LES"}
SWEARS = re.compile(r"^(mother)?f+u+c*k+\w*$|^sh+i+t+\w*$|^b+i+t+c+h+\w*$|^bullshit$|^ass(hole)?$|^dick\w*$|^pussy$|^cunt\w*$", re.I)


# Auto-picked reaction fx (emoji/boom/flash from loudness) are OFF: the user wants every meme matched by judgment
# via <base>.fx.json. No plan file -> captions + hook title only.
AUTO_FX = False

RU_STREAMERS = {"buster", "evelone2004", "strogo", "recrent", "t2x2", "mokrivskyi", "gagik", "gensyxa", "stintik",
                "frametamer666"}

# Russian mat (RU clips showed БЛЯ/БЛЯДЬ/ЕБАНАЯ uncensored - TikTok reach risk)
RU_SWEARS = re.compile(r"^(бля|ебан|ебат|ебал|ёб|еб[ау]|хуй|хуе|хуё|хуя|пизд|сук[аи]|мудак|пидор|залуп|нахуй|похуй)", re.I)


RU_ROOT = re.compile(r"(бл[яи]|[её]б|ху[йеёя]|пизд|сук|муд|пид|залуп)", re.I)


def censor_word(w: str) -> str:
    if SLURS.search(w):
        return w[0] + "*" * (len(w) - 1)
    r = RU_ROOT.search(w)
    if r and RU_SWEARS.search(w.strip("'?!.,-")):
        i = r.start() + 1                       # star the vowel inside the root: н*хуй -> нах*й
        return w[:i] + "*" + w[i + 1:]
    if SWEARS.match(w.strip("'?!.,-")):
        m = re.search(r"[AEIOUaeiouАЕЁИОУЫЭЮЯаеёиоуыэюя]", w[1:])
        if m:
            i = m.start() + 1
            return w[:i] + "*" + w[i + 1:]
    return w


FILLERS = {"UM", "UH", "UHH", "UMM", "ERM", "HMM", "MM", "AH", "EH"}


def chunk_words(words: list[dict], max_words=3, max_chars=14, max_gap=0.6) -> list[list[dict]]:
    """1-3 words per caption, cut at punctuation and pauses, never ending on a lean-in word mid-sentence."""
    words = [w for w in words if w["w"] not in FILLERS]
    chunks, cur = [], []

    def close():
        nonlocal cur
        if cur:
            chunks.append(cur)
            cur = []

    for i, w in enumerate(words):
        if cur:
            text_len = sum(len(x["w"]) + 1 for x in cur) + len(w["w"])
            pause = w["s"] - cur[-1]["e"] > max_gap
            full = len(cur) >= max_words or text_len > max_chars
            if pause or (full and not (cur[-1]["w"] in LEAN_IN and text_len <= max_chars + 6 and len(cur) < 4)):
                close()
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if re.search(r"[.!?,;:]$", w["raw"]) and not (w["w"] in LEAN_IN and nxt and nxt["s"] - w["e"] < 0.3):
            close()
    close()
    return chunks


SLURS = re.compile(r"n+[i1!]+g+[ae3]*r*|f+[a@]+g+|r+e+t+[a@]+r+d|k+[i1]+k+e|ch+[i1]+n+k|tr+[a@]+nn+y", re.I)


def pick_hook(viewer_titles: list[str], chat_sample: list, channel: str, stream_title: str | None) -> str | None:
    """On-screen hook for the first seconds. A viewer-made clip title is a human-written headline for exactly this
    moment, so it wins; otherwise the phrase chat repeated most. Nothing hateful, nothing generic."""
    generic = {channel.lower(), "gta", "gta 6", "gta6", "gta vi", "clip", "lol", "w", "l", (stream_title or "").lower()}

    def clean(t: str) -> str:
        # only characters the caption font can draw: letters (any language), digits, basic punctuation
        t = "".join(ch for ch in t if ch.isalnum() or ch in " '?!.,&-:")
        return re.sub(r"\s+", " ", t).strip(" -:,.")

    for t in viewer_titles:
        t = clean(t)
        if 3 <= len(t) <= 42 and t.lower() not in generic and not SLURS.search(t):
            return t.upper()
    # From chat only a phrase is a headline; a lone reaction (LMAO, YOO, W) is not a hook - better none than that.
    counts = collections.Counter()
    for _, _, m in chat_sample:
        norm = clean(re.sub(r"@\w+", "", re.sub(r"(.)\1{2,}", r"\1\1", m.upper())))
        letters = sum(ch.isalpha() for ch in norm)
        if 2 <= len(norm.split()) <= 6 and letters >= 6 and len(norm) <= 30 and norm.lower() not in generic \
                and not SLURS.search(norm):
            counts[norm] += 1
    best = counts.most_common(1)
    return best[0][0] if best and best[0][1] >= 3 else None


# where text sits for each vertical layout (all inside SAFE): split = cam 0-608 / game 608-1920
VERTICAL_TEXT = {
    "fit": {},
    "split": dict(mv=560, hook_y=760, tag_y=1420),      # captions on the seam, hook on the gameplay, credit low
    "stack": dict(mv=790, hook_y=1460 - 160, tag_y=1460),  # captions on the cam/game seam (y 838)
    "fill": dict(mv=1150, hook_y=330, tag_y=1420),
}


def build_ass(words: list[dict], layout: str, duration: float, credit: str | None, hook: str | None = None,
              kind: str = "fit") -> str:
    L = dict(LAYOUTS[layout])
    if layout == "vertical":
        L.update(VERTICAL_TEXT.get(kind, {}))
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {L['w']}", f"PlayResY: {L['h']}", "WrapStyle: 0",
        "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, "
        "MarginV, Encoding",
        f"Style: Cap,Arial Black,{L['fs']},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,1,0,1,"
        f"{L['outline']},{L['shadow']},{L['align']},{L['ml']},{L['mr']},{L['mv']},1",
        f"Style: Tag,Arial Black,{L['tag_fs'] or 40},&H30FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,1,0,1,"
        f"3,0,8,{L['ml']},{L['mr']},{L['tag_y'] or 40},1",
        f"Style: Hook,Arial Black,{L['hook_fs'] or 60},&H00FFFFFF,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,1,0,1,"
        f"8,4,8,{L['ml']},{L['mr']},{L['hook_y'] or 40},1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    if credit and L["tag_y"]:
        lines.append(f"Dialogue: 0,{ass_time(0)},{ass_time(duration)},Tag,,0,0,0,,{ass_escape(credit)}")
    if hook and L["hook_y"]:
        # builds word by word from 0.2 s and lands by ~1.4 s (the virality skill's 1.2-1.6 s window), holds to 3.6 s
        hw = hook.split()                              # pick_hook caps it at 42 characters; never drop words
        step = 1.0 / max(1, len(hw) - 1)              # first word at 0.3 s, last word lands at 1.3 s
        for k in range(len(hw)):
            s = 0.3 + k * step if len(hw) > 1 else 1.3
            e = 0.3 + (k + 1) * step if k + 1 < len(hw) else 3.6
            hidden = " ".join(hw[k + 1:])
            last = "{\\c&H00E5FF&}" + ass_escape(hw[k]) + "{\\c&HFFFFFF&}"
            txt = (ass_escape(" ".join(hw[:k])) + " " if k else "") + last
            if hidden:
                txt += " {\\alpha&HFF&}" + ass_escape(hidden)
            fade = "{\\fad(0,250)}" if k + 1 == len(hw) else ""
            lines.append(f"Dialogue: 2,{ass_time(s)},{ass_time(e)},Hook,,0,0,0,,{fade}{txt}")
    chunks = chunk_words(words)
    for ci, ch in enumerate(chunks):
        c_start = ch[0]["s"]
        nxt = chunks[ci + 1][0]["s"] if ci + 1 < len(chunks) else duration
        c_end = min(max(ch[-1]["e"] + 0.35, c_start + 0.5), nxt, duration)
        for wi, w in enumerate(ch):
            s = c_start if wi == 0 else w["s"]
            e = ch[wi + 1]["s"] if wi + 1 < len(ch) else c_end
            if e - s < 0.04:
                continue
            parts = []
            for k, x in enumerate(ch):
                t = ass_escape(x["w"])
                # the word being said turns yellow and pops (88% -> 110% in 80 ms)
                parts.append("{\\c&H00E5FF&\\fscx88\\fscy88\\t(0,80,\\fscx110\\fscy110)}" + t + "{\\r}" if k == wi else t)
            lines.append(f"Dialogue: 1,{ass_time(s)},{ass_time(e)},Cap,,0,0,0,,{' '.join(parts)}")
    return "\n".join(lines) + "\n"


_AMF_OK: bool | None = None


def amf_ok() -> bool:
    """1-frame test encode with h264_amf, cached for the process (falls back to libx264 when it fails)."""
    global _AMF_OK
    if _AMF_OK is None:
        try:
            r = subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=256x256",
                                "-frames:v", "1", "-c:v", "h264_amf", "-f", "null", "-"],
                               stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
            _AMF_OK = r.returncode == 0
        except Exception:
            _AMF_OK = False
    return _AMF_OK


X264_ARGS = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-threads", "4"]


def encoder_args(name: str, vertical: bool) -> list[str]:
    br = "10M" if vertical else "8M"
    if name == "amf":
        # no -hwaccel d3d11va: it corrupted the blurred background (green/gray halves). speed preset + cqp measured 1.7x faster than libx264 veryfast on this RX 6650 XT
        if not amf_ok():
            return X264_ARGS
        return ["-c:v", "h264_amf", "-usage", "transcoding", "-quality", "speed", "-rc", "cqp",
                "-qp_i", "25", "-qp_p", "27", "-profile:v", "high"]
    if name == "nvenc":
        return ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "21", "-b:v", br]
    if name == "qsv":
        return ["-c:v", "h264_qsv", "-global_quality", "22", "-b:v", br]
    return X264_ARGS


class ClipFactory(threading.Thread):
    """One worker for all channels: cut -> transcribe -> render -> index. Holds the whisper model."""

    def __init__(self, cfg: Config):
        super().__init__(daemon=True, name="clip-factory")
        self.cfg = cfg
        self.q: queue.Queue[ClipJob] = queue.Queue()
        self.locked: collections.Counter = collections.Counter()   # segment paths a queued/running job needs
        self.lock = threading.Lock()
        self.model = None
        self.busy = False
        self.done_count = 0
        self.font = self._find_font()
        self.last_cam: dict = {}                        # channel -> (cam, cam_left, cam_right) last seen

    @staticmethod
    def _find_font() -> Path | None:
        for d in (Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts", Path("/usr/share/fonts"), Path("/Library/Fonts")):
            for name in ("ariblk.ttf", "Arial Black.ttf", "ArialBlack.ttf"):
                if (d / name).exists():
                    return d / name
        return None

    def submit(self, job: ClipJob):
        with self.lock:
            for s in job.segments:
                self.locked[str(s.path)] += 1
        self.q.put(job)

    def is_locked(self, path: Path) -> bool:
        with self.lock:
            return self.locked.get(str(path), 0) > 0

    def pending(self) -> int:
        return self.q.qsize() + (1 if self.busy else 0)

    def preload(self):
        if self.cfg.captions and self.model is None:
            from faster_whisper import WhisperModel
            log("captions", f"loading whisper '{self.cfg.whisper_model}' (first run downloads it)")
            self.model = WhisperModel(self.cfg.whisper_model, device="cpu", compute_type="int8",
                                      cpu_threads=max(2, min(4, (os.cpu_count() or 4) // 3)))
            log("captions", "whisper ready")

    def run(self):
        try:
            self.preload()
        except Exception as e:  # noqa: BLE001
            log("captions", f"whisper unavailable ({e}); clips will be made without captions")
            self.cfg.captions = False
        while True:
            job = self.q.get()
            self.busy = True
            try:
                self.make(job)
            except Exception:  # noqa: BLE001
                log(job.channel, "clip failed:\n" + traceback.format_exc())
            finally:
                with self.lock:
                    for s in job.segments:
                        self.locked[str(s.path)] -= 1
                        if self.locked[str(s.path)] <= 0:
                            del self.locked[str(s.path)]
                self.busy = False
                if job.on_done:
                    job.on_done()
                self.q.task_done()

    # -- one clip
    def make(self, job: ClipJob):
        cfg, sp = self.cfg, job.spike
        segs = [s for s in job.segments if s.path.exists()]
        if not segs:
            log(job.channel, "clip skipped: its recording segments are gone")
            return
        start = max(job.start, segs[0].wall_start)
        end = min(job.end, segs[-1].wall_end)
        dur = end - start
        if dur < 3:
            log(job.channel, f"clip skipped: only {dur:.1f}s of recording covers the moment")
            return
        offset = start - segs[0].wall_start
        when = dt.datetime.fromtimestamp(sp.onset)
        day_dir = Path(job.extra["out_dir"]) if job.extra.get("out_dir") else cfg.out / job.channel / f"{when:%Y-%m-%d}"
        day_dir.mkdir(parents=True, exist_ok=True)
        base = job.extra.get("file_base") or f"{job.channel}_{when:%H%M%S}_x{sp.ratio:.1f}"   # re-renders keep their name
        tmp = job.session_dir / f"tmp_{when:%H%M%S}"
        tmp.mkdir(exist_ok=True)
        t0 = time.time()
        try:
            listing = "".join("file '" + str(s.path).replace("\\", "/").replace("'", "'\\''") + "'\n" for s in segs)
            (tmp / "list.txt").write_text(listing, "utf-8")
            # Seek on the INPUT side: the filter graph (and so the burned subtitles) then runs on the clip's own
            # timeline starting at 0. Seeking on the output side shifted every caption by `offset` seconds.
            src = ["-ss", f"{offset:.3f}", "-t", f"{dur:.3f}", "-f", "concat", "-safe", "0", "-i", "list.txt"]

            words, segments_txt, lang = [], [], None
            if cfg.captions and self.model is not None:
                run_ff(src + ["-vn", "-ac", "1", "-ar", "16000", "audio.wav"], cwd=tmp)
                # short RU clips got auto-detected as English (recrent_140210r) -> force Russian for RU streamers
                words, segments_txt, lang = self.transcribe(tmp / "audio.wav",
                                                            "ru" if job.channel in RU_STREAMERS else None)
            said = " ".join(t for _, _, t in segments_txt)
            replies = collections.Counter(re.sub(r"(.)\1{2,}", r"\1\1", x.strip().lower()) for _, _, x in sp.sample)
            top = replies.most_common(1)
            if POLL_ASK.search(said) and top and len(top[0][0]) <= 12 and top[0][1] >= 0.3 * max(1, len(sp.sample)):
                # found on Clix: "type ME if you have a girlfriend" -> chat answers, nothing happened on screen
                log(job.channel, f"clip dropped: the streamer asked chat to type something ('{top[0][0]}'), not a moment")
                return
            wav_shift = 0.0                         # where the clip starts inside audio.wav (wide window)
            if not job.extra.get("fixed"):
                # Length follows the moment (user: "why all exactly 28 s, does it sacrifice good moments?"):
                # the job holds a wide window; start on a sentence near `pre` s before the reaction, end on a
                # sentence after chat calms down. 15-60 s.
                rel_onset = sp.onset - start
                s_rel = sentence_start(segments_txt, rel_onset - cfg.pre, rel_onset - 22, rel_onset - 6)
                e_rel = sentence_end(segments_txt, (job.react_end or sp.onset + cfg.post) - start)
                s_rel = max(0.0, s_rel)
                e_rel = min(dur, max(e_rel, s_rel + 15.0), s_rel + 60.0)   # user: up to 1 minute
                if s_rel > 0.05 or e_rel < dur - 0.05:
                    words = [dict(w, s=w["s"] - s_rel, e=w["e"] - s_rel) for w in words if s_rel <= w["s"] and w["e"] <= e_rel]
                    segments_txt = [(max(0.0, a - s_rel), min(e_rel, b) - s_rel, t) for a, b, t in segments_txt
                                    if b > s_rel and a < e_rel]
                    start, offset, dur = start + s_rel, offset + s_rel, e_rel - s_rel
                    wav_shift = s_rel
                    src = ["-ss", f"{offset:.3f}", "-t", f"{dur:.3f}", "-f", "concat", "-safe", "0", "-i", "list.txt"]
            # Jump cuts (user: "no boring moments where the streamer does nothing or says nothing"): a gap with no
            # speech AND quiet game audio is cut out; loud gaps (crash, gunfire, a scream) stay.
            keeps, rms = [(0.0, dur)], None
            words_orig = list(words)
            if cfg.jumpcuts and cfg.captions and words and (tmp / "audio.wav").exists():
                rms = wav_rms(tmp / "audio.wav")
                motion = picture_motion(tmp, src)
                keeps = quiet_cuts(words, rms, wav_shift, dur, motion=motion)
            new_dur = sum(b - a for a, b in keeps)
            if len(keeps) > 1:
                words = [dict(w, s=remap_t(keeps, w["s"]), e=remap_t(keeps, w["e"])) for w in words
                         if remap_t(keeps, w["s"]) is not None and remap_t(keeps, w["e"]) is not None]
                segments_txt = [(remap_t(keeps, a, True), remap_t(keeps, b, True), t) for a, b, t in segments_txt]
                log(job.channel, f"jump cuts: {len(keeps) - 1} quiet gaps removed, {dur:.0f}s -> {new_dur:.0f}s")
            # Cold open (user: "the hook is speed"): the payoff must land in the first 1-2 s. The loudest moment
            # (a shout, a crash) also plays first as a ~2 s teaser, then the clip runs from its setup.
            teaser = None
            if cfg.teaser and rms is not None:
                teaser = shout_teaser(words_orig, rms, wav_shift, keeps)
            if teaser:
                pa, pb = teaser
                tl = pb - pa
                words = ([dict(w, s=w["s"] - pa, e=w["e"] - pa) for w in words_orig if pa <= w["s"] and w["e"] <= pb]
                         + [dict(w, s=w["s"] + tl, e=w["e"] + tl) for w in words])
                segments_txt = [(a + tl, b + tl, t) for a, b, t in segments_txt]
                keeps = [teaser] + keeps
                new_dur += tl
                log(job.channel, f"cold open: {tl:.1f}s teaser from {pa:.1f}s plays first")
            srt_path = day_dir / f"{base}.srt"
            write_srt(srt_path, segments_txt)

            if self.font:
                shutil.copy2(self.font, tmp / self.font.name)
            credit = f"twitch.tv/{job.channel}"
            hook = pick_hook(job.hook_sources, sp.sample, job.channel, (job.stream or {}).get("title"))
            files = {"srt": srt_path.name}
            qc = {}
            cam, frame = None, {}
            if "vertical" in cfg.formats and cfg.layout in ("auto", "stack", "split", "fill"):
                cam, frame = self.find_facecam(tmp, src, dur)
                cam_file = cfg.work / job.channel / "last_cam.json"   # remembered across runs
                if job.channel not in self.last_cam and cam_file.exists():
                    try:
                        self.last_cam[job.channel] = tuple(json.loads(cam_file.read_text("utf-8")))
                    except (OSError, ValueError):
                        pass
                if cam:
                    self.last_cam[job.channel] = (cam, frame.get("cam_left"), frame.get("cam_right"))
                    cam_file.parent.mkdir(parents=True, exist_ok=True)
                    cam_file.write_text(json.dumps(self.last_cam[job.channel]), "utf-8")
                elif job.channel in self.last_cam:
                    # streamer ducked or fell out of frame (found on Lacy): his webcam is still where it was
                    cam, frame["cam_left"], frame["cam_right"] = self.last_cam[job.channel]
                    cam = dict(cam, reused=True)
            # auto: webcam + full game frame; no webcam -> the full game frame on blur. Never a cropped game.
            vlayout = cfg.layout if cfg.layout != "auto" else ("stack" if cam else "fit")
            if vlayout in ("split", "stack") and not cam:
                vlayout = "fit"
            # Reaction effects. A per-clip plan <out_dir>/<base>.fx.json, written by judgment, wins over the
            # auto-pick (user: "ur meme dont match the thing happening"): [{"t", "sound", "visual", "why"}]
            fx_peaks, cut_times, faces = [], [], []
            plan_file = day_dir / f"{base}.fx.json"
            if cfg.fx:
                acc = 0.0
                for a, b in keeps[:-1]:
                    acc += b - a
                    cut_times.append(round(acc, 2))
            if cfg.fx and plan_file.exists():
                fx_peaks = memes.from_plan(json.loads(plan_file.read_text("utf-8")), new_dur)
                log(job.channel, f"reaction fx from {plan_file.name}: " + memes.describe(fx_peaks))
            elif cfg.fx and AUTO_FX and rms is not None and words_orig:   # off: memes only from a judged plan
                body = keeps[1:] if teaser else keeps
                lead = (keeps[0][1] - keeps[0][0]) if teaser else 0.0
                looks = {}                                  # peak time -> the face seen in the webcam then

                def present(t):
                    looks[t] = self.at_webcam(tmp, src, cam, t)
                    return bool(looks[t])
                # the user: "too much a bit" - about one hit per 8 s, 6 s apart at least, no filler beats
                info = {}
                for tp, emo in reaction_peaks(words_orig, rms, wav_shift, most=max(2, int(new_dur / 8)), gap=6.0,
                                              present=present if cam else None, info=info):
                    tt = remap_t(body, tp)
                    if tt is not None and 0.3 < tt + lead < new_dur - 0.6:
                        box = looks.get(tp)
                        fx_peaks.append({"t": round(tt + lead, 2), "kind": "reaction", "rank": info[tp]["rank"],
                                         "mood": memes.mood_of(info[tp]["near"]),
                                         "face": face_in_panel(cam, frame, box if isinstance(box, tuple) else None)
                                         if vlayout == "stack" else None})
                fx_peaks = memes.plan(sorted(fx_peaks, key=lambda h: h["t"]), seed=base,
                                      memes=2 if new_dur >= 30 else 1, streamer=job.channel)
                if fx_peaks:
                    log(job.channel, "reaction fx: " + memes.describe(fx_peaks))
            # sounds only (user 2026-11-19: "keep only sound bro"): no meme video, emoji or flash - except text cards
            # like "Mission passed! Respect +" ("the writing memes are good")
            fx_peaks = [h if (h.get("overlay") or {}).get("text") or h.get("popup") else
                        {k: v for k, v in h.items() if k not in ("emoji", "overlay")} | {"visual": None}
                        for h in fx_peaks]
            title = hook_title(day_dir, base, job.channel) if "vertical" in cfg.formats else None
            for fmt in cfg.formats:
                if fmt not in LAYOUTS:
                    continue
                kind = vlayout if fmt == "vertical" else "horizontal"
                ass_name = f"{fmt}.ass"
                (tmp / ass_name).write_text(build_ass(words, fmt, new_dur, credit if cfg.credit else None,
                                                             hook if cfg.hook and not title else None, kind), "utf-8")
                out = day_dir / f"{base}_{fmt}.mp4"
                prefix, vin, ain = cut_graph(keeps)
                use_fx = fmt == "vertical" and (fx_peaks or cut_times)
                self._fx = fx_peaks if (fmt == "vertical" and kind == "stack") else []
                vf = prefix + self.filter_graph(fmt, ass_name, kind, cam, frame).replace("[0:v]", vin, 1)
                self._fx = []
                extra = []
                if use_fx:
                    vf, extra = add_fx(vf, ain, fx_peaks, cut_times, new_dur, tmp, HERE / "fx")
                else:
                    vf += f";{ain}{VOICE},{FINAL_AUDIO}[aout]"
                if fmt == "vertical" and title:
                    hy = hook_png(title, tmp / "hook.png", hook_bottom(kind, cam, frame))
                    hi, end = 1 + extra.count("-i"), vf.rfind("[v]")
                    # pop-in: 0.15 s fade with a short drop, holds, fades out 3.0-3.3 s
                    vf = (vf[:end] + "[vh]" + vf[end + 3:] +
                          f";[{hi}:v]format=rgba,fade=t=in:st=0:d=0.15:alpha=1,fade=t=out:st=3.0:d=0.3:alpha=1[hk];"
                          f"[vh][hk]overlay=x={HOOK_SIDE}:y='{hy}-24*exp(-t*20)':eof_action=pass:"
                          f"enable='lte(t,{HOOK_END})'[v]")
                    extra = extra + ["-loop", "1", "-framerate", "60", "-t", f"{HOOK_END}", "-i", "hook.png"]
                    log(job.channel, f"hook title at y {hy}: {title}")
                def render(enc: str):
                    run_ff(src + extra +
                           ["-filter_complex", vf, "-map", "[v]", "-map", "[aout]",
                            *encoder_args(enc, fmt == "vertical"), "-pix_fmt", "yuv420p",
                            "-r", "60", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                            "-movflags", "+faststart", str(out)], cwd=tmp)
                try:
                    render(cfg.encoder)
                except RuntimeError as e:
                    if cfg.encoder == "x264":
                        raise
                    log(job.channel, f"{cfg.encoder} render failed, retrying with libx264: {str(e)[-200:]}")
                    render("x264")
                files[fmt] = out.name
                if fmt == "vertical":
                    qc = self.qc_safe_zone(tmp, ass_name, new_dur)
                    if qc.get("frames_outside_safe_zone"):
                        log(job.channel, f"QC: text left the safe zone in {qc['frames_outside_safe_zone']} frames "
                                         f"(bbox {qc['text_bbox']})")
            qc["caption_words"] = len(words)
            qc["virality"] = virality_score(words, new_dur, segments_txt, rms, wav_shift, keeps, sp.ratio,
                                            job.extra.get("viewer_clips") or [], qc.get("dead_air_s", 0))
            if cfg.captions and not words:
                log(job.channel, "QC: no captions in this clip (no speech found)")
            qc["dead_air_s"] = dead_air(tmp, src)
            if qc["dead_air_s"] >= 4:
                log(job.channel, f"QC: {qc['dead_air_s']:.0f}s of black or frozen picture in this clip")
            post = day_dir / f"{base}_post.txt"
            game_name = ((job.stream or {}).get("game") or {}).get("name")   # GQL gives game as {"name": ...}
            post.write_text(post_caption(hook, job.channel, game_name, (job.stream or {}).get("title"),
                                         cfg.channel_tags.get(job.channel) or cfg.tags), "utf-8")
            files["post_caption"] = post.name
            first = day_dir / files.get("vertical", files.get("horizontal", ""))
            if first.suffix == ".mp4":
                thumb = day_dir / f"{base}.jpg"
                peak = (remap_t(keeps[1:], sp.onset - start + 1.0, True) or 0.0) + (keeps[0][1] - keeps[0][0]) if teaser \
                    else (remap_t(keeps, sp.onset - start + 1.0, True) or 0.0)
                peak = min(max(0.0, peak), new_dur - 0.1)
                run_ff(["-ss", f"{peak:.2f}", "-i", str(first), "-frames:v", "1", "-q:v", "3", str(thumb)], cwd=tmp)
                files["thumbnail"] = thumb.name
            transcript = " ".join(t for _, _, t in segments_txt).strip()
            rec = {
                "file_base": base, "channel": job.channel,
                "stream_title": (job.stream or {}).get("title"),
                "game": ((job.stream or {}).get("game") or {}).get("name"),
                "moment": when.isoformat(timespec="seconds"),
                "clip_start": dt.datetime.fromtimestamp(start).isoformat(timespec="seconds"),
                "duration": round(new_dur, 2), "jump_cuts": len(keeps) - 1, "cut_seconds": round(dur - new_dur, 1),
                "chat_score": round(sp.score, 1), "baseline": round(sp.baseline, 1), "ratio": round(sp.ratio, 2),
                "caption_language": lang, "transcript": transcript, "hook": hook, "hook_title": title, "qc": qc,
                "vertical_layout": vlayout, "facecam": cam, "framing": frame,
                "chat_sample": [f"{u}: {x}" for _, u, x in sp.sample[:12]],
                "files": files, "folder": str(day_dir),
                **job.extra,
            }
            (day_dir / f"{base}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), "utf-8")
            with self.lock:
                idx = day_dir.parent.parent / "index.jsonl"     # <out>/<channel>/<date>/ -> <out>/index.jsonl
                rows = idx.read_text("utf-8").splitlines() if idx.exists() else []
                rows = [r for r in rows if f'"file_base": "{base}"' not in r]
                rows.append(json.dumps(rec, ensure_ascii=False))
                idx.write_text("\n".join(rows) + "\n", "utf-8")
            self.done_count += 1
            log(job.channel, f"CLIP READY {base}  ({dur:.0f}s, chat x{sp.ratio:.1f}, made in {time.time() - t0:.0f}s) "
                             f"-> {day_dir}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def qc_safe_zone(self, tmp: Path, ass_name: str, dur: float) -> dict:
        """Render only the text layer on black (4 fps, half size) and measure where it lands, frame by frame."""
        import numpy as np
        font_opt = ":fontsdir=." if self.font else ""
        w, h = 540, 960
        r = subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                            f"color=c=black:s=1080x1920:r={min(4.0, 120.0 / max(dur, 1)):.3f}:d={dur:.2f}", "-vf", f"ass={ass_name}{font_opt},scale={w}:{h}",
                            "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"], cwd=tmp, capture_output=True,
                           creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        if r.returncode != 0 or not r.stdout:
            return {"error": r.stderr.decode("utf-8", "replace")[-300:]}
        frames = np.frombuffer(r.stdout, dtype=np.uint8)[: (len(r.stdout) // (w * h)) * w * h].reshape(-1, h, w)
        x0, x1, y0, y1 = (SAFE[k] // 2 for k in ("x0", "x1", "y0", "y1"))
        bad, bbox = 0, None
        for f in frames:
            ys, xs = np.nonzero(f > 90)
            if not len(xs):
                continue
            b = [int(xs.min()) * 2, int(ys.min()) * 2, int(xs.max()) * 2, int(ys.max()) * 2]
            bbox = b if bbox is None else [min(bbox[0], b[0]), min(bbox[1], b[1]), max(bbox[2], b[2]), max(bbox[3], b[3])]
            if xs.min() < x0 or xs.max() > x1 or ys.min() < y0 or ys.max() > y1:
                bad += 1
        return {"frames_checked": int(len(frames)), "frames_outside_safe_zone": bad, "text_bbox": bbox,
                "safe_zone": [SAFE["x0"], SAFE["y0"], SAFE["x1"], SAFE["y1"]]}

    def at_webcam(self, tmp: Path, src: list, cam: dict, t: float):
        """Is the streamer's face in his webcam at clip time t? Two looks, 0.1 s and 0.5 s after t. A loud line with
        nobody at the webcam is the game talking (Lacy lay on the floor while the game said "my case officer...").
        Returns the face (x, y, w, h as fractions of the frame), None when nobody is there, True when it cannot look."""
        model = HERE / "models" / "face_detection_yunet_2023mar.onnx"
        if not model.exists() or src[:1] != ["-ss"] or "-f" not in src:
            return True
        import cv2
        for f in tmp.glob("look_*.png"):
            f.unlink()
        seek = ["-ss", f"{float(src[1]) + max(0.0, t):.3f}"] + src[src.index("-f"):]
        try:
            run_ff(seek + ["-t", "0.7", "-an", "-vf", "select='eq(n,6)+eq(n,30)',scale=960:-2", "-fps_mode", "passthrough",
                           "look_%d.png"], cwd=tmp)
        except RuntimeError:
            return True                                     # cannot look: do not drop the reaction
        x0, x1 = cam["x"] - 0.25 * cam["w"], cam["x"] + 1.25 * cam["w"]
        y0, y1 = cam["y"] - 0.25 * cam["h"], cam["y"] + 1.25 * cam["h"]
        for f in sorted(tmp.glob("look_*.png")):
            img = cv2.imread(str(f))
            if img is None:
                continue
            H, W = img.shape[:2]
            det = cv2.FaceDetectorYN_create(str(model), "", (W, H), 0.75, 0.3, 50)
            _, faces = det.detect(img)
            for b in (faces if faces is not None else []):
                cx, cy = (b[0] + b[2] / 2) / W, (b[1] + b[3] / 2) / H
                if x0 <= cx <= x1 and y0 <= cy <= y1:
                    return (float(b[0]) / W, float(b[1]) / H, float(b[2]) / W, float(b[3]) / H)
        return None

    def find_facecam(self, tmp: Path, src: list, dur: float) -> dict | None:
        """The streamer's webcam overlay: a face that stays in one place across most of the clip (game faces move).
        Returns the crop for a 16:9 top panel in fractions of the frame, or None."""
        model = HERE / "models" / "face_detection_yunet_2023mar.onnx"
        if not model.exists():
            return None
        import cv2
        n = int(min(40, max(12, dur / 2.5)))             # long clips: more samples (a 170 s clip with 12 missed the cam)
        run_ff(src + ["-vf", f"fps={n / max(dur, 1):.4f},scale=960:-2", "-frames:v", str(n), "cam_%02d.png"], cwd=tmp)
        frames = sorted(tmp.glob("cam_*.png"))
        if not frames:
            return None
        det = None
        hits = []
        for fi, f in enumerate(frames):
            img = cv2.imread(str(f))
            if img is None:
                continue
            H, W = img.shape[:2]
            if det is None:
                det = cv2.FaceDetectorYN_create(str(model), "", (W, H), 0.75, 0.3, 50)
            det.setInputSize((W, H))
            _, faces = det.detect(img)
            for x in (faces if faces is not None else []):
                hits.append((float(x[0]), float(x[1]), float(x[2]), float(x[3]), fi))
        if not hits:
            return None, {}
        cellof = lambda b: (int((b[0] + b[2] / 2) // 48), int((b[1] + b[3] / 2) // 48))  # noqa: E731
        cells = collections.Counter(cellof(b) for b in hits)

        def near_to(c):
            return lambda b: abs(cellof(b)[0] - c[0]) <= 1 and abs(cellof(b)[1] - c[1]) <= 1

        # the webcam = the spot (with its neighbours: the streamer leans and moves) where a face is in most frames
        cell = max(cells, key=lambda c: len({b[4] for b in hits if near_to(c)(b)}))
        near = near_to(cell)
        group = [b for b in hits if near(b)]
        count = len({b[4] for b in group})
        fx, fy, fw, fh = (statistics.median(v[i] for v in group) for i in range(4))
        cx, cy = (fx + fw / 2) / W, (fy + fh / 2) / H
        is_cam = count >= 0.5 * len(frames) and not (0.3 < cx < 0.7 and 0.25 < cy < 0.75)
        # (no face that stays put -> no webcam; a fixed face in the middle is a cutscene, not a webcam)
        # only faces away from the edges steer the gameplay crop: an edge face is usually a webcam we did not confirm
        game = [b for b in hits if not near(b) and 0.2 < (b[0] + b[2] / 2) / W < 0.8]
        frame = {"aspect": W / H}
        if len(game) >= 3:                              # where the people in the game are: the crop follows them
            frame["focus_x"] = round(statistics.median((b[0] + b[2] / 2) / W for b in game), 4)
        if is_cam:                                      # roughly where the whole webcam overlay sits (~7x face width)
            frame["cam_left"], frame["cam_right"] = round(cx - 3.6 * fw / W, 4), round(cx + 3.6 * fw / W, 4)
        if not is_cam:
            return None, frame
        # measured on Kai Cenat: cam box ~7x face width; 6x with the face at 45% reached past the cam into the chat
        # overlay under it, 5.2x with the face at 52% stays inside
        cw_px = min(W, fw * 5.2)
        ch_px = cw_px * 9 / 16
        x0 = min(max(0.0, cx * W - cw_px / 2), W - cw_px)
        y0 = min(max(0.0, cy * H - 0.52 * ch_px), H - ch_px)
        return ({"x": round(x0 / W, 4), "y": round(y0 / H, 4), "w": round(cw_px / W, 4), "h": round(ch_px / H, 4),
                 "face_px_at_960": [round(fx), round(fy), round(fw), round(fh)], "frames_with_face": f"{count}/{len(frames)}"},
                frame)

    @staticmethod
    def crop_left(frame: dict, crop_frac: float) -> float:
        """Left edge (fraction of width) of a crop `crop_frac` wide: centred on the game's people when found,
        otherwise the middle, and never sliding over the webcam overlay."""
        left = frame.get("focus_x", 0.5) - crop_frac / 2
        left = min(max(0.0, left), 1.0 - crop_frac)
        if "cam_right" in frame and frame["cam_left"] < left + crop_frac and frame["cam_right"] > left:
            if frame["cam_right"] < 0.5 and frame["cam_right"] + crop_frac <= 1.0:
                left = frame["cam_right"]
            elif frame["cam_left"] > 0.5 and frame["cam_left"] - crop_frac >= 0.0:
                left = frame["cam_left"] - crop_frac
        return round(min(max(0.0, left), 1.0 - crop_frac), 4)

    def filter_graph(self, fmt: str, ass_name: str | None, kind: str = "fit", cam: dict | None = None,
                     frame: dict | None = None) -> str:
        frame = frame or {}
        aspect = frame.get("aspect", 16 / 9)
        font_opt = ":fontsdir=." if self.font else ""
        subs = f",ass={ass_name}{font_opt}" if ass_name else ""
        if fmt == "vertical" and kind == "stack" and cam:
            # the user's call: gameplay is always the FULL 16:9 desktop frame, never cropped. Webcam 16:9 on top
            # (y 230-838), whole game frame below (y 838-1446), both inside the safe zone, blurred game behind.
            return ("[0:v]split=3[bgs][c][g];"
                    "[bgs]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=8:2,"
                    "scale=1080:1920,eq=brightness=-0.12:saturation=1.1[bg];"
                    f"[c]crop=iw*{cam['w']}:ih*{cam['h']}:iw*{cam['x']}:ih*{cam['y']},scale=1080:608:flags=lanczos,"
                    "unsharp=5:5:0.5[cam];"
                    "[g]scale=1080:608:flags=lanczos[game];"
                    "[bg][cam]overlay=0:230[t1];"
                    f"[t1][game]overlay=0:838{flash(getattr(self, '_fx', []))}{subs}[v]")
        if fmt == "vertical" and kind == "split" and cam:
            # webcam full width on top (1080x608), gameplay CROPPED below to fill the rest (1080x1312)
            return ("[0:v]split=2[c][g];"
                    f"[c]crop=iw*{cam['w']}:ih*{cam['h']}:iw*{cam['x']}:ih*{cam['y']},scale=1080:608:flags=lanczos,"
                    "unsharp=5:5:0.5[cam];"
                    f"[g]crop=ih*1080/1312:ih:iw*{self.crop_left(frame, (1080 / 1312) / aspect)}:0,"
                    "scale=1080:1312:flags=lanczos[game];"
                    f"[cam][game]vstack=inputs=2{subs}[v]")
        if fmt == "vertical" and kind == "fill":
            return (f"[0:v]crop=ih*9/16:ih:iw*{self.crop_left(frame, (9 / 16) / aspect)}:0,"
                    f"scale=1080:1920:flags=lanczos{subs}[v]")
        if fmt == "vertical":
            z = self.cfg.zoom
            crop = f"crop=iw/{z}:ih:(iw-iw/{z})/2:0," if z > 1.0 else ""
            return ("[0:v]split=2[a][b];"
                    "[a]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=8:2,"
                    "scale=1080:1920,eq=brightness=-0.10:saturation=1.15[bg];"
                    f"[b]{crop}scale=1080:-2[fg];"
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2-110{subs}[v]")
        return f"[0:v]scale=-2:1080{subs}[v]"

    def transcribe(self, wav: Path, lang: str | None = None):
        # No VAD: Silero dropped the game characters' lines (Clix 26-38 s), and faster-whisper's VAD stitching put
        # words into the wrong speech chunk, shifting them by the removed silence (Kai: 8 s early).
        # Whisper hears a level-normalised copy: the game characters' lines sit ~15 dB under the streamer and came out
        # empty or under the 0.25 word probability (Clix: 45-66 s of the window). audio.wav stays raw for the cuts.
        asr = wav.with_name("asr.wav")
        run_ff(["-i", wav.name, "-af", "dynaudnorm=f=150:g=15:p=0.9:m=20", "-ar", "16000", "-ac", "1", asr.name], cwd=wav.parent)
        import ctranslate2
        ctranslate2.set_random_seed(0)   # temperature fallback samples: same audio -> same words -> same clip timeline
        segs, info = self.model.transcribe(str(asr), language=lang or self.cfg.language, vad_filter=False,
                                           word_timestamps=True, condition_on_previous_text=False, beam_size=5)
        words, sents = [], []
        for s in segs:
            text = s.text.strip()
            if not text or HALLUCINATIONS.search(text) or (s.no_speech_prob > 0.8 and s.avg_logprob < -0.7):
                continue
            kept = [w for w in (s.words or []) if (w.probability or 0) >= 0.25]
            if not kept:
                continue
            sents.append((s.start, s.end, text))
            for w in kept:
                raw = w.word.strip()
                clean = re.sub(r"[^\w'?!-]", "", raw).upper()
                if clean:
                    words.append({"s": float(w.start), "e": float(w.end),
                                  "w": censor_word(clean) if self.cfg.censor else clean, "raw": raw})
        return words, sents, getattr(info, "language", None)


def dead_air(tmp: Path, src: list) -> float:
    """Seconds of black or frozen picture in the clip (ffmpeg blackdetect + freezedetect at low resolution)."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostats", *src, "-an", "-vf",
                        "scale=320:-2,blackdetect=d=1.5:pix_th=0.10,freezedetect=n=0.003:d=3", "-f", "null", "-"],
                       cwd=tmp, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    black = sum(float(x) for x in re.findall(r"black_duration:([\d.]+)", r.stderr))
    frozen = sum(float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", r.stderr))
    return round(max(black, frozen), 1)


GAME_TAGS = {"grand theft auto vi": ["gta6", "gtavi", "gta"], "grand theft auto v": ["gta5", "gtav", "gta"]}


def post_caption(hook: str | None, channel: str, game: str | None, title: str | None = None, campaign: list | None = None) -> str:
    """Ready-to-paste post text (caption-and-hashtags skill: the point first, credit, relevant tags)."""
    g = (game or "").lower()
    if g not in GAME_TAGS and re.search(r"\bgta ?(6|vi)\b|grand theft auto vi\b", title or "", re.I):
        g = "grand theft auto vi"                   # the VOD's category is often its first one ("Just Chatting")
    tags = GAME_TAGS.get(g, [re.sub(r"[^a-z0-9]", "", g)] if g and g != "just chatting" else [])
    extra = ["gta6clips"] if g == "grand theft auto vi" else []
    campaign = campaign or []
    name = campaign[0] if campaign else channel
    tags = campaign + [channel, f"{channel}clips"] + [t for t in tags if t] + extra + ["twitch", "twitchclips", "streamclips", "gaming"]
    if hook:
        head = hook[0] + hook[1:].lower()
        head = re.sub(r"\b(gta|vi|npc|ai|w|l)\b", lambda m: m.group(0).upper(), head)
    else:
        head = f"{name} GTA 6 moment" if extra else f"{name} moment"
    if name.lower() not in head.lower():           # campaign rule: the caption must mention the streamer's name
        head = f"{name}: {head}"
    return f"{head} \U0001F480\n\n\U0001F3A5 twitch.tv/{channel}\n\n" + " ".join("#" + t for t in dict.fromkeys(tags, None) if t.lower() not in [x.lower() for x in campaign] or t in campaign) + "\n"


def wav_rms(wav: Path, hop: float = 0.1):
    """Loudness in dB per 0.1 s of a 16 kHz mono wav."""
    import wave
    import numpy as np
    with wave.open(str(wav), "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        rate = w.getframerate()
    n = int(rate * hop)
    frames = x[: len(x) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-6)


def picture_motion(tmp: Path, src: list):
    """How much the picture changes, per 0.25 s (mean absolute difference of 160x90 grey frames at 4 fps)."""
    import numpy as np
    r = subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", *src, "-an", "-vf", "fps=4,scale=160:90,format=gray",
                        "-f", "rawvideo", "pipe:1"], cwd=tmp, capture_output=True,
                       creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    n = len(r.stdout) // (160 * 90)
    if n < 2:
        return None
    f = np.frombuffer(r.stdout[: n * 160 * 90], dtype=np.uint8).reshape(n, 90, 160).astype(np.int16)
    return np.concatenate([[0.0], np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))])


def quiet_cuts(words: list, rms, shift: float, dur: float, min_gap: float = 1.6, pad: float = 0.35, motion=None,
               max_cut_share: float = 0.3) -> list:
    """Spans to KEEP. A speech gap longer than min_gap is cut only when nothing happens: game audio quiet
    (8 dB under the speech level) AND the picture nearly still. Found on Lacy: silent chases (dog, alligator) are
    the moment itself and audio alone cut them (39 s -> 16 s). Never cuts more than 30 % of the clip."""
    import numpy as np

    def db(a, b):
        i, j = int((a + shift) * 10), max(int((a + shift) * 10) + 1, int((b + shift) * 10))
        seg = rms[i:j]
        return float(seg.mean()) if len(seg) else -120.0

    speech = [db(w["s"], w["e"]) for w in words]
    level = float(np.median(speech)) if speech else -30.0
    still = None
    if motion is not None and len(motion) > 4:
        typical = float(np.median(motion))

        def still(a, b):                                # the picture barely moves during [a, b]
            seg = motion[int(a * 4): max(int(a * 4) + 1, int(b * 4))]
            return len(seg) > 0 and float(np.median(seg)) < 0.5 * typical
    cuts = []
    edges = [(0.0, words[0]["s"])] + [(words[i]["e"], words[i + 1]["s"]) for i in range(len(words) - 1)] + [(words[-1]["e"], dur)]
    for k, (a, b) in enumerate(edges):
        lead = k == 0
        tail = k == len(edges) - 1
        if b - a < min_gap or db(a, b) > level - 8.0:
            continue
        if still is not None and not still(a, b):
            continue                                    # something is moving on screen: keep it
        ca = a if lead else a + pad                    # leading silence goes entirely, a short breath elsewhere
        cb = b - (0.4 if lead else pad)
        if tail:
            ca, cb = a + 0.8, b                         # keep a beat after the last word
        if cb - ca > 0.3:
            cuts.append((ca, cb))
    budget = max_cut_share * dur                       # longest dead stretches go first, within the 30 % budget
    chosen = []
    for a, b in sorted(cuts, key=lambda c: c[0] - c[1]):
        if budget < 1.0:
            break
        if (b - a) > budget:                            # longer than what is left: cut its middle, keep the edges
            spare = ((b - a) - budget) / 2
            a, b = a + spare, b - spare
        chosen.append((a, b))
        budget -= b - a
    cuts = sorted(chosen)
    keeps, t = [], 0.0
    for a, b in cuts:
        if a > t:
            keeps.append((t, a))
        t = b
    if t < dur:
        keeps.append((t, dur))
    if sum(b - a for a, b in keeps) < 12.0:             # too short after cutting: leave it as it was
        return [(0.0, dur)]
    return keeps


def shout_teaser(words: list, rms, shift: float, keeps: list):
    """Teaser = the streamer's loudest EXCLAIMED line ("I'm God!", "No way!"), not just the loudest sound -
    checked by eye: loudest-sound picked game audio and setup lines on Kai's and Lacy's clips."""
    import numpy as np
    if rms is None or not words:
        return None

    def loud(w):
        i, j = int((w["s"] + shift) * 10), max(int((w["s"] + shift) * 10) + 1, int((w["e"] + shift) * 10))
        seg = rms[i:j]
        return float(seg.max()) if len(seg) else -120.0

    usual = float(np.median([loud(w) for w in words]))
    shouts = [w for w in words if w["raw"].rstrip().endswith("!")]
    if not shouts:
        return None
    best = max(shouts, key=loud)
    if loud(best) < usual + 3.0:                       # an exclamation said quietly is not a hook
        return None
    if (remap_t(keeps, best["s"], True) or 0.0) < 3.0:   # already opens the clip
        return None
    # the line it belongs to: back up to the previous pause (max 1.6 s), end just after the shout
    i = words.index(best)
    a = best["s"]
    while i > 0 and a - words[i - 1]["s"] <= 1.6 and words[i]["s"] - words[i - 1]["e"] < 0.4:
        i -= 1
        a = words[i]["s"]
    return (max(keeps[0][0], a - 0.3), best["e"] + 0.7)


def peak_teaser(rms, shift: float, keeps: list, before: float = 1.2, after: float = 1.0):
    """The loudest 0.5 s of the (cut) clip as a teaser span in uncut clip time - only when it is clearly a peak
    (8 dB over the clip's usual level) and not already in the first 3 s."""
    import numpy as np
    if rms is None or len(rms) < 20:
        return None
    sm = np.convolve(rms, np.ones(5) / 5, mode="same")       # 0.5 s smoothing, 0.1 s steps
    usual = float(np.median(rms))
    best, best_t = None, None
    for a, b in keeps:
        for t in np.arange(a, b, 0.1):
            i = int((t + shift) * 10)
            if 0 <= i < len(sm) and (best is None or sm[i] > best):
                best, best_t = float(sm[i]), float(t)
    if best is None or best < usual + 8.0:
        return None
    first = keeps[0][0]
    if remap_t(keeps, best_t, True) < 3.0:                   # the payoff already opens the clip
        return None
    pa = max(first, best_t - before)
    return (pa, best_t + after)


def remap_t(keeps: list, t: float, clamp: bool = False):
    """Time in the uncut clip -> time in the cut clip (None if it falls inside a cut, unless clamp)."""
    acc = 0.0
    for a, b in keeps:
        if t < a:
            return acc if clamp else None
        if t <= b:
            return acc + (t - a)
        acc += b - a
    return acc if clamp else None


def cut_graph(keeps: list) -> tuple:
    """Filter-graph prefix that keeps only `keeps` of input 0; returns (prefix, video label, audio label)."""
    if len(keeps) <= 1:
        return "", "[0:v]", "[0:a]"
    n = len(keeps)
    parts = ["[0:v]split=%d%s" % (n, "".join(f"[vs{i}]" for i in range(n))),
             "[0:a]asplit=%d%s" % (n, "".join(f"[as{i}]" for i in range(n)))]
    for i, (a, b) in enumerate(keeps):
        parts.append(f"[vs{i}]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[as{i}]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}]")
    parts.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vcut][acut]")
    return ";".join(parts) + ";", "[vcut]", "[acut]"


def virality_score(words, dur, sents, rms, shift, keeps, chat_ratio, viewer_clips, dead) -> dict:
    """0-10, the STREAMER first (user: chat is not the most important): how much he talks, how excited he is,
    loud reactions; then crowd proof (viewer-made clips' views); chat spike last."""
    import numpy as np
    wps = len(words) / max(dur, 1.0)
    text = " ".join(t for _, _, t in sents)
    excl = text.count("!") + text.count("?")
    loud = 0
    if rms is not None and len(rms):
        lvl = float(np.median(rms))
        loud = int((rms > lvl + 9).sum())                 # 0.1 s frames far above the usual level (shouts, bangs)
    views = 0
    for v in viewer_clips:
        m = re.search(r"\((\d+) views\)", v)
        views += int(m.group(1)) if m else 0
    parts = {
        "talk": 3.5 * min(1.0, wps / 2.2),
        "excitement": 2.5 * min(1.0, (excl + loud / 5) / 8),
        "crowd": 2.5 * min(1.0, math.log10(1 + views) / 3.3),
        "chat": 1.0 * min(1.0, max(0.0, (chat_ratio or 0) - 1) / 3),
        "dead_air": -2.0 if dead >= 4 else 0.0,
    }
    return {"score": round(max(0.0, sum(parts.values())), 1), **{k: round(v, 2) for k, v in parts.items()},
            "words_per_s": round(wps, 2), "viewer_views": views}


LAUGH_RE = re.compile(r"\b(ha(ha)+|lol|lmao|laugh|haha)\b", re.I)
SHOCK_RE = re.compile(r"\b(what|wtf|huh|no way|why|who)\b|\?", re.I)


def word_levels(words: list, rms, shift: float) -> list:
    """Loudest 0.1 s rms (dB) inside each word."""
    def loud(w):
        i, j = int((w["s"] + shift) * 10), max(int((w["s"] + shift) * 10) + 1, int((w["e"] + shift) * 10))
        seg = rms[i:j]
        return float(seg.max()) if len(seg) else -120.0
    return [loud(w) for w in words]


def reaction_peaks(words: list, rms, shift: float, most: int = 3, gap: float = 4.5, present=None,
                   pct: float = 75, bar: tuple = (2.0, 4.0), info: dict | None = None) -> list:
    """The streamer's reactions: runs of raised words that stand out from his own talk in THIS clip.
    Loud = over his usual word level by the clip's own top-`pct` % margin, kept within `bar` dB. Measured: Kai's mic
    is compressed, his shouts are only ~4 dB over his talk, so a fixed +6 dB found none; Lacy's shouts are 6+ dB.
    The old shouts-only bar was pct=90, bar=(3, 6); the user wanted hits far more often, so emphasized lines count too.
    Shouted ("!") and longer runs rank first. present(t) -> bool: is the streamer at his webcam then (game dialogue
    is loud too). Returns [(time in uncut clip, emoji)] - at most `most`, `gap` s apart, at the start of the shout."""
    import numpy as np
    if rms is None or not words:
        return []
    lv = word_levels(words, rms, shift)
    usual = float(np.median(lv))
    thr = usual + min(bar[1], max(bar[0], float(np.percentile(lv, pct)) - usual))
    runs, cur = [], []
    for w, lw in zip(words, lv):                       # consecutive raised words (2 dB+), at most 0.35 s apart
        if lw >= usual + 2.0 and cur and w["s"] - cur[-1][0]["e"] <= 0.35:
            cur.append((w, lw))
            continue
        if cur:
            runs.append(cur)
        cur = [(w, lw)] if lw >= usual + 2.0 else []
    if cur:
        runs.append(cur)
    cand = []
    for run in runs:
        peak = max(lw for _, lw in run)
        shout = any(w["raw"].rstrip().endswith("!") for w, _ in run)
        need = thr - (1.5 if shout else 0.0)
        if peak < need:
            continue
        first = next(w for w, lw in run if lw >= need - 1.0)     # where the shout starts, not a quiet lead-in
        length = run[-1][0]["e"] - run[0][0]["s"]
        cand.append((peak + (2.0 if shout else 0.0) + 1.5 * min(length, 1.5), first["s"]))
    out = []
    for _, t in sorted(cand, key=lambda c: -c[0]):
        if len(out) >= most:
            break
        if all(abs(t - u) >= gap for u, _ in out) and (present is None or present(t)):
            near = " ".join(x["raw"] for x in words if abs(x["s"] - t) <= 2.0)
            emo = "sob" if LAUGH_RE.search(near) else "flushed" if SHOCK_RE.search(near) else "skull"
            if info is not None:                       # rank 0 = the biggest reaction; the words around it
                info[t] = {"rank": len(out), "near": near}
            out.append((t, emo))
    return sorted(out)


EMOJI = ("skull", "sob", "flushed", "fire")


def vary_emoji(peaks: list) -> list:
    """No two identical emoji in a row: a repeat becomes the next one in EMOJI that differs from both neighbours."""
    out = []
    for k, (t, emo) in enumerate(peaks):
        prev = out[-1][1] if out else None
        nxt = peaks[k + 1][1] if k + 1 < len(peaks) else None
        if emo == prev:
            i = EMOJI.index(emo) if emo in EMOJI else 0
            emo = next((e for e in EMOJI[i + 1:] + EMOJI[:i] if e not in (prev, nxt)), emo)
        out.append((t, emo))
    return out


EMOJI_PX = 200


def flash(hits: list) -> str:
    """Filter chain piece for the whole 1080x1920 frame, before the captions: a quick white flash (0.15 s)."""
    fl = [(h["t"], 0.32) for h in hits if h.get("visual") == "flash"]
    if not fl:
        return ""
    b = "+".join(f"{a}*if(between(t,{t:.2f},{t + 0.15:.2f}),1-(t-{t:.2f})/0.15,0)" for t, a in fl)
    on = "+".join(f"between(t,{t:.2f},{t + 0.15:.2f})" for t, _ in fl)
    return f",eq=brightness='{b}':eval=frame:enable='{on}'"


def face_in_panel(cam: dict | None, frame: dict | None, box: tuple | None = None) -> tuple | None:
    """The streamer's face (centre x, centre y, width, height) in the 1080x608 webcam panel: `box` (fractions of the
    frame, seen at the peak) or else his usual place from find_facecam."""
    if not cam:
        return None
    hs = 960 / ((frame or {}).get("aspect") or 16 / 9)
    if box:
        fx, fy, fw, fh = box[0] * 960, box[1] * hs, box[2] * 960, box[3] * hs
    elif cam.get("face_px_at_960"):
        fx, fy, fw, fh = cam["face_px_at_960"]
    else:
        return None
    return (((fx + fw / 2) / 960 - cam["x"]) / cam["w"] * 1080, ((fy + fh / 2) / hs - cam["y"]) / cam["h"] * 608,
            fw / 960 / cam["w"] * 1080, fh / hs / cam["h"] * 608)


def emoji_xy(face: tuple | None, size: int = EMOJI_PX) -> tuple:
    """Where the emoji goes (top-left, screen px): beside the face, at eye height, inside
    the webcam panel (y 230-838), never over the face, and ending above the captions (QC bbox top y 808)."""
    if not face:
        return 730, 275
    cx, cy, fw, fh = face
    head = fw * 1.6                                     # face box -> head with hair and headphones
    right, left = cx + head / 2 + 20, cx - head / 2 - 20 - size
    if right + size <= 1064:
        x = right
    elif left >= 16:
        x = left
    else:                                               # face fills the panel: the side with more room
        x = right if 1080 - (cx + head / 2) >= cx - head / 2 else left
    x = min(max(16, x), 1080 - 16 - size)
    y = min(max(16 + 40, cy - 0.2 * fh - size / 2), 565 - size)   # 40 px headroom for the drop-in; 565 = y 795
    return int(x), int(230 + y)


# Burned-in hook title (user 2026-11-19, replaces "no title"): what is about to happen, for the first ~3 s, drawn
# with Pillow so emoji come out in colour (libass cannot do colour emoji).
HOOK_FONT, HOOK_EMOJI = Path(r"C:\Windows\Fonts\impact.ttf"), Path(r"C:\Windows\Fonts\seguiemj.ttf")
HOOK_TOP, HOOK_SIDE, HOOK_END = 60, 60, 3.3      # safe area: not in the top 60 px, 60 px side margins


def hook_title(day_dir: Path, base: str, channel: str) -> str | None:
    """<out_dir>/<base>.hook.txt, else titles.json keyed by the exported mp4 name ("Streamer - situation.mp4")."""
    f = day_dir / f"{base}.hook.txt"
    if f.exists():
        return f.read_text("utf-8").strip() or None
    titles, names = HERE / "titles.json", HERE / "names.json"
    if not (titles.exists() and names.exists()):
        return None
    try:
        import export_clips as ex
        what = json.loads(names.read_text("utf-8")).get(base)
        if not what:
            return None
        label = f"{ex.NAMES.get(channel, channel)} - " + "".join(ch for ch in what if ch not in ex.BAD_CHARS).strip(" .")
        t = json.loads(titles.read_text("utf-8"))
        return (t.get(label + ".mp4") or t.get(label) or "").strip() or None
    except (OSError, ValueError):
        return None


def hook_bottom(kind: str, cam: dict | None, frame: dict | None) -> int:
    """Lowest screen y the title may reach: above the captions and above the streamer's head in the webcam panel."""
    L = dict(LAYOUTS["vertical"], **VERTICAL_TEXT.get(kind, {}))
    bottom = L["mv"] - 20
    face = face_in_panel(cam, frame) if kind == "stack" else None
    if face:
        bottom = min(bottom, int(230 + face[1] - 0.9 * face[3]) - 10)   # face box -> top of the hair
    return max(bottom, 230)                          # the top band (y 60-230) is always free


def _is_emoji(ch: str) -> bool:
    o = ord(ch)
    return o >= 0x1F000 or 0x2600 <= o <= 0x27BF or o in (0xFE0F, 0x200D, 0x2B50)


def hook_png(text: str, out: Path, bottom: int, width: int = 1080 - 2 * HOOK_SIDE) -> int:
    """Draws the title (max 2 lines, Impact 90 -> 58 px until it fits above `bottom`, white, thick black outline,
    colour emoji) into a transparent PNG `width` wide. Returns the screen y to place it at (x = HOOK_SIDE)."""
    from PIL import Image, ImageDraw, ImageFont

    def runs(t):                                     # [(is_emoji, text)] so each run gets its own font
        out_ = []
        for ch in t:
            e = _is_emoji(ch)
            if out_ and out_[-1][0] == e:
                out_[-1][1] += ch
            else:
                out_.append([e, ch])
        return out_

    for size in range(90, 57, -4):
        font = ImageFont.truetype(str(HOOK_FONT), size)
        emo = ImageFont.truetype(str(HOOK_EMOJI), int(size * 0.8))
        stroke = max(6, size // 9)
        meas = lambda t: sum((emo if e else font).getlength(r) for e, r in runs(t)) + 2 * stroke  # noqa: E731
        lines = []
        for w in text.split():
            if lines and meas(lines[-1] + "  " + w) <= width:     # double space: the thick outline eats one
                lines[-1] += "  " + w
            else:
                lines.append(w)
        line_h = int(size * 1.15) + stroke
        h = len(lines) * line_h + stroke
        if len(lines) <= 2 and all(meas(x) <= width for x in lines) and HOOK_TOP + h <= bottom:
            break
    img = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    asc = font.getmetrics()[0]
    for li, line in enumerate(lines):
        x, base_y = (width - meas(line)) / 2 + stroke, stroke + li * line_h + asc
        for e, r in runs(line):
            if e:
                d.text((x, base_y), r, font=emo, embedded_color=True, anchor="ls")
            else:
                d.text((x, base_y), r, font=font, fill="white", stroke_width=stroke, stroke_fill="black", anchor="ls")
            x += (emo if e else font).getlength(r)
    img.save(out)
    # one line: centred in the band above the webcam (y 60-230); two lines: from the top of the safe area
    return max(HOOK_TOP, (HOOK_TOP + 230 - h) // 2) if HOOK_TOP + h <= 230 else HOOK_TOP


OVL_H = 420         # a keyed green-screen cut-out, sat on the bottom corner of the game panel
OVL_BOTTOM = 1470   # game panel is y 838-1446; the cut-out may stand 24 px into the blurred band, inside the safe zone
CUT_LEN = 1.2       # a non-green meme replaces the game panel for this long, then straight back
POP_W, POP_MAXH = 380, 300   # streamer face pop-up: 380 px wide, centred in the blurred band (y 1530-1880) under
POP_TOP, POP_BAND = 1530, 350  # the game and the credit line (y 1460), clear of the webcam and the captions
POP_R, POP_B = 22, 4         # corner radius and white border, px


def rounded(r: int) -> str:
    """geq alpha: opaque inside a W x H rectangle with corners of radius r."""
    return (f"255*lte(hypot(max(0,abs(X-W/2+0.5)-(W/2-{r})),max(0,abs(Y-H/2+0.5)-(H/2-{r}))),{r})")


# The last audio stage, after ALL mixing: at the output rate (loudnorm runs at 192 kHz; resampling after the limiter
# let overs through), -2.5 dB sample ceiling so the AAC encode stays under -1.5 dBTP, and a 5 ms fade-in: the clip
# starts mid-sound and AAC rang that hard onset up to +0.3 dBFS (Kai render, first 10 ms).
FINAL_AUDIO = "aresample=48000,alimiter=limit=0.75:level=disabled,afade=t=in:d=0.005"
VOICE = "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000"


def add_fx(vf: str, ain: str, hits: list, cuts: list, dur: float, tmp: Path, fxdir: Path) -> tuple:
    """The planned hits (memes.plan dicts) on top of the finished picture: emoji pops and meme videos over the frame,
    each hit's own sound (meme sounds levelled in fx/memes/cache) ducked under the voice, and a whoosh on
    every jump cut (pitch varied, so no two are the same). Returns (filter graph, extra ffmpeg inputs).
    Input 0 is the clip; extra inputs start at 1."""
    inputs, n = [], 1

    def add_input(path: Path, name: str, loop: bool = False, pre: tuple = ()) -> int:
        nonlocal n
        shutil.copy2(path, tmp / name)
        inputs.extend(list(pre) + (["-loop", "1", "-t", f"{dur:.2f}"] if loop else []) + ["-i", name])
        n += 1
        return n - 1

    # non-green memes are cutaways: they replace the 1080x608 game panel (y 838) under the captions, so the
    # captions are split off the end of the graph and drawn again on top
    end = vf.rfind("[v]")
    at = vf.rfind(",ass=", 0, end)
    v, subs = (vf[:at], vf[at + 1:end]) if at > 0 else (vf[:end], "null")
    v += "[pre0]"
    cur, k = "[pre0]", 0
    for h in hits:
        ov = h.get("overlay")
        if not ov or ov.get("key") or h.get("popup"):
            continue
        t, ln = h["t"], float(h.get("len") or min(CUT_LEN, float(ov["len"])))
        i = add_input(memes.src(ov), f"cut{k}{memes.src(ov).suffix}", pre=("-ss", f"{ov.get('start', 0)}", "-t", f"{ln:.2f}"))
        v += (f";[{i}:v]scale=1080:608:force_original_aspect_ratio=decrease,pad=1080:608:(ow-iw)/2:(oh-ih)/2:black,"
              f"setsar=1,setpts=PTS-STARTPTS+{t:.2f}/TB[cw{k}];{cur}[cw{k}]overlay=0:838:eof_action=pass:"
              f"enable='between(t,{t:.2f},{t + ln:.2f})'[pre{k + 1}]")
        h["at"] = (0, 838, 1080, 608)
        cur, k = f"[pre{k + 1}]", k + 1
    v += f";{cur}{subs}[vfx0]"
    cur, k = "[vfx0]", 0
    for h in hits:
        t, face = h["t"], h.get("face")
        nxt = f"[vfx{k + 1}]"
        if h.get("emoji"):
            ex, ey = emoji_xy(face)
            i = add_input(fxdir / f"{h['emoji']}.png", f"emo{k}.png", loop=True)
            v += (f";[{i}:v]scale={EMOJI_PX}:-1,format=rgba[em{k}];{cur}[em{k}]overlay=x={ex}:"
                  f"y='{ey}-40*exp(-(t-{t:.2f})*9)':enable='between(t,{t:.2f},{t + 1.3:.2f})'{nxt}")
        elif h.get("popup"):
            ov, ln = h["overlay"], float(h["overlay"]["len"])
            sw, sh = memes.probe_size(memes.src(ov))
            cx, cy, cwf, chf = ov.get("crop") or (0, 0, 1, 1)      # plan crop (fractions) framing the face
            sw, sh = sw * cwf, sh * chf
            pw, ph = POP_W, min(POP_MAXH, int(round(POP_W * sh / sw / 2)) * 2)
            cw, chh = pw + 2 * POP_B, ph + 2 * POP_B
            ox, oy = (1080 - cw) // 2, POP_TOP + (POP_BAND - chh) // 2
            i = add_input(memes.src(ov), f"pop{k}{memes.src(ov).suffix}", pre=("-ss", f"{ov['start']}", "-t", f"{ln:.2f}"))
            fades = f"fade=t=in:st=0:d=0.1:alpha=1,fade=t=out:st={max(0.0, ln - 0.15):.2f}:d=0.15:alpha=1"
            # faces sit in the upper part of a tall source: crop 30 % down from the top
            v += (f";[{i}:v]crop=iw*{cwf}:ih*{chf}:iw*{cx}:ih*{cy},fps=30,scale={pw}:{ph}:force_original_aspect_ratio=increase,crop={pw}:{ph}:(iw-ow)/2:(ih-oh)*0.3,"
                  f"setsar=1,format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='{rounded(POP_R - POP_B)}'[pf{k}];"
                  f"color=c=white:s={cw}x{chh}:r=30:d={ln:.2f},format=rgba,"
                  f"geq=r='255':g='255':b='255':a='{rounded(POP_R)}'[pc{k}];"
                  f"[pc{k}][pf{k}]overlay={POP_B}:{POP_B}:shortest=1,{fades},setpts=PTS-STARTPTS+{t:.2f}/TB[po{k}];"
                  f"{cur}[po{k}]overlay=x={ox}:y={oy}:eof_action=pass:enable='between(t,{t:.2f},{t + ln:.2f})'{nxt}")
            h["at"] = (ox, oy, cw, chh)
        elif h.get("overlay") and h["overlay"].get("key"):
            # green screen: keyed (cache), ~420 px tall, bottom corner of the game panel, on the side away from
            # the action ("side" in the plan, else right), like a reaction-person dropped in the corner
            ov = h["overlay"]
            mov = memes.cached(ov, "mov")
            sw, sh = memes.probe_size(mov)
            if ov.get("text"):                  # a text card: centred on the game panel, 900 px wide
                ow, oh = 900, int(round(900 * sh / sw / 2)) * 2
                ox, oy = (1080 - ow) // 2, 838 + (608 - oh) // 2
            else:
                oh = OVL_H
                ow = int(round(sw / sh * oh / 2)) * 2
                if ow > 1080:
                    ow, oh = 1080, int(round(1080 * sh / sw / 2)) * 2
                ox, oy = (0 if h.get("side") == "left" else 1080 - ow), OVL_BOTTOM - oh
            i = add_input(mov, f"meme{k}.mov")
            ln = float(h.get("len") or ov["len"])
            v += (f";[{i}:v]scale={ow}:{oh},fade=t=in:st=0:d=0.12:alpha=1,setpts=PTS-STARTPTS+{t:.2f}/TB[ov{k}];"
                  f"{cur}[ov{k}]overlay=x={ox}:y={oy}:eof_action=pass:enable='between(t,{t:.2f},{t + ln:.2f})'{nxt}")
            h["at"] = (ox, oy, ow, oh)
        else:
            continue
        cur, k = nxt, k + 1
    v += f";{cur}null[v]"

    hit_sfx, other = [], []
    for j, h in enumerate(hits):
        snd = h.get("sound")
        if not snd or (h["kind"] == "filler" and any(abs(h["t"] - c) <= 0.4 for c in cuts)):
            continue        # a filler beat right on a jump cut already gets that cut's whoosh
        i = add_input(memes.cached(snd, "wav"), f"snd{j}.wav")
        vol = 0.3 if h["kind"] == "filler" else 0.5          # the meme bed sits 6 dB lower (user: "too loud")
        v += f";[{i}:a]adelay={int(h['t'] * 1000)}:all=1,volume={vol}[sx{j}]"
        hit_sfx.append(f"[sx{j}]")
    cs = cuts[:20]
    if cs:
        i = add_input(fxdir / "whoosh.wav", "whoosh.wav")
        v += f";[{i}:a]asplit={len(cs)}" + "".join(f"[wo{q}]" for q in range(len(cs)))
        for q, t in enumerate(cs):
            rate = (0.85, 1.0, 1.18, 0.92, 1.1)[q % 5]
            # whoosh.wav (0.5 s) swells to its peak at ~0.42 s: it lands on the cut
            v += (f";[wo{q}]asetrate={int(48000 * rate)},aresample=48000,"
                  f"adelay={int(max(0.0, t - 0.42 / rate) * 1000)}:all=1,volume=0.35[wd{q}]")
            other.append(f"[wd{q}]")
    # both on the sample clock (the VOD's concat audio carries its own timestamps, which broke timestamp sync before)
    v += f";{ain}{VOICE},asetpts=N/SR/TB" + ("[an]" if not hit_sfx else ",asplit=2[an][key]")
    if hit_sfx:
        # meme sounds UNDER speech (user: "too loud when other people are talking"): the stream audio (streamer and
        # game voices) keys a compressor on the meme bus, ~8 dB further down while anyone talks
        bus = hit_sfx[0] if len(hit_sfx) == 1 else "[bus]"
        if len(hit_sfx) > 1:
            v += f";{''.join(hit_sfx)}amix=inputs={len(hit_sfx)}:normalize=0:duration=longest[bus]"
        v += f";{bus}asetpts=N/SR/TB[busn];[busn][key]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=250[mduck]"
        other = ["[mduck]"] + other
    if other:
        v += f";[an]{''.join(other)}amix=inputs={1 + len(other)}:normalize=0:duration=first,{FINAL_AUDIO}[aout]"
    else:
        v += f";[an]{FINAL_AUDIO}[aout]"
    return v, inputs


def sentence_start(sents: list, target: float, lo: float, hi: float) -> float:
    """A start in [lo, hi] that begins a sentence, the one closest to `target`; else `target`."""
    starts = [a for a, _, _ in sents if lo <= a <= hi]
    if starts:
        return min(starts, key=lambda a: abs(a - target)) - 0.25
    inside = [(a, b) for a, b, _ in sents if a < target < b]
    if inside and inside[0][0] >= lo:          # target falls mid-sentence: back up to where that sentence starts
        return inside[0][0] - 0.25
    return target


def sentence_end(sents: list, target: float) -> float:
    """The end of the sentence running at `target` (or the next one ending within 8 s); else `target`."""
    ends = [b for a, b, _ in sents if target - 1.0 <= b <= target + 8.0]
    return (min(ends) + 0.6) if ends else target


def write_srt(path: Path, sents):
    out = []
    for i, (s, e, t) in enumerate(sents, 1):
        out.append(f"{i}\n{srt_time(s)} --> {srt_time(e)}\n{t}\n")
    path.write_text("\n".join(out), "utf-8")


def run_ff(args: list[str], cwd: Path):
    # own process group on Windows, so Ctrl+C (meant to stop recording) doesn't kill a clip mid-render
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    r = subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *args], cwd=cwd, creationflags=flags,
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({r.returncode}): {r.stderr.strip()[-1500:]}")


# --------------------------------------------------------------------------- per-channel watcher


class ChannelWatcher(threading.Thread):
    def __init__(self, channel: str, cfg: Config, factory: ClipFactory, stop: threading.Event, auto_mode=False):
        super().__init__(daemon=True, name=f"watch-{channel}")
        self.channel, self.cfg, self.factory, self.stop, self.auto = channel, cfg, factory, stop, auto_mode
        self.clips_made = 0
        self.error: str | None = None

    def run(self):
        announced_offline = 0.0
        while not self.stop.is_set():
            try:
                info = stream_info(self.channel)
            except ValueError as e:
                self.error = str(e)
                log(self.channel, f"stopping: {e}")
                return
            except Exception as e:  # noqa: BLE001
                log(self.channel, f"live check failed ({e}); retrying in {self.cfg.poll}s")
                self.stop.wait(self.cfg.poll)
                continue
            if not info:
                if self.auto:
                    log(self.channel, "offline; auto mode releases this slot")
                    return
                if time.time() - announced_offline > 600:
                    log(self.channel, f"offline, checking again every {self.cfg.poll}s")
                    announced_offline = time.time()
                self.stop.wait(self.cfg.poll)
                continue
            announced_offline = 0.0
            try:
                self.session(info)
            except Exception:  # noqa: BLE001
                log(self.channel, "session crashed:\n" + traceback.format_exc())
                self.stop.wait(10)
            if self.auto:
                return

    def session(self, info: dict):
        cfg = self.cfg
        sess_dir = cfg.work / self.channel / f"{dt.datetime.now():%Y%m%d-%H%M%S}"
        sess_dir.mkdir(parents=True, exist_ok=True)
        game = (info.get("game") or {}).get("name")
        log(self.channel, f"LIVE: \"{info.get('title', '')}\" ({game}, {info.get('viewersCount')} viewers) - recording to {sess_dir}")
        det = SpikeDetector(cfg)
        sess_stop = threading.Event()
        chat_file = open(sess_dir / "chat.jsonl", "a", encoding="utf-8")
        chat_lock = threading.Lock()
        n_msgs = [0]

        def on_msg(t, user, text):
            det.add(t, user, text)
            with chat_lock:
                n_msgs[0] += 1
                chat_file.write(json.dumps({"t": round(t, 3), "u": user, "m": text}, ensure_ascii=False) + "\n")

        chat = ChatReader(self.channel, on_msg, sess_stop)
        chat.start()
        rec = Recorder(self.channel, sess_dir, cfg)
        rec.start()
        session_started = time.time()
        pending: list[ClipJob] = []
        recent_clip_times: collections.deque = collections.deque()
        last_stats, msgs_at_stats = time.time(), 0
        quick_fails = 0
        open_jobs = [0]
        jobs_lock = threading.Lock()

        def job_done():
            with jobs_lock:
                open_jobs[0] -= 1

        try:
            while not self.stop.is_set():
                now = time.time()
                for sp in det.tick(now):
                    cur_game = (info.get("game") or {}).get("name")
                    if cfg.only_game and cur_game != cfg.only_game:
                        log(self.channel, f"spike x{sp.ratio:.1f} ignored: playing {cur_game}, not {cfg.only_game}")
                        continue
                    while recent_clip_times and recent_clip_times[0] < now - 3600:
                        recent_clip_times.popleft()
                    if len(recent_clip_times) >= cfg.max_clips_per_hour:
                        log(self.channel, f"spike x{sp.ratio:.1f} ignored: hit --max-clips-per-hour {cfg.max_clips_per_hour}")
                        continue
                    recent_clip_times.append(now)
                    job = ClipJob(self.channel, sp, sp.onset - WIDE_PRE, sp.onset + cfg.post + WIDE_POST, info, sess_dir)
                    job.react_end = sp.onset + cfg.post
                    pending.append(job)
                    log(self.channel, f"SPIKE chat {sp.score:.0f} vs baseline {sp.baseline:.0f} (x{sp.ratio:.1f}) "
                                      f"at {dt.datetime.fromtimestamp(sp.onset):%H:%M:%S} - clip queued")
                segs = rec.segments()
                newest = segs[-1].wall_end if segs else 0
                for job in pending:                         # chat still going -> the clip keeps going (up to MAX_REACT)
                    if (now >= job.react_end + 1 and job.react_end < job.spike.onset + MAX_REACT
                            and hot(det.per_sec, job.react_end - 3, job.react_end, react_level(job.spike))):
                        job.react_end += 4
                        job.end = job.react_end + WIDE_POST
                for job in [j for j in pending if newest >= j.end]:
                    self._submit(job, segs, open_jobs, jobs_lock, job_done)
                    pending.remove(job)
                self._janitor(segs, pending, now)

                if not rec.alive():
                    ran = time.time() - rec.started_at
                    tail = rec.log_tail()
                    try:
                        again = stream_info(self.channel)
                    except Exception:  # noqa: BLE001
                        again = info
                    if again and not self.stop.is_set():
                        quick_fails = quick_fails + 1 if ran < 60 else 0
                        if quick_fails >= 3:
                            log(self.channel, f"recorder keeps failing, pausing 5 min. streamlink said: {tail}")
                            self.stop.wait(300)
                            quick_fails = 0
                        else:
                            log(self.channel, f"recorder stopped after {ran:.0f}s while still live; restarting. ({tail[-200:]})")
                        info = again
                        rec.start()
                        continue
                    log(self.channel, "stream ended")
                    break

                if now - last_stats >= 60:
                    try:                                    # category can change mid-stream (Just Chatting, other games)
                        fresh = stream_info(self.channel)
                        if fresh:
                            info = fresh
                    except Exception:  # noqa: BLE001
                        pass
                    with chat_lock:
                        n = n_msgs[0]
                        chat_file.flush()
                    rate = (n - msgs_at_stats) / (now - last_stats)
                    last_stats, msgs_at_stats = now, n
                    buf = sum(s.path.stat().st_size for s in segs if s.path.exists()) / 1e9
                    L = det.last
                    base = f"{L['baseline']:.0f}" if L["baseline"] is not None else "warming up"
                    thr = f"{L['threshold']:.0f}" if L["threshold"] is not None else "-"
                    log(self.channel, f"rec {fmt_dur(now - session_started)} | buffer {buf:.2f} GB | chat {rate:.1f} msg/s | "
                                      f"window {L['score']:.0f} baseline {base} spike>={thr} | clips {self.clips_made} "
                                      f"({len(pending)} waiting, {self.factory.pending()} rendering)")
                self.stop.wait(0.5)
        finally:
            rec.stop()
            sess_stop.set()
            segs = rec.segments()
            for job in pending:
                if segs and segs[-1].wall_end > job.start + 3:
                    self._submit(job, segs, open_jobs, jobs_lock, job_done)
            with chat_lock:
                chat_file.close()
            if cfg.buffer_minutes > 0:
                # not a daemon: on shutdown Python must wait for it, or the leftover buffer stays on disk
                threading.Thread(target=self._final_cleanup, args=(sess_dir, open_jobs, jobs_lock), daemon=False).start()

    def _submit(self, job, segs, open_jobs, jobs_lock, job_done):
        job.segments = [s for s in segs if s.wall_end > job.start and s.wall_start < job.end]
        job.on_done = job_done
        with jobs_lock:
            open_jobs[0] += 1
        self.clips_made += 1
        self.factory.submit(job)

    def _janitor(self, segs, pending, now):
        if self.cfg.buffer_minutes <= 0 or not segs:
            return
        keep_from = now - self.cfg.buffer_minutes * 60
        if pending:
            keep_from = min(keep_from, min(j.start for j in pending) - 15)
        for s in segs[:-2]:
            if s.wall_end < keep_from and not self.factory.is_locked(s.path):
                try:
                    s.path.unlink()
                except OSError:
                    pass

    def _final_cleanup(self, sess_dir: Path, open_jobs, jobs_lock):
        """Buffer mode: once this session's clips are rendered, the leftover recording buffer is deleted."""
        for _ in range(3600):
            with jobs_lock:
                if open_jobs[0] <= 0:
                    break
            time.sleep(1)
        removed = 0
        for f in sess_dir.glob("p*_seg_*.ts"):
            if not self.factory.is_locked(f):
                try:
                    f.unlink()
                    removed += 1
                except OSError:
                    pass
        log(self.channel, f"session finished; cleared {removed} buffer segments (chat log kept in {sess_dir})")


def fmt_dur(s: float) -> str:
    s = int(s)
    return f"{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}"


# --------------------------------------------------------------------------- auto mode


def director(cfg: Config, factory: ClipFactory, stop: threading.Event, watchers: dict):
    while not stop.is_set():
        try:
            ranked = top_streams(cfg.game, cfg.top, cfg.lang)
            for name in list(watchers):
                if not watchers[name].is_alive():
                    del watchers[name]
            for login in ranked:
                if len(watchers) >= cfg.top:
                    break
                if login not in watchers:
                    w = ChannelWatcher(login, cfg, factory, stop, auto_mode=True)
                    watchers[login] = w
                    w.start()
            log("auto", f"top {cfg.game} streams{' (' + cfg.lang + ')' if cfg.lang else ''}: {', '.join(ranked[:cfg.top + 3])} "
                        f"| watching: {', '.join(watchers)}")
        except Exception as e:  # noqa: BLE001
            log("auto", f"could not list streams ({e}); retrying")
        stop.wait(cfg.rescan)


# --------------------------------------------------------------------------- past streams (--vod)

# Chat is typed by viewers who watch ~2-4 s behind the broadcaster (measured on Twitch: the newest HLS segment
# was 2.2-3.5 s old), while VOD segments are stamped with the broadcaster's clock. Shift chat back by this much.
VOD_CHAT_LAG = 3.0

COMMENTS_Q = ("query($id:ID!,$off:Int){ video(id:$id){ comments(contentOffsetSeconds:$off){ edges{ node{ id "
              "contentOffsetSeconds createdAt commenter{login} message{fragments{text}} } } } } }")


def iso_epoch(s: str) -> float:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def resolve_vod(arg: str) -> dict:
    arg = arg.strip().rstrip("/")
    m = re.search(r"(?:videos/)?(\d{6,})(?:\?.*)?$", arg)
    if m:
        vid = m.group(1)
    else:
        login = arg.split("/")[-1].lower()
        d = gql("query($l:String!){ user(login:$l){ videos(first:1, type:ARCHIVE){ edges{ node{ id } } } } }", {"l": login})
        if not d.get("user"):
            raise SystemExit(f"Twitch channel '{login}' does not exist")
        edges = d["user"]["videos"]["edges"]
        if not edges:
            raise SystemExit(f"{login} has no saved broadcasts (VODs are turned off, sub-only or deleted)")
        vid = edges[0]["node"]["id"]
    v = gql("query($id:ID!){ video(id:$id){ id title lengthSeconds createdAt status owner{login} game{name} } }",
            {"id": vid}).get("video")
    if not v:
        raise SystemExit(f"video {vid} not found (deleted or sub-only)")
    return v


def vod_segments(video_id: str, quality: str, created_at: str | None = None) -> list[dict]:
    """The VOD's HLS segments with broadcaster wall-clock start times (#EXT-X-PROGRAM-DATE-TIME; when a playlist has
    none - found on recrent/buster/evelone - the broadcast's start time + elapsed). Fragmented-MP4 VODs carry an
    #EXT-X-MAP init segment that every piece needs (without it: "no tfhd was found")."""
    r = subprocess.run(streamlink_cmd() + ["--stream-url", f"https://www.twitch.tv/videos/{video_id}", quality],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    url = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    if not url.startswith("http"):
        raise SystemExit(f"could not open VOD {video_id}: {(r.stdout + r.stderr).strip()[-300:]}")
    with urllib.request.urlopen(url, timeout=30) as resp:
        text = resp.read().decode("utf-8", "replace")
    from urllib.parse import urljoin
    segs, pdt, dur, elapsed, init = [], None, 10.0, 0.0, None
    base_epoch = iso_epoch(created_at) if created_at else 0.0
    for line in text.splitlines():
        if line.startswith("#EXT-X-MAP:"):
            m = re.search(r'URI="([^"]+)"', line)
            init = urljoin(url, m.group(1)) if m else None
        elif line.startswith("#EXT-X-PROGRAM-DATE-TIME:"):
            pdt = iso_epoch(line.split(":", 1)[1].strip())
        elif line.startswith("#EXTINF:"):
            dur = float(line[8:].split(",")[0])
        elif line and not line.startswith("#"):
            start = pdt if pdt is not None else (segs[-1]["start"] + segs[-1]["dur"] if segs else base_epoch)
            segs.append({"url": urljoin(url, line), "start": start, "dur": dur, "elapsed": elapsed, "muted": "muted" in line,
                         "init": init})
            elapsed += dur
            pdt = None
    if not segs:
        raise SystemExit("the VOD playlist is empty")
    return segs


def vod_chapters(video_id: str) -> list[tuple]:
    """[(start_s, end_s, game)] from the VOD's chapter markers; the last chapter runs to the end."""
    try:
        d = gql("query($id:ID!){ video(id:$id){ moments(momentRequestType: VIDEO_CHAPTER_MARKERS, first: 100){ edges{ node{"
                " positionMilliseconds durationMilliseconds details{ ... on GameChangeMomentDetails{ game{ name } } } } } } } }",
                {"id": video_id})
    except Exception as e:  # noqa: BLE001
        log("vod", f"chapter markers unavailable ({e})")
        return []
    out = []
    for e in ((d.get("video") or {}).get("moments") or {}).get("edges") or []:
        n = e["node"]
        start = n["positionMilliseconds"] / 1000
        dur = n["durationMilliseconds"] / 1000
        game = ((n.get("details") or {}).get("game") or {}).get("name")
        out.append((start, start + dur if dur > 0 else float("inf"), game))
    return out


def game_at(chapters: list[tuple], offset: float) -> str | None:
    for start, end, game in chapters:
        if start <= offset < end:
            return game
    return None if chapters else "unknown"


def elapsed_to_epoch(segs: list[dict], offset: float) -> float:
    for s in segs:
        if s["elapsed"] <= offset < s["elapsed"] + s["dur"]:
            return s["start"] + (offset - s["elapsed"])
    return segs[-1]["start"] + (offset - segs[-1]["elapsed"])


def fetch_vod_chat(video: dict, path: Path, workers: int = 6) -> list[tuple]:
    """Chat replay of a VOD by stepping through it by offset (no login). Each request returns ~50 messages.
    Cached in `path`; for a VOD that is still recording, later runs only fetch the new part."""
    length = int(video["lengthSeconds"])
    meta_path = path.with_suffix(".meta.json")
    seen: dict[str, tuple] = {}
    start_at = 0
    if path.exists() and meta_path.exists():
        for line in path.read_text("utf-8").splitlines():
            d = json.loads(line)
            seen[d["id"]] = (d["t"], d["u"], d["m"])
        start_at = max(0, json.loads(meta_path.read_text())["covered"] - 30)
    if start_at >= length - 10:
        log("vod", f"chat replay cached ({len(seen)} messages)")
        return sorted(seen.values())
    lock = threading.Lock()
    done = [0]
    total = length - start_at
    bounds = [start_at + total * i // workers for i in range(workers + 1)]

    def work(a: int, b: int):
        off, fails = a, 0
        while off < b:
            try:
                edges = gql(COMMENTS_Q, {"id": video["id"], "off": off}, timeout=20)["video"]["comments"]["edges"]
                fails = 0
            except Exception:  # noqa: BLE001
                fails += 1
                time.sleep(min(2 * fails, 10))
                if fails >= 6:
                    off, fails = off + 5, 0
                continue
            if not edges:
                step = 10
            else:
                last = max(e["node"]["contentOffsetSeconds"] for e in edges)
                step = max(1, last + 1 - off)
                with lock:
                    for e in edges:
                        n = e["node"]
                        if n["id"] in seen or not n.get("commenter"):
                            continue
                        text = "".join(f.get("text") or "" for f in n["message"]["fragments"])
                        seen[n["id"]] = (iso_epoch(n["createdAt"]), n["commenter"]["login"], text)
            off += step
            with lock:
                before = done[0] * 10 // total
                done[0] += step
                if done[0] * 10 // total > before:
                    log("vod", f"chat replay {min(100, done[0] * 100 // total)}% ({len(seen)} messages)")

    threads = [threading.Thread(target=work, args=(bounds[i], bounds[i + 1]), daemon=True) for i in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for k, (t, u, m) in seen.items():
            f.write(json.dumps({"id": k, "t": round(t, 3), "u": u, "m": m}, ensure_ascii=False) + "\n")
    meta_path.write_text(json.dumps({"covered": length}))
    return sorted(seen.values())


CLIP_PERIOD = "LAST_WEEK"   # --clip-period LAST_DAY for fresh-only pulls


def fetch_viewer_clips(login: str, video_id: str) -> list[dict]:
    """Clips viewers made of this broadcast (top 100 by views of the past week)."""
    d = None
    for attempt in range(4):                           # Twitch answers "service error" now and then
        try:
            d = gql("query($l:String!){ user(login:$l){ clips(first:100, criteria:{period:%s, sort:VIEWS_DESC}){ "
                    "edges{ node{ slug title viewCount durationSeconds videoOffsetSeconds video{id} } } } } }" % CLIP_PERIOD, {"l": login})
            break
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                log("vod", f"WARNING: viewer clips unavailable after 4 tries ({e}); ranking by chat only")
                return []
            time.sleep(3 * (attempt + 1))
    out = []
    for e in d["user"]["clips"]["edges"]:
        n = e["node"]
        if n.get("video") and n["video"]["id"] == video_id and n.get("videoOffsetSeconds") is not None:
            out.append(n)
    return out


def fetch_url(url: str) -> bytes:
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2)
    return b""


def download_window(segs: list[dict], a: float, b: float, dest: Path) -> list[Segment]:
    dest.mkdir(parents=True, exist_ok=True)
    wanted = [s for s in segs if s["start"] + s["dur"] > a and s["start"] < b]
    if wanted and wanted[0].get("init"):
        # fragmented-MP4 VOD: fragments keep the stream's absolute timestamps (a 10 s piece probes as 1072 s), so
        # init + all fragments in order go into ONE continuous file for this window
        p = dest / f"vod_{int(wanted[0]['elapsed']):07d}-{int(wanted[-1]['elapsed']):07d}.mp4"
        if not p.exists():
            tmp = p.with_suffix(".part")
            with open(tmp, "wb") as f:
                f.write(fetch_url(wanted[0]["init"]))
                for s in wanted:
                    f.write(fetch_url(s["url"]))
            tmp.replace(p)
        start, end = wanted[0]["start"], wanted[-1]["start"] + wanted[-1]["dur"]
        return [Segment(p, start, end, end - start)]
    out = []
    for s in wanted:
        p = dest / f"vod_{int(s['elapsed']):07d}.ts"
        if not p.exists():
            tmp = p.with_suffix(".part")
            tmp.write_bytes(fetch_url(s["url"]))
            tmp.replace(p)
        out.append(Segment(p, s["start"], s["start"] + s["dur"], s["dur"]))
    return out


def parse_offset(s: str) -> float:
    s = s.strip().lower()
    if ":" in s:
        parts = [float(p) for p in s.split(":")]
        return sum(p * 60 ** i for i, p in enumerate(reversed(parts)))
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s?)?", s)
    if not m or not s:
        raise SystemExit(f"cannot read time '{s}' (use 6h10m30s or 6:10:30)")
    return int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + float(m.group(3) or 0)


def parse_range(r: str, length: float) -> tuple[float, float]:
    a, _, b = r.partition("-")
    start = parse_offset(a)
    end = length - 1 if b.strip().lower() in ("", "end") else parse_offset(b)
    end = min(end, length - 1)
    if end - start < 3:
        raise SystemExit(f"range {r} is empty or past the end of the VOD ({fmt_offset(length)})")
    return start, end


def fmt_offset(sec: float) -> str:
    sec = int(max(0, sec))
    return f"{sec // 3600}h{sec // 60 % 60:02d}m{sec % 60:02d}s"


def vod_mode(cfg: Config, args):
    video = resolve_vod(args.vod)
    login, vid = video["owner"]["login"], video["id"]
    sess = cfg.work / login / f"vod_{vid}"
    sess.mkdir(parents=True, exist_ok=True)
    log("vod", f"{login}: \"{video['title']}\" - {int(video['lengthSeconds']) / 3600:.1f} h "
               f"({'still live' if video.get('status') == 'RECORDING' else 'finished'})")
    factory = ClipFactory(cfg)
    factory.start()                                    # loads whisper while chat downloads
    segs = vod_segments(vid, cfg.quality, video.get("createdAt"))
    t0 = time.time()
    if args.crowd or args.range:
        chat = []                                      # crowd mode picks by viewer clips: no chat replay needed
    else:
        chat = fetch_vod_chat(video, sess / "chat.jsonl")
        log("vod", f"chat replay: {len(chat)} messages in {time.time() - t0:.0f}s")
    chat = [(t - VOD_CHAT_LAG, u, m) for t, u, m in chat]
    vod_start = segs[0]["start"]
    vod_end = segs[-1]["start"] + segs[-1]["dur"]
    if args.range:
        a_off, b_off = parse_range(args.range, segs[-1]["elapsed"] + segs[-1]["dur"])
        a_ep, b_ep = elapsed_to_epoch(segs, a_off), elapsed_to_epoch(segs, b_off)
        sample = [(round(t, 1), u, m) for t, u, m in chat if a_ep <= t <= b_ep][:400]
        sp = Spike(onset=a_ep, bucket_start=a_ep, score=0.0, baseline=0.0, threshold=0.0, ratio=0.0, sample=sample)
        log(login, f"range clip {fmt_offset(a_off)} - {fmt_offset(b_off)} ({b_off - a_off:.0f}s)")
        job = ClipJob(login, sp, a_ep, b_ep, {"title": video["title"], "game": video.get("game")}, sess)
        job.extra["fixed"] = True                      # a hand-picked range is cut exactly as asked
        job.segments = download_window(segs, a_ep, b_ep, sess / "vod_segments")
        job.extra |= {"found_by": "manual range", "stream_time": fmt_offset(a_off),
                     "vod_url": f"https://www.twitch.tv/videos/{vid}?t={fmt_offset(a_off)}"}
        factory.submit(job)
        factory.q.join()
        log("vod", f"done - {factory.done_count} clip in {cfg.out / login}")
        return

    det = SpikeDetector(cfg)
    spikes = []
    for t, u, m in chat:
        spikes += det.tick(t)
        det.add(t, u, m)
    if chat:
        spikes += det.tick(chat[-1][0] + 2 * cfg.bucket)
    series = det.series

    def chat_at(moment):
        """Best chat ratio in the reaction window after `moment`, plus the baseline it is measured against."""
        best = (0.0, 0.0, 1.0)
        for start, score, med in series:
            if moment - 5 <= start <= moment + 20:
                r = score / max(med, 1.0)
                if r > best[0]:
                    best = (r, score, med)
        return best

    cands = [{"onset": sp.onset, "spike": sp, "viewer": []} for sp in spikes]
    viewer = fetch_viewer_clips(login, vid)
    if args.crowd:                                     # independent review: viewer clips were the only reliable signal
        viewer = [v for v in viewer if v["viewCount"] >= args.min_views]
    for vc in viewer:
        vstart = elapsed_to_epoch(segs, vc["videoOffsetSeconds"])
        end = elapsed_to_epoch(segs, vc["videoOffsetSeconds"] + vc["durationSeconds"])
        moment = vstart + cfg.pre if args.crowd else end - 10.0   # crowd: the viewer's own start is the clip start
        near = [c for c in cands if abs(c["onset"] - moment) <= cfg.pre + cfg.post]
        if near:
            best = min(near, key=lambda c: abs(c["onset"] - moment))
            best["viewer"].append(vc)
            best["vend"] = max(best.get("vend") or 0, end)
        else:
            cands.append({"onset": moment, "spike": None, "viewer": [vc], "vend": end})
    for c in cands:
        ratio = c["spike"].ratio if c["spike"] else chat_at(c["onset"])[0]
        views = sum(v["viewCount"] for v in c["viewer"])
        c["ratio"], c["views"] = ratio, views
        c["score"] = ratio + 0.6 * math.log10(1 + views) + 0.3 * len(c["viewer"])
    cands = [c for c in cands if vod_start + cfg.pre <= c["onset"] <= vod_end - cfg.post]
    if cfg.only_game:                                  # Twitch chapter markers say when each game was played
        chapters = vod_chapters(vid)
        if chapters:
            before = len(cands)
            cands = [c for c in cands if game_at(chapters, c["onset"] - vod_start) == cfg.only_game]
            log("vod", f"{before - len(cands)} moments dropped: not during {cfg.only_game}")
        else:
            # no chapters: the VOD's own category decides (found on evelone2004: an old Just Chatting VOD with no
            # chapters let 3 non-GTA clips through)
            vgame = (video.get("game") or {}).get("name")
            if vgame != cfg.only_game:
                log("vod", f"skipped: this VOD has no chapter markers and its category is {vgame}, not {cfg.only_game}")
                cands = []
    cands.sort(key=lambda c: c["score"], reverse=True)
    picked = []
    for c in cands:                                    # best first; spares in case some turn out to be dead air
        if len(picked) >= args.best * 2:
            break
        if all(abs(c["onset"] - p["onset"]) >= 90 for p in picked):   # critic: picks 55 s apart were one moment
            picked.append(c)
    log("vod", f"{len(spikes)} chat spikes + {len(viewer)} viewer clips -> {len(cands)} moments; rendering the best {args.best}")

    chat_per_sec = collections.Counter()
    for t, u, m in chat:
        chat_per_sec[int(t)] += chat_weight(m)
    rank = 0
    for c in picked:
        if rank >= args.best:
            break
        onset = c["onset"]
        sp = c["spike"]
        if sp is None:
            ratio, score, med = chat_at(onset)
            sample = [(round(t, 1), u, m) for t, u, m in chat if onset - 3 <= t <= onset + 15][:40]
            sp = Spike(onset=onset, bucket_start=onset, score=score, baseline=med, threshold=0.0, ratio=ratio, sample=sample)
        source = " + ".join(x for x, ok in (("chat spike", c["spike"] is not None), ("viewer clips", bool(c["viewer"]))) if ok)
        off = onset - vod_start
        react_end = onset + cfg.post                   # follow the reaction while chat stays hot
        while react_end < onset + MAX_REACT and hot(chat_per_sec, react_end - 3, react_end, react_level(sp)):
            react_end += 4
        if args.crowd and c.get("vend"):
            react_end = min(c["vend"] + 2.0, onset - cfg.pre + 60.0)   # the viewer own end, 1 minute at most
        when = dt.datetime.fromtimestamp(onset)
        made = cfg.out / login / f"{when:%Y-%m-%d}" / f"{login}_{when:%H%M%S}_x{sp.ratio:.1f}.json"
        if made.exists():                              # already rendered on an earlier run: keep it, don't redo
            rank += 1
            log(login, f"#{rank} at {fmt_offset(off)} already made, skipped")
            continue
        job = ClipJob(login, sp, onset - WIDE_PRE, react_end + WIDE_POST,
                      {"title": video["title"], "game": video.get("game")}, sess)
        job.react_end = react_end
        try:
            job.segments = download_window(segs, job.start, job.end, sess / "vod_segments")
        except OSError as e:
            log(login, f"moment at {fmt_offset(off)} skipped: could not download its video ({e})")
            continue
        # critic: one pick ended in 9 s of black loading screen, one opened on a frozen menu -> take the next one
        listing = "".join("file '" + str(sg.path).replace("\\", "/") + "'\n" for sg in job.segments)
        (sess / "check_list.txt").write_text(listing, "utf-8")
        dead = dead_air(sess, ["-ss", f"{max(0.0, onset - cfg.pre - job.segments[0].wall_start):.2f}",
                               "-t", f"{react_end - onset + cfg.pre:.2f}", "-f", "concat", "-safe", "0", "-i", "check_list.txt"])
        if dead >= 4:
            log(login, f"moment at {fmt_offset(off)} skipped: {dead:.0f}s of black or frozen picture")
            continue
        rank += 1
        log(login, f"#{rank} at {fmt_offset(off)} into the stream: {source}, chat x{c['ratio']:.1f}, "
                   f"{len(c['viewer'])} viewer clips / {c['views']} views")
        job.extra = {"rank": rank, "found_by": source, "stream_time": fmt_offset(off),
                     "vod_url": f"https://www.twitch.tv/videos/{vid}?t={fmt_offset(max(0, off - cfg.pre))}",
                     "viewer_clips": [f"{v['title']} ({v['viewCount']} views)" for v in c["viewer"]],
                     "rank_score": round(c["score"], 2)}
        job.hook_sources = [v["title"] for v in sorted(c["viewer"], key=lambda v: -v["viewCount"])]
        factory.submit(job)
    factory.q.join()
    if cfg.buffer_minutes > 0:
        shutil.rmtree(sess / "vod_segments", ignore_errors=True)
    log("vod", f"done - {factory.done_count} clips in {cfg.out / login}")


# --------------------------------------------------------------------------- analyze mode


def analyze(cfg: Config, path: Path):
    msgs = []
    for line in path.read_text("utf-8").splitlines():
        try:
            d = json.loads(line)
            msgs.append((float(d["t"]), d["u"], d["m"]))
        except (ValueError, KeyError):
            continue
    if not msgs:
        print("no messages in", path)
        return []
    msgs.sort()
    det = SpikeDetector(cfg)
    spikes, scores = [], []
    for t, u, m in msgs:
        for sp in det.tick(t):
            spikes.append(sp)
        det.add(t, u, m)
        if det.last.get("baseline") is not None:
            scores.append((det.last["score"], det.last["baseline"]))
    spikes += det.tick(msgs[-1][0] + 2 * cfg.bucket)
    span = msgs[-1][0] - msgs[0][0]
    print(f"{path.name}: {len(msgs)} messages over {span / 60:.1f} min ({len(msgs) / max(span, 1):.1f} msg/s)")
    for sp in spikes:
        print(f"  spike at {dt.datetime.fromtimestamp(sp.onset):%H:%M:%S}  score {sp.score:.0f} vs {sp.baseline:.0f} "
              f"(x{sp.ratio:.1f})  e.g. {' | '.join(x for _, _, x in sp.sample[:5])[:150]}")
    print(f"  -> {len(spikes)} clips, {len(spikes) / max(span / 3600, 1e-9):.0f} per hour at sensitivity {cfg.sensitivity}")
    return spikes


# --------------------------------------------------------------------------- startup

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"


def streamlink_cmd() -> list[str]:
    try:
        import streamlink  # noqa: F401
        return [sys.executable, "-m", "streamlink"]
    except ImportError:
        exe = shutil.which("streamlink")
        if exe:
            return [exe]
        raise SystemExit("streamlink is not installed: run  python -m pip install streamlink")


def preflight(cfg: Config):
    problems = []
    if not shutil.which("ffmpeg"):
        problems.append("ffmpeg not found on PATH (Windows: winget install Gyan.FFmpeg)")
    try:
        streamlink_cmd()
    except SystemExit as e:
        problems.append(str(e))
    if cfg.captions:
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            problems.append("faster-whisper is not installed: python -m pip install faster-whisper  (or run with --no-captions)")
    if problems:
        raise SystemExit("cannot start:\n  - " + "\n  - ".join(problems))


def main(argv=None):
    global _log_file
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass
    cfg, args = parse_args(argv)
    if os.name == "nt":
        # be a background job: the user's own apps come first (children inherit below-normal on Windows)
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)
    if args.analyze:
        analyze(cfg, args.analyze)
        return
    preflight(cfg)
    cfg.out.mkdir(parents=True, exist_ok=True)
    cfg.work.mkdir(parents=True, exist_ok=True)
    _log_file = open(cfg.work / "autoclip.log", "a", encoding="utf-8")
    if args.vod:
        globals()['CLIP_PERIOD'] = args.clip_period
        vod_mode(cfg, args)
        return
    log("autoclip", f"clips -> {cfg.out} | buffer {cfg.buffer_minutes or 'whole stream'} min | "
                    f"spike = {cfg.sensitivity}x baseline | clip = {cfg.pre:.0f}s before + {cfg.post:.0f}s after the reaction")

    stop = threading.Event()
    factory = ClipFactory(cfg)
    factory.start()
    watchers: dict[str, ChannelWatcher] = {}
    for ch in cfg.channels:
        w = ChannelWatcher(ch, cfg, factory, stop)
        watchers[ch] = w
        w.start()
    if cfg.game:
        threading.Thread(target=director, args=(cfg, factory, stop, watchers), daemon=True, name="director").start()

    started = time.time()
    try:
        while True:
            time.sleep(0.5)
            if not cfg.game and not any(w.is_alive() for w in watchers.values()):
                break
            if args.max_minutes and time.time() - started >= args.max_minutes * 60:
                log("autoclip", f"--max-minutes {args.max_minutes:g} reached; finishing queued clips")
                break
    except KeyboardInterrupt:
        log("autoclip", "stopping: finishing the clips already queued (Ctrl+C again to quit now)")
    stop.set()
    try:
        for w in list(watchers.values()):
            w.join(timeout=30)
        while factory.pending():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    log("autoclip", f"done - {factory.done_count} clips this run, index at {cfg.out / 'index.jsonl'}")


if __name__ == "__main__":
    main()
