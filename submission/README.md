# AFAC2026 初创组 — QuantInsight Pro 提交包索引

> **📌 V2 头注** · **编制日期：2026-07-08** · **版本状态：V2（最终冲刺版）**
>
> ⚠ **数据统一 T35 修正：HS300 8.56%（修正前 19.22% 旧值）**

**项目编号**：2026FINTECH-FINT-0093  
**参赛组别**：AFAC2026 金融智能创新大赛 · 初创组  
**产品 Demo**：https://3blue1brownlab.cn  
**编制日期**：2026 年 7 月

---

## 🆕 统一交付目录（V2.1 新增 · 2026-07-08）

> **手动上传 AFAC 平台时定位 ≤ 3 秒**

`delivery/` 目录是**专门为手动上传优化的统一交付物目录**，与本目录的物料完全镜像但**结构按平台上传字段重组**：

```
delivery/
├── 00_README_交付总览.md          ← 上传前必读
├── 01_AFAC平台材料/               ← 平台必传
├── 02_商业计划书/                  ← BP V2 PDF
├── 03_PPT/                         ← 2 PPT
├── 04_答辩材料/                    ← 5 docx
├── 05_自评与评分/                  ← 自评打分报告
├── 06_图表素材/                    ← 7 PNG
├── 07_视频/                        ← 视频（1 已就绪 + 2 待渲染）
├── 08_锦上添花/                    ← 海报 + 易拉宝 + 永字背书
├── 09_代码仓库/                    ← GitHub URL
├── 10_完整提交包/                  ← 一站式 ZIP
└── 11_验收报告/                    ← T41 验收报告
```

**重建命令**:
```bash
python scripts/_build_delivery.py
```

---

## 🆕 V2 新增交付物（最终冲刺物料 · 2026-07-08 状态）

> 本节列出 V2 版本中新增/升级的所有交付物（7 图 / 2 视频 / 5 Word / 5 杀手锏 / 3 锦上添花 / 1 ZIP）。

### 🖼️ H1. 7 张图 PNG（`03_正式文档_WORD/_assets/`）

| # | 文件名 | 用途 |
|---|--------|------|
| 1 | [`01_business_model_canvas.png`](03_正式文档_WORD/_assets/01_business_model_canvas.png) | 商业模式画布（9 宫格） |
| 2 | [`02_ltv_cac_radar.png`](03_正式文档_WORD/_assets/02_ltv_cac_radar.png) | LTV/CAC 雷达图 |
| 3 | [`03_nrr_funnel.png`](03_正式文档_WORD/_assets/03_nrr_funnel.png) | NRR 净收入留存漏斗 |
| 4 | [`04_backtest_curve.png`](03_正式文档_WORD/_assets/04_backtest_curve.png) | T35 HS300 多因子回测曲线（8.56% 修正版） |
| 5 | [`05_client_growth.png`](03_正式文档_WORD/_assets/05_client_growth.png) | 客户增长曲线 |
| 6 | [`06_customer_subscription_matrix.png`](03_正式文档_WORD/_assets/06_customer_subscription_matrix.png) | 客户订阅矩阵 |
| 7 | [`07_team_structure.png`](03_正式文档_WORD/_assets/07_team_structure.png) | 团队组织架构 |

### 🎬 H2. 2 段视频

| # | 文件名 | 用途 | 状态 |
|---|--------|------|------|
| 1 | [`02_Demo交付/QuantInsight_Pro_Demo_3min.mp4`](02_Demo交付/QuantInsight_Pro_Demo_3min.mp4) | 3 分钟产品 Demo 视频（V1 终版） | ✅ 完成 |
| 2 | [`02_Demo交付/QuantInsight_Pro_Demo_3min_V2.mp4`](02_Demo交付/) | 3 分钟产品 Demo 视频（V2 修订版） | ⏳ 即将生成 |
| 3 | [`QuantInsight_Pro_Pitch_5min_V1.mp4`](QuantInsight_Pro_Pitch_5min_V1.mp4) | 5 分钟路演 Pitch 视频 V1 | ⏳ 即将生成 |

### 📄 H3. 5 份答辩 Word

