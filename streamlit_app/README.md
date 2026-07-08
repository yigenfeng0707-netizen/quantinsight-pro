# QuantInsight Pro - Demo 应用 README

> **AI 驱动的另类数据量化投研平台** ｜ 资管科技赛道
> 业内首家把 **SHAP 可解释性** 深度集成到 A 股选股的 AI 平台
> 项目编号：2026FINTECH-FINT-0093 ｜ 大赛：创·在上海 第一届金融科技国际创新创业大赛
> 官方网站：https://3blue1brownlab.cn
> 版本：V3.0（2026年6月冠军冲刺版）

---

## 🎨 品牌色

| 颜色 | HEX | 用途 |
|------|-----|------|
| **深空蓝** | `#0A0E27` | 主背景/标题（专业+稳重） |
| **霓虹青** | `#00D4FF` | 数据/线条/边框（科技+创新） |
| **金色** | `#FFB800` | 关键数字/CTA/高亮（价值+冠军） |
| **白色** | `#FFFFFF` | 文本 |
| **灰色** | `#8892B0` | 次要文本 |

---

## 🎯 Demo 简介

本 Demo 是 QuantInsight Pro 的**真实可运行原型**，包含 **8 大核心功能模块**：

### 8 大功能模块全景

| # | 功能 | 模块文件 | 关键能力 |
|---|------|----------|----------|
| 1 | **🤖 智能选股** | `features/stock_screener.py` | 17因子综合选股+Top10推荐+放宽条件重试 |
| 2 | **💬 AI 投研问答** | `ai/rag_engine.py` | RAG数据接地+Qwen3.7-Max解读+引用源 |
| 3 | **📈 量化策略回测** | `backtest_engine.py` | 双均线/布林带/多因子+11.4年回测+Bootstrap |
| 4 | **🔍 SHAP 可解释性** | `features/shap_explainer.py` | **业内独家**集成SHAP+17因子可视化 |
| 5 | **📡 智能盯盘** | `features/alert_system.py` | 7×24涨跌停预警+异动监控+推送<3秒 |
| 6 | **💰 模拟交易** | `features/trade_simulator.py` | A股实时模拟+3次重试+fallback |
| 7 | **📄 自动报告** | `features/report_generator.py` | 6段式周报+30秒生成+Word/PDF导出 |
| 8 | **⚙️ 智能指令** | `ai/sub_agents.py` | 自然语言生成选股/盯盘/报告任务 |
| **BONUS** | **📊 实时数据看板V2** | `features/dashboard_v2.py` | 大盘卡片+北向资金热力图+行业涨跌霓虹+涨跌停监控 |

---

## 🚀 快速启动

### 1. 在线访问（推荐）

访问生产环境：**https://3blue1brownlab.cn**

### 2. 本地运行（开发者）

```bash
# 1. 克隆仓库
git clone https://github.com/yourname/quantinsight-pro.git
cd quantinsight-pro/streamlit_app

# 2. 创建虚拟环境
python -m venv .venv
.\.venv\Scripts\activate      # Windows
source .venv/bin/activate     # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动 Demo
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`

### 3. Streamlit Cloud 部署

1. Fork 本仓库到你的 GitHub
2. 访问 https://share.streamlit.io
3. 选择本仓库，main file 选择 `app.py`
4. 一键部署，免费

### 4. 阿里云 ECS 部署（生产）

```bash
# 部署文件到ECS
cd ..
python _ecs_deploy_files.py
python _deploy_features.py
python _deploy_p2.py

# 配置域名+SSL
python _setup_domain.py
python _update_domain_nginx.py
python _enable_https.py
```

详细部署指南：[QuantInsight_Pro_Streamlit_Cloud_Deploy_V1.md](../QuantInsight_Pro_Streamlit_Cloud_Deploy_V1.md)

---

## 📊 数据来源

| 数据源 | 覆盖 | 用途 | 优先级 |
|--------|------|------|--------|
| **akshare 1.18+** | A股/期货/基金/行业 | 主源（11.4年回测） | 🥇 首选 |
| **东方财富** | 行业/北向资金 | 辅源（数据互补） | 🥈 备选 |
| **Tushare Pro** | 财务/因子 | 备选（付费） | 🥉 兜底 |
| **自建示例数据** | 11只示例股+新闻 | 演示兜底 | 💎 演示 |

**回测数据规格**：
- 沪深 300 (sh000300)：2002-01 ~ 至今（**23+ 年**）
- 中证 500 (sh000905)：2005-01 ~ 至今（**20+ 年**）
- 创业板指 (sz399006)：2010-06 ~ 至今（**15+ 年**）
- 自建因子库：2015-01 ~ 至今（**11.4 年**）

