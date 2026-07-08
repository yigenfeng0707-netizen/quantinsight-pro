# 视频状态说明 · V3 Cinematic

**目标文件**：`QuantInsight_Pro_Demo_3min.mp4`  
**状态**：✅ **V3 电影级交付**（2026-07-08 从零重置）

| 项目 | 值 |
|------|-----|
| 脚本 | `AFAC_Demo_电影级脚本_V3.md`（8 幕 · 180s · SSML 抑扬顿挫） |
| 管线 | `scripts/afac_cinematic_demo_v3.py` |
| 分辨率 | 1920×1080 |
| 时长 | **179.91 s**（目标 180±3s ✅） |
| 音画差 | **0.01 s**（video 179.87s / audio 179.86s ✅） |
| 文件大小 | ~3.0 MB（3,126,154 字节） |
| 旁白 | edge-tts `zh-CN-YunxiNeural` + SSML prosody |
| 配乐 | Chopin Nocturne Op.9 No.2（CC0，-20 dB） |
| 字幕 | **无烧录字幕** |

## ffprobe 验证（2026-07-08 V3）

```json
{
  "format": { "duration": "179.914062", "size": "3126154" },
  "video": { "width": 1920, "height": 1080, "duration": "179.872031" },
  "audio": { "duration": "179.861000" },
  "delta": "0.01s"
}
```

## 功能覆盖

| 场景 | 时间 | 状态 |
|------|------|------|
| Act 1 片头品牌 | 5s | ✅ 品牌标题卡 #0A0E27/#00D4FF |
| Act 2 行业痛点 | 12s | ✅ 叙事标题卡 |
| Act 3 智能选股 | 33s | ✅ 旁白 + UI 录制 |
| Act 4 SHAP | 33s | ✅ 旁白 + UI 录制 |
| Act 5 AI 问答 | 27s | ✅ 旁白 + UI 录制 |
| Act 6 回测 | 27s | ✅ 旁白 + UI 录制 |
| Act 7 落地+团队 | 18s | ✅ 永字 + 4 人团队 |
| Act 8 CTA | 25s | ✅ URL + 项目编号 |

## 已完成的重置

- ✅ 旧 MP4/SRT/变体 → `archive/legacy_video/`
- ✅ demo-output 旧产物清空
- ✅ remotion media 清空（结构保留）
- ✅ 旧 storyboard / 脚本 / VIDEO_STATUS 归档
- ✅ 新 V3 脚本 + 管线 + 唯一交付 MP4

## 重新生成

```powershell
cd quantinsight-deploy
pip install edge-tts Pillow
cd streamlit_app && npm install playwright && npx playwright install chromium
cd ..
$env:DEMO_PASSWORD = "<Demo 登录密码>"
python scripts/afac_cinematic_demo_v3.py --target production
```

## 诚实质量评估

| 维度 | 目标 | V3 达成 |
|------|------|---------|
| 180s ±3s | ✅ | ✅ 179.91s |
| 音画同步 ≤3s | ✅ | ✅ 0.01s |
| 无烧录字幕 | ✅ | ✅ |
| SSML 抑扬顿挫旁白 | ✅ | ✅ 8 幕独立 SSML |
| 钢琴 BGM + 人声混音 | ✅ | ✅ -20dB amix |
| 品牌标题卡 | ✅ | ✅ 4 幕 cinematic title |
| 场景 fade 转场 | ✅ | ✅ per-segment fade in/out |
| UI zoompan | ✅ | ✅ browser 场景 |
| 单次 Playwright 新录 | 理想 | ⚠ 首次构建使用已归档 production webm（Playwright Chromium 下载中）；运行完整管线可刷新 |

### 与「电影级」理想的差距

- 当前转场为 segment fade，非 xfade 链式叠化（稳定性优先）
- Browser 素材可 `--target production` 无 `--skip-record` 重录刷新
- 文件 3.0MB 偏小（高压缩）；可降 CRF 提升画质

## 旧脚本（已归档，勿用）

见 `archive/legacy_video/README.md`

## 打包

```powershell
python scripts/build_submission_zip.py
```
