"""Shared pytest fixtures for Persona Studio tests.

Test isolation for the static directory
---------------------------------------
``PersonaStudioApp`` defaults its ``static_dir`` to the real ``prototype/``
directory, and a few tests pass ``static_dir=Path("prototype")`` explicitly.
Generation endpoints write files there (``assets/generated/gen-*.svg``, and the
external-image download path writes ``gen-*.png``). Running the suite therefore
littered the working tree with stray artifacts — e.g. an 8-byte invalid
``prototype/assets/generated/gen-000005.png`` written by the mocked Wanx
download test.

This autouse fixture redirects any app that would otherwise write into the real
``prototype/`` tree to a per-test sandbox copy, so tests can read the real UI
assets they need (index.html, persona-ref images, ...) while their generated
output stays in ``tmp_path``. Tests that already pass an isolated ``static_dir``
(their own ``tmp_path``) are left untouched.
"""

import shutil
from pathlib import Path

import pytest

from persona_studio import server

_REAL_PROTOTYPE = (Path(server.__file__).resolve().parent.parent / "prototype").resolve()


@pytest.fixture(autouse=True)
def isolate_prototype_static_dir(tmp_path, monkeypatch):
    sandbox = tmp_path / "prototype"
    # Copy the lightweight UI assets but skip the multi-MB generated/ outputs;
    # generation tests recreate whatever they need under the sandbox.
    shutil.copytree(
        _REAL_PROTOTYPE,
        sandbox,
        ignore=shutil.ignore_patterns("generated"),
    )
    (sandbox / "assets" / "generated").mkdir(parents=True, exist_ok=True)

    original_init = server.PersonaStudioApp.__init__

    def patched_init(self, manager=None, static_dir=None, data_path=None):
        if static_dir is None or Path(static_dir).resolve() == _REAL_PROTOTYPE:
            static_dir = sandbox
        return original_init(self, manager=manager, static_dir=static_dir, data_path=data_path)

    monkeypatch.setattr(server.PersonaStudioApp, "__init__", patched_init)
    yield