| # | 文件名 | 用途 |
|---|--------|------|
| 1 | `01_答辩话术_Word版.docx` | 答辩话术 Word 富文本版 |
| 2 | `02_3轮模拟答辩脚本_Word版.docx` | 3 轮模拟答辩脚本 Word |
| 3 | `03_5杀手锏提问_Word版.docx` | 5 杀手锏提问 Word |
| 4 | `04_评委FAQ手册_Word版.docx` | 评委 FAQ 手册 Word（与 `03_正式文档_WORD/04_评委FAQ手册.docx` 互补） |
| 5 | `05_风险预案_Word版.docx` | 风险预案 Word（V2 富文本版） |

### 🥷 H4. 5 杀手锏提问 docx（独立版本）

| # | 文件名 | 用途 |
|---|--------|------|
| 1 | `01_杀手锏_永字资管实证.docx` | 杀手锏 1：永字资管 4 周 A/B Test 实证 |
| 2 | `02_杀手锏_SHAP可解释性.docx` | 杀手锏 2：SHAP 商业化可解释性白皮书 |
| 3 | `03_杀手锏_回测11.4年.docx` | 杀手锏 3：T35 修正后 11.4 年完整回测 |
| 4 | `04_杀手锏_8.56%数据统一.docx` | 杀手锏 4：HS300 8.56% 数据主动修正 |
| 5 | `05_杀手锏_永字背书函.docx` | 杀手锏 5：永字资管战略合作背书函 |

### 🎁 H5. P2 锦上添花物料

| # | 文件名 | 用途 | 状态 |
|---|--------|------|------|
| 1 | `A1_海报_QuantInsight_Pro_V1.png` | A1 尺寸（594×841mm）项目海报 | ⏳ 即将生成 |
| 2 | `易拉宝_QuantInsight_Pro_V1.png` | 80×200cm 易拉宝主视觉 | ⏳ 即将生成 |
| 3 | `永字资管战略合作背书函_V1.pdf` | 永字资管（薛永再）签章背书函 | ⏳ 即将生成 |

### 📦 H6. 提交包 V2 ZIP

| 文件名 | 用途 |
|--------|------|
| `QuantInsight_Pro_AFAC2026_提交包_V2_20260708.zip` | **V2 最终提交包**（含全部 V2 物料：7 图 / 2 视频 / 5 Word / 5 杀手锏 / 3 P2 物料 / 9 正式 Word / BP / 测试报告） |

> 打包命令：`python scripts/build_submission_zip.py --version V2`

---

## 提交清单总览

