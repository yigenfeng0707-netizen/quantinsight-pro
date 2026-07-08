# AFAC2026 初创组 — QuantInsight Pro 提交包索引

**项目编号**：2026FINTECH-FINT-0093  
**参赛组别**：AFAC2026 金融智能创新大赛 · 初创组  
**产品 Demo**：https://3blue1brownlab.cn  
**编制日期**：2026 年 7 月

---

## 提交清单总览

| # | 交付物 | 路径 | 状态 |
|---|--------|------|------|
| 1 | 商业计划书 (Markdown) | [`01_商业计划书_QuantInsight_Pro.md`](01_商业计划书_QuantInsight_Pro.md) | ✅ 完成 |
| 2 | 商业计划书 (可打印 HTML) | [`01_商业计划书_QuantInsight_Pro.html`](01_商业计划书_QuantInsight_Pro.html) | ✅ 完成 |
| 3 | Demo 运行指南 | [`02_Demo交付/README_运行指南.md`](02_Demo交付/README_运行指南.md) | ✅ 完成 |
| 4 | Windows 一键启动 | [`02_Demo交付/启动Demo.bat`](02_Demo交付/启动Demo.bat) | ✅ 完成 |
| 5 | 3 分钟演示视频 | [`02_Demo交付/QuantInsight_Pro_Demo_3min.mp4`](02_Demo交付/QuantInsight_Pro_Demo_3min.mp4) | ⚠️ 脚本就绪，MP4 待录制 |
| 6 | 视频制作脚本 | [`02_Demo交付/Demo视频制作脚本_3min.md`](02_Demo交付/Demo视频制作脚本_3min.md) | ✅ 完成 |
| 7 | 交互设计 HTML | [`02_Demo交付/交互设计与流程图.html`](02_Demo交付/交互设计与流程图.html) | ✅ 完成 |
| 8 | 逻辑流程图 (Mermaid) | [`02_Demo交付/逻辑流程图.md`](02_Demo交付/逻辑流程图.md) | ✅ 完成 |
| 9 | POC 实验数据包 | [`02_Demo交付/POC实验数据/`](02_Demo交付/POC实验数据/) | ✅ 完成 |
| 10 | 可运行产品原型 | [`../streamlit_app/`](../streamlit_app/) | ✅ 已验证 |
| 11 | **正式 Word 文档包** | [`03_正式文档_WORD/`](03_正式文档_WORD/) | ✅ 9 份 DOCX |
| 12 | 生产级测试报告 | [`03_正式文档_WORD/02_生产级测试报告.docx`](03_正式文档_WORD/02_生产级测试报告.docx) | ✅ 21/21 通过 |
| 13 | AFAC 规则对照自评 | [`03_正式文档_WORD/01_AFAC2026_规则对照与评分自评.docx`](03_正式文档_WORD/01_AFAC2026_规则对照与评分自评.docx) | ✅ 自评 88 分 |
| 14 | **提交材料总览** | [`03_正式文档_WORD/00_AFAC2026_提交材料总览.docx`](03_正式文档_WORD/00_AFAC2026_提交材料总览.docx) | ✅ 平台对照 |

---

## 正式 Word 文档包（富文本 DOCX）

生成命令：`python scripts/generate_afac_word_pack.py`

| 文件 | 内容 |
|------|------|
| `00_AFAC2026_提交材料总览.docx` | **平台项目 20260110040 对照 + 材料清单 + 历史文档取舍** |
| `01_AFAC2026_规则对照与评分自评.docx` | 官方要求对照 + 五维评分自评表 + 雷达图 |
| `02_生产级测试报告.docx` | 单元测试 + POC 回测指标 + 策略对比图 |
| `03_Executive_Summary.docx` | 一页纸 Executive Summary |
| `04_评委FAQ手册.docx` | 10 问 10 答 |
| `05_POC实验报告.docx` | T35 HS300 五策略对比 + 图表 |
| `06_技术方案白皮书.docx` | 六层架构 + 技术白皮书 + 架构图 |
| `07_商业计划书.docx` | AFAC 八章节 BP（Word 版） |
| `08_Demo运行与验证指南.docx` | Demo 启动与验证步骤 |

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
| MP4 成品 | ❌ 需用户录制（见脚本「制作方式」章节） |

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
| CEO/主讲 | 冯亦根 | AFAC 参赛队员 |
| CTO | 王宇寒 | AFAC 参赛队员 |
| 产品/数据 | 官馨 | AFAC 参赛队员 |
| 量化/运营 | 梁理智 | AFAC 参赛队员 |
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
- [ ] **3 分钟 MP4 视频待录制**
- [ ] BP PDF（可选：HTML 或 Word 另存为 PDF）
- [x] **HTTPS Demo**（https://3blue1brownlab.cn，复用旧域名 SSL）

---

## 五、待用户操作项

| 优先级 | 事项 | 建议方式 |
|--------|------|----------|
| P0 | 录制 3 分钟 Demo 视频 | OBS 录屏 + `Demo视频制作脚本_3min.md` 旁白 |
| P1 | 导出 BP PDF | 浏览器打开 `01_商业计划书_QuantInsight_Pro.html` → 打印为 PDF |
| P2 | 本地 Demo 实测 | 双击 `启动Demo.bat` 确认页面加载 |

---

## 六、目录结构

```
submission/
├── README.md                              ← 本文件
├── 01_商业计划书_QuantInsight_Pro.md
├── 01_商业计划书_QuantInsight_Pro.html
└── 02_Demo交付/
    ├── README_运行指南.md
    ├── 启动Demo.bat
    ├── Demo视频制作脚本_3min.md
    ├── 交互设计与流程图.html
    ├── 逻辑流程图.md
    ├── QuantInsight_Pro_Demo_3min.mp4       ← 待生成
    └── POC实验数据/
        ├── README.md
        ├── POC实验报告.md
        ├── t35_hs300_summary.json
        ├── t35_hs300_summary.csv
        ├── _backtest_results.json
        ├── _backtest_results_v2.json
        └── _backtest_nav.json
```

---

**联系人**：冯亦根 ceo@3blue1brownlab.cn  
**技术支持**：王宇寒 cto@3blue1brownlab.cn
