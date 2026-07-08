"""
Shared ECS deploy helper — import from any deploy script.

Usage:
    from scripts.ecs_api import ECSClient

    ecs = ECSClient()
    ecs.status()                              # instance status
    ecs.run("systemctl is-active quantinsight")  # remote command
    ecs.hotfix(r"D:/AFAC2026金融智能创新大赛/quantinsight-deploy/streamlit_app\app.py", "/opt/quantinsight/app.py")
    ecs.deploy_files(["app.py", "ui_themes.py"])
"""
import urllib.request, urllib.parse, hashlib, hmac, base64, time, uuid, json, os, tarfile, io

# ── Config ──────────────────────────────────────────────────────────
# Credentials are read from environment variables to avoid leaking secrets in git.
# Set them before importing, or pass them explicitly to ECSClient().
AK_ID       = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID', '')
AK_SECRET   = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET', '')
REGION      = os.environ.get('ALIBABA_CLOUD_REGION', 'cn-hangzhou')
ENDPOINT    = f'ecs.{REGION}.aliyuncs.com'
INSTANCE_ID = os.environ.get('ECS_INSTANCE_ID', 'i-bp1g3jpaz9v1xczizza8')
LOCAL_BASE  = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'streamlit_app'))
CHUNK_SIZE  = 15000  # base64 chars per chunk (Cloud Assistant ~18KB limit)

