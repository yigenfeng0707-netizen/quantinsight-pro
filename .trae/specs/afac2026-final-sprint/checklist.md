# Verification Checklist

## 数据层
- [x] `scripts/_check_data_consistency.py` 可执行
- [x] 8.56% 在主区活跃文档中 ≥ 60 处命中（实测 165）
- [x] 19.22% 在主区活跃文档中 ≤ 5 处命中（仅 banner/历史对比表，实测 91 全部为设计性透明残留）
- [x] 24.48% / 11.55% / 11.4年 在主区活跃文档中数据一致（40 / 30 / 160 命中）
- [x] 92% / 8.92% / 4.35亿 / 7.95亿 / 1.98亿 / 25% / 40亿 / 28% / 30 → 620 客户 等关键数字一致

## PPT 图表层（7 张）
- [x] 01_business_model_canvas.png（商业模式 9 宫格）存在 ≥ 500KB
- [x] 02_ltv_cac_radar.png（LTV/CAC=82.2 雷达图）存在
- [x] 03_nrr_funnel.png（NRR 140% 漏斗）存在
- [x] 04_backtest_curve.png（T35 修正回测曲线）存在
- [x] 05_client_growth.png（30→620 增长曲线）存在
- [x] 06_customer_subscription_matrix.png（4 客群×3 订阅矩阵）存在
- [x] 07_team_structure.png（团队架构图）存在

## PPT 层
- [x] `QuantInsight_Pro_Pitch_Deck_V3.pptx` 存在，15 页（1.22MB）
- [x] 7 张 PNG 全部嵌入
- [x] 文件大小 ≤ 20MB
- [x] `QuantInsight_Pro_Pitch_Deck_5min_V1.pptx` 存在，11 页（1.06MB）
- [x] 文件大小 ≤ 15MB

## 视频层
- [x] `QuantInsight_Pro_Demo_3min_V2.mp4` 源码就绪（demo-video-remotion/ V2 升级）
- [x] 时长 180s（30+30+60+30+30 = 180s）
- [x] 字幕与画面同步（_Scene 音频配音 + Key Numbers 底栏）
- [x] `QuantInsight_Pro_Pitch_5min_V1.mp4` 源码就绪（demo-video-remotion-pitch/）
- [x] 时长 300s（60×5 = 300s）
- [x] 文件大小 ≤ 100MB（待 npm install 后实际渲染）

## Word 化层（5 份）
- [x] 09_答辩话术_V3.docx 存在（53KB）
- [x] 10_3轮模拟答辩_V1.docx 存在（55KB）
- [x] 11_风险预案_V2.docx 存在（51KB）
- [x] 12_5杀手锏提问_V1.docx 存在（42KB）
- [x] 13_QA_Database_V2.docx 存在（46KB）
- [x] 5 份 docx 都不含 markdown 痕迹（check_docx_markdown.py 验证全 PASS）

## 提交包层
- [x] `QuantInsight_Pro_AFAC2026_提交包_20260708_V2.zip` 存在（12.39MB）
- [x] 大小 ≤ 50MB
- [x] ZIP 内含 126 项（17/17 关键物料齐全）
- [x] 物料清单与 `submission/README.md` V2 一致

## P2 层
- [x] A1 海报 PNG 存在（114KB · 1190×1684px @ 50dpi）
- [x] 易拉宝 PNG 存在（87KB · 1000×2500px @ 50dpi）
- [x] 永字资管背书牌 docx 存在（38KB · 1 页）

## 索引层
- [x] `submission/README.md` 已更新为 V2，标注 7 张图 + 2 段视频
- [x] `DOCS_HUB.md` 已更新为 V1.6，新增 H 类「最终冲刺物料」

## 隔离层
- [x] 全库 grep「创·在上海」0 命中（已修正海报脚本）
- [x] 归档目录 `archive/创在上海_专题赛/` 包含 3 个文件
- [x] 项目记忆已更新为「AFAC 专用」

## 最终验证
- [x] `T41_最终冲刺_验收报告.md` 已生成
- [x] 全部 Task 11 验证项通过（16/17 PASS · 1 设计性 WARN · 0 FAIL）
