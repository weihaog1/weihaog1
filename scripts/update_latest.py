"""Rewrite the git-log block in README.md with the five most recently pushed repos."""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone

USER = "weihaog1"
README = os.path.join(os.path.dirname(__file__), "..", "README.md")
START = "<!-- LATEST:START -->"
END = "<!-- LATEST:END -->"


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def relative(iso):
    then = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - then
    days = delta.days
    if days >= 60:
        return f"{days // 30} months ago"
    if days >= 2:
        return f"{days} days ago"
    hours = delta.seconds // 3600 + days * 24
    if hours >= 2:
        return f"{hours} hours ago"
    return "just now"


def main():
    repos = api(f"/users/{USER}/repos?sort=pushed&per_page=20")
    picked = [r for r in repos if not r["fork"] and r["name"] != USER][:5]

    lines = []
    for repo in picked:
        commits = api(f"/repos/{USER}/{repo['name']}/commits?per_page=1")
        if not commits:
            continue
        sha = commits[0]["sha"][:7]
        message = commits[0]["commit"]["message"].splitlines()[0]
        if len(message) > 60:
            message = message[:57] + "..."
        when = relative(commits[0]["commit"]["committer"]["date"])
        lines.append(f"{sha}  {repo['name']}: {message} ({when})")

    block = f"{START}\n```text\n" + "\n".join(lines) + f"\n```\n{END}"
    with open(README, encoding="utf-8") as f:
        content = f.read()
    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END), block, content, flags=re.S
    )
    if updated != content:
        with open(README, "w", encoding="utf-8") as f:
            f.write(updated)
        print("README updated")
    else:
        print("no changes")


if __name__ == "__main__":
    main()
