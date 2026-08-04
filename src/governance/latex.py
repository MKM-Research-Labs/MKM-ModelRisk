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

The house style follows ``docs/Swaption.tex`` as its canonical template — that file
is the reference for the preamble (geometry, one-half spacing, booktabs tables,
sectioning depth), the large title fonts and the title-page layout. On top of the
template we add the governance chrome it omits: the brand colour, the running
header/footer and the title-page legal notice.

One preamble, one title page, one header/footer, so the Meeting Pack, the Model
Risk Report and the interoperability handover all read as the same document family:
the ``mkmblue`` brand colour, one-half spacing, a fancy header carrying the document
title, and a ``Page x of y`` / classification footer. Every title page carries the
legal notice from ``config.reporting``, which asserts rights over the *contents* of
the generated document — the models, methodology and calculations it describes. That
is separate from the software that produced it, which remains MIT-licensed.
"""
from __future__ import annotations

from typing import Any

from config.reporting import (DEFAULT_AUTHOR, DEFAULT_CLASSIFICATION,
                              DEFAULT_LEGAL_NOTICE, DEFAULT_ORG)

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


def _longtable(cols: str, head: str, body: str, caption: str | None) -> str:
    """Assemble one booktabs longtable — no vertical rules, a heavy rule top and
    bottom and a light rule under the header, the clean look the model-documentation
    protocol uses.

    With a ``caption`` the table is numbered (``Table N: ...``): the caption shows
    once, on the first page, while the column header repeats via ``\\endhead`` on any
    continuation page. Without one it is an unnumbered table whose header still repeats.
    """
    header_rows = "\\toprule\n" + head + "\n\\midrule\n"
    if caption:
        top = ("\\caption{" + _esc(caption) + "}\\\\\n" + header_rows +
               "\\endfirsthead\n" + header_rows + "\\endhead\n")
    else:
        top = header_rows + "\\endhead\n"
    return ("\\begin{longtable}{" + cols + "}\n" + top + body +
            "\\bottomrule\n\\end{longtable}\n")


def _table(headers: list[str], rows: list[list[Any]], caption: str | None = None) -> str:
    cols = "l" * len(headers)
    head = " & ".join("\\textbf{" + _esc(h) + "}" for h in headers) + " \\\\"
    body = "".join(" & ".join(_esc(c) for c in row) + " \\\\\n" for row in rows)
    return _longtable(cols, head, body, caption)


def _wrappable(value: Any) -> str:
    """Escaped text that may break after an underscore or a slash. Identifiers and
    module paths (``BRI_FLOOR_UPLIFT``, ``config/bri.py``) have no hyphenation points,
    so in a narrow column they otherwise run straight over the right margin."""
    return _esc(value).replace("\\_", "\\_\\allowbreak{}").replace("/", "/\\allowbreak{}")


def _quoted(text: str) -> str:
    """Straight double quotes as LaTeX opening/closing pairs, so a notice reads as
    ``"as is"`` rather than with two closing quotes."""
    out, opening = [], True
    for char in text:
        if char == '"':
            out.append("``" if opening else "''")
            opening = not opening
        else:
            out.append(char)
    return "".join(out)


def legal_notice(paragraphs=None) -> str:
    """The legal notice block for a title page.

    It covers the contents of the generated document -- the models, methodology and
    calculations it describes -- and is deliberately silent about the software that
    produced it, which is MIT-licensed. Every document family reaches this through
    ``title_page``, so a new report cannot be published without it.
    """
    text = DEFAULT_LEGAL_NOTICE if paragraphs is None else paragraphs
    if not text:
        return ""
    body = "\\par\\medskip\n".join(_quoted(_esc(p)) for p in text)
    return ("\\vfill\n\\begin{minipage}{\\textwidth}\\footnotesize\\raggedright\n"
            "\\textbf{Legal notice}\\par\\medskip\n" + body +
            "\n\\end{minipage}\n")


def _para_table(headers: list[str], rows: list[list[Any]], weights: list[float],
                caption: str | None = None) -> str:
    """A longtable whose columns wrap, for tables carrying prose rather than codes.

    ``weights`` are each column's share of the text width and should sum to 1; they
    are scaled down slightly to leave room for the inter-column padding, otherwise
    the table runs over the right margin. Columns are ragged-right: justifying a
    column this narrow leaves rivers of white space between the words.

    Styled to match ``_table``'s booktabs house style — horizontal rules only, a
    light rule under the header, and \\addlinespace giving each row a little air. A
    ``caption`` numbers the table (``Table N: ...``)."""
    col = ">{\\raggedright\\arraybackslash}p{%.4f\\textwidth}"
    cols = " ".join(col % (w * 0.93) for w in weights)
    head = " & ".join("\\textbf{" + _esc(h) + "}" for h in headers) + " \\\\"
    body = "".join(" & ".join(_wrappable(c) for c in row) + " \\\\\n\\addlinespace\n"
                   for row in rows)
    return _longtable(cols, head, body, caption)


def _section(title: str, body: str) -> str:
    # Numbered sections, as the model-documentation protocol uses.
    return "\\section{" + _esc(title) + "}\n" + body


def _subsection(title: str, body: str) -> str:
    """A numbered subsection, for documents that break a section down per topic."""
    return "\\subsection{" + _esc(title) + "}\n" + body


def preamble(doc_title: str, *, doc_version: str = "1.0", org_name: str = "") -> str:
    """The shared document preamble, modelled on the ``docs/Swaption.tex`` house
    template: its geometry, one-half spacing, booktabs tables, sectioning depth and
    the large title fonts. On top of the template we keep the governance chrome the
    template omits — the brand colour and the fancy header/footer carrying
    ``doc_title`` and a CONFIDENTIAL / page-count foot."""
    org = _esc(org_name or DEFAULT_ORG)
    return (
        "\\documentclass[11pt]{article}\n"
        "\\usepackage[utf8]{inputenc}\n"
        # Number and list sections/subsections down to the depth the template uses.
        "\\setcounter{tocdepth}{3}\\setcounter{secnumdepth}{3}\n"
        "\\usepackage{graphicx}\\usepackage{longtable}\\usepackage{array}\\usepackage{booktabs}\n"
        "\\usepackage{subcaption}\\usepackage[toc,page]{appendix}\n"
        "\\usepackage{xcolor}\\usepackage{parskip}\\usepackage{enumitem}\\setlist{nosep}\n"
        "\\usepackage{float}\\usepackage{lastpage}\\usepackage{fancyhdr}\\usepackage{hyperref}\n"
        # amsmath so model documentation can carry mathematics; \text{} inside a
        # formula is undefined without it, which silently fails a whole compile.
        "\\usepackage{amsmath}\\usepackage{amsfonts}\n"
        # calc backs the \real{} column widths pandoc emits for the user guide's tables.
        "\\usepackage{calc}\n"
        # The template's large title fonts, used on the title page.
        "\\font\\myverylargefont=cmr12 at 35pt\n\\font\\mylargefont=cmr12 at 25pt\n"
        # The template's geometry (170mm text, 20mm top); we keep a 25mm bottom so the
        # footer rule the template does not carry still has room.
        "\\usepackage{geometry}\\geometry{a4paper, left=20mm, right=20mm, top=20mm, bottom=25mm}\n"
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
    """A title page in the ``docs/Swaption.tex`` house style: the logo on top, the
    organisation and the document subject in the template's large title font, the
    document type beneath, and a ``Document Version`` / date line pushed toward the
    foot. We keep the governance chrome the template omits — a CONFIDENTIAL mark and
    the legal notice (a report cannot be published without it)."""
    graphic = ("\\includegraphics[width=0.4\\textwidth]{" + LOGO_ASSET + "}\\\\[1.2cm]\n"
               if logo else "")
    author_line = "{\\large " + _esc(author) + "\\par}\\vspace{0.5cm}\n" if author else ""
    return (
        "\\begin{titlepage}\\thispagestyle{empty}\\begin{center}\n"
        "\\vspace*{1.5cm}\n" + graphic +
        # Organisation and document subject in the template's large font; the subject
        # (a model/product identifier and name) can be long, so it is allowed to wrap.
        "{\\mylargefont " + _esc(org_name or DEFAULT_ORG) + "\\par}\\vspace{2\\baselineskip}\n"
        "{\\LARGE\\bfseries " + _esc(title) + "\\par}\\vspace{1\\baselineskip}\n"
        "{\\Large\\textcolor{gray}{" + _esc(subtitle) + "}\\par}\n"
        "\\vspace{\\stretch{2}}\n"
        "{\\large " + _esc(date) + "\\\\[0.3cm]Document Version " + _esc(version) + "\\par}\\vspace{0.8cm}\n"
        + author_line +
        "\\textcolor{red}{\\textbf{" + _esc(DEFAULT_CLASSIFICATION) + "}}\\par\n"
        "\\end{center}\n" + legal_notice() + "\\end{titlepage}\n"
    )


def history_page(date: str, description: str, *, org_name: str = "", version: str = "1.0") -> str:
    """The Document History section (Date / Version / Description / Author). Numbered,
    and placed at the END of the document, as the model-documentation protocol does."""
    rows = [[date, version, description, org_name or DEFAULT_ORG]]
    return "\\section{Document History}\n" + _table(
        ["Date", "Version", "Description", "Author"], rows, caption="Document history")


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
