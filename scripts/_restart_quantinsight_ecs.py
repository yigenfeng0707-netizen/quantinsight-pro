"""Restart quantinsight.service on ECS after hotfix."""
from pathlib import Path
import paramiko
import time

ENV = Path(__file__).resolve().parents[1] / "deploy" / "ecs.local.env"
pw = None
for line in ENV.read_text(encoding="utf-8").splitlines():
    if line.startswith("ALIYUN_ECS_PASSWORD="):
        pw = line.split("=", 1)[1].strip()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("47.76.46.88", username="root", password=pw, timeout=30)

def run(cmd: str) -> str:
    stdin, stdout, stderr = client.exec_command(cmd)
    return (stdout.read() + stderr.read()).decode("utf-8", errors="replace").strip()

print(run("systemctl restart quantinsight.service"))
time.sleep(3)
print("active:", run("systemctl is-active quantinsight.service"))
print("health:", run("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8501/_stcore/health"))
print("line69:", run("sed -n '69p' /opt/quantinsight/admin/dashboard.py"))
client.close()
