# 07 · 视频素材

| # | 文件 | 状态 | 时长 |
|---|------|------|------|
| 1 | `QuantInsight_Pro_Demo_3min_V1_终版.mp4` | ✅ **已就绪** | 180s |
| 2 | `QuantInsight_Pro_Demo_3min_V2.mp4` | ⏳ **待渲染** | 180s |
| 3 | `QuantInsight_Pro_Pitch_5min_V1.mp4` | ⏳ **待渲染** | 300s |

## 📤 上传 AFAC 平台

**首选**: `QuantInsight_Pro_Demo_3min_V1_终版.mp4`（已就绪 · 3 分钟 · 电影级）

## ⏳ V2 视频渲染命令

```bash
# 3 分钟 Demo V2（修订版）
cd d:\AFAC2026金融智能创新大赛\quantinsight-deploy\demo-video-remotion
npm install
npm run render:v2
# 输出: ../submission/02_Demo交付/QuantInsight_Pro_Demo_3min_V2.mp4
# 复制到 delivery/07_视频/QuantInsight_Pro_Demo_3min_V2.mp4

# 5 分钟决赛路演 V1
cd d:\AFAC2026金融智能创新大赛\quantinsight-deploy\demo-video-remotion-pitch
npm install
npm run render
# 输出: ../submission/02_Demo交付/QuantInsight_Pro_Pitch_5min_V1.mp4
# 复制到 delivery/07_视频/QuantInsight_Pro_Pitch_5min_V1.mp4
```

## 🎬 视频设计亮点

- 1920×1080@30fps
- 5 幕分镜（开场 / 痛点 / SHAP / POC / 商业）
- 嵌入 7 张 dynamic-ui 图表
- 音视频字幕完全同步
- 配音使用 Edge TTS / Azure Speech
