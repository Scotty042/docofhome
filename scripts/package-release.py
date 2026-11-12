"""Build a clean source ZIP and SHA-256 sidecar without local/private artifacts."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT/'VERSION').read_text().strip()
assert json.loads((ROOT/'SOURCE_INFO.json').read_text())['version'] == version
excluded = {'node_modules', 'dist', '.git', '__pycache__', '.pytest_cache', '.mypy_cache',
            '.ruff_cache', '.venv', 'data', 'backups', 'logs', 'secrets', 'coverage', '.pnpm-store'}
package = ROOT.parent/f'DocOfHome-{version}.zip'
assert not package.exists(), f'Package already exists: {package}'
paths = []
for path in sorted(ROOT.rglob('*')):
    relative = path.relative_to(ROOT)
    if any(part in excluded or part.startswith('.pytest-temp-') for part in relative.parts):
        continue
    if path.is_symlink() or not path.is_file():
        continue
    if path.name in {'.DS_Store', '.env'} or path.suffix in {'.pyc', '.pyo', '.sqlite3', '.db', '.key', '.pem', '.token'}:
        continue
    paths.append(path)
with ZipFile(package, 'w', ZIP_DEFLATED, compresslevel=9) as archive:
    for path in paths:
        archive.write(path, path.relative_to(ROOT).as_posix())
with ZipFile(package) as archive:
    names = archive.namelist()
    assert names.count("VERSION") == 1
    assert "Dockerfile" in names
    assert all(not name.startswith("/") and ".." not in Path(name).parts for name in names)
    assert archive.read("VERSION").decode().strip() == version
    assert archive.testzip() is None
    assert len(archive.namelist()) == len(paths)
    for path in paths:
        name = path.relative_to(ROOT).as_posix()
        assert archive.read(name) == path.read_bytes(), name
checksum = hashlib.sha256(package.read_bytes()).hexdigest()
package.with_suffix('.zip.sha256').write_text(f'{checksum}  {package.name}\n')
print(f'{package}\n{len(paths)} verified files; {package.stat().st_size} bytes\nSHA256 {checksum}')
