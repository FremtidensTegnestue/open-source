"""Statisk kontrol af alle versionsstyrede Markdown-/HTML-henvisninger."""
import collections
import html
import posixpath
import re
import subprocess
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.ids.update(v for k, v in attrs.items() if k == 'id' and v)
        if tag == 'a' and attrs.get('name'):
            self.ids.add(attrs['name'])
        for key in ('href', 'src'):
            if attrs.get(key):
                self.links.append((self.getpos()[0], attrs[key]))

def prose(text):
    # Fjern kodeblokke uden at flytte linjenumre.
    lines = text.splitlines(keepends=True)
    fence = None
    result = []
    for line in lines:
        m = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if m:
            if fence is None:
                fence = m.group(1)[0]
            elif m.group(1)[0] == fence:
                fence = None
            result.append('\n')
        elif fence:
            result.append('\n')
        else:
            result.append(re.sub(r'`[^`\n]+`', '', line))
    return ''.join(result)

def markdown_links(text):
    for m in re.finditer(r'\]\(', text):
        start = m.end()
        i = start
        depth = 1
        angle = text[start:start+1] == '<'
        while i < len(text):
            c = text[i]
            if c == '\\':
                i += 2
                continue
            if angle:
                if c == '>':
                    raw = text[start+1:i]
                    break
            else:
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        raw = text[start:i].strip().split()[0] if text[start:i].strip() else ''
                        break
            i += 1
        else:
            continue
        if raw:
            yield text.count('\n', 0, m.start()) + 1, raw
    for m in re.finditer(r'^\s{0,3}\[[^]]+\]:\s+(\S+)', text, re.M):
        yield text.count('\n', 0, m.start()) + 1, m.group(1).strip('<>')

def heading_ids(text):
    parser = HTMLLinks()
    parser.feed(text)
    found = parser.ids
    counts = collections.Counter()
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', prose(text), re.M):
        heading = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', heading)
        heading = re.sub(r'<[^>]*>', '', heading)
        # GitHub drops symbols such as subscript ₂; preserve letters and decimal digits.
        heading = ''.join(c for c in html.unescape(heading).lower()
                          if unicodedata.category(c).startswith(('L', 'M'))
                          or unicodedata.category(c) == 'Nd'
                          or c.isspace() or c in '_-')
        slug = re.sub(r'\s', '-', heading)
        n = counts[slug]
        counts[slug] += 1
        found.add(slug if n == 0 else f'{slug}-{n}')
    return found


def audit(root, files):
    """Check static Markdown/HTML paths and Markdown headings, with exact path case.

    Does not validate external content, rendered layout or JavaScript-generated links.
    """
    files = set(files)
    dirs = {'.'}
    for path in files:
        parent = posixpath.dirname(path)
        while parent:
            dirs.add(parent)
            parent = posixpath.dirname(parent)
    anchor_cache = {}
    checked, broken, external = [], [], set()
    pages = sorted(p for p in files if p.endswith(('.md', '.html')))
    for page in pages:
        text = (root / page).read_text(encoding='utf-8')
        parser = HTMLLinks()
        clean = prose(text) if page.endswith('.md') else text
        parser.feed(clean)
        links = list(markdown_links(clean)) + parser.links if page.endswith('.md') else parser.links
        for line, raw in links:
            raw = html.unescape(raw)
            if raw.startswith(('mailto:', 'data:', 'javascript:', 'tel:')):
                continue
            u = urlsplit(raw)
            if u.scheme or u.netloc:
                external.add(raw)
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(page), unquote(u.path))) if u.path else page
            row = {'page': page, 'line': line, 'link': raw, 'target': target}
            if target not in files and target not in dirs:
                row['error'] = 'file_or_directory_missing_or_wrong_case'
            elif target in files and target.endswith('.md') and u.fragment:
                if target not in anchor_cache:
                    anchor_cache[target] = heading_ids((root / target).read_text(encoding='utf-8'))
                if unquote(u.fragment) not in anchor_cache[target]:
                    row['error'] = 'Markdown_heading_missing'
            checked.append(row)
            if 'error' in row:
                broken.append(row)
    return {'pages': len(pages), 'local_references': len(checked),
            'external_URLs': len(external), 'broken': broken,
            'checked': checked, 'external_references': sorted(external)}


def main():
    root = Path(__file__).resolve().parents[2]
    files = subprocess.check_output(
        ['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z']
    ).decode('utf-8').split('\0')
    report = audit(root, (p for p in files if p))
    print(f"{report['pages']} Markdown/HTML pages; {report['local_references']} local references; {len(report['broken'])} errors")
    for row in report['broken']:
        print(f"{row['page']}:{row['line']}: {row['error']}: {row['link']}")
    return bool(report['broken'])


if __name__ == '__main__':
    raise SystemExit(main())
