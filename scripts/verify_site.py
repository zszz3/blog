#!/usr/bin/env python3
"""Check public static output for broken local page, asset and section links."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse
import json
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'dist').resolve()
class Page(HTMLParser):
    def __init__(self, file):
        super().__init__()
        self.file, self.ids, self.refs, self.headings = file, set(), [], []
        self.canonical = None
        self.feed(file.read_text())
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
            if tag in ['h1','h2','h3','h4','h5','h6']: self.headings.append(a['id'])
        if a.get('rel') == 'canonical': self.canonical = a.get('href')
        for name in ['href', 'src', 'poster']:
            if a.get(name): self.refs.append(a[name])
        if a.get('srcset'):
            self.refs.extend(v.strip().split()[0] for v in a['srcset'].split(',') if v.strip())

pages = {file: Page(file) for file in root.rglob('*.html')}
errors = []
for file, page in pages.items():
    relative = file.relative_to(root).as_posix()
    route = '/' + (relative[:-10] if relative.endswith('index.html') else relative)
    base = page.canonical or 'https://wojiecihuo.cn' + route
    for heading, count in Counter(page.headings).items():
        if count > 1: errors.append(f'{relative}: duplicate heading anchor {heading}')
    for ref in page.refs:
        url = urlparse(urljoin(base, ref))
        if url.scheme not in ['http', 'https'] or url.netloc != urlparse(base).netloc: continue
        candidate = root / unquote(url.path).lstrip('/')
        if candidate.is_dir(): candidate /= 'index.html'
        if not candidate.is_file() and candidate.suffix == '': candidate = candidate.with_suffix('.html')
        if not candidate.is_file(): errors.append(f'{relative}: missing {ref}')
        elif url.fragment and candidate in pages and unquote(url.fragment) not in pages[candidate].ids:
            errors.append(f'{relative}: missing anchor {ref}')
for forbidden in ['.prerender', 'server']:
    if (root / forbidden).exists(): errors.append(f'Unexpected server intermediate: {forbidden}')
index = json.loads((root / 'search.json').read_text())
for entry in index:
    candidate = root / unquote(entry['url']).lstrip('/') / 'index.html'
    if not candidate.is_file(): errors.append('Search result has no page: ' + entry['url'])
if errors:
    print('\n'.join(dict.fromkeys(errors)))
    raise SystemExit(1)
print(f'Checked {len(pages)} pages and {len(index)} search entries: local links, assets and section anchors are valid.')
