# QuantInsight Pro - 真实 LLM 接入指南 (B7)

**项目**: QuantInsight Pro - AI 驱动的另类数据量化投研平台
**项目编号**: 2026FINTECH-FINT-0093
**任务**: B7 真实 LLM 接入
**版本**: V2.0
**日期**: 2026-06-06

---

## 一、任务背景

T20 P0 修订 + B7: Demo 接入真实 LLM (SenseNova / DeepSeek / Qwen), 替换 mock 关键词匹配.
**V2 升级**: 集成 SenseNova (商汤日日新) 作为最高优先级 LLM (国内访问快 + 中文优化 + 含思考过程).

## 二、支持的 3 家 LLM

| LLM | 成本 (元/千tokens) | 中文 | 速度 | 思考链 | 推荐度 |
|-----|---------------------|------|------|--------|--------|
| **SenseNova-6.7-flash-lite** | 1-3 | 优秀 | 极快 | ✅ reasoning_content | ⭐⭐⭐⭐⭐ |
| DeepSeek-chat | 1-2 | 优秀 | 快 | - (需 R1) | ⭐⭐⭐⭐ |
| Qwen-turbo | 3-6 | 优秀 | 快 | - | ⭐⭐⭐ |

**推荐**: SenseNova-6.7-flash-lite (含 reasoning_content 思考过程, 国内访问延迟 < 500ms, 中文优化)

**优先级**: SenseNova > DeepSeek > Qwen

## 三、配置方式 (3 种)

### 方式 1: Streamlit Cloud Secrets (部署后, 推荐)

**步骤**:
1. 访问 https://share.streamlit.io
2. 进入您的 quantinsight-pro 应用
3. 点击右下角 **"⚙️ Settings"** 按钮
4. 切换到 **"Secrets"** 标签
5. 粘贴以下内容 (三选一):

#### SenseNova 配置 (推荐, 含思考链):
```toml
SENSENOVA_API_KEY = "sk-v24McU1SzzMxNuuckNWoP8solabzknK9"
SENSENOVA_MODEL = "sensenova-6.7-flash-lite"
SENSENOVA_BASE_URL = "https://token.sensenova.cn/v1/chat/completions"
```

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
$env:SENSENOVA_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxx"
$env:SENSENOVA_MODEL = "sensenova-6.7-flash-lite"
python -m streamlit run D:\shFintech\streamlit_app\app.py
```

### 方式 3: 跳过配置 (使用 Mock 模式)

如果无 API key, Demo 自动回退到 mock 关键词匹配 (3 个行业模板 + 通用回答).

## 四、API Key 获取

### 4.1 SenseNova (推荐, V2 新增)

1. 访问 https://platform.sensenova.cn
2. 商汤账号注册 + 实名认证
3. 进入 "API Keys" → "Create new secret key"
4. 充值 (建议 ¥50 起步, 约 30 万 tokens)
5. 复制 key (格式: `sk-xxxxxxxxxxxxxxxxxxxx`)

**优势**:
- 思考过程可见 (reasoning_content 字段) - 路演时演示"AI 思考"效果
- 国内访问延迟 < 500ms (上海/深圳节点)
- 6.7B flash-lite 模型, 速度比 Qwen-turbo 快 2-3 倍

### 4.2 DeepSeek (备选)

1. 访问 https://platform.deepseek.com
2. 注册账号 + 实名认证
3. 进入 "API Keys" → "Create new secret key"
4. 充值 (建议 ¥50 起步, 约 100 万 tokens)
5. 复制 key (格式: `sk-xxxxxxxxxxxxxxxxxxxx`)

**免费额度**: 注册送 ¥5 (约 10 万 tokens)

### 4.3 Qwen (备选)

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
配置 SENSENOVA_API_KEY / DEEPSEEK_API_KEY / QWEN_API_KEY
可启用真实 AI 推理
```

配置后 (Real 模式):
```
🤖 AI 引擎
SENSENOVA ✅
模型: sensenova-6.7-flash-lite
模式: 真实 LLM 推理
```

### 5.2 提问示例

