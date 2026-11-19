"""Insert streamer reaction clips into a rendered narrated body with FFmpeg.

Run:
    python tools/scripts/assemble.py <slug> <body.mp4> --output out/<name>.mp4
    python tools/scripts/assemble.py --self-test

Reads   src/data/<slug>.json          captions[].from, one per script phrase
        videos/<slug>/plan.json       {"inserts":[{"after_phrase":k,"file","in","out","credit","handle"}]}
The body is cut at frame captions[k+1].from and the clip's [in, out] plays there with its own audio.
"pops" entries {"after_phrase","vertical","horizontal","v_in","v_out","h_in","credit","handle","bleeps"?} are
inserted the same way, but the picture is the raw 16:9 gameplay cropped to 9:16 with the vertical clip's webcam
box as a bordered inset below the header; the audio is the vertical clip's. after_phrase is shared with inserts.
Clip audio is levelled to the narration with a two-pass loudnorm; clip folders are only ever read.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
FPS = 30
SPF = 48000 // FPS  # audio samples per frame
FONT = ROOT / "public" / "fonts" / "Montserrat-BlackItalic.ttf"
WHOOSH = ROOT / "public" / "sfx" / "whoosh.wav"
LUFS = -15  # the narration is mastered to about this
WHOOSH_GAIN = 0.35
WHOOSH_LEAD = 0.15  # seconds before the join, so the swoosh peaks on the cut
PLATE_SECONDS = 2.5
FADE = 0.2
# Reaction clips stack webcam (top), game (middle), burned captions in the middle, black below.
# The empty blurred band at the very top (y 0-230) is the one area with no face, action or caption.
NAME_Y, HANDLE_Y = 70, 170
# Pop layout: webcam box measured on xQc's vertical export (x 0-870, y 228-835; the rest is blurred fill), cut at 798 to stay above the burned caption (y ~810).
CAM = (870, 570, 0, 228)
INSET_W, BORDER, INSET_TOP = 720, 6, 340
INSET_H = round(INSET_W * CAM[1] / CAM[0] / 2) * 2
# 0.8 crop height from y=0 drops the raw capture's facecam (left 0-23%) and its burned captions (88-92% of height).
POP_BG = "crop=w=ih*0.8*9/16:h=ih*0.8:x=(iw-ow)/2:y=0,scale=1080:1920:flags=lanczos"
# Used only when plan.json has "bed" (SOUND-RULES.md section 2); without it the old mix is unchanged.
SFX = ROOT / "media" / "sfx"
BED_DB, POP_BED_DB, POP_WHOOSH_DB, MEME_DB = -10, -24, -12, -4  # memes at -10 were masked by the duck (measured -14..-29 dB under the mix)
DUCK = "sidechaincompress=threshold=0.03:ratio=6:attack=40:release=400"


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def frame_count(path: Path) -> int:
    streams = probe(path)["streams"]
    video = next((s for s in streams if s["codec_type"] == "video"), {})
    if (video.get("width"), video.get("height"), video.get("avg_frame_rate")) != (1080, 1920, "30/1"):
        raise ValueError(f"{path.name} must use 1080x1920 video at 30 fps.")
    if not any(s["codec_type"] == "audio" for s in streams):
        raise ValueError(f"{path.name} needs an audio track.")
    frames = video.get("nb_frames", "")
    if not frames.isdigit() or int(frames) < 1:
        raise ValueError(f"{path.name} has no countable video track.")
    return int(frames)


def measure_loudness(clip: Path, start: float, dur: float) -> dict | None:
    """loudnorm pass 1. None when the trim is silent (nothing to level)."""
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(clip),
         "-vn", "-af", f"loudnorm=I={LUFS}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    found = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", result.stderr, re.S)
    if not found:
        raise ValueError(f"loudnorm gave no measurement for {clip.name}")
    stats = json.loads(found[-1])
    return None if float(stats["input_i"]) < -60 else stats


def esc_font(path: Path) -> str:
    return path.as_posix().replace(":", r"\:")  # C:/x -> C\:/x


def plate_filters(name_file: str, handle_file: str, name: str, name_y: int = NAME_Y, handle_y: int = HANDLE_Y) -> str:
    size = int(min(96, 920 / (0.8 * max(len(name), 1))))
    alpha = f"if(lt(t,{FADE}),t/{FADE},if(gt(t,{PLATE_SECONDS - FADE}),({PLATE_SECONDS}-t)/{FADE},1))"
    common = (f"fontfile='{esc_font(FONT)}':fontcolor=white:bordercolor=black:expansion=none:"
              f"x=(w-text_w)/2:enable='lt(t,{PLATE_SECONDS})':alpha='{alpha}'")
    return (f"drawtext=textfile={name_file}:fontsize={size}:borderw=8:y={name_y}:{common},"
            f"drawtext=textfile={handle_file}:fontsize=46:borderw=5:y={handle_y}:{common}")


def anchor(m: dict, caps: list, plan: list, counts: list, joins: list) -> float:
    """Output seconds of a plan meme/sfx: "pop": j = the j-th pop's join, else the start of caption "phrase"; plus "at"."""
    if "pop" in m:
        return joins[m["pop"]] + float(m.get("at", 0))
    before = sum(counts[2 * j + 1] for j, p in enumerate(plan) if p["after_phrase"] < m["phrase"])
    return (caps[m["phrase"]]["from"] + before) / FPS + float(m.get("at", 0))


