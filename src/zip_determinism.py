"""Rewrite an Office file so that two builds of the same data are byte-identical.

.xlsx and .pptx are zip archives, and both openpyxl and python-pptx stamp each entry with the
current clock. That alone makes every rebuild differ, which breaks the idempotence guarantee the
rest of the pipeline keeps and puts noise in every diff. Rewriting the archive with a fixed
timestamp and a stable entry order removes the only source of non-determinism in these two
artifacts; the parts themselves are already deterministic.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

# The earliest timestamp the zip format can represent. Any fixed value works; this one is the
# conventional choice for reproducible archives.
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def normalize(path: Path) -> Path:
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")

    with zipfile.ZipFile(path) as source:
        # Sorted by name, which also keeps [Content_Types].xml first as the format requires.
        entries = sorted(source.infolist(), key=lambda info: info.filename)
        payload = [(info, source.read(info.filename)) for info in entries]

    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as target:
        for info, data in payload:
            stable = zipfile.ZipInfo(info.filename, date_time=FIXED_TIMESTAMP)
            stable.compress_type = zipfile.ZIP_DEFLATED
            stable.external_attr = info.external_attr
            stable.create_system = 0
            target.writestr(stable, data)

    temporary.replace(path)
    return path
