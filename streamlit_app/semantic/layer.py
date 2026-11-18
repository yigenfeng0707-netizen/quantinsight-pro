"""
QuantInsight Pro - 语义层（Semantic Layer）
============================================
本体的运行时门面：实体链接 / 指标解析 / 本体图查询。

供 ai/data_grounder.py（问答接地）与 features/semantic_browser.py（语义目录页）
共用，把"问题里的自然语言指称"解析为本体实体与指标，驱动确定性取数。

核心类：
  EntityLinker  文本 → Stock/Index/Corporation 实体（代码/全称/简称三级匹配）
  MetricParser  文本 → (指标, 日期窗口) 结构化解析
  SemanticGraph 本体图查询：邻居/解释/指标表/因子表

设计原则：匹配失败一律返回空，绝不猜测——上层（RAG/LLM）决定如何兜底。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

logger = logging.getLogger(__name__)

QI = Namespace("http://quantinsight.pro/ontology/")
SEMANTIC_DIR = Path(__file__).parent
TTL_FILES = ("ontology.ttl", "metrics.ttl", "factors.ttl", "entities.ttl")

_CODE_RE = re.compile(r"(?<![A-Za-z0-9])(?:sh|sz|SH|SZ)?(\d{6})(?![0-9])")
_DATE_RE = re.compile(r"(?<!\d)(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})")


# ----------------------------------------------------------------------
# 图装载
# ----------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_graph() -> Graph:
    """装载全部 ttl（TBox + ABox）为单一图；进程级缓存。"""
    g = Graph()
    for fname in TTL_FILES:
        path = SEMANTIC_DIR / fname
        if not path.exists():
            logger.warning("本体文件缺失：%s", path)
            continue
        g.parse(str(path), format="turtle")
    g.bind("qi", QI)
    return g


def _sparql(g: Graph, q: str):
    return g.query(q, initNs={"qi": QI, "rdf": RDF, "rdfs": RDFS})


# ----------------------------------------------------------------------
# 实体链接
# ----------------------------------------------------------------------

@dataclass
class LinkedEntity:
    uri: URIRef
    kind: str            # Stock / Index / Corporation / Industry
    code: str = ""
    name: str = ""
    matched_by: str = ""  # code / name / alias / contains
    score: float = 1.0


class EntityLinker:
    """文本 → 领域实体。三级匹配：代码 > 全称/别名 > 唯一子串。"""

    def __init__(self, g: Optional[Graph] = None):
        self.g = g if g is not None else load_graph()
        self._name_idx = self._build_name_index()

    # -- 索引构建 ------------------------------------------------------
    def _build_name_index(self) -> dict[str, list[URIRef]]:
        """全称与别名 → 实体 URI 的倒排（名称归一化：去空格、大小写不敏感）

        公司实体与股票实体同名时（贵州茅台 ×2）只保留股票——
        问答接地以标的为单位，公司级概念经 listedBy 可达。
        """
        idx: dict[str, list[URIRef]] = {}
        q = '''
        SELECT DISTINCT ?s ?n WHERE {
            { ?s a qi:Stock } UNION { ?s a qi:Index } UNION { ?s a qi:Corporation } UNION { ?s a qi:Industry }
            { ?s qi:name ?n } UNION { ?s qi:alias ?n }
        }'''
        for row in _sparql(self.g, q):
            s, n = row
            key = self._norm(str(n))
            if not key:
                continue
            rivals = idx.setdefault(key, [])
            if (s, RDF.type, QI.Stock) in self.g:
                # 股票优先：替换掉同名的公司实体
                rivals[:] = [s]
            elif not any((x, RDF.type, QI.Stock) in self.g for x in rivals):
                rivals.append(s)
        return idx

    @staticmethod
    def _norm(text: str) -> str:
        return re.sub(r"[\s*A]", "", str(text)).lower()

    @staticmethod
    def _norm_question(text: str) -> str:
        return re.sub(r"[\s*]", "", str(text)).lower()

    # -- 对外接口 ------------------------------------------------------
    def link(self, text: str) -> list[LinkedEntity]:
        """从一段文本中解析全部可识别实体（按出现顺序去重）。"""
        out: list[LinkedEntity] = []
        seen: set[URIRef] = set()
        for ent in self.link_codes(text):
            if ent.uri not in seen:
                seen.add(ent.uri); out.append(ent)
        for ent in self.link_names(text):
            if ent.uri not in seen:
                seen.add(ent.uri); out.append(ent)
        return out

    def link_codes(self, text: str) -> list[LinkedEntity]:
        """6 位代码（可带 sh/sz 前缀）→ Stock 实体。"""
        hits: list[LinkedEntity] = []
        for m in _CODE_RE.finditer(text):
            code = m.group(1)
            uri = QI[f"stk_{code}"]
            if (uri, RDF.type, QI.Stock) in self.g:
                hits.append(LinkedEntity(
                    uri=uri, kind="Stock", code=code,
                    name=self._entity_name(uri), matched_by="code"))
        return hits

    def link_names(self, text: str) -> list[LinkedEntity]:
        """全称/别名精确匹配 → 任意实体；再退唯一子串匹配。"""
        q = self._norm_question(text)
        hits: list[LinkedEntity] = []

        # 精确匹配（最长名称优先，避免"中国银行"被"中国"截胡）
        for name in sorted(self._name_idx, key=len, reverse=True):
            if name and name in q:
                uris = self._name_idx[name]
                if len(uris) == 1:
                    uri = uris[0]
                    hits.append(LinkedEntity(
                        uri=uri, kind=self._entity_kind(uri),
                        code=self._entity_code(uri),
                        name=self._entity_name(uri),
                        matched_by="name"))
        if hits:
            return self._dedup(hits)

        # 唯一缩略匹配：如"茅台"∈"贵州茅台"，"宁德"∈"宁德时代"
        # 候选词取名称的 2-3 字前缀/后缀；同一候选词命中多家公司则作废
        # 纯数字候选码跳过（避免撞上问题里的代码/日期串）
        token_hits: dict[str, set[URIRef]] = {}
        for name, uris in self._name_idx.items():
            if len(uris) != 1 or not name or len(name) < 3:
                continue
            for token in {name[:2], name[:3], name[-2:], name[-3:]} - {name}:
                if len(token) < 2 or token.isdigit():
                    continue
                if token in q:
                    token_hits.setdefault(token, set()).update(uris)
        out, seen_uri = [], set()
        for token, uris in token_hits.items():
            if len(uris) == 1:
                uri = uris.pop()
                if uri in seen_uri:
                    continue
                seen_uri.add(uri)
                out.append(LinkedEntity(
                    uri=uri, kind=self._entity_kind(uri),
                    code=self._entity_code(uri),
                    name=self._entity_name(uri),
                    matched_by="abbr", score=0.6))
        return out

    def _dedup(self, hits: list[LinkedEntity]) -> list[LinkedEntity]:
        seen, out = set(), []
        for h in hits:
            if h.uri not in seen:
                seen.add(h.uri); out.append(h)
        return out

    def _entity_name(self, uri: URIRef) -> str:
        r = self.g.value(uri, QI.name)
        return str(r) if r else ""

    def _entity_code(self, uri: URIRef) -> str:
        r = self.g.value(uri, QI.code)
        return str(r) if r else ""

    def _entity_kind(self, uri: URIRef) -> str:
        for kind in ("Stock", "Index", "Corporation", "Industry"):
            if (uri, RDF.type, QI[kind]) in self.g:
                return kind
        return "Entity"


# ----------------------------------------------------------------------
# 指标解析
# ----------------------------------------------------------------------

@dataclass
class ParsedMetric:
    key: str                  # 指标 key（如 m_pct_change）
    name: str                 # 规范名（涨跌幅）
    uri: URIRef
    caliber: str = ""
    unit: str = ""
    binding_table: str = ""
    binding_column: str = ""
    eval_type: str = ""
    dates: list[str] = field(default_factory=list)   # 问题里的 ISO 日期
    recent_window: str = ""    # "最近一年" / "最近N日" 等自然窗口标记


class MetricParser:
    """文本 → 指标（同义词匹配）+ 日期/窗口标记。"""

    # 自然窗口标记 → 语义描述（不猜具体日期，交给取数层按数据实际解释）
    WINDOW_PATTERNS = [
        (r"最近一年|近一年|过去一年|年度", "最近一年"),
        (r"最近半年|近半年", "最近半年"),
        (r"最近一个季度|近一季度|本季度", "最近一季度"),
        (r"今年以来|年初至今", "今年以来"),
    ]

    def __init__(self, g: Optional[Graph] = None):
        self.g = g if g is not None else load_graph()
        self._metrics = self._load_metrics()

    def _load_metrics(self) -> list[dict]:
        rows = []
        q = '''
        SELECT ?m ?name ?alias ?caliber ?unit ?tbl ?col ?eval WHERE {
            ?m a qi:Metric ; qi:name ?name .
            OPTIONAL { ?m qi:caliber ?caliber }
            OPTIONAL { ?m qi:unit ?unit }
            OPTIONAL { ?m qi:bindingTable ?tbl }
            OPTIONAL { ?m qi:bindingColumn ?col }
            OPTIONAL { ?m qi:evalType ?eval }
            OPTIONAL { ?m qi:alias ?alias }
        }'''
        agg: dict[str, dict] = {}
        for row in _sparql(self.g, q):
            m, name, alias, cal, unit, tbl, col, ev = row
            d = agg.setdefault(str(m), {
                "uri": m, "name": str(name), "aliases": [],
                "caliber": str(cal or ""), "unit": str(unit or ""),
                "table": str(tbl or ""), "column": str(col or ""),
                "eval": str(ev or ""),
            })
            if alias:
                d["aliases"].append(str(alias))
        return list(agg.values())

    def parse(self, text: str) -> list[ParsedMetric]:
        """解析文本中的全部指标（最长同义词优先）。"""
        q = EntityLinker._norm_question(text)
        hits: list[ParsedMetric] = []
        seen: set[str] = set()

        # 候选词 = 规范名 + 别名，按长度降序
        cands = []
        for m in self._metrics:
            cands.append((m["name"], m))
            for a in m["aliases"]:
                cands.append((a, m))
        cands.sort(key=lambda x: len(x[0]), reverse=True)

        for word, m in cands:
            w = EntityLinker._norm(word)
            if not w or m["name"] in seen:
                continue
            if w in q:
                seen.add(m["name"])
                hits.append(ParsedMetric(
                    key=str(m["uri"]).rsplit("/", 1)[-1],
                    name=m["name"], uri=m["uri"], caliber=m["caliber"],
                    unit=m["unit"], binding_table=m["table"],
                    binding_column=m["column"], eval_type=m["eval"],
                    dates=self._parse_dates(text),
                    recent_window=self._parse_window(text)))
        return hits

    @staticmethod
    def _parse_dates(text: str) -> list[str]:
        out = []
        for y, mo, d in _DATE_RE.findall(text):
            try:
                out.append(f"{int(y):04d}-{int(mo):02d}-{int(d):02d}")
            except ValueError:
                continue
        return out

    @classmethod
    def _parse_window(cls, text: str) -> str:
        for pat, label in cls.WINDOW_PATTERNS:
            if re.search(pat, text):
                return label
        return ""


# ----------------------------------------------------------------------
# 本体图查询（UI 与解释链用）
# ----------------------------------------------------------------------

class SemanticGraph:
    """邻居查询 / 指标表 / 因子表 —— 语义目录页与引用解释的共用门面。"""

    def __init__(self, g: Optional[Graph] = None):
        self.g = g if g is not None else load_graph()

    def neighbors(self, uri: URIRef) -> list[dict]:
        """一跳邻居（双向），供实体查询页与图谱页使用。"""
        rows = []
        for s, p, o in self.g.triples((uri, None, None)):
            if isinstance(o, Literal) or str(p).rsplit("/", 1)[-1] in ("code",):
                continue
            if p in (RDF.type,):
                continue
            rows.append({"edge": str(p).rsplit("/", 1)[-1], "target_uri": str(o),
                         "target": self._label(o), "direction": "out"})
        for s, p, o in self.g.triples((None, None, uri)):
            if p in (RDF.type,):
                continue
            rows.append({"edge": str(p).rsplit("/", 1)[-1], "target_uri": str(s),
                         "target": self._label(s), "direction": "in"})
        return rows

    def _label(self, uri: URIRef) -> str:
        n = self.g.value(uri, QI.name)
        c = self.g.value(uri, QI.code)
        if n and c:
            return f"{n}（{c}）"
        return str(n) if n else str(uri).rsplit("/", 1)[-1]

    def metrics(self) -> list[dict]:
        mp = MetricParser(self.g)
        return sorted(mp._metrics, key=lambda m: m["name"])

    def factors(self) -> list[dict]:
        rows: dict[str, dict] = {}
        q = '''
        SELECT ?f ?name ?formula ?cal ?cat ?catname ?mod WHERE {
            ?f a qi:Factor ; qi:name ?name .
            OPTIONAL { ?f qi:formula ?formula }
            OPTIONAL { ?f qi:caliber ?cal }
            OPTIONAL { ?f qi:inCategory ?cat . ?cat qi:name ?catname }
            OPTIONAL { ?f qi:bindingApi ?mod }
        }'''
        for row in _sparql(self.g, q):
            f, name, formula, cal, cat, catname, mod = row
            d = rows.setdefault(str(f), {
                "uri": str(f), "name": str(name), "formula": str(formula or ""),
                "caliber": str(cal or ""), "category": "", "module": "",
                "deps": [],
            })
            if catname:
                d["category"] = str(catname)
            if mod:
                d["module"] = str(mod)
        for f_key, d in rows.items():
            for _, _, o in self.g.triples((QI[f_key.rsplit("/", 1)[-1]], QI.computedFrom, None)):
                mname = self.g.value(o, QI.name)
                if mname and str(mname) not in d["deps"]:
                    d["deps"].append(str(mname))
        return sorted(rows.values(), key=lambda x: (x["category"], x["name"]))

    def categories(self) -> list[dict]:
        q = '''SELECT ?c ?name ?cal WHERE { ?c a qi:FactorCategory ; qi:name ?name . OPTIONAL { ?c qi:caliber ?cal } }'''
        return [{"uri": str(c), "name": str(n), "caliber": str(cal or "")}
                for c, n, cal in _sparql(self.g, q)]

    def explain_entity(self, uri: URIRef) -> str:
        """实体的可读关系描述（引用链/页面解释用）。"""
        parts = []
        for r in self.neighbors(uri):
            arrow = "→" if r["direction"] == "out" else "→（反向）"
            parts.append(f"{arrow} {r['edge']}: {r['target']}")
        return "\n".join(parts)


# 便捷单例（App 多处复用同一图缓存）
_linker: Optional[EntityLinker] = None
_parser: Optional[MetricParser] = None
_graph: Optional[SemanticGraph] = None


def get_linker() -> EntityLinker:
    global _linker
    if _linker is None:
        _linker = EntityLinker()
    return _linker


def get_parser() -> MetricParser:
    global _parser
    if _parser is None:
        _parser = MetricParser()
    return _parser


def get_semantic_graph() -> SemanticGraph:
    global _graph
    if _graph is None:
        _graph = SemanticGraph()
    return _graph