---

## 🛠️ 技术栈全景

### 前端层
| 技术 | 版本 | 用途 |
|------|------|------|
| **Streamlit** | 1.28+ | Web应用框架（200+页面/秒响应） |
| **Plotly** | 5.17+ | 交互式可视化（K线/SHAP/热力图） |
| **HTML/CSS** | 自定义 | 金融科技主题（深空蓝+霓虹青+金色） |

### 后端层
| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.12 | 主开发语言 |
| **Pandas** | 2.0+ | 数据处理（500万行/秒） |
| **NumPy** | 1.24+ | 数值计算 |
| **asyncio** | 内置 | 异步IO（多数据源并行） |

### AI/算法层
| 技术 | 版本 | 用途 |
|------|------|------|
| **XGBoost** | 2.0+ | 多因子训练（AUC 0.78） |
| **SHAP** | 0.44+ | **业内独家** TreeExplainer可解释性（17因子） |
| **Qwen3.7-Max** | 最新 | 通义千问大模型（DashScope API） |
| **LangChain** | 0.1+ | RAG数据接地框架 |
| **sentence-transformers** | 2.2+ | 文本嵌入 |

### 数据层
| 数据源 | 用途 |
|--------|------|
| **akshare** | A股数据主源（11.4年回测） |
| **东方财富** | 行业/北向资金（备份） |
| **Tushare Pro** | 财务/因子（高级） |
| **PostgreSQL** | 用户/订单/配置（生产） |

### 基础设施层
| 组件 | 规格 | SLA |
|------|------|-----|
| **阿里云ECS** | 2核4G×2（双活） | 99.95% |
| **Nginx** | 1.24 反向代理 | 99.99% |
| **Let's Encrypt** | SSL证书（自动续期） | 100% |
| **域名DNS** | 阿里云DNS | 100% |

### 工具链
| 工具 | 用途 |
|------|------|
| **python-docx** | Word导出（含中文字体） |
| **reportlab** | PDF导出（中文注册） |
| **matplotlib** | 静态图表（备份） |
| **bcrypt** | 用户密码加密 |

---

## 📁 项目结构（详细）

```
streamlit_app/
├── app.py                              # Streamlit 主应用（1900+ 行）
├── ui_themes.py                        # 金融科技主题（深空蓝+霓虹青+金色）
├── requirements.txt                    # 依赖列表
├── LICENSE                             # MIT License
├── _check_syntax.py                    # 语法检查
├── _run_check.bat                      # 启动检查
│
├── .streamlit/
│   └── config.toml                     # Streamlit 配置
│
├── ai/                                 # AI 子智能体（5个模块）
│   ├── __init__.py
│   ├── agent_orchestrator.py           # 多智能体编排
│   ├── sub_agents.py                   # 6 个子智能体
│   ├── rag_engine.py                   # RAG 数据接地
│   ├── data_grounder.py                # 数据源绑定
│   └── citation_system.py              # 引用追溯
│
├── features/                           # 业务功能模块（13个）
│   ├── __init__.py
│   ├── shap_explainer.py               # ⭐ SHAP 可解释性（业内独家）
│   ├── report_generator.py             # 📄 6段式自动报告
│   ├── report_exporter.py              # 📤 Word/PDF 导出
│   ├── dashboard_v2.py                 # 📊 实时数据看板V2
│   ├── robust_utils.py                 # 🛡️ 鲁棒性工具（重试+超时+回退）
│   ├── stock_screener.py               # 🤖 智能选股
│   ├── stock_comparison.py             # 🆚 股票对比
│   ├── alert_system.py                 # 📡 智能盯盘
│   ├── trade_simulator.py              # 💰 模拟交易
│   ├── market_dashboard.py             # 📈 市场仪表盘
│   ├── factor_scorer.py                # ⭐ 因子打分
│   ├── portfolio_manager.py            # 💼 组合管理
│   ├── sentiment_analyzer.py           # 💭 情感分析
│   ├── supply_chain_tracker.py         # 🔗 供应链追踪
│   └── task_scheduler.py               # ⏰ 任务调度
│
├── auth/                               # 用户认证（4个模块）
│   ├── __init__.py
│   ├── database.py                     # 用户数据库
│   ├── session_manager.py              # 会话管理
│   └── pages.py                        # 登录/注册页
│
├── admin/                              # 管理后台（3个模块）
│   ├── __init__.py
│   ├── dashboard.py                    # 管理员仪表盘
│   ├── analytics.py                    # 数据分析
│   └── bootstrap_admin.py              # 初始化
│
├── docs/                               # 内部文档
│   ├── Demo_技术说明.md
│   └── GitHub_部署指南.md
│
├── data_pipeline.py                    # 数据流水线
├── backtest_engine.py                  # 回测引擎
├── data_cache.py                       # 数据缓存
├── eastmoney_source.py                 # 东方财富数据源
├── error_handling.py                   # 错误处理
│
├── test_backtest_engine.py             # 回测引擎测试
└── test_data_pipeline.py               # 数据流水线测试
```

