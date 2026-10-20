#!/usr/bin/env python3
"""Fetch the numbers behind the character sheet and write tools/stats.json.

With GITHUB_TOKEN (or GH_STATS_TOKEN, a PAT that also counts private
contributions) it asks the GraphQL API. Without a token it falls back to the
public REST API plus the public contribution calendar, which is enough to run
locally. Standard library only, so the workflow needs no pip install.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request

USER = "TheRealNightmare"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats.json")
TOP_LANGS = 6


def _get(url, token=None, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": f"{USER}-profile"})
    if token:
        req.add_header("Authorization", f"bearer {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def streaks(days):
    """(current, longest) from [(date, count)] sorted by date.

    Today not having a contribution yet doesn't break the current streak; the
    day isn't over.
    """
    longest = run = 0
    for _, n in days:
        run = run + 1 if n > 0 else 0
        longest = max(longest, run)
    current = 0
    for i, (d, n) in enumerate(reversed(days)):
        if n > 0:
            current += 1
        elif i == 0:
            continue
        else:
            break
    return current, longest


def lang_share(sizes):
    total = sum(sizes.values()) or 1
    top = sorted(sizes.items(), key=lambda kv: -kv[1])[:TOP_LANGS]
    return [{"name": k, "pct": round(100 * v / total, 1)} for k, v in top]


# --------------------------------------------------------------------------
def via_graphql(token):
    q = """query($login:String!){ user(login:$login){
      createdAt followers{totalCount}
      repositories(ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC, first:100){
        totalCount nodes{ stargazerCount
          languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name } } } } }
      contributionsCollection{ contributionCalendar{ totalContributions
        weeks{ contributionDays{ date contributionCount } } } } } }"""
    body = json.dumps({"query": q, "variables": {"login": USER}}).encode()
    u = json.loads(_get("https://api.github.com/graphql", token, body))["data"]["user"]

    # lifetime total: one contributionsCollection per calendar year since sign-up
    first = int(u["createdAt"][:4])
    years = range(first, dt.date.today().year + 1)
    parts = " ".join(f'y{y}: contributionsCollection(from:"{y}-01-01T00:00:00Z", to:"{y}-12-31T23:59:59Z")'
                     f'{{ contributionCalendar{{ totalContributions }} }}' for y in years)
    body = json.dumps({"query": f'query($login:String!){{ user(login:$login){{ {parts} }} }}',
                       "variables": {"login": USER}}).encode()
    yu = json.loads(_get("https://api.github.com/graphql", token, body))["data"]["user"]
    lifetime = sum(v["contributionCalendar"]["totalContributions"] for v in yu.values())

    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    sizes = {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            sizes[e["node"]["name"]] = sizes.get(e["node"]["name"], 0) + e["size"]
    cur, longest = streaks(days)
    return {
        "contributions_year": cal["totalContributions"],
        "contributions_total": lifetime,
        "streak_current": cur,
        "streak_longest": longest,
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "repos": u["repositories"]["totalCount"],
        "followers": u["followers"]["totalCount"],
        "since": first,
        "languages": lang_share(sizes),
    }


def via_public():
    user = json.loads(_get(f"https://api.github.com/users/{USER}"))
    repos = json.loads(_get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner"))
    repos = [r for r in repos if not r["fork"]]
    sizes = {}
    for r in repos:
        for k, v in json.loads(_get(r["languages_url"])).items():
            sizes[k] = sizes.get(k, 0) + v

    html = _get(f"https://github.com/users/{USER}/contributions")
    dates = dict(re.findall(r'data-date="([\d-]+)" id="([^"]+)"', html))
    counts = {}
    for cid, txt in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        m = re.match(r"\s*(\d+|No) contribution", txt)
        if m:
            counts[cid] = 0 if m.group(1) == "No" else int(m.group(1))
    days = sorted((d, counts.get(cid, 0)) for d, cid in dates.items())
    year = re.search(r"([\d,]+)\s+contributions?\s+in the last year", html)
    cur, longest = streaks(days)
    first = int(user["created_at"][:4])
    return {
        "contributions_year": int(year.group(1).replace(",", "")) if year else sum(n for _, n in days),
        # the public page only shows the last year; the workflow fills in the real lifetime total
        "contributions_total": sum(n for _, n in days),
        "streak_current": cur,
        "streak_longest": longest,
        "stars": sum(r["stargazers_count"] for r in repos),
        "repos": user["public_repos"],
        "followers": user["followers"],
        "since": first,
        "languages": lang_share(sizes),
    }


if __name__ == "__main__":
    token = os.environ.get("GH_STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    stats = via_graphql(token) if token else via_public()
    stats["updated"] = dt.date.today().isoformat()
    with open(OUT, "w") as f:
        json.dump(stats, f, indent=2)
        f.write("\n")
    print(json.dumps(stats, indent=2))
    sys.exit(0)
