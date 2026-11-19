"""Copy finished clips (phone 9:16 version) into ONE folder, named streamer + what happens:  python export_clips.py
   Downloads/GTA 6/Kai Cenat - sex scene.mp4, Lacy - fight with an alligator.mp4 ... + captions.txt
Names come from names.json (edit it to rename); a clip without a name there uses its viewer-clip title or hook."""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEST = Path.home() / "Downloads" / "GTA 6"
# live chat-spike clips went 0 for 35 in review -> only reviewed past-stream picks and crowd-proven moments
SOURCES = [HERE / "clips_ready", HERE / "clips_crowd", HERE / "clips_crowd_older"]
NAMES = {"kaicenat": "Kai Cenat", "lacy": "Lacy", "clix": "Clix", "yourragegaming": "YourRAGE", "jynxzi": "Jynxzi",
         "theburntpeanut": "TheBurntPeanut", "ohnepixel": "ohnePixel", "zackrawrr": "Asmongold", "xqc": "xQc",
         "evelone2004": "Evelone", "buster": "Buster", "ishowspeed": "Speed", "caseoh_": "CaseOh",
         "stableronaldo": "StableRonaldo", "joe_bartolozzi": "Joe Bartolozzi", "recrent": "Recrent",
         "jasontheween": "JasonTheWeen", "summit1g": "Summit1g", "agent00": "Agent 00", "squeex": "Squeex"}
REJECT = {
    "lacy_190439_x7.7", "lacy_153249_x4.7",        # chat polls ("type ME", "ofc"), not moments
    "lacy_164107_x2.0",                            # Lacy not visible (fell out of his cam) -> re-cut as lacy_164053
    "kaicenat_191153_x0.0",                        # bed scene, too long -> re-cut as kaicenat_191215
    "kaicenat_133035_x2.3", "kaicenat_131111_x1.4",  # already sent to a friend
    "clix_144730_x6.7",                            # chat poll ("type me if you have a girlfriend")
}
NON_GTA = HERE / "non_gta.json"   # written by rerender.py from Twitch chapter markers


def moment_key(base: str) -> str:
    """'kaicenat_133035_x2.3' -> 'kaicenat_133035': the same moment keeps its key even when the chat ratio in the
    name changes (a re-made clip had slipped back in that way)."""
    return base.rsplit("_x", 1)[0]


DROPS = HERE / "drops.json"       # clips an independent review scored as not worth posting


def rejected(base: str) -> bool:
    non_gta = set(json.loads(NON_GTA.read_text("utf-8"))) if NON_GTA.exists() else set()
    drops = set(json.loads(DROPS.read_text("utf-8")).get("drop", [])) if DROPS.exists() else set()
    keys = {moment_key(b) for b in REJECT | non_gta | drops}
    exact = set(json.loads(DROPS.read_text("utf-8")).get("drop_exact", [])) if DROPS.exists() else set()
    return not base or moment_key(base) in keys or base in exact


APPROVED = HERE / "approved.json"  # crowd clips the independent review passed


CROWD_MIN_VIEWS = 300   # user: "download the viral ones from Twitch" - a viewer clip with this many views is the proof


def crowd_views(d: dict) -> int:
    import re
    return sum(int(m.group(1)) for v in d.get("viewer_clips") or [] for m in [re.search(r"\((\d+) views\)", v)] if m)


def approved() -> set:
    return {moment_key(b) for b in (json.loads(APPROVED.read_text("utf-8")) if APPROVED.exists() else [])}


SCORES = HERE / "scores.json"     # independent reviewer score per moment
MIN_SCORE = 6                     # user: "we need at least 6/10s"


def score(base: str):
    s = json.loads(SCORES.read_text("utf-8")).get("scores", {}) if SCORES.exists() else {}
    return s.get(moment_key(base))


