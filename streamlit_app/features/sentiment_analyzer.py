"""
QuantInsight Pro - 舆情分析引擎 (Sentiment Analyzer)
=====================================================

基于真实新闻数据的 NLP 情感分析.
使用 SnowNLP 进行中文情感打分, 无需外部 API.

功能:
- 新闻情感分析 (正面/负面/中性)
- 舆情热度追踪
- 关键词提取
- 舆情预警

License: MIT
"""

import logging
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)

try:
    from snownlp import SnowNLP
    HAS_SNOWNLP = True
except ImportError:
    HAS_SNOWNLP = False
    logger.warning("SnowNLP not installed. Using rule-based fallback.")


@dataclass
class SentimentResult:
    """情感分析结果"""
    text: str
    score: float  # 0-1, >0.6 正面, <0.4 负面
    label: str  # positive/negative/neutral
    keywords: List[str]
    source: str
    timestamp: str


@dataclass
class SentimentSummary:
    """舆情汇总"""
    total_articles: int
    positive_count: int
    negative_count: int
    neutral_count: int
    avg_score: float
    hot_keywords: List[tuple]  # [(keyword, count)]
    sentiment_trend: str  # bullish/bearish/neutral


class SentimentAnalyzer:
    """
    舆情分析引擎

    支持:
    - SnowNLP 中文情感分析
    - 规则兜底 (关键词匹配)
    - 热度统计
    - 关键词提取
    """

    # 金融领域情感关键词
    POSITIVE_WORDS = {
        "上涨", "涨停", "利好", "突破", "新高", "增长", "超预期", "买入",
        "看好", "强势", "反弹", "放量", "主力", "净流入", "业绩预增",
        "订单", "中标", "战略合作", "创新", "领先", "龙头", "景气",
    }

    NEGATIVE_WORDS = {
        "下跌", "跌停", "利空", "暴跌", "新低", "下滑", "不及预期", "卖出",
        "看空", "弱势", "破位", "缩量", "出逃", "净流出", "业绩预减",
        "亏损", "处罚", "违规", "诉讼", "风险", "警示", "退市",
    }

    def __init__(self):
        self.use_snownlp = HAS_SNOWNLP

    def analyze_text(
        self,
        text: str,
        source: str = "unknown",
        timestamp: Optional[str] = None,
    ) -> SentimentResult:
        """
        分析单条文本情感

        Args:
            text: 新闻标题或内容
            source: 来源
            timestamp: 时间戳

        Returns:
            SentimentResult
        """
        if not text or not text.strip():
            return SentimentResult(
                text=text,
                score=0.5,
                label="neutral",
                keywords=[],
                source=source,
                timestamp=timestamp or datetime.now().isoformat(),
            )

        # SnowNLP 情感打分
        if self.use_snownlp:
            try:
                s = SnowNLP(text)
                score = s.sentiments  # 0-1, 越接近1越正面
            except Exception:
                score = self._rule_based_score(text)
        else:
            score = self._rule_based_score(text)

        # 标签
        if score >= 0.6:
            label = "positive"
        elif score <= 0.4:
            label = "negative"
        else:
            label = "neutral"

        # 关键词提取
        keywords = self._extract_keywords(text)

        return SentimentResult(
            text=text,
            score=round(score, 3),
            label=label,
            keywords=keywords,
            source=source,
            timestamp=timestamp or datetime.now().isoformat(),
        )

    def analyze_batch(self, articles: List[Dict]) -> List[SentimentResult]:
        """
        批量分析新闻列表

        Args:
            articles: [{"title": str, "source": str, "time": str}, ...]

        Returns:
            List[SentimentResult]
        """
        results = []
        for article in articles:
            text = article.get("title", "") or article.get("content", "")
            result = self.analyze_text(
                text=text,
                source=article.get("source", "unknown"),
                timestamp=article.get("time", ""),
            )
            results.append(result)
        return results

    def summarize(self, results: List[SentimentResult]) -> SentimentSummary:
        """
        汇总舆情分析结果

        Args:
            results: 情感分析结果列表

        Returns:
            SentimentSummary
        """
        if not results:
            return SentimentSummary(
                total_articles=0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                avg_score=0.5,
                hot_keywords=[],
                sentiment_trend="neutral",
            )

        positive = sum(1 for r in results if r.label == "positive")
        negative = sum(1 for r in results if r.label == "negative")
        neutral = sum(1 for r in results if r.label == "neutral")
        avg_score = sum(r.score for r in results) / len(results)

        # 热词统计
        all_keywords = []
        for r in results:
            all_keywords.extend(r.keywords)
        hot_keywords = Counter(all_keywords).most_common(10)

        # 趋势判断
        if avg_score >= 0.6:
            trend = "bullish"
        elif avg_score <= 0.4:
            trend = "bearish"
        else:
            trend = "neutral"

        return SentimentSummary(
            total_articles=len(results),
            positive_count=positive,
            negative_count=negative,
            neutral_count=neutral,
            avg_score=round(avg_score, 3),
            hot_keywords=hot_keywords,
            sentiment_trend=trend,
        )

    def analyze_stock_sentiment(
        self,
        stock_name: str,
        news_data: pd.DataFrame,
    ) -> Dict:
        """
        分析个股舆情

        Args:
            stock_name: 股票名称
            news_data: 新闻 DataFrame (columns: title, source, time)

        Returns:
            {
                "stock": str,
                "summary": SentimentSummary,
                "details": List[SentimentResult],
                "recommendation": str,
            }
        """
        # 过滤相关股票新闻
        if not news_data.empty and "title" in news_data.columns:
            mask = news_data["title"].str.contains(stock_name, na=False)
            stock_news = news_data[mask]
        else:
            stock_news = pd.DataFrame()

        if stock_news.empty:
            return {
                "stock": stock_name,
                "summary": SentimentSummary(0, 0, 0, 0, 0.5, [], "neutral"),
                "details": [],
                "recommendation": "暂无相关新闻",
            }

        # 分析
        articles = stock_news.to_dict("records")
        results = self.analyze_batch(articles)
        summary = self.summarize(results)

        # 建议
        if summary.sentiment_trend == "bullish" and summary.positive_count > summary.negative_count * 2:
            recommendation = f"{stock_name} 舆情偏正面, 市场情绪较好"
        elif summary.sentiment_trend == "bearish" and summary.negative_count > summary.positive_count * 2:
            recommendation = f"{stock_name} 舆情偏负面, 建议关注风险"
        else:
            recommendation = f"{stock_name} 舆情中性, 建议结合基本面判断"

        return {
            "stock": stock_name,
            "summary": summary,
            "details": results,
            "recommendation": recommendation,
        }

    # ── Private helpers ──────────────────────────────────

    def _rule_based_score(self, text: str) -> float:
        """基于关键词的规则打分"""
        pos_count = sum(1 for w in self.POSITIVE_WORDS if w in text)
        neg_count = sum(1 for w in self.NEGATIVE_WORDS if w in text)

        total = pos_count + neg_count
        if total == 0:
            return 0.5

        return pos_count / total

    def _extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """
        简单关键词提取 (中文分词 + 词频)

        如果安装了 jieba, 使用 jieba 分词;
        否则用正则匹配中文词组.
        """
        try:
            import jieba
            words = jieba.lcut(text)
            # 过滤停用词和短词
            words = [w for w in words if len(w) >= 2 and not w.isdigit()]
            # 取词频最高的
            counter = Counter(words)
            return [w for w, _ in counter.most_common(top_n)]
        except ImportError:
            # 简单正则匹配
            pattern = r"[\u4e00-\u9fa5]{2,6}"
            matches = re.findall(pattern, text)
            counter = Counter(matches)
            return [w for w, _ in counter.most_common(top_n)]
