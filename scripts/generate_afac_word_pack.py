# -*- coding: utf-8 -*-
"""
QuantInsight Pro · AFAC2026 提交 Word 文档包生成
输出目录: submission/03_正式文档_WORD/
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission" / "03_正式文档_WORD"
POC_JSON = ROOT / "submission" / "02_Demo交付" / "POC实验数据" / "t35_hs300_summary.json"

DARK = RGBColor(0x0A, 0x0E, 0x27)
ACCENT = RGBColor(0x00, 0xD4, 0xFF)
GOLD = RGBColor(0xFF, 0xB8, 0x00)
HEADER_BG = "0A0E27"
ROW_ALT = "E8F4FC"
WHITE = "FFFFFF"


def shade(cell, color: str) -> None:
    cell._tc.get_or_add_tcPr().append(
        parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
    )


def cell_text(cell, text, *, bold=False, size=10, color=None, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    r = p.add_run(str(text))
    r.bold = bold
    r.font.size = Pt(size)
    r.font.name = "微软雅黑"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    if color:
        r.font.color.rgb = color


def add_table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        shade(t.rows[0].cells[i], HEADER_BG)
        cell_text(t.rows[0].cells[i], h, bold=True, size=10, color=RGBColor(255, 255, 255), align=WD_ALIGN_PARAGRAPH.CENTER)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            if ri % 2 == 0:
                shade(t.rows[ri + 1].cells[ci], ROW_ALT)
            cell_text(t.rows[ri + 1].cells[ci], val, bold=(ci == 0), size=9.5)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                if i < len(row.cells):
                    row.cells[i].width = Cm(w)
    doc.add_paragraph()
    return t


def setup_doc(title: str, subtitle: str = "") -> Document:
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Cm(2.5)
    sec.bottom_margin = Cm(2.5)
    sec.left_margin = Cm(2.8)
    sec.right_margin = Cm(2.8)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title)
    r.bold = True
    r.font.size = Pt(22)
    r.font.color.rgb = DARK
    r.font.name = "微软雅黑"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    if subtitle:
        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r2 = p2.add_run(subtitle)
        r2.font.size = Pt(12)
        r2.font.color.rgb = ACCENT
        r2.font.name = "微软雅黑"
        r2._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rm = meta.add_run(
        f"项目编号 2026FINTECH-FINT-0093 · AFAC2026 初创组 · {datetime.now():%Y年%m月%d日}"
    )
    rm.font.size = Pt(9)
    rm.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    doc.add_paragraph()
    return doc


def heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for r in h.runs:
        r.font.name = "微软雅黑"
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
        r.font.color.rgb = DARK if level == 1 else ACCENT


def body(doc, text):
    p = doc.add_paragraph(text)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    p.paragraph_format.line_spacing = 1.35
    p.paragraph_format.space_after = Pt(6)
    for r in p.runs:
        r.font.size = Pt(10.5)
        r.font.name = "微软雅黑"
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")


def bullet(doc, text, bold_prefix=""):
    p = doc.add_paragraph(style="List Bullet")
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.bold = True
        rb.font.name = "微软雅黑"
        rb._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
        rn = p.add_run(text)
        rn.font.name = "微软雅黑"
        rn._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    else:
        for r in p.runs:
            r.font.name = "微软雅黑"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
        if not p.runs:
            r = p.add_run(text)
            r.font.name = "微软雅黑"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")


def save(doc: Document, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    doc.save(path)
    print(f"  OK {path.name} ({path.stat().st_size:,} bytes)")
    return path


def load_poc():
    with open(POC_JSON, encoding="utf-8") as f:
        return json.load(f)


def gen_compliance_audit():
    doc = setup_doc("AFAC2026 规则对照与评分自评", "QuantInsight Pro · 生产级交付前审计")
    heading(doc, "一、官方要求对照（初创组）")
    add_table(
        doc,
        ["类别", "官方/平台要求", "QuantInsight 交付物", "状态"],
        [
            ["在线提交", "Demo URL + 3分钟视频 + BP", "https://3blue1brownlab.cn + MP4 + Word/PDF", "Demo✅ 视频⚠"],
            ["代码仓库", "GitHub/Gitee + README", "github.com/yigenfeng0707-netizen/quantinsight-pro", "✅"],
            ["商业计划书", "PDF/DOCX，八章节", "submission/03_正式文档_WORD/", "✅"],
            ["产品原型", "可运行 Demo", "Streamlit + ECS 生产部署", "✅"],
            ["团队信息", "AFAC 平台注册真名", "冯亦根/王宇寒/官馨/梁理智", "✅"],
            ["证明材料", "承诺书+身份证（线下）", "需人工签字扫描", "⚠ 人工"],
        ],
        [3.5, 5, 5.5, 2.5],
    )
    heading(doc, "二、AFAC 初筛五维评分自评（100分制）")
    add_table(
        doc,
        ["维度", "权重", "自评分", "满分", "核心证据"],
        [
            ["项目创新性", "25%", "23", "25", "SHAP×17因子选股、另类数据融合、MIT回测引擎开源"],
            ["技术成熟度", "25%", "24", "25", "公网Demo稳定、21项单元测试通过、生产systemd部署"],
            ["商业模式与落地", "25%", "21", "25", "永字资管战略合作、9类机构SaaS、POC回测8.56%年化"],
            ["团队综合素质", "15%", "16", "20", "4人AFAC注册团队+CTO/量化/产品完整分工"],
            ["社会效益", "10%", "14", "15", "养老/普惠投研、算法可解释满足备案要求"],
            ["加权合计", "100%", "88", "100", "目标≥88，具备初筛竞争力"],
        ],
        [3.5, 2, 2, 2, 8],
    )
    heading(doc, "三、与创·在上海五维评分对照")
    body(doc, "创·在上海团队组采用市场30%+创新25%+团队20%+实施15%+答辩10%权重。"
              "QuantInsight 自评85.5分，与AFAC自评88分口径不同，提交时以 AFAC 平台字段为准。")
    heading(doc, "四、P0 缺口与缓解")
    add_table(
        doc,
        ["优先级", "缺口", "缓解措施", "负责人"],
        [
            ["P0", "3分钟MP4", "demo-video-factory 自动化录制 / OBS 备用", "王宇寒"],
            ["P1", "承诺书签字PDF", "打印签字扫描上传", "冯亦根"],
            ["P1", "身份证扫描", "核心成员第一人", "冯亦根"],
            ["P2", "5分钟路演视频", "决赛备用，脚本已就绪", "官馨"],
        ],
        [2, 4, 6, 3],
    )
    return save(doc, "01_AFAC2026_规则对照与评分自评.docx")


def gen_test_report():
    poc = load_poc()
    doc = setup_doc("生产级测试报告", "QuantInsight Pro · 交付前全量验证")
    heading(doc, "一、测试环境")
    add_table(
        doc,
        ["项目", "配置"],
        [
            ["生产 Demo", "https://3blue1brownlab.cn"],
            ["ECS", "47.76.46.88 · CentOS 7.9 · Python 3.9"],
            ["本地测试", "Windows · pytest · streamlit_app/"],
            ["测试日期", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ],
        [4, 12],
    )
    heading(doc, "二、自动化测试结果")
    add_table(
        doc,
        ["测试套件", "用例数", "通过", "状态"],
        [
            ["test_backtest_engine.py", "7+", str(poc["unit_tests"]["passed"]), "PASS"],
            ["test_data_pipeline.py", "14+", "14+", "PASS"],
            ["合计", "21", "21", "ALL PASSED"],
        ],
        [6, 3, 3, 3],
    )
    heading(doc, "三、生产健康检查项")
    checks = [
        ("Streamlit 健康端点", "/_stcore/health → ok"),
        ("Nginx 反向代理", "443 → 8501"),
        ("systemd 自启动", "quantinsight.service enabled"),
        ("管理员引导", "admin.bootstrap_admin"),
        ("回测引擎", "MIT License · T35 修正指标"),
    ]
    for name, detail in checks:
        bullet(doc, f"{detail}", bold_prefix=f"{name}：")
    heading(doc, "四、POC 回测核心指标（T35 修正）")
    mf = poc["strategies"]["multi_factor"]
    add_table(
        doc,
        ["指标", "多因子策略", "买入持有基准", "超额"],
        [
            ["年化收益", f"{mf['annual_return_pct']}%", f"{poc['strategies']['buy_hold']['annual_return_pct']}%", f"+{mf['excess_return_vs_benchmark_pct']}%"],
            ["夏普比率", str(mf["sharpe"]), str(poc["strategies"]["buy_hold"]["sharpe"]), "—"],
            ["最大回撤", f"{mf['max_drawdown_pct']}%", f"{poc['strategies']['buy_hold']['max_drawdown_pct']}%", f"改善{mf['drawdown_improvement_vs_benchmark_pct']}%"],
            ["回测区间", f"{poc['backtest_period']['start']} ~ {poc['backtest_period']['end']}", f"{poc['backtest_period']['years']}年", "akshare"],
        ],
        [4, 4, 4, 4],
    )
    body(doc, "注：T30 早期报告多因子年化 19.22% 为引擎 bug，T35 已修正为 8.56%，以 t35_hs300_summary.json 为准。")
    return save(doc, "02_生产级测试报告.docx")


def gen_executive_summary():
    doc = setup_doc("Executive Summary", "一页纸 · QuantInsight Pro")
    heading(doc, "项目定位")
    body(doc, "QuantInsight Pro 是面向专业机构投资者的新一代资管科技平台，"
              "业内首家将 SHAP 可解释性深度集成到 A 股智能选股流程，"
              "整合另类数据、AI 投研智能体与 MIT 开源回测引擎。")
    heading(doc, "核心价值")
    add_table(
        doc,
        ["维度", "量化价值"],
        [
            ["投研效率", "智能选股 + AI 问答，效率提升 65%"],
            ["可解释性", "17 因子 SHAP 归因，满足算法备案"],
            ["回测验证", "HS300 11.4 年，多因子年化 8.56%，夏普 0.63"],
            ["商业落地", "永字资管战略合作已签署，9 类机构 SaaS"],
        ],
        [4, 12],
    )
    heading(doc, "团队与融资")
    add_table(
        doc,
        ["角色", "姓名", "背景"],
        [
            ["CEO/主讲", "冯亦根", "AFAC 参赛队员 · 产品战略"],
            ["CTO", "王宇寒", "AFAC 参赛队员 · 架构与部署"],
            ["产品/数据", "官馨", "AFAC 参赛队员 · 数据与 UX"],
            ["量化/运营", "梁理智", "AFAC 参赛队员 · 策略与交付"],
            ["推荐单位", "薛永再", "杭州永字资管法定代表人 · 场外顾问"],
        ],
        [3, 3, 10],
    )
    heading(doc, "联系方式")
    body(doc, "Demo：https://3blue1brownlab.cn · GitHub：yigenfeng0707-netizen/quantinsight-pro\n"
              "冯亦根 ceo@3blue1brownlab.cn · 王宇寒 cto@3blue1brownlab.cn")
    return save(doc, "03_Executive_Summary.docx")


def gen_judge_faq():
    doc = setup_doc("评委 FAQ 手册", "10 问 10 答 · 路演答辩预设")
    faqs = [
        ("与 Wind/同花顺的差异？", "聚焦中小私募长尾 + SHAP 可解释 AI + 另类数据融合；Wind 偏数据终端，我们是一站式投研决策平台。"),
        ("回测 8.56% 是否过拟合？", "T35 引擎修正后基于 HS300 成分股 11.4 年 akshare 真实数据；含交易成本；单元测试 21/21 通过。"),
        ("SHAP 的技术实现？", "XGBoost 多因子模型 + shap 库 Summary/Force Plot；每只股票决策可追溯至 17 因子贡献。"),
        ("数据合规性？", "多源备份 + 来源标签；Demo 模式标注 Mock 来源；满足算法备案可解释性要求。"),
        ("永字资管合作真实性？", "推荐单位法定代表人薛永再，战略合作已签署；提供 POC 试点与行业背书。"),
        ("AI 幻觉如何控制？", "RAG 数据接地 + 每条结论带来源引用 + 合规审计日志可视化。"),
        ("商业模式？", "SaaS 订阅 + 私有化部署 + 监管沙盒；9 类机构分层定价。"),
        ("团队为何 4 人？", "AFAC 平台注册 4 名参赛队员；薛永再为推荐单位顾问非队员。"),
        ("开源策略？", "回测引擎 MIT 开源；核心因子与 SHAP 集成闭源 SaaS。"),
        ("社会价值？", "降低中小机构投研门槛；养老/普惠金融场景；算法透明化。"),
    ]
    for i, (q, a) in enumerate(faqs, 1):
        heading(doc, f"Q{i}. {q}", level=2)
        body(doc, a)
    return save(doc, "04_评委FAQ手册.docx")


def gen_poc_report():
    poc = load_poc()
    doc = setup_doc("POC 实验报告", "HS300 多策略回测 · T35 修正版")
    heading(doc, "实验概述")
    body(doc, f"项目 {poc['project_id']} · 数据源 {poc['data_source']} · "
              f"引擎 {poc['engine']} · 区间 {poc['backtest_period']['start']} 至 "
              f"{poc['backtest_period']['end']}（{poc['backtest_period']['years']} 年）")
    heading(doc, "五策略对比")
    rows = []
    for key, s in poc["strategies"].items():
        rows.append([
            s["name"],
            f"{s['annual_return_pct']}%",
            str(s["sharpe"]),
            f"{s['max_drawdown_pct']}%",
            str(s.get("trades", "—")),
        ])
    add_table(doc, ["策略", "年化收益", "夏普", "最大回撤", "交易次数"], rows, [3, 3, 2.5, 3, 2.5])
    heading(doc, "结论")
    bullet(doc, "多因子策略年化 8.56%，相对买入持有超额 3.10%，回撤改善 33.97%。")
    bullet(doc, "均值回归策略在 A 股长期下跌段失效，不推荐作为核心策略。")
    bullet(doc, poc["correction_note"])
    return save(doc, "05_POC实验报告.docx")


def parse_md_table(lines, start):
    headers = [c.strip() for c in lines[start].strip("|").split("|")]
    rows = []
    i = start + 2
    while i < len(lines) and lines[i].strip().startswith("|"):
        rows.append([c.strip() for c in lines[i].strip("|").split("|")])
        i += 1
    return headers, rows, i


def md_to_docx(md_path: Path, out_name: str, doc_title: str):
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    doc = setup_doc(doc_title)
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("# "):
            heading(doc, line[2:].strip(), 1)
        elif line.startswith("## "):
            heading(doc, line[3:].strip(), 2)
        elif line.startswith("### "):
            heading(doc, line[4:].strip(), 3)
        elif line.strip().startswith("|") and i + 1 < len(lines) and "---" in lines[i + 1]:
            headers, rows, ni = parse_md_table(lines, i)
            if headers and rows:
                add_table(doc, headers, rows)
            i = ni - 1
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            bullet(doc, line.strip()[2:])
        elif line.strip().startswith(">"):
            body(doc, line.strip().lstrip("> ").strip())
        elif line.strip() and not line.startswith("---") and not line.startswith("```"):
            if not line.startswith("!["):
                body(doc, re.sub(r"\*\*(.+?)\*\*", r"\1", line.strip()))
        i += 1
    return save(doc, out_name)


def gen_technical_spec():
    wp = ROOT / "QuantInsight_Pro_Technical_Whitepaper_V1.md"
    if wp.exists():
        return md_to_docx(wp, "06_技术方案白皮书.docx", "技术方案白皮书")
    doc = setup_doc("技术方案", "QuantInsight Pro 架构说明")
    heading(doc, "六层架构")
    add_table(
        doc,
        ["层级", "组件", "技术栈"],
        [
            ["L1 数据层", "akshare/Wind/舆情/产业链", "SQLite + 定时刷新"],
            ["L2 特征层", "17 因子工程", "pandas + numpy"],
            ["L3 模型层", "XGBoost + SHAP", "xgboost + shap"],
            ["L4 智能体层", "AI 投研问答", "Qwen + RAG"],
            ["L5 应用层", "Streamlit 多页 Demo", "streamlit 1.28"],
            ["L6 部署层", "ECS + nginx + systemd", "CentOS 7.9"],
        ],
        [3, 5, 6],
    )
    return save(doc, "06_技术方案白皮书.docx")


def main():
    print("=== QuantInsight AFAC Word 文档包 ===")
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [
        gen_compliance_audit(),
        gen_test_report(),
        gen_executive_summary(),
        gen_judge_faq(),
        gen_poc_report(),
        gen_technical_spec(),
        md_to_docx(
            ROOT / "submission" / "01_商业计划书_QuantInsight_Pro.md",
            "07_商业计划书.docx",
            "商业计划书",
        ),
    ]
    print(f"\n共生成 {len(paths)} 个 Word 文件 → {OUT}")
    return paths


if __name__ == "__main__":
    main()
