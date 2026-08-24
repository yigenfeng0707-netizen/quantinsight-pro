"""One-shot: fix datetime.now().normalize() on ECS admin/dashboard.py"""
from pathlib import Path
import paramiko

HOST = "47.76.46.88"
USER = "root"
ENV = Path(__file__).resolve().parents[1] / "deploy" / "ecs.local.env"
REMOTE = "/opt/quantinsight/admin/dashboard.py"


def load_password() -> str:
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if line.startswith("ALIYUN_ECS_PASSWORD="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f"password not found in {ENV}")


def main() -> None:
    pw = load_password()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=pw, timeout=30)

    def run(cmd: str) -> str:
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        return (out + err).strip()

    print("=== BEFORE ===")
    print(run(f"grep -n 'normalize\\|datetime.now\\|Timestamp.now\\|from datetime' {REMOTE}"))

    fix_py = r"""
from pathlib import Path
p = Path('/opt/quantinsight/admin/dashboard.py')
text = p.read_text(encoding='utf-8')
old = 'datetime.now().normalize()'
new = 'pd.Timestamp.now().normalize()'
if old not in text:
    if new in text:
        print('ALREADY_FIXED')
    else:
        print('PATTERN_NOT_FOUND')
        for i, line in enumerate(text.splitlines(), 1):
            if 'date_range' in line or 'normalize' in line:
                print(f'{i}: {line}')
else:
    text2 = text.replace(old, new)
    # drop unused import if datetime no longer referenced
    rest = text2.replace('from datetime import datetime\n', '', 1)
    if 'datetime.' not in rest and 'datetime(' not in rest:
        text2 = rest
    p.write_text(text2, encoding='utf-8')
    print('FIXED_OK')
"""
    # write fix script remotely then execute
    sftp = client.open_sftp()
    with sftp.file("/tmp/_fix_normalize.py", "w") as f:
        f.write(fix_py)
    sftp.close()
    print("=== FIX ===")
    print(run("python3 /tmp/_fix_normalize.py"))

    print("=== AFTER ===")
    print(run(f"grep -n 'normalize\\|datetime.now\\|Timestamp.now\\|from datetime' {REMOTE}"))

    print("=== SERVICE ===")
    print(run("systemctl list-units --type=service --all 2>/dev/null | grep -iE 'quant|streamlit' || true"))
    print(run("ls /etc/systemd/system/*quant* /etc/systemd/system/*streamlit* 2>/dev/null || true"))
    print(run("supervisorctl status 2>/dev/null || true"))
    print(run("ps aux | grep -i '[s]treamlit' || true"))
    print(run("which systemctl; cat /etc/systemd/system/quantinsight.service 2>/dev/null | head -40 || true"))

    client.close()


if __name__ == "__main__":
    main()
