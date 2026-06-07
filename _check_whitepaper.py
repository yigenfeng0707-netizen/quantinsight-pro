import re
import os

with open('D:/shFintech/QuantInsight_Pro_Technical_Whitepaper_V1.md', 'r', encoding='utf-8') as f:
    content = f.read()

print(f'Characters: {len(content):,}')
print(f'Lines: {content.count(chr(10))+1:,}')

# Count sections
h1 = re.findall(r'^# (.+)$', content, re.MULTILINE)
h2 = re.findall(r'^## (.+)$', content, re.MULTILINE)
h3 = re.findall(r'^### (.+)$', content, re.MULTILINE)

print(f'H1 sections: {len(h1)}')
print(f'H2 sections: {len(h2)}')
print(f'H3 sections: {len(h3)}')
print()
print('H2 sections:')
for s in h2:
    print(f'  - {s}')

# Estimate pages (assuming ~3000 chars per page)
estimated_pages = len(content) / 3000
print(f'\nEstimated pages: {estimated_pages:.1f}')

size = os.path.getsize('D:/shFintech/QuantInsight_Pro_Technical_Whitepaper_V1.md')
print(f'File size: {size:,} bytes ({size/1024:.1f} KB)')