def per_window(times: list, most: int, what: str, window: float = 30.0) -> None:
    for i, t in enumerate(times):
        n = sum(t <= u < t + window for u in times[i:])
        if n > most:
            raise ValueError(f"{n} {what} in the 30 s from {t:.2f}s (most {most}).")


def meme_times(memes: list, caps: list, plan: list, counts: list, joins: list, total: float) -> list:
    """(meme, output seconds, length) per plan meme; ValueError on any SOUND-RULES section 4 violation."""
    out = []
    for m in memes:
        t = anchor(m, caps, plan, counts, joins)
        d = float(m["len"]) if "len" in m else float(probe(ROOT / m["file"])["format"]["duration"])
        if m.get("streamer") and not any(
                p.get("credit", "").lower() == m["streamer"].lower() and j0 <= t and t + d <= j0 + counts[2 * j + 1] / FPS
                for j, (p, j0) in enumerate(zip(plan, joins))):
            raise ValueError(f"{m['file']} is a {m['streamer']} meme outside that streamer's pop.")
        out.append((m, t, d))
    out.sort(key=lambda x: x[1])
    if len(out) < 2:
        raise ValueError(f"plan.json needs at least 2 memes, has {len(out)}.")
    if len({m["file"] for m, _, _ in out}) != len(out):
        raise ValueError("A meme sound is used twice.")
    per_window([t for _, t, _ in out], 5, "memes")
    for (a, ta, da), (b, tb, _) in zip(out, out[1:]):
        if ta + da > tb:
            raise ValueError(f"{a['file']} ({ta:.2f}+{da:.2f}s) overlaps or is after {b['file']} ({tb:.2f}s).")
    if out[-1][1] + out[-1][2] > total:
        raise ValueError(f"{out[-1][0]['file']} runs past the end ({total:.2f}s).")
    return out


def sfx_times(sfx: list, memes: list, caps: list, plan: list, counts: list, joins: list, total: float) -> list:
    """(sfx, onset seconds) per plan "sfx" entry {file, phrase|pop, at, lead?, db, why}; the onset is the anchor minus lead,
    so a whoosh peaks on the cut. ValueError past 6 per 30 s, outside the video, or within 0.5 s of another sound."""
    out = []
    for e in sfx:
        t = anchor(e, caps, plan, counts, joins) - float(e.get("lead", 0))
        if t < 0 or t + float(probe(ROOT / e["file"])["format"]["duration"]) > total:
            raise ValueError(f"{e['file']} at {t:.2f}s does not fit inside the {total:.2f}s video.")
        out.append((e, t))
    out.sort(key=lambda x: x[1])
    per_window([t for _, t in out], 6, "SFX")
    onsets = sorted([(t, e["file"]) for e, t in out] + [(t, m["file"]) for m, t, _ in memes])
    for (ta, fa), (tb, fb) in zip(onsets, onsets[1:]):
        if tb - ta < 0.5:
            raise ValueError(f"{fa} ({ta:.2f}s) and {fb} ({tb:.2f}s) start within 0.5 s.")
    return out


