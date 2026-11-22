"""Make the bindery and reader editions from the same linked vector pages."""
import sys
from pathlib import Path

import pikepdf

mm = 72 / 25.4
folder = Path(sys.argv[2])
with pikepdf.open(sys.argv[1]) as book:
    assert len(book.pages) % 4 == 0
    book.Root.PageLayout = pikepdf.Name('/TwoPageRight')
    book.docinfo['/Author'] = 'Fremtidens Tegnestue'
    for page in book.pages:
        width, height = map(float, list(page.MediaBox)[2:])
        # Centre the exact trim box within Chromium's rounded media size.
        dx, dy = (width - 170 * mm) / 2, (height - 240 * mm) / 2
        page.TrimBox = [dx, dy, width - dx, height - dy]
        page.MediaBox = [dx - 3*mm, dy - 3*mm, width - dx + 3*mm, height - dy + 3*mm]
        page.CropBox = page.MediaBox
        page.BleedBox = page.MediaBox
    book.save(folder / 'tryk.pdf')
    for page in book.pages:
        page.CropBox = page.TrimBox
    book.save(folder / sys.argv[3])
