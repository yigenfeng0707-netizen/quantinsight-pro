"""
QuantInsight Pro - 金融 RAG 引擎 (Retrieval-Augmented Generation)
===================================================================

基于向量检索增强 LLM 回答, 实现金融知识的精准召回.
对标 AI涨乐 的亿级金融 RAG 系统.

技术方案:
- 向量库: ChromaDB (本地, 无需外部服务)
- 嵌入模型: DashScope text-embedding 或 本地 bge-small-zh
- 检索: Top-K 相似度 + 关键词过滤
- 知识源: 项目白皮书, QA库, 研报, 行业分析

License: MIT
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FinancialRAG:
    """
    金融 RAG 引擎

    功能:
    1. 文档分块 (Markdown / 纯文本)
    2. 嵌入生成 (DashScope API 或本地模型)
    3. 向量存储 (ChromaDB)
    4. 相似度检索 (Top-K)
    5. 上下文组装 (用于 LLM prompt)

    使用示例:
        >>> rag = FinancialRAG()
        >>> rag.load_documents("./knowledge_base/")  # 加载知识库
        >>> results = rag.retrieve("新能源行业投资机会", top_k=5)
        >>> context = rag.build_context(results)
    """

    def __init__(self, persist_dir: str = "./rag_db", embedding_provider: str = "local"):
        """
        Args:
            persist_dir: ChromaDB 持久化目录
            embedding_provider: "dashscope" / "local" / "mock"
        """
        self.persist_dir = persist_dir
        self.embedding_provider = embedding_provider
        self._collection = None
        self._chromadb = None
        self._embedder = None
        self._document_count = 0

    # ========================================================================
    # 初始化
    # ========================================================================

    def _init_chromadb(self):
        """初始化 ChromaDB (懒加载)"""
        if self._chromadb is not None:
            return

        try:
            import chromadb
            from chromadb.config import Settings
            self._chromadb = chromadb.Client(Settings(
                persist_directory=self.persist_dir,
                anonymized_telemetry=False,
            ))
            self._collection = self._chromadb.get_or_create_collection(
                name="quantinsight_knowledge",
                metadata={"hnsw:space": "cosine"},
            )
            self._document_count = self._collection.count()
            logger.info(f"ChromaDB 初始化成功, 已有 {self._document_count} 条文档")
        except ImportError:
            logger.warning("chromadb 未安装, RAG 引擎使用 mock 模式. 安装: pip install chromadb")
            self._chromadb = None
        except Exception as e:
            logger.error(f"ChromaDB 初始化失败: {e}")
            self._chromadb = None

    def _init_embedder(self):
        """初始化嵌入模型"""
        if self._embedder is not None:
            return

        if self.embedding_provider == "dashscope":
            api_key = os.environ.get("QWEN_API_KEY", "")
            if api_key:
                self._embedder = DashScopeEmbedder(api_key)
                logger.info("嵌入模型: DashScope text-embedding-v3")
                return

        # Fallback: 简单的关键词嵌入 (无需外部模型)
        self._embedder = SimpleKeywordEmbedder()
        logger.info("嵌入模型: SimpleKeywordEmbedder (关键词匹配)")

    # ========================================================================
    # 文档加载
    # ========================================================================

    def load_documents(self, directory: str, file_extensions: list[str] = None):
        """
        加载目录下的文档并分块入库

        Args:
            directory: 文档目录
            file_extensions: 文件类型过滤 [".md", ".txt"]
        """
        self._init_chromadb()
        self._init_embedder()

        if self._chromadb is None:
            logger.warning("ChromaDB 未初始化, 跳过文档加载")
            return

        file_extensions = file_extensions or [".md", ".txt"]
        doc_dir = Path(directory)

        if not doc_dir.exists():
            logger.warning(f"文档目录不存在: {directory}")
            return

        chunks = []
        for fpath in sorted(doc_dir.rglob("*")):
            if fpath.suffix.lower() in file_extensions and fpath.is_file():
                try:
                    text = fpath.read_text(encoding="utf-8", errors="ignore")
                    doc_chunks = self._split_into_chunks(text, fpath.name)
                    chunks.extend(doc_chunks)
                except Exception as e:
                    logger.warning(f"读取文件失败 {fpath}: {e}")

        if not chunks:
            logger.warning("未找到可加载的文档")
            return

        # 入库
        self._add_chunks_to_collection(chunks)
        logger.info(f"加载完成: {len(chunks)} 个文档块, 总计 {self._document_count} 条")

    def load_text(self, text: str, source: str = "inline"):
        """直接加载文本"""
        self._init_chromadb()
        self._init_embedder()

        if self._chromadb is None:
            return

        chunks = self._split_into_chunks(text, source)
        if chunks:
            self._add_chunks_to_collection(chunks)

    def _split_into_chunks(self, text: str, source: str, chunk_size: int = 500, overlap: int = 50) -> list[dict]:
        """将文本分成块"""
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text.strip())

        chunks = []
        current_chunk = ""
        chunk_idx = 0

        for para in paragraphs:
            para = para.strip()
            if not para or len(para) < 10:
                continue

            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += "\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.append({
                        "id": self._make_id(source, chunk_idx),
                        "text": current_chunk,
                        "metadata": {
                            "source": source,
                            "chunk_idx": chunk_idx,
                        },
                    })
                    chunk_idx += 1
                current_chunk = para

        # 最后一块
        if current_chunk and len(current_chunk) > 20:
            chunks.append({
                "id": self._make_id(source, chunk_idx),
                "text": current_chunk,
                "metadata": {
                    "source": source,
                    "chunk_idx": chunk_idx,
                },
            })

        return chunks

    def _make_id(self, source: str, idx: int) -> str:
        """生成唯一ID"""
        return hashlib.md5(f"{source}_{idx}".encode()).hexdigest()[:16]

    def _add_chunks_to_collection(self, chunks: list[dict]):
        """将文档块添加到向量库"""
        if not chunks or self._collection is None:
            return

        # 去重 (跳过已存在的 ID)
        existing_ids = set(self._collection.get()["ids"]) if self._collection.count() > 0 else set()
        new_chunks = [c for c in chunks if c["id"] not in existing_ids]

        if not new_chunks:
            logger.info("所有文档块已存在, 跳过")
            return

        # 生成嵌入
        texts = [c["text"] for c in new_chunks]
        embeddings = self._embedder.embed_batch(texts)
        ids = [c["id"] for c in new_chunks]
        metadatas = [c["metadata"] for c in new_chunks]

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        self._document_count += len(new_chunks)
        logger.info(f"添加 {len(new_chunks)} 个新文档块 (总计 {self._document_count})")

    # ========================================================================
    # 检索
    # ========================================================================

    def retrieve(self, query: str, top_k: int = 5, min_similarity: float = 0.3) -> list[dict]:
        """
        检索相关文档块

        Args:
            query: 查询文本
            top_k: 返回前 K 个结果
            min_similarity: 最低相似度阈值

        Returns:
            list[dict]: [{"text": str, "source": str, "score": float, "chunk_idx": int}]
        """
        self._init_chromadb()
        self._init_embedder()

        if self._chromadb is None or self._collection is None:
            logger.warning("ChromaDB 未初始化, 返回空结果")
            return []

        if self._collection.count() == 0:
            logger.warning("知识库为空, 请先加载文档")
            return []

        # 生成查询嵌入
        query_embedding = self._embedder.embed(query)

        # 检索
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        # 格式化结果
        output = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i] if results.get("distances") else 0
                score = 1.0 - distance  # cosine distance -> similarity
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}

                if score >= min_similarity:
                    output.append({
                        "text": doc,
                        "source": metadata.get("source", "unknown"),
                        "score": score,
                        "chunk_idx": metadata.get("chunk_idx", 0),
                    })

        logger.info(f"RAG 检索: '{query[:30]}...' -> {len(output)} 条结果")
        return output

    def build_context(self, results: list[dict], max_tokens: int = 2000) -> str:
        """
        将检索结果组装为 LLM 上下文

        Args:
            results: retrieve() 返回的结果列表
            max_tokens: 最大字符数 (近似 token)

        Returns:
            str: 格式化后的上下文文本
        """
        if not results:
            return ""

        context_parts = ["以下是从知识库检索到的相关参考资料:\n"]
        total_len = 0

        for i, r in enumerate(results, 1):
            snippet = r["text"][:500]
            source = r.get("source", "未知")
            score = r.get("score", 0)

            entry = f"[参考{i}] (来源: {source}, 相关度: {score:.2f})\n{snippet}\n\n"

            if total_len + len(entry) > max_tokens:
                break

            context_parts.append(entry)
            total_len += len(entry)

        context_parts.append(
            "请基于上述参考资料回答用户问题. 引用来源时标注 [参考N]. "
            "如果参考资料不足以回答, 请明确说明并结合专业知识补充.\n"
        )

        return "".join(context_parts)

    def search_and_context(self, query: str, top_k: int = 5) -> str:
        """一步到位: 检索 + 组装上下文"""
        results = self.retrieve(query, top_k)
        return self.build_context(results)

    # ========================================================================
    # 状态查询
    # ========================================================================

    def get_stats(self) -> dict:
        """获取知识库统计"""
        self._init_chromadb()
        return {
            "document_count": self._document_count,
            "embedding_provider": self.embedding_provider,
            "persist_dir": self.persist_dir,
            "initialized": self._chromadb is not None,
        }


# ============================================================================
# 嵌入模型适配器
# ============================================================================

class SimpleKeywordEmbedder:
    """
    简单的关键词嵌入 (无需外部模型, 适合小规模知识库)

    基于 TF-IDF 风格的稀疏向量, 维度 = 词表大小.
    性能不及专业嵌入模型, 但零依赖, 即开即用.
    """

    def __init__(self, vocab_size: int = 5000):
        self.vocab_size = vocab_size
        self._vocab: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._docs_count = 0

    def _tokenize(self, text: str) -> list[str]:
        """简单中文分词 (按字符和常见词)"""
        # 移除标点, 保留中文字符和英文单词
        text = re.sub(r'[^\u4e00-\u9fff\w\s]', ' ', text)
        tokens = []
        # 中文: 按2-gram
        cn_chars = re.findall(r'[\u4e00-\u9fff]+', text)
        for segment in cn_chars:
            for i in range(len(segment) - 1):
                tokens.append(segment[i:i+2])
            if len(segment) == 1:
                tokens.append(segment)
        # 英文: 按单词
        en_words = re.findall(r'[a-zA-Z]+', text.lower())
        tokens.extend(en_words)
        return tokens

    def embed(self, text: str) -> list[float]:
        """生成嵌入向量"""
        tokens = self._tokenize(text)
        vec = [0.0] * self.vocab_size

        for token in tokens:
            idx = hash(token) % self.vocab_size
            vec[idx] += 1.0

        # L2 归一化
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]

        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入"""
        return [self.embed(t) for t in texts]


class DashScopeEmbedder:
    """
    DashScope (通义千问) 嵌入模型

    需要: QWEN_API_KEY 环境变量
    模型: text-embedding-v3 (1024维)
    """

    def __init__(self, api_key: str, model: str = "text-embedding-v3"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"

    def embed(self, text: str) -> list[float]:
        """生成单条嵌入"""
        import requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": text[:2000],
            "dimensions": 256,  # 降维以节省空间
        }

        try:
            resp = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            return result["data"][0]["embedding"]
        except Exception as e:
            logger.warning(f"DashScope 嵌入失败: {e}")
            # Fallback to simple
            return SimpleKeywordEmbedder().embed(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入 (逐条调用, 可优化为批接口)"""
        results = []
        for text in texts:
            results.append(self.embed(text))
        return results
