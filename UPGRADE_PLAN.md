# QuantInsight Pro 全面升级改造方案 — 对标华泰AI涨乐

## Context

QuantInsight Pro 当前是一个以比赛交付为导向的 Streamlit 演示应用，具备 5 个功能页面（首页/AI问答/另类数据/回测/行业分析），使用 akshare 免费数据接口，LLM 直连无 RAG/Agent 框架，另类数据全部为模拟数据。

华泰证券 AI涨乐 是面向财富管理领域的 AI 原生应用，具备智能选股、智能盯盘、智能交易、智能指令四大核心功能，采用五层技术架构和"规划-执行-反思-调整"的智能闭环。

本方案目标：将 QuantInsight Pro 从演示级升级为对标 AI涨乐 的 AI 原生投研平台，核心抓手是 (1) 接入东方财富 Choice 数据源 (2) 构建 Multi-Agent + RAG 架构 (3) 实现四大智能功能。

---

## 现状差距分析

| 维度 | 当前状态 | AI涨乐对标 | 差距 |
|------|---------|-----------|------|
| **数据层** | akshare 直连，仅指数+行业+新闻；`data_pipeline.py` 未接入 `app.py` | 东方财富全量数据 + 金融中台 | 缺少个股行情、财务报表、估值、资金流、宏观数据 |
| **AI引擎** | 3家LLM直连，无RAG/无Agent/无数据接地 | 主Agent+多Agent协作，RAG+金融知识图谱 | 无规划-执行-反思闭环，无引用溯源 |
| **智能选股** | 无 | 自然语言选股 + 多模型协同 + 可解释逻辑 | 全部缺失 |
| **智能盯盘** | 无 | 7×24h 监控 + 主动预警推送 | 全部缺失 |
| **智能交易** | 无 | 语音/文字下单 + 风控体系 | 全部缺失 |
| **智能指令** | 无 | 复杂周期任务 + 自动执行 + 主动推送 | 全部缺失 |
| **另类数据** | 全部模拟（正弦波卫星/随机舆情/硬编码供应链） | 真实事件驱动分析 | 无真实NLP，无真实供应链 |
| **回测引擎** | 5策略，单标的，无组合/风控/参数优化 | Agent调度策略回测 | 缺组合回测、风险管理、自定义策略 |
| **基础设施** | 无数据库/无API/无认证/无监控 | 五层架构 + K8s + GPU | 无生产级能力 |

---

## 改造方案总览（9大阶段，45个子任务）

### Task 1：东方财富 Choice 数据源接入
> **目标**：构建 `EastMoneyChoiceSource` 数据源，获取 A 股全量数据  
> **关键文件**：新建 `streamlit_app/eastmoney_source.py`，修改 `data_pipeline.py`、`app.py`

| 子任务 | 说明 | 文件 |
|--------|------|------|
| 1.1 创建 `EastMoneyChoiceSource` 类 | 继承 `DataSource` ABC，封装 akshare 东方财富接口 | `eastmoney_source.py` |
| 1.2 实现实时行情接口 | `stock_zh_a_spot_em()` → 全A股实时报价(代码/名称/价格/PE/PB/市值/成交量) | `eastmoney_source.py` |
| 1.3 实现个股历史数据接口 | `stock_zh_a_hist(symbol, period, start, end)` → OHLCV | `eastmoney_source.py` |
| 1.4 实现财务报表接口 | `stock_yjbb_em` / `stock_lrb_em` / `stock_zcfz_em` / `stock_xjll_em` → 业绩报表/利润表/资产负债表/现金流量表 | `eastmoney_source.py` |
| 1.5 实现资金流向接口 | `stock_individual_fund_flow_rank` / `stock_hsgt_hold_stock_em` → 主力资金排名/北向持仓 | `eastmoney_source.py` |
| 1.6 实现估值对比接口 | `stock_zh_valuation_comparison_em` → 同业PE/PB/PS对比 | `eastmoney_source.py` |
| 1.7 实现宏观经济接口 | 通过akshare获取GDP/CPI/PMI/M2等宏观指标 | `eastmoney_source.py` |
| 1.8 扩展 `DataSource` ABC | 在 `data_pipeline.py` 中添加新抽象方法（`fetch_stock_universe`, `fetch_financials`等） | `data_pipeline.py` |
| 1.9 创建缓存适配层 | `StreamlitCacheAdapter` 桥接异步Pipeline与Streamlit缓存 | `data_cache.py` |
| 1.10 替换 `app.py` 数据调用 | 将 `app.py` 中直接 akshare 调用替换为 DataPipeline + EastMoneyChoiceSource | `app.py` |

