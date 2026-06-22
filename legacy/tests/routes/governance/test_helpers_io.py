# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Tests for governance helpers: inventory, audit log, and meetings I/O.
"""

import json


def _write_json(path, data):
    path.write_text(json.dumps(data))


# ===========================================================================
# _load_inventory / _save_inventory
# ===========================================================================

class TestLoadInventory:

    def test_loads_valid_file(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_inventory
        inv = {"models": [{"model_id": "M1"}]}
        p = tmp_path / "inv.json"
        _write_json(p, inv)
        monkeypatch.setattr(c, "INVENTORY_PATH", str(p))
        result = _load_inventory()
        assert result["models"][0]["model_id"] == "M1"

    def test_returns_none_when_missing(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_inventory
        monkeypatch.setattr(c, "INVENTORY_PATH", str(tmp_path / "missing.json"))
        assert _load_inventory() is None

    def test_returns_none_on_bad_json(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_inventory
        p = tmp_path / "bad.json"
        p.write_text("not json {{}")
        monkeypatch.setattr(c, "INVENTORY_PATH", str(p))
        assert _load_inventory() is None


class TestSaveInventory:

    def test_saves_data(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_inventory
        p = tmp_path / "inv.json"
        monkeypatch.setattr(c, "INVENTORY_PATH", str(p))
        result = _save_inventory({"models": []})
        assert result is True
        assert json.loads(p.read_text())["models"] == []

    def test_returns_false_on_oserror(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_inventory
        monkeypatch.setattr(c, "INVENTORY_PATH", str(tmp_path))
        result = _save_inventory({"models": []})
        assert result is False


# ===========================================================================
# _load_audit_log / _save_audit_log
# ===========================================================================

class TestLoadAuditLog:

    def test_returns_empty_list_when_missing(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_audit_log
        monkeypatch.setattr(c, "AUDIT_LOG_PATH", str(tmp_path / "no.json"))
        assert _load_audit_log() == []

    def test_returns_empty_list_on_bad_json(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_audit_log
        p = tmp_path / "audit.json"
        p.write_text("not json")
        monkeypatch.setattr(c, "AUDIT_LOG_PATH", str(p))
        assert _load_audit_log() == []

    def test_loads_entries(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_audit_log
        p = tmp_path / "audit.json"
        _write_json(p, [{"event": "test"}])
        monkeypatch.setattr(c, "AUDIT_LOG_PATH", str(p))
        result = _load_audit_log()
        assert result[0]["event"] == "test"


class TestSaveAuditLog:

    def test_saves_entries(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_audit_log
        p = tmp_path / "audit.json"
        monkeypatch.setattr(c, "AUDIT_LOG_PATH", str(p))
        result = _save_audit_log([{"event": "created"}])
        assert result is True
        assert json.loads(p.read_text())[0]["event"] == "created"

    def test_returns_false_on_oserror(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_audit_log
        monkeypatch.setattr(c, "AUDIT_LOG_PATH", str(tmp_path))
        assert _save_audit_log([]) is False


# ===========================================================================
# _load_meetings / _save_meetings / _find_meeting / _save_and_respond
# ===========================================================================

class TestLoadMeetings:

    def test_returns_empty_list_when_missing(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_meetings
        monkeypatch.setattr(c, "MRC_MEETINGS_PATH", str(tmp_path / "no.json"))
        assert _load_meetings() == []

    def test_loads_list(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_meetings
        p = tmp_path / "mrc.json"
        _write_json(p, [{"id": "M1"}])
        monkeypatch.setattr(c, "MRC_MEETINGS_PATH", str(p))
        assert _load_meetings()[0]["id"] == "M1"


class TestSaveMeetings:

    def test_saves_meetings(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_meetings
        p = tmp_path / "mrc.json"
        monkeypatch.setattr(c, "MRC_MEETINGS_PATH", str(p))
        result = _save_meetings([{"id": "M1"}])
        assert result is True
        assert json.loads(p.read_text())[0]["id"] == "M1"

    def test_returns_false_on_oserror(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_meetings
        monkeypatch.setattr(c, "MRC_MEETINGS_PATH", str(tmp_path))
        assert _save_meetings([]) is False


class TestFindMeeting:

    def _make_app(self):
        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        return app

    def test_finds_existing_meeting(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _find_meeting
        p = tmp_path / "mrc.json"
        _write_json(p, [{"id": "M1", "title": "Meeting 1"}])
        monkeypatch.setattr(c, "MRC_MEETINGS_PATH", str(p))
        app = self._make_app()
        with app.app_context():
            meetings, meeting, err = _find_meeting("M1")
            assert meeting is not None
            assert meeting["id"] == "M1"
            assert err is None

    def test_returns_error_for_missing_meeting(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _find_meeting
        p = tmp_path / "mrc.json"
        _write_json(p, [])
        monkeypatch.setattr(c, "MRC_MEETINGS_PATH", str(p))
        app = self._make_app()
        with app.app_context():
            meetings, meeting, err = _find_meeting("GHOST")
            assert meeting is None
            assert err is not None


class TestSaveAndRespond:

    def test_saves_and_returns_response(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_and_respond
        p = tmp_path / "mrc.json"
        meetings = [{"id": "M1", "title": "T"}]
        _write_json(p, meetings)
        monkeypatch.setattr(c, "MRC_MEETINGS_PATH", str(p))
        app = __import__("server").create_app()
        app.config["TESTING"] = True
        with app.app_context():
            resp = _save_and_respond(meetings, meetings[0])
            assert resp is not None
