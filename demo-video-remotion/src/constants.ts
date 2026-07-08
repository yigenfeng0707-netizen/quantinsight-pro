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
  /** 幕次序号（1..5），用于 V2 五幕布局 */
  actNumber?: number;
  title?: string;
  subtitle?: string;
  highlight?: string;
  /** 截图资源（来自 public/screenshots/） */
  screenshot?: string;
  /** 图表资源（来自 public/charts/），V2 优先用 PNG 图表 */
  chartImage?: string;
  /** 视频资源（来自 public/videos/），V1 兼容字段 */
  video?: string;
  /** 关键数字，用于叠在场景画面上 */
  keyNumbers?: { label: string; value: string }[];
  audio?: string;
};

/**
 * V2 五幕布局（更紧凑）：
 *  幕 1 开场 30s
 *  幕 2 痛点 30s
 *  幕 3 技术 SHAP 60s
 *  幕 4 POC 回测 30s
 *  幕 5 商业 30s
 * 总时长 180s（保持 3 分钟）
 *
 * 关键数字采用 T35 修正后：
 *   HS300 8.56% / ZZ500 24.48% / CYB 11.55% / 11.4 年回测
 *   LTV/CAC = 82.2, NRR = 140%, 客户 30 → 620
 */
export const SCENES: SceneDef[] = [
  {
    id: "act1_opening",
    actNumber: 1,
    durationSeconds: 30,
    title: "QuantInsight Pro · AFAC2026",
    subtitle: "AI 驱动的另类数据量化投研平台",
    highlight: "11.4 年 POC 真实回测 · T35 修正后年化 8.56%~24.48%",
    keyNumbers: [
      { label: "回测窗口", value: "11.4 年" },
      { label: "客户增速", value: "30 → 620" },
      { label: "NRR", value: "140%" },
    ],
    audio: "intro.mp3",
  },
  {
    id: "act2_pain",
    actNumber: 2,
    durationSeconds: 30,
    title: "中小私募的 AI 鸿沟",
    subtitle: "缺数据、缺工程、缺合规——Wind+优矿年费 30 万起，AI 投研 0 工具链",
    highlight: "QuantInsight Pro · 中小私募 0 AI 成本可解释投研 SaaS",
    keyNumbers: [
      { label: "传统工具年费", value: "¥30 万+" },
      { label: "目标客群规模", value: "30,000+" },
      { label: "AI 黑盒率", value: "95%+" },
    ],
    chartImage: "06_customer_subscription_matrix.png",
    audio: "h1.mp3",
  },
  {
    id: "act3_shap",
    actNumber: 3,
    durationSeconds: 60,
    title: "技术 · SHAP 17 因子可解释",
    subtitle: "业内独家 SHAP 多因子归因 · 17 因子库 · 3 模态融合（舆情/资金流/政策）",
    highlight: "MIT 开源回测引擎（已开源 5 项） · 21/21 单元测试 100% PASS",
    keyNumbers: [
      { label: "因子库", value: "17 因子" },
      { label: "单元测试", value: "21/21" },
      { label: "可解释", value: "SHAP" },
    ],
    screenshot: "h2_shap.png",
    chartImage: "02_ltv_cac_radar.png",
    audio: "h2.mp3",
  },
  {
    id: "act4_poc",
    actNumber: 4,
    durationSeconds: 30,
    title: "POC 真实回测 · T35 修正",
    subtitle: "永字资管战略合作 · 2015-01 → 2026-06 月度净值序列",
    highlight: "T35 修正后：HS300 8.56% / ZZ500 24.48% / CYB 11.55%",
    keyNumbers: [
      { label: "HS300", value: "8.56%" },
      { label: "ZZ500", value: "24.48%" },
      { label: "CYB", value: "11.55%" },
    ],
    chartImage: "04_backtest_curve.png",
    screenshot: "h4_backtest.png",
    audio: "h4.mp3",
  },
  {
    id: "act5_business",
    actNumber: 5,
    durationSeconds: 30,
    title: "商业模式 · 5 年路线图",
    subtitle: "4 客群 × 3 订阅层级 · 自助 SaaS 90% + VIP 1v1 10%",
    highlight: "LTV/CAC = 82.2 · NRR 140% · 30 → 620 客户（2026-2030）",
    keyNumbers: [
      { label: "LTV/CAC", value: "82.2" },
      { label: "NRR", value: "140%" },
      { label: "Y3 ARR", value: "4.35 亿" },
    ],
    chartImage: "05_client_growth.png",
    audio: "outro.mp3",
  },
];

export const TOTAL_DURATION_SECONDS = SCENES.reduce(
  (sum, s) => sum + s.durationSeconds,
  0,
);

export const TOTAL_FRAMES = TOTAL_DURATION_SECONDS * FPS;

/**
 * V2 五幕标题样式元数据
 */
export const ACT_TITLES: { number: number; label: string; accent: string }[] = [
  { number: 1, label: "Opening", accent: BRAND.accent },
  { number: 2, label: "Pain", accent: BRAND.highlight },
  { number: 3, label: "Technology · SHAP", accent: BRAND.accent },
  { number: 4, label: "POC Backtest", accent: BRAND.highlight },
  { number: 5, label: "Business Model", accent: BRAND.accent },
];