| # | 交付物 | 路径 | 状态 |
|---|--------|------|------|
| 0 | **项目 README（Word）** | [`00_项目README_QuantInsight_Pro.docx`](00_项目README_QuantInsight_Pro.docx) | ✅ 完成 |
| 0b | 项目 README（HTML 备份） | [`00_项目README_QuantInsight_Pro.html`](00_项目README_QuantInsight_Pro.html) | ✅ 完成 |
| 0c | 文档归档说明 | [`06_文档归档说明.md`](06_文档归档说明.md) | ✅ 完成 |
| 1 | 商业计划书 (Markdown) | [`01_商业计划书_QuantInsight_Pro.md`](01_商业计划书_QuantInsight_Pro.md) | ✅ 完成 |
| 2 | 商业计划书 (可打印 HTML) | [`01_商业计划书_QuantInsight_Pro.html`](01_商业计划书_QuantInsight_Pro.html) | ✅ 完成 |
| 3 | Demo 运行指南 | [`02_Demo交付/README_运行指南.md`](02_Demo交付/README_运行指南.md) | ✅ 完成 |
| 4 | Windows 一键启动 | [`02_Demo交付/启动Demo.bat`](02_Demo交付/启动Demo.bat) | ✅ 完成 |
| 5 | 3 分钟演示视频（V1 终版） | [`02_Demo交付/QuantInsight_Pro_Demo_3min.mp4`](02_Demo交付/QuantInsight_Pro_Demo_3min.mp4) | ✅ V3 电影级（179.9s，~3.0 MB，无字幕+BGM） |
| 5b | 3 分钟演示视频（V2 修订版） | [`02_Demo交付/QuantInsight_Pro_Demo_3min_V2.mp4`](02_Demo交付/) | ⏳ 即将生成（H2） |
| 6 | Demo 录制脚本 V4 | [`02_Demo交付/AFAC_Demo_录制脚本_V4.md`](02_Demo交付/AFAC_Demo_录制脚本_V4.md) | ✅ 8 幕 · 180s · SSML |
| 6b | 视频状态 | [`02_Demo交付/VIDEO_STATUS.md`](02_Demo交付/VIDEO_STATUS.md) | ✅ ffprobe 验证 |
| 6c | 旧版脚本（参考） | [`02_Demo交付/Demo视频制作脚本_3min.md`](02_Demo交付/Demo视频制作脚本_3min.md) | 📄 已被 V4 取代 |
| 7 | 交互设计 HTML | [`02_Demo交付/交互设计与流程图.html`](02_Demo交付/交互设计与流程图.html) | ✅ 完成 |
| 8 | 逻辑流程图 (Mermaid) | [`02_Demo交付/逻辑流程图.md`](02_Demo交付/逻辑流程图.md) | ✅ 完成 |
| 9 | POC 实验数据包 | [`02_Demo交付/POC实验数据/`](02_Demo交付/POC实验数据/) | ✅ 完成 |
| 10 | 可运行产品原型 | [`../streamlit_app/`](../streamlit_app/) | ✅ 已验证 |
| 11 | **正式 Word 文档包** | [`03_正式文档_WORD/`](03_正式文档_WORD/) | ✅ 9 份 DOCX + 富文本 v2 |
| 11b | **AFAC 自评打分报告** | [`07_AFAC2026_自评打分报告.docx`](07_AFAC2026_自评打分报告.docx) | ✅ 六维 86 分 |
| 12 | 生产级测试报告 | [`03_正式文档_WORD/02_生产级测试报告.docx`](03_正式文档_WORD/02_生产级测试报告.docx) | ✅ 21/21 通过 |
| 13 | AFAC 规则对照自评 | [`03_正式文档_WORD/01_AFAC2026_规则对照与评分自评.docx`](03_正式文档_WORD/01_AFAC2026_规则对照与评分自评.docx) | ✅ 自评 88 分 |
| 14 | **提交材料总览** | [`03_正式文档_WORD/00_AFAC2026_提交材料总览.docx`](03_正式文档_WORD/00_AFAC2026_提交材料总览.docx) | ✅ 平台对照 |

---

## 正式 Word 文档包（富文本 DOCX v2）

生成命令：

```bash
python scripts/generate_afac_word_pack.py
python scripts/check_docx_markdown.py   # 质量门禁：markdown 痕迹应为 0
```

> **v2 更新（2026-07）**：全部 DOCX 由 `md_to_docx_rich.py` 渲染为原生 Word 元素（标题样式、加粗斜体、表格、列表、超链接），不再残留 `#`、`**`、`| 表格 |` 等 Markdown 痕迹。配套 matplotlib 架构图/数据流/团队架构/回测对比图嵌入 06 白皮书、07 BP、01/02 报告与 00 README。

> **团队信息变更后**：请先同步根目录 Markdown 源文件，再重新运行上述命令以更新 `03_正式文档_WORD/` 内全部 DOCX（勿手动编辑二进制 docx）。

| 文件 | 内容 |
|------|------|
| `00_AFAC2026_提交材料总览.docx` | **平台项目 20260110040 对照 + 材料清单 + 历史文档取舍** |
| `01_AFAC2026_规则对照与评分自评.docx` | 官方要求对照 + 架构/数据流/团队图 + 五维评分 |
| `02_生产级测试报告.docx` | 单元测试 + POC 回测指标 + 策略对比图 |
| `03_Executive_Summary.docx` | 一页纸 Executive Summary + 团队架构图 |
| `04_评委FAQ手册.docx` | 10 问 10 答 |
| `05_POC实验报告.docx` | T35 HS300 五策略对比 + 图表（质量基准，原生生成） |
| `06_技术方案白皮书.docx` | 六层架构 + 技术白皮书 + 专业示意图 |
| `07_商业计划书.docx` | AFAC 八章节 BP（Word 富文本版 + 附录图表） |
| `08_Demo运行与验证指南.docx` | Demo 启动与验证步骤 |
| `07_AFAC2026_自评打分报告.docx` | **六维自评矩阵 + 优劣势 + 预估奖项区间** |
**ZIP 打包**：`python scripts/build_submission_zip.py` → `submission/QuantInsight_Pro_AFAC2026_提交包_YYYYMMDD.zip`

## 一、商业计划书

**文件**：`01_商业计划书_QuantInsight_Pro.md`