### Task 2：AI 架构升级（Multi-Agent + RAG + 数据接地）
> **目标**：对标AI涨乐"规划-执行-反思-调整"智能闭环  
> **关键文件**：新建 `streamlit_app/ai/` 目录，4个新文件

| 子任务 | 说明 | 文件 |
|--------|------|------|
| 2.1 主Agent编排器 | `MainAgent` 类：plan→execute→reflect→adjust→synthesize，最大3轮反思 | `ai/agent_orchestrator.py` |
| 2.2 专业子Agent群 | `StockSelectionAgent` / `AnalysisAgent` / `RiskAgent` / `PortfolioAgent` / `MarketMonitorAgent` | `ai/sub_agents.py` |
| 2.3 RAG 引擎 | ChromaDB向量库 + 金融知识嵌入 + Top-K检索 + 重排序 | `ai/rag_engine.py` |
| 2.4 引用溯源系统 | `CitationTracker`：追踪数据来源，生成结构化引用链 | `ai/citation_system.py` |
| 2.5 数据接地层 | AI回答时自动检索平台数据（行情/财务/回测结果）作为上下文 | `ai/data_grounder.py` |
| 2.6 改造AI问答页面 | 替换 `ai_qa_real()` 为 `MainAgent.process_query()`，显示推理链+引用 | `app.py` |
| 2.7 知识库种子数据 | 将项目现有白皮书/QA库/研报等内容导入向量库 | `ai/knowledge_base/` |

### Task 3：智能选股（核心功能）
> **目标**：对标AI涨乐"一句话选股"，自然语言筛选 + 多因子评分 + 可解释逻辑  
> **关键文件**：新建 `streamlit_app/features/` 目录

| 子任务 | 说明 | 文件 |
|--------|------|------|
| 3.1 自然语言选股引擎 | `NaturalLanguageScreener`：LLM解析NL→结构化过滤条件→执行筛选 | `features/stock_screener.py` |
| 3.2 多因子评分系统 | `MultiFactorScorer`：估值(25%)+成长(25%)+质量(25%)+动量(25%)，行业中性 | `features/factor_scorer.py` |
| 3.3 股票对比工具 | `StockComparator`：最多5只股票横向对比，雷达图+AI分析 | `features/stock_comparison.py` |
| 3.4 选股结果解释 | 生成人类可读的推荐逻辑："因为PE低于行业均值且ROE连续3年提升" | `features/stock_screener.py` |
| 3.5 选股UI页面 | 新增侧边栏"🎯 智能选股"，NL输入+结构化过滤+结果表格+对比入口 | `app.py` |

### Task 4：智能盯盘（核心功能）
> **目标**：对标AI涨乐"7×24h监控+主动预警"  
> **关键文件**：3个新文件

| 子任务 | 说明 | 文件 |
|--------|------|------|
| 4.1 组合管理器 | `PortfolioManager`：创建/管理组合，实时盈亏，风险指标(VaR/Beta/集中度) | `features/portfolio_manager.py` |
| 4.2 智能预警引擎 | `SmartAlertEngine`：价格/成交量/资金流/技术面/新闻/财报6类预警 | `features/alert_system.py` |
| 4.3 NL设置预警 | "牧原股份涨到50元提醒"→结构化条件，对标AI涨乐一句话盯盘 | `features/alert_system.py` |
| 4.4 市场大盘面板 | `MarketDashboard`：指数/板块热力图/涨跌家数/资金流全景/市场宽度 | `features/market_dashboard.py` |
| 4.5 盯盘UI页面 | 新增"👁 智能盯盘"+"💼 我的组合"两个侧边栏页面 | `app.py` |

