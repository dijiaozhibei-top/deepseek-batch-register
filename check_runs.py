import urllib.request, json, os, time

os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
ph = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10810", "https": "http://127.0.0.1:10810"})
urllib.request.install_opener(urllib.request.build_opener(ph))

t = os.environ.get("GITHUB_TOKEN", "")
r = json.loads(urllib.request.urlopen(urllib.request.Request(
    "https://api.github.com/repos/dijiaozhibei-top/deepseek-batch-register/actions/runs?per_page=5",
    headers={"Authorization": f"Bearer {t}"}
)).read())

for x in r["workflow_runs"]:
    print(f'{x["head_sha"][:8]} {x["id"]} {x["status"]} {x.get("conclusion","")}')
