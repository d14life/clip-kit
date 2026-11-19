"""Print mosaic-active spans from marks.json: start-end, max box px (rects merged exactly as render does)."""
import json, sys, vision_mosaic as vm
marks = json.load(open(sys.argv[1])); fps = 30.0
spans, cur = [], None
for i in range(int(61 * fps)):
    t = i / fps
    rs = vm.rects(vm.active_cells(marks, t))
    if rs:
        box = max((round((c1 + 1 - c0) * vm.CW), round((r1 + 1 - r0) * vm.CH)) for c0, r0, c1, r1 in rs)
        cells = vm.active_cells(marks, t)
        if cur and abs(cur[1] - (t - 1 / fps)) < 1e-6:
            cur[1] = t; cur[3].update(cells)
            if box[0] * box[1] > cur[2][0] * cur[2][1]: cur[2] = box
        else:
            cur = [t, t, box, set(cells)]; spans.append(cur)
for s, e, (w, h), cells in spans:
    print(f"{s:6.2f}-{e:6.2f}  max box {w}x{h}px  cells {len(cells)}")