def build(slug: str, body: Path, output: Path) -> None:
    caps = json.loads((ROOT / "src" / "data" / f"{slug}.json").read_text(encoding="utf-8"))["captions"]
    raw = json.loads((ROOT / "videos" / slug / "plan.json").read_text(encoding="utf-8"))
    # a pop with no "vertical" is horizontal-only: picture, cam inset and audio all come from the 16:9 clip
    plan = raw.get("inserts", []) + [{**p, "file": p.get("vertical", p["horizontal"]), "in": p.get("v_in", p["h_in"]),
                                      "out": p.get("v_out", p.get("h_out"))} for p in raw.get("pops", [])]
    bed = raw.get("bed")
    plan = sorted(plan, key=lambda i: i["after_phrase"])
    ks = [i["after_phrase"] for i in plan]
    if len(set(ks)) != len(ks) or any(not 0 <= k < len(caps) - 1 for k in ks):
        raise ValueError(f"after_phrase must be unique and in 0..{len(caps) - 2}; got {ks}")
    if not plan:
        raise ValueError("plan.json has no inserts or pops.")

    body_frames = frame_count(body)
    cuts = [caps[k + 1]["from"] for k in ks]
    if cuts != sorted(set(cuts)) or cuts[0] < 1 or cuts[-1] >= body_frames:
        raise ValueError(f"Cut frames {cuts} must be increasing and inside the {body_frames}-frame body.")

    with TemporaryDirectory(dir=output.parent) as folder:
        work = Path(folder)
        inputs = ["-i", str(body)]
        vf, af, order, counts = [], [], [], []
        edges = [0, *cuts, body_frames]
        n = len(plan)
        vf.append(f"[0:v]split={n + 1}" + "".join(f"[b{i}]" for i in range(n + 1)))
        af.append("[0:a]aresample=48000:async=1:first_pts=0,aformat=channel_layouts=stereo,"
                  f"asplit={n + 1}" + "".join(f"[a{i}]" for i in range(n + 1)))
        nin = 1  # next ffmpeg input index (0 is the body)
        joins = []  # output time in seconds of each body->clip join
        elapsed = 0

        def body_piece(i):
            nonlocal elapsed
            a, b = edges[i], edges[i + 1]
            vf.append(f"[b{i}]trim=start_frame={a}:end_frame={b},setsar=1,settb=1/{FPS},setpts=N[bv{i}]")
            af.append(f"[a{i}]atrim=start_sample={a * SPF}:end_sample={b * SPF},asetpts=N/SR/TB[ba{i}]")
            order.append(f"[bv{i}][ba{i}]")
            counts.append(b - a)
            elapsed += b - a

        for i, ins in enumerate(plan):
            body_piece(i)
            clip, start, end = Path(ins["file"]), float(ins["in"]), float(ins["out"])
            frames = round((end - start) * FPS)
            if frames < 1 or start < 0:
                raise ValueError(f"Bad in/out for {clip.name}: {start}-{end}")
            clip_len = float(probe(clip)["format"]["duration"])
            if end > clip_len + 0.001:
                raise ValueError(f"{clip.name}: out={end} is past the clip end ({clip_len:.2f}s).")
            stats = measure_loudness(clip, start, frames / FPS)
            norm = ("" if stats is None else
                    f"loudnorm=I={LUFS}:TP=-1.5:LRA=11:measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
                    f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
                    f"offset={stats['target_offset']}:linear=true,")
            (work / f"n{i}.txt").write_text(ins["credit"].upper(), encoding="utf-8")
            (work / f"h{i}.txt").write_text(ins["handle"].upper(), encoding="utf-8")
            idx = nin
            inputs += ["-ss", f"{start:.3f}", "-t", f"{frames / FPS + 0.5:.3f}", "-i", str(clip)]
            nin += 1
            trim = f"trim=end_frame={frames},settb=1/{FPS},setpts=N"
            if "horizontal" in ins and "vertical" not in ins:
                k = "(0.85+0.15*min(n,4)/4)"
                x = float(ins.get("x", 0.5))
                bg = (f"crop=w=ih*0.77*9/16:h=ih*0.77:x='clip(iw*{x}-ow/2,0,iw-ow)':y=0,"
                      "scale=1080:1920:flags=lanczos,setsar=1,format=yuv420p")
                if ins.get("fit"):  # [x0,y0,x1,y1]: show this source box full-width on black (a card a 9:16 crop would cut)
                    fx0, fy0, fx1, fy1 = ins["fit"]
                    bg = (f"crop=iw*{fx1 - fx0}:ih*{fy1 - fy0}:iw*{fx0}:ih*{fy0},scale=1080:-2:flags=lanczos,"
                          "pad=1080:1920:0:1000:black,setsar=1,format=yuv420p")
                if ins.get("cam"):
                    x0, y0, x1, y1 = ins["cam"]
                    v = next(s for s in probe(clip)["streams"] if s["codec_type"] == "video")
                    ih = round(INSET_W * (y1 - y0) * v["height"] / ((x1 - x0) * v["width"]) / 2) * 2
                    w, h = INSET_W + 2 * BORDER, ih + 2 * BORDER
                    vf.append(f"[{idx}:v]fps={FPS},split[sp{i}][sq{i}]")
                    vf.append(f"[sp{i}]{bg},{trim}[bg{i}]")
                    vf.append(f"[sq{i}]crop=iw*{x1 - x0}:ih*{y1 - y0}:iw*{x0}:ih*{y0},scale={INSET_W}:{ih},"
                              f"pad={w}:{h}:{BORDER}:{BORDER}:white,format=yuv420p,{trim},"
                              f"scale=w='trunc({w}*{k}/2)*2':h='trunc({h}*{k}/2)*2':eval=frame[in{i}]")
                    vf.append(f"[bg{i}][in{i}]overlay=x=(W-w)/2:y='{INSET_TOP}+({h}-h)/2':eof_action=repeat,setsar=1,"
                              + plate_filters(f"n{i}.txt", f"h{i}.txt", ins["credit"], INSET_TOP + h + 40,
                                              INSET_TOP + h + 140) + f"[cv{i}]")
                else:
                    vf.append(f"[{idx}:v]fps={FPS},{bg},{trim}," + plate_filters(
                        f"n{i}.txt", f"h{i}.txt", ins["credit"], INSET_TOP + 40, INSET_TOP + 140) + f"[cv{i}]")
            elif "horizontal" in ins:
                hor, h_in = Path(ins["horizontal"]), float(ins["h_in"])
                if h_in < 0 or h_in + frames / FPS > float(probe(hor)["format"]["duration"]) + 0.001:
                    raise ValueError(f"{hor.name}: h_in={h_in} + {frames / FPS:.2f}s runs past the clip end.")
                inputs += ["-ss", f"{h_in:.3f}", "-t", f"{frames / FPS + 0.5:.3f}", "-i", str(hor)]
                nin += 1
                w, h = INSET_W + 2 * BORDER, INSET_H + 2 * BORDER
                k = "(0.85+0.15*min(n,4)/4)"  # pop-in over the first 4 frames
                vf.append(f"[{idx + 1}:v]fps={FPS},{POP_BG},setsar=1,format=yuv420p,{trim}[bg{i}]")
                vf.append(f"[{idx}:v]fps={FPS},crop={CAM[0]}:{CAM[1]}:{CAM[2]}:{CAM[3]},scale={INSET_W}:{INSET_H},"
                          f"pad={w}:{h}:{BORDER}:{BORDER}:white,format=yuv420p,{trim},"
                          f"scale=w='trunc({w}*{k}/2)*2':h='trunc({h}*{k}/2)*2':eval=frame[in{i}]")
                vf.append(f"[bg{i}][in{i}]overlay=x=(W-w)/2:y='{INSET_TOP}+({h}-h)/2':eof_action=repeat,setsar=1,"
                          + plate_filters(f"n{i}.txt", f"h{i}.txt", ins["credit"], INSET_TOP + h + 40,
                                          INSET_TOP + h + 140) + f"[cv{i}]")
            else:
                vf.append(
                    f"[{idx}:v]fps={FPS},scale=1080:1920:force_original_aspect_ratio=decrease,"
                    f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1,format=yuv420p,{trim},"
                    + plate_filters(f"n{i}.txt", f"h{i}.txt", ins["credit"]) + f"[cv{i}]")
            # optional "bleeps": [[a, b], ...] in clip seconds: mute the span (before loudnorm, which breaks t for enable=), lay a 1 kHz tone at -20 dB (0.1)
            gate = "+".join(f"between(t,{a - start:.3f},{b - start:.3f})" for a, b in ins.get("bleeps", []))
            mute = f"volume=enable='{gate}':volume=0," if gate else ""
            tail = f"[cb{i}]" if gate else f"[ca{i}]"
            af.append(f"[{idx}:a]{mute}{norm}aresample=48000,aformat=channel_layouts=stereo,apad,"
                      f"atrim=end_sample={frames * SPF},asetpts=N/SR/TB"
                      + (f",afade=t=in:d=0.03,afade=t=out:st={frames / FPS - 0.03:.3f}:d=0.03" if bed else "") + tail)
            if gate:
                af.append(f"aevalsrc='0.1*sin(2*PI*1000*t)*({gate})':s=48000:d={frames / FPS:.3f},"
                          f"aformat=channel_layouts=stereo[bt{i}]")
                af.append(f"[cb{i}][bt{i}]amix=inputs=2:duration=first:normalize=0[ca{i}]")
            order.append(f"[cv{i}][ca{i}]")
            joins.append(elapsed / FPS)
            counts.append(frames)
            elapsed += frames
        body_piece(n)

        vf.append("".join(order) + f"concat=n={len(order)}:v=1:a=1[v][acat]")
        whoosh = []
        if not bed:
            for j, t in enumerate(joins):
                inputs += ["-i", str(WHOOSH)]
                ms = max(0, round((t - WHOOSH_LEAD) * 1000))
                whoosh.append(f"[{nin + j}:a]aformat=channel_layouts=stereo,aresample=48000,volume={WHOOSH_GAIN},"
                              f"adelay={ms}|{ms}[w{j}]")
            mix = "".join(f"[w{j}]" for j in range(n))
            af_tail = f"[acat]{mix}amix=inputs={n + 1}:duration=first:normalize=0[a]"
        else:
            pops = [(t, t + counts[2 * j + 1] / FPS) for j, t in enumerate(joins)]
            total = sum(counts) / FPS
            memes = meme_times(raw.get("memes", []), caps, plan, counts, joins, total)
            mixed = []
            # plan "sfx" (beat SFX at named moments) replaces the automatic whoosh in and out of every pop
            beats = (sfx_times(raw["sfx"], memes, caps, plan, counts, joins, total) if "sfx" in raw else
                     [({"file": f"media/sfx/{name}.wav", "db": POP_WHOOSH_DB}, max(0.0, t - lead)) for t0, t1 in pops
                      for name, t, lead in (("whoosh_short", t0, 0.15), ("whoosh_down", t1, 0.1))])
            for e, t in beats:
                inputs += ["-i", str(ROOT / e["file"])]
                ms = round(t * 1000)
                whoosh.append(f"[{nin}:a]aformat=channel_layouts=stereo,aresample=48000,"
                              f"volume={float(e['db'])}dB,adelay={ms}|{ms}[w{nin}]")
                mixed.append(f"[w{nin}]")
                nin += 1
            # [acat] (voice + pop audio) is the mix base and the sidechain key for the bed and every meme
            whoosh.append(f"[acat]asplit={len(memes) + 2}[ak]" + "".join(f"[k{j}]" for j in range(len(memes) + 1)))
            gate = "+".join(f"between(t,{a - 0.15:.3f},{b + 0.15:.3f})" for a, b in pops)
            inputs += ["-stream_loop", "-1", "-i", str(ROOT / bed)]
            whoosh.append(f"[{nin}:a]aformat=channel_layouts=stereo,aresample=48000,atrim=end={total:.3f},"
                          f"volume={BED_DB}dB,volume='if({gate},{10 ** ((POP_BED_DB - BED_DB) / 20):.4f},1)':eval=frame,"
                          f"afade=t=in:d=0.2,afade=t=out:st={total - 0.3:.3f}:d=0.3[bd]")
            whoosh.append(f"[bd][k0]{DUCK}[bed]")
            mixed.append("[bed]")
            nin += 1
            for e, t in beats:
                print(f"sfx  {t:6.2f}s  {Path(e['file']).stem}  {e.get('why', '')}")
            for m, t, d in memes:
                print(f"meme {t:6.2f}-{t + d:.2f}s  {Path(m['file']).stem}  {m.get('why', '')}")
            vlast = "v"
            for j, (m, t, d) in enumerate(memes):
                ms = round(t * 1000)
                if "key" in m:  # green-screen overlay meme: picture keyed over [v], its sound into the mix
                    cx, cy, cw, ch = m.get("crop", [0, 0, 1, 1])
                    inputs += ["-ss", f"{float(m.get('start', 0)):.3f}", "-t", f"{d:.3f}", "-i", str(ROOT / m["file"])]
                    if vlast == "v":
                        vf[-1] = vf[-1].replace("[v][acat]", "[vc][acat]")
                        vlast = "vc"
                    vf.append(f"[{nin}:v]fps={FPS},crop=iw*{cw}:ih*{ch}:iw*{cx}:ih*{cy},scale=1000:-2,"
                              f"chromakey={m['key']}:{m.get('similarity', 0.15)}:0.05,setpts=PTS-STARTPTS+{t:.3f}/TB[mv{j}]")
                    vf.append(f"[{vlast}][mv{j}]overlay=x=(W-w)/2:y=(H-h)/2:eof_action=pass[vo{j}]")
                    vlast = f"vo{j}"
                else:
                    inputs += ["-i", str(ROOT / m["file"])]
                whoosh.append(f"[{nin}:a]aformat=channel_layouts=stereo,aresample=48000,loudnorm=I=-20:TP=-2,"
                              f"aresample=48000,volume={float(m.get('db', MEME_DB))}dB,adelay={ms}|{ms}[mm{j}]")
                whoosh.append(f"[mm{j}][k{j + 1}]sidechaincompress=threshold=0.03:ratio=4:attack=40:release=400[me{j}]")
                mixed.append(f"[me{j}]")
                nin += 1
            if vlast != "v":
                vf.append(f"[{vlast}]null[v]")
            af_tail = (f"[ak]{''.join(mixed)}amix=inputs={len(mixed) + 1}:duration=first:normalize=0,"
                       f"atrim=end={total:.3f}[a]")

        temporary = work / "assembled.mp4"
        subprocess.run(
            ["ffmpeg", "-v", "error", *inputs, "-filter_complex", ";".join(vf + af + whoosh + [af_tail]),
             "-map", "[v]", "-map", "[a]", "-r", str(FPS), "-c:v", "libx264", "-crf", "17", "-preset", "medium",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(temporary)],
            check=True, cwd=work,
        )
        if frame_count(temporary) != sum(counts):
            raise ValueError(f"Output has {frame_count(temporary)} frames, expected {sum(counts)}.")
        temporary.rename(output)
    print(f"{output}\n{sum(counts)} frames at 30 fps ({sum(counts) / 30:.2f} seconds)")


