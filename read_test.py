import urllib.request, json, os, zipfile, io, sys

sys.stdout.reconfigure(encoding="utf-8")

os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
ph = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10810", "https": "http://127.0.0.1:10810"})
urllib.request.install_opener(urllib.request.build_opener(ph))
t = os.environ.get("GITHUB_TOKEN", "")

run_id = 26071701088

z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(urllib.request.Request(
    f"https://api.github.com/repos/dijiaozhibei-top/deepseek-batch-register/actions/runs/{run_id}/logs",
    headers={"Authorization": f"Bearer {t}"}
)).read()))

for name in z.namelist():
    if "Test sign" in name:
        content = z.read(name).decode("utf-8", errors="replace")
        # Print only ASCII-safe parts (skip binary or encoding errors)
        for line in content.split("\n"):
            # Filter to show only important lines
            if any(kw in line for kw in ["===", "Status", "CLOUDFLARE", "AWS", "Body", "First", "Error", "x-amzn"]):
                print(line[:300])
        break
