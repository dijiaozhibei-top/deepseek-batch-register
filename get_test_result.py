import urllib.request, json, os, time, zipfile, io

os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
ph = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10810", "https": "http://127.0.0.1:10810"})
urllib.request.install_opener(urllib.request.build_opener(ph))
t = os.environ.get("GITHUB_TOKEN", "")

# Find the test run
search = json.loads(urllib.request.urlopen(urllib.request.Request(
    "https://api.github.com/repos/dijiaozhibei-top/deepseek-batch-register/actions/runs?per_page=10",
    headers={"Authorization": f"Bearer {t}"}
)).read())

for run in search["workflow_runs"]:
    if run["name"] == "Test GHA access to sign_up":
        run_id = run["id"]
        print(f"Run: {run_id}, Status: {run['status']}, SHA: {run['head_sha'][:8]}")
        
        for _ in range(60):
            r = json.loads(urllib.request.urlopen(urllib.request.Request(
                f"https://api.github.com/repos/dijiaozhibei-top/deepseek-batch-register/actions/runs/{run_id}",
                headers={"Authorization": f"Bearer {t}"}
            )).read())
            if r["status"] == "completed":
                print(f"Conclusion: {r.get('conclusion', '')}")
                
                z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(urllib.request.Request(
                    f"https://api.github.com/repos/dijiaozhibei-top/deepseek-batch-register/actions/runs/{run_id}/logs",
                    headers={"Authorization": f"Bearer {t}"}
                )).read()))
                
                for name in z.namelist():
                    if "Test sign" in name or "Test" in name:
                        print(f"\n--- {name} ---")
                        content = z.read(name).decode("utf-8", errors="replace")
                        print(content[:3000])
                        break
                break
            time.sleep(10)
        break
