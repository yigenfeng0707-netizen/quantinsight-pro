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

type TitleSceneProps = {
  title: string;
  subtitle?: string;
  highlight?: string;
};

export const TitleScene: React.FC<TitleSceneProps> = ({
  title,
  subtitle,
  highlight,
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
  title: string;
  highlight?: string;
};

export const ScreenshotScene: React.FC<ScreenshotSceneProps> = ({
  screenshot,
  video,
  title,
  highlight,
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

  return (
    <AbsoluteFill style={{ background: BRAND.bg, fontFamily: "Segoe UI, Microsoft YaHei, sans-serif" }}>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 120,
          background: "linear-gradient(180deg, rgba(10,14,39,0.95) 0%, transparent 100%)",
          zIndex: 2,
          display: "flex",
          alignItems: "center",
          padding: "0 80px",
          opacity: headerOpacity,
        }}
      >
        <div style={{ fontSize: 48, fontWeight: 700, color: BRAND.accent }}>{title}</div>
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
        {video ? (
          <Video src={staticFile(`videos/${video}`)} style={mediaStyle} volume={0} />
        ) : screenshot ? (
          <Img src={staticFile(`screenshots/${screenshot}`)} style={mediaStyle} />
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