AFAC 标准八章节结构：

1. 执行摘要
2. 市场分析
3. 产品与技术方案（含 SHAP + 六层架构）
4. 商业模式
5. 团队介绍（冯亦根/王宇寒/官馨/梁理智 + 薛永再场外顾问）
6. 财务预测
7. 风险评估
8. 落地案例（永字资管战略合作已签署）

**PDF 说明**：环境无 weasyprint/reportlab，已提供可打印 HTML 版本。浏览器打开 HTML → Ctrl+P → 另存为 PDF。

---

## 二、Demo 交付包

### 2a. 可运行产品原型

| 项目 | 说明 |
|------|------|
| 源码位置 | `streamlit_app/` |
| 在线地址 | https://3blue1brownlab.cn |
| 本地启动 | 双击 `02_Demo交付/启动Demo.bat` |
| 验证结果 | `app.py` 语法通过 · 回测引擎 7/7 测试通过 |

### 2b. 3 分钟演示视频

| 项目 | 状态 |
|------|------|
| 分镜脚本 | ✅ `Demo视频制作脚本_3min.md` |
| SRT 字幕素材 | ✅ 仓库根目录 4 个 .srt 文件 |
| MP4 成品 | ✅ `02_Demo交付/QuantInsight_Pro_Demo_3min.mp4`（180s，~9.3 MB） |

### 2c. 交互设计与流程图

| 文件 | 格式 | 内容 |
|------|------|------|
| `交互设计与流程图.html` | 自包含 HTML | 用户旅程 + 六层架构 + 4 屏线框 + 数据流 + T35 指标表 |
| `逻辑流程图.md` | Mermaid | 6 张流程图（旅程/架构/数据流/时序/合作/柱状图） |

品牌色：#0A0E27 / #00D4FF / #FFB800

### 2d. POC 实验数据

| 文件 | 说明 |
|------|------|
| `POC实验报告.md` | HS300 11.4 年完整实验报告 |
| `README.md` | 指标定义 + 复现方法 |
| `t35_hs300_summary.json` | T35 修正结构化摘要 |
| `t35_hs300_summary.csv` | Excel 友好导出 |
| `_backtest_results.json` | 早期回测原始数据 |
| `_backtest_results_v2.json` | 三指数五策略完整结果 |
| `_backtest_nav.json` | 日频净值序列 |

**核心指标（T35 修正）**：多因子年化 **8.56%** · 夏普 **0.63** · 最大回撤 **-38.33%**

---

## 三、团队信息（权威）

| 角色 | 姓名 | 说明 |
|------|------|------|
| CEO/主讲 | 冯亦根 | 浙江大学计算机通信工程本科、亚洲城市大学硕士，慧点资本创始人，CFA，15+ 年金融科技投资，项目总负责人 |
| CTO | 王宇寒 | 杭州电子科技大学软件工程专业 2022级本科，平台开发与 AI 工程 |
| 产品/数据 | 官馨 | 陕西师范大学人工智能专业大三学生，产品设计与客户研究 |
| AI/量化负责人 | 梁理智 | 河北科技大学，翼支付 AI 开发者，金融科技师（二级）证书，金融业务产业落地 |
| 推荐单位/顾问 | 薛永再 | 杭州永字资管法定代表人，**场外顾问，非参赛队员** |

**永字合作状态**：战略合作已签署（不披露具体金额）

---

## 四、提交前检查清单

- [x] 商业计划书八章节完整
- [x] 团队使用 AFAC 平台真名
- [x] 永字合作标注「已签署」
- [x] 回测数据使用 T35 修正值（8.56%）
- [x] Demo 语法 + 单元测试通过
- [x] 交互设计 HTML 自包含可打开
- [x] POC 数据包完整
- [x] **Word 文档包 7 份**（`03_正式文档_WORD/`）
- [x] **生产级测试 21/21 通过**
- [x] **FinAgent 旧项目已归档**（`_archive/`）
- [x] **3 分钟 MP4 视频（V1 终版）** — `02_Demo交付/QuantInsight_Pro_Demo_3min.mp4`（180s，~9.3 MB）
- [ ] BP PDF（可选：HTML 或 Word 另存为 PDF）
- [x] **HTTPS Demo**（https://3blue1brownlab.cn，复用旧域名 SSL）

