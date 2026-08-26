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
"""How a client pack explains itself: CONTENTS.txt and the cover page.

The same information twice, for two readers. ``CONTENTS.txt`` is the machine-readable
manifest; the cover PDF is what a person opens first, which is why it is named to
sort to the top of the archive listing.

Both describe the FINISHED pack, so both are written last, once the packed and
missing lists are complete -- and neither lists itself. Saying what was recorded but
unavailable matters as much as saying what was packed: a pack that quietly omitted a
missing file would be read as a complete one.
"""
from __future__ import annotations

# Friendly section names for the top-level folder each packed file lives under, used
# on the cover page's "Pack contents" table.
FOLDER_LABELS = {
    "models": "Model Risk Documents",
    "events": "Operational event write-ups",
    "governance": "Governance",
    "mrc": "MRC minutes and Terms of Reference",
    "supplementary": "Supplementary evidence",
}


def contents_txt(client: dict, as_of: str, generated_at: str,
                 packed: list[str], missing: list[str]) -> str:
    data = client.get("data") or {}
    lines = [
        f"{client['client_id']} --- {data.get('name') or ''}",
        "Client pack",
        f"As of (valid time):      {as_of}",
        f"Generated at (txn time): {generated_at}",
        "",
        "This pack contains:",
    ]
    lines += ["  " + name for name in packed]
    if missing:
        lines += ["", "Recorded but not available at the time of packing:"]
        lines += ["  " + name for name in missing]
    return "\n".join(lines) + "\n"


def _cover_rows(paths: list[str]) -> list[list[str]]:
    """One row per packed file: its friendly section and its path within the pack,
    grouped by section so the reader can find each document."""
    return [[FOLDER_LABELS.get(p.split("/", 1)[0], p.split("/", 1)[0]), p]
            for p in sorted(paths, key=lambda x: (x.split("/", 1)[0], x))]


def cover_pdf(client: dict, as_of: str, generated_at: str,
              packed: list[str], missing: list[str], settings: dict) -> bytes:
    """A cover-page PDF in the shared house style: title page with the client and the
    bi-temporal stamps, then a numbered "Pack contents" table (and, when relevant, a
    table of items recorded but unavailable). The same information as CONTENTS.txt,
    presented for a human rather than a machine."""
    from src.governance.latex import (_esc, _para_table, _section, front_matter,
                                       logo_asset, preamble)
    from src.governance.mrc.pack import compile_tex
    data = client.get("data") or {}
    org = (settings.get("fields") or {}).get("org_name", "")
    name = data.get("name") or ""
    title = str(client["client_id"]) + (" --- " + name if name else "")
    assets = logo_asset(settings)
    intro = ("Generated on \\textbf{" + _esc(generated_at) + "} for the model risk "
             "position as of \\textbf{" + _esc(as_of) + "}. This pack bundles the "
             "documents listed below; every generated PDF was built at the moment of "
             "packing, so nothing here is a stale copy.\n\n")
    body = _section("Pack contents", intro + _para_table(
        ["Section", "File in pack"], _cover_rows(packed), [0.34, 0.66],
        caption="Pack contents"))
    if missing:
        body += _section("Recorded but not available", (
            "The following items are recorded against the client but their files were "
            "not available when the pack was built.\n\n") + _para_table(
            ["Section", "File in pack"], _cover_rows(missing), [0.34, 0.66],
            caption="Recorded but not available at packing"))
    tex = (preamble("Client Pack", org_name=org) + "\\begin{document}\n"
           + front_matter(title, "Client Pack", org_name=org, date=as_of,
                          logo=bool(assets))
           + body + "\\end{document}\n")
    return compile_tex(tex, assets)


__all__ = ["FOLDER_LABELS", "contents_txt", "cover_pdf"]
