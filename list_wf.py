import urllib.request, json, os

os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
ph = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10810", "https": "http://127.0.0.1:10810"})
urllib.request.install_opener(urllib.request.build_opener(ph))

t = os.environ.get("GITHUB_TOKEN", "")
r = json.loads(urllib.request.urlopen(urllib.request.Request(
    "https://api.github.com/repos/dijiaozhibei-top/deepseek-batch-register/actions/workflows",
    headers={"Authorization": f"Bearer {t}", "Accept": "application/vnd.github+json"}
)).read())

for wf in r["workflows"]:
    print(f'{wf["id"]}: {wf["name"]} ({wf["path"]}) - {wf["state"]}')
