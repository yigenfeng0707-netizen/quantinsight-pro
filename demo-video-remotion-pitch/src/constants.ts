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
  /** 幕次序号（1..5） */
  actNumber?: number;
  title?: string;
  subtitle?: string;
  highlight?: string;
  /** 截图资源（来自 public/screenshots/） */
  screenshot?: string;
  /** 图表资源（来自 public/charts/） */
  chartImage?: string;
  /** 视频资源（来自 public/media/） */
  video?: string;
  /** 关键数字，叠在场景画面上 */
  keyNumbers?: { label: string; value: string }[];
  /** 详细 bullet points（路演 5min 信息密度更高） */
  bullets?: string[];
  audio?: string;
};

/**
 * 5 分钟决赛路演 V1（5 幕 × 60s = 300s）
 *  幕 1 (60s): 开场 + Hook 数据
 *  幕 2 (60s): 痛点
 *  幕 3 (60s): 技术 SHAP
 *  幕 4 (60s): POC 回测
 *  幕 5 (60s): 商业模式 + 财务
 */
export const SCENES: SceneDef[] = [
  {
    id: "act1_opening",
    actNumber: 1,
    durationSeconds: 60,
    title: "QuantInsight Pro · 让 AI 可解释",
    subtitle: "AI 驱动的另类数据量化投研平台 · 5 分钟路演",
    highlight:
      "永字资管战略合作已签 · 11.4 年 POC 真实回测 · T35 修正后年化 8.56%~24.48%",
    keyNumbers: [
      { label: "回测窗口", value: "11.4 年" },
      { label: "客户增速", value: "30 → 620" },
      { label: "LTV/CAC", value: "82.2" },
      { label: "NRR", value: "140%" },
    ],
    bullets: [
      "T35 修正后：HS300 8.56% / ZZ500 24.48% / CYB 11.55%",
      "Y3 ARR 4.35 亿元 · Y5 ARR 5.85 亿元",
      "5 校学术 MOU · 17 因子库 · MIT 开源回测引擎",
    ],
    audio: "intro.mp3",
  },
  {
    id: "act2_pain",
    actNumber: 2,
    durationSeconds: 60,
    title: "中小私募的 AI 鸿沟",
    subtitle: "缺数据、缺工程、缺合规——Wind+优矿年费 30 万起，AI 投研 0 工具链",
    highlight: "QuantInsight Pro · 中小私募 0 AI 成本可解释投研 SaaS",
    keyNumbers: [
      { label: "传统工具年费", value: "¥30 万+" },
      { label: "目标客群规模", value: "30,000+" },
      { label: "AI 黑盒率", value: "95%+" },
      { label: "合规成本", value: "高" },
    ],
    bullets: [
      "中小私募 < 50 亿：买不起 Wind+优矿+AI 投研",
      "家办 / 财富线：缺另类数据 + 缺工程能力",
      "个人高净值：缺可信 AI 解释、缺透明业绩归因",
      "银行私行/券商投顾：缺合规可解释白盒 AI",
    ],
    chartImage: "06_customer_subscription_matrix.png",
    audio: "h1.mp3",
  },
  {
    id: "act3_shap",
    actNumber: 3,
    durationSeconds: 60,
    title: "技术 · SHAP 17 因子可解释",
    subtitle:
      "业内独家 SHAP 多因子归因 · 17 因子库 · 3 模态融合（舆情/资金流/政策）",
    highlight:
      "MIT 开源回测引擎（已开源 5 项） · 21/21 单元测试 100% PASS",
    keyNumbers: [
      { label: "因子库", value: "17 因子" },
      { label: "单元测试", value: "21/21" },
      { label: "可解释", value: "SHAP" },
      { label: "SLA", value: "92%" },
    ],
    bullets: [
      "3 模态融合：舆情 NLP + 资金流 + 政策事件",
      "SHAP 归因：每个预测输出 Top-K 因子贡献",
      "RAG 数据接地：所有 AI 回答引用可追溯",
      "Streamlit Cloud + 蚂蚁云 ECS · systemd 7×24",
    ],
    screenshot: "h2_shap.png",
    chartImage: "02_ltv_cac_radar.png",
    audio: "h2.mp3",
  },
  {
    id: "act4_poc",
    actNumber: 4,
    durationSeconds: 60,
    title: "POC 真实回测 · T35 修正",
    subtitle:
      "永字资管战略合作 · 2015-01 → 2026-06 月度净值序列 · 真实可审计",
    highlight:
      "T35 修正后：HS300 8.56% / ZZ500 24.48% / CYB 11.55%",
    keyNumbers: [
      { label: "HS300", value: "8.56%" },
      { label: "ZZ500", value: "24.48%" },
      { label: "CYB", value: "11.55%" },
      { label: "回测窗口", value: "11.4 年" },
    ],
    bullets: [
      "T35 修正：HS300 19.22% → 8.56%（降幅 10.66pp）",
      "ZZ500 多因子：策略 24.48% vs 基准 20.48%",
      "CYB 多因子：策略 11.55% vs 基准 13.09%",
      "回测引擎已开源：MIT 协议 · 5 项核心模块",
    ],
    chartImage: "04_backtest_curve.png",
    screenshot: "h4_backtest.png",
    audio: "h4.mp3",
  },
  {
    id: "act5_business",
    actNumber: 5,
    durationSeconds: 60,
    title: "商业模式 · 5 年路线图",
    subtitle:
      "4 客群 × 3 订阅层级 · 自助 SaaS 90% + VIP 1v1 10% · Y3 ARR 4.35 亿",
    highlight: "LTV/CAC = 82.2 · NRR 140% · 30 → 620 客户（2026-2030）",
    keyNumbers: [
      { label: "LTV/CAC", value: "82.2" },
      { label: "NRR", value: "140%" },
      { label: "Y3 ARR", value: "4.35 亿" },
      { label: "Y5 ARR", value: "5.85 亿" },
    ],
    bullets: [
      "Y1 30 客户 / 1.98 亿 → Y5 620 客户 / 5.85 亿",
      "客户 CAGR 113% · ARR CAGR 31%",
      "4 创始人 + 5 顾问 · 期权池 35%",
      "复旦/上财量化组学术背书 · 永字资管战略合作",
    ],
    chartImage: "05_client_growth.png",
    screenshot: "h5_team.png",
    audio: "outro.mp3",
  },
];

export const TOTAL_DURATION_SECONDS = SCENES.reduce(
  (sum, s) => sum + s.durationSeconds,
  0,
);

export const TOTAL_FRAMES = TOTAL_DURATION_SECONDS * FPS;

export const ACT_TITLES: { number: number; label: string; accent: string }[] = [
  { number: 1, label: "Opening · Hook", accent: BRAND.accent },
  { number: 2, label: "Pain · Market", accent: BRAND.highlight },
  { number: 3, label: "Technology · SHAP", accent: BRAND.accent },
  { number: 4, label: "POC · Backtest", accent: BRAND.highlight },
  { number: 5, label: "Business · Finance", accent: BRAND.accent },
];
