# Nudity detection options for GTA 6 gameplay (1080x608, 60 fps, RX 6650 XT, onnxruntime CPU/DirectML)

Research only, nothing installed or run. Web research on 2026-11-19. Facts marked (verified) came from a model card or
repo page. Speeds are my ESTIMATES from model size, not measurements. Nobody publishes benchmarks on game footage.

**Main finding: I found NO public model trained on game or 3D-rendered nudity.** The only stylized-domain model is
deepghs (anime). Every other model is photo-trained, so every failure you see is domain shift. Whatever we pick, we
must test it on ~100 of our own labelled frames.

## Ranking (best first for our case)

### 1. Pipeline: person gate -> upscaled crops -> UNION of detectors (recommended)
Do not rely on one model. Steps:
1. YOLO person/seg model (YOLO11n/s-seg or YOLOv8n-seg, COCO, ONNX, DirectML ok) on the full frame at 640. Gives a
   box (or mask) for every NPC, including small ones.
2. Crop each person with padding, upscale so the person is ~640 px tall (this is what fixes "small or far away").
3. Run NudeNet 640m + deepghs censor detector (+ optionally EraX) on the crop. Union the boxes.
4. Rule: if any exposed-class hit, or a skin-ratio test (see #9) says "mostly skin", mosaic the person's torso+hip band
   (e.g. 25%-65% of person-box height) instead of trusting the tight box.
5. Reject false hits: an "exposed buttocks" box is only accepted if it sits inside a person box, and only if 2 of
   3 consecutive checked frames agree (kills the clothed-shoulder case).
6. Run the detectors at 4-6 fps, track person boxes between checks and carry the mosaic forward (60 fps is not needed
   for detection). Cost estimate: person model ~15-30 ms CPU, crops ~50-150 ms each. Fine for offline clipping.
- Licenses: Ultralytics YOLO is AGPL-3.0 (fine for personal use; check if the clips are a commercial service).
  RT-DETR/YOLOX (Apache-2.0) are alternatives for the person step.
- Regions: yes (boxes/masks). Game content: person detectors work well on game humans (they are people-shaped);
  that is exactly why this gate helps.

### 2. NudeNet 640m (drop-in upgrade from 320n)
- URL: https://github.com/notAI-tech/NudeNet (v3 releases; ONNX file attached to release)
- License: AGPL-3.0 for the repo (from memory, not re-verified here); model file ~104 MB (third-party mirror
  listing, 103.5 MB LFS pointer).
- Detects regions: yes, 18 classes with boxes (verified). Based on YOLOv8m at 640x640 (verified).
- Usage (verified): `NudeDetector(model_path="640m.onnx", inference_resolution=640)`.
- 3D/game/anime: not documented; photo-trained. Expect better than 320n on small objects, still imperfect.
- CPU/DirectML: plain ONNX, works with onnxruntime-directml. Estimate 150-400 ms/frame on CPU, ~40-100 ms on DirectML.
- Maintainer says repo is lightly maintained.

### 3. deepghs anime_censor_detection (stylized-art domain)
- URL: https://huggingface.co/deepghs/anime_censor_detection
- License: MIT (verified). ONNX (verified). Sizes: v1.0_n 3.01M params (F1 0.80), v1.0_s 11.1M params (F1 0.83).
- Regions: yes, boxes, but only 3 classes: nipple_f, penis, pussy. No buttocks/breast-wide class.
- Domain: trained on drawn/anime censor data. NOT photo, NOT 3D game; stylized renders of NPCs may sit between
  the two domains, which is why it is worth adding to the union. Unverified on 3D.
- Speed: tiny, ~10-40 ms CPU at 640 (estimate). Also see imgutils (https://github.com/deepghs/imgutils) which wraps
  it plus a NudeNet ONNX.

### 4. EraX-NSFW-V1.0 (YOLO11 n/s/m)
- URL: https://huggingface.co/erax-ai/EraX-NSFW-V1.0
- License: Apache-2.0 for weights (verified), but the code path uses Ultralytics (AGPL). Needs conversion .pt -> ONNX.
- Size: yolo11m .pt ~40.5 MB, yolo11s ~19.2 MB (verified). Classes: anus, make_love, nipple, penis, vagina
  (verified). No buttocks, no breast-body, so weak for the "naked body" case.
- Trained on 31,890 private internet images, 640 px (verified). No metrics published ("coming soon"). No anime/3D claim.
- Detects regions: yes (boxes). Speed: m ~100-300 ms CPU, s about half (estimates).
- A similar file, yolo_11m_nsfw.onnx (80 MB), ships in FaceFusion's HF repo
  https://huggingface.co/facefusion/models-3.2.0 but its license is unclear (FaceFusion is OpenRAIL-AS). Avoid unless checked.

### 5. NSFW-API/NSFW_Segmentation (masks)
- URL: https://huggingface.co/NSFW-API/NSFW_Segmentation
- Real polygon MASKS (breast/areola/nipple, vagina, penis), YOLO11 s and x, .pt only (convert to ONNX yourself).
- License: not stated (verified: none on page). Private training data. Card warns of domain-shift drops. Nothing on anime/3D.
- Three separate models = three passes; the x models are heavy for CPU. Masks are nicer than boxes but the classes
  are the same narrow set. Low priority.

### 6. NSFW image classifier on person crops (verdict gate only, not regions)
- Marqo/nsfw-image-detection-384: https://huggingface.co/Marqo/nsfw-image-detection-384 - Apache-2.0, ViT-Tiny, 384 px,
  claims 98.56% on their own set. Falconsai/nsfw_image_detection: Apache-2.0, ~86M params (ViT).
- Classifies the whole crop (no regions). Photo-trained, 3D/anime behaviour unknown. Useful as a second opinion
  ("is this crop naked?") to confirm or veto a detector hit, and to trigger the torso/hip mosaic when the part
  detector found nothing. Speed: ViT-Tiny ~10-30 ms CPU per crop (estimate).
- deepghs/anime_rating (MIT, safe/r15/r18, https://huggingface.co/deepghs/anime_rating) is the anime-trained analogue.

### 7. Zero-shot: Grounding DINO / OWLv2 / Florence-2 ("naked person" boxes)
- Grounding DINO (Apache-2.0), OWLv2 (Apache-2.0), Florence-2 (MIT), YOLO-World (GPL-3.0).
- Regions: yes. They also tend to work on game art for generic objects (they were trained on web images).
- I found NO evidence that any of them reliably localises nudity; they were not trained for it and text prompts like
  "nude" are often filtered or ignored in the data. Treat as unproven.
- Speed: GDINO-T / OWLv2 / Florence-2-base are 0.2-1 B params, several seconds per frame on CPU, painful on
  DirectML. Only usable offline on a few sampled frames. Not recommended as the main detector.

### 8. SAM2 + classifier
- SAM2 (Apache-2.0) gives masks but no semantics, so it needs a classifier per mask. Large and slow without CUDA.
  Overkill: a person-seg YOLO gives the person mask already. Skip.

### 9. Skin-tone mask on the person mask (cheap helper, never alone)
- Take the person-seg mask, compute fraction of skin-coloured pixels (YCrCb or HSV range) in the torso/hip band.
  Clothed NPCs in swimwear or tight outfits and tanned skin on faces/arms will false-positive, and stylised lighting
  breaks the ranges. Use only as a signal inside pipeline #1 (e.g. skin ratio above ~0.6 in torso band plus any
  weak detector hit or classifier vote). Cost: negligible.

### 10. Models trained on games / 3D renders
- Searched HF, GitHub, Roboflow: none found. Closest are anime/art models (deepghs, Roboflow "anime nsfw
  detection" https://universe.roboflow.com/nyanners-workshop/anime-nsfw-detection, quality unknown).
- Fix if the union still misses: fine-tune YOLO11n/s (640) on our own frames. Label ~300-600 frames of GTA 6 NPCs
  (partially or fully nude, plus hard negatives: clothed shoulders, bikinis, tanned skin) in Roboflow/CVAT, start from
  NudeNet or EraX weights, export ONNX. This is the only route that targets our domain directly. Needs a GPU for
  training (RunPod is available) but inference stays CPU/DirectML.

## Why the current setup fails (likely causes)
- 320n at 320 px: a far NPC is a few dozen pixels, below the model's useful size, even on zoomed tiles.
- Photo-trained: stylised skin shading, no pores, and game lighting lower scores below the threshold.
- Shoulder -> BUTTOCKS_EXPOSED: a pure shape/colour false positive; a person-box + temporal + second-model vote removes it.

## Suggested test before committing (30 minutes)
1. Pull ~100 frames: 40 nude NPCs (near/far), 60 clothed hard negatives.
2. Score: NudeNet 320n (baseline), 640m, deepghs _s, EraX-m, and pipeline #1.
3. Pick on recall for nude NPCs first (misses are the costly failure), then false-positive rate.

## Sources
- https://github.com/notAI-tech/NudeNet (README via raw v3 branch)
- https://huggingface.co/erax-ai/EraX-NSFW-V1.0
- https://huggingface.co/deepghs/anime_censor_detection
- https://huggingface.co/NSFW-API/NSFW_Segmentation
- https://huggingface.co/Marqo/nsfw-image-detection-384
- https://huggingface.co/facefusion/models-3.2.0
- https://github.com/deepghs/imgutils
