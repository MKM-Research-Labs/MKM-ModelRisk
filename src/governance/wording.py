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
"""What a generated document says on behalf of the institution that publishes it.

The classification banner, the "prepared by" author line and the title-page legal
notice are one institution's words, not platform behaviour. They are recorded as
settings (Admin > Misc) and read here at generation time, so an adopter re-labels
every document it publishes without editing code. ``config.reporting`` holds the
wording that ships, used until the institution records its own.
"""
from __future__ import annotations

from config.governance import LEGAL_NOTICE_SEPARATOR
from config.reporting import (DEFAULT_AUTHOR, DEFAULT_CLASSIFICATION,
                              DEFAULT_LEGAL_NOTICE)


def _settings_fields(settings=None) -> dict:
    """The MRC settings fields, or ``{}`` when they cannot be read.

    A document must still build where there is no settings record to read — a unit
    test, a first run — so any failure falls back to the shipped defaults rather
    than stopping the compile.
    """
    try:
        if settings is None:
            from src.governance.mrc_settings import get_settings
            settings = get_settings()
        return (settings or {}).get("fields") or {}
    except Exception:
        return {}


def report_wording(settings=None) -> dict:
    """The classification banner, author line and legal-notice paragraphs.

    A setting that has never been recorded falls back to its ``config.reporting``
    default, so a fresh install prints the shipped wording. A setting saved as
    blank is an adopter deliberately dropping that line — an institution that does
    not classify its documents, or that files its legal notice elsewhere — and is
    honoured as empty rather than quietly restored.
    """
    fields = _settings_fields(settings)

    def _value(key, default):
        return default if fields.get(key) is None else str(fields[key]).strip()

    notice = _value("report_legal_notice", None)
    paragraphs = DEFAULT_LEGAL_NOTICE if notice is None else tuple(
        p.strip() for p in notice.split(LEGAL_NOTICE_SEPARATOR) if p.strip())
    return {
        "classification": _value("report_classification", DEFAULT_CLASSIFICATION),
        "author": _value("report_author", DEFAULT_AUTHOR),
        "legal_notice": paragraphs,
    }
