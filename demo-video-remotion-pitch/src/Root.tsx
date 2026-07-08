import { Composition } from "remotion";
import { Pitch } from "./Pitch";
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
        id="Pitch"
        component={Pitch}
        durationInFrames={TOTAL_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
    </>
  );
};
