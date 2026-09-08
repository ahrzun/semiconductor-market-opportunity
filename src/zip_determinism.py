"""Rewrite an Office file so that two builds of the same data are byte-identical.

.xlsx and .pptx are zip archives, and there are two clocks in each: the zip entry timestamps,
and the document timestamps inside docProps/core.xml. Both writers set the second one at save
time - openpyxl overwrites dcterms:modified even when the property is pinned beforehand - so
neither can be fixed by the calling script. Rewriting the archive here with a stable entry order,
a fixed entry timestamp and a fixed document timestamp removes both, which is everything that
made these two artifacts differ between rebuilds; their parts are otherwise deterministic.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

# The earliest timestamp the zip format can represent. Any fixed value works; this one is the
# conventional choice for reproducible archives.
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
FIXED_DOCUMENT_TIME = b"1980-01-01T00:00:00Z"

CORE_PROPERTIES = "docProps/core.xml"
W3CDTF = re.compile(rb"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def _stabilise(name: str, data: bytes) -> bytes:
    if name != CORE_PROPERTIES:
        return data
    return W3CDTF.sub(FIXED_DOCUMENT_TIME, data)


def normalize(path: Path) -> Path:
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")

    with zipfile.ZipFile(path) as source:
        # Sorted by name, which also keeps [Content_Types].xml first as the format requires.
        entries = sorted(source.infolist(), key=lambda info: info.filename)
        payload = [(info, _stabilise(info.filename, source.read(info.filename)))
                   for info in entries]

    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as target:
        for info, data in payload:
            stable = zipfile.ZipInfo(info.filename, date_time=FIXED_TIMESTAMP)
            stable.compress_type = zipfile.ZIP_DEFLATED
            stable.external_attr = info.external_attr
            stable.create_system = 0
            target.writestr(stable, data)

    temporary.replace(path)
    return path
