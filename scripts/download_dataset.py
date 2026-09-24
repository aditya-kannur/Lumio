"""
Downloads VersionQuery's dataset: 1 OpenAPI reference file,
2 changelog files, and 6 per-version migration/changelog docs.
Organizes them into data/reference, data/changelog, data/migrations.
"""
import os
import urllib.request
import urllib.error

BASE = "https://developers.notion.com"

FILES = {
    "reference": {
        "openapi.json": f"{BASE}/openapi.json",
    },
    "changelog": {
        "changelog.md": f"{BASE}/page/changelog.md",
        "historical-changelog.md": f"{BASE}/guides/resources/historical-changelog.md",
    },
    "migrations": {
        "2021-05-13.md": f"{BASE}/changelog/unversioned-requests-no-longer-accepted.md",
        "2021-08-16.md": f"{BASE}/changelog/notion-version-2021-08-16.md",
        "2022-02-22.md": f"{BASE}/changelog/releasing-notion-version-2022-02-22.md",
        "2022-06-28.md": f"{BASE}/changelog/releasing-notion-version-2022-06-28.md",
        "2025-09-03.md": f"{BASE}/guides/get-started/upgrade-guide-2025-09-03.md",
        "2026-03-11.md": f"{BASE}/guides/get-started/upgrade-guide-2026-03-11.md",
    },
}

def download_all(data_dir="data"):
    results = {"ok": [], "failed": []}
    for folder, files in FILES.items():
        target_dir = os.path.join(data_dir, folder)
        os.makedirs(target_dir, exist_ok=True)
        for filename, url in files.items():
            path = os.path.join(target_dir, filename)
            try:
                urllib.request.urlretrieve(url, path)
                size = os.path.getsize(path)
                if size < 50:  # suspiciously small = probably an error page
                    raise ValueError(f"downloaded file too small ({size} bytes)")
                results["ok"].append(path)
                print(f"OK   {path} ({size} bytes)")
            except (urllib.error.URLError, ValueError) as e:
                results["failed"].append((path, str(e)))
                print(f"FAIL {path}: {e}")
    return results

if __name__ == "__main__":
    results = download_all()
    print(f"\n{len(results['ok'])} succeeded, {len(results['failed'])} failed")
    if results["failed"]:
        exit(1)