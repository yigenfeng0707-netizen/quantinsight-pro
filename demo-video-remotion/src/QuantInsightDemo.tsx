import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { staticFile } from "remotion";
import { FPS, SCENES } from "./constants";
import { ScreenshotScene, TitleScene } from "./Scenes";

export const QuantInsightDemo: React.FC = () => {
  const { fps } = useVideoConfig();
  let from = 0;

  return (
    <AbsoluteFill>
      {SCENES.map((scene) => {
        const durationInFrames = scene.durationSeconds * fps;
        const seq = (
          <Sequence
            key={scene.id}
            from={from}
            durationInFrames={durationInFrames}
          >
            {scene.screenshot || scene.video ? (
              <ScreenshotScene
                screenshot={scene.screenshot}
                video={scene.video}
                title={scene.title ?? ""}
                highlight={scene.highlight}
              />
            ) : (
              <TitleScene
                title={scene.title ?? ""}
                subtitle={scene.subtitle}
                highlight={scene.highlight}
              />
            )}
            {scene.audio ? (
              <Audio src={staticFile(`audio/${scene.audio}`)} volume={1} />
            ) : null}
          </Sequence>
        );
        from += durationInFrames;
        return seq;
      })}
    </AbsoluteFill>
  );
};

// Re-export for metadata
export { FPS, SCENES, TOTAL_FRAMES, TOTAL_DURATION_SECONDS } from "./constants";
