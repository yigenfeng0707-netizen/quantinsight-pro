# QuantInsight Pro — 5-min Final Pitch (V1)

独立 Remotion npm 项目，用于 AFAC 决赛 5 分钟路演。

## 规格

- 总时长：5 分钟（300s）
- 5 幕布局：每幕 60s
- 分辨率：1920×1080 @ 30fps

## 5 幕时间表

| 幕 | 时长 | 主题 | 关键数字 |
|---|------|------|----------|
| ACT 1 | 60s | 开场 + Hook | 11.4 年 / 30→620 / LTV/CAC 82.2 / NRR 140% |
| ACT 2 | 60s | 痛点 | ¥30 万+ / 30,000+ 客群 / AI 黑盒 95%+ |
| ACT 3 | 60s | 技术 SHAP | 17 因子 / 21/21 单元测试 / SHAP / SLA 92% |
| ACT 4 | 60s | POC 回测 | HS300 8.56% / ZZ500 24.48% / CYB 11.55% / 11.4 年 |
| ACT 5 | 60s | 商业模式 | LTV/CAC 82.2 / NRR 140% / Y3 ARR 4.35 亿 / Y5 5.85 亿 |

## 资产结构

```
demo-video-remotion-pitch/
  public/
    audio/         # 配音
    charts/        # 业务图表 PNG
    screenshots/   # UI 截图
    media/         # 视频
  src/
    constants.ts   # SCENES 5 幕（300s）
    Scenes.tsx     # TitleScene / ScreenshotScene（支持 chartImage + bullets）
    Pitch.tsx      # 5 幕 Sequence 布局
    Root.tsx       # Composition 注册（id="Pitch"）
    index.ts       # entry
  remotion.config.ts
  tsconfig.json
  package.json
```

## 渲染

```powershell
cd demo-video-remotion-pitch
npm install
npm run render
# → ../submission/02_Demo交付/QuantInsight_Pro_Pitch_5min_V1.mp4
```

## 关联项目

- `../demo-video-remotion/`：3 分钟 Demo V2（180s · 5 幕紧凑）
- 本项目：5 分钟决赛路演 V1（300s · 5 幕展开）
