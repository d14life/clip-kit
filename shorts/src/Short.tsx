import React from "react";
import { AbsoluteFill, Audio, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame } from "remotion";
import { ACCENT, INK } from "./types";
import { Mocks } from "./components/Mocks";
import { Captions, SubTag, TopBlock } from "./components/Text";
import { Desktop, Shot, Timeline } from "./types";

/** One shot: the pre-cut 9:16 clip with a slow push-in so no frame is ever static. */
const ShotClip: React.FC<{ shot: Shot }> = ({ shot }) => {
  const frame = useCurrentFrame();
  const z = shot.zoom * interpolate(frame, [0, shot.dur], [1.0, 1.05]);
  return (
    <AbsoluteFill style={{ transform: `scale(${z})` }}>
      <OffthreadVideo src={staticFile(shot.file)} startFrom={shot.start} muted={!shot.vol} volume={shot.vol} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    </AbsoluteFill>
  );
};

const vid = (shot: Shot, style: React.CSSProperties, audible = false) => (
  <OffthreadVideo src={staticFile(shot.file)} startFrom={shot.start} muted={!(audible && shot.vol)} volume={shot.vol} style={style} />
);

/** Layout A, used for per-shot desktop shots when the timeline sets no `desktop` options. */
const DESKTOP_A: Desktop = { top: 656, bg: "blur", capTop: 1330 };

/** Desktop layout: the 16:9 source whole at 1080x608 (nothing cropped), on a blurred copy or a solid colour. */
const DesktopClip: React.FC<{ shot: Shot; d: Desktop }> = ({ shot, d }) => (
  <AbsoluteFill>
    {d.bg === "blur" ? (
      <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
        {vid(shot, { width: "100%", height: "100%", objectFit: "cover", transform: "scale(1.15)", filter: "blur(38px) brightness(0.38) saturate(1.2)" })}
      </AbsoluteFill>
    ) : (
      <AbsoluteFill style={{ background: "#0e0b14" }} />
    )}
    <div style={{ position: "absolute", left: 0, top: d.top, width: 1080, height: 608, boxShadow: "0 0 60px rgba(0,0,0,0.6)" }}>
      {vid(shot, { width: 1080, height: 608, objectFit: "fill" }, true)}
    </div>
    {d.camTop !== undefined && (
      <div style={{ position: "absolute", left: 270, top: d.camTop, width: 540, height: 302, overflow: "hidden", borderRadius: 26, border: `7px solid ${INK}`, outline: `5px solid ${ACCENT}`, boxShadow: "0 14px 40px rgba(0,0,0,0.6)" }}>
        {/* the streamer cam is the top-left 480x268 of the 1920x1080 source */}
        <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: "scale(1.125)", transformOrigin: "0 0" }}>
          {vid(shot, { width: 1920, height: 1080 })}
        </div>
      </div>
    )}
  </AbsoluteFill>
);

export const Short: React.FC<{ tl: Timeline }> = ({ tl }) => {
  const frame = useCurrentFrame();
  const item = tl.items.find((i) => frame >= i.from && frame < i.to);
  const ask = frame >= tl.askFrom;
  const d = tl.layout === "desktop" ? tl.desktop : undefined;
  // per-shot desktop layout (shot.layout) inside an otherwise cropped Short
  const cur = tl.shots.find((s) => frame >= s.from && frame < s.from + s.dur);
  const dNow = d ?? (cur?.layout === "desktop" ? tl.desktop ?? DESKTOP_A : undefined);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {tl.shots.map((s, i) => (
        <Sequence key={i} from={s.from} durationInFrames={s.dur}>
          {d || s.layout === "desktop" ? <DesktopClip shot={s} d={d ?? tl.desktop ?? DESKTOP_A} /> : <ShotClip shot={s} />}
        </Sequence>
      ))}
      {/* legibility: darken behind the caption band */}
      {!dNow && <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0) 58%, rgba(0,0,0,0.45) 74%, rgba(0,0,0,0.15) 100%)" }} />}
      <TopBlock tl={tl} item={ask ? undefined : item} />
      <Mocks mocks={tl.mocks} />
      {tl.earlySubFrom !== undefined && (
        <Sequence from={tl.earlySubFrom} durationInFrames={72}>
          <SubTag from={0} cta={tl.cta} line={tl.ctaLine} />
        </Sequence>
      )}
      <SubTag from={tl.subFrom} cta={tl.cta} line={tl.ctaLine} />
      <Captions caps={tl.captions} top={dNow?.capTop} />
      <Audio src={staticFile(tl.voice ?? `audio/${tl.slug}/voice.wav`)} />
      {tl.bed !== false && (
        <Audio
          src={staticFile("audio/bed.wav")}
          volume={(f) => 0.2 * interpolate(f, [0, 3, tl.frames - 3, tl.frames], [0.6, 1, 1, 0.6], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}
        />
      )}
      {tl.sfx.map((s, i) => (
        <Sequence key={i} from={s.from}>
          <Audio src={staticFile(`sfx/${s.name}.wav`)} volume={s.vol * 0.5} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
