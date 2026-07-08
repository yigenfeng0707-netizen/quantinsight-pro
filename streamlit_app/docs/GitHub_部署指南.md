# QuantInsight Pro Demo - GitHub 部署指南

> 本指南帮助你把 Demo 部署到 GitHub + Streamlit Cloud，让评委可以在线访问。

---

## 一、准备 GitHub 仓库

### 1.1 创建仓库

1. 登录 https://github.com
2. 点击右上角 `+` → `New repository`
3. 填写：
   - **Repository name**: `quantinsight-pro`（或自定义）
   - **Description**: `AI 驱动的另类数据量化投研平台 - 资管科技赛道参赛 Demo`
   - **Public**（必须公开，Streamlit Cloud 需要）
   - **Add a README file**: ✓
   - **Add .gitignore**: Python
4. 点击 `Create repository`

### 1.2 本地推送代码

```bash
# 进入 streamlit_app 目录
cd D:/AFAC2026金融智能创新大赛/quantinsight-deploy/streamlit_app

# 初始化 git
git init
git add .
git commit -m "feat: QuantInsight Pro Demo v1.0 - 3 modules + public A-share data"

# 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/yourname/quantinsight-pro.git

# 推送到 main 分支
git branch -M main
git push -u origin main
```

如果使用 Personal Access Token (PAT)：
```bash
git remote set-url origin https://<TOKEN>@github.com/yourname/quantinsight-pro.git
git push -u origin main
```

---

## 二、部署到 Streamlit Cloud（推荐）

### 2.1 准备工作

1. 访问 https://share.streamlit.io
2. 使用 GitHub 账号登录
3. 点击 `New app`

### 2.2 配置部署

| 字段 | 填写 |
|------|------|
| **Repository** | 选择 `yourname/quantinsight-pro` |
| **Branch** | `main` |
| **Main file path** | `app.py` |
| **App URL** | 自定义，如 `quantinsight-pro-demo` |

### 2.3 高级设置（可选）

点击 `Advanced settings`：
- **Python version**: 3.11 或 3.12
- **Secrets**: 如有 API key 在此配置（不需要 key 也能跑）

### 2.4 部署

点击 `Deploy!` 后等待 2-5 分钟，部署完成后会得到一个公开 URL：
```
https://quantinsight-pro-demo.streamlit.app
```

### 2.5 部署后验证

1. 访问公开 URL
2. 检查首页加载（应显示 3 大模块概览）
3. 测试 AI 问答：输入"分析新能源"→ 应返回结构化报告
4. 测试回测：选择沪深300 + 双均线 + 2020-01-01 → 点击"运行回测" → 应显示 NAV 曲线

---

## 三、本地运行（开发模式）

```bash
# 1. 克隆仓库
git clone https://github.com/yourname/quantinsight-pro.git
cd quantinsight-pro

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动
streamlit run app.py
```

浏览器自动打开 http://localhost:8501

---

## 四、常见问题

### Q1: akshare 数据加载慢
**原因**：akshare 实时调用东方财富等公开接口，受网络影响。
**解决**：已使用 `@st.cache_data(ttl=3600)` 缓存 1 小时。

### Q2: Streamlit Cloud 部署失败
**检查**：
1. `requirements.txt` 完整
2. `app.py` 路径正确
3. Python 版本 ≥ 3.9
4. Secrets 配置（如果有 API key）

### Q3: AI 问答返回 mock 数据
**原因**：当前版本未配置 LLM API key。
**未来升级**：编辑 `app.py` 中 `ai_qa_mock` 函数，替换为真实 API 调用：
```python
def ai_qa_real(question, api_key):
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content
```

### Q4: 行业数据加载失败
**原因**：akshare 行业 API 不稳定。
**解决**：已在 app.py 中加入 fallback，加载失败时显示申万行业静态信息。

---

## 五、性能与安全

- **数据缓存**：使用 `@st.cache_data` 减少重复请求
- **无敏感数据**：所有数据来自 akshare 公开接口
- **无 API key**：Demo 版本完全免费运行
- **生产部署建议**：
  - 接入真实 LLM API（DeepSeek/Qwen 价格约 ¥0.001/千 token）
  - 添加用户认证（Streamlit 内置 `st.experimental_user`）
  - 部署到私有云（阿里云/AWS）

---

## 六、文件清单

```
quantinsight-pro/
├── app.py                  # Streamlit 主应用（597 行）
├── requirements.txt        # 依赖列表
├── README.md              # 项目说明
├── .streamlit/
│   └── config.toml        # Streamlit 主题配置
└── docs/
    ├── T05_Demo_部署指南.md
    ├── T05_Demo_技术说明.md
    └── screenshots/        # 截图（可选）
```

---

## 七、给评委的访问说明

部署完成后，请把以下信息附在 BP 或路演 PPT 中：

> **Demo 在线访问**：https://quantinsight-pro-demo.streamlit.app
> 
> **测试账号**：无需登录，直接访问
> 
> **推荐测试路径**：
> 1. 进入"AI 投研问答"，输入"分析新能源"查看 AI 报告
> 2. 进入"量化策略回测"，选择"创业板指"+"多因子"+"2020-01-01"运行回测
> 3. 进入"另类数据仪表盘"查看卫星图像/舆情/供应链数据
> 
> **GitHub 仓库**：https://github.com/yourname/quantinsight-pro

---

**部署完成后请把 URL 发给我，我可以帮你做最终验收测试。**
