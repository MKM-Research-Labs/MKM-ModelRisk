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
"""The .env loader: one file configures the machine, whatever the entry point."""
from __future__ import annotations

from config import env


def test_loads_key_values_and_strips_quotes(tmp_path, monkeypatch):
    monkeypatch.delenv("SAMPLE_PATH", raising=False)
    monkeypatch.delenv("SAMPLE_PLAIN", raising=False)
    f = tmp_path / ".env"
    f.write_text('# a comment\n\nSAMPLE_PATH="/Volumes/A Disk/data"\nSAMPLE_PLAIN=5433\nnot-a-pair\n')
    assert env.load(f) == 2
    import os
    assert os.environ["SAMPLE_PATH"] == "/Volumes/A Disk/data"   # quotes stripped
    assert os.environ["SAMPLE_PLAIN"] == "5433"


def test_a_real_environment_variable_wins(tmp_path, monkeypatch):
    """A deployment's settings must never be overridden by a stray local file."""
    monkeypatch.setenv("SAMPLE_WINS", "from-environment")
    f = tmp_path / ".env"
    f.write_text("SAMPLE_WINS=from-file\n")
    assert env.load(f) == 0
    import os
    assert os.environ["SAMPLE_WINS"] == "from-environment"


def test_missing_file_is_not_an_error(tmp_path):
    assert env.load(tmp_path / "absent.env") == 0