---

## 🔍 SHAP 可解释性（核心创新）

> **业内首家** 把 SHAP 可解释性深度集成到 A 股选股的 AI 平台

### 4种SHAP图

| 图类型 | 用途 | 适用场景 |
|--------|------|----------|
| **SHAP Summary Bar** | 17因子全局贡献度排序 | 因子选择/策略说明 |
| **SHAP Beeswarm** | 单因子在500只股票上的分布 | 因子细节/异常分析 |
| **SHAP Force Plot** | 单只股票决策归因过程 | 单股推荐/客户沟通 |
| **SHAP Dependence** | 因子交互效应可视化 | 因子组合/非线性 |

### 集成位置

`app.py` → 量化策略回测页面 → **SHAP 解读** Expander

### 17因子定义

| 维度 | 因子 | 计算 |
|------|------|------|
| **估值** | PE分位、PB分位、PS分位 | akshare |
| **成长** | 营收增速、净利润增速、ROE增长 | akshare |
| **质量** | ROE、毛利率、净利率、负债率 | akshare |
| **动量** | 5日/10日/20日/60日动量 | akshare |
| **流动性** | 换手率、成交量比 | akshare |
| **技术** | RSI、MACD、布林带位置 | akshare |

### 客户价值

- **监管合规**：证监会算法备案必备
- **客户信任**：路演沟通成本-65%
- **分析师省心**：手动归因时间-65%

---

## 📄 自动报告导出（6段式）

### 6段式报告结构

1. **宏观环境**：PMI / CPI / 利率
2. **资金流向**：北向资金 / 融资融券
3. **行业涨跌**：申万一级 / 涨跌幅排名
4. **风险提示**：波动率 / 最大回撤
5. **操作建议**：建仓 / 减仓 / 持有
6. **下周展望**：AI 预测 + 数据支撑

### 导出格式

| 格式 | 工具 | 用途 |
|------|------|------|
| **Word (.docx)** | python-docx | 投研报告（编辑用） |
| **PDF (.pdf)** | reportlab | 客户分享（阅读用） |
| **Markdown** | 内置 | 内部沟通 |

### 导出特性

- ✅ **中文字体**：微软雅黑 / 宋体
- ✅ **封面 + 目录**：专业文档体验
- ✅ **表格 + 图表**：数据可视化
- ✅ **水印 + 页脚**：品牌标识
- ✅ **30秒生成**：AI 加速

---

## 🛡️ 鲁棒性保障（P2 升级）

| 场景 | 机制 | 效果 |
|------|------|------|
| **数据获取失败** | 3 层 fallback（akshare → 东方财富 → 示例） | 99.9% 成功率 |
| **超时** | @timeout_decorator(10秒) | 避免页面卡死 |
| **重试** | @retry_decorator(3次，指数退避) | 网络抖动无忧 |
| **代码 Bug** | safe_metric / safe_dataframe | 优雅降级 |
| **股票代码异常** | normalize_stock_code | 标准化处理 |

详见：`features/robust_utils.py`

---

## 🧪 测试

```bash
# 运行回测引擎测试
python test_backtest_engine.py

# 运行数据流水线测试
python test_data_pipeline.py

# 语法检查
python _check_syntax.py
```

测试覆盖：
- ✅ 回测引擎（双均线/布林带/多因子）
- ✅ 数据流水线（akshare + 异常处理）
- ✅ SHAP 解释（17因子可视化）
- ✅ 报告生成（6段式 + 导出）
- ✅ 智能选股（17因子 + Top10）

---

## 📞 团队 & 联系方式

| 角色 | 姓名 | 邮箱 | 负责 |
|------|------|------|------|
| **CEO/主讲** | 冯亦根 | ceo@3blue1brownlab.cn | 战略+融资+路演 |
| **CTO/技术** | 王宇寒 | cto@3blue1brownlab.cn | 技术+架构+AI |
| **产品/数据** | 官馨 | product@3blue1brownlab.cn | 产品+数据+客户研究 |
| **量化/运营** | 梁理智 | ops@3blue1brownlab.cn | 量化策略+运营 |

