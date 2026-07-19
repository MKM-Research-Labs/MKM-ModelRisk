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
"""The shared LaTeX house style for every generated PDF.

One preamble, one title page, one header/footer, so the Meeting Pack, the Model
Risk Report and the interoperability handover all read as the same document family:
the ``mkmblue`` brand colour, one-half spacing, a fancy header carrying the document
title, and a ``Page x of y`` / ``CONFIDENTIAL`` footer. Governance PDFs are marked
CONFIDENTIAL, but nothing here asserts proprietary rights — the code is MIT-licensed.
"""
from __future__ import annotations

from typing import Any

from config.reporting import DEFAULT_AUTHOR, DEFAULT_CLASSIFICATION, DEFAULT_ORG

_LATEX_REPLACEMENTS = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

LOGO_ASSET = "logo"  # \includegraphics{logo}; graphicx picks the actual extension


def logo_asset(settings=None) -> dict[str, bytes]:
    """The organisation's uploaded logo as a ``compile_tex`` asset, or empty if none
    is uploaded. The logo is supplied by the adopting institution at runtime (via MRC
    settings) — never bundled in the repo. No logo means a text-only title page."""
    try:
        from config.files import IMAGE_EXTENSIONS
        from src.files import extension, upload_path
        if settings is None:
            from src.governance.mrc_settings import get_settings
            settings = get_settings()
        logo = (settings or {}).get("logo")
        ext = extension((logo or {}).get("filename", ""))
        if not logo or ext not in IMAGE_EXTENSIONS:
            return {}
        return {LOGO_ASSET + "." + ext: upload_path("mrc", logo["filename"]).read_bytes()}
    except Exception:
        return {}


def _esc(value: Any) -> str:
    text = "" if value is None else str(value)
    return "".join(_LATEX_REPLACEMENTS.get(ch, ch) for ch in text)


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    cols = "|" + "l|" * len(headers)
    head = " & ".join("\\textbf{" + _esc(h) + "}" for h in headers) + " \\\\ \\hline"
    body = "".join(" & ".join(_esc(c) for c in row) + " \\\\ \\hline\n" for row in rows)
    return ("\\begin{longtable}{" + cols + "}\n\\hline " + head + "\n" + body +
            "\\end{longtable}\n")


def _section(title: str, body: str) -> str:
    # Numbered sections, as the model-documentation protocol uses.
    return "\\section{" + _esc(title) + "}\n" + body


def preamble(doc_title: str, *, doc_version: str = "1.0", org_name: str = "") -> str:
    """The shared document preamble: packages, geometry, brand colour and the
    fancy header/footer carrying ``doc_title`` and a CONFIDENTIAL / page-count foot."""
    org = _esc(org_name or DEFAULT_ORG)
    return (
        "\\documentclass[11pt]{article}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage{graphicx}\\usepackage{longtable}\\usepackage{array}\\usepackage{booktabs}\n"
        "\\usepackage{xcolor}\\usepackage{parskip}\\usepackage{enumitem}\\setlist{nosep}\n"
        "\\usepackage{float}\\usepackage{lastpage}\\usepackage{fancyhdr}\\usepackage{hyperref}\n"
        # calc backs the \real{} column widths pandoc emits for the user guide's tables.
        "\\usepackage{calc}\n"
        "\\usepackage{geometry}\\geometry{a4paper, total={170mm,247mm}, left=20mm, top=25mm, bottom=25mm}\n"
        "\\usepackage{setspace}\\onehalfspacing\n"
        "\\definecolor{mkmblue}{HTML}{1565C0}\n"
        "\\hypersetup{colorlinks=true,linkcolor=mkmblue,citecolor=mkmblue,urlcolor=mkmblue}\n"
        "\\pagestyle{fancy}\\fancyhf{}\n"
        "\\fancyhead[L]{\\small\\textcolor{gray}{" + org + "}}\n"
        "\\fancyhead[R]{\\small\\textcolor{gray}{" + _esc(doc_title) + " --- v" + _esc(doc_version) + "}}\n"
        "\\fancyfoot[C]{\\small\\textcolor{gray}{" + _esc(DEFAULT_CLASSIFICATION) + "}}\n"
        "\\fancyfoot[R]{\\small\\textcolor{gray}{Page \\thepage\\ of \\pageref{LastPage}}}\n"
        "\\renewcommand{\\headrulewidth}{0.4pt}\\renewcommand{\\footrulewidth}{0.4pt}\n"
    )


def title_page(title: str, subtitle: str, *, org_name: str = "", version: str = "1.0",
               date: str = "", author: str = "", logo: bool = False) -> str:
    """A full title page: optional cover graphic, brand-blue title, subtitle, and the
    org/version/date, closing with a CONFIDENTIAL mark (no proprietary assertion)."""
    graphic = ("\\vspace*{1cm}\\includegraphics[width=0.4\\textwidth]{" + LOGO_ASSET + "}\\\\[1.5cm]\n"
               if logo else "\\vspace*{1cm}\n")
    author_line = "{\\large " + _esc(author) + "\\par}\\vspace{0.5cm}\n" if author else ""
    return (
        "\\begin{titlepage}\\begin{center}\n" + graphic +
        "{\\Huge\\bfseries\\textcolor{mkmblue}{" + _esc(title) + "}\\par}\\vspace{0.5cm}\n"
        "{\\Large\\textcolor{gray}{" + _esc(subtitle) + "}\\par}\\vspace{2cm}\n"
        "{\\large " + _esc(org_name or DEFAULT_ORG) + "\\par}\\vspace{0.5cm}\n"
        "{\\large Version " + _esc(version) + " --- " + _esc(date) + "\\par}\\vspace{0.5cm}\n"
        + author_line +
        "\\vspace{2cm}\\textcolor{red}{\\textbf{" + _esc(DEFAULT_CLASSIFICATION) + "}}\n"
        "\\end{center}\\end{titlepage}\n"
    )


def history_page(date: str, description: str, *, org_name: str = "", version: str = "1.0") -> str:
    """The Document History section (Date / Version / Description / Author). Numbered,
    and placed at the END of the document, as the model-documentation protocol does."""
    rows = [[date, version, description, org_name or DEFAULT_ORG]]
    return "\\section{Document History}\n" + _table(
        ["Date", "Version", "Description", "Author"], rows)


def front_matter(title: str, subtitle: str, *, org_name: str = "", date: str = "",
                 author: str = "", logo: bool = False, version: str = "1.0",
                 toc: bool = False) -> str:
    """A document's opening: the title page, then (for multi-section documents) a
    Table of Contents. The Document History goes at the end via ``history_page``."""
    front = title_page(title, subtitle, org_name=org_name, date=date,
                       author=author or DEFAULT_AUTHOR, version=version, logo=logo)
    if toc:
        front += "\\tableofcontents\n\\clearpage\n"
    return front
