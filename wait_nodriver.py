import urllib.request, json, os, time, zipfile, io

os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
ph = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10810", "https": "http://127.0.0.1:10810"})
urllib.request.install_opener(urllib.request.build_opener(ph))

t = os.environ.get("GITHUB_TOKEN", "")

# Find the latest run
search = json.loads(urllib.request.urlopen(urllib.request.Request(
    "https://api.github.com/repos/dijiaozhibei-top/deepseek-batch-register/actions/runs?per_page=5",
    headers={"Authorization": f"Bearer {t}"}
)).read())

run = search["workflow_runs"][0]
run_id = run["id"]
sha = run["head_sha"][:8]
print(f"Run: {run_id}, SHA: {sha}, Status: {run['status']}")

# Wait for completion
for _ in range(120):
    r = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"https://api.github.com/repos/dijiaozhibei-top/deepseek-batch-register/actions/runs/{run_id}",
        headers={"Authorization": f"Bearer {t}"}
    )).read())
    status = r["status"]
    conclusion = r.get("conclusion", "")
    print(f"  {status} {conclusion}")
    if status == "completed":
        break
    time.sleep(15)

# Get logs
z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(urllib.request.Request(
    f"https://api.github.com/repos/dijiaozhibei-top/deepseek-batch-register/actions/runs/{run_id}/logs",
    headers={"Authorization": f"Bearer {t}"}
)).read()))

for name in z.namelist():
    if "Run batch" in name or "Python" in name or "Install" in name:
        content = z.read(name).decode("utf-8", errors="replace")
        lines = content.split("\n")
        error_lines = [l for l in lines if any(kw in l for kw in [
            "send-code", "ERROR", "biz_code", "验证码", "跳过", "注册成功",
            "start", "Turnstile", "WAF", "blocked", "Cloudflare", "Failed"
        ])]
        if error_lines:
            print(f"\n--- {name} ---")
            for l in error_lines[:30]:
                print(l)
