# AFAC2026 终极冲刺 全量执行 Spec

## Why
距离 AFAC2026 提交截止（用户自述）日期迫近，需一次性解决所有可自动化的材料问题：数据一致性、PPT 专业图表、视频重制、答辩 word 化、提交包复检、锦上添花物料。**用户负责**：AFAC 平台材料（承诺书/身份证）、BP PDF 浏览器打印。**项目主体负责**：所有可在本地自动完成的工作。

## What Changes

### 数据质量层
- [ ] 跨文件数据一致性 100% 核查脚本（剩余 8.56% / 24.48% / 11.55% / 11.4年 等关键数字全库扫描）
- [ ] 关键文件数字哈希报告

### PPT 专业渲染层
- [ ] 7 张 dynamic-ui 高保真图表（SVG/HTML 输出 → PNG）
  - 商业模式 9 宫格
  - LTV/CAC 雷达图（=82.2）
  - NRR 140% 漏斗
  - T35 修正回测曲线（HS300 8.56% / ZZ500 24.48% / CYB 11.55%）
  - 30→620 客户增长曲线
  - 4 客群 × 3 订阅矩阵
  - 团队架构图
- [ ] 嵌入 `Pitch_Deck_V2.pptx` 重新生成（15 页）
- [ ] 重新输出 Pitch_Deck_V3.pptx

### Demo 视频重制层
- [ ] 用 `remotion-best-practices` 重制 3 分钟 Demo 视频
  - 5 幕：开场 30s / 痛点 30s / 技术 SHAP 60s / POC 回测 30s / 商业 30s
  - 嵌入 5 张 dynamic-ui 图表
  - 1920×1080@30fps，音视频字幕完全同步
- [ ] 输出 `QuantInsight_Pro_Demo_3min_V2.mp4`

### 5 分钟决赛路演视频层
- [ ] 用 `remotion-best-practices` 制作 5 分钟决赛路演视频
  - 5 幕 × 60s = 300s
  - 嵌入 5-7 张 dynamic-ui 图表
  - 音视频字幕完全同步
- [ ] 输出 `QuantInsight_Pro_Pitch_5min_V1.mp4`

### 答辩与风控 Word 化层
- [ ] 答辩话术 V3 word 版（25 高频问题）
- [ ] 3 轮模拟答辩脚本 V1 word 版
- [ ] 风险预案 V2 word 版
- [ ] 5 杀手锏提问 V1 word 版
- [ ] QA_Database_V2 word 版（30 题）

### 5 分钟路演 PPT 配套层
- [ ] 5 分钟路演 PPT（与 5 分钟视频配套，10-12 页）

### 提交包复检层
- [ ] 重新跑 `build_submission_zip.py`
- [ ] 校验 ZIP 内文件清单 + 关键数字
- [ ] 输出 `QuantInsight_Pro_AFAC2026_提交包_20260708_V2.zip`

### 锦上添花层（P2）
- [ ] A1 海报 PNG（用 dynamic-ui 渲染）
- [ ] 易拉宝 PNG（用 dynamic-ui 渲染）
- [ ] 永字资管背书模板（1 页 word）

### 索引与文档层
- [ ] 更新 `submission/README.md`（标注新交付物）
- [ ] 更新 `DOCS_HUB.md`（V1.6 新增 7 张图表 + V2 视频）
- [ ] 更新项目记忆

## Impact

- **Affected specs**: AFAC2026 初创组提交通道
- **Affected code**: `scripts/_build_ppt_v2.py`, `scripts/build_submission_zip.py`, `scripts/afac_charts.py`, `demo-video-remotion/`
- **Affected docs**: `submission/03_正式文档_WORD/`, `submission/02_Demo交付/`, `DOCS_HUB.md`, `submission/README.md`
- **Affected data**: 7 张 PNG/SVG 图表，2 段 MP4，1 份 ZIP，5 份 word

## ADDED Requirements

### Requirement: 数据一致性 100% 核查
系统 SHALL 提供一个 Python 脚本，扫描主区活跃 MD/docx/PDF/PNG 中所有量化数字，输出关键数字（T35 修正值、市场规模、客户数、订阅价格、年化等）一致性报告。

