import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { staticFile } from "remotion";
import { ACT_TITLES, SCENES } from "./constants";
import { ScreenshotScene, TitleScene } from "./Scenes";

/**
 * 5 分钟决赛路演 V1 主组件
 *  5 幕 × 60s = 300s
 *  幕 1 (60s): 开场 + Hook 数据
 *  幕 2 (60s): 痛点
 *  幕 3 (60s): 技术 SHAP
 *  幕 4 (60s): POC 回测
 *  幕 5 (60s): 商业模式 + 财务
 */
export const Pitch: React.FC = () => {
  const { fps } = useVideoConfig();
  let from = 0;

  return (
    <AbsoluteFill>
      {SCENES.map((scene) => {
        const durationInFrames = scene.durationSeconds * fps;
        const actLabel = scene.actNumber
          ? ACT_TITLES.find((a) => a.number === scene.actNumber)?.label
          : undefined;
        const seq = (
          <Sequence
            key={scene.id}
            from={from}
            durationInFrames={durationInFrames}
          >
            {scene.chartImage || scene.screenshot || scene.video ? (
              <ScreenshotScene
                screenshot={scene.screenshot}
                video={scene.video}
                chartImage={scene.chartImage}
                title={scene.title ?? ""}
                highlight={scene.highlight}
                actNumber={scene.actNumber}
                actLabel={actLabel}
                keyNumbers={scene.keyNumbers}
                bullets={scene.bullets}
              />
            ) : (
              <TitleScene
                title={scene.title ?? ""}
                subtitle={scene.subtitle}
                highlight={scene.highlight}
                actNumber={scene.actNumber}
                actLabel={actLabel}
                keyNumbers={scene.keyNumbers}
                bullets={scene.bullets}
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
export {
  ACT_TITLES,
  FPS,
  SCENES,
  TOTAL_DURATION_SECONDS,
  TOTAL_FRAMES,
} from "./constants";
