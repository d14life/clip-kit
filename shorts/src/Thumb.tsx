import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { Heavy } from "./components/Text";
import { ACCENT, RED } from "./types";

export type ThumbProps = { bg: string; top: string; big: string; bigColor: "g" | "r"; mid: string; icon: string; tag?: string; shade?: number; y?: number; scale?: number };

/** Cover image for a Short: one sharp footage frame, three or four huge words kept inside the centre crop.
 * Instagram shows covers cropped to the middle 3:4 (y 240-1680) on the profile grid: use scale 0.8 and y ~1040 there. */
export const Thumb: React.FC<ThumbProps> = ({ bg, top, big, bigColor, mid, icon, tag, shade = 1, y = 1010, scale = 1 }) => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Img src={staticFile(bg)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "saturate(1.15) contrast(1.08)" }} />
    <AbsoluteFill style={{ background: `linear-gradient(180deg, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 48%, rgba(0,0,0,${0.82 * shade}) 74%, rgba(0,0,0,${0.9 * shade}) 100%)` }} />
    <div style={{ position: "absolute", left: 40, right: 40, top: y, textAlign: "center", transform: `rotate(-3deg) scale(${scale})`, transformOrigin: "50% 0%" }}>
      {tag ? (
        <div style={{ marginBottom: 14 }}>
          <Heavy size={56} stroke={12} color={ACCENT}>{tag}</Heavy>
        </div>
      ) : null}
      <div>
        <Heavy size={92} stroke={16}>{top}</Heavy>
      </div>
      <div style={{ marginTop: -6 }}>
        <Heavy size={236} stroke={26} color={bigColor === "g" ? ACCENT : RED} style={{ textShadow: "0 12px 0 #0b0b0b, 0 22px 40px rgba(0,0,0,0.7)" }}>
          {big}
        </Heavy>
      </div>
      <div style={{ marginTop: -10, display: "flex", alignItems: "center", justifyContent: "center", gap: 28 }}>
        <Heavy size={150} stroke={22}>{mid}</Heavy>
        {icon ? <span style={{ fontSize: 138, lineHeight: 1, display: "block", transform: "translateY(-8px) rotate(6deg)", filter: "drop-shadow(0 8px 12px rgba(0,0,0,0.7))" }}>{icon}</span> : null}
      </div>
    </div>
  </AbsoluteFill>
);