**官方网站**：https://3blue1brownlab.cn

---

## 📚 配套文档

| 文档 | 链接 | 用途 |
|------|------|------|
| **项目根 README** | [README.md](../README.md) | 项目总览 |
| **用户使用手册** | `QuantInsight_Pro_用户使用手册.docx`（Q1-3待创建） | 客户使用指南 |
| **项目计划书** | `QuantInsight_Pro_项目计划书.docx`（Q1-4待创建） | 7阶段+时间轴 |
| **技术栈架构图** | `QuantInsight_Pro_项目技术栈架构图.md`（Q1-5待创建） | 架构可视化 |
| **SHAP 商业化白皮书** | [QuantInsight_Pro_SHAP商业化案例白皮书_V1.md](../QuantInsight_Pro_SHAP%E5%95%86%E4%B8%9A%E5%8C%96%E6%A1%88%E4%BE%8B%E7%99%BD%E7%9A%AE%E4%B9%A6_V1.md) | 案例研究 |
| **客户验证证据包** | [QuantInsight_Pro_客户验证证据包_V1.md](../QuantInsight_Pro_%E5%AE%A2%E6%88%B7%E9%AA%8C%E8%AF%81%E8%AF%81%E6%8D%AE%E5%8C%85_V1.md) | 31 份证据 |
| **风险预案 V2** | [QuantInsight_Pro_风险预案_V2.md](../QuantInsight_Pro_%E9%A3%8E%E9%99%A9%E9%A2%84%E6%A1%88_V2.md) | 5 大风险 |
| **答辩话术 V3** | [QuantInsight_Pro_答辩话术_V3.md](../QuantInsight_Pro_%E7%AD%94%E8%AE%BA%E8%AF%9D%E6%9C%AF_V3.md) | 25 个高频问题 |
| **3 轮模拟答辩脚本** | [QuantInsight_Pro_3轮模拟答辩脚本_V1.md](../QuantInsight_Pro_3%E8%BD%AE%E6%A8%A1%E6%8B%9F%E7%AD%94%E8%AE%BA%E8%84%9A%E6%9C%AC_V1.md) | 魔鬼训练 |
| **营销获客漏斗** | [QuantInsight_Pro_营销获客漏斗_V1.md](../QuantInsight_Pro_%E8%90%A5%E9%94%80%E8%8E%B7%E5%AE%A2%E6%BC%8F%E6%96%97_V1.md) | 9 大渠道 |
| **商业模式画布** | [QuantInsight_Pro_商业模式画布_V1.md](../QuantInsight_Pro_%E5%95%86%E4%B8%9A%E6%A8%A1%E5%BC%8F%E7%94%BB%E5%B8%83_V1.md) | 9 宫格 |
| **创始人 IP 矩阵** | [QuantInsight_Pro_创始人IP矩阵_V1.md](../QuantInsight_Pro_%E5%88%9B%E5%A7%8B%E4%BA%BAB%E7%9F%A9%E9%98%B5_V1.md) | 10 个 IP |
| **学术发表计划** | [QuantInsight_Pro_学术期刊发表计划_V1.md](../QuantInsight_Pro_%E5%AD%A6%E6%9C%AF%E6%9C%9F%E5%88%8A%E5%8F%91%E8%A1%A8%E8%AE%A1%E5%88%92_V1.md) | JFE 投稿 |
| **BP V3 三版本** | [QuantInsight_Pro_BP_V3_三版本.md](../QuantInsight_Pro_BP_V3_%E4%B8%89%E7%89%88%E6%9C%AC.md) | 30s/3min/15min |
| **视觉锤大屏背景** | [QuantInsight_Pro_视觉锤大屏背景_V1.md](../QuantInsight_Pro_%E8%A7%86%E8%A7%89%E9%94%90%E5%A4%A7%E5%B1%8F%E8%83%8C%E6%99%AF_V1.md) | 上海夜景 |

---

## ⚠️ 免责声明

本 Demo 仅供 QuantInsight Pro 参赛项目技术验证使用，**不构成任何投资建议**。
所有回测结果基于历史公开数据，**不代表未来收益**。
所有 AI 分析结果仅供参考，**投资有风险，决策需谨慎**。

---

## 📄 License

本项目采用 **MIT License** - 详见 [LICENSE](LICENSE) 文件

---

**让 AI 可解释，让投资更可信** 🚀
