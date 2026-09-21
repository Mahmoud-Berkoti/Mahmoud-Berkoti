"""Render a small, dependency-free profile card from real public GitHub data."""
import json
from collections import Counter
from html import escape
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
        ('#132231', '#f0f3f6', '#b0c0cc', '#2b3d4b') if theme == 'dark'
        else ('#ffffff', '#1d1d1f', '#6e6e73', '#d8dee4')
    )
    values = [len(repositories), sum(r['stargazers_count'] for r in repositories),
              len({r['language'] for r in repositories if r['language']})]
    labels = ['Public repositories', 'Stars received', 'Primary languages']
    date = datetime.now(timezone.utc).strftime('%d %b %Y')
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="780" height="246" viewBox="0 0 780 246" role="img" aria-labelledby="title desc">',
             '<title id="title">Public GitHub activity</title>',
             f'<desc id="desc">{values[0]} public repositories, {values[1]} stars, {values[2]} primary languages. Updated {date}. Forks excluded.</desc>',
             f'<rect width="780" height="246" rx="16" fill="{background}"/>',
             '<g font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif">']
    for index, (value, label) in enumerate(zip(values, labels)):
        x = 28 + index * 260
        parts.extend([f'<text x="{x}" y="64" font-size="34" font-weight="600" fill="{foreground}">{value}</text>',
                      f'<text x="{x}" y="91" font-size="14" fill="{secondary}">{label}</text>'])
    counts = Counter(r['language'] for r in repositories if r['language'])
    top = counts.most_common(5)
    if len(counts) > 5:
        top.append(('Other', sum(counts.values()) - sum(n for _, n in top)))
    colors = ['#86d9bc', '#9bbcf9', '#f3bd75', '#c5acf1', '#f39aaf', '#8095a6']
    total = sum(counts.values())
    x = 28
    parts.append(f'<text x="28" y="143" font-size="12" fill="{secondary}">PRIMARY LANGUAGE · REPOSITORY COUNT</text>')
    for index, ((language, count), color) in enumerate(zip(top, colors)):
        width = 724 * count / total
        parts.append(f'<rect x="{x:.2f}" y="158" width="{max(0, width-3):.2f}" height="10" rx="3" fill="{color}"/>')
        label_x = 28 + index * 121
        parts.append(f'<circle cx="{label_x+3}" cy="190" r="3" fill="{color}"/>')
        parts.append(f'<text x="{label_x+12}" y="194" font-size="11" fill="{secondary}">{escape(language)} {count}</text>')
        x += width
    parts.extend([f'<path d="M28 116H752" stroke="{line}"/>',
                  f'<text x="28" y="227" font-size="11" fill="{secondary}">PUBLIC REPOSITORIES · UPDATED {date.upper()}</text>', '</g></svg>'])
    return '\n'.join(parts) + '\n'

if __name__ == '__main__':
    repositories = fetch_repositories()
    output = Path(__file__).resolve().parents[1] / 'assets'
    output.mkdir(exist_ok=True)
    for theme in ('light', 'dark'):
        (output / f'activity-{theme}.svg').write_text(render(repositories, theme))
