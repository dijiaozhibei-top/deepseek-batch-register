import urllib.request, json, os, zipfile, io

os.environ["HTTP_PROXY"] = "http://127.0.0.1:10810"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10810"
ph = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10810", "https": "http://127.0.0.1:10810"})
urllib.request.install_opener(urllib.request.build_opener(ph))

t = os.environ.get("GITHUB_TOKEN", "")
run_id = 26071207347

z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(urllib.request.Request(
    f"https://api.github.com/repos/dijiaozhibei-top/deepseek-batch-register/actions/runs/{run_id}/logs",
    headers={"Authorization": f"Bearer {t}"}
)).read()))

for name in z.namelist():
    content = z.read(name).decode("utf-8", errors="replace")
    lines = content.split("\n")
    # Get first 10 and last 10 lines
    relevant = [l for l in lines if any(kw in l.lower() for kw in [
        "chrome", "error", "failed", "installing", "browser", "path", "which", "found"
    ])]
    if relevant:
        print(f"\n--- {name} ---")
        for l in relevant[:20]:
            print(l)
    else:
        # Print all if it's short
        if len(lines) < 30:
            print(f"\n--- {name} ---")
            for l in lines[:20]:
                print(l)
