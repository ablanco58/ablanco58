"""Actualiza solo la seccion de estadisticas con datos publicos de GitHub."""
import datetime
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

USER = "ablanco58"
ROOT = Path(__file__).resolve().parents[1]
START = "<!-- PUBLIC-STATS:START -->"
END = "<!-- PUBLIC-STATS:END -->"


def fetch(path):
    headers = {"User-Agent": "ablanco58-profile", "Accept": "application/vnd.github+json"}
    if token := os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request("https://api.github.com" + path, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def stats(user, repos):
    public = [repo for repo in repos if not repo.get("private", False)]
    projects = [repo for repo in public if not repo.get("fork", False) and repo["name"] != USER]
    languages = sorted({repo["language"] for repo in projects if repo.get("language")})
    year = datetime.datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")).year
    stars = sum(repo.get("stargazers_count", 0) for repo in projects)
    text = (
        f"En GitHub desde **{year}** · **{len(projects)} proyectos públicos** "
        f"· **{len(languages)} lenguajes** en mis repositorios."
    )
    if stars:
        text += f" **{stars} {'estrella' if stars == 1 else 'estrellas'}** entre mis proyectos."
    return text


def replace_stats(readme, text):
    if readme.count(START) != 1 or readme.count(END) != 1:
        raise ValueError("El README debe tener un solo bloque PUBLIC-STATS.")
    before, rest = readme.split(START, 1)
    _, after = rest.split(END, 1)
    return before + START + "\n" + text + "\n" + END + after


def main():
    user = fetch("/users/" + USER)
    repos = []
    page = 1
    while True:
        batch = fetch(f"/users/{USER}/repos?per_page=100&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    path = ROOT / "README.md"
    updated = replace_stats(path.read_text(encoding="utf-8"), stats(user, repos))
    path.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