#### Scenario: 数字冲突
- **WHEN** 扫描发现 19.22% 残留（除 banner/归档外）
- **THEN** 报告列出文件 + 行号 + 建议修正值

#### Scenario: 数字一致
- **WHEN** 扫描发现 8.56% 命中数 ≥ 60
- **THEN** 输出"✅ T35 修正值已全库统一"

### Requirement: PPT V3 嵌入 dynamic-ui 图表
系统 SHALL 使用 `PureShowWidget` / `dynamic-ui` skill 渲染 7 张高保真图表，并以 PNG 形式嵌入 `QuantInsight_Pro_Pitch_Deck_V3.pptx`。

#### Scenario: 渲染成功
- **WHEN** 7 张图表全部生成
- **THEN** 重新生成 PPT，每页含 1-2 张图 + 文字 + 演讲话术

#### Scenario: 渲染失败
- **WHEN** 某张图 dynamic-ui 失败
- **THEN** 跳过该图，继续生成其他图，并在最后报告"⚠ X 号图缺失"

### Requirement: 3 分钟 Demo V2 视频
系统 SHALL 使用 `remotion-best-practices` skill 制作 1920×1080@30fps、3 分钟（180s ± 5s）的 Demo 视频。

#### Scenario: 视频生成
- **WHEN** 5 幕脚本 + 5 张图表 + 音轨就绪
- **THEN** 输出 MP4，大小 ≤ 50MB

### Requirement: 5 分钟决赛路演 V1 视频
系统 SHALL 使用 `remotion-best-practices` skill 制作 1920×1080@30fps、5 分钟（300s ± 5s）的路演视频。

#### Scenario: 视频生成
- **WHEN** 5 幕脚本 + 5-7 张图表 + 音轨就绪
- **THEN** 输出 MP4，大小 ≤ 100MB

### Requirement: 答辩与风控 Word 化
系统 SHALL 将 5 份 MD 文档（答辩话术 V3、3 轮模拟答辩、风险预案 V2、5 杀手锏、QA_Database_V2）转换为 word DOCX 格式，保留原结构与高保真样式。

#### Scenario: 转换成功
- **WHEN** MD 文件已存在
- **THEN** 输出同名 .docx 在 `submission/03_正式文档_WORD/`

### Requirement: 提交包 V2 复检
系统 SHALL 重新打包 `build_submission_zip.py`，并校验 ZIP 内关键文件存在。

#### Scenario: 打包成功
- **WHEN** 所有 7 类文件齐全
- **THEN** 输出 `_V2.zip` ≤ 50MB

## MODIFIED Requirements

### Requirement: submission/README.md
V1.0 列表已过时，新增 7 张图表 + V2 视频条目。V2 版本 SHALL 包含更新后的清单。

### Requirement: DOCS_HUB.md
V1.5 列表已过时，新增 7 张图表 + V2 视频条目。V1.6 版本 SHALL 在 A-G 7 大类基础上新增 H 类「最终冲刺物料」。

## REMOVED Requirements

无（保留所有现有交付物，仅增量）。

---

## 用户边界（明确不自动化项）

> **用户** 自行负责：
> 1. ~~AFAC 平台登录 → 下载 AFAC 自己的承诺书 + 签字 + 扫描~~ ✅ 2026-07-08 已完成
> 2. ~~AFAC 平台登录 → 上传冯亦根身份证正反面扫描~~ ✅ 2026-07-08 已完成
> 3. 浏览器打印 `01_商业计划书_QuantInsight_Pro.html` → PDF
> 4. ~~5 校 MOU 实签~~（已下线，与永字资管合作替代学校 MOU 路径）
> 5. ~~顾问委员会正式邀请~~（已下线）
> 6. ~~软著加急~~（已下线，团队已有自有软著）
> 7. ~~LOI 实签~~ ✅ 2026-07-08 永字资管已签约
> 8. ~~永字法人背书视频~~（已下线，2026-07-08 永字资管合作协议已替代背书视频）
> 9. JFE 论文摘要（需学术写作）
> 10. 视频最终渲染：`cd demo-video-remotion && npm install && npm run render:v2`
> 11. 视频最终渲染：`cd demo-video-remotion-pitch && npm install && npm run render`

> **本 Spec 自动化覆盖**：上述以外的所有可脚本化任务。
