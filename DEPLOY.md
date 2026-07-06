# QuantInsight Pro · ECS 部署工作区

> 本地目录：`D:\AFAC2026金融智能创新大赛\quantinsight-deploy\`  
> 仓库：https://github.com/yigenfeng0707-netizen/quantinsight-pro  
> 生产域名：**https://quantinsight.cn/**  
> ECS：**47.76.46.88** · CentOS 7.9

## 目录说明

| 路径 | 用途 |
|------|------|
| `streamlit_app/` | 应用源码（Streamlit） |
| `deploy/` | ECS 部署脚本（nginx / systemd / SSL） |
| `deploy/setup.sh` | 服务器一键部署 |
| `deploy/ssl-acme.sh` | HTTPS 证书申请 |

## 服务器路径

| 路径 | 说明 |
|------|------|
| `/opt/quantinsight/` | 运行目录（streamlit_app 扁平化） |
| `/opt/quantinsight-repo/` | Git 克隆目录 |
| `/opt/miniconda3/` | Python 3.9（CentOS 7 兼容；**已存在则跳过安装**） |

> **Conda 复用原则**：`setup.sh` 会先检测 `/opt/miniconda3` 或 PATH 中的 `conda`，**仅在完全未安装时才下载 Miniconda**。重复执行 `bash deploy/setup.sh` 不会重装 Python 环境。

## 首次部署（SSH）

```bash
ssh root@47.76.46.88
git clone https://github.com/yigenfeng0707-netizen/quantinsight-pro.git /opt/quantinsight-repo
bash /opt/quantinsight-repo/deploy/setup.sh
bash /opt/quantinsight-repo/deploy/ssl-acme.sh   # DNS 生效后
```

## 更新部署

```bash
cd /opt/quantinsight-repo && git pull
bash deploy/setup.sh
```

## 验证

```bash
curl -sk https://quantinsight.cn/_stcore/health
systemctl status quantinsight
```

## DNS

将 `quantinsight.cn` 和 `www.quantinsight.cn` 的 **A 记录** 指向 `47.76.46.88`。

## 本地开发

本机已安装 **Miniconda**（`D:\miniconda3`，Python 3.13）时，**请勿重复安装**，直接使用：

```powershell
cd streamlit_app
conda activate base   # 或你的专用环境名
pip install -r requirements.txt
streamlit run app.py
```

若无 conda，也可用 venv：

```powershell
cd streamlit_app
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
