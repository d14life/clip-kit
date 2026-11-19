// Middle-frame still of every phrase at scale 0.25 (same API `remotion still` uses, one bundle for all).
// Run: node tools/scripts/preview_stills.mjs <slug>  -> out/preview/<slug>/pNN.png
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import fs from "node:fs";
import path from "node:path";
const slug = process.argv[2];
const tl = JSON.parse(fs.readFileSync(`src/data/${slug}.json`, "utf8"));
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts"), publicDir: path.resolve("public") });
const comp = await selectComposition({ serveUrl, id: "short", inputProps: tl });
const dir = `out/preview/${slug}`;
fs.mkdirSync(dir, { recursive: true });
for (const [i, c] of tl.captions.entries()) {
  const frame = Math.min(Math.floor((c.from + c.to) / 2), comp.durationInFrames - 1);
  await renderStill({ composition: comp, serveUrl, inputProps: tl, frame, scale: 0.25, output: `${dir}/p${String(i + 1).padStart(2, "0")}.png` });
  console.log(slug, i + 1, frame);
}
