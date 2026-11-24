"""Check release hashes and local Markdown links; no network access."""
import hashlib
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
def verify():
    records=(ROOT/'SHA256SUMS').read_text(encoding='utf-8').splitlines()
    count=0
    for line in records:
        if not line.strip():continue
        expected,relative=line.split('  ',1)
        path=(ROOT/relative).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():raise ValueError('Invalid release path: '+relative)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Hash mismatch: '+relative)
        count+=1
    links=0
    for path in ROOT.rglob('*.md'):
        if any(x in path.parts for x in ('.git','work')):continue
        for link in re.findall(r'\]\(([^\s)]+)\)',path.read_text(encoding='utf-8')):
            if '://' in link or link.startswith('#'):continue
            target=(path.parent/link.split('#')[0]).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():raise ValueError(f'Broken local link: {path.name}: {link}')
            links+=1
    print(f'PASS: {count} release files; {links} local links')
if __name__=='__main__':verify()