def unscored(sources=None) -> list:
    """Finished clips that still need a review (no score yet) - the reviewer's next round."""
    out = []
    for root in sources or SOURCES:
        for meta in root.glob("*/*/*.json"):
            try:
                d = json.loads(meta.read_text("utf-8"))
            except (OSError, ValueError):
                continue
            b = d.get("file_base") if isinstance(d, dict) else None  # some .json are lists
            if b and not rejected(b) and score(b) is None and (meta.parent / f"{b}_{FORMAT}.mp4").exists():
                out.append(str(meta))
    return sorted(out)


BAD_CHARS = '<>:"/\\|?*'
FORMAT = "vertical"        # phone 9:16 (facecam on top, gameplay below); "horizontal" for the 16:9 desktop version


def said_line(transcript: str) -> str:
    """A name from what the streamer said: the most exclaimed sentence, first 7 words, swears softened."""
    import re
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", transcript) if len(x.split()) >= 3]
    if not sents:
        return ""
    best = max(sents, key=lambda x: (x.count("!") * 2 + x.count("?"), -abs(len(x.split()) - 6)))
    words = re.sub(r"[^\w' ]", "", best).lower().split()[:7]
    soft = {"fuck": "f", "fucking": "f", "shit": "sh", "bitch": "b"}
    return " ".join(soft.get(w, w) for w in words)


DEST_LOW = Path.home() / "Downloads" / "GTA 6 - under 6"   # user: keep the ones under 6 to watch, in their own folder


def main():
    good, low = {}, {}
    for root in SOURCES:
        for meta in root.glob("*/*/*.json"):
            try:
                d = json.loads(meta.read_text("utf-8"))
            except (OSError, ValueError):
                continue
            base = d.get("file_base")
            if rejected(base) or not (meta.parent / f"{base}_{FORMAT}.mp4").exists():
                continue
            sc = score(base)
            if sc is None:
                continue                               # not reviewed yet: waits for the reviewer
            target = good if sc >= MIN_SCORE else low  # 6/10 or more -> GTA 6, under 6 -> GTA 6 - under 6
            target.setdefault(d["channel"], {})[base] = (d.get("moment") or "", meta.parent, d)
    export_to(DEST, good, with_score=False)
    export_to(DEST_LOW, low, with_score=True)
    make_batches()


BATCHES = HERE / "batches.json"   # user: batches of 5 clips scoring over 6, each in its own Downloads folder
CAMPAIGN = {"lacy": "LACY", "clix": "Clix", "yourragegaming": "YourRAGE"}   # Reach campaigns: name + this hashtag


def post_text(channel: str, what: str) -> str:
    """Post caption from the clip's name. Campaign streamers: their name in the text and the campaign hashtag
    (Reach rules); a re-render had dropped #LACY from the alligator clip's own post file."""
    name = NAMES.get(channel, channel)
    tag = CAMPAIGN.get(channel)
    tags = ([tag] if tag else []) + [channel, f"{channel}clips", "gta6", "gtavi", "gta6clips", "twitch", "twitchclips"]
    head = f"{name} {what}" if name.lower() not in what.lower() else what
    return f"{head} \U0001F480\n\n\U0001F3A5 twitch.tv/{channel}\n\n" + " ".join("#" + t for t in dict.fromkeys(tags))


