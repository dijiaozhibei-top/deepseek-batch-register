import urllib.request, json, os, zipfile, io

os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
proxy_handler = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10810", "https": "http://127.0.0.1:10810"})
opener = urllib.request.build_opener(proxy_handler)
urllib.request.install_opener(opener)

token = os.environ.get("GITHUB_TOKEN", "")
owner = "dijiaozhibei-top"
repo = "deepseek-batch-register"
run_id = 26070547840

req = urllib.request.Request(
    f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/logs",
    headers={"Authorization": f"Bearer {token}"}
)
z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req).read()))

for name in z.namelist():
    if "Run batch" in name:
        content = z.read(name).decode("utf-8", errors="replace")
        for line in content.split("\n"):
            if "send-code" in line or "ERROR" in line or "验证码" in line or "跳过" in line:
                print(line)
        break
