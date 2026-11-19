# Remotion edit: real snippets from 24FRAME `src/Final.tsx`

Full source: `gh repo clone YOUR_GITHUB_USER/24frame-reel -- -b hooks` → `src/Final.tsx`, `src/Root.tsx`, `package.json`.

Remotion 4.0.543 (`remotion`, `@remotion/cli`, `@remotion/transitions`, `@remotion/motion-blur`,
`@remotion/google-fonts`), React 19. Clips live in `public/final/<clip>-g.mp4` (graded).

## Compositions (Root.tsx): one component, three outputs
```tsx
<Composition id="Final"     component={Final} durationInFrames={FINAL_FRAMES} fps={30} width={1080} height={1920} defaultProps={{vo: false}} />
<Composition id="FinalVO"   component={Final} durationInFrames={FINAL_FRAMES} fps={30} width={1080} height={1920} defaultProps={{vo: true}} />
<Composition id="FinalLoop" component={Final} durationInFrames={LOOP_FRAMES}  fps={30} width={1080} height={1920} defaultProps={{vo: false, loop: true}} />
```

## Beat grid + clip table
```tsx
export const SCENE_STARTS = [0, 120, 270, 495, 615, 1005, 1125]; // all multiples of 15 f (120 BPM)
type K = 'cut' | 'zoom' | 'whip';
// f = file, s = src start, r = playback rate, a/b = global in/out, n = src frames, t = transition in, sc = scene range
const CLIPS: Clip[] = [
  {f: 'mx5-scene1v4', s: 0, r: 1, a: 0, b: 120, n: 113, t: 'cut', sc: S1},
  {f: 'scene2', s: 0, r: 0.84, a: 120, b: 270, n: 126, t: 'zoom', N: 8, sc: S2, fit: {k: 0.68, dy: 250, dur: 15}},
  // ...
];
```
Comment every row with WHY and WHO decided (date + Damir's words). Those comments were the only
way later sessions knew which clip was the locked one.

## Clip player: rate, freeze on the last frame, optional mid-freeze
```tsx
const Vid: React.FC<{f: string; file?: string; start: number; r: number; n?: number; hl?: [number, number]}> = ({hl, ...p}) => {
  const lf = useCurrentFrame();
  if (!hl) return <VidIn {...p} />;
  if (lf < hl[0]) return <VidIn {...p} />;
  if (lf < hl[0] + hl[1]) return <Freeze frame={hl[0]}><VidIn {...p} /></Freeze>;
  return <Sequence from={hl[1]} layout="none"><VidIn {...p} /></Sequence>;
};
const VidIn: React.FC<{f: string; file?: string; start: number; r: number; n?: number}> = ({f, file, start, r, n}) => {
  const lf = useCurrentFrame();
  const last = n ? Math.floor((n - 1 - start) / r) : Infinity;
  const v = <OffthreadVideo src={staticFile(file ?? `final/${f}-g.mp4`)} muted startFrom={start} playbackRate={r} style={{width: 1080, height: 1920}} />;
  return lf > last ? <Freeze frame={last}>{v}</Freeze> : v;
};
```
Beware: a `Freeze` on a hold is exactly what Damir calls "static / looks AI". Prefer slowing the
clip (`r < 1`) or a slow camera drift over the hold.

## House easing and the pop
```tsx
const ease = Easing.bezier(0.65, 0, 0.35, 1);   // cubic in-out
const easeOut = Easing.bezier(0.2, 0.8, 0.2, 1);
const cl = (v: number) => Math.max(0, Math.min(1, v));
// ~6 % overshoot
const pop = (g: number, at: number) => (g < at ? 0 : spring({frame: g - at, fps: 30, config: {damping: 12, stiffness: 150, mass: 0.8}}));
```

## Render commands that worked
```bash
npm run studio                                   # preview
# chunked, muted (one-piece render hit ENOSPC)
npx remotion render src/index.ts Final out/vN/p1.mp4 --frames=0-179 --muted --props '{"vo":true}'
# ... p2 = 180-359, etc.; then one audio-only pass, concat the parts with ffmpeg -c copy and mux the audio
npx remotion still src/index.ts FinalVO out/cover.png --frame=45 --image-format=png   # cover frame for the brief
```
