# -*- coding: utf-8 -*-
"""补全中证500中 QVeris 未成功的成分股 (东方财富免费 API)"""
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1] / "streamlit_app"
sys.path.insert(0, str(ROOT))

from datetime import datetime, timedelta
from features.sqlite_data_layer import QIDataDB
from features.eastmoney_direct import fetch_stock_history

db = QIDataDB()
zz = [ln.strip() for ln in (ROOT / "data" / "zz500_codes.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
existing = set(r[0] for r in db._get_conn().execute("SELECT DISTINCT code FROM stock_history"))
todo = [c for c in zz if c not in existing]
end = datetime.now().strftime("%Y%m%d")
start = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

print(f"ZZ500 backfill: {len(todo)} remaining (East Money)")
ok = fail = 0
for i, code in enumerate(todo):
    try:
        df = fetch_stock_history(code, start, end)
        if df is not None and not df.empty:
            db.upsert_stock_history(code, df)
            ok += 1
            if (i + 1) % 20 == 0:
                print(f"  [{i+1}/{len(todo)}] ok={ok} fail={fail}")
        else:
            fail += 1
    except Exception as e:
        fail += 1
        if fail <= 3:
            print(f"  FAIL {code}: {e}")
    time.sleep(0.25)

print(f"Done: ok={ok} fail={fail}")
conn = db._get_conn()
print("total stocks", conn.execute("SELECT COUNT(DISTINCT code) FROM stock_history").fetchone()[0])
