# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Tests for mediasrv security utilities."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from aqt.mediasrv import (
    MAIN_WEBVIEW_API_WHITELIST,
    UNTRUSTED_MEDIA_CSP,
    LocalFileRequest,
    UnsafePathException,
    _editor_content_security_policy,
    _handle_local_file_request,
    ensure_safe_path,
    exposed_backend_list,
    is_localhost_origin,
    is_sveltekit_page,
)


class TestEnsureSafePath:
    def setup_method(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        subdir = Path(self.tmpdir) / "sub"
        subdir.mkdir()
        (subdir / "file.txt").write_text("ok")

    def test_valid_subpath(self) -> None:
        result = ensure_safe_path(self.tmpdir, "sub/file.txt")
        assert result == os.path.join(os.path.realpath(self.tmpdir), "sub", "file.txt")

    def test_rejects_parent_traversal(self) -> None:
        with pytest.raises(UnsafePathException):
            ensure_safe_path(self.tmpdir, "../etc/passwd")

    def test_rejects_double_traversal(self) -> None:
        with pytest.raises(UnsafePathException):
            ensure_safe_path(self.tmpdir, "sub/../../etc/passwd")

    def test_rejects_absolute_path_escape(self) -> None:
        with pytest.raises(UnsafePathException):
            ensure_safe_path(self.tmpdir, "/etc/passwd")

    def test_rejects_base_dir_itself(self) -> None:
        with pytest.raises(UnsafePathException):
            ensure_safe_path(self.tmpdir, ".")

    def test_rejects_empty_path(self) -> None:
        with pytest.raises(UnsafePathException):
            ensure_safe_path(self.tmpdir, "")

    def test_accepts_pathlib_args(self) -> None:
        result = ensure_safe_path(Path(self.tmpdir), Path("sub/file.txt"))
        assert result.endswith(os.path.join("sub", "file.txt"))

    def test_normalizes_redundant_separators(self) -> None:
        result = ensure_safe_path(self.tmpdir, "sub///file.txt")
        assert result == os.path.join(os.path.realpath(self.tmpdir), "sub", "file.txt")

    def test_rejects_traversal_after_normalization(self) -> None:
        with pytest.raises(UnsafePathException):
            ensure_safe_path(self.tmpdir, "sub/../../../etc/passwd")


class TestIsLocalhostOrigin:
    @pytest.mark.parametrize(
        "origin",
        [
            "http://127.0.0.1:40000",
            "http://localhost:40000",
            "http://[::1]:40000",
            "https://127.0.0.1:40000",
            "https://localhost:40000",
            "https://[::1]:40000",
            "http://127.0.0.1",
            "http://localhost",
            "http://[::1]",
            "http://127.0.0.1/",
            "http://localhost/path",
        ],
    )
    def test_allowed_origins(self, origin: str) -> None:
        assert is_localhost_origin(origin) is True

    @pytest.mark.parametrize(
        "origin",
        [
            "http://evil.com",
            "http://127.0.0.1.evil.com",
            "http://localhost.evil.com",
            "http://evil.com:127.0.0.1",
            "http://notlocalhost:40000",
            "https://evil.com",
            "",
        ],
    )
    def test_rejected_origins(self, origin: str) -> None:
        assert is_localhost_origin(origin) is False


class TestIsSveltekitPage:
    """Routes migrated from PyQt to Svelte must be recognised as SvelteKit pages.

    Each entry is matched on the first path segment, so dynamic route params
    (e.g. a deck id) do not affect the result. Flask's <path:...> route
    converter strips the query string before it reaches this function, so
    query params (e.g. export's ?did=) are never part of the input here.
    """

    @pytest.mark.parametrize(
        "path",
        [
            "deck-chooser/1",
            "deck-description/1",
            "deck-options/1",
            "export",
            "deck-browser",
        ],
    )
    def test_migrated_pages_are_recognised(self, path: str) -> None:
        assert is_sveltekit_page(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            "not-a-real-page",
            "deck-chooser-evil",
            "exports",
            "",
        ],
    )
    def test_unknown_pages_are_rejected(self, path: str) -> None:
        assert is_sveltekit_page(path) is False


class TestExposedBackend:
    """Backend RPCs the migrated pages call must stay exposed to the frontend."""

    @pytest.mark.parametrize(
        "rpc",
        [
            "get_deck",
            "update_deck",
            "get_deck_names",
            "set_deck_collapsed",
            "reparent_decks",
        ],
    )
    def test_deck_rpcs_exposed(self, rpc: str) -> None:
        assert rpc in exposed_backend_list