class ECSClient:
    """Alibaba Cloud ECS API client using v3 signature (ACS3-HMAC-SHA256)."""

    def api(self, action, params=None):
        """Signed POST to ECS API."""
        now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        nonce = str(uuid.uuid4()).replace('-', '')
        qs = urllib.parse.urlencode(sorted((params or {}).items())) if params else ''
        body_hash = hashlib.sha256(b'').hexdigest()
        hdrs = {
            'host': ENDPOINT, 'x-acs-action': action, 'x-acs-version': '2014-05-26',
            'x-acs-date': now, 'x-acs-signature-nonce': nonce,
            'x-acs-content-sha256': body_hash, 'x-acs-credentials-provider': 'static_ak',
            'accept': 'application/json', 'user-agent': 'ecs-deploy-skill/1.0',
        }
        sorted_h = sorted(hdrs.items(), key=lambda x: x[0])
        canon_h = ''.join(f'{k}:{v}\n' for k, v in sorted_h)
        signed_h = ';'.join(k for k, _ in sorted_h)
        cr = '\n'.join(['POST', '/', qs, canon_h, signed_h, body_hash])
        sts = f'ACS3-HMAC-SHA256\n{hashlib.sha256(cr.encode()).hexdigest()}'
        sig = hmac.new(AK_SECRET.encode(), sts.encode(), hashlib.sha256).hexdigest()
        hdrs['Authorization'] = f'ACS3-HMAC-SHA256 Credential={AK_ID},SignedHeaders={signed_h},Signature={sig}'
        url = f'https://{ENDPOINT}/' + (f'?{qs}' if qs else '')
        req = urllib.request.Request(url, method='POST', data=b'')
        for k, v in hdrs.items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            try: return json.loads(body)
            except: return {'Error': body[:600]}

    def run(self, script, timeout_secs=120, poll_interval=5, verbose=True):
        """Run a shell script on the server via Cloud Assistant. Returns dict."""
        cmd_b64 = base64.b64encode(script.encode()).decode()
        result = self.api('RunCommand', {
            'Type': 'RunShellScript', 'CommandContent': cmd_b64,
            'ContentEncoding': 'Base64', 'InstanceId.1': INSTANCE_ID,
            'RegionId': REGION, 'Timeout': str(timeout_secs),
        })
        if 'InvokeId' not in result:
            print(f"RunCommand failed: {result}")
            return None
        invoke_id = result['InvokeId']
        for i in range(timeout_secs // poll_interval + 10):
            time.sleep(poll_interval)
            desc = self.api('DescribeInvocations', {
                'InvokeId': invoke_id, 'IncludeOutput': 'true', 'RegionId': REGION,
            })
            invocations = desc.get('Invocations', {}).get('Invocation', [])
            if invocations:
                inv = invocations[0]
                status = inv.get('InvokeStatus', '')
                if verbose and i % 4 == 0:
                    print(f"  Poll {i+1}: {status}")
                if status in ('Finished', 'Failed', 'Stopped'):
                    output, exit_code = '', -1
                    for ii in inv.get('InvokeInstances', {}).get('InvokeInstance', []):
                        raw = ii.get('Output', '')
                        if raw:
                            output = base64.b64decode(raw).decode('utf-8', errors='replace')
                        exit_code = ii.get('ExitCode', -1)
                    return {'status': status, 'output': output, 'exit_code': exit_code}
        return {'status': 'Timeout', 'output': '', 'exit_code': -1}

    def upload_chunks(self, b64_data, remote_path='/tmp/deploy_b64.txt'):
        """Upload base64 string to server in 15KB chunks."""
        chunks = [b64_data[i:i+CHUNK_SIZE] for i in range(0, len(b64_data), CHUNK_SIZE)]
        print(f"  Uploading {len(chunks)} chunks ({len(b64_data)} chars)...")
        for idx, chunk in enumerate(chunks):
            op = '>' if idx == 0 else '>>'
            r = self.run(f'echo -n "{chunk}" {op} {remote_path}', 30, verbose=False)
            if not r or r['exit_code'] != 0:
                print(f"  FAILED chunk {idx+1}: {r}")
                return False
            print(f"  Chunk {idx+1}/{len(chunks)} OK")
        return True

    def status(self):
        """Print instance status and health check."""
        print("=== ECS Status ===")
        r = self.api('DescribeInstances', {'PageSize': '10', 'RegionId': REGION})
        instances = r.get('Instances', {}).get('Instance', [])
        if not instances:
            print("No instances found!"); return
        inst = instances[0]
        ip_list = inst.get('PublicIpAddress', {}).get('IpAddress', [])
        eip = inst.get('EipAddress', {}).get('IpAddress', '')
        ip = ip_list[0] if ip_list else (eip or '?')
        print(f"  Instance: {inst['InstanceId']}")
        print(f"  IP: {ip}  Status: {inst['Status']}")
        print("\n=== Service Health ===")
        r = self.run("systemctl is-active quantinsight; curl -sk -o /dev/null -w 'HTTP %{http_code}' https://localhost:8443/")
        if r: print(f"  {r['output'].strip()}")

    def hotfix(self, local_path, remote_path):
        """Deploy a single file to the server."""
        print(f"Hotfix: {os.path.basename(local_path)} → {remote_path}")
        with open(local_path, 'rb') as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        print(f"  {len(data)} bytes, {len(b64)} base64 chars")
        if not self.upload_chunks(b64, '/tmp/hotfix_b64.txt'):
            return
        fname = os.path.basename(remote_path)
        r = self.run(f"""#!/bin/bash
set -e
base64 -d /tmp/hotfix_b64.txt > /tmp/hotfix_new
cp {remote_path} {remote_path}.bak.$(date +%H%M%S) 2>/dev/null || true
cp /tmp/hotfix_new {remote_path}
rm -f /tmp/hotfix_b64.txt /tmp/hotfix_new
python3 -c "import py_compile; py_compile.compile('{remote_path}')" 2>&1 && echo "Syntax OK" || echo "SYNTAX ERROR"
systemctl restart quantinsight
sleep 4
echo "Status: $(systemctl is-active quantinsight)"
echo "Health: $(curl -sk -o /dev/null -w '%{{http_code}}' https://localhost:8443/)"
wc -c < {remote_path}
""", 120)
        if r: print(r['output'])

    def deploy_files(self, file_list):
        """Deploy multiple files via tar.gz + base64 transfer."""
        print(f"Deploying {len(file_list)} files...")
        local_base = os.path.normpath(LOCAL_BASE)
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w:gz') as tar:
            for rel in file_list:
                lp = os.path.join(local_base, rel.replace('/', os.sep))
                if os.path.exists(lp):
                    tar.add(lp, arcname=rel)
                    print(f"  + {rel} ({os.path.getsize(lp)} bytes)")
                else:
                    print(f"  ! MISSING: {rel}")
        b64 = base64.b64encode(buf.getvalue()).decode()
        print(f"  Archive base64: {len(b64)} chars")
        if not self.upload_chunks(b64, '/tmp/deploy_b64.txt'):
            return
        # Build copy commands dynamically
        dirs = set()
        copies = []
        for rel in file_list:
            parts = rel.split('/')
            if len(parts) > 1:
                dirs.add(f"/opt/quantinsight/{parts[0]}")
            copies.append(f"cp -f /tmp/deploy_extract/{rel} /opt/quantinsight/{rel}")
        mkdir_cmds = '\n'.join(f'mkdir -p {d}' for d in sorted(dirs))
        copy_cmds = '\n'.join(copies)
        r = self.run(f"""#!/bin/bash
set -e
base64 -d /tmp/deploy_b64.txt > /tmp/deploy.tar.gz
rm -f /tmp/deploy_b64.txt
mkdir -p /tmp/deploy_extract
cd /tmp/deploy_extract && tar xzf /tmp/deploy.tar.gz
rm -f /tmp/deploy.tar.gz
{mkdir_cmds}
# Backup originals
for f in app.py ui_themes.py error_handling.py requirements.txt; do
    [ -f /opt/quantinsight/$f ] && cp /opt/quantinsight/$f /opt/quantinsight/$f.bak.$(date +%H%M%S) 2>/dev/null || true
done
{copy_cmds}
rm -rf /tmp/deploy_extract
systemctl restart quantinsight
sleep 4
echo "Status: $(systemctl is-active quantinsight)"
echo "Health: $(curl -sk -o /dev/null -w '%{{http_code}}' https://localhost:8443/)"
""", 300)
        if r: print(r['output'])
