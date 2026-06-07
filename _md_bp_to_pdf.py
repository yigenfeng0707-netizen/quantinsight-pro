"""将 BP V2 markdown 转为 PDF (复用白皮书转换器)"""
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                  Preformatted, HRFlowable)

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
pdfmetrics.registerFont(TTFont('Consolas', 'C:/Windows/Fonts/consola.ttf'))
CHINESE_FONT = 'SimHei'

with open('D:/shFintech/QuantInsight_Pro_BP_V2.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

styles = getSampleStyleSheet()
style_normal = ParagraphStyle('Chinese', parent=styles['Normal'],
                                fontName=CHINESE_FONT, fontSize=10, leading=15,
                                textColor=black, alignment=TA_JUSTIFY,
                                spaceBefore=2, spaceAfter=4)
style_h1 = ParagraphStyle('H1', parent=styles['Heading1'],
                            fontName=CHINESE_FONT, fontSize=18, leading=24,
                            textColor=HexColor('#1F4E78'),
                            spaceBefore=18, spaceAfter=10, alignment=TA_LEFT)
style_h2 = ParagraphStyle('H2', parent=styles['Heading2'],
                            fontName=CHINESE_FONT, fontSize=14, leading=20,
                            textColor=HexColor('#2E86AB'),
                            spaceBefore=14, spaceAfter=6, alignment=TA_LEFT)
style_h3 = ParagraphStyle('H3', parent=styles['Heading3'],
                            fontName=CHINESE_FONT, fontSize=12, leading=17,
                            textColor=HexColor('#A23B72'),
                            spaceBefore=10, spaceAfter=4, alignment=TA_LEFT)
style_h4 = ParagraphStyle('H4', parent=styles['Heading4'],
                            fontName=CHINESE_FONT, fontSize=11, leading=15,
                            textColor=HexColor('#5A4FCF'),
                            spaceBefore=8, spaceAfter=3, alignment=TA_LEFT)
style_code = ParagraphStyle('Code', parent=styles['Code'],
                              fontName='Consolas', fontSize=8, leading=11,
                              textColor=HexColor('#222222'),
                              backColor=HexColor('#F0F0F0'),
                              leftIndent=15, rightIndent=15,
                              spaceBefore=4, spaceAfter=8)
style_cover_title = ParagraphStyle('CoverTitle', fontName=CHINESE_FONT,
                                      fontSize=36, leading=44, alignment=TA_CENTER,
                                      textColor=HexColor('#1F4E78'))
style_cover_sub = ParagraphStyle('CoverSub', fontName=CHINESE_FONT,
                                    fontSize=22, leading=28, alignment=TA_CENTER,
                                    textColor=HexColor('#A23B72'))

def escape_rl(text):
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def parse_inline(text):
    text = escape_rl(text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    text = re.sub(r'`([^`]+)`', r'<font name="Consolas" color="#C7254E" bgcolor="#F9F2F4">\1</font>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<font color="#0563C1"><u>\1</u></font>', text)
    return text

story = []
lines = md_content.split('\n')
i = 0
in_code_block = False
code_buffer = []
in_list = False
list_buffer = []

while i < len(lines):
    line = lines[i]
    stripped = line.rstrip()

    if stripped.startswith('```'):
        if not in_code_block:
            in_code_block = True
            code_buffer = []
        else:
            in_code_block = False
            code_text = '\n'.join(code_buffer)
            if code_text.strip():
                story.append(Preformatted(code_text, style_code))
        i += 1
        continue

    if in_code_block:
        code_buffer.append(line)
        i += 1
        continue

    if not stripped.strip():
        if in_list:
            for item in list_buffer:
                story.append(Paragraph(f'• {parse_inline(item)}', style_normal))
            list_buffer = []
            in_list = False
        story.append(Spacer(1, 0.15*cm))
        i += 1
        continue

    if stripped.startswith('# '):
        text = stripped[2:].strip()
        if in_list:
            for item in list_buffer:
                story.append(Paragraph(f'• {parse_inline(item)}', style_normal))
            list_buffer = []
            in_list = False
        story.append(Paragraph(parse_inline(text), style_h1))
    elif stripped.startswith('## '):
        text = stripped[3:].strip()
        if in_list:
            for item in list_buffer:
                story.append(Paragraph(f'• {parse_inline(item)}', style_normal))
            list_buffer = []
            in_list = False
        story.append(Paragraph(parse_inline(text), style_h2))
    elif stripped.startswith('### '):
        text = stripped[4:].strip()
        if in_list:
            for item in list_buffer:
                story.append(Paragraph(f'• {parse_inline(item)}', style_normal))
            list_buffer = []
            in_list = False
        story.append(Paragraph(parse_inline(text), style_h3))
    elif stripped.startswith('#### '):
        text = stripped[5:].strip()
        if in_list:
            for item in list_buffer:
                story.append(Paragraph(f'• {parse_inline(item)}', style_normal))
            list_buffer = []
            in_list = False
        story.append(Paragraph(parse_inline(text), style_h4))
    elif stripped.strip() in ('---', '***', '___'):
        if in_list:
            for item in list_buffer:
                story.append(Paragraph(f'• {parse_inline(item)}', style_normal))
            list_buffer = []
            in_list = False
        story.append(Spacer(1, 0.2*cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#CCCCCC')))
        story.append(Spacer(1, 0.2*cm))
    elif stripped.startswith('> '):
        text = stripped[2:].strip()
        quote_style = ParagraphStyle('Quote', parent=style_normal,
                                        leftIndent=20, rightIndent=10,
                                        textColor=HexColor('#666666'),
                                        borderColor=HexColor('#A23B72'),
                                        borderWidth=0, borderPadding=8,
                                        backColor=HexColor('#F8F9FA'))
        story.append(Paragraph(parse_inline(f'「 {text} 」'), quote_style))
    elif stripped.startswith('- ') or stripped.startswith('* ') or re.match(r'^\d+\.\s', stripped):
        if not in_list:
            in_list = True
            list_buffer = []
        item_text = re.sub(r'^[-*]\s+|^\d+\.\s+', '', stripped)
        list_buffer.append(item_text)
    elif '|' in stripped and i + 1 < len(lines) and re.match(r'^\|?[\s\-:|]+\|?$', lines[i+1].strip()):
        if in_list:
            for item in list_buffer:
                story.append(Paragraph(f'• {parse_inline(item)}', style_normal))
            list_buffer = []
            in_list = False
        table_lines = []
        while i < len(lines) and '|' in lines[i]:
            table_lines.append(lines[i])
            i += 1
            if i < len(lines) and not re.match(r'^[\s\-|:]+$', lines[i]):
                break
        for tl in table_lines[2:]:
            cells = [c.strip() for c in tl.split('|') if c.strip()]
            if cells:
                row_text = ' | '.join(cells)
                story.append(Paragraph(parse_inline(row_text), style_normal))
        continue
    else:
        if in_list:
            for item in list_buffer:
                story.append(Paragraph(f'• {parse_inline(item)}', style_normal))
            list_buffer = []
            in_list = False
        story.append(Paragraph(parse_inline(stripped), style_normal))

    i += 1

if in_list:
    for item in list_buffer:
        story.append(Paragraph(f'• {parse_inline(item)}', style_normal))

# 封面
cover = [
    Spacer(1, 5*cm),
    Paragraph('QuantInsight Pro', style_cover_title),
    Spacer(1, 0.5*cm),
    Paragraph('AI 驱动的另类数据量化投研平台', style_cover_sub),
    Spacer(1, 1*cm),
    Paragraph('商业计划书 V2.0', ParagraphStyle('CoverSub2', fontName=CHINESE_FONT,
                                                     fontSize=20, leading=26, alignment=TA_CENTER,
                                                     textColor=HexColor('#5A4FCF'))),
    Spacer(1, 1.5*cm),
    Paragraph('—— 资管科技 (AssetTech) 子公司视角 ——', ParagraphStyle('CoverSlogan', fontName=CHINESE_FONT,
                                                                          fontSize=14, leading=20, alignment=TA_CENTER,
                                                                          textColor=HexColor('#1F4E78'))),
    Spacer(1, 1*cm),
    Paragraph('慧点资本 (InsightQuant) 量化研究部', ParagraphStyle('CoverInfo', fontName=CHINESE_FONT,
                                                                      fontSize=12, leading=18, alignment=TA_CENTER,
                                                                      textColor=grey)),
    Paragraph('杭州永字资产管理有限公司 (推荐单位)', ParagraphStyle('CoverInfo2', fontName=CHINESE_FONT,
                                                                        fontSize=11, leading=16, alignment=TA_CENTER,
                                                                        textColor=grey)),
    Spacer(1, 0.3*cm),
    Paragraph('项目编号: 2026FINTECH-FINT-0093', ParagraphStyle('CoverID', fontName=CHINESE_FONT,
                                                                   fontSize=10, leading=14, alignment=TA_CENTER,
                                                                   textColor=grey)),
    Paragraph('FinTech@外滩金融科技大赛 · 资管科技赛道', ParagraphStyle('CoverRace', fontName=CHINESE_FONT,
                                                                          fontSize=10, leading=14, alignment=TA_CENTER,
                                                                          textColor=grey)),
    Spacer(1, 1.5*cm),
    Paragraph('2026 年 6 月', ParagraphStyle('CoverDate', fontName=CHINESE_FONT,
                                                fontSize=14, leading=20, alignment=TA_CENTER,
                                                textColor=HexColor('#A23B72'))),
    PageBreak(),
]

output_path = 'D:/shFintech/QuantInsight_Pro_BP_V2.pdf'
doc = SimpleDocTemplate(
    output_path,
    pagesize=A4,
    rightMargin=2.2*cm, leftMargin=2.2*cm,
    topMargin=2*cm, bottomMargin=2*cm
)

doc.build(cover + story)
size_kb = os.path.getsize(output_path) / 1024
print(f'[OK] BP V2 PDF: {output_path}')
print(f'[OK] 大小: {size_kb:.0f} KB')

import pypdf
reader = pypdf.PdfReader(output_path)
print(f'[OK] 页数: {len(reader.pages)}')
