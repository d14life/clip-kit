import React from "react";
import { AbsoluteFill, Audio, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT, Heavy } from "./components/Text";
import { INK, SUNSET_WIDE } from "./types";

/**
 * Channel outro, 4 s, 1080x1920. Vice City sunset drawn in code (no Rockstar art):
 * six wanted-level stars light up, the SIXSTARS wordmark lands, then three call-to-action plates.
 * `hero` makes one platform's plate the big pulsing one: use the platform the file is uploaded to.
 * Everything sits inside y 200-1560 and x 110-970 so TikTok's and Instagram's buttons do not cover it.
 */
/** `voice`: optional spoken call to action, a file under public/ (e.g. "audio/outro/youtube.wav"), played from frame 12. */
export type OutroProps = { hero?: "youtube" | "instagram" | "tiktok" | "all"; handle?: string; line?: string; voice?: string };
export const OUTRO_FRAMES = 120;

const STAR = "M50 3 L61.8 36.2 L97 37.3 L69 58.8 L79 92.7 L50 72.5 L21 92.7 L31 58.8 L3 37.3 L38.2 36.2 Z";

export const Star: React.FC<{ i: number }> = ({ i }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const on = 6 + i * 4;
  const s = spring({ frame: frame - on, fps, config: { damping: 7, stiffness: 300, mass: 0.5 } });
  const lit = frame >= on;
  // wanted-level flash: all six blink twice once the last one is lit
  const blink = frame >= 32 && frame < 46 && Math.floor((frame - 32) / 3.5) % 2 === 1;
  const bright = lit && !blink;
  return (
    <svg width={118} height={118} viewBox="0 0 100 100" style={{ margin: "0 4px", transform: `scale(${lit ? 0.6 + 0.4 * s : 0.9}) rotate(${lit ? (1 - s) * -40 : 0}deg)`, filter: bright ? "drop-shadow(0 0 16px rgba(255,170,60,0.95)) drop-shadow(0 6px 0 #0b0b0b)" : "drop-shadow(0 6px 0 #0b0b0b)" }}>
      <defs>
        <linearGradient id={`sg${i}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#FFF3A6" />
          <stop offset="0.5" stopColor="#FFB23D" />
          <stop offset="1" stopColor="#FF4FA3" />
        </linearGradient>
      </defs>
      <path d={STAR} fill={bright ? `url(#sg${i})` : "#2a1c3d"} stroke={INK} strokeWidth={7} strokeLinejoin="round" />
    </svg>
  );
};

export const Palm: React.FC<{ x: number; y: number; h: number; flip?: boolean; sway: number }> = ({ x, y, h, flip, sway }) => {
  const fronds = [-150, -115, -80, -45, -10, 25, 60];
  return (
    <svg width={h} height={h * 1.25} viewBox="0 0 400 500" style={{ position: "absolute", left: x, top: y, transform: `${flip ? "scaleX(-1) " : ""}rotate(${sway}deg)`, transformOrigin: "50% 100%" }}>
      <path d="M205 500 Q 170 330 215 150" stroke="#12061f" strokeWidth={20} fill="none" strokeLinecap="round" />
      {fronds.map((a, k) => (
        <path key={k} d="M0 0 Q 95 -75 205 18 Q 150 0 120 6 Q 95 -22 0 0 Z" fill="#12061f" transform={`translate(215 150) rotate(${a}) scale(${0.92 + (k % 3) * 0.08})`} />
      ))}
      <circle cx={215} cy={152} r={15} fill="#12061f" />
    </svg>
  );
};

const Icon: React.FC<{ kind: "youtube" | "instagram" | "tiktok"; size: number }> = ({ kind, size }) => {
  if (kind === "youtube")
    return (
      <svg width={size} height={size} viewBox="0 0 100 100">
        <rect x={4} y={18} width={92} height={64} rx={18} fill="#FF2E2E" stroke={INK} strokeWidth={6} />
        <path d="M41 35 L66 50 L41 65 Z" fill="#fff" />
      </svg>
    );
  if (kind === "instagram")
    return (
      <svg width={size} height={size} viewBox="0 0 100 100">
        <defs>
          <linearGradient id="igg" x1="0" y1="1" x2="1" y2="0">
            <stop offset="0" stopColor="#FFD23F" />
            <stop offset="0.5" stopColor="#FF4FA3" />
            <stop offset="1" stopColor="#9B4DFF" />
          </linearGradient>
        </defs>
        <rect x={8} y={8} width={84} height={84} rx={24} fill="url(#igg)" stroke={INK} strokeWidth={6} />
        <circle cx={50} cy={50} r={19} fill="none" stroke="#fff" strokeWidth={8} />
        <circle cx={73} cy={27} r={6} fill="#fff" />
      </svg>
    );
  const note = "M56 14 L56 62 A17 17 0 1 1 42 45 L42 58 A5.5 5.5 0 1 0 44 62 L44 14 Z M56 14 Q 60 34 80 36 L80 48 Q 64 47 56 38 Z";
  return (
    <svg width={size} height={size} viewBox="0 0 100 100">
      <rect x={8} y={8} width={84} height={84} rx={22} fill="#0b0b0b" stroke="#fff" strokeWidth={4} />
      <path d={note} fill="#25F4EE" transform="translate(-3 -2)" />
      <path d={note} fill="#FE2C55" transform="translate(3 2)" />
      <path d={note} fill="#fff" />
    </svg>
  );
};

export const ROWS: { kind: "youtube" | "instagram" | "tiktok"; verb: string; where: string }[] = [
  { kind: "youtube", verb: "SUBSCRIBE", where: "ON YOUTUBE" },
  { kind: "instagram", verb: "FOLLOW", where: "ON INSTAGRAM" },
  { kind: "tiktok", verb: "FOLLOW", where: "ON TIKTOK" },
];

export const Plate: React.FC<{ row: (typeof ROWS)[number]; i: number; hero: boolean }> = ({ row, i, hero }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const from = 44 + i * 8;
  const t = frame - from;
  const s = spring({ frame: t, fps, config: { damping: 12, stiffness: 190, mass: 0.7 } });
  const dir = i % 2 === 0 ? -1 : 1;
  const x = interpolate(s, [0, 1], [dir * 1100, 0]);
  const pulse = hero ? 1 + 0.03 * Math.sin(Math.max(0, t - 12) / 4) : 1;
  const h = hero ? 236 : 184;
  // a sheen sweeps across each plate once it has landed
  const sheen = interpolate(t, [10, 30], [-40, 140], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ display: "flex", justifyContent: "center", margin: hero ? "26px 0" : "20px 0", opacity: t < 0 ? 0 : 1, transform: `translateX(${x}px) scale(${pulse})` }}>
      <div
        style={{
          position: "relative",
          overflow: "hidden",
          width: hero ? 860 : 780,
          height: h,
          transform: "skewX(-9deg)",
          borderRadius: 26,
          border: `7px solid ${INK}`,
          background: hero ? SUNSET_WIDE : "linear-gradient(90deg, rgba(34,14,58,0.94) 0%, rgba(70,22,92,0.94) 100%)",
          boxShadow: hero ? "0 10px 0 #0b0b0b, 0 0 60px rgba(255,79,163,0.75), 0 24px 44px rgba(0,0,0,0.6)" : "0 8px 0 #0b0b0b, 0 0 0 3px rgba(255,79,163,0.55) inset, 0 18px 34px rgba(0,0,0,0.55)",
        }}
      >
        <div style={{ position: "absolute", top: 0, bottom: 0, left: `${sheen}%`, width: "22%", background: "linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.5) 50%, rgba(255,255,255,0) 100%)" }} />
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", padding: "0 34px", transform: "skewX(9deg)" }}>
          <Icon kind={row.kind} size={hero ? 156 : 122} />
          <div style={{ marginLeft: 26, lineHeight: 1 }}>
            <div style={{ fontFamily: FONT, fontStyle: "italic", fontWeight: 900, fontSize: hero ? 96 : 76, color: hero ? INK : "#fff", letterSpacing: "0.005em" }}>{row.verb}</div>
            <div style={{ fontFamily: FONT, fontStyle: "italic", fontWeight: 900, fontSize: hero ? 40 : 34, color: hero ? "rgba(11,11,11,0.78)" : "#FFB86B", marginTop: 6, letterSpacing: "0.06em" }}>{row.where}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export const Outro: React.FC<OutroProps> = ({ hero = "all", handle, line = "SEE YOU IN VICE CITY", voice }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const push = interpolate(frame, [0, OUTRO_FRAMES], [1.0, 1.06]);
  const sunY = interpolate(frame, [0, OUTRO_FRAMES], [70, 0]);
  const sway = Math.sin(frame / 14) * 1.6;
  const word = spring({ frame: frame - 28, fps, config: { damping: 9, stiffness: 240, mass: 0.7 } });
  const flash = interpolate(frame, [28, 31, 40], [0, 0.32, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const lineIn = interpolate(frame, [72, 82], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fadeIn = interpolate(frame, [0, 5], [0, 1], { extrapolateRight: "clamp" });
  // put the hero platform's plate first so it is the one the eye lands on
  const rows = hero === "all" ? ROWS : [...ROWS.filter((r) => r.kind === hero), ...ROWS.filter((r) => r.kind !== hero)];
  return (
    <AbsoluteFill style={{ background: "#0d0418", overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: `scale(${push})`, opacity: fadeIn }}>
        {/* sky */}
        <AbsoluteFill style={{ background: "linear-gradient(180deg, #1a0b3d 0%, #5b1a8a 22%, #c7307f 41%, #ff6a3d 55%, #ffc34a 63%, #2a0f3e 63.2%, #0d0418 100%)" }} />
        {/* striped sun */}
        <div style={{ position: "absolute", left: 540 - 400, top: 470 + sunY, width: 800, height: 800, borderRadius: "50%", background: "linear-gradient(180deg, #FFF09A 0%, #FFB23D 38%, #FF4FA3 78%, #C92C9A 100%)", boxShadow: "0 0 160px rgba(255,120,80,0.75)", WebkitMaskImage: "repeating-linear-gradient(180deg, #000 0px, #000 46px, transparent 46px, transparent 60px)", maskImage: "repeating-linear-gradient(180deg, #000 0px, #000 46px, transparent 46px, transparent 60px)" }} />
        {/* skyline blocks on the horizon */}
        <svg width={1080} height={300} viewBox="0 0 1080 300" style={{ position: "absolute", left: 0, top: 912 }}>
          <path d="M0 300 V230 H60 V170 H110 V210 H170 V120 H215 V200 H290 V150 H330 V90 H372 V190 H450 V230 H640 V180 H700 V110 H742 V60 H786 V160 H850 V205 H920 V140 H968 V190 H1030 V225 H1080 V300 Z" fill="#160828" />
        </svg>
        {/* water with neon reflections */}
        <div style={{ position: "absolute", left: 0, right: 0, top: 1212, bottom: 0, background: "linear-gradient(180deg, #2a0f3e 0%, #0d0418 70%)" }} />
        {[0, 1, 2, 3, 4, 5, 6].map((k) => {
          const w = 620 - k * 70 + 40 * Math.sin(frame / 9 + k);
          return <div key={k} style={{ position: "absolute", left: 540 - w / 2, top: 1240 + k * 46, width: w, height: 9, borderRadius: 5, background: "linear-gradient(90deg, rgba(255,79,163,0) 0%, rgba(255,150,80,0.75) 50%, rgba(255,79,163,0) 100%)", opacity: 0.8 - k * 0.09 }} />;
        })}
        <Palm x={-120} y={520} h={560} sway={sway} />
        <Palm x={690} y={440} h={640} flip sway={-sway * 0.8} />
        <Palm x={-40} y={760} h={360} sway={sway * 1.3} />
      </AbsoluteFill>
      {/* darken so the type reads */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(8,2,18,0.55) 0%, rgba(8,2,18,0.25) 30%, rgba(8,2,18,0.5) 55%, rgba(8,2,18,0.82) 100%)" }} />
      {/* scanlines */}
      <AbsoluteFill style={{ background: "repeating-linear-gradient(180deg, rgba(0,0,0,0) 0px, rgba(0,0,0,0) 4px, rgba(0,0,0,0.13) 4px, rgba(0,0,0,0.13) 6px)", mixBlendMode: "multiply" }} />

      <div style={{ position: "absolute", left: 0, right: 0, top: 236, textAlign: "center" }}>
        <div style={{ display: "flex", justifyContent: "center" }}>
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <Star key={i} i={i} />
          ))}
        </div>
        <div style={{ marginTop: 18, opacity: frame >= 28 ? 1 : 0, transform: `scale(${interpolate(word, [0, 1], [2.1, 1])}) rotate(-3deg)` }}>
          <Heavy size={168} color="#FFC83D" stroke={16}>
            SIXSTARS
          </Heavy>
        </div>
        {handle ? (
          <div style={{ marginTop: 2, opacity: frame >= 34 ? 1 : 0 }}>
            <Heavy size={46} stroke={10}>
              {handle}
            </Heavy>
          </div>
        ) : null}
      </div>

      <div style={{ position: "absolute", left: 0, right: 0, top: handle ? 770 : 730 }}>
        {rows.map((r, i) => (
          <Plate key={r.kind} row={r} i={i} hero={hero === r.kind} />
        ))}
      </div>

      <div style={{ position: "absolute", left: 0, right: 0, top: 1508, textAlign: "center", opacity: lineIn, transform: `translateY(${(1 - lineIn) * 24}px)` }}>
        <Heavy size={50} stroke={10}>
          {line}
        </Heavy>
      </div>

      <AbsoluteFill style={{ background: "#fff", opacity: flash, mixBlendMode: "screen" }} />

      <Audio src={staticFile("audio/bed.wav")} volume={(f) => 0.22 * interpolate(f, [0, 6, OUTRO_FRAMES - 14, OUTRO_FRAMES], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <Sequence key={i} from={6 + i * 4}>
          <Audio src={staticFile("sfx/tick.wav")} volume={0.45} />
        </Sequence>
      ))}
      <Sequence from={28}>
        <Audio src={staticFile("sfx/hit.wav")} volume={0.6} />
      </Sequence>
      {[0, 1, 2].map((i) => (
        <Sequence key={i} from={44 + i * 8}>
          <Audio src={staticFile("sfx/whoosh.wav")} volume={0.4} />
        </Sequence>
      ))}
      <Sequence from={72}>
        <Audio src={staticFile("sfx/pop.wav")} volume={0.4} />
      </Sequence>
      {voice ? (
        <Sequence from={12}>
          <Audio src={staticFile(voice)} />
        </Sequence>
      ) : null}
    </AbsoluteFill>
  );
};
