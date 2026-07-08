import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Video } from "@remotion/media";
import { BRAND } from "./constants";

type KeyNumber = { label: string; value: string };

type TitleSceneProps = {
  title: string;
  subtitle?: string;
  highlight?: string;
  /** V2 幕次序号 1..5 */
  actNumber?: number;
  /** 幕标签（Opening / Pain / Technology · SHAP / POC Backtest / Business Model） */
  actLabel?: string;
  keyNumbers?: KeyNumber[];
};

export const TitleScene: React.FC<TitleSceneProps> = ({
  title,
  subtitle,
  highlight,
  actNumber,
  actLabel,
  keyNumbers,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, fps * 0.8], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const titleY = interpolate(frame, [0, fps * 1.2], [40, 0], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const glowOpacity = interpolate(
    frame,
    [fps * 0.5, fps * 2, fps * 4],
    [0.2, 0.5, 0.3],
    { extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse at 50% 30%, #152040 0%, ${BRAND.bg} 70%)`,
        fontFamily: "Segoe UI, Microsoft YaHei, sans-serif",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: "20%",
          left: "50%",
          width: 600,
          height: 600,
          marginLeft: -300,
          borderRadius: "50%",
          background: BRAND.accent,
          opacity: glowOpacity * 0.15,
          filter: "blur(80px)",
        }}
      />
      {/* V2 五幕左上角徽章 */}
      {actNumber ? (
        <div
          style={{
            position: "absolute",
            top: 60,
            left: 80,
            display: "flex",
            alignItems: "center",
            gap: 16,
            opacity: fadeIn,
          }}
        >
          <div
            style={{
              fontSize: 36,
              fontWeight: 700,
              color: BRAND.accent,
              padding: "8px 24px",
              border: `2px solid ${BRAND.accent}`,
              borderRadius: 8,
              background: "rgba(0, 212, 255, 0.08)",
            }}
          >
            ACT {actNumber} / 5
          </div>
          {actLabel ? (
            <div
              style={{
                fontSize: 28,
                color: BRAND.muted,
                letterSpacing: 1.5,
                textTransform: "uppercase",
              }}
            >
              {actLabel}
            </div>
          ) : null}
        </div>
      ) : null}

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          padding: "0 120px",
          opacity: fadeIn,
          gap: 32,
        }}
      >
        <div
          style={{
            fontSize: 96,
            fontWeight: 700,
            color: BRAND.text,
            textAlign: "center",
            translate: `0 ${titleY}px`,
            letterSpacing: 2,
          }}
        >
          {title}
        </div>
        {subtitle ? (
          <div
            style={{
              fontSize: 44,
              color: BRAND.muted,
              textAlign: "center",
              maxWidth: 1400,
              lineHeight: 1.4,
            }}
          >
            {subtitle}
          </div>
        ) : null}
        {highlight ? (
          <div
            style={{
              fontSize: 36,
              color: BRAND.highlight,
              textAlign: "center",
              padding: "16px 40px",
              border: `2px solid ${BRAND.highlight}`,
              borderRadius: 12,
              marginTop: 16,
            }}
          >
            {highlight}
          </div>
        ) : null}
        {/* V2 关键数字 3 列横排 */}
        {keyNumbers && keyNumbers.length > 0 ? (
          <div
            style={{
              display: "flex",
              gap: 48,
              marginTop: 32,
              flexWrap: "wrap",
              justifyContent: "center",
            }}
          >
            {keyNumbers.map((k, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  minWidth: 220,
                  padding: "16px 28px",
                  borderRadius: 12,
                  background: "rgba(0, 212, 255, 0.08)",
                  border: `1px solid rgba(0, 212, 255, 0.3)`,
                }}
              >
                <div
                  style={{
                    fontSize: 56,
                    fontWeight: 700,
                    color: BRAND.accent,
                    lineHeight: 1.1,
                  }}
                >
                  {k.value}
                </div>
                <div
                  style={{
                    fontSize: 22,
                    color: BRAND.muted,
                    marginTop: 8,
                    letterSpacing: 1,
                  }}
                >
                  {k.label}
                </div>
              </div>
            ))}
          </div>
        ) : null}
        <div
          style={{
            position: "absolute",
            bottom: 80,
            width: 200,
            height: 4,
            background: `linear-gradient(90deg, transparent, ${BRAND.accent}, transparent)`,
            opacity: fadeIn,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

type ScreenshotSceneProps = {
  screenshot?: string;
  video?: string;
  /** V2 图表 PNG（来自 public/charts/），优先级最高 */
  chartImage?: string;
  title: string;
  highlight?: string;
  actNumber?: number;
  actLabel?: string;
  keyNumbers?: KeyNumber[];
};

export const ScreenshotScene: React.FC<ScreenshotSceneProps> = ({
  screenshot,
  video,
  chartImage,
  title,
  highlight,
  actNumber,
  actLabel,
  keyNumbers,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, fps * 0.6], [0, 1], {
    extrapolateRight: "clamp",
  });

  const zoom = interpolate(frame, [0, durationInFrames], [1.0, 1.04], {
    extrapolateRight: "clamp",
  });

  const headerOpacity = interpolate(frame, [0, fps * 0.5], [0, 1], {
    extrapolateRight: "clamp",
  });

  const mediaStyle = {
    width: "100%",
    height: "100%",
    objectFit: "contain" as const,
    scale: zoom,
  };

  // 媒体优先级：chartImage (V2) > video (V1 兼容) > screenshot
  const primary = chartImage
    ? { kind: "chart" as const, src: staticFile(`charts/${chartImage}`) }
    : video
    ? { kind: "video" as const, src: staticFile(`videos/${video}`) }
    : screenshot
    ? { kind: "img" as const, src: staticFile(`screenshots/${screenshot}`) }
    : null;

  return (
    <AbsoluteFill
      style={{
        background: BRAND.bg,
        fontFamily: "Segoe UI, Microsoft YaHei, sans-serif",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 120,
          background:
            "linear-gradient(180deg, rgba(10,14,39,0.95) 0%, transparent 100%)",
          zIndex: 2,
          display: "flex",
          alignItems: "center",
          padding: "0 80px",
          opacity: headerOpacity,
        }}
      >
        {actNumber ? (
          <div
            style={{
              fontSize: 28,
              fontWeight: 700,
              color: BRAND.accent,
              padding: "4px 16px",
              border: `1.5px solid ${BRAND.accent}`,
              borderRadius: 6,
              marginRight: 24,
              background: "rgba(0, 212, 255, 0.08)",
            }}
          >
            ACT {actNumber} / 5
          </div>
        ) : null}
        <div style={{ fontSize: 48, fontWeight: 700, color: BRAND.accent }}>
          {title}
        </div>
        {highlight ? (
          <div
            style={{
              marginLeft: 40,
              fontSize: 32,
              color: BRAND.highlight,
              padding: "8px 24px",
              borderLeft: `3px solid ${BRAND.highlight}`,
            }}
          >
            {highlight}
          </div>
        ) : null}
        {actLabel ? (
          <div
            style={{
              marginLeft: "auto",
              fontSize: 22,
              color: BRAND.muted,
              letterSpacing: 1.2,
              textTransform: "uppercase",
            }}
          >
            {actLabel}
          </div>
        ) : null}
      </div>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          opacity: fadeIn,
          overflow: "hidden",
        }}
      >
        {primary ? (
          primary.kind === "video" ? (
            <Video src={primary.src} style={mediaStyle} volume={0} />
          ) : (
            <Img src={primary.src} style={mediaStyle} />
          )
        ) : (
          // 图表占位：当 chartImage 还没复制到 public/charts/ 时的兜底
          <div
            style={{
              width: "70%",
              height: "70%",
              border: `2px dashed ${BRAND.accent}`,
              borderRadius: 16,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              color: BRAND.muted,
              fontSize: 32,
              gap: 16,
            }}
          >
            <div style={{ fontSize: 48, color: BRAND.accent, fontWeight: 700 }}>
              📊 Chart Placeholder
            </div>
            <div>{chartImage ?? "(no chart)"}</div>
          </div>
        )}
      </div>
      {/* V2 关键数字条（底部横排） */}
      {keyNumbers && keyNumbers.length > 0 ? (
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            height: 140,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 48,
            background:
              "linear-gradient(0deg, rgba(10,14,39,0.95) 0%, transparent 100%)",
            zIndex: 2,
            opacity: fadeIn,
          }}
        >
          {keyNumbers.map((k, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                minWidth: 200,
                padding: "8px 20px",
              }}
            >
              <div
                style={{
                  fontSize: 40,
                  fontWeight: 700,
                  color: BRAND.accent,
                  lineHeight: 1.1,
                }}
              >
                {k.value}
              </div>
              <div
                style={{
                  fontSize: 18,
                  color: BRAND.muted,
                  marginTop: 4,
                }}
              >
                {k.label}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
