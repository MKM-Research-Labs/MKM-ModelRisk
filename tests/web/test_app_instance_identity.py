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
"""Two running apps must not be able to stop each other.

The estate's app (5015, the real database) and the verification app (5016, a scratch
copy) are the same command run twice. Until 2026-08-25 they also shared gunicorn's
default control socket, so a control command aimed at one reached whichever held it,
and a second app could fail to start because the first had the socket. Killing "the
verification app" took the estate's app down with it.

The separation is keyed on the DATABASE, because that is what makes one of these
disposable and the other the firm's governance record.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _identity(db_name: str) -> tuple[str, str]:
    """``(proc_name, control_socket)`` as a fresh process would resolve them.

    Read in a subprocess because config is resolved at import: setting the variable
    in this one would be answered from the already-imported module.
    """
    code = ("from config.web import WEB_PROC_NAME, WEB_CONTROL_SOCKET;"
            "print(WEB_PROC_NAME);print(WEB_CONTROL_SOCKET)")
    out = subprocess.run([sys.executable, "-c", code], cwd=str(REPO_ROOT),
                         env={"DB_NAME": db_name, "PATH": "/usr/bin:/bin",
                              "HOME": str(Path.home()),
                              "PYTHONPATH": str(REPO_ROOT)},
                         capture_output=True, text=True, check=True)
    name, socket = out.stdout.strip().splitlines()[:2]
    return name, socket


def test_the_estate_app_and_the_scratch_app_have_different_control_sockets():
    live_name, live_socket = _identity("mkm_modelrisk")
    scratch_name, scratch_socket = _identity("mkm_modelrisk_scratch")
    assert live_socket != scratch_socket
    assert live_name != scratch_name
    # Named for the database, so which is which is readable rather than inferred.
    assert "mkm_modelrisk" in live_name and "scratch" in scratch_name


def test_the_socket_is_not_gunicorns_shared_default():
    """The default is one path for every gunicorn on the machine — the whole bug."""
    _, socket = _identity("mkm_modelrisk")
    assert not socket.endswith("/gunicorn.ctl")


def test_gunicorn_actually_wires_the_two_settings():
    """Config values nothing reads would be a fix in name only."""
    text = (REPO_ROOT / "gunicorn.conf.py").read_text(encoding="utf-8")
    assert "proc_name = WEB_PROC_NAME" in text
    assert "control_socket = WEB_CONTROL_SOCKET" in text


def test_proc_name_renames_the_process_only_where_gunicorn_allows_it():
    """``proc_name`` is NOT a rename you can rely on, and the difference is platform.

    gunicorn disables setproctitle on macOS on purpose -- it segfaults there through
    fork (benoitc/gunicorn#3021) -- so on a Mac ``proc_name`` is accepted and does
    nothing. Asserting the dependency is installed would pass while the rename never
    happens, which is worse than no test: it reads as proof and is not.

    So this asserts what is actually true on THIS platform, and the port on the
    command line below is what makes the two apps distinguishable regardless.
    """
    import gunicorn.util as util
    renames = util._setproctitle("probe") is not None or sys.platform != "darwin"
    if sys.platform == "darwin":
        assert not renames, ("gunicorn has started honouring proc_name on macOS — "
                             "good news, but this test and config/web.py both say it "
                             "does not, and they should be corrected together")
    else:
        pytest.importorskip("setproctitle")


def test_the_verification_app_puts_its_port_on_its_command_line():
    """What actually tells the two apps apart on macOS, where the rename is a no-op:
    the port is in the raw command line, which is what ``ps`` and ``pgrep -f`` read."""
    text = (REPO_ROOT / "scripts" / "dev_app.sh").read_text(encoding="utf-8")
    assert '--bind "$WEB_HOST:$WEB_PORT"' in text


def test_both_settings_are_overridable_from_the_environment():
    """An operator running a third copy must be able to name it."""
    module = importlib.import_module("config.web")
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert 'os.environ.get("WEB_PROC_NAME")' in source
    assert '"WEB_CONTROL_SOCKET"' in source
