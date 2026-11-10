#!/usr/bin/env python3
"""Fetch the public contribution calendars for Aazim's GitHub accounts and
merge them into data/contributions.json.

Source: https://github.com/users/<username>/contributions — the same public
calendar GitHub renders on a profile page. No auth, no token.
Usernames come from PROFILE_USERNAMES (comma separated) or argv.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "contributions.json")


def fetch_user(username: str) -> dict:
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (profile-card-renderer)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")
    tds = re.findall(
        r'data-date="(\d{4}-\d{2}-\d{2})" id="(contribution-day-component-[\d-]+)" data-level="(\d)"',
        html,
    )
    tips = dict(
        re.findall(
            r'<tool-tip[^>]*for="(contribution-day-component-[\d-]+)"[^>]*>([^<]+)</tool-tip>',
            html,
        )
    )
    days = {}
    for d, cid, _lvl in tds:
        m = re.match(r"(No|\d+) contribution", tips.get(cid, "").strip())
        days[d] = 0 if (not m or m.group(1) == "No") else int(m.group(1))
    if not days:
        raise RuntimeError(f"No contribution days parsed for {username} — GitHub markup changed?")
    return days


def main() -> None:
    env = os.environ.get("PROFILE_USERNAMES", "")
    users = [u.strip() for u in (sys.argv[1:] or env.split(",")) if u.strip()]
    if not users:
        users = ["aazimameen1-dotcom", "aazimameen1122"]
    merged: dict[str, int] = {}
    per_user = {}
    repos_total = 0
    for u in users:
        days = fetch_user(u)
        try:
            req = urllib.request.Request(
                f"https://api.github.com/users/{u}",
                headers={"User-Agent": "profile-card-renderer"},
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                repos_total += int(json.load(r).get("public_repos", 0))
        except Exception as e:  # repo count is a tile stat, never block the render
            print(f"warn: public_repos lookup failed for {u}: {e}")
        per_user[u] = {"total": sum(days.values()), "days": days}
        for d, c in days.items():
            merged[d] = merged.get(d, 0) + c
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(
            {"generated_at": date.today().isoformat(), "usernames": users,
             "public_repos_total": repos_total,
             "per_user": per_user, "days": merged},
            f, indent=1, sort_keys=True,
        )
    print(f"Wrote {OUT}: {sum(merged.values())} contributions across {len(users)} account(s)")


if __name__ == "__main__":
    main()