### Task 5：智能交易（模拟）
> **目标**：对标AI涨乐"简化操作+风控体系"  
> **关键文件**：2个新文件

| 子任务 | 说明 | 文件 |
|--------|------|------|
| 5.1 交易模拟器 | `TradeSimulator`：市价/限价/止损/止单，含滑点模型和智能拆单 | `features/trade_simulator.py` |
| 5.2 风控引擎 | `RiskControlEngine`：单股≤20%/单行业≤40%/日亏损≤3%/回撤≤10% | `features/risk_control.py` |
| 5.3 反情绪化交易 | 止损冷却期(30min)/恐慌卖出确认/日内交易次数警告 | `features/risk_control.py` |
| 5.4 NL下单 | "买入500股贵州茅台"→结构化订单→风控检查→执行 | `features/trade_simulator.py` |
| 5.5 交易UI页面 | 新增"💹 模拟交易"页面：下单表单+风控展示+交易历史+盈亏追踪 | `app.py` |

### Task 6：智能指令（周期任务）
> **目标**：对标AI涨乐"承接复杂周期性投研任务并自动执行"  
> **关键文件**：2个新文件

| 子任务 | 说明 | 文件 |
|--------|------|------|
| 6.1 任务调度器 | `ResearchTaskScheduler`：创建/执行/推送周期投研任务 | `features/task_scheduler.py` |
| 6.2 预置任务模板 | 晨报(8:30)/盘后总结(15:30)/周报(周五)/财报监控/宏观数据跟踪 | `features/task_scheduler.py` |
| 6.3 报告生成器 | `AutoReportGenerator`：从Agent输出自动生成结构化报告(含图表) | `features/report_generator.py` |
| 6.4 NL创建任务 | "每天早上帮我出一份持仓分析报告"→调度配置 | `features/task_scheduler.py` |
| 6.5 智能指令UI页面 | 新增"📋 智能指令"页面：任务创建向导+任务列表+结果归档 | `app.py` |

### Task 7：另类数据增强（替换模拟数据）
> **目标**：将全部模拟数据替换为真实分析  
> **关键文件**：3个新文件

| 子任务 | 说明 | 文件 |
|--------|------|------|
| 7.1 真实舆情NLP | `NewsSentimentEngine`：FinBERT/SnowNLP对东方财富新闻做情感分析，按行业聚合 | `features/sentiment_analyzer.py` |
| 7.2 供应链可视化 | `SupplyChainVisualizer`：基于行业成分股构建产业链Sankey图 | `features/supply_chain_tracker.py` |
| 7.3 ESG数据模块 | 基于公开数据的ESG评分（环境/社会/治理三维度） | `features/esg_data.py` |
| 7.4 替换模拟数据 | 在app.py的另类数据页面中用真实分析替换正弦波/随机数/硬编码 | `app.py` |

### Task 8：技术基础设施升级
> **目标**：生产级后端分离  
> **关键文件**：新建 `backend/` 目录

| 子任务 | 说明 | 文件 |
|--------|------|------|
| 8.1 FastAPI后端 | RESTful API端点（认证/行情/组合/预警/AI） | `backend/main.py` + `routes/` |
| 8.2 WebSocket实时推送 | 行情推送/预警推送/任务完成推送 | `backend/api/websocket.py` |
| 8.3 数据库 | SQLite(开发)/PostgreSQL(生产)：用户/组合/持仓/交易/预警/任务/聊天记录 | `backend/models/` |
| 8.4 用户认证 | JWT认证 + 用户管理 + 多租户数据隔离 | `backend/core/auth.py` |
| 8.5 Redis缓存 | 行情缓存(60s)/财报缓存(24h)/AI回答缓存(1h) | `backend/core/cache.py` |

### Task 9：UI/UX 全面提升
> **目标**：对标AI涨乐双界面(GUI+LUI)设计语言  
> **关键文件**：`app.py` + 新UI组件

