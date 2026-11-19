"""Realistic Pokémon on Atlas (nano-banana-2.1-developer). Shared client (call/upload/run) + batch 1.
Run: python3 gen.py [redo]   (sheets.py and scenes.py import run/upload from here)"""
import csv, json, pathlib, ssl, subprocess, sys, time, urllib.error, urllib.request

MODEL = "google/nano-banana-2.1-developer/text-to-image"
BASE = "https://api.atlascloud.ai/api/v1/model/"
ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "out"
IMG = (".png", ".jpg", ".jpeg", ".webp", ".mp4")  # finished outputs (images + video)
UA = "pokemon-real/1.0"
CTX = ssl.create_default_context(cafile="/etc/ssl/cert.pem")  # python.org builds ship no CA bundle
def _key():
    """Atlas Cloud API key from env ATLAS_API_KEY (get your own at atlascloud.ai)."""
    import os
    k = os.environ.get("ATLAS_API_KEY", "YOUR_TOKEN_HERE")
    if k == "YOUR_TOKEN_HERE":
        raise SystemExit("set ATLAS_API_KEY")
    return k


KEY = _key()

REAL = ("Hyper-realistic photograph of how {name} would look if it were a real living creature in our world. "
        "Keep the official design EXACTLY: same silhouette, same proportions, same face, same colours and markings, "
        "same number of fingers and toes. Only the materials change: {skin}, visible pores and fine texture, "
        "subsurface light through thin skin, wet glossy eyes with real reflections, believable weight and muscle. "
        "Real camera photo, natural light, shallow depth of field, fine film grain. "
        "Not a cartoon, not a toy, not a plush, not a person in a costume, not a smooth CGI render. No text, no logos.")

CHARS = [
    ("1-mewtwo", "Mewtwo",
     "Tall bipedal psychic creature, pale lavender-white body, deep purple long thick tail and purple lower belly, "
     "a tube running from the back of its skull to its upper spine, short blunt horn-like ears, violet narrow eyes, "
     "plated chest ridges, three thick fingers with round bulb tips, powerful thighs, stern cold stare",
     "smooth pale hairless skin like a real animal's hide, faint veins",
     "standing on a ridge in an overcast alpine valley, full body, eye-level wildlife photo, 85mm",
     "low-angle cinematic film still inside a ruined dark genetics laboratory at night, purple and teal light, "
     "glowing liquid tank behind it, rain-streaked glass, moody volumetric haze"),
    ("2-charizard", "Charizard",
     "Large orange fire dragon, cream-yellow belly, broad teal-green wing membranes with orange wing bones, "
     "two horns at the back of its head, long neck, small fangs, clawed hands and feet with white claws, "
     "a real burning flame on the tip of its tail",
     "orange reptile skin with fine scales and leathery wing membranes with veins",
     "standing on volcanic rock on a cliff at golden hour, wings half open, full body, wildlife photo, 200mm",
     "cinematic action still, flying fast through a deep blue sky with streaking clouds, wings fully spread, "
     "motion blur in the background, sharp on the dragon"),
    ("3-gengar", "Gengar",
     "Round squat dark purple ghost creature, spiky back and pointed spiky ears, huge wide grin full of flat white "
     "teeth, glowing red-pink eyes, short stubby arms and legs with three small fingers, mischievous expression",
     "dense short velvety dark purple fur over a soft round body, slightly translucent edges",
     "crouching in an old abandoned Victorian house hallway lit by one candle, full body, 50mm",
     "cinematic still, floating out of deep shadow toward the camera at night in a foggy graveyard, "
     "cold moonlight rim, red eyes glowing, unsettling grin"),
    ("4-pikachu", "Pikachu",
     "Small round yellow electric mouse, long pointed ears with black tips, round red cheek pouches, "
     "small black shiny eyes, tiny mouth, lightning-bolt shaped tail with a brown base, two brown stripes on its back, "
     "short arms, standing upright",
     "dense soft yellow fur with individual hairs, damp black nose",
     "sitting in tall green grass on a summer meadow, eye-level macro wildlife photo, 100mm, soft morning light",
     "standing on an orange clay tennis court in bright daylight, tiny sparks crackling from its red cheeks, "
     "low eye-level angle, sport photography look"),
    ("5-lucario", "Mega Lucario",
     "Upright jackal-like fighter, blue and black fur, cream yellow chest fur, sharp white spikes on the backs of its "
     "hands and on its chest, four long black aura appendages with red tips flowing from the back of its head, "
     "red-orange eyes, red markings on its paws and lower legs, cream bushy tail, lean muscular build",
     "short dense blue and black fur with real guard hairs, white bone-like spikes",
     "standing in a misty mountain forest at dawn, full body, eye-level wildlife photo, 85mm",
     "cinematic still in a stone temple courtyard at dusk, blue aura energy glowing around its hands, "
     "appendages lifted by the wind, dramatic rim light"),
    ("6-dragonite", "Dragonite",
     "Large friendly chubby dragon, orange-tan body, pale cream segmented belly, small teal-green wings, "
     "two thin antennae on its forehead, a small horn on top of its head, small rounded snout, kind eyes, "
     "short arms with three claws, thick tail",
     "warm orange smooth reptile skin with fine pebbled scales and soft leathery wing membranes",
     "standing on a sea cliff above a stormy ocean, full body, wildlife photo, 135mm, overcast light",
     "cinematic still flying low over ocean waves at sunset, wings beating, spray in the air, warm backlight"),
]
VARIANTS = {"A": ("2:3", 4), "B": ("16:9", 5)}  # index into CHARS tuple for the scene

