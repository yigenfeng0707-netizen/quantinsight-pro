import akshare as ak

# Try multiple possible APIs for industry data
apis = [
    'stock_board_industry_summary_em',
    'stock_board_industry_index_em',
    'stock_board_industry_name_em',
    'sw_index_third_info',
    'stock_industry_category_sw',
]
for api in apis:
    try:
        func = getattr(ak, api)
        result = func()
        cols = list(result.columns)[:8] if hasattr(result, 'columns') else 'N/A'
        shape = result.shape if hasattr(result, 'shape') else 'N/A'
        print(f'{api}: OK, type={type(result).__name__}, shape={shape}')
        print(f'  columns: {cols}')
        if hasattr(result, 'head'):
            print(f'  head: {result.head(2).to_string()[:200]}')
        print()
    except Exception as e:
        print(f'{api}: {type(e).__name__}: {str(e)[:100]}')
