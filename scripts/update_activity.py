"""Render a small, dependency-free profile card from real public GitHub data."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = 'Mahmoud-Berkoti'

def fetch_repositories():
    repositories = []
    for page in range(1, 101):
        headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-statistics'}
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            headers['Authorization'] = 'Bearer ' + token
        request = Request(
            f'https://api.github.com/users/{USERNAME}/repos?type=owner&per_page=100&page={page}',
            headers=headers,
        )
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        repositories.extend(r for r in batch if not r['fork'] and not r['private'])
        if len(batch) < 100:
            return repositories
    raise RuntimeError('Repository pagination exceeded expected bounds')

def render(repositories, theme):
    background, foreground, secondary, line = (
        ('#0d1117', '#f0f3f6', '#9198a1', '#30363d') if theme == 'dark'
        else ('#ffffff', '#1d1d1f', '#6e6e73', '#d8dee4')
    )
    values = [len(repositories), sum(r['stargazers_count'] for r in repositories),
              len({r['language'] for r in repositories if r['language']})]
    labels = ['Public repositories', 'Stars received', 'Primary languages']
    date = datetime.now(timezone.utc).strftime('%d %b %Y')
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="780" height="164" viewBox="0 0 780 164" role="img" aria-labelledby="title desc">',
             '<title id="title">Public GitHub activity</title>',
             f'<desc id="desc">{values[0]} public repositories, {values[1]} stars, {values[2]} primary languages. Updated {date}. Forks excluded.</desc>',
             f'<rect width="780" height="164" rx="16" fill="{background}"/>',
             '<g font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif">']
    for index, (value, label) in enumerate(zip(values, labels)):
        x = 28 + index * 260
        parts.extend([f'<text x="{x}" y="64" font-size="34" font-weight="600" fill="{foreground}">{value}</text>',
                      f'<text x="{x}" y="91" font-size="14" fill="{secondary}">{label}</text>'])
    parts.extend([f'<path d="M28 116H752" stroke="{line}"/>',
                  f'<text x="28" y="144" font-size="11" fill="{secondary}">PUBLIC REPOSITORIES · UPDATED {date.upper()}</text>', '</g></svg>'])
    return '\n'.join(parts) + '\n'

if __name__ == '__main__':
    repositories = fetch_repositories()
    output = Path(__file__).resolve().parents[1] / 'assets'
    output.mkdir(exist_ok=True)
    for theme in ('light', 'dark'):
        (output / f'activity-{theme}.svg').write_text(render(repositories, theme))
