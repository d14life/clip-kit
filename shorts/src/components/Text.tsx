import React from "react";
import { continueRender, delayRender, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { ACCENT, Caption, colorOf, INK, Item, SUNSET, SUNSET_WIDE, Timeline } from "../types";

// Montserrat Black Italic, loaded once from public/fonts.
const handle = delayRender("font");
const face = new FontFace("MontBI", `url(${staticFile("fonts/Montserrat-BlackItalic.ttf")})`, { weight: "900", style: "italic" });
face
  .load()
  .then((f) => {
    (document as any).fonts.add(f);
    continueRender(handle);
  })
  .catch(() => continueRender(handle));

export const FONT = "MontBI, 'Arial Black', sans-serif";

/** Heavy italic uppercase with a black stroke behind the fill. Text in ACCENT gets the sunset gradient. */
export const Heavy: React.FC<{ size: number; color?: string; stroke?: number; style?: React.CSSProperties; children: React.ReactNode }> = ({
  size,
  color = "#fff",
  stroke = 12,
  style,
  children,
}) => {
  const base: React.CSSProperties = {
    fontFamily: FONT,
    fontStyle: "italic",
    fontWeight: 900,
    fontSize: size,
    lineHeight: 1.04,
    textTransform: "uppercase",
    letterSpacing: "-0.01em",
    display: "inline-block",
  };
  const shadow = "0 6px 14px rgba(0,0,0,0.65)";
  if (color !== ACCENT) {
    return (
      <span style={{ ...base, color, WebkitTextStroke: `${stroke}px ${INK}`, paintOrder: "stroke fill", textShadow: shadow, ...style }}>{children}</span>
    );
  }
  // gradient fill: a black stroked copy underneath, the gradient-clipped copy on top
  return (
    <span style={{ position: "relative", display: "inline-block", ...style }}>
      <span style={{ ...base, color: INK, WebkitTextStroke: `${stroke}px ${INK}`, textShadow: shadow }}>{children}</span>
      <span aria-hidden style={{ ...base, position: "absolute", left: 0, right: 0, top: 0, textShadow: "none", background: SUNSET, WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent" }}>
        {children}
      </span>
    </span>
  );
};

/** On-screen subscribe tag, shown through the last item and the ask. */
export const SubTag: React.FC<{ from?: number; line?: string; cta?: string }> = ({ from, line = "FOR LAUNCH DAY TIPS", cta = "SUBSCRIBE" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (from === undefined || frame < from) return null;
  const t = frame - from;
  const s = spring({ frame: t, fps, config: { damping: 9, stiffness: 240, mass: 0.6 } });
  const pulse = 1 + 0.035 * Math.sin(t / 5);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 1130, display: "flex", flexDirection: "column", alignItems: "center", transform: `scale(${interpolate(s, [0, 1], [0.5, 1]) * pulse}) rotate(-3deg)`, opacity: Math.min(1, t / 3) }}>
      <div style={{ background: SUNSET_WIDE, border: `7px solid ${INK}`, borderRadius: 26, padding: "10px 34px 12px", boxShadow: "0 10px 0 #0b0b0b, 0 22px 40px rgba(0,0,0,0.55)" }}>
        <span style={{ fontFamily: FONT, fontStyle: "italic", fontWeight: 900, fontSize: 70, color: INK, letterSpacing: "0.01em" }}>★ {cta}</span>
      </div>
      <div style={{ marginTop: 16 }}>
        <Heavy size={38} stroke={9}>{line}</Heavy>
      </div>
    </div>
  );
};

/** Top block: channel-made "GTA VI" wordmark (drawn in code, not Rockstar's logo art) and the Short's title. */
export const TopBlock: React.FC<{ tl: Timeline; item?: Item }> = ({ tl, item }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const showTitle = !item;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 560, pointerEvents: "none" }}>
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, rgba(0,0,0,0.62) 0%, rgba(0,0,0,0.38) 55%, rgba(0,0,0,0) 100%)" }} />
      <div style={{ position: "absolute", top: 104, left: 0, right: 0, textAlign: "center" }}>
        {/* GTA-style lettering drawn in code (sunset gradient); not Rockstar's logo file. */}
        <span
          style={{
            fontFamily: FONT,
            fontStyle: "italic",
            fontWeight: 900,
            fontSize: 124,
            letterSpacing: "0.02em",
            background: "linear-gradient(180deg, #ffd36b 0%, #ff7a59 42%, #e63fa6 76%, #7a3cff 100%)",
            WebkitBackgroundClip: "text",
            color: "transparent",
            filter: "drop-shadow(0 5px 0 #0b0b0b) drop-shadow(0 -2px 0 #0b0b0b) drop-shadow(3px 0 0 #0b0b0b) drop-shadow(-3px 0 0 #0b0b0b) drop-shadow(0 0 16px rgba(0,0,0,0.6))",
          }}
        >
          GTA&nbsp;VI
        </span>
      </div>
      {showTitle ? (
        <div style={{ position: "absolute", top: 246, left: 40, right: 40, textAlign: "center" }}>
          {tl.titleWords.map((w, i) => {
            // a title word placed on frame 0 is drawn full size from frame 0 (the first frame is the cover TikTok shows)
            const s = w.f === 0 ? 1 : spring({ frame: frame - w.f, fps, config: { damping: 11, stiffness: 240, mass: 0.5 } });
            return (
              <React.Fragment key={i}>
                <Heavy size={66} color={colorOf(w.c)} stroke={11} style={{ opacity: frame >= w.f ? 1 : 0, transform: `scale(${0.6 + 0.4 * s})`, margin: "0 9px" }}>
                  {w.t}
                </Heavy>
                {w.t.endsWith("\n") ? <br /> : null}
              </React.Fragment>
            );
          })}
        </div>
      ) : (
        <ItemHeader item={item} />
      )}
    </div>
  );
};

