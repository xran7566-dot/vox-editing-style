// Adapter: use approved source-time ranges without changing the original file.
// Remotion project must validate the approval file before preview/render.
import React from 'react';
import {OffthreadVideo, Sequence, useVideoConfig} from 'remotion';

export type CutTimeline = {segments: {source_start: number; source_end: number;
  output_start: number; output_end: number}[]};

export const RoughCutSource: React.FC<{src: string; timeline: CutTimeline}> = ({src, timeline}) => {
  const {fps} = useVideoConfig();
  return <>{timeline.segments.map((segment, i) => {
    const from = Math.round(segment.output_start * fps);
    const duration = Math.round(segment.output_end * fps) - from;
    return duration > 0 ? <Sequence key={i} from={from} durationInFrames={duration}>
      <OffthreadVideo src={src} startFrom={Math.round(segment.source_start * fps)}
        style={{width: '100%', height: '100%', objectFit: 'contain'}} />
    </Sequence> : null;
  })}</>;
};
