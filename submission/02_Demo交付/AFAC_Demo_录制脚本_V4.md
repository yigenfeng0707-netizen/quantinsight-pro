# AFAC Demo 录制脚本 V4

**目标时长**：180 秒（±3s）  
**旁白**：edge-tts `zh-CN-YunxiNeural`，正常语速（+5%），纯文本，无 SSML  
**画面**：Playwright 1920×1080 单次登录录制真实 Streamlit UI  
**交付**：`QuantInsight_Pro_Demo_3min.mp4`（无字幕）

---

## 场景一览

| # | 场景 | 时长 | 画面 | 旁白 |
|---|------|------|------|------|
| 1 | 片头 | ~18s | 品牌标题卡 | 见下 |
| 2 | 智能选股 | ~32s | 登录 → 多因子评分 → Top10 | 见下 |
| 3 | SHAP | ~32s | 可解释性分析 → Force Plot | 见下 |
| 4 | AI 问答 | ~28s | RAG 投研问答 | 见下 |
| 5 | 回测 | ~28s | 沪深300 多因子回测 | 见下 |
| 6 | 片尾 CTA | ~22s | URL + 项目编号 | 见下 |

---

## 旁白全文（正常语速，可直接 TTS）

### 1. 片头

欢迎来到 QuantInsight Pro。业内首家将 SHAP 可解释性深度集成到 A 股选股的 AI 投研平台。让 AI 可解释，让投资更可信。

### 2. 智能选股

第一步，智能选股。平台基于估值、成长、质量、动量、流动性、技术六大维度，共十七个因子对全市场股票综合评分，一键输出 Top10 推荐名单。

### 3. SHAP 可解释性

第二步，SHAP 可解释性分析。每一只推荐股票的决策过程，都可以追溯到具体因子贡献。Summary Bar 展示全局排序，Force Plot 展示单股归因。

### 4. AI 投研问答

第三步，AI 投研问答。基于 Qwen 大模型和 RAG 数据接地，用自然语言提问即可获得专业投研分析。每条结论都有数据来源引用，可追溯、可审计。

### 5. 量化回测

第四步，量化回测。沪深三百指数十一年真实数据，多因子策略年化收益百分之八点五六，夏普零点六三，回测引擎 MIT 开源。

### 6. 片尾

立即体验 3blue1brownlab.cn。QuantInsight Pro，让 AI 可解释，让投资更可信。感谢观看。

---

## UI 操作清单（单次登录）

1. 打开首页 → 用户名 `admin` → 密码（环境变量 `DEMO_PASSWORD`）
2. **智能选股** → 多因子评分 → 计算评分 → 等待 Top10
3. **量化策略回测** → AI 可解释性分析 → 开始 SHAP 分析
4. **AI 投研问答** → 输入「贵州茅台最新财报的核心亮点和风险点是什么？」→ 分析
5. **量化策略回测** → 策略「多因子合成」→ 运行回测

---

## 重新生成

```powershell
cd quantinsight-deploy
pip install edge-tts Pillow
cd streamlit_app; npm install playwright; npx playwright install chromium; cd ..
$env:DEMO_PASSWORD = "<从 .env 或 secrets.toml 读取，勿提交仓库>"
python scripts/afac_demo_v4.py --target local
```

若 localhost 不可用，自动回退 `https://3blue1brownlab.cn`。

---

## 技术参数

| 项 | 值 |
|----|-----|
| 分辨率 | 1920×1080 @ 30fps |
| 编码 | H.264 CRF 22 |
| 旁白 | zh-CN-YunxiNeural +5% |
| BGM | Chopin Nocturne Op.9 No.2，-20 dB |
| 字幕 | 无 |
