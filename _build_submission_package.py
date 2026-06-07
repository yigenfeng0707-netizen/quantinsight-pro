"""
T21 提交包整合 - 创建 ZIP 压缩包
排除中间产物 (_开头的脚本/_test_/_build_/_data_/_chart_/_video_/_t11_/_t12_/_narration/_tts/_backtest_/_generate_等)
只保留最终交付物
"""
import os
import zipfile
from datetime import datetime

# 输出路径
output_zip = f'D:/shFintech/QuantInsight_Pro_提交包_v1.0_{datetime.now().strftime("%Y%m%d")}.zip'

# 需要排除的中间产物
EXCLUDE_PATTERNS = [
    '_test_', '_build_', '_data_', '_chart_', '_video_', '_t11_', '_t12_',
    '_narration', '_tts_', '_backtest_', '_generate_', '_read_', '_check_',
    '_verify_', '_regen_', '_md_to_', '_md_bp_', '_streamlit_',
    'akshare', 'pypdf', 'openpyxl', 'python-docx',
    'requirements', '__pycache__', '.pyc', '.log',
    'Thumbs.db', 'Desktop.ini',
    # 原始 PDF 和提取文件 (有 V2 替代)
    'QuantInsight Pro - 商业计划书_extracted.txt',
    # 老的中间文件
    'QuantInsight_Pro_Project_PDF_extracted.txt',
    'QuantInsight_Pro_BP.md',  # 旧 BP
    'QuantInsight_Pro_Pitch_Deck.md',  # 旧 Pitch Deck
    'QuantInsight_Pro_Pitch_Deck.html',  # 旧 HTML
    'QuantInsight_Pro_Pitch_Training.md',
    'QuantInsight_Pro_BP_备份版.html',
    'QuantInsight_Pro_Demo_Video.html',  # 旧 HTML
    'QuantInsight_Pro_Financial_Model.xlsx',  # 旧 V1
    'QuantInsight_Pro_QA.md',  # 旧 QA
    'QuantInsight_Pro_QA_Database.md',  # 旧 QA
    'QuantInsight_Pro_Tech_Video_v1_ai_qa.srt',  # 重复
    'QuantInsight_Pro_Tech_Video_v2_backtest.srt',
    'QuantInsight_Pro_Tech_Video_v3_alt_data.srt',
    'QuantInsight_Pro_Tech_Video_v1_ai_qa.mp4',  # 在 T11 重复
    'QuantInsight_Pro_Tech_Video_v2_backtest.mp4',
    'QuantInsight_Pro_Tech_Video_v3_alt_data.mp4',
    'QuantInsight_Pro_Chart_01_Financial.png',  # 旧 V2 图表
    'QuantInsight_Pro_Project_PDF_extracted.txt',
    '_commitment_extracted.txt',
    '_backtest_nav.json', '_backtest_results.json',
    'QuantInsight_Pro_Pitch_Presenter_Video.srt',  # 重复
    'QuantInsight_Pro_BP.md',  # 旧 BP
    'QuantInsight_Pro_BP_备份版.html',  # 旧 HTML
    'QuantInsight_Pro_Tech_Video_v1_ai_qa',  # T11
    'QuantInsight_Pro_Tech_Video_v2_backtest',
    'QuantInsight_Pro_Tech_Video_v3_alt_data',
    'QuantInsight Pro - 商业计划书.pdf',  # 旧版
]

# 必需包含的文件
INCLUDED_FILES = [
    'README.md',
    'QuantInsight_Pro_BP_V2.md',
    'QuantInsight_Pro_BP_V2.pdf',
    'QuantInsight_Pro_Pitch_Deck_V2.pptx',
    'QuantInsight_Pro_Financial_Model_V3.xlsx',
    'QuantInsight_Pro_Financial_Report_V3.md',
    'QuantInsight_Pro_Chart_01_Financial.png',
    'QuantInsight_Pro_Technical_Whitepaper_V1.md',
    'QuantInsight_Pro_Technical_Whitepaper_V1.pdf',
    'QuantInsight_Pro_Demo_Video_Final.mp4',
    'QuantInsight_Pro_Demo_Video_V1.srt',
    'QuantInsight_Pro_Pitch_Presenter_Video.mp4',
    'QuantInsight_Pro_QA_Database_V2.md',
    'QuantInsight_Pro_Team_Compliance_DR_V1.md',
    'QuantInsight_Pro_Third_Party_Review_V1.md',
    # 验收报告
    'T06_视频验收报告.md',
    'T07_T10_综合包_验收报告.md',
    'T11_短视频验收报告.md',
    'T12_路演视频验收报告.md',
    'T13_技术白皮书_验收报告.md',
    'T15_财务重写_验收报告.md',
    'T16_BP_V2_验收报告.md',
    'T17_PPT_V2_验收报告.md',
    'T18_QA升级_验收报告.md',
    'T19_团队合规灾备升级_验收报告.md',
    'T20_第三方盲评_验收报告.md',
]

# 客户证据包
EVIDENCE_FILES = [
    '_evidence_pack/T07_expert_perspectives.md',
    '_evidence_pack/T08_public_case_studies.md',
    '_evidence_pack/T09_academic_backing.md',
    '_evidence_pack/T10_pilot_report.md',
    '_evidence_pack/T10_pilot_backtest_chart.png',
    '_evidence_pack/T07_T10_综合包_验收报告.md',
]

# Streamlit Demo 包
STREAMLIT_FILES = []
streamlit_dir = 'D:/shFintech/streamlit_app'
if os.path.exists(streamlit_dir):
    for f in os.listdir(streamlit_dir):
        if not f.startswith('__') and not f.endswith('.pyc'):
            STREAMLIT_FILES.append(f'streamlit_app/{f}')

# 创建 ZIP
with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    added_count = 0
    total_size = 0

    # 1. 添加核心交付物
    for fname in INCLUDED_FILES:
        src = f'D:/shFintech/{fname}'
        if os.path.exists(src):
            arcname = fname
            zf.write(src, arcname)
            size = os.path.getsize(src)
            total_size += size
            added_count += 1
            print(f'  + {fname} ({size:,} bytes)')
        else:
            print(f'  ! 缺失: {fname}')

    # 2. 添加证据包
    for fname in EVIDENCE_FILES:
        src = f'D:/shFintech/{fname}'
        if os.path.exists(src):
            arcname = f'05_证据与案例/{os.path.basename(fname)}'
            zf.write(src, arcname)
            size = os.path.getsize(src)
            total_size += size
            added_count += 1
            print(f'  + {arcname} ({size:,} bytes)')

    # 3. 添加 Streamlit Demo 包
    for fname in STREAMLIT_FILES:
        src = f'D:/shFintech/{fname}'
        if os.path.exists(src):
            arcname = f'01_产品与技术/Demo原型代码/{os.path.basename(fname)}'
            zf.write(src, arcname)
            size = os.path.getsize(src)
            total_size += size
            added_count += 1
            print(f'  + {arcname} ({size:,} bytes)')

# 显示结果
zip_size = os.path.getsize(output_zip)
print(f'\n========== 提交包已生成 ==========')
print(f'文件: {output_zip}')
print(f'大小: {zip_size:,} bytes ({zip_size/1024/1024:.2f} MB)')
print(f'包含: {added_count} 个文件')
print(f'原始大小: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)')
print(f'压缩比: {(1 - zip_size/total_size)*100:.1f}%')
