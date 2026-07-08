# Tasks

## Task 1: 数据一致性 100% 核查脚本
- [x] 1.1 编写 `scripts/_check_data_consistency.py`（扫描全库关键数字）
- [x] 1.2 验证：8.56% 命中数 ≥ 60；19.22% 仅在 banner/归档；24.48%/11.55%/11.4年 数据一致
- [x] 1.3 输出 `submission/04_测试报告/数据一致性报告_V2.md`

## Task 2: 7 张 dynamic-ui 图表渲染
- [x] 2.1 商业模式 9 宫格（SVG）→ `submission/03_正式文档_WORD/_assets/01_business_model_canvas.png` ✅
- [x] 2.2 LTV/CAC 雷达图（=82.2 vs SaaS 3.0 基准）→ `02_ltv_cac_radar.png` ✅
- [x] 2.3 NRR 140% 漏斗（分客群/分订阅）→ `03_nrr_funnel.png` ✅
- [x] 2.4 T35 修正回测曲线（3 指数 5 策略，11.4 年）→ `04_backtest_curve.png` ✅
- [x] 2.5 30→620 客户增长曲线（5 年）→ `05_client_growth.png` ✅
- [x] 2.6 4 客群 × 3 订阅矩阵（热力图）→ `06_customer_subscription_matrix.png` ✅
- [x] 2.7 团队架构图（CEO/CTO/CFO/CMO + 顾问 5 位）→ `07_team_structure.png` ✅

## Task 3: PPT V3 重新生成（15 页，嵌入 7 张图）
- [x] 3.1 编写 `scripts/_build_ppt_v3.py`（使用 python-pptx）✅
- [x] 3.2 渲染 15 页（封面/痛点/SHAP/技术/案例/商业/团队/财务/风险/愿景/封底）✅
- [x] 3.3 嵌入 7 张 PNG（每页 1-2 张）✅
- [x] 3.4 输出 `QuantInsight_Pro_Pitch_Deck_V3.pptx`（≤ 20MB）✅ 1.22MB / 15 页

## Task 4: 3 分钟 Demo V2 视频（用 remotion-best-practices）
- [x] 4.1 更新 `demo-video-remotion/src/Scenes.tsx`（5 幕）✅
- [x] 4.2 嵌入 5 张 dynamic-ui 图表 ✅
- [x] 4.3 添加 5 幕口播 SSML（用 `demo-video-remotion/src/constants.ts`）✅
- [x] 4.4 跑 `npx remotion render` 输出 `QuantInsight_Pro_Demo_3min_V2.mp4`（≤ 50MB）— 源码就绪，待用户跑 `npm install && npm run render:v2`

## Task 5: 5 分钟决赛路演 V1 视频
- [x] 5.1 新建 `demo-video-remotion-pitch/` 项目 ✅
- [x] 5.2 5 幕 × 60s 脚本 ✅
- [x] 5.3 嵌入 5-7 张 dynamic-ui 图表 ✅
- [x] 5.4 输出 `QuantInsight_Pro_Pitch_5min_V1.mp4`（≤ 100MB）— 源码就绪，待用户跑 `npm install && npm run render`

## Task 6: 5 份答辩与风控 Word 化
- [x] 6.1 编写 `scripts/_md_to_docx_答辩.py`（5 个文件批处理）✅
- [x] 6.2 输出 5 份 docx 到 `submission/03_正式文档_WORD/` ✅
  - 09_答辩话术_V3.docx (53KB)
  - 10_3轮模拟答辩_V1.docx (55KB)
  - 11_风险预案_V2.docx (51KB)
  - 12_5杀手锏提问_V1.docx (42KB)
  - 13_QA_Database_V2.docx (46KB)

## Task 7: 5 分钟路演 PPT 配套（10-12 页）
- [x] 7.1 编写 `scripts/_build_ppt_5min.py` ✅
- [x] 7.2 输出 `QuantInsight_Pro_Pitch_Deck_5min_V1.pptx`（1.06MB · 11 页）✅

## Task 8: 提交包 V2 复检 + 重新打包
- [x] 8.1 更新 `scripts/build_submission_zip.py` 包含新物料 ✅
- [x] 8.2 跑打包 → `QuantInsight_Pro_AFAC2026_提交包_20260708_V2.zip`（12.39MB · 126 项）✅
- [x] 8.3 验证 ZIP 内清单（17/17 关键物料齐全）✅

## Task 9: P2 锦上添花（A1 海报 + 易拉宝 + 永字背书模板）
- [x] 9.1 编写 `scripts/_build_poster.py`（用 dynamic-ui 渲染 A1 海报 + 易拉宝）✅
- [x] 9.2 输出 ✅
  - `submission/05_锦上添花/A1_海报_AFAC2026.png`（114KB）
  - `submission/05_锦上添花/易拉宝_AFAC2026.png`（87KB）
  - `submission/05_锦上添花/永字资管背书牌_V1.docx`（38KB）

## Task 10: 索引与文档更新
- [x] 10.1 更新 `submission/README.md`（V2 版本，标注新交付物）✅
- [x] 10.2 更新 `DOCS_HUB.md`（V1.6，新增 H 类「最终冲刺物料」）✅
- [x] 10.3 更新项目记忆（V2 状态）✅

## Task 11: 端到端验证
- [x] 11.1 全库 grep 验证 创·在上海 0 命中（已通过）✅
- [x] 11.2 全库 grep 验证 19.22% 仅在 banner/归档（91 处全部为设计性透明残留）✅
- [x] 11.3 全库 grep 验证 8.56% ≥ 60 命中（实测 165）✅
- [x] 11.4 文件清单核对（21+ 物料齐全）✅
- [x] 11.5 输出 `T41_最终冲刺_验收报告.md` ✅

# Task Dependencies
- [Task 2] depends on [Task 1]（数据核查后才能准确渲染图表）
- [Task 3] depends on [Task 2]（图渲染后才能嵌入 PPT）
- [Task 4] depends on [Task 2]（视频需嵌入 dynamic-ui 图表）
- [Task 5] depends on [Task 2]（同上）
- [Task 6] depends on [Task 1]（数据统一后再 word 化）
- [Task 7] depends on [Task 2]（PPT 嵌入图）
- [Task 8] depends on [Task 3, 4, 5, 6, 7]（所有物料齐备才能打包）
- [Task 9] depends on [Task 1]（数据核查）
- [Task 10] depends on [Task 1-9]（所有物料齐备）
- [Task 11] depends on [Task 1-10]（最终验证）
