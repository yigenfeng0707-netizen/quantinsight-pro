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
  /** 幕次序号 1..5 */
  actNumber?: number;
  actLabel?: string;
  keyNumbers?: KeyNumber[];
  /** 路演 5min 信息密度更高 */
  bullets?: string[];
};

export const TitleScene: React.FC<TitleSceneProps> = ({
  title,
  subtitle,
  highlight,
  actNumber,
  actLabel,
  keyNumbers,
  bullets,
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
          gap: 28,
        }}
      >
        <div
          style={{
            fontSize: 88,
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
              fontSize: 38,
              color: BRAND.muted,
              textAlign: "center",
              maxWidth: 1500,
              lineHeight: 1.4,
            }}
          >
            {subtitle}
          </div>
        ) : null}
        {highlight ? (
          <div
            style={{
              fontSize: 30,
              color: BRAND.highlight,
              textAlign: "center",
              padding: "12px 32px",
              border: `2px solid ${BRAND.highlight}`,
              borderRadius: 12,
              marginTop: 8,
            }}
          >
            {highlight}
          </div>
        ) : null}
        {keyNumbers && keyNumbers.length > 0 ? (
          <div
            style={{
              display: "flex",
              gap: 36,
              marginTop: 24,
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
                  minWidth: 200,
                  padding: "14px 24px",
                  borderRadius: 12,
                  background: "rgba(0, 212, 255, 0.08)",
                  border: `1px solid rgba(0, 212, 255, 0.3)`,
                }}
              >
                <div
                  style={{
                    fontSize: 48,
                    fontWeight: 700,
                    color: BRAND.accent,
                    lineHeight: 1.1,
                  }}
                >
                  {k.value}
                </div>
                <div
                  style={{
                    fontSize: 20,
                    color: BRAND.muted,
                    marginTop: 6,
                    letterSpacing: 1,
                  }}
                >
                  {k.label}
                </div>
              </div>
            ))}
          </div>
        ) : null}
        {bullets && bullets.length > 0 ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 10,
              marginTop: 16,
              maxWidth: 1400,
            }}
          >
            {bullets.map((b, i) => (
              <div
                key={i}
                style={{
                  fontSize: 26,
                  color: BRAND.text,
                  lineHeight: 1.4,
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 12,
                }}
              >
                <span
                  style={{
                    color: BRAND.accent,
                    fontWeight: 700,
                    fontSize: 30,
                    lineHeight: 1.2,
                  }}
                >
                  ▸
                </span>
                <span>{b}</span>
              </div>
            ))}
          </div>
        ) : null}
        <div
          style={{
            position: "absolute",
            bottom: 60,
            width: 240,
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
  chartImage?: string;
  title: string;
  highlight?: string;
  actNumber?: number;
  actLabel?: string;
  keyNumbers?: KeyNumber[];
  bullets?: string[];
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
  bullets,
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

  // 媒体优先级：chartImage > video > screenshot
  const primary = chartImage
    ? { kind: "chart" as const, src: staticFile(`charts/${chartImage}`) }
    : video
    ? { kind: "video" as const, src: staticFile(`media/${video}`) }
    : screenshot
    ? {
        kind: "img" as const,
        src: staticFile(`screenshots/${screenshot}`),
      }
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
          height: 110,
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
              fontSize: 26,
              fontWeight: 700,
              color: BRAND.accent,
              padding: "4px 14px",
              border: `1.5px solid ${BRAND.accent}`,
              borderRadius: 6,
              marginRight: 20,
              background: "rgba(0, 212, 255, 0.08)",
            }}
          >
            ACT {actNumber} / 5
          </div>
        ) : null}
        <div style={{ fontSize: 42, fontWeight: 700, color: BRAND.accent }}>
          {title}
        </div>
        {highlight ? (
          <div
            style={{
              marginLeft: 32,
              fontSize: 26,
              color: BRAND.highlight,
              padding: "6px 18px",
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
              fontSize: 20,
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
      {/* 关键数字 + bullets 底部条 */}
      {(keyNumbers && keyNumbers.length > 0) ||
      (bullets && bullets.length > 0) ? (
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            padding: "24px 80px 32px",
            background:
              "linear-gradient(0deg, rgba(10,14,39,0.96) 0%, transparent 100%)",
            zIndex: 2,
            opacity: fadeIn,
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          {keyNumbers && keyNumbers.length > 0 ? (
            <div
              style={{
                display: "flex",
                gap: 40,
                justifyContent: "center",
                flexWrap: "wrap",
              }}
            >
              {keyNumbers.map((k, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    minWidth: 180,
                  }}
                >
                  <div
                    style={{
                      fontSize: 36,
                      fontWeight: 700,
                      color: BRAND.accent,
                      lineHeight: 1.1,
                    }}
                  >
                    {k.value}
                  </div>
                  <div
                    style={{
                      fontSize: 16,
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
          {bullets && bullets.length > 0 ? (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 6,
                maxWidth: 1500,
                margin: "0 auto",
              }}
            >
              {bullets.map((b, i) => (
                <div
                  key={i}
                  style={{
                    fontSize: 22,
                    color: BRAND.text,
                    lineHeight: 1.3,
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 10,
                  }}
                >
                  <span
                    style={{
                      color: BRAND.highlight,
                      fontWeight: 700,
                      lineHeight: 1.2,
                    }}
                  >
                    ▸
                  </span>
                  <span>{b}</span>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
