import urllib.request, json, os, zipfile, io, sys, time

os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
proxy_handler = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10810", "https": "http://127.0.0.1:10810"})
opener = urllib.request.build_opener(proxy_handler)
urllib.request.install_opener(opener)

token = os.environ.get("GITHUB_TOKEN", "")
if not token:
    print("GITHUB_TOKEN env var not set")
    sys.exit(1)

# Find latest run for 60f90bf
search = json.loads(urllib.request.urlopen(urllib.request.Request(
    "https://api.github.com/repos/dijiaozhibei-top/deepseek-batch-register/actions/runs?per_page=5",
    headers={"Authorization": f"Bearer {token}"}
)).read())

for run in search["workflow_runs"]:
    if run["head_sha"] == "60f90bf":
        run_id = run["id"]
        print(f"Run ID: {run_id}, Status: {run['status']}")
        
        # Wait for completion
        for _ in range(120):
            r = json.loads(urllib.request.urlopen(urllib.request.Request(
                f"https://api.github.com/repos/dijiaozhibei-top/deepseek-batch-register/actions/runs/{run_id}",
                headers={"Authorization": f"Bearer {token}"}
            )).read())
            if r["status"] == "completed":
                print(f"Conclusion: {r['conclusion']}")
                break
            time.sleep(10)
        
        # Get logs
        z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(urllib.request.Request(
            f"https://api.github.com/repos/dijiaozhibei-top/deepseek-batch-register/actions/runs/{run_id}/logs",
            headers={"Authorization": f"Bearer {token}"}
        )).read()))
        
        for name in z.namelist():
            if "Run batch" in name:
                content = z.read(name).decode("utf-8", errors="replace")
                for line in content.split("\n"):
                    if any(kw in line for kw in ["send-code", "ERROR", "验证码", "跳过", "注册成功", "start"]):
                        print(line)
                break
        break
