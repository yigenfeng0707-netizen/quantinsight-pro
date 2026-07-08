# QuantInsight Pro — hyperframes + Remotion Demo Pipeline (V2)

3-minute AFAC submission video composed with **PNG screenshots + embedded charts** + **Remotion** (scene composition).

> V2 升级：5 幕紧凑布局，移除对 webm 视频帧的依赖，改用 PNG 截图 + 7 张业务图表。

## Prerequisites (verified)

- Node.js 22+ / npm
- FFmpeg 6.1+
- Python 3.10+ (仅用于素材预处理)
- Streamlit demo 已部署或图表 PNG 已生成

## V2 — 3 分钟 Demo (QuantInsight_Pro_Demo_3min_V2.mp4)

5 幕紧凑布局（180s），关键数字采用 **T35 修正后** 数据。

### 5 幕时间表

| 幕 | 时长 | 主题 | 关键数字 |
|---|------|------|----------|
| ACT 1 | 30s | 开场 + Hook | 11.4 年回测 / 30→620 客户 / NRR 140% |
| ACT 2 | 30s | 痛点 | 传统工具 ¥30 万+ / 30,000+ 客群 / AI 黑盒 95%+ |
| ACT 3 | 60s | 技术 SHAP | 17 因子 / 21/21 单元测试 / SHAP 可解释 |
| ACT 4 | 30s | POC 回测 | HS300 8.56% / ZZ500 24.48% / CYB 11.55% |
| ACT 5 | 30s | 商业模式 | LTV/CAC 82.2 / NRR 140% / Y3 ARR 4.35 亿 |

### V2 资产结构

```
demo-video-remotion/
  public/
    audio/         # 配音（intro.mp3 / h1-h4.mp3 / outro.mp3）
    charts/        # V2 新增：7 张业务图表 PNG
      01_business_model_canvas.png
      02_ltv_cac_radar.png
      03_nrr_funnel.png
      04_backtest_curve.png
      05_client_growth.png
      06_customer_subscription_matrix.png
      07_team_structure.png
    screenshots/   # V1 兼容：UI 截图（h2_shap.png / h4_backtest.png 等）
    videos/        # V1 兼容：webm 视频（可选）
  src/
    constants.ts   # SCENES 数组（5 幕 + T35 修正数字）
    Scenes.tsx     # TitleScene / ScreenshotScene（支持 chartImage）
    QuantInsightDemo.tsx  # 5 幕 Sequence 布局
    Root.tsx       # Composition 注册
    index.ts       # entry
```

### V2 渲染

```powershell
cd demo-video-remotion
npm install
npm run render:v2
# → ../submission/02_Demo交付/QuantInsight_Pro_Demo_3min_V2.mp4
```

### V2 5 分钟决赛路演

```powershell
# 切换到独立的 5min 项目（位于 demo-video-remotion-pitch/）
cd ../demo-video-remotion-pitch
npm install
npm run render
# → ../submission/02_Demo交付/QuantInsight_Pro_Pitch_5min_V1.mp4
```

## V1 — 兼容保留（180s 7 幕）

V1 旧 7 幕（intro / h1-h5 / outro）配置仍保留在 `package.json` 的 `render` script，原始 `public/screenshots` + `public/videos` 资产不受影响。

```powershell
npm run render
# → ../submission/02_Demo交付/QuantInsight_Pro_Demo_3min.mp4
```

## Brand

- Background: `#0A0E27`
- Accent: `#00D4FF`
- Highlight: `#FFB800`

## V1 7 幕时间表（180s，仅供参照）

| Scene | Duration | Content |
|-------|----------|---------|
| intro | 12s | Title card |
| h1 | 40s | 智能选股 screenshot |
| h2 | 40s | SHAP 解读 screenshot |
| h3 | 30s | AI 问答 screenshot |
| h4 | 30s | 回测 screenshot |
| h5 | 18s | 团队 title card |
| outro | 10s | CTA title card |
