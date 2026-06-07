# QuantInsight Pro - Demo视频制作指南

## 📋 已完成的工作

### 1. HyperFrames项目创建 ✅
- 项目位置：`d:\shFintech\quantinsight-demo\`
- 包含完整的视频合成HTML文件

### 2. 视频合成内容 ✅
- **时长**：2分30秒（90秒）
- **分辨率**：1920×1080（1080p）
- **帧率**：30fps

### 3. 视频结构

| 时间段 | 内容 | 字幕 |
|--------|------|------|
| 0:00-0:15 | 开场动画 | 欢迎来到QuantInsight Pro |
| 0:15-0:33 | AI大语言模型功能展示 | AI大语言模型，10秒生成专业投研报告 |
| 0:33-0:51 | 另类数据中心展示 | 独家数据管道，提前捕捉市场信号 |
| 0:51-1:15 | 量化策略平台展示 | 强化学习驱动，自适应策略优化 |
| 1:15-1:30 | 结尾 | 立即体验，开启智能投研新时代 |

---

## 🚀 生成MP4视频步骤

### 前提条件

1. **安装FFmpeg**
   ```bash
   # Windows - 使用Chocolatey
   choco install ffmpeg -y
   
   # 或下载手动安装：https://ffmpeg.org/download.html
   ```

2. **确保FFmpeg在PATH中**
   ```bash
   ffmpeg --version  # 验证安装
   ```

### 渲染命令

```bash
# 进入项目目录
cd d:\shFintech\quantinsight-demo

# 使用hyperframes渲染
hyperframes render -o output.mp4

# 或指定参数
hyperframes render --fps 30 --quality high -o quantinsight_demo.mp4
```

### 预期输出

```
◆  Rendering quantinsight-demo → output.mp4
   30fps · high · auto workers
   GPU: browser GPU (auto-detect)

◇  Browser: launching

◇  Rendering: 100% [████████████████████████] 01:30 / 01:30

◇  Encoding: 100% [████████████████████████]

◆  Done! Output written to output.mp4
```

---

## 🌐 浏览器播放方案

已创建交互式HTML演示页面：
- 文件：`d:\shFintech\QuantInsight_Pro_Demo_Video.html`
- 直接在浏览器中打开即可播放
- 支持播放/暂停、进度拖动、重新开始

### 使用方法

1. 双击打开 `QuantInsight_Pro_Demo_Video.html`
2. 点击▶按钮开始播放
3. 拖动进度条跳转到任意时间点

---

## 📁 项目文件结构

```
quantinsight-demo/
├── index.html          # 视频合成主文件
├── hyperframes.json    # 项目配置
├── meta.json           # 项目元数据
├── package.json        # 依赖配置
└── assets/             # 资源文件夹（如有）
```

---

## ⚙️ 自定义配置

### 修改视频时长

编辑 `index.html` 中的 `data-duration` 属性：
```html
<div id="root" data-composition-id="main" data-duration="90">
```

### 修改分辨率

编辑 `index.html` 中的 `data-width` 和 `data-height`：
```html
<meta name="viewport" content="width=1920, height=1080" />
```

### 修改动画时间线

编辑 `index.html` 中的GSAP动画代码，调整时间参数。

---

## 📝 故障排除

### FFmpeg未找到
```bash
# 确保FFmpeg路径正确
where ffmpeg

# 添加到PATH
set PATH=%PATH%;C:\path\to\ffmpeg\bin
```

### 渲染失败
```bash
# 检查项目配置
hyperframes lint

# 更新hyperframes
hyperframes upgrade
```

---

## 📧 技术支持

如果在渲染过程中遇到问题，请联系技术团队：
- 邮箱：contact@quantinsight.pro
- 官网：www.quantinsight.pro

---

文档生成日期：2026年6月
版本：V1.0