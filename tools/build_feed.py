"""Generate the tools-only SkunkCrafts depot using the official CRC32 format."""
from pathlib import Path
import argparse
import json
import sys
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_FILES = (
    'NRT-CSL-Tools/README.txt',
    'NRT-CSL-Tools/VERSION.txt',
    'NRT-CSL-Tools/Verify-NRT-CSL.cmd',
    'NRT-CSL-Tools/Verify-NRT-CSL.ps1',
    'NRT-CSL-Tools/runtime-integrity.json',
    'changelog.txt',
)

def generate(root=ROOT):
    root = Path(root)
    config = json.loads((root / 'release.json').read_text())
    if config['scope'] != 'tools-only':
        raise ValueError('Only the tools-only publication scope is supported.')
    if not config['module'].startswith('https://raw.githubusercontent.com/') or not config['module'].endswith('/'):
        raise ValueError('Expected a full HTTPS GitHub raw directory URL ending in /.')
    payload = root / 'payload'
    actual = {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}
    if actual != set(PAYLOAD_FILES):
        raise ValueError(f'Payload violates the tools-only allowlist: {actual ^ set(PAYLOAD_FILES)}')
    # GitHub serves LF text; normalize Windows working copies before checksums.
    files = {name: (payload / name).read_bytes().replace(b'\r\n', b'\n') for name in PAYLOAD_FILES}
    if files['NRT-CSL-Tools/VERSION.txt'].decode().strip() != config['version']:
        raise ValueError('VERSION.txt and release.json disagree.')
    cfg = '\n'.join((f"name|{config['name']}", f"module|{config['module']}",
                      f"version|{config['version']}", 'zone|custom', 'locked|false',
                      'disabled|false', 'liveries|false', ''))
    # The configuration is fetched separately, not included in the managed list.
    files['skunkcrafts_updater.cfg'] = cfg.encode()
    files['skunkcrafts_updater_whitelist.txt'] = ''.join(
        f'{name}|{zlib.crc32(files[name]) & 0xffffffff}\n' for name in PAYLOAD_FILES).encode()
    files['skunkcrafts_updater_sizeslist.txt'] = ''.join(
        f'{name}|{len(files[name])}\n' for name in PAYLOAD_FILES).encode()
    files['skunkcrafts_updater_blacklist.txt'] = b''
    return files

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    p.add_argument('--zip', type=Path, help='Create a starter ZIP outside the repository.')
    args = p.parse_args()
    files = generate()
    depot = ROOT / 'updates/stable'
    if args.check:
        actual = {p.relative_to(depot).as_posix() for p in depot.rglob('*') if p.is_file()}
        if actual != set(files) or any((depot / n).read_bytes() != b for n, b in files.items()):
            raise SystemExit('Generated depot is stale. Run python tools/build_feed.py.')
    else:
        extras = {p.relative_to(depot).as_posix() for p in depot.rglob('*') if p.is_file()} - set(files)
        if extras:
            raise SystemExit(f'Unexpected depot files; review before publishing: {extras}')
        for name, data in files.items():
            path = depot / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if args.zip:
        target = args.zip.resolve()
        if target.is_relative_to(ROOT):
            raise SystemExit('The starter ZIP must be outside the public repository.')
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED) as z:
            for name in (*PAYLOAD_FILES, 'skunkcrafts_updater.cfg'):
                z.writestr(name, files[name])
        with zipfile.ZipFile(target) as z:
            if z.testzip() is not None:
                raise SystemExit('Starter ZIP failed verification.')
    print('Tools-only feed verified: six managed files; no deletions or aircraft assets.')

if __name__ == '__main__':
    main()
