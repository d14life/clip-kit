import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ACCENT, Mock, RED } from "../types";
import { FONT } from "./Text";

/**
 * Mock-ups: game-style UI rebuilt in code to prove a spoken claim.
 * Every one sits in a dark rounded box with a thin green border and an ILLUSTRATION tag,
 * because none of them is a real screenshot. The footer names the source of the claim.
 */
const T: React.CSSProperties = { fontFamily: FONT, fontStyle: "italic", fontWeight: 900, textTransform: "uppercase", color: "#fff" };
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Box: React.FC<{ t: number; left: number; source?: string; width?: number; children: React.ReactNode }> = ({ t, left, source, width = 760, children }) => {
  const { fps } = useVideoConfig();
  const s = spring({ frame: t, fps, config: { damping: 9, stiffness: 300, mass: 0.5 } });
  const out = interpolate(left, [0, 4], [0, 1], clamp);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 700, display: "flex", justifyContent: "center" }}>
      <div
        style={{
          width,
          transform: `scale(${interpolate(s, [0, 1], [0.92, 1]) * (0.9 + 0.1 * out)})`,
          opacity: Math.min(1, t / 2) * out,
          background: "rgba(12,14,16,0.9)",
          border: `3px solid ${ACCENT}`,
          borderRadius: 34,
          padding: "40px 40px 30px",
          boxShadow: "0 18px 50px rgba(0,0,0,0.6)",
          position: "relative",
        }}
      >
        <div style={{ ...T, position: "absolute", top: -19, left: 30, background: ACCENT, color: "#0b0b0b", fontSize: 22, padding: "5px 14px", borderRadius: 10, letterSpacing: "0.06em" }}>
          Illustration
        </div>
        {children}
        {source ? <div style={{ ...T, fontSize: 22, opacity: 0.7, marginTop: 20, textAlign: "center", letterSpacing: "0.05em" }}>Source: {source}</div> : null}
      </div>
    </div>
  );
};

const Versus: React.FC<{ t: number }> = ({ t }) => {
  const line = interpolate(t, [6, 13], [0, 1], clamp);
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 40 }}>
      <div style={{ position: "relative" }}>
        <span style={{ ...T, fontSize: 110, color: "#9aa0a6" }}>GTA V</span>
        <div style={{ position: "absolute", left: -10, top: "50%", height: 14, width: `${line * 108}%`, background: RED, transform: "rotate(-9deg)", borderRadius: 8, boxShadow: `0 0 18px ${RED}` }} />
      </div>
    </div>
  );
};

const Phone: React.FC<{ t: number; p: any }> = ({ t, p }) => {
  const reply = t > 26;
  return (
    <div>
      <div style={{ ...T, fontSize: 34, opacity: 0.75, marginBottom: 14 }}>📱 {p.from}</div>
      <div style={{ background: "#2b2f36", borderRadius: "30px 30px 30px 8px", padding: "22px 30px", display: "inline-block" }}>
        <span style={{ fontFamily: "Segoe UI, Segoe UI Emoji, sans-serif", fontWeight: 700, fontSize: 56, color: "#fff" }}>{p.msg}</span>
      </div>
      <div style={{ ...T, fontSize: 44, marginTop: 22, color: reply ? RED : "#9aa0a6", textAlign: "right", transform: `scale(${reply ? interpolate(t, [26, 30], [1.3, 1], clamp) : 1})`, transformOrigin: "right" }}>
        {reply ? "✕ No reply" : "Seen" + ".".repeat(1 + (Math.floor(t / 6) % 3))}
      </div>
    </div>
  );
};

