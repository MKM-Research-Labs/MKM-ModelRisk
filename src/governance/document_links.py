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
"""Documents filed as a link: an address instead of an upload.

A link is stored as an Internet Shortcut (``.url``) file in the record's upload
directory and recorded through ``add_document`` like any other document, with its
address carried in the metadata as ``url``. Being a real file is the point: the
packs, the MRC tabling list and the completeness scan all walk a record's files,
and none of them needs to know a link from a PDF. Only the console and the download
endpoint look at ``url`` — to open the address rather than the shortcut.
"""
from __future__ import annotations

from urllib.parse import unquote, urlsplit

from config.files import LINK_DOC_EXTENSION, LINK_DOC_SCHEMES, MAX_LINK_LENGTH
from src.files import UploadError, upload_path
from src.governance.documents import add_document, list_documents


def clean_link(url) -> str:
    """The address, trimmed, or ``UploadError`` if it is not a web link.

    Whitespace and control characters are refused rather than stripped: the address
    is written into the shortcut file line by line, and a newline in it would let a
    caller add lines of their own.
    """
    text = str(url or "").strip()
    if not text:
        raise UploadError("no link provided")
    if len(text) > MAX_LINK_LENGTH:
        raise UploadError("link is too long")
    if any(ord(ch) <= 0x20 or ord(ch) == 0x7F for ch in text):
        raise UploadError("link must not contain spaces or control characters")
    parts = urlsplit(text)
    if parts.scheme.lower() not in LINK_DOC_SCHEMES or not parts.netloc:
        raise UploadError("link must be a web address (http or https)")
    return text


def shortcut_bytes(url: str) -> bytes:
    """The Internet Shortcut file for ``url`` — what opens the link from a pack."""
    return ("[InternetShortcut]\r\nURL=" + url + "\r\n").encode("utf-8")


def link_name(url: str, title: str = "") -> str:
    """The document's name: the title given, else the address's last path segment,
    else its host — always ending in the shortcut extension."""
    name = str(title or "").strip()
    if not name:
        parts = urlsplit(url)
        segments = [s for s in parts.path.split("/") if s]
        name = unquote(segments[-1]) if segments else parts.hostname or "link"
    suffix = "." + LINK_DOC_EXTENSION
    return name if name.lower().endswith(suffix) else name + suffix


def add_link(
    *, aggregate_type: str, aggregate_id: str, scope: str, url: str, title: str,
    description: str, actor: str, category: str = "", config=None,
) -> dict:
    """File ``url`` against the aggregate as a document.

    Two documents stored under one file name would share a file on disk, and a
    second link would silently repoint the first one's shortcut, so a name already
    in use is refused. Compared as stored, not as typed: "a b" and "a_b" are one file.
    """
    address = clean_link(url)
    name = link_name(address, title)
    stored = upload_path(scope, name).name
    if any(d.get("filename") == stored
           for d in list_documents(aggregate_type, aggregate_id, config)):
        raise UploadError(f"a document named {name!r} is already filed here")
    return add_document(
        aggregate_type=aggregate_type, aggregate_id=aggregate_id, scope=scope,
        filename=name, data=shortcut_bytes(address), description=description,
        actor=actor, category=category, url=address, config=config,
    )
