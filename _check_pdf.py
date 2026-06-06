import pypdf

reader = pypdf.PdfReader('D:/shFintech/QuantInsight_Pro_Technical_Whitepaper_V1.pdf')
print(f'页数: {len(reader.pages)}')
print(f'标题: {reader.metadata.title if reader.metadata else "无"}')
# 提取首页文字验证
first_page = reader.pages[0].extract_text()
print(f'\n首 200 字:')
print(first_page[:200])
