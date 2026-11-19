export type Color = "w" | "g" | "r";

export type Shot = { from: number; dur: number; file: string; start: number; zoom: number; layout?: "crop" | "desktop"; /** play the clip's own audio at this volume */ vol?: number };
export type Item = { from: number; to: number; n: number; label: string; icon: string };
export type CapWord = { t: string; f: number; c: Color };
export type Caption = { from: number; to: number; words: CapWord[] };
export type Mock = { from: number; to: number; type: string; props: Record<string, any> };
export type Sfx = { from: number; name: string; vol: number };

export type Timeline = {
  slug: string;
  fps: number;
  frames: number;
  titleEnd: number;
  askFrom: number;
  titleWords: CapWord[];
  shots: Shot[];
  items: Item[];
  captions: Caption[];
  mocks: Mock[];
  sfx: Sfx[];
  subFrom?: number;
  earlySubFrom?: number;
  ctaLine?: string;
  /** Word on the call-to-action tag: SUBSCRIBE (YouTube, default) or FOLLOW (Instagram, TikTok). */
  cta?: string;
  /** "crop" (default) fills 9:16; "desktop" shows the 16:9 source whole, with `desktop` options. */
  layout?: "crop" | "desktop";
  desktop?: Desktop;
  /** voice track (default audio/<slug>/voice.wav) */
  voice?: string;
  /** false: no music bed here (assemble.py lays it under the whole cut) */
  bed?: boolean;
};

export type Desktop = {
  /** y of the top edge of the 1080x608 gameplay window */
  top: number;
  /** "blur": darkened, zoomed copy of the frame fills the page; "solid": flat dark brand colour */
  bg: "blur" | "solid";
  /** y of the caption block (default: below the gameplay) */
  capTop?: number;
  /** streamer-cam pop (crop of the source's own top-left cam) in the lower band, top y */
  camTop?: number;
};

// GTA 6 sunset theme. ACCENT is the flat "good" colour (bars, borders, ticks);
// text in ACCENT is drawn with the SUNSET gradient by <Heavy>. Old look: ACCENT = "#39FF3C", no gradient.
export const ACCENT = "#FFC83D";
export const SUNSET = "linear-gradient(180deg, #FFE066 0%, #FF9A3D 48%, #FF4FA3 100%)";
export const SUNSET_WIDE = "linear-gradient(90deg, #FFD23F 0%, #FF8A3D 38%, #FF4FA3 72%, #9B4DFF 100%)";
export const RED = "#FF2E2E";
export const INK = "#0b0b0b";
export const colorOf = (c: Color) => (c === "g" ? ACCENT : c === "r" ? RED : "#FFFFFF");
