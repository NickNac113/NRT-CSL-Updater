from pathlib import Path
from tempfile import TemporaryDirectory
import contextlib
import copy
import hashlib
import http.server
import importlib.util
import json
import shutil
import subprocess
import threading
import unittest
import urllib.request
import zlib

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT / 'tools/build_feed.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class FeedTests(unittest.TestCase):
    def test_protocol_crc_size_and_scope(self):
        files = builder.generate()
        checksums = dict(line.rsplit('|', 1) for line in files['skunkcrafts_updater_whitelist.txt'].decode().splitlines())
        sizes = dict(line.rsplit('|', 1) for line in files['skunkcrafts_updater_sizeslist.txt'].decode().splitlines())
        self.assertEqual(set(checksums), set(builder.PAYLOAD_FILES))
        self.assertEqual(set(sizes), set(checksums))
        self.assertEqual(files['skunkcrafts_updater_blacklist.txt'], b'')
        self.assertNotIn('skunkcrafts_updater.cfg', checksums)
        for name in checksums:
            self.assertEqual(int(checksums[name]), zlib.crc32(files[name]) & 0xffffffff)
            self.assertEqual(int(sizes[name]), len(files[name]))

    def test_rejects_accidental_aircraft_payload(self):
        with TemporaryDirectory() as d:
            stage = Path(d)
            shutil.copytree(ROOT / 'payload', stage / 'payload')
            shutil.copy2(ROOT / 'release.json', stage / 'release.json')
            (stage / 'payload/model.obj').write_text('not allowed')
            with self.assertRaisesRegex(ValueError, 'allowlist'):
                builder.generate(stage)

    def test_feed_is_identical_for_windows_line_endings(self):
        with TemporaryDirectory() as d:
            stage = Path(d)
            shutil.copytree(ROOT / 'payload', stage / 'payload')
            shutil.copy2(ROOT / 'release.json', stage / 'release.json')
            for p in (stage / 'payload').rglob('*'):
                if p.is_file():
                    p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
            self.assertEqual(builder.generate(stage), builder.generate())

    def test_catalog_contains_metadata_only(self):
        catalog = json.loads((ROOT / 'payload/NRT-CSL-Tools/runtime-integrity.json').read_text())
        self.assertEqual(len(catalog['types']), 27)
        for code, item in catalog['types'].items():
            self.assertTrue(code.isalnum())
            for path, digest in item['assets'].items():
                self.assertEqual(Path(path).name, path)
                self.assertEqual(len(digest), 64)
                int(digest, 16)

    def test_http_depot_round_trip(self):
        files = builder.generate()
        with TemporaryDirectory() as d:
            root = Path(d)
            for name, value in files.items():
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(value)
            class Handler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=d, **kwargs)
                def log_message(self, *args):
                    pass
            server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            try:
                for name, value in files.items():
                    with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}/{name}?v=0.1.0') as r:
                        self.assertEqual(r.read(), value)
            finally:
                server.shutdown()
                server.server_close()
                t.join()

@unittest.skipUnless(shutil.which('powershell.exe') or shutil.which('pwsh'), 'PowerShell is not installed')
class CheckerTests(unittest.TestCase):
    def test_valid_zero_filled_and_missing_files(self):
        ps = shutil.which('powershell.exe') or shutil.which('pwsh')
        with TemporaryDirectory() as d:
            root = Path(d)
            tools = root / 'NRT-CSL-Tools'
            tools.mkdir()
            script = tools / 'Verify-NRT-CSL.ps1'
            shutil.copy2(ROOT / 'payload/NRT-CSL-Tools/Verify-NRT-CSL.ps1', script)
            type_dir = root / 'NRT CSL/TEST'
            type_dir.mkdir(parents=True)
            manifest = b'EXPORT_NAME test\n'
            (type_dir / 'xsb_aircraft.txt').write_bytes(manifest)
            sample = b'fixture data'
            (type_dir / 'fixture.dat').write_bytes(sample)
            catalog = {'types': {'TEST': {
                'allowed_manifest_sha256': [hashlib.sha256(manifest).hexdigest()],
                'assets': {'fixture.dat': hashlib.sha256(sample).hexdigest()}}}}
            (tools / 'runtime-integrity.json').write_text(json.dumps(catalog))
            def run():
                return subprocess.run([ps, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script)], capture_output=True, text=True)
            result = run()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            (type_dir / 'xsb_aircraft.txt').write_bytes(b'\0' * len(manifest))
            self.assertNotEqual(run().returncode, 0)
            (type_dir / 'xsb_aircraft.txt').write_bytes(manifest)
            (type_dir / 'fixture.dat').unlink()
            self.assertNotEqual(run().returncode, 0)

if __name__ == '__main__':
    unittest.main()
