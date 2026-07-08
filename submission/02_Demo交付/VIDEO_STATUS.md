# 视频状态说明

**目标文件**：`QuantInsight_Pro_Demo_3min.mp4`  
**状态**：✅ **已自动生成**（2026-07-07）

| 项目 | 值 |
|------|-----|
| 分辨率 | 1920×1080 (16:9) |
| 时长 | ~273 秒（约 4:33，含完整操作录屏；可二次裁剪至 180s） |
| 旁白 | edge-tts `zh-CN-YunxiNeural` |
| 字幕 | `QuantInsight_Pro_Demo_3min.srt`（已烧录至 MP4） |
| 生成方式 | demo-video-factory · Playwright record + ffmpeg |

## 重新生成

```powershell
cd quantinsight-deploy
powershell -File scripts/run_quantinsight_demo_video.ps1 -Target production -Mode record
```

## 历史记录

| 任务 | 状态 |
|------|------|
| Record 3min demo (Playwright/ffmpeg) | ✅ 2026-07-07 成功 |
| 早期自动任务 | ⏹️ 已停止（子任务无产出） |

## 原因

仓库内检索结果：
- ❌ 无 `.mp4` 视频文件
- ✅ 有 4 个 SRT 字幕文件（仓库根目录）：
  - `QuantInsight_Pro_Demo_Video_V1.srt`（3 分钟总览）
  - `QuantInsight_Pro_Tech_Video_v1_ai_qa.srt`
  - `QuantInsight_Pro_Tech_Video_v2_backtest.srt`
  - `QuantInsight_Pro_Tech_Video_v3_alt_data.srt`

## 下一步

请按 `Demo视频制作脚本_3min.md` 录制，推荐 OBS 录屏方式（约 30 分钟可完成）。

录制完成后将 MP4 放置于本目录，文件名为 `QuantInsight_Pro_Demo_3min.mp4`。