def self_test() -> None:
    kai = Path(r"C:\Users\D1\Downloads\GTA 6\Kai Cenat - Mandy finds out about the prison wife (YouTube).mp4")
    test = ROOT / "out" / "test" / "assemble"
    test.mkdir(parents=True, exist_ok=True)
    slug = "_assemble_test"
    data, plans = ROOT / "src" / "data" / f"{slug}.json", ROOT / "videos" / slug
    try:
        body = test / "body.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=s=1080x1920:r=30:d=10",
                        "-f", "lavfi", "-i", "sine=f=440:r=48000:d=10", "-ac", "2", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", str(body)], check=True)
        data.parent.mkdir(exist_ok=True)
        data.write_text(json.dumps({"captions": [{"from": 0}, {"from": 100}, {"from": 200}]}))
        plans.mkdir(exist_ok=True)
        inserts = [{"after_phrase": 0, "file": str(kai), "in": 5.0, "out": 7.0, "bleeps": [[5.5, 6.0]],
                    "credit": "Kai Cenat", "handle": "twitch.tv/kaicenat"},
                   {"after_phrase": 1, "file": str(kai), "in": 20.5, "out": 23.0,
                    "credit": "Kai Cenat", "handle": "twitch.tv/kaicenat"}]
        (plans / "plan.json").write_text(json.dumps({"inserts": inserts}))
        out = test / "out.mp4"
        build(slug, body, out)
        assert frame_count(out) == 300 + 60 + 75, frame_count(out)
        for name, f in (("j1", 101), ("j2", 100 + 60 + 100 + 1), ("end", 434)):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-vf",
                            f"select=eq(n\\,{f}),scale=540:-1", "-frames:v", "1", str(test / f"{name}.png")], check=True)
        xqc = Path(r"C:\Users\D1\Downloads\GTA 6\xQc - Mandy confrontation (YouTube).mp4")
        hor = Path(r"C:\Users\D1\Downloads\autoclipper\clips_crowd\xqc\1970-01-01\xqc_063820_x0.0_horizontal.mp4")
        pop = {"after_phrase": 1, "vertical": str(xqc), "horizontal": str(hor), "v_in": 21.0, "v_out": 22.8,
               "h_in": 21.0, "credit": "XQC", "handle": "twitch.tv/xqc", "bleeps": [[21.5, 21.7]]}
        (plans / "plan.json").write_text(json.dumps({"pops": [pop]}))
        out2 = test / "pop.mp4"
        build(slug, body, out2)
        assert frame_count(out2) == 300 + 54, frame_count(out2)
        for name, f in (("pop1", 200 + 1), ("pop2", 200 + 20)):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out2), "-vf",
                            f"select=eq(n\\,{f}),scale=540:-1", "-frames:v", "1", str(test / f"{name}.png")], check=True)
        print(f"frames OK ({frame_count(out)}, pop {frame_count(out2)}); stills in {test}")
    finally:
        if "--keep" not in sys.argv:
            shutil.rmtree(test, ignore_errors=True)
            data.unlink(missing_ok=True)
            shutil.rmtree(plans, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", nargs="?")
    parser.add_argument("body", nargs="?", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--keep", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not (args.slug and args.body and args.output):
        parser.error("slug, body and --output are required.")
    output = args.output.resolve()
    if output.suffix.lower() != ".mp4" or output.exists():
        parser.error("Choose a new .mp4 output path.")
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        build(args.slug, args.body.resolve(), output)
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError) as exc:
        parser.exit(1, f"Assemble failed. {exc}\n")


if __name__ == "__main__":
    main()
