"""
QuantInsight Pro - 产业链追踪器 (Supply Chain Tracker)
======================================================

产业链可视化 + 上下游关系分析.
基于申万行业分类, 构建产业链 Sankey 图.

功能:
- 产业链关系图谱
- 上下游传导分析
- 行业热度传导
- Sankey 可视化数据

License: MIT
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)


# 产业链关系定义 (简化版)
# 格式: {行业: {"upstream": [上游行业], "downstream": [下游行业]}}
INDUSTRY_CHAINS = {
    "新能源汽车": {
        "upstream": ["锂矿", "钴矿", "稀土", "汽车零部件"],
        "midstream": ["电池制造", "电机制造", "电控系统"],
        "downstream": ["整车制造", "充电桩", "汽车服务"],
        "key_stocks": {
            "锂矿": ["天齐锂业", "赣锋锂业"],
            "电池制造": ["宁德时代", "比亚迪", "亿纬锂能"],
            "整车制造": ["比亚迪", "长安汽车", "长城汽车"],
            "充电桩": ["特锐德", "万马股份"],
        },
    },
    "半导体": {
        "upstream": ["硅片", "光刻胶", "电子特气", "靶材"],
        "midstream": ["IC设计", "晶圆代工", "封装测试"],
        "downstream": ["消费电子", "汽车电子", "工业控制", "通信设备"],
        "key_stocks": {
            "硅片": ["沪硅产业", "立昂微"],
            "IC设计": ["韦尔股份", "兆易创新", "紫光国微"],
            "晶圆代工": ["中芯国际", "华虹半导体"],
            "封装测试": ["长电科技", "通富微电"],
        },
    },
    "光伏": {
        "upstream": ["多晶硅", "银浆", "EVA胶膜"],
        "midstream": ["硅片", "电池片", "组件"],
        "downstream": ["光伏电站", "分布式光伏", "光伏设备"],
        "key_stocks": {
            "多晶硅": ["通威股份", "大全能源"],
            "硅片": ["隆基绿能", "TCL中环"],
            "电池片": ["通威股份", "爱旭股份"],
            "组件": ["隆基绿能", "晶科能源", "天合光能"],
        },
    },
    "白酒": {
        "upstream": ["高粱", "小麦", "包装材料"],
        "midstream": ["白酒酿造", "品牌运营"],
        "downstream": ["经销商", "餐饮", "电商", "礼品"],
        "key_stocks": {
            "白酒酿造": ["贵州茅台", "五粮液", "泸州老窖", "山西汾酒"],
            "经销商": ["华致酒行"],
        },
    },
    "医药生物": {
        "upstream": ["原料药", "医药中间体", "药用辅料"],
        "midstream": ["化学制药", "生物制品", "中药", "医疗器械"],
        "downstream": ["医院", "药店", "医药电商"],
        "key_stocks": {
            "原料药": ["华海药业", "普洛药业"],
            "化学制药": ["恒瑞医药", "复星医药"],
            "生物制品": ["长春高新", "智飞生物"],
            "医疗器械": ["迈瑞医疗", "联影医疗"],
        },
    },
    "房地产": {
        "upstream": ["钢铁", "水泥", "玻璃", "建材"],
        "midstream": ["房地产开发", "建筑施工"],
        "downstream": ["家居", "家电", "装修", "物业管理"],
        "key_stocks": {
            "钢铁": ["宝钢股份", "鞍钢股份"],
            "水泥": ["海螺水泥", "华新水泥"],
            "房地产开发": ["万科A", "保利发展", "招商蛇口"],
            "家居": ["欧派家居", "索菲亚"],
            "家电": ["美的集团", "格力电器", "海尔智家"],
        },
    },
}


@dataclass
class ChainNode:
    """产业链节点"""
    name: str
    level: str  # upstream / midstream / downstream
    stocks: List[str] = field(default_factory=list)
    heat_score: float = 0.5  # 0-1 热度


@dataclass
class ChainLink:
    """产业链连接"""
    source: str
    target: str
    value: float = 1.0


@dataclass
class IndustryChain:
    """产业链完整数据"""
    name: str
    nodes: List[ChainNode]
    links: List[ChainLink]
    sankey_data: Dict


class SupplyChainTracker:
    """
    产业链追踪器

    功能:
    - 查询产业链关系
    - 生成 Sankey 图数据
    - 上下游热度传导分析
    """

    def __init__(self):
        self.chains = INDUSTRY_CHAINS

    def get_available_chains(self) -> List[str]:
        """获取可用产业链列表"""
        return list(self.chains.keys())

    def get_chain(self, chain_name: str) -> Optional[IndustryChain]:
        """
        获取完整产业链数据

        Args:
            chain_name: 产业链名称

        Returns:
            IndustryChain or None
        """
        if chain_name not in self.chains:
            logger.warning(f"产业链 '{chain_name}' 不存在")
            return None

        chain_def = self.chains[chain_name]
        nodes = []
        links = []

        # 构建节点
        for level in ["upstream", "midstream", "downstream"]:
            industries = chain_def.get(level, [])
            for ind in industries:
                stocks = chain_def.get("key_stocks", {}).get(ind, [])
                nodes.append(ChainNode(
                    name=ind,
                    level=level,
                    stocks=stocks,
                    heat_score=0.5,
                ))

        # 构建连接 (upstream → midstream → downstream)
        upstream = chain_def.get("upstream", [])
        midstream = chain_def.get("midstream", [])
        downstream = chain_def.get("downstream", [])

        for u in upstream:
            for m in midstream:
                links.append(ChainLink(source=u, target=m, value=1.0))

        for m in midstream:
            for d in downstream:
                links.append(ChainLink(source=m, target=d, value=1.0))

        # 生成 Sankey 数据
        sankey_data = self._build_sankey(nodes, links)

        return IndustryChain(
            name=chain_name,
            nodes=nodes,
            links=links,
            sankey_data=sankey_data,
        )

    def analyze_upstream_impact(
        self,
        chain_name: str,
        upstream_industry: str,
        impact_score: float,
    ) -> Dict:
        """
        分析上游行业变动对下游的传导影响

        Args:
            chain_name: 产业链名称
            upstream_industry: 上游行业
            impact_score: 影响分数 (-1 到 1)

        Returns:
            传导分析结果
        """
        chain = self.get_chain(chain_name)
        if not chain:
            return {"error": f"产业链 {chain_name} 不存在"}

        # 找到受影响的 midstream 和 downstream
        chain_def = self.chains[chain_name]
        midstream = chain_def.get("midstream", [])
        downstream = chain_def.get("downstream", [])

        # 传导衰减 (上游→中游衰减30%, 中游→下游衰减50%)
        mid_impact = impact_score * 0.7
        down_impact = mid_impact * 0.5

        affected_mid = [
            {"industry": m, "impact": round(mid_impact, 2)}
            for m in midstream
        ]
        affected_down = [
            {"industry": d, "impact": round(down_impact, 2)}
            for d in downstream
        ]

        return {
            "chain": chain_name,
            "source_industry": upstream_industry,
            "source_impact": impact_score,
            "midstream_impact": affected_mid,
            "downstream_impact": affected_down,
            "conclusion": self._generate_conclusion(
                chain_name, upstream_industry, impact_score
            ),
        }

    def get_chain_stocks(self, chain_name: str) -> pd.DataFrame:
        """
        获取产业链相关股票

        Args:
            chain_name: 产业链名称

        Returns:
            DataFrame with columns: industry, level, stock
        """
        if chain_name not in self.chains:
            return pd.DataFrame()

        chain_def = self.chains[chain_name]
        rows = []

        for level in ["upstream", "midstream", "downstream"]:
            industries = chain_def.get(level, [])
            for ind in industries:
                stocks = chain_def.get("key_stocks", {}).get(ind, [])
                for stock in stocks:
                    rows.append({
                        "industry": ind,
                        "level": level,
                        "stock": stock,
                    })

        return pd.DataFrame(rows)

    # ── Private helpers ──────────────────────────────────

    def _build_sankey(
        self, nodes: List[ChainNode], links: List[ChainLink]
    ) -> Dict:
        """构建 Sankey 图数据 (ECharts 格式)"""
        node_names = [n.name for n in nodes]
        sankey_nodes = [{"name": name} for name in node_names]

        sankey_links = []
        for link in links:
            if link.source in node_names and link.target in node_names:
                sankey_links.append({
                    "source": link.source,
                    "target": link.target,
                    "value": link.value,
                })

        return {
            "nodes": sankey_nodes,
            "links": sankey_links,
        }

    def _generate_conclusion(
        self,
        chain_name: str,
        upstream: str,
        impact: float,
    ) -> str:
        """生成传导结论"""
        direction = "上涨" if impact > 0 else "下跌"
        strength = "显著" if abs(impact) > 0.5 else "温和"

        if abs(impact) < 0.2:
            return f"{upstream} 变动对 {chain_name} 产业链影响有限"

        return (
            f"{upstream} {direction} 将对 {chain_name} 产业链产生 {strength} 影响, "
            f"建议关注中游制造环节的成本传导和下游需求变化"
        )
