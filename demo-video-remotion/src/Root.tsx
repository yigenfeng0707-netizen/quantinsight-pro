import { Composition } from "remotion";
import { QuantInsightDemo } from "./QuantInsightDemo";
import {
  FPS,
  HEIGHT,
  TOTAL_FRAMES,
  WIDTH,
} from "./constants";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="QuantInsightDemo"
        component={QuantInsightDemo}
        durationInFrames={TOTAL_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
    </>
  );
};