class TestMainWebviewApiWhitelist:
    """The deck browser (rendered in the shared, lower-trust main webview,
    which also hosts the reviewer) needs its endpoints explicitly
    whitelisted, since that webview doesn't get blanket API access."""

    @pytest.mark.parametrize(
        "path",
        [
            "/_anki/getDeckBrowserContent",
            "/_anki/setDeckCollapsed",
            "/_anki/reparentDecks",
        ],
    )
    def test_deck_browser_endpoints_whitelisted(self, path: str) -> None:
        assert path in MAIN_WEBVIEW_API_WHITELIST


def _make_media_file(tmpdir: str, filename: str, content: bytes = b"test") -> str:
    path = os.path.join(tmpdir, filename)
    with open(path, "wb") as f:
        f.write(content)
    return filename


def _get_csp(response) -> str | None:
    return response.headers.get("Content-Security-Policy")


def _csp_directives(csp: str) -> dict[str, str]:
    directives = {}
    for part in csp.split(";"):
        name, _, value = part.strip().partition(" ")
        directives[name] = value
    return directives


class TestMediaFileCSP:
    """CSP headers on media file responses should block script execution."""

    @pytest.mark.parametrize("doctype", ["html", "svg"])
    def test_doc_has_csp_header(self, doctype: str) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            fname = _make_media_file(
                tmpdir, f"test.{doctype}", f"<{doctype}></{doctype}>".encode()
            )
            req = LocalFileRequest(root=tmpdir, path=fname)
            from aqt.mediasrv import app

            with app.test_request_context():
                resp = _handle_local_file_request(req)
            csp = _get_csp(resp)
            assert csp is not None, f"{doctype} response must have CSP header"

    def test_csp_blocks_connect_to_local_api(self) -> None:
        """Scripts must not be able to fetch() the local /_anki/ API.

        Even if script-src somehow gets relaxed in the future, connect-src
        should not allow http: (which includes http://127.0.0.1).
        """
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            fname = _make_media_file(tmpdir, "test.svg", b"<svg></svg>")
            req = LocalFileRequest(root=tmpdir, path=fname)
            from aqt.mediasrv import app

            with app.test_request_context():
                resp = _handle_local_file_request(req)
            csp = _get_csp(resp)
            assert csp is not None

            # default-src 'none' implies connect-src 'none', which is sufficient
            if "default-src 'none'" in csp:
                return

            # Otherwise connect-src must not include http: or 'self'
            assert "http:" not in csp, (
                f"CSP must not allow http: connections (enables local API access): {csp}"
            )
            assert "'self'" not in csp, (
                f"CSP must not allow 'self' connections (enables local API access): {csp}"
            )

    def test_untrusted_media_is_sandboxed(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            fname = _make_media_file(tmpdir, "test.svg", b"<svg></svg>")
            req = LocalFileRequest(root=tmpdir, path=fname)
            from aqt.mediasrv import app

            with app.test_request_context():
                resp = _handle_local_file_request(req)
            csp = _get_csp(resp)
            assert csp == UNTRUSTED_MEDIA_CSP

            directives = _csp_directives(csp)
            assert directives["default-src"] == "'none'"
            assert directives["script-src"] == "'none'"
            assert directives["connect-src"] == "'none'"
            assert directives["object-src"] == "'none'"
            assert directives["frame-src"] == "'none'"
            assert directives["child-src"] == "'none'"
            assert directives["base-uri"] == "'none'"
            assert directives["form-action"] == "'none'"
            assert directives["sandbox"] == ""
            assert "frame-ancestors" not in directives

    def test_trusted_local_file_does_not_get_untrusted_media_csp(self) -> None:
        """Add-on exports use LocalFileRequest too, but should not be sandboxed."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            fname = _make_media_file(tmpdir, "addon.html", b"<html></html>")
            req = LocalFileRequest(root=tmpdir, path=fname, untrusted=False)
            from aqt.mediasrv import app

            with app.test_request_context():
                resp = _handle_local_file_request(req)
            assert _get_csp(resp) is None


class TestEditorPageCSP:
    def test_editor_csp_does_not_block_user_embeds(self) -> None:
        csp = _editor_content_security_policy(port=12345)
        directives = _csp_directives(csp)

        assert directives["script-src"] == (
            "http://127.0.0.1:12345/_anki/ http://127.0.0.1:12345/_addons/"
        )
        assert "object-src" not in directives
        assert "frame-src" not in directives
        assert "child-src" not in directives
        assert "img-src" not in directives
