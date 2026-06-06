# QuantInsight Pro - Streamlit Cloud 部署指南 (B6)

**项目**: QuantInsight Pro - AI 驱动的另类数据量化投研平台
**项目编号**: 2026FINTECH-FINT-0093
**任务**: B6 Streamlit Cloud 部署
**版本**: V1.0
**日期**: 2026-06-06

---

## 一、部署前置条件 (已完成 ✅)

| 条件 | 状态 |
|------|------|
| GitHub 仓库已就绪 | ✅ https://github.com/yigenfeng0707-netizen/quantinsight-pro |
| streamlit_app/ 已推送 | ✅ 8 文件 |
| app.py 语法正确 | ✅ 545 行 |
| requirements.txt 完整 | ✅ 7 依赖 |
| 本地启动测试 | ✅ 健康检查 200 OK |
| .streamlit/config.toml | ✅ |

## 二、Streamlit Cloud 部署步骤 (用户操作 3 分钟)

### Step 1: 登录 Streamlit Cloud (30 秒)

1. 打开浏览器, 访问: **https://share.streamlit.io**
2. 点击 **"Continue with GitHub"** 按钮
3. 授权 Streamlit Cloud 访问 GitHub
4. 登录后, 进入 Workspace

### Step 2: 创建新应用 (60 秒)

1. 点击右上角 **"Create app"** 按钮
2. 填写部署表单:
   - **Repository**: `yigenfeng0707-netizen/quantinsight-pro`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app/app.py`
   - **App URL** (可选自定义): `quantinsight-pro-demo` (最终 URL: `https://quantinsight-pro-demo.streamlit.app`)
3. 点击 **"Deploy!"** 按钮

### Step 3: 等待部署完成 (2-3 分钟)

1. Streamlit Cloud 自动:
   - 拉取 GitHub 仓库
   - 安装 requirements.txt 依赖
   - 启动 app.py
   - 分配 URL
2. 等待日志显示: `Your app is live at: https://quantinsight-pro-demo.streamlit.app`
3. 点击 URL 访问 Demo

## 三、部署后验证清单

- [ ] 访问 https://quantinsight-pro-demo.streamlit.app
- [ ] 4 个标签页正常显示 (项目概览/AI 智能问答/财务模型/回测业绩)
- [ ] AI 智能问答可输入问题 (mock 模式)
- [ ] 财务模型图表正常显示
- [ ] 回测业绩图表正常显示
- [ ] 移动端响应式 (可选)

## 四、配置 (可选)

### 4.1 Secrets (用于 B7 真实 LLM API)

Streamlit Cloud → App settings → Secrets:

```toml
# .streamlit/secrets.toml
DEEPSEEK_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxx"
QWEN_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxx"
```

### 4.2 自定义域名 (可选)

Streamlit Cloud 支持自定义子域: `quantinsight-pro-demo.streamlit.app`

### 4.3 资源限制 (免费版)

- 内存: 1 GB
- CPU: 0.78 核
- 带宽: 无限制
- 休眠: 7 天无访问后休眠 (再次访问自动唤醒)

## 五、故障排除

### 5.1 部署失败 (ModuleNotFoundError)

**原因**: requirements.txt 缺少依赖
**解决**: 在 streamlit_app/requirements.txt 添加缺失依赖, 提交后自动重部署

### 5.2 部署失败 (FileNotFoundError)

**原因**: 主文件路径错误
**解决**: 确认 `streamlit_app/app.py` 路径正确

### 5.3 启动慢 (1-3 分钟)

**原因**: 首次部署需要安装依赖
**解决**: 等待 2-3 分钟, 后续访问秒开

### 5.4 休眠唤醒

**原因**: 7 天无访问
**解决**: 访问 URL 即可唤醒, 30 秒后可用

## 六、URL 汇总

| 类型 | URL |
|------|-----|
| GitHub 仓库 | https://github.com/yigenfeng0707-netizen/quantinsight-pro |
| Streamlit Demo (待部署) | https://quantinsight-pro-demo.streamlit.app |
| 项目主页 | https://github.com/yigenfeng0707-netizen/quantinsight-pro#readme |

## 七、配套使用

- **T05 Demo 原型**: 本地演示
- **T06 3 分钟 Demo 视频**: 路演主用
- **T07-T10 客户证据**: 离线参考
- **B5 GitHub 推送**: 代码托管 ✅
- **B6 Streamlit Cloud 部署**: 在线 Demo (本任务)
- **B7 真实 LLM 接入**: AI 智能问答增强 (待 API key)

## 八、用户操作清单

请按以下顺序操作:

1. ☐ 打开 https://share.streamlit.io
2. ☐ GitHub 账号登录
3. ☐ 创建新应用
4. ☐ 填入仓库信息 (见 Step 2)
5. ☐ 等待部署完成 (2-3 分钟)
6. ☐ 验证 4 个标签页
7. ☐ (可选) 配置 Secrets 用于 B7

预计总耗时: **3-5 分钟**

---

**B6 部署指南版本**: V1.0
**日期**: 2026-06-06
**状态**: ✅ 准备就绪, 等待用户登录 share.streamlit.io 完成最后 3 步
