# QuantInsight Pro - 可运行 Demo

> **AI 驱动的另类数据量化投研平台** ｜ 资管科技赛道
> 项目编号：2026FINTECH-FINT-0093 ｜ 大赛：Fintech@外滩 第一届金融科技国际创新创业大赛

## 🎯 Demo 简介

本 Demo 是 QuantInsight Pro 的**真实可运行原型**，包含 3 大核心模块：

1. **🤖 AI 投研问答** - 自然语言投研分析、报告生成
2. **📡 另类数据仪表盘** - 卫星图像、舆情分析、供应链追踪
3. **📈 量化策略回测** - 双均线/布林带/多因子策略真实回测

## 🚀 快速启动

### 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/yourname/quantinsight-pro.git
cd quantinsight-pro

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动 Demo
streamlit run app.py
```

浏览器自动打开 http://localhost:8501

### Streamlit Cloud 部署

1. Fork 本仓库到你的 GitHub
2. 访问 https://share.streamlit.io
3. 选择本仓库，main file 选择 `app.py`
4. 一键部署，免费

## 📊 数据来源

- **akshare 1.18+** - 开源 A 股数据接口
  - 沪深300 (sh000300)：2002-01 ~ 至今
  - 中证500 (sh000905)：2005-01 ~ 至今
  - 创业板指 (sz399006)：2010-06 ~ 至今
- **东方财富** - 申万行业数据
- **公开舆情** - 股吧、雪球、微博（模拟数据用于演示）

## 🛠️ 技术栈

- **Streamlit 1.28+** - Web 应用框架
- **Plotly 5.17+** - 交互式可视化
- **pandas 2.0+** - 数据处理
- **akshare 1.12+** - 公开数据接口
- **NumPy 1.24+** - 数值计算

## 📁 项目结构

```
quantinsight-pro/
├── app.py                  # Streamlit 主应用
├── requirements.txt        # 依赖列表
├── README.md              # 本文件
├── .streamlit/            # Streamlit 配置
│   └── config.toml
└── data/                  # 缓存数据（运行时生成）
```

## ⚠️ 免责声明

本 Demo 仅供 QuantInsight Pro 参赛项目技术验证使用，不构成任何投资建议。
所有回测结果基于历史公开数据，不代表未来收益。

## 📞 联系方式

- 编制：黄成选（清华软工推免、大模型应用算法工程师）
- 审核：冯亦根（项目主导、浙江省产业教授）
- 商务：薛永再（永字资管总经理）
- 法务：冯思涵（Northwestern JD 2025）

## 📄 License

MIT License - 详见 LICENSE 文件
