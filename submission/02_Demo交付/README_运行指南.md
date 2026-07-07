# QuantInsight Pro Demo 运行指南

**项目编号**：2026FINTECH-FINT-0093  
**产品 Demo**：https://3blue1brownlab.cn  
**版本**：AFAC2026 提交包 V1.0

---

## 一、在线访问（推荐）

直接访问生产环境，无需本地安装：

**https://3blue1brownlab.cn**

包含 8 大功能模块：智能选股、SHAP 解读、AI 投研问答、量化回测、智能盯盘、模拟交易、自动报告、实时数据看板。

---

## 二、本地一键启动（Windows）

### 方式 A：双击批处理

1. 进入 `submission/02_Demo交付/` 目录
2. 双击 **`启动Demo.bat`**
3. 等待依赖安装与启动（首次约 2–5 分钟）
4. 浏览器自动打开 `http://localhost:8501`

### 方式 B：手动命令行

```powershell
# 1. 进入 Demo 目录
cd D:\AFAC2026金融智能创新大赛\quantinsight-deploy\streamlit_app

# 2. 创建虚拟环境（首次）
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动
streamlit run app.py
```

---

## 三、系统要求

| 项目 | 最低要求 |
|------|----------|
| 操作系统 | Windows 10+ / macOS / Linux |
| Python | 3.10+（推荐 3.11） |
| 内存 | 4 GB+ |
| 磁盘 | 500 MB（含依赖） |
| 网络 | 可选（离线可用演示数据 fallback） |

---

## 四、依赖清单

`streamlit_app/requirements.txt`：

```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.17.0
akshare>=1.12.0
matplotlib>=3.7.0
openpyxl>=3.1.0
snownlp>=0.12.3
jieba>=0.42.1
requests>=2.31.0
bcrypt>=4.0.0
```

---

## 五、功能演示路径（3 分钟版）

按以下顺序操作，覆盖 AFAC 评审核心关注点：

| 步骤 | 页面/模块 | 演示要点 | 建议时长 |
|------|-----------|----------|----------|
| 1 | 首页 / 数据看板 | 品牌色、实时行情卡片 | 20s |
| 2 | **智能选股** | 17 因子评分 → Top10 推荐 | 40s |
| 3 | **SHAP 解读** | 因子贡献度排序 + Force Plot 单股归因 | 50s |
| 4 | **AI 投研问答** | 自然语言提问 → RAG 引用溯源 | 40s |
| 5 | **量化策略回测** | HS300 多因子 11.4 年 → 年化 8.56% | 30s |

---

## 六、验证检查清单

启动后请确认以下项目：

- [ ] 页面正常加载，无 Python traceback
- [ ] 智能选股可输出 Top10 列表
- [ ] SHAP 图表可渲染（Summary Bar / Force Plot）
- [ ] AI 问答可输入并返回回复（或演示模式 fallback）
- [ ] 回测页面可选择「多因子」策略并显示指标

### 自动化测试

```powershell
cd streamlit_app
python test_backtest_engine.py
# 预期：7 passed
```

---

## 七、常见问题

### Q1：pip install 失败

使用国内镜像：

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2：akshare 数据获取超时

Demo 内置 3 层 fallback（akshare → 东方财富 → 示例数据），不影响演示。

### Q3：端口 8501 被占用

```powershell
streamlit run app.py --server.port 8502
```

### Q4：SHAP 图不显示

SHAP 为可选依赖，部分环境需额外安装：

```powershell
pip install shap xgboost
```

---

## 八、项目结构

```
streamlit_app/
├── app.py                  # 主应用（4500+ 行）
├── backtest_engine.py      # 开源回测引擎（MIT）
├── requirements.txt        # 依赖
├── features/
│   ├── stock_screener.py   # 智能选股
│   ├── shap_explainer.py   # SHAP 可解释性
│   └── ...
└── ai/
    ├── rag_engine.py       # AI 投研问答
    └── agent_orchestrator.py
```

---

## 九、免责声明

本 Demo 仅供 AFAC2026 参赛技术验证，**不构成投资建议**。回测基于历史公开数据，不代表未来收益。

---

**技术支持**：王宇寒 cto@3blue1brownlab.cn  
**产品咨询**：官馨 product@3blue1brownlab.cn
