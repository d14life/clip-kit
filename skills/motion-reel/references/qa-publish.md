# QA, patching and publishing: real snippets from 24FRAME

## Splice a re-rendered frame range into the last good cut (copy: `scripts/splice2.sh` here; it was never committed to the repo)
Re-encodes only the GOP span around the fix and stream-copies the rest, so a small fix needs no full render.
```bash
set -e
# usage: splice2.sh SRC RENDER RENDER_FIRST_G CH_A CH_B BLK_A BLK_B OUT
V=$1; R=$2; RF=$3; A=$4; B=$5; BA=$6; BB=$7; OUT=$8
X="-c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -profile:v high -color_primaries bt709 -color_trc iec61966-2-1 -color_range tv"
ffmpeg -v error -y -i $V -i $R -filter_complex "[0:v]trim=start_frame=$BA:end_frame=$A,setpts=PTS-STARTPTS[a];[1:v]trim=start_frame=$((A-RF)):end_frame=$((B+1-RF)),setpts=PTS-STARTPTS[b];[0:v]trim=start_frame=$((B+1)):end_frame=$((BB+1)),setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0,fps=30[v]" -map "[v]" $X mid.mp4
ffmpeg -v error -y -i $V -map 0:v -c copy -frames:v $BA head.mp4
ffmpeg -v error -y -ss $(python3 -c "print(($BB+1)/30)") -i $V -map 0:v -c copy tail.mp4
for p in head mid tail; do ffmpeg -v error -y -i $p.mp4 -c copy -bsf:v h264_mp4toannexb $p.ts; done
ffmpeg -v error -y -i "concat:head.ts|mid.ts|tail.ts" -i $V -map 0:v -map 1:a -c copy -r 30 $OUT
for p in head mid tail $OUT; do echo $p $(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 ${p%.mp4}.mp4); done
ffmpeg -v error -i $OUT -f null - && echo decode-clean
```
BLK_A/BLK_B must sit on keyframes (GOP starts) of SRC.

## Seam / loop check: mean abs diff of two frames (idea from repo `scripts/loop_diff.py`)
```python
import numpy as np; from PIL import Image
L = lambda p: np.asarray(Image.open(p).convert('RGB')).astype(float)
def d(a, b): x = np.abs(L(a) - L(b)); return 'mean %.2f  max %d' % (x.mean(), x.max())
```
Report it for every seam (shot N END vs N+1 START) and for the loop (last frame vs reel frame 0).
24FRAME also checked "never still" holds: neighbour-frame difference must stay above 0 on every hold frame.

## Delivery checks (paste the output)
```bash
df -h ~                                   # before any render; ENOSPC killed a cut and an agent hid it
ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames,width,height,r_frame_rate -of csv=p=0 out.mp4
ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 out.mp4    # aac
ffmpeg -i out.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -12                            # ≈ -21 LUFS, peak ≤ -1 dBFS
ffmpeg -v error -i out.mp4 -vf "select='not(mod(n\,30))',scale=180:-1,tile=7x6" -frames:v 1 sheet.png   # contact sheet
```
Use `set -o pipefail` in any script that pipes a render into `tail`/`tee`.

## Publish for his phone (public demo repo, GitHub Pages)
- Repo `<owner>/<name>-demo`, Pages on main / root, a bare `index.html` with `<video controls playsinline>` + README.
- New cut = `<name>.mp4`; previous kept as `<name>-vN.mp4`; keyframes in `keyframes/`.
- After push: wait for the Pages run (`gh run watch`), then `curl -sI` each file: 200 and
  content-length equal to the local size. Every machine that publishes needs Write access (the PC got 403).
- Also `open -a "QuickTime Player" out.mp4` on the Mac.
