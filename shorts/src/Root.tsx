import React from "react";
import { Composition } from "remotion";
import { Outro, OUTRO_FRAMES } from "./Outro";
import { Short } from "./Short";
import { Thumb, ThumbProps } from "./Thumb";
import { Timeline } from "./types";

const emptyTimeline: Timeline = {
  slug: "",
  fps: 30,
  frames: 1,
  titleEnd: 1,
  askFrom: 1,
  titleWords: [],
  shots: [],
  items: [],
  captions: [],
  mocks: [],
  sfx: [],
};

const ShortFromProps: React.FC<Timeline> = (timeline) =>
  timeline.slug ? <Short tl={timeline} /> : null;

const ThumbFromProps: React.FC<ThumbProps> = (props) =>
  props.bg ? <Thumb {...props} /> : null;

export const Root: React.FC = () => (
  <>
    <Composition
      id="short"
      component={ShortFromProps}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={1}
      defaultProps={emptyTimeline}
      calculateMetadata={({ props }) => ({ durationInFrames: props.frames })}
    />
    <Composition
      id="thumb"
      component={ThumbFromProps}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={1}
      defaultProps={{ bg: "", top: "", big: "", bigColor: "g", mid: "", icon: "" }}
    />
    <Composition
      id="outro"
      component={Outro}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={OUTRO_FRAMES}
      defaultProps={{ hero: "tiktok" }}
    />
  </>
);