const Meter: React.FC<{ t: number; p: any }> = ({ t, p }) => {
  const v = interpolate(t, [6, 26], [p.from, p.to], clamp);
  const down = p.to < p.from;
  return (
    <div>
      <div style={{ ...T, fontSize: 44, display: "flex", justifyContent: "space-between" }}>
        <span>{p.label}</span>
        <span style={{ color: down ? RED : ACCENT }}>{down ? "▼" : "▲"}</span>
      </div>
      <div style={{ height: 44, background: "#2b2f36", borderRadius: 22, marginTop: 16, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${v * 100}%`, background: down ? RED : ACCENT, borderRadius: 22 }} />
      </div>
    </div>
  );
};

const Prompt: React.FC<{ t: number; p: any }> = ({ t, p }) => {
  const pulse = 1 + 0.06 * Math.sin(t / 3);
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 28 }}>
      <div style={{ ...T, fontSize: 40, background: "#fff", color: "#0b0b0b", borderRadius: 16, padding: "14px 22px", transform: `scale(${pulse})`, boxShadow: `0 0 0 6px ${ACCENT}` }}>{p.button}</div>
      <span style={{ ...T, fontSize: 64 }}>{p.text}</span>
    </div>
  );
};

const Checklist: React.FC<{ t: number; p: any }> = ({ t, p }) => (
  <div>
    <div style={{ ...T, fontSize: 40, color: RED, marginBottom: 14 }}>🚨 {p.title}</div>
    {p.rows.map((r: string, i: number) => {
      const on = t > 8 + i * 9;
      return (
        <div key={r} style={{ display: "flex", alignItems: "center", gap: 22, margin: "10px 0", opacity: on ? 1 : 0.28 }}>
          <div style={{ width: 50, height: 50, borderRadius: 12, border: `4px solid ${on ? ACCENT : "#666"}`, background: on ? ACCENT : "transparent", color: "#0b0b0b", fontSize: 38, fontWeight: 900, textAlign: "center", lineHeight: "46px" }}>{on ? "✓" : ""}</div>
          <span style={{ ...T, fontSize: 56 }}>{r}</span>
        </div>
      );
    })}
  </div>
);

const Stars: React.FC<{ t: number; p: any }> = ({ t, p }) => (
  <div style={{ display: "flex", justifyContent: "center", gap: 14 }}>
    {Array.from({ length: p.n }).map((_, i) => {
      const on = t > 3 + i * 3;
      const last = i === p.n - 1;
      const pop = on ? interpolate(t - (3 + i * 3), [0, 4], [1.6, 1], clamp) : 1;
      return (
        <span key={i} style={{ fontSize: 100, lineHeight: 1, color: on ? (last ? RED : "#fff") : "#3a3f46", transform: `scale(${pop})`, textShadow: on && last ? `0 0 24px ${RED}` : "none" }}>
          ★
        </span>
      );
    })}
  </div>
);

const Scan: React.FC<{ t: number; p: any }> = ({ t, p }) => (
  <div>
    <div style={{ ...T, fontSize: 38, color: ACCENT, marginBottom: 12 }}>📡 Scanning vehicle{".".repeat(1 + (Math.floor(t / 5) % 3))}</div>
    {p.rows.map((r: [string, string], i: number) => {
      const on = t > 8 + i * 10;
      const bad = r[0] === "TRACKER";
      return (
        <div key={r[0]} style={{ display: "flex", justifyContent: "space-between", margin: "8px 0", opacity: on ? 1 : 0.2 }}>
          <span style={{ ...T, fontSize: 50 }}>{r[0]}</span>
          <span style={{ ...T, fontSize: 50, color: bad ? RED : "#fff" }}>{on ? r[1] : "—"}</span>
        </div>
      );
    })}
  </div>
);

const Speed: React.FC<{ t: number }> = ({ t }) => {
  const mph = Math.round(interpolate(t, [0, 40], [48, 14], clamp));
  const alert = mph < 22;
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ ...T, fontSize: 130, lineHeight: 1, color: alert ? RED : "#fff" }}>
        {mph} <span style={{ fontSize: 50 }}>MPH</span>
      </div>
      <div style={{ ...T, fontSize: 46, marginTop: 10, color: alert ? RED : "#9aa0a6", opacity: alert ? (Math.floor(t / 4) % 2 ? 1 : 0.55) : 1 }}>{alert ? "🚨 Tracker pinged police" : "📍 Tracker active"}</div>
    </div>
  );
};

const Stare: React.FC<{ t: number }> = ({ t }) => {
  const v = interpolate(t, [4, 60], [0, 1], clamp);
  const hot = v > 0.75;
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
        <span style={{ fontSize: 90, lineHeight: 1 }}>👀</span>
        <div style={{ flex: 1, height: 44, background: "#2b2f36", borderRadius: 22, overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${v * 100}%`, background: hot ? RED : "#fff", borderRadius: 22 }} />
        </div>
        <span style={{ fontSize: 90, lineHeight: 1, transform: `scale(${hot ? 1.25 : 0.9})`, filter: hot ? "none" : "grayscale(1) opacity(0.5)" }}>🐕</span>
      </div>
      <div style={{ ...T, fontSize: 42, marginTop: 14, textAlign: "center", color: hot ? RED : "#9aa0a6" }}>{hot ? "What you looking at?" : "Staring…"}</div>
    </div>
  );
};

