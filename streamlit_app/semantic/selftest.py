"""
QuantInsight Pro - 语义层自测
=============================
python semantic/selftest.py  （纯本地，无需网络/LLM）

覆盖：图装载、实体链接三级匹配、指标解析、SPARQL 邻居、口径可读性。
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")

from rdflib import RDF
from semantic.layer import (  # noqa: E402
    QI, EntityLinker, MetricParser, SemanticGraph, load_graph,
)

OK, FAIL = "✅", "❌"
results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, bool(cond), detail))


# ---------- 1. 图装载 ----------
g = load_graph()
n_triples = len(g)
check("图装载 triples>800", n_triples > 800, f"{n_triples} triples")


# ---------- 2. 实体链接（三级） ----------
lk = EntityLinker()

e = lk.link_codes("600519")
check("代码匹配 600519", len(e) == 1 and e[0].code == "600519"
      and "茅台" in e[0].name, str(e[0].name if e else ""))

e2 = lk.link_names("贵州茅台最近一年营业收入是多少")
check("全称匹配 贵州茅台", len(e2) == 1 and e2[0].matched_by == "name",
      str(e2[0].name if e2 else ""))

e3 = lk.link_names("茅台今天跌了多少")
check("缩略匹配 茅台", len(e3) == 1 and e3[0].code == "600519",
      str(e3[0].name if e3 else ""))

e4 = lk.link_names("平安银行涨停")
check("歧义词 平安(银行) 只命中平安银行", len(e4) == 1 and e4[0].code == "000001",
      str([x.name for x in e4]))

e5 = lk.link_names("创业板指涨了1.5%")
kinds = [x.kind for x in e5]
check("指数匹配 创业板指", "Index" in kinds and len(e5) == 1,
      str([(x.name, x.kind) for x in e5]))

e6 = lk.link("600519与000858昨天谁跌得多")
check("混合文本多实体", len(e6) == 2, str([x.code for x in e6]))

e7 = lk.link("今天天气不错")
check("无实体文本返回空", e7 == [], str(e7))

# ---------- 3. 指标解析 ----------
mp = MetricParser()
p = mp.parse("茅台的归母净利润是多少")
check("指标解析 归母净利润", any(x.name == "归母净利润" for x in p),
      str([(x.name, x.unit) for x in p]))

p2 = mp.parse("600519从2026-01-01到2026-06-30的区间涨跌幅")
pm = {x.name for x in p2}
check("指标解析 区间涨跌幅", "区间涨跌幅" in pm, str(pm))
check("日期解析", p2 and p2[0].dates == ["2026-01-01", "2026-06-30"],
      str(p2[0].dates if p2 else []))

p3 = mp.parse("茅台最近一年营业收入")
p3m = {x.name for x in p3}
check("财务指标 营业收入 + 自然窗口", "营业收入" in p3m
      and p3[0].recent_window == "最近一年",
      str([(x.name, x.recent_window) for x in p3]))

p4 = mp.parse("这只股票PE高不高")
check("英文缩略 PE", any(x.name == "市盈率" for x in p4),
      str([x.name for x in p4]))

# ---------- 4. 本体图查询 ----------
sg = SemanticGraph()
nb = sg.neighbors(QI["stk_600519"])
edges = {r["edge"] for r in nb}
check("茅台邻居关系",
      "memberOf" in edges or "listedBy" in edges, str(sorted(edges)))

mt = sg.metrics()
check("指标表 ≥25 条", len(mt) >= 25, f"{len(mt)} 条")

ft = sg.factors()
check("因子表 ≥60 条", len(ft) >= 60, f"{len(ft)} 条")
rsi = [f for f in ft if f["name"] == "RSI(6)"]
check("RSI(6) 有公式", bool(rsi) and "avg_gain" in rsi[0]["formula"],
      str(rsi[0]["formula"] if rsi else ""))

# ---------- 5. 口径可读性（引用链素材） ----------
cal = [m for m in mt if m["name"] == "归母净利润"]
check("口径文本完整",
      bool(cal) and "母公司" in cal[0]["caliber"]
      and cal[0]["table"] == "financials",
      str(cal[0]["caliber"] if cal else ""))

# ---------- 汇总 ----------
width = max(len(r[0]) for r in results)
for name, ok, detail in results:
    print(f"{OK if ok else FAIL} {name:<{width}} {detail}")
bad = [r for r in results if not r[1]]
print(f"\n{'全部通过' if not bad else f'{len(bad)} 项失败'}（共 {len(results)} 项）")
raise SystemExit(1 if bad else 0)
