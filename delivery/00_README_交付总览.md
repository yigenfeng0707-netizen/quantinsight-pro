# AFAC2026 统一交付目录 · delivery/

> **生成日期**: 2026-07-08
> **项目**: QuantInsight Pro · AI 驱动的另类数据量化投研平台
> **组别**: AFAC2026 金融智能创新大赛 · 初创组
> **生成工具**: `scripts/_build_delivery.py`

---

## 📂 目录结构

```
delivery/
├── 00_README_交付总览.md          ← 你正在读
├── 01_AFAC平台材料/               ← 平台必传（线下保管占位）
├── 02_商业计划书/                  ← BP V2 PDF + V3 HTML/MD
├── 03_PPT/                         ← 2 份 PPT（V3 + 5min V1）
├── 04_答辩材料/                    ← 5 份 docx
├── 05_自评与评分/                  ← 自评打分报告（md + docx）
├── 06_图表素材/                    ← 7 张 PNG
├── 07_视频/                        ← 3 段 MP4（1 已就绪 + 2 待渲染）
├── 08_锦上添花/                    ← A1 海报 + 易拉宝 + 永字背书
├── 09_代码仓库/                    ← GitHub URL
├── 10_完整提交包/                  ← 一站式 ZIP
└── 11_验收报告/                    ← T41 验收报告
```

---

## 📤 AFAC 平台上传清单

| 平台字段 | 上传文件 | 目录 | 状态 |
|---------|---------|------|------|
| **承诺书** | `承诺书_冯亦根签字扫描.pdf` | 01_AFAC平台材料/ | ✅ 线下已签 |
| **CEO 身份证** | `身份证_冯亦根正反面扫描.pdf` | 01_AFAC平台材料/ | ✅ 线下已上传 |
| **商业计划书** | `QuantInsight_Pro_BP_V2.pdf` | 02_商业计划书/ | ✅ 已就绪 |
| **Demo URL** | `https://3blue1brownlab.cn` | - | ✅ 已部署 |
| **Demo 视频** | `QuantInsight_Pro_Demo_3min_V1_终版.mp4` | 07_视频/ | ✅ 已就绪 |
| **PPT 演示** | `QuantInsight_Pro_Pitch_Deck_V3.pptx` | 03_PPT/ | ✅ 已就绪 |
| **代码仓库** | https://github.com/yigenfeng0707-netizen/quantinsight-pro | 09_代码仓库/ | ✅ 已公开 |
| **自评报告** | `07_AFAC2026_自评打分报告.docx` | 05_自评与评分/ | ✅ 已就绪 |
| **团队信息** | 在线填写（4 人已填）| - | ✅ 已填 |

---

## ✅ 自检清单

### 数据层面
- [x] HS300 8.56% (T35 修正) 全库统一（151 处命中）
- [x] ZZ500 24.48% / CYB 11.55% 一致
- [x] 19.22% 仅在 banner/历史对比表（设计性透明残留）
- [x] 创·在上海 主区 0 处残留（已归档独立项目）

### 文档层面
- [x] BP PDF / MD / HTML 三版本齐备
- [x] PPT V3 (15页) + 5min V1 (11页) 嵌入 7 张图
- [x] 5 份答辩 docx 无 markdown 痕迹
- [x] 3 份 P2 锦上添花
- [x] 1 份完整提交包 ZIP（12.39 MB · 126 项 · 17/17 关键文件）

### 平台层面
- [x] 承诺书（冯亦根签字+扫描）2026-07-08 完成
- [x] 冯亦根身份证正反面 2026-07-08 已上传
- [x] 永字资管合作协议 2026-07-08 已签（替代 LOI + 背书视频）

### 用户手动剩余（4 项）
- [ ] 浏览器打印 `02_商业计划书/QuantInsight_Pro_BP_V3.html` → PDF（备用）
- [ ] JFE 论文摘要（学术写作）
- [ ] Demo V2 视频渲染（`cd demo-video-remotion && npm install && npm run render:v2`）
- [ ] 5min 视频渲染（`cd demo-video-remotion-pitch && npm install && npm run render`）

---

## 📊 自评总分：88/100

| 维度 | 权重 | 自评 |
|------|------|------|
| 项目创新性 | 25% | 22/25 |
| 技术成熟度 | 25% | 23/25 |
| 商业模式与落地 | 25% | 22/25 |
| 团队综合素质 | 15% | 12/15 |
| 社会效益 | 10% | 9/10 |

**等级**: 二等奖偏上 / 一等奖临界

---

## 🔧 重新生成本目录

如需重新整理交付物：
```bash
cd d:\AFAC2026金融智能创新大赛\quantinsight-deploy
python scripts/_build_delivery.py
```

报告生成: Trae Spec Mode Auto-Build · 2026-07-08
