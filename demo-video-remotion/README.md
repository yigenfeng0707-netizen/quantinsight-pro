# QuantInsight Pro — hyperframes + Remotion Demo Pipeline

3-minute AFAC submission video composed with **hyperframes** (site capture) + **Remotion** (scene composition).

## Prerequisites (verified)

- hyperframes 0.7.36+
- Node.js 22+ / npm
- FFmpeg 6.1+
- Streamlit demo at `http://127.0.0.1:8501` (or set `DEMO_BASE_URL`)
- Python 3.10+ with `edge-tts` (optional, falls back to Windows SAPI)

## Pipeline

```powershell
# 1. Start Streamlit (if not running)
cd streamlit_app
.\.venv\Scripts\python -m streamlit run app.py --server.port 8501

# 2. Capture screenshots (Playwright + hyperframes capture)
node scripts/capture_demo_frames.mjs

# 3. Generate narration TTS
python scripts/generate_narration.py

# 4. Install Remotion deps (first time)
cd demo-video-remotion
npm install

# 5. Render final MP4
npm run render
```

Output: `submission/02_Demo交付/QuantInsight_Pro_Demo_3min.mp4`

## Brand

- Background: `#0A0E27`
- Accent: `#00D4FF`
- Highlight: `#FFB800`

## Scene timing (180s)

| Scene | Duration | Content |
|-------|----------|---------|
| intro | 12s | Title card |
| h1 | 40s | 智能选股 screenshot |
| h2 | 40s | SHAP 解读 screenshot |
| h3 | 30s | AI 问答 screenshot |
| h4 | 30s | 回测 screenshot |
| h5 | 18s | 团队 title card |
| outro | 10s | CTA title card |
