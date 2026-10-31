"""Reject third-party aircraft payloads and local/private records before publication."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SUFFIXES = {'.md', '.txt', '.json', '.py', '.ps1', '.cmd', '.yml', '.cfg'}
ALLOWED_EXTENSIONLESS = {'LICENSE', '.gitignore', '.gitattributes'}

def check(paths):
    for p in paths:
        rel = p.relative_to(ROOT)
        if p.suffix.lower() not in ALLOWED_SUFFIXES and p.name not in ALLOWED_EXTENSIONLESS:
            raise ValueError(f'Unsupported public file: {rel}')
        data = p.read_bytes()
        if b'\x00' in data:
            raise ValueError(f'Binary file is not allowed: {rel}')
        text = data.decode('utf-8')
        private_prefixes = ('c:' + '\\' + 'users' + '\\', 'c:' + '/' + 'users' + '/',
                            'x:' + '\\' + 'x-plane', 'a:' + '\\' + 'nrt', 'o:' + '\\' + 'nrt')
        if any(prefix in text.lower() for prefix in private_prefixes):
            raise ValueError(f'Local/private path is not allowed: {rel}')
    return True

def main():
    # Inspect all source files, including newly added/untracked ones.
    paths = [p for p in ROOT.rglob('*') if p.is_file()
             and not any(part in ('.git', '__pycache__') for part in p.relative_to(ROOT).parts)]
    check(paths)
    print(f'Public scope verified: {len(paths)} text/metadata files; no aircraft payloads.')

if __name__ == '__main__':
    main()
