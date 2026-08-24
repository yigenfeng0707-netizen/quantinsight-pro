"""Deploy registration rate-limit fix to ECS and clear blocked attempts."""
from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "deploy" / "ecs.local.env"
HOST = "47.76.46.88"
USER = "root"

LOCAL_FILES = {
    ROOT / "streamlit_app" / "auth" / "pages.py": "/opt/quantinsight/auth/pages.py",
    ROOT / "streamlit_app" / "auth" / "database.py": "/opt/quantinsight/auth/database.py",
}


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
        return (stdout.read() + stderr.read()).decode("utf-8", errors="replace").strip()

    # Find DB path
    print("=== DB LOCATE ===")
    print(run("find /opt/quantinsight -name '*.db' 2>/dev/null; ls -la /opt/quantinsight/*.db /opt/quantinsight/data/*.db 2>/dev/null || true"))

    sftp = client.open_sftp()
    for local, remote in LOCAL_FILES.items():
        print(f"upload {local.name} -> {remote}")
        sftp.put(str(local), remote)
    sftp.close()

    print("=== CLEAR RATE LIMIT ===")
    # Clear shared placeholder IP and show counts; try common db paths
    clear_sql = r"""
import sqlite3, glob, os
candidates = []
for pat in ['/opt/quantinsight/*.db', '/opt/quantinsight/data/*.db', '/opt/quantinsight/**/*.db']:
    candidates.extend(glob.glob(pat, recursive=True))
# also search
for root, dirs, files in os.walk('/opt/quantinsight'):
    for f in files:
        if f.endswith('.db'):
            candidates.append(os.path.join(root, f))
seen = set()
for db in candidates:
    if db in seen:
        continue
    seen.add(db)
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if 'registration_attempts' not in tables:
            conn.close()
            continue
        before = cur.execute('SELECT COUNT(*) FROM registration_attempts').fetchone()[0]
        by_ip = cur.execute('SELECT ip_address, COUNT(*) FROM registration_attempts GROUP BY ip_address').fetchall()
        cur.execute('DELETE FROM registration_attempts')
        conn.commit()
        after = cur.execute('SELECT COUNT(*) FROM registration_attempts').fetchone()[0]
        print(f'DB={db} before={before} after={after} by_ip={by_ip}')
        conn.close()
    except Exception as e:
        print(f'skip {db}: {e}')
"""
    sftp = client.open_sftp()
    with sftp.file("/tmp/_clear_reg_rate.py", "w") as f:
        f.write(clear_sql)
    sftp.close()
    print(run("python3 /tmp/_clear_reg_rate.py"))

    print("=== VERIFY SNIPPETS ===")
    print(run("grep -n 'client_ip\\|max_per_day\\|0.0.0.0\\|reg_client_id' /opt/quantinsight/auth/pages.py /opt/quantinsight/auth/database.py | head -40"))

    print("=== RESTART ===")
    print(run("systemctl restart quantinsight.service"))
    time.sleep(3)
    print("active:", run("systemctl is-active quantinsight.service"))
    print("health:", run("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8501/_stcore/health"))
    client.close()


if __name__ == "__main__":
    main()