| 子任务 | 说明 | 文件 |
|--------|------|------|
| 9.1 现代化UI组件 | 卡片式布局 + 动画 + streamlit-extras/antd-components | `app.py` |
| 9.2 数据导出 | CSV/Excel/PDF报告导出 | `features/data_export.py` |
| 9.3 新手引导 | 分步引导教程 | `app.py` |
| 9.4 移动端优化 | 增强响应式设计 | `app.py` |

---

## 阶段依赖关系

```
Task 1 (数据接入) ──基础──┐
                          ├──→ Task 2 (AI架构) ──→ Task 3 (智能选股)
                          │        │                       │
                          │        └──→ Task 6 (智能指令)   │
                          │                                ▼
                          ├──→ Task 4 (智能盯盘) ──→ Task 5 (智能交易)
                          │
                          └──→ Task 7 (另类数据)

Task 1-7 ──→ Task 8 (基础设施) ──→ Task 9 (UI/UX)
```

**关键路径**: Task 1 → Task 2 → Task 3 → Task 4 → Task 5

---

## 文件变更清单

### 新建文件 (21个)
| 文件 | 估计行数 | 说明 |
|------|---------|------|
| `streamlit_app/eastmoney_source.py` | ~450 | 东方财富Choice数据源 |
| `streamlit_app/data_cache.py` | ~150 | Streamlit缓存适配层 |
| `streamlit_app/ai/__init__.py` | ~5 | AI模块初始化 |
| `streamlit_app/ai/agent_orchestrator.py` | ~500 | 主Agent编排器 |
| `streamlit_app/ai/sub_agents.py` | ~600 | 5个专业子Agent |
| `streamlit_app/ai/rag_engine.py` | ~400 | RAG引擎 |
| `streamlit_app/ai/citation_system.py` | ~200 | 引用溯源 |
| `streamlit_app/ai/data_grounder.py` | ~250 | 数据接地 |
| `streamlit_app/features/__init__.py` | ~5 | 功能模块初始化 |
| `streamlit_app/features/stock_screener.py` | ~500 | 智能选股 |
| `streamlit_app/features/factor_scorer.py` | ~350 | 多因子评分 |
| `streamlit_app/features/stock_comparison.py` | ~300 | 股票对比 |
| `streamlit_app/features/portfolio_manager.py` | ~400 | 组合管理 |
| `streamlit_app/features/alert_system.py` | ~450 | 智能预警 |
| `streamlit_app/features/market_dashboard.py` | ~350 | 市场面板 |
| `streamlit_app/features/trade_simulator.py` | ~500 | 交易模拟 |
| `streamlit_app/features/risk_control.py` | ~300 | 风控引擎 |
| `streamlit_app/features/task_scheduler.py` | ~400 | 任务调度 |
| `streamlit_app/features/report_generator.py` | ~300 | 报告生成 |
| `streamlit_app/features/sentiment_analyzer.py` | ~350 | 真实NLP舆情 |
| `streamlit_app/features/supply_chain_tracker.py` | ~250 | 供应链可视化 |

### 修改文件 (3个)
| 文件 | 修改范围 |
|------|---------|
| `streamlit_app/app.py` | 大幅扩展：新增6个侧边栏页面，替换数据层，集成Agent架构 |
| `streamlit_app/data_pipeline.py` | 扩展DataSource ABC，添加新抽象方法 |
| `streamlit_app/requirements.txt` | 添加新依赖 |

---

## 安全说明

用户提供的东方财富Choice账号（13588855006）和密码应存储在环境变量或密钥管理器中，**绝不硬编码**。由于akshare的东方财富接口免费且无需登录Choice账号，本次实现优先使用akshare封装的东方财富数据端点，Choice账号可作为后续企业版数据源备选。

---

## 验证计划

每个Task完成后进行以下验证：
1. **数据验证**: 运行数据拉取脚本，确认返回数据非空且格式正确
2. **功能验证**: 在Streamlit中启动应用，逐一测试新增页面
3. **集成验证**: 确保新旧模块间无冲突，数据流畅通
4. **AI验证**: 测试自然语言输入→结构化输出→引用溯源的完整链路
5. **性能验证**: 确认缓存命中、API限流、LLM超时等边界场景正确处理
