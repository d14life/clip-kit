# Blender shots: real snippets from 24FRAME

## Setup check for any machine (from repo YOUR_GITHUB_USER/24frame-reel, branch `hooks`, `docs/BLENDER_FRIEND.md`)
1. `pgrep -x Blender` (Windows: `tasklist | findstr blender`). **Only one Blender may run.**
2. `claude mcp list`; if `blender` is missing: `claude mcp add blender -- uvx blender-mcp`, restart Claude Code.
3. Addon from github.com/ahujasid/blender-mcp (`addon.py`), enabled; N panel → BlenderMCP → "Connect to Claude".
4. Test: MCP `get_scene_info` must list the shot-1 objects (24FRAME: `Zero`, `Cam`, `Floor`, three lights).

## Send a script to the running Blender without the MCP client (copy: `scripts/bl.py` here; repo `scripts/bl.py`)
```python
#!/usr/bin/env python3
"""Send a python file to the running Blender MCP socket (no second Blender). Usage: bl.py file.py"""
import socket,json,sys
code=open(sys.argv[1]).read()
s=socket.create_connection(('localhost',9876),timeout=3000)
s.sendall(json.dumps({"type":"execute_code","params":{"code":code}}).encode())
buf=b''
while True:
    d=s.recv(65536)
    if not d: break
    buf+=d
    try: r=json.loads(buf); break
    except: pass
print(r.get('result',{}).get('result',r) if isinstance(r.get('result'),dict) else r)
```

## House style (copy from the approved shot 1 file, never overwrite it)
- EEVEE, view transform Standard.
- World colour = bg: linear (0.92158, 0.92158, 0.89627) = sRGB #F6F6F3.
- Accent material `Orange`: base (0.807, 0.065, 0.012), roughness 0.28. One accent only.
- Type: the reel's one font (`blender/fonts/InterTight-Bold.ttf`), lens 50–85 mm, facing the camera.
- The 3D lives in the objects: frosted glass, satin plastic, soft contact shadows, DoF, motion blur.

## Keyframes → approval → video
```bash
# keyframes: START / MID / END, ≤800 px, inspected and pushed, then WAIT for Damir
sips -Z 800 out/bNN/0001.png --out docs/refs/blender/bNN-START.jpg
# after his OK
ffmpeg -framerate 30 -i out/bNN/%04d.png -c:v libx264 -crf 16 -pix_fmt yuv420p -movflags +faststart public/final/bNN.mp4
ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames,width,height,r_frame_rate -of csv=p=0 public/final/bNN.mp4
```

## Report per shot (under 80 words)
shot ID · keyframe paths · defects found and fixed · seam pixel diff · commit hash · what you wait on.
Never claim a render is done without the `ls` and ffprobe output.

## Two-machine split
- Each machine has its own branch (24FRAME: `hooks` = Mac/edit, `blender`, `t3-*`) and commits only its own paths.
- gitignored media (24FRAME `public/final`, 116 MB) goes in a release:
  `gh release download assets-final -R <owner>/<repo> -p public-final.tgz && tar -xzf public-final.tgz && rm public-final.tgz`
- Give the human one paste-ready prompt per machine that says: pull, read CLAUDE.md + REQUESTS.md, do rows X/Y, report.
