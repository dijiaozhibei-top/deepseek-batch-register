import urllib.request, json, os, zipfile, io

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
        out_path = r"D:\Windows-Users\Documents\Python\deepseek-batch-register\gha_test_result.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Saved to {out_path} ({len(content)} chars)")
        break