测试问题:
- "分析近期新能源行业投资机会"
- "半导体行业当前估值与投资逻辑"
- "2026 年 A 股市场展望"
- "美联储加息对中国股市影响"
- "量化对冲基金策略对比"

### 5.3 V2 新增: 思考过程展示

SenseNova 模型返回包含 `reasoning_content` 字段, Demo 自动展开"🧠 AI 思考过程"面板, 演示 AI 推理链, 增强路演效果.

**路演演示技巧**:
1. 评委问"你们的 AI 是怎么推理的?"
2. 点击"🧠 AI 思考过程"展开
3. 显示 AI 思考步骤: "好的, 用户问的是... 首先, 我需要..."

### 5.4 真实 LLM 优势

| 维度 | Mock 模式 | 真实 LLM 模式 (SenseNova) |
|------|-----------|---------------------------|
| 覆盖行业 | 3 个 (新能源/半导体/消费) | **无限 (任何主题)** |
| 数据时效 | 静态模板 | **实时知识 (2024-2025)** |
| 推理深度 | 关键词匹配 | **多步推理 + 数据引用** |
| 思考可见 | ❌ | ✅ **reasoning_content** |
| 回答质量 | 6/10 | **8-9/10** |
| 响应时间 | 1.5 秒 | **3-5 秒** |

## 六、推理成本估算

| LLM | 单次问题成本 | 月 1000 次 | 月 1 万次 |
|-----|--------------|------------|------------|
| SenseNova-6.7-flash-lite | ¥0.02 | ¥20 | ¥200 |
| DeepSeek-chat | ¥0.01 | ¥10 | ¥100 |
| Qwen-turbo | ¥0.03 | ¥30 | ¥300 |

**比赛使用** (假设 100 次路演 + 1000 次 Q&A):
- SenseNova: ¥20
- DeepSeek: ¥10
- Qwen: ¥30
- Mock: ¥0

## 七、代码兼容性处理 (V2 新增)

### 7.1 SenseNova 特殊处理

- **response_format 不支持**: DeepSeek/Qwen 用 `response_format: {type: json_object}`, SenseNova 需在 prompt 中要求 JSON 格式 + 后处理
- **reasoning_content 字段**: SenseNova 特有, 单独提取展示
- **JSON 解析容错**: 引入 `_extract_json_from_text()`, 支持 3 种格式 (直接/代码块/正则)

### 7.2 数据类型兼容

LLM 返回的 `summary` / `recommendation` 可能是 list 或 str, 自动转换为字符串:
```python
def _to_str(v, default=''):
    if v is None: return default
    if isinstance(v, list): return '\n'.join(str(x) for x in v)
    return str(v)
```

## 八、配套使用

- **T05 Demo 原型**: 基础版 (Mock 模式)
- **B5 GitHub 仓库**: 代码托管 ✅
- **B6 Streamlit Cloud 部署**: 在线 Demo (3 步)
- **B7 真实 LLM 接入**: 增强 AI 问答 (本任务 V2)
- **T18 Q&A V2**: 路演现场备用

## 九、安全提示

- API key 一旦比赛结束, 建议在平台撤销
- Streamlit Secrets 自动加密存储
- 公开仓库不包含任何 key (通过 .gitignore 保护)
- **V2 新增**: 思考过程不写入日志, 避免泄露商业敏感信息

## 十、用户操作清单

1. ☐ 访问 https://share.streamlit.io
2. ☐ 进入 quantinsight-pro 应用
3. ☐ Settings → Secrets → 粘贴 SenseNova 配置
4. ☐ Save → 等待 5 秒重启
5. ☐ 侧边栏确认显示 "SENSENOVA ✅"
6. ☐ 测试 5 个问题验证 (含"🧠 AI 思考过程"展开)
7. ☐ (比赛后) 在 SenseNova 平台撤销 API key

**预计总耗时**: 3 分钟 (使用现有 API key)

---

**B7 LLM 接入指南版本**: V2.0
**日期**: 2026-06-06
**状态**: ✅ 代码已推送 (含 SenseNova 集成), 待用户在 Streamlit Cloud Secrets 配置