const Bars: React.FC<{ t: number; p: any }> = ({ t, p }) => (
  <div>
    {p.rows.map((r: [string, number, number, string]) => {
      const v = interpolate(t, [5, 24], [r[1], r[2]], clamp);
      const col = r[3] === "g" ? ACCENT : r[3] === "r" ? RED : "#fff";
      return (
        <div key={r[0]} style={{ margin: "10px 0" }}>
          <div style={{ ...T, fontSize: 42, display: "flex", justifyContent: "space-between" }}>
            <span>{r[0]}</span>
            <span style={{ color: col }}>{r[2] > r[1] ? "▲" : r[2] < r[1] ? "▼" : ""}</span>
          </div>
          <div style={{ height: 38, background: "#2b2f36", borderRadius: 19, marginTop: 8, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${v * 100}%`, background: col, borderRadius: 19 }} />
          </div>
        </div>
      );
    })}
  </div>
);

const Table: React.FC<{ t: number; p: any }> = ({ t, p }) => (
  <div>
    <div style={{ ...T, fontSize: 40, marginBottom: 12 }}>{p.title}</div>
    {p.rows.map((r: [string, string, string], i: number) => {
      const on = t > 6 + i * 10;
      const col = r[2] === "g" ? ACCENT : r[2] === "r" ? RED : "#fff";
      return (
        <div key={r[0]} style={{ display: "flex", justifyContent: "space-between", gap: 20, margin: "10px 0", opacity: on ? 1 : 0.2 }}>
          <span style={{ ...T, fontSize: 46 }}>{r[0]}</span>
          <span style={{ ...T, fontSize: 46, color: col, transform: `scale(${on ? interpolate(t - (6 + i * 10), [0, 4], [1.3, 1], clamp) : 1})`, transformOrigin: "right" }}>{on ? r[1] : "—"}</span>
        </div>
      );
    })}
  </div>
);

const Levels: React.FC<{ t: number; p: any }> = ({ t, p }) => (
  <div>
    <div style={{ ...T, fontSize: 42, marginBottom: 10 }}>{p.label}</div>
    <div style={{ display: "flex", justifyContent: "center", gap: 18 }}>
      {Array.from({ length: p.n }).map((_, i) => {
        const on = i < p.lit && t > 4 + i * 5;
        const pop = on ? interpolate(t - (4 + i * 5), [0, 4], [1.6, 1], clamp) : 1;
        return (
          <span key={i} style={{ fontSize: 120, lineHeight: 1, color: on ? "#FF4FA3" : "#3a3f46", transform: `scale(${pop})`, textShadow: on ? "0 0 22px rgba(255,79,163,0.7)" : "none" }}>
            ♥
          </span>
        );
      })}
    </div>
  </div>
);

export const Mocks: React.FC<{ mocks: Mock[] }> = ({ mocks }) => {
  const frame = useCurrentFrame();
  const m = mocks.find((x) => frame >= x.from && frame < x.to);
  if (!m) return null;
  const t = frame - m.from;
  const left = m.to - frame;
  const p = m.props;
  const body =
    m.type === "versus" ? <Versus t={t} /> :
    m.type === "phone" ? <Phone t={t} p={p} /> :
    m.type === "meter" ? <Meter t={t} p={p} /> :
    m.type === "prompt" ? <Prompt t={t} p={p} /> :
    m.type === "checklist" ? <Checklist t={t} p={p} /> :
    m.type === "stars" ? <Stars t={t} p={p} /> :
    m.type === "scan" ? <Scan t={t} p={p} /> :
    m.type === "speed" ? <Speed t={t} /> :
    m.type === "stare" ? <Stare t={t} /> :
    m.type === "bars" ? <Bars t={t} p={p} /> :
    m.type === "table" ? <Table t={t} p={p} /> :
    m.type === "levels" ? <Levels t={t} p={p} /> : null;
  return (
    <Box t={t} left={left} source={p.source} width={m.type === "versus" ? 560 : 760}>
      {body}
    </Box>
  );
};
