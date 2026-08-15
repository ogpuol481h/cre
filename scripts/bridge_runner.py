#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys, urllib.request

ROOT = pathlib.Path.cwd()
OUT = ROOT / "bridge-output"
OUT.mkdir(exist_ok=True)


def write_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def http_get(job):
    url = job["url"]
    max_bytes = int(job.get("max_bytes", 1048576))
    req = urllib.request.Request(url, headers={"User-Agent": "vm-bridge/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise RuntimeError("response exceeds max_bytes")
        (OUT / "response.bin").write_bytes(data)
        write_json("result.json", {"ok": True, "status": r.status, "url": r.geturl(), "headers": dict(r.headers), "bytes": len(data)})


def download(job):
    url = job["url"]
    filename = pathlib.Path(job.get("filename") or pathlib.PurePosixPath(url.split("?",1)[0]).name or "download.bin").name
    max_bytes = int(job.get("max_bytes", 536870912))
    req = urllib.request.Request(url, headers={"User-Agent": "vm-bridge/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        total = 0
        target = OUT / filename
        with target.open("wb") as f:
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise RuntimeError("download exceeds max_bytes")
                f.write(chunk)
    write_json("result.json", {"ok": True, "file": filename, "bytes": total})


def npm_pack(job):
    package = job["package"]
    subprocess.run(["npm", "pack", package, "--pack-destination", str(OUT)], check=True)
    write_json("result.json", {"ok": True, "package": package})


def pip_download(job):
    packages = job.get("packages") or [job["package"]]
    cmd = [sys.executable, "-m", "pip", "download", "--dest", str(OUT)] + list(packages)
    subprocess.run(cmd, check=True)
    write_json("result.json", {"ok": True, "packages": packages})


def deepseek_chat(job):
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY secret is not configured")
    base_url = job.get("base_url", "https://api.deepseek.com")
    payload = {
        "model": job.get("model", "deepseek-chat"),
        "messages": job["messages"],
        "stream": False,
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=body, method="POST", headers={
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "User-Agent": "vm-bridge/1.0",
    })
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read(20 * 1024 * 1024)
    (OUT / "deepseek-response.json").write_bytes(data)
    write_json("result.json", {"ok": True, "bytes": len(data)})


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: bridge_runner.py JOB.json")
    p = pathlib.Path(sys.argv[1])
    job = json.loads(p.read_text(encoding="utf-8"))
    kind = job.get("type")
    funcs = {
        "http_get": http_get,
        "download": download,
        "npm_pack": npm_pack,
        "pip_download": pip_download,
        "deepseek_chat": deepseek_chat,
    }
    if kind not in funcs:
        raise RuntimeError(f"unsupported job type: {kind!r}")
    funcs[kind](job)

if __name__ == "__main__":
    main()
