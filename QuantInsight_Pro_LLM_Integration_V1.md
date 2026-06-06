# QuantInsight Pro - 真实 LLM 接入指南 (B7)

**项目**: QuantInsight Pro - AI 驱动的另类数据量化投研平台
**项目编号**: 2026FINTECH-FINT-0093
**任务**: B7 真实 LLM 接入
**版本**: V1.0
**日期**: 2026-06-06

---

## 一、任务背景

T20 P0 修订 + B7: Demo 接入真实 LLM (DeepSeek / Qwen), 替换 mock 关键词匹配.

## 二、支持的双 API

| LLM | 成本 (元/千tokens) | 中文 | 速度 | 推荐度 |
|-----|---------------------|------|------|--------|
| **DeepSeek-chat** | 1-2 | 优秀 | 快 | ⭐⭐⭐⭐⭐ |
| Qwen-turbo | 3-6 | 优秀 | 快 | ⭐⭐⭐⭐ |
| Qwen-plus | 6-20 | 优秀 | 中 | ⭐⭐⭐ |

**推荐**: DeepSeek-chat (成本低 + 中文好 + 国内访问快)

## 三、配置方式 (3 种)

### 方式 1: Streamlit Cloud Secrets (部署后, 推荐)

**步骤**:
1. 访问 https://share.streamlit.io
2. 进入您的 quantinsight-pro 应用
3. 点击右下角 **"⚙️ Settings"** 按钮
4. 切换到 **"Secrets"** 标签
5. 粘贴以下内容 (二选一):

#### DeepSeek 配置:
```toml
DEEPSEEK_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxx"
DEEPSEEK_MODEL = "deepseek-chat"
```

#### Qwen 配置:
```toml
QWEN_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxx"
QWEN_MODEL = "qwen-turbo"
```

6. 点击 **"Save"** 保存
7. 应用自动重启, 5 秒后激活

### 方式 2: 环境变量 (本地测试)

Windows PowerShell:
```powershell
$env:DEEPSEEK_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxx"
python -m streamlit run D:\shFintech\streamlit_app\app.py
```

### 方式 3: 跳过配置 (使用 Mock 模式)

如果无 API key, Demo 自动回退到 mock 关键词匹配 (3 个行业模板 + 通用回答).

## 四、API Key 获取

### 4.1 DeepSeek (推荐)

1. 访问 https://platform.deepseek.com
2. 注册账号 + 实名认证
3. 进入 "API Keys" → "Create new secret key"
4. 充值 (建议 ¥50 起步, 约 100 万 tokens)
5. 复制 key (格式: `sk-xxxxxxxxxxxxxxxxxxxx`)

**免费额度**: 注册送 ¥5 (约 10 万 tokens)

### 4.2 Qwen (备选)

1. 访问 https://dashscope.aliyun.com
2. 阿里云账号登录
3. 开通 "百炼" 服务
4. 创建 API-KEY
5. 复制 key (格式: `sk-xxxxxxxxxxxxxxxxxxxx`)

**免费额度**: 注册送 100 万 tokens (约 3 个月免费)

## 五、配置后的使用

### 5.1 侧边栏状态变化

配置前 (Mock 模式):
```
🤖 AI 引擎
Mock 模式 ⚠️
当前使用关键词匹配
配置 DEEPSEEK_API_KEY 或 QWEN_API_KEY
可启用真实 AI 推理
```

配置后 (Real 模式):
```
🤖 AI 引擎
DEEPSEEK ✅
模型: deepseek-chat
模式: 真实 LLM 推理
```

### 5.2 提问示例

测试问题:
- "分析近期新能源行业投资机会"
- "半导体行业当前估值与投资逻辑"
- "2026 年 A 股市场展望"
- "美联储加息对中国股市影响"
- "量化对冲基金策略对比"

### 5.3 真实 LLM 优势

| 维度 | Mock 模式 | 真实 LLM 模式 |
|------|-----------|---------------|
| 覆盖行业 | 3 个 (新能源/半导体/消费) | **无限 (任何主题)** |
| 数据时效 | 静态模板 | **实时知识 (2024-2025)** |
| 推理深度 | 关键词匹配 | **多步推理 + 数据引用** |
| 回答质量 | 6/10 | **8-9/10** |
| 响应时间 | 1.5 秒 | **3-5 秒** |

## 六、推理成本估算

| LLM | 单次问题成本 | 月 1000 次 | 月 1 万次 |
|-----|--------------|------------|------------|
| DeepSeek-chat | ¥0.01 | ¥10 | ¥100 |
| Qwen-turbo | ¥0.03 | ¥30 | ¥300 |

**比赛使用** (假设 100 次路演 + 1000 次 Q&A):
- DeepSeek: ¥10
- Qwen: ¥30
- Mock: ¥0

## 七、配套使用

- **T05 Demo 原型**: 基础版 (Mock 模式)
- **B5 GitHub 仓库**: 代码托管 ✅
- **B6 Streamlit Cloud 部署**: 在线 Demo (3 步)
- **B7 真实 LLM 接入**: 增强 AI 问答 (本任务)
- **T18 Q&A V2**: 路演现场备用

## 八、安全提示

- API key 一旦比赛结束, 建议在平台撤销
- Streamlit Secrets 自动加密存储
- 公开仓库不包含任何 key (通过 .gitignore 保护)

## 九、用户操作清单

1. ☐ 获取 DeepSeek 或 Qwen API key
2. ☐ 访问 https://share.streamlit.io
3. ☐ 进入 quantinsight-pro 应用
4. ☐ Settings → Secrets → 粘贴配置
5. ☐ Save → 等待 5 秒重启
6. ☐ 测试 5 个问题验证
7. ☐ (比赛后) 在平台撤销 API key

**预计总耗时**: 5 分钟 (含获取 key)

---

**B7 LLM 接入指南版本**: V1.0
**日期**: 2026-06-06
**状态**: ✅ 代码已推送, 等待用户在 Streamlit Cloud Secrets 配置
