"""
QuantInsight Pro - 领域实体实例生成器
=====================================
生成 ABox：股票 / 公司 / 指数 / 行业的本体实例（semantic/entities.ttl）。

两种模式：
  离线（默认）：从本地 qi_data.db 读取标的代码；名称取内置核心股票表
                + data/hs300_codes.txt / zz500_codes.txt 的成分关系。
  在线 --online：额外用 akshare 全市场快照补齐全部股票名称、指数与行业板块。
                （本地代理环境可能无法直连；生产服务器上可跑）

用法：
  python semantic/build_entities.py            # 离线
  python semantic/build_entities.py --online   # 在线（服务器环境）
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

try:
    from rdflib import Graph, Literal, Namespace, URIRef
    from rdflib.namespace import RDF, XSD
except ImportError:
    sys.exit("需要 rdflib：pip install rdflib")

QI = Namespace("http://quantinsight.pro/ontology/")
HERE = Path(__file__).parent
DB_PATH = HERE.parent / "data" / "qi_data.db"

# 主要指数（公开常量，代码与名称固定）
INDICES = [
    ("idx_sh000001", "sh000001", "上证综指", "上海证券交易所综合指数"),
    ("idx_sz399001", "sz399001", "深证成指", "深圳证券交易所成份指数"),
    ("idx_sz399006", "sz399006", "创业板指", "创业板指数"),
    ("idx_sh000300", "sh000300", "沪深300", "沪深 300 指数"),
    ("idx_sh000905", "sh000905", "中证500", "中证 500 指数"),
    ("idx_sh000906", "sh000906", "中证800", "中证 800 指数"),
    ("idx_sh000852", "sh000852", "中证1000", "中证 1000 指数"),
]

# 本地成分股名单 → index URI
CONSTITUENT_FILES = {
    "idx_sh000300": "hs300_codes.txt",
    "idx_sh000905": "zz500_codes.txt",
}

# 核心股票（演示/问答高频标的；名称为公开信息）
CORE_STOCKS = {
    "600519": "贵州茅台", "300750": "宁德时代", "601318": "中国平安",
    "600036": "招商银行", "000858": "五粮液",   "002594": "比亚迪",
    "600276": "恒瑞医药", "601899": "紫金矿业", "002475": "立讯精密",
    "603259": "药明康德", "600030": "中信证券", "601398": "工商银行",
    "600000": "浦发银行", "000001": "平安银行", "600887": "伊利股份",
    "000333": "美的集团", "600406": "国电南瑞", "601012": "隆基绿能",
    "600089": "特变电工", "002230": "科大讯飞", "600585": "海螺水泥",
    "601166": "兴业银行", "600690": "海尔智家", "000651": "格力电器",
    "601888": "中国中免", "002241": "歌尔股份", "300059": "东方财富",
    "600016": "民生银行", "601288": "农业银行", "600919": "江苏银行",
    "601628": "中国人寿", "601601": "中国太保", "002304": "洋河股份",
    "000568": "泸州老窖", "600809": "山西汾酒", "002714": "牧原股份",
    "300498": "温氏股份", "600196": "复星医药", "600436": "片仔癀",
    "000538": "云南白药", "601919": "中远海控", "601006": "大秦铁路",
    "600104": "上汽集团", "300274": "阳光电源", "603501": "韦尔股份",
    "000725": "京东方A",  "002415": "海康威视", "300124": "汇川技术",
    "600941": "中国移动", "601857": "中国石油", "600028": "中国石化",
}

# 证监会行业分类一级（公开标准，离线兜底）
INDUSTRIES_CSRC = [
    "A-农林牧渔业", "B-采矿业", "C-制造业", "D-电力热力燃气及水生产供应业",
    "E-建筑业", "F-批发和零售业", "G-交通运输仓储邮政业", "H-住宿和餐饮业",
    "I-信息传输软件信息技术服务业", "J-金融业", "K-房地产业",
    "L-租赁和商务服务业", "M-科学技术服务业", "N-水利环境公共设施管理业",
    "O-居民服务修理服务业", "P-教育", "Q-卫生社会工作", "R-文化体育娱乐业",
    "S-综合",
]


def exchange_of(code: str) -> str:
    """代码前缀 → 交易所（用于口径说明）"""
    if code.startswith(("sh", "6")):
        return "上海证券交易所"
    if code.startswith(("sz", "0", "3")):
        return "深圳证券交易所"
    return "北京证券交易所"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--online", action="store_true", help="启用 akshare 在线补全名称")
    ap.add_argument("--db", type=Path, default=DB_PATH)
    args = ap.parse_args()

    if not args.db.exists():
        sys.exit(f"找不到数据库：{args.db}")
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    codes = [r[0] for r in conn.execute(
        "SELECT DISTINCT code FROM stock_history ORDER BY code")]
    print(f"标的后备集：{len(codes)} 只（stock_history）")

    # 在线模式：akshare 快照补全名称
    name_map: dict[str, str] = dict(CORE_STOCKS)
    board_names: list[str] = []
    if args.online:
        try:
            import akshare as ak
            spot = ak.stock_zh_a_spot_em()
            for _, row in spot.iterrows():
                c = str(row.get("代码", "")).strip()
                n = str(row.get("名称", "")).strip()
                if c and n:
                    name_map[c] = n
            print(f"akshare 快照补全名称：{len(name_map)} 只")
            boards = ak.stock_board_industry_name_em()
            board_names = [str(r["板块名称"]) for _, r in boards.iterrows()]
            print(f"东财行业板块：{len(board_names)} 个")
        except Exception as e:  # 在线失败自动降级
            print(f"[warn] akshare 不可用，降级离线模式：{e}")

    g = Graph()
    g.bind("qi", QI)
    g.bind("rdf", RDF)
    g.bind("xsd", XSD)

    # 1) 指数
    for uri, code, name, full in INDICES:
        g.add((QI[uri], RDF.type, QI.Index))
        g.add((QI[uri], QI.code, Literal(code)))
        g.add((QI[uri], QI.name, Literal(name)))
        g.add((QI[uri], QI.alias, Literal(full)))
        g.add((QI[uri], QI.caliber, Literal(f"{exchange_of(code)} 编制的 {full}")))

    # 2) 行业（在线用东财板块，离线用证监会一级）
    industry_uris: list[str] = []
    if board_names:
        for i, bname in enumerate(board_names):
            uri = f"ind_em_{i:03d}"
            g.add((QI[uri], RDF.type, QI.Industry))
            g.add((QI[uri], QI.name, Literal(bname)))
            g.add((QI[uri], QI.caliber, Literal("东方财富行业板块分类")))
            industry_uris.append(uri)
    else:
        for label in INDUSTRIES_CSRC:
            uri = "ind_" + label.split("-")[0]
            g.add((QI[uri], RDF.type, QI.Industry))
            g.add((QI[uri], QI.name, Literal(label.split("-", 1)[1])))
            g.add((QI[uri], QI.caliber, Literal("证监会行业分类（一级，GB/T 4754 类似)")))
            g.add((QI[uri], QI.code, Literal(label.split("-")[0])))
            industry_uris.append(uri)

    # 3) 成分关系（本地名单）
    code_set = set(codes)
    membership: dict[str, list[str]] = {}
    for idx_uri, fname in CONSTITUENT_FILES.items():
        f = HERE.parent / "data" / fname
        if not f.exists():
            print(f"[warn] 缺成分表：{f}")
            continue
        n_hit = 0
        for line in f.read_text(encoding="utf-8").split():
            c = line.strip()
            if c in code_set:
                membership.setdefault(c, []).append(idx_uri)
                n_hit += 1
        print(f"{fname}: {n_hit} 只在标的后备集内")
    # 全部 800 只视为中证800 成分（DB 数据源即 000906）
    for c in codes:
        membership.setdefault(c, []).append("idx_sh000906")
    for c, idxs in membership.items():
        for uri in set(idxs):
            g.add((QI[f"stk_{c}"], QI.memberOf, QI[uri]))

    # 4) 股票 / 公司实例
    n_named = 0
    for c in codes:
        s = QI[f"stk_{c}"]
        g.add((s, RDF.type, QI.Stock))
        g.add((s, QI.code, Literal(c)))
        g.add((s, QI.caliber, Literal(f"{exchange_of(c)} 上市 A 股标的")))
        g.add((s, QI.sourcedFrom, QI.src_local_sqlite))
        name = name_map.get(c)
        if name:
            n_named += 1
            g.add((s, QI.name, Literal(name)))
            if len(name) > 2:  # 简称别名：去公司名后缀
                for suffix in ("股份有限公司", "有限公司", "股份公司", "集团"):
                    if name.endswith(suffix):
                        g.add((s, QI.alias, Literal(name[: -len(suffix)])))
                        break
            corp = QI[f"corp_{c}"]
            g.add((corp, RDF.type, QI.Corporation))
            g.add((corp, QI.name, Literal(name)))
            g.add((corp, QI.code, Literal(c)))
            g.add((corp, QI.tradedAs, s))
            g.add((s, QI.listedBy, corp))

    out = HERE / "entities.ttl"
    g.serialize(destination=str(out), format="turtle", encoding="utf-8")
    print(f"已生成 {out}")
    print(f"  股票 {len(codes)} 只（有名称 {n_named}），"
          f"指数 {len(INDICES)}，行业 {len(industry_uris)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
