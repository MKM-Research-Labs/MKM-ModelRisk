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
"""Client (external counterparty) field metadata and vocabulary (coding rule R1).

A Client is an external company we hand a governance evidence pack to. Unlike the
institution (which is a singleton on the MRC settings), Clients are a list: each
carries its own contact org tree (Divisions -> Departments -> Contacts) and the
Products / Models it is linked to. The pack-history collection records every
generated pack so the platform stays bi-temporal — the *as-of* the pack reflects
and the *generated-at* it was produced are both retained.
"""
from __future__ import annotations

VALID_CLIENT_STATUS = ("Active", "Prospect", "Inactive", "Retired")

# A link is to either a Product or an inventory Model, and the client pack is
# assembled from whatever these resolve to.
VALID_CLIENT_LINK_TYPES = ("Product", "Model")

# How many of the most-recent completed MRC meetings' minutes the client pack
# carries. The pack scope is "most recent, regardless of the linked models"; this
# caps how far back it reaches so a pack does not balloon over a long meeting history.
CLIENT_PACK_RECENT_MEETINGS = 5

# Client identifiers are generated (CL-001, CL-002, ...) rather than supplied:
# a client is a company someone types the name of, not a coded artefact like a
# model, so there is no natural id for the user to provide.
CLIENT_ID_PREFIX = "CL"

# Ordered scalar field specs (mirrors the Product/Model field-spec shape).
CLIENT_FIELD_SPECS = {
    "name": {"label": "Client name", "type": "text", "group": "Company"},
    "legal_entity": {"label": "Legal entity", "type": "text", "group": "Company"},
    "sector": {"label": "Sector", "type": "text", "group": "Company"},
    "relationship_owner": {"label": "Relationship owner", "type": "text",
                           "group": "Company", "reference": "people"},
    "notes": {"label": "Notes", "type": "text", "group": "Company"},
    "status": {"label": "Status", "type": "choice", "options": VALID_CLIENT_STATUS,
               "group": "Governance"},
}

# The register form's minimum: just the company name. Everything else — the org
# tree, contacts and links — is filled in on the client's own view afterwards.
CLIENT_REGISTER_FIELDS = ("name",)

# Fields editable through the generic field-edit command. ``status`` Retired is
# reached via the retire command, not a free edit, but the field itself is set.
CLIENT_EDITABLE_FIELDS = (
    "name", "legal_entity", "sector", "relationship_owner", "notes", "status",
)
CLIENT_FIELD_CHOICES = {"status": VALID_CLIENT_STATUS}

# Collection names carried on a Client aggregate.
CLIENT_DIVISIONS = "divisions"
CLIENT_DEPARTMENTS = "departments"
CLIENT_CONTACTS = "contacts"
CLIENT_LINKS = "links"
CLIENT_PACKS = "packs"

# The client's own contact org tree, its Product/Model links, and its pack
# history — all driven by the generic collections engine. Divisions and
# Departments are the client's internal structure (e.g. Division "Risk",
# Department "Model Validation"); Contacts are the key people within it.
CLIENT_COLLECTION_SPECS = {
    CLIENT_DIVISIONS: {"label": "Divisions", "id_prefix": "CLDV", "fields": [
        {"key": "value", "label": "Division", "type": "text", "required": True},
    ]},
    CLIENT_DEPARTMENTS: {"label": "Departments", "id_prefix": "CLDP", "fields": [
        {"key": "value", "label": "Department", "type": "text", "required": True},
        {"key": "division", "label": "Division", "type": "text"},
    ]},
    CLIENT_CONTACTS: {"label": "Contacts", "id_prefix": "CLC", "fields": [
        {"key": "name", "label": "Name", "type": "text", "required": True},
        {"key": "email", "label": "Email", "type": "text"},
        {"key": "role", "label": "Role", "type": "text"},
        {"key": "department", "label": "Department", "type": "text"},
    ]},
    CLIENT_LINKS: {"label": "Links", "id_prefix": "CLL", "fields": [
        {"key": "link_type", "label": "Link type", "type": "choice",
         "options": VALID_CLIENT_LINK_TYPES, "required": True},
        {"key": "subject_id", "label": "Product / Model", "type": "text", "required": True},
        {"key": "note", "label": "Note", "type": "text"},
    ]},
    # Written only by the pack command (server-stamped), never the generic add
    # route. ``as_of`` is valid time, ``generated_at`` is transaction time.
    CLIENT_PACKS: {"label": "Pack history", "id_prefix": "CLP", "fields": [
        {"key": "as_of", "label": "As of", "type": "text", "required": True},
        {"key": "generated_at", "label": "Generated at", "type": "text", "required": True},
        {"key": "filename", "label": "Stored file", "type": "text", "required": True},
        {"key": "original_name", "label": "File name", "type": "text"},
        {"key": "size", "label": "Size", "type": "text"},
    ]},
}
