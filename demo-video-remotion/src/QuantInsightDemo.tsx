import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { staticFile } from "remotion";
import { ACT_TITLES, SCENES } from "./constants";
import { ScreenshotScene, TitleScene } from "./Scenes";

/**
 * V2 主组件：5 幕布局（180s）
 * - 优先使用 PNG 截图 + 图表嵌入（不再依赖 webm 视频帧）
 * - 保留 audio 配音
 * - 每幕左上角显示 "ACT n / 5" 徽章 + 幕标签
 */
export const QuantInsightDemo: React.FC = () => {
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
            {/* 纯标题幕（开场 / 商业结尾）用 TitleScene；其他用 ScreenshotScene 承载图表+关键数字 */}
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
              />
            ) : (
              <TitleScene
                title={scene.title ?? ""}
                subtitle={scene.subtitle}
                highlight={scene.highlight}
                actNumber={scene.actNumber}
                actLabel={actLabel}
                keyNumbers={scene.keyNumbers}
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
