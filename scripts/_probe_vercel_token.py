import re
import urllib.request

base = "https://ai-governance-gateway-psi.vercel.app"
html = urllib.request.urlopen(f"{base}/approvals").read().decode("utf-8", "replace")
chunks = re.findall(r"/_next/static/[^\"']+\.js", html)
print("js_count", len(chunks))
needles = (
    "dev-admin-token",
    "aigw-admin-7f3k9m2pqx",
    "NEXT_PUBLIC_ADMIN_TOKEN",
    "X-Admin-Token",
    "ca-aigw-gateway",
    "127.0.0.1:8000",
)
found = {n: False for n in needles}
for path in chunks:
    url = base + path
    try:
        body = urllib.request.urlopen(url).read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        print("fail", path, exc)
        continue
    for n in needles:
        if n in body:
            found[n] = True
            print("FOUND", n, "in", path)
print("summary", found)