REDO = {  # `python3 gen.py redo`: batch-1 weak ones again at 2k, saved as <stem>2
    "1-mewtwo-A": "Make the skin look alive, not a statue or vinyl figure: uneven skin tone, faint blotches, creases "
                  "at the joints, small scars, dust on the feet, muscle shifting under the skin. "
                  "RAW wildlife photo on a Sony A1, 85mm f/2.",
    "1-mewtwo-B": "It must look like a real photograph taken with a real camera on a practical film set, NOT a CGI "
                  "movie render: practical lights, real haze, lens imperfections, film grain, skin with pores, "
                  "creases and blemishes. 35mm film still.",
    "6-dragonite-A": "Make the skin look alive, not rubber or a toy: matte weathered reptile hide, uneven colour, "
                     "small scratches, salt spray and wet patches, creases at the joints and neck. "
                     "RAW wildlife photo on a Sony A1, 135mm f/2.8.",
}


def call(path, payload=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode() if payload else None,
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                                          "User-Agent": UA})  # Atlas 403s Python's default UA
    try:
        with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:  # Atlas puts the refusal reason in the body
        try:
            return json.loads(e.read())
        except ValueError:
            raise e


def upload(path):
    """Free. curl does the multipart; the key goes in via stdin so it never shows in `ps`."""
    r = subprocess.run(["curl", "-s", "-A", UA, "-H", "@-", "-F", f"file=@{path}", BASE + "uploadMedia"],
                       input=f"Authorization: Bearer {KEY}\n", capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    if d.get("code") != 200:
        raise RuntimeError(f"upload {path}: {d.get('msg') or d.get('message')}")
    return d["data"].get("url") or d["data"]["download_url"]


def balance():
    """Free. Real USD left on the account (Atlas billing API), or None if unreachable."""
    req = urllib.request.Request("https://api.atlascloud.ai/public/v1/balance",
                                 headers={"Authorization": f"Bearer {KEY}", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
            return float(json.load(r)["available"]["value"])
    except Exception:
        return None


SPEND_LOG = pathlib.Path.home() / "atlas_spend.csv"  # one log for every project on this key


def _log_spend(before, stems, out):
    """Real cost = balance drop over the run. Counts other users of the key too, so it can only over-report."""
    after = balance()
    if before is None or after is None or not stems:
        return
    new = not SPEND_LOG.exists()
    with SPEND_LOG.open("a") as f:
        if new:
            f.write("time,folder,jobs,balance_before,balance_after,real_cost\n")
        f.write(f"{time.strftime('%F %T')},{out},{len(stems)},{before:.4f},{after:.4f},{before - after:.4f}\n")
    print(f"real cost {before - after:.4f} USD for {len(stems)} jobs, {after:.2f} left", flush=True)


def run(items, out, endpoint="generateImage"):
    """items = {stem: payload}. Resumable and never pays twice: a <stem>.task file means already submitted."""
    out.mkdir(parents=True, exist_ok=True)
    before, submitted = balance(), []
    jobs = {}
    for stem, p in items.items():
        if any((out / (stem + e)).exists() for e in IMG):
            continue
        task = out / f"{stem}.task"
        if task.exists():
            jobs[stem] = task.read_text().strip(); continue
        (out / f"{stem}.request.json").write_text(json.dumps(p, indent=1))
        try:
            d = call(endpoint, p)
        except Exception as e:
            print(stem, "submit error", e, flush=True); continue
        if d.get("code") != 200:
            print(stem, "refused:", d.get("msg") or d.get("message"), flush=True); continue
        jobs[stem] = d["data"]["id"]
        task.write_text(jobs[stem]); submitted.append(stem)
        print(stem, "submitted", flush=True)
    end = time.time() + 900
    while jobs and time.time() < end:
        time.sleep(6)
        for stem, pid in list(jobs.items()):
            try:
                d = call(f"prediction/{pid}")["data"]
            except Exception:
                continue  # transient; the job is already paid, keep polling
            if d["status"] == "failed":
                print(stem, "FAILED:", d.get("error"), flush=True); del jobs[stem]
            elif d["status"] == "completed":
                url = d["outputs"][0]
                ext = pathlib.Path(url.split("?")[0]).suffix or ".png"
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}),
                                            timeout=120, context=CTX) as r:
                    (out / f"{stem}{ext}").write_bytes(r.read())
                print(stem, "done", flush=True); del jobs[stem]
    for stem in jobs:
        print(stem, "still processing (rerun to fetch, costs nothing)", flush=True)
    _log_spend(before, submitted, out)


def main(redo=False):
    items = {}
    for c in CHARS:
        slug, name, design, skin = c[:4]
        for v, (ar, i) in VARIANTS.items():
            stem, res, extra = f"{slug}-{v}", "1k", ""
            if redo:
                if stem not in REDO:
                    continue
                stem, res, extra = stem + "2", "2k", " " + REDO[stem]
            prompt = f"{name}. {design}. Scene: {c[i]}. " + REAL.format(name=name, skin=skin) + extra
            items[stem] = {"model": MODEL, "prompt": prompt, "aspect_ratio": ar, "resolution": res}
    run(items, OUT)


if __name__ == "__main__":
    main(redo="redo" in sys.argv)