def make_batches(size: int = 5, min_score: int = 6):  # user: 6 counts
    """Every 5 clips scoring 6+ that are not in a batch yet become the next 'GTA 6 - batch N' folder."""
    names = json.loads((HERE / "names.json").read_text("utf-8")) if (HERE / "names.json").exists() else {}
    done = json.loads(BATCHES.read_text("utf-8")) if BATCHES.exists() else []
    used = {b for batch in done for b in batch}
    pool = []
    for root in SOURCES:
        for meta in root.glob("*/*/*.json"):
            try:
                d = json.loads(meta.read_text("utf-8"))
            except (OSError, ValueError):
                continue
            b = d.get("file_base") if isinstance(d, dict) else None  # some .json are lists
            if b and b not in used and not rejected(b) and (score(b) or 0) >= min_score \
                    and (meta.parent / f"{b}_{FORMAT}.mp4").exists():
                pool.append(((score(b), crowd_views(d)), b, meta.parent, d))
    pool.sort(key=lambda x: x[0], reverse=True)          # best first
    while len(pool) >= size:
        batch, pool = pool[:size], pool[size:]
        n = len(done) + 1
        dest = Path.home() / "Downloads" / f"GTA 6 - batch {n}"
        dest.mkdir(parents=True, exist_ok=True)
        lines = []
        for (sc, _), b, folder, d in batch:
            what = "".join(ch for ch in (names.get(b) or b) if ch not in BAD_CHARS).strip(" .")
            label = f"{NAMES.get(d['channel'], d['channel'])} - {what}"
            shutil.copy2(folder / f"{b}_{FORMAT}.mp4", dest / f"{label}.mp4")
            lines.append(f"===== {label}  ({sc}/10, {d.get('duration')}s)\n" + post_text(d["channel"], what))
        (dest / "captions.txt").write_text("\n\n".join(lines) + "\n", "utf-8")
        done.append([b for _, b, _, _ in batch])
        BATCHES.write_text(json.dumps(done, indent=1), "utf-8")
        print(f"NEW BATCH READY: {dest}")


def titles() -> dict:
    """Funny hook titles per exported mp4 name (titles.json) - kept in captions.txt on every export."""
    f = HERE / "titles.json"
    try:
        return json.loads(f.read_text("utf-8")) if f.exists() else {}
    except ValueError:
        return {}


def export_to(dest: Path, clips: dict, with_score: bool):
    dest.mkdir(parents=True, exist_ok=True)
    manifest = dest / ".exported.json"               # only files this script wrote are ever replaced
    previous = json.loads(manifest.read_text("utf-8")) if manifest.exists() else []
    written = []
    names_file = HERE / "names.json"
    names = json.loads(names_file.read_text("utf-8")) if names_file.exists() else {}
    used, captions, total = set(), [], 0
    for channel, items in sorted(clips.items()):
        name = NAMES.get(channel, channel)
        for base, (moment, folder, d) in sorted(items.items(), key=lambda kv: kv[1][0]):
            what = (names.get(base)
                    or next((v.rsplit(" (", 1)[0] for v in d.get("viewer_clips") or []), None)
                    or (d.get("hook") or "").lower()
                    or said_line(d.get("transcript") or "")
                    or "moment " + moment[-8:].replace(":", ""))
            what = "".join(ch for ch in what if ch not in BAD_CHARS).strip(" .")
            if with_score:
                what += f" ({score(base)} of 10)"
            tag, k = f"{name} - {what}", 2
            while tag.lower() in used:
                tag, k = f"{name} - {what} ({k})", k + 1
            used.add(tag.lower())
            src, dst = folder / f"{base}_{FORMAT}.mp4", dest / f"{tag}.mp4"
            if not dst.exists() or dst.stat().st_size != src.stat().st_size:   # only new or changed clips are copied
                shutil.copy2(src, dst)
            written.append(dst.name)
            title = titles().get(dst.name)
            captions.append(f"===== {tag}  ({d.get('stream_time') or moment}, {d.get('duration')}s)\n"
                            + (f"TITLE: {title}\n" if title else "") + post_text(d["channel"], what) + "\n")
            total += 1
            print(f"{tag}.mp4")
    for f in set(previous) - set(written) - {"captions.txt"}:   # a file this script wrote that is now renamed/held
        (dest / f).unlink(missing_ok=True)
    (dest / "captions.txt").write_text("\n".join(captions), "utf-8")
    manifest.write_text(json.dumps(written + ["captions.txt"]), "utf-8")
    print(f"\n{total} clips in {dest}\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
