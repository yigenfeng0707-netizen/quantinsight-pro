import akshare as ak

# Found sw_index_third_info works. Try to get board daily changes
apis_to_try = [
    ('stock_board_concept_name_em', None),
    ('stock_board_concept_summary_em', None),
    ('stock_board_industry_cons_em', 'BK0438'),  # 半导体行业
]
for item in apis_to_try:
    api = item[0]
    try:
        func = getattr(ak, api)
        if item[1]:
            result = func(item[1])
        else:
            result = func()
        cols = list(result.columns)[:8] if hasattr(result, 'columns') else 'N/A'
        shape = result.shape if hasattr(result, 'shape') else 'N/A'
        print(f'{api}: OK, type={type(result).__name__}, shape={shape}')
        print(f'  columns: {cols}')
        if hasattr(result, 'head'):
            print(f'  head: {result.head(2).to_string()[:300]}')
        print()
    except Exception as e:
        print(f'{api}: {type(e).__name__}: {str(e)[:150]}')
