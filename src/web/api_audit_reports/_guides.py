# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Publishing the platform's own guides as PDFs (and the user guide as Word).

Its own module in this package because these are document renderers rather than HTTP:
assembling the user guide's LaTeX takes more lines than every route here put
together. ``generate`` decides *when* the guides are published; this decides *how*.

Each renderer returns quietly when its optional engine is missing — pandoc for the
user guide, tectonic for either PDF — so a deployment without them serves everything
else rather than failing the whole Generate action.
"""
from __future__ import annotations

import shutil
import subprocess
from datetime import date

from config.audit import INTEGRATION_GUIDE_TEX, USER_GUIDE_MD
from config.reporting import DOCUMENT_COLOUR_INCLUDE
from src.governance.latex import front_matter, history_page, logo_asset, preamble
from src.governance.latex_style import colour_definitions
from src.governance.mrc.pack import TectonicNotFound, compile_tex
from src.governance.mrc_settings import get_settings


def render_user_guide_docx(dest):
    """The same guide as an editable Word document. An adopter's own people mark a guide
    up and hand it back; a PDF cannot be worked on, so both forms are published from the
    one markdown source rather than diverging as two hand-kept documents."""
    if shutil.which("pandoc") is None:
        return
    subprocess.run(["pandoc", str(USER_GUIDE_MD), "-o", str(dest)],
                   check=True, capture_output=True, text=True)


def render_user_guide(dest):
    """Publish the user guide as a PDF in the shared house style (skipped if pandoc
    or tectonic is absent). The markdown body is converted to a LaTeX fragment and
    wrapped in the standard preamble/title, so the guide matches every other PDF."""
    if shutil.which("pandoc") is None:
        return
    body = subprocess.run(
        ["pandoc", str(USER_GUIDE_MD), "-t", "latex"],
        check=True, capture_output=True, text=True).stdout
    as_of = date.today().isoformat()
    # The institution heads this document like every other one it publishes; the
    # guide is the only report that used to head itself with the platform's name.
    settings = get_settings()
    org = (settings.get("fields") or {}).get("org_name", "")
    assets = logo_asset(settings)
    tex = (
        preamble("User Guide", org_name=org)
        # pandoc's LaTeX uses \tightlist, which its standalone template defines;
        # a fragment does not, so provide it here.
        + "\\providecommand{\\tightlist}{\\setlength{\\itemsep}{0pt}\\setlength{\\parskip}{0pt}}\n"
        # A markdown table becomes a longtable, and an uncaptioned one is wrapped in
        # \def\LTcaptype{none} so the table counter is not stepped. longtable then steps
        # a counter of that name, which nothing defines — so the guide compiled only
        # while it contained no tables, and generating the reports began failing with
        # "No counter 'none' defined" the day one was added. Defining the counter is
        # what pandoc's own template amounts to: it exists to be thrown away.
        + "\\newcounter{none}\n"
        + "\\begin{document}\n"
        + front_matter("User Guide", "Model risk governance console", org_name=org,
                       date=as_of, logo=bool(assets), toc=True)
        + history_page(as_of, "User guide generated", org_name=org)
        + body
        + "\\end{document}\n"
    )
    try:
        dest.write_bytes(compile_tex(tex, assets))
    except TectonicNotFound:
        return


def render_integration_guide(dest):
    """Publish the integration guide (skipped if tectonic is absent).

    Unlike the user guide this one is already LaTeX, and standalone, so that it also
    builds by hand outside the app. Its colours are handed to it alongside the source
    rather than left to the values written in it, so the copy an institution publishes
    is drawn in that institution's brand like every other generated document."""
    assets = {DOCUMENT_COLOUR_INCLUDE: colour_definitions().encode("utf-8")}
    try:
        dest.write_bytes(
            compile_tex(INTEGRATION_GUIDE_TEX.read_text(encoding="utf-8"), assets))
    except TectonicNotFound:
        return