### V2 新增检查项（最终冲刺）

- [x] **H1 7 张图 PNG**（`03_正式文档_WORD/_assets/` 全部就位）
- [x] **H2a 3 分钟 Demo V1 终版** MP4（已完成）
- [ ] **H2b 3 分钟 Demo V2 修订版** MP4（即将生成）
- [ ] **H2c 5 分钟路演 Pitch V1** MP4（即将生成）
- [ ] **H3 5 份答辩 Word**（即将生成）
- [ ] **H4 5 杀手锏 docx**（即将生成）
- [ ] **H5a A1 海报**（即将生成）
- [ ] **H5b 易拉宝**（即将生成）
- [ ] **H5c 永字背书函**（即将生成）
- [ ] **H6 提交包 V2 ZIP**（待 H1-H5 全部就绪后打包）

---

## 五、待用户操作项

| 优先级 | 事项 | 建议方式 |
|--------|------|----------|
| P0 | ~~录制 3 分钟 Demo 视频~~ | ✅ 已完成（见 `02_Demo交付/QuantInsight_Pro_Demo_3min.mp4`） |
| P1 | 导出 BP PDF | 浏览器打开 `01_商业计划书_QuantInsight_Pro.html` → 打印为 PDF |
| P2 | 本地 Demo 实测 | 双击 `启动Demo.bat` 确认页面加载 |

---

## 六、目录结构

```
submission/
├── README.md                              ← 本文件（V2）
├── 01_商业计划书_QuantInsight_Pro.md
├── 01_商业计划书_QuantInsight_Pro.html
├── 02_Demo交付/
│   ├── README_运行指南.md
│   ├── 启动Demo.bat
│   ├── Demo视频制作脚本_3min.md
│   ├── 交互设计与流程图.html
│   ├── 逻辑流程图.md
│   ├── QuantInsight_Pro_Demo_3min.mp4       ← 已完成（180s，V1 终版）
│   ├── QuantInsight_Pro_Demo_3min_V2.mp4   ← 即将生成（V2 修订版）
│   └── POC实验数据/
│       ├── README.md
│       ├── POC实验报告.md
│       ├── t35_hs300_summary.json
│       ├── t35_hs300_summary.csv
│       ├── _backtest_results.json
│       ├── _backtest_results_v2.json
│       └── _backtest_nav.json
├── 03_正式文档_WORD/                       ← 9 份正式 Word + _assets
│   ├── 00_AFAC2026_提交材料总览.docx
│   ├── 01_AFAC2026_规则对照与评分自评.docx
│   ├── 02_生产级测试报告.docx
│   ├── 03_Executive_Summary.docx
│   ├── 04_评委FAQ手册.docx
│   ├── 05_POC实验报告.docx
│   ├── 06_技术方案白皮书.docx
│   ├── 07_商业计划书.docx
│   ├── 08_Demo运行与验证指南.docx
│   └── _assets/                            ← H1 7 张图 PNG
│       ├── 01_business_model_canvas.png
│       ├── 02_ltv_cac_radar.png
│       ├── 03_nrr_funnel.png
│       ├── 04_backtest_curve.png
│       ├── 05_client_growth.png
│       ├── 06_customer_subscription_matrix.png
│       └── 07_team_structure.png
├── 04_测试报告/                            ← e2e + smoke 测试报告
├── 05_团队信息一致性核查报告.md
├── 06_文档归档说明.md
├── 07_AFAC2026_自评打分报告.md/.docx
│
├── [H2c 5min Pitch]  QuantInsight_Pro_Pitch_5min_V1.mp4        ← 即将生成（根目录）
├── [H3 5 答辩 Word]  01_答辩话术_Word版.docx … 05_风险预案_Word版.docx
├── [H4 5 杀手锏]     01_杀手锏_永字资管实证.docx … 05_杀手锏_永字背书函.docx
├── [H5 P2 物料]
│   ├── A1_海报_QuantInsight_Pro_V1.png
│   ├── 易拉宝_QuantInsight_Pro_V1.png
│   └── 永字资管战略合作背书函_V1.pdf
│
└── [H6 V2 提交包]   QuantInsight_Pro_AFAC2026_提交包_V2_20260708.zip
```

---

**联系人**：冯亦根 ceo@3blue1brownlab.cn  
**技术支持**：王宇寒 cto@3blue1brownlab.cn
