export const BRAND = {
  bg: "#0A0E27",
  accent: "#00D4FF",
  highlight: "#FFB800",
  text: "#FFFFFF",
  muted: "#A8B2D1",
} as const;

export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

export type SceneDef = {
  id: string;
  durationSeconds: number;
  title?: string;
  subtitle?: string;
  highlight?: string;
  screenshot?: string;
  video?: string;
  audio?: string;
};

export const SCENES: SceneDef[] = [
  {
    id: "intro",
    durationSeconds: 12,
    title: "QuantInsight Pro",
    subtitle: "AI 驱动的另类数据量化投研平台",
    audio: "intro.mp3",
  },
  {
    id: "h1",
    durationSeconds: 40,
    title: "智能选股",
    highlight: "17 因子综合评分 · Top10 智能推荐",
    video: "h1.webm",
    screenshot: "h1_stock_pick.png",
    audio: "h1.mp3",
  },
  {
    id: "h2",
    durationSeconds: 40,
    title: "SHAP 解读",
    highlight: "业内独家 · SHAP 17 因子可解释",
    video: "h2.webm",
    screenshot: "h2_shap.png",
    audio: "h2.mp3",
  },
  {
    id: "h3",
    durationSeconds: 30,
    title: "AI 投研问答",
    highlight: "RAG 数据接地 · 引用可追溯",
    video: "h3.webm",
    screenshot: "h3_ai_qa.png",
    audio: "h3.mp3",
  },
  {
    id: "h4",
    durationSeconds: 30,
    title: "量化策略回测",
    highlight: "11.4 年真实数据 · T35 开源引擎验证",
    video: "h4.webm",
    screenshot: "h4_backtest.png",
    audio: "h4.mp3",
  },
  {
    id: "h5",
    durationSeconds: 18,
    title: "核心团队",
    subtitle: "冯亦根 · 王宇寒 · 官馨 · 梁理智",
    highlight: "永字资管战略合作已签署",
    audio: "h5.mp3",
  },
  {
    id: "outro",
    durationSeconds: 10,
    title: "QuantInsight Pro",
    subtitle: "https://quantinsight.cn",
    highlight: "让 AI 可解释，让投资更可信",
    audio: "outro.mp3",
  },
];

export const TOTAL_DURATION_SECONDS = SCENES.reduce(
  (sum, s) => sum + s.durationSeconds,
  0,
);

export const TOTAL_FRAMES = TOTAL_DURATION_SECONDS * FPS;
