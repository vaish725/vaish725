"""
Regenerates the 'Programming Languages' badge section of README.md
based on real language usage across all public GitHub repositories.

Requires: pip install requests
Env vars used (set automatically by the GitHub Action):
  GITHUB_TOKEN     - auth token (higher API rate limit + read access)
  GITHUB_USERNAME  - your GitHub username
"""

import os
import re
import sys
import requests

USERNAME = os.environ.get("GITHUB_USERNAME", "vaish725")
TOKEN = os.environ.get("GITHUB_TOKEN")
README_PATH = "README.md"
TOP_N = 10                     # max number of language badges to show
INCLUDE_FORKS = False          # set True to count forked repos too

# languages to ignore even if detected (markup/config noise, not "skills")
EXCLUDE = {"Makefile", "CMake", "Dockerfile", "Batchfile", "PowerShell"}

# language -> (hex color, shields.io logo slug, logo color)
BADGE_STYLE = {
    "Python": ("3776AB", "python", "white"),
    "JavaScript": ("F7DF1E", "javascript", "black"),
    "TypeScript": ("3178C6", "typescript", "white"),
    "Java": ("ED8B00", "openjdk", "white"),
    "C++": ("00599C", "cplusplus", "white"),
    "C": ("A8B9CC", "c", "black"),
    "C#": ("239120", "csharp", "white"),
    "HTML": ("E34F26", "html5", "white"),
    "CSS": ("1572B6", "css3", "white"),
    "Swift": ("FA7343", "swift", "white"),
    "Go": ("00ADD8", "go", "white"),
    "Rust": ("000000", "rust", "white"),
    "Ruby": ("CC342D", "ruby", "white"),
    "PHP": ("777BB4", "php", "white"),
    "Kotlin": ("7F52FF", "kotlin", "white"),
    "Shell": ("4EAA25", "gnubash", "white"),
    "Jupyter Notebook": ("F37626", "jupyter", "white"),
    "SQL": ("4479A1", "mysql", "white"),
    "R": ("276DC3", "r", "white"),
    "Dart": ("0175C2", "dart", "white"),
    "Vue": ("4FC08D", "vuedotjs", "white"),
}

session = requests.Session()
if TOKEN:
    session.headers["Authorization"] = f"Bearer {TOKEN}"
session.headers["Accept"] = "application/vnd.github+json"


def get_repos():
    repos, page = [], 1
    while True:
        r = session.get(
            f"https://api.github.com/users/{USERNAME}/repos",
            params={"per_page": 100, "page": page, "type": "owner"},
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    if not INCLUDE_FORKS:
        repos = [r for r in repos if not r.get("fork")]
    return repos


def get_language_totals(repos):
    totals = {}
    for repo in repos:
        r = session.get(repo["languages_url"])
        if r.status_code != 200:
            continue
        for lang, byte_count in r.json().items():
            if lang in EXCLUDE:
                continue
            totals[lang] = totals.get(lang, 0) + byte_count
    return totals


def make_badge(lang):
    color, logo, logo_color = BADGE_STYLE.get(lang, ("333333", "", "white"))
    label = lang.replace(" ", "_").replace("+", "%2B").replace("#", "%23")
    logo_part = f"&logo={logo}&logoColor={logo_color}" if logo else ""
    return f"![{lang}](https://img.shields.io/badge/{label}-{color}?style=for-the-badge{logo_part})"


def update_readme(badges_markdown):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(<!-- LANGUAGES:START -->)(.*?)(<!-- LANGUAGES:END -->)"
    replacement = r"\1\n" + badges_markdown + r"\n\3"
    new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)

    if count == 0:
        print("No <!-- LANGUAGES:START/END --> markers found in README.md")
        sys.exit(1)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    repos = get_repos()
    totals = get_language_totals(repos)
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N]
    badges = "\n".join(make_badge(lang) for lang, _ in ranked)
    update_readme(badges)
    print(f"Updated README with {len(ranked)} languages: {[l for l, _ in ranked]}")


if __name__ == "__main__":
    main()