const ItemHeader: React.FC<{ item: Item }> = ({ item }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame - item.from;
  const s = spring({ frame: t, fps, config: { damping: 9, stiffness: 260, mass: 0.6 } });
  const scale = interpolate(s, [0, 1], [1.7, 1]);
  const iconS = spring({ frame: t - 5, fps, config: { damping: 8, stiffness: 200, mass: 0.6 } });
  const long = item.label.length > 14;
  return (
    <div style={{ position: "absolute", top: 244, left: 30, right: 30, textAlign: "center", transform: `scale(${scale})`, opacity: Math.min(1, t / 2 + 0.4) }}>
      <div>
        {item.n > 0 && (
          <Heavy size={long ? 70 : 84} color={ACCENT}>
            {item.n}.
          </Heavy>
        )}
        <Heavy size={long ? 70 : 84} style={{ marginLeft: item.n > 0 ? 18 : 0 }}>
          {item.label}
        </Heavy>
      </div>
      <div style={{ fontSize: 96, lineHeight: 1.2, marginTop: 6, transform: `scale(${iconS})`, filter: "drop-shadow(0 6px 10px rgba(0,0,0,0.6))" }}>{item.icon}</div>
    </div>
  );
};

/** Captions: each word appears on its own syllable; one key word per phrase is coloured and pops. */
export const Captions: React.FC<{ caps: Caption[]; top?: number }> = ({ caps, top }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const full = caps.find((c) => frame >= c.from && frame < c.to);
  if (!full) return null;
  // Long sentences: show word-timed chunks (<= 30 chars, two lines) at the normal caption size instead of shrinking the font.
  let cap = full;
  const len = (ws: typeof full.words) => ws.map((w) => w.t).join(" ").length;
  if (len(full.words) > 30 && !full.words.every((w) => w.f === full.words[0].f)) {
    const chunks: (typeof full.words)[] = [[]];
    for (const w of full.words) {
      const cur = chunks[chunks.length - 1];
      if (cur.length && len([...cur, w]) > 30) chunks.push([w]);
      else cur.push(w);
    }
    const started = chunks.filter((c) => c[0].f <= frame);
    cap = { ...full, words: started.length ? started[started.length - 1] : chunks[0] };
  }
  // max 3 words a line, 2 lines
  const lines: (typeof cap.words)[] = [];
  // one line when it fits (about 15 characters), otherwise two balanced lines
  const total = cap.words.map((w) => w.t).join(" ").length;
  const instant = cap.words.length > 4 && cap.words.every((w) => w.f === cap.words[0].f);
  if (total <= 15 || cap.words.length === 1) {
    lines.push(cap.words);
  } else if (instant) {
    // the hook: whole sentence at once, three balanced lines so it can be big
    const target = total / 3;
    let cur: typeof cap.words = [];
    for (const w of cap.words) {
      const len = cur.map((x) => x.t).join(" ").length;
      if (cur.length && lines.length < 2 && len + w.t.length / 2 > target) {
        lines.push(cur);
        cur = [];
      }
      cur.push(w);
    }
    lines.push(cur);
  } else {
    let best = 1;
    let bestDiff = Infinity;
    for (let k = 1; k < cap.words.length; k++) {
      const l = cap.words.slice(0, k).map((w) => w.t).join(" ").length;
      const d = Math.abs(l - (total - l - 1));
      if (d < bestDiff) {
        bestDiff = d;
        best = k;
      }
    }
    lines.push(cap.words.slice(0, best), cap.words.slice(best));
  }
  const chars = Math.max(...lines.map((l) => l.map((w) => w.t).join(" ").length));
  // The words are inline-blocks with no text space between them, so the gap is all margin. In the hook the
  // margin used to be a fixed 12 px, which the 12 px stroke and the key word's pop swallowed ("IGNORLUCIA").
  // Now the gap scales with the font size, and the size is worked out from letters plus gaps so a line still fits.
  const GAP = 0.19; // em of margin on each side of a hook word: about 0.38 em between words
  const widest = Math.max(...lines.map((l) => 0.7 * l.reduce((n, w) => n + w.t.length, 0) + 2 * GAP * l.length + 0.12));
  const size = instant ? Math.min(110, Math.floor(1000 / widest)) : Math.min(96, Math.floor(1150 / Math.max(chars, 1)));
  return (
    <div style={{ position: "absolute", left: 30, right: 30, top: top ?? (instant ? 1250 : 1340), textAlign: "center" }}>
      {lines.map((line, li) => (
        <div key={li} style={{ whiteSpace: "nowrap" }}>
          {line.map((w, i) => {
            const s = spring({ frame: frame - w.f, fps, config: { damping: 10, stiffness: 320, mass: 0.4 } });
            const key = w.c !== "w";
            const sc = frame < w.f ? 0.8 : instant ? 1 : key ? interpolate(s, [0, 1], [1.35, 1.08]) : interpolate(s, [0, 1], [1.18, 1]);
            return (
              <Heavy key={i} size={size} color={colorOf(w.c)} style={{ margin: instant ? `0 ${Math.round(size * GAP)}px` : key ? "0 34px" : "0 20px", opacity: frame >= w.f ? 1 : 0, transform: `scale(${sc})` }}>
                {w.t}
              </Heavy>
            );
          })}
        </div>
      ))}
    </div>
  );
};
