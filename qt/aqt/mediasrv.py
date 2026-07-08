# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from __future__ import annotations

import asyncio
import enum
import logging
import mimetypes
import os
import re
import secrets
import sys
import threading
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from errno import EPROTOTYPE
from http import HTTPStatus
from pathlib import Path
from typing import Any, Generic, cast

import flask
import stringcase
import waitress.wasyncore
from flask import Response, abort, request
from waitress.server import create_server

import aqt
import aqt.main
import aqt.operations
from anki import frontend_pb2, generic_pb2, hooks
from anki.collection import (
    NestedOpChanges,
    OpChanges,
    OpChangesOnly,
    Progress,
    SearchNode,
)
from anki.decks import UpdateDeckConfigs, UpdateDeckConfigsMode
from anki.scheduler.v3 import SchedulingStatesWithContext, SetSchedulingStatesRequest
from anki.utils import dev_mode, from_json_bytes, to_json_bytes
from aqt.changenotetype import ChangeNotetypeDialog
from aqt.deckoptions import DeckOptionsDialog
from aqt.operations import on_op_finished
from aqt.operations.deck import update_deck_configs as update_deck_configs_op
from aqt.progress import ProgressUpdate
from aqt.qt import *
from aqt.utils import (
    aqt_data_path,
    askUser,
    openLink,
    show_info,
    show_warning,
    tr,
)

# https://forums.ankiweb.net/t/anki-crash-when-using-a-specific-deck/22266
waitress.wasyncore._DISCONNECTED = waitress.wasyncore._DISCONNECTED.union({EPROTOTYPE})  # type: ignore

logger = logging.getLogger(__name__)
app = flask.Flask(__name__, root_path="/fake")


@dataclass
class LocalFileRequest:
    # base folder, eg media folder
    root: str
    # path to file relative to root folder
    path: str
    # collection media is untrusted user content; add-on web exports are not
    untrusted: bool = True


UNTRUSTED_MEDIA_CSP = "; ".join(
    (
        "default-src 'none'",
        "script-src 'none'",
        "connect-src 'none'",
        "object-src 'none'",
        "frame-src 'none'",
        "child-src 'none'",
        "base-uri 'none'",
        "form-action 'none'",
        "sandbox",
    )
)


def _legacy_editor_content_security_policy(port: int) -> str:
    csp_paths = (
        f"http://127.0.0.1:{port}/_anki/",
        f"http://127.0.0.1:{port}/_addons/",
    )
    return "; ".join((f"script-src {' '.join(csp_paths)}",))


_SVELTEKIT_SCRIPT_HASH_RE = re.compile(rb"'sha256-[A-Za-z0-9+/=]+'")


def _sveltekit_render_script_hash(html: bytes) -> str | None:
    """Extract the hash SvelteKit computed for its inline render script.

    SvelteKit (csp.mode = 'hash' in svelte.config.js) bakes this into a
    <meta http-equiv="content-security-policy"> tag in the built HTML.
    """
    match = _SVELTEKIT_SCRIPT_HASH_RE.search(html)
    return match.group(0).decode("utf-8") if match else None


def _sveltekit_content_security_policy(port: int, script_hash: str | None) -> str:
    csp_paths = [
        f"http://127.0.0.1:{port}/_anki/",
        f"http://127.0.0.1:{port}/_app/",
        f"http://127.0.0.1:{port}/_addons/",
    ]
    if script_hash:
        csp_paths.append(script_hash)
    return "; ".join((f"script-src {' '.join(csp_paths)}",))


@dataclass
class BundledFileRequest:
    # path relative to aqt data folder
    path: str
    # set for SvelteKit routes
    is_sveltekit: bool = False


@dataclass
class NotFound:
    message: str


DynamicRequest = Callable[[], Response]


class PageContext(enum.IntEnum):
    UNKNOWN = enum.auto()
    EDITOR = enum.auto()
    REVIEWER = enum.auto()
    PREVIEWER = enum.auto()
    CARD_LAYOUT = enum.auto()
    DECK_OPTIONS = enum.auto()
    # something in /_anki/pages/
    NON_LEGACY_PAGE = enum.auto()
    # Do not use this if you present user content (e.g. content from cards), as it's a
    # security issue.
    ADDON_PAGE = enum.auto()


@dataclass
class LegacyPage:
    html: str
    context: PageContext


class MediaServer(threading.Thread):
    _ready = threading.Event()
    daemon = True

    def __init__(self, mw: aqt.main.AnkiQt) -> None:
        super().__init__()
        self.is_shutdown = False
        # map of webview ids to pages
        self._legacy_pages: dict[int, LegacyPage] = {}

    def run(self) -> None:
        try:
            desired_host = os.getenv("ANKI_API_HOST", "127.0.0.1")
            desired_port = int(os.getenv("ANKI_API_PORT") or 0)
            self.server = create_server(
                app,
                host=desired_host,
                port=desired_port,
                clear_untrusted_proxy_headers=True,
            )
            logger.info(
                "Serving on http://%s:%s",
                self.server.effective_host,  # type: ignore[union-attr]
                self.server.effective_port,  # type: ignore[union-attr]
            )

            self._ready.set()
            self.server.run()

        except Exception:
            if not self.is_shutdown:
                raise

    def shutdown(self) -> None:
        self.is_shutdown = True
        sockets = list(self.server._map.values())  # type: ignore
        for socket in sockets:
            socket.handle_close()
        # https://github.com/Pylons/webtest/blob/4b8a3ebf984185ff4fefb31b4d0cf82682e1fcf7/webtest/http.py#L93-L104
        self.server.task_dispatcher.shutdown()

    def getPort(self) -> int:
        self._ready.wait()
        return int(self.server.effective_port)  # type: ignore

    def set_page_html(
        self, id: int, html: str, context: PageContext = PageContext.UNKNOWN
    ) -> None:
        self._legacy_pages[id] = LegacyPage(html, context)

    def get_page(self, id: int) -> LegacyPage | None:
        return self._legacy_pages.get(id)

    def get_page_html(self, id: int) -> str | None:
        if page := self.get_page(id):
            return page.html
        else:
            return None

    def get_page_context(self, id: int) -> PageContext | None:
        if page := self.get_page(id):
            return page.context
        else:
            return None

    def clear_page_html(self, id: int) -> None:
        try:
            del self._legacy_pages[id]
        except KeyError:
            pass


@app.route("/favicon.ico")
def favicon() -> Response:
    request = BundledFileRequest(os.path.join("imgs", "favicon.ico"))
    return _handle_builtin_file_request(request)


@app.route("/_anki/readyz")
def readyz() -> Response:
    """Reports whether the profile's collection is open.

    The HTTP server starts listening before the profile/collection finishes
    loading (setupMediaServer() runs synchronously in AnkiQt.__init__, while
    setupProfile() is deferred via a QTimer), so callers that need the
    collection open - e.g. the e2e test harness's webServer readiness check -
    should poll this instead of /favicon.ico, which responds regardless of
    collection state.
    """
    if aqt.mw.col is None:
        return Response(status=HTTPStatus.SERVICE_UNAVAILABLE)
    return Response(status=HTTPStatus.OK)


def _mime_for_path(path: str) -> str:
    "Mime type for provided path/filename."

    _, ext = os.path.splitext(path)
    ext = ext.lower()

    # Badly-behaved apps on Windows can alter the standard mime types in the registry, which can completely
    # break Anki's UI. So we hard-code the most common extensions.
    mime_types = {
        ".css": "text/css",
        ".js": "application/javascript",
        ".mjs": "application/javascript",
        ".html": "text/html",
        ".htm": "text/html",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".ico": "image/x-icon",
        ".json": "application/json",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
        ".otf": "font/otf",
        ".mp3": "audio/mpeg",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".ogg": "audio/ogg",
        ".pdf": "application/pdf",
        ".txt": "text/plain",
    }

    if mime := mime_types.get(ext):
        return mime
    else:
        # fallback to mimetypes, which may consult the registry
        mime, _encoding = mimetypes.guess_type(path)
        return mime or "application/octet-stream"


def _text_response(code: HTTPStatus, text: str) -> Response:
    """Return an error message.

    Response is returned as text/plain, so no escaping of untrusted
    input is required."""
    resp = flask.make_response(text, code)
    resp.headers["Content-type"] = "text/plain"
    return resp


class UnsafePathException(Exception):
    def __init__(self, path: str):
        super().__init__(f"Invalid path: {path}")


def ensure_safe_path(base_dir: str | Path, path: str | Path) -> str:
    base_dir = os.path.realpath(base_dir)
    path = os.path.normpath(path)
    fullpath = os.path.abspath(os.path.join(base_dir, path))

    # protect against directory traversal: https://security.openstack.org/guidelines/dg_using-file-paths.html
    if not fullpath.startswith(base_dir + os.sep):
        raise UnsafePathException(path)
    return fullpath


_LOCALHOST_HOSTS = ("127.0.0.1", "localhost", "[::1]")

_ALLOWED_ORIGIN_PREFIXES = tuple(
    f"{scheme}{host}" for scheme in ("http://", "https://") for host in _LOCALHOST_HOSTS
)


def is_localhost_origin(origin: str) -> bool:
    for prefix in _ALLOWED_ORIGIN_PREFIXES:
        if (
            origin == prefix
            or origin.startswith(prefix + ":")
            or origin.startswith(prefix + "/")
        ):
            return True
    return False


def _handle_local_file_request(request: LocalFileRequest) -> Response:
    directory = request.root
    path = request.path
    try:
        isdir = os.path.isdir(os.path.join(directory, path))
    except ValueError:
        return _text_response(
            HTTPStatus.BAD_REQUEST, f"Path for '{directory} - {path}' is too long!"
        )

    fullpath = ensure_safe_path(directory, path)

    if isdir:
        return _text_response(
            HTTPStatus.FORBIDDEN,
            f"Path for '{directory} - {path}' is a directory (not supported)!",
        )

    try:
        mimetype = _mime_for_path(fullpath)
        if os.path.exists(fullpath):
            if fullpath.endswith(".css"):
                # caching css files prevents flicker in the webview, but we want
                # a short cache
                max_age = 10
            elif fullpath.endswith(".js"):
                # don't cache js files
                max_age = 0
            else:
                max_age = 60 * 60
            response = flask.send_file(
                fullpath,
                mimetype=mimetype,
                conditional=True,
                max_age=max_age,
                download_name="foo",  # type: ignore[call-arg]
            )
            if request.untrusted:
                # Prevent user-provided HTML/SVG from running as an active document.
                response.headers["Content-Security-Policy"] = UNTRUSTED_MEDIA_CSP
            return response
        else:
            print(f"Not found: {path}")
            return _text_response(HTTPStatus.NOT_FOUND, f"Invalid path: {path}")

    except Exception as error:
        if dev_mode:
            print(
                "Caught HTTP server exception,\n%s"
                % "".join(traceback.format_exception(*sys.exc_info())),
            )

        # swallow it - user likely surfed away from
        # review screen before an image had finished
        # downloading
        return _text_response(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))


def _builtin_data(path: str) -> bytes:
    """Return data from file in aqt/data folder."""
    full_path = ensure_safe_path(aqt_data_path().parent, path)
    with open(full_path, "rb") as f:
        return f.read()


def _handle_builtin_file_request(request: BundledFileRequest) -> Response:
    path = request.path
    # do we need to serve the fallback page?
    immutable = "immutable" in path
    if path.startswith("sveltekit/") and not immutable:
        path = "sveltekit/index.html"
    mimetype = _mime_for_path(path)
    data_path = f"data/web/{path}"
    try:
        data = _builtin_data(data_path)
        response = Response(data, mimetype=mimetype)
        if immutable:
            response.headers["Cache-Control"] = "max-age=31536000"
        if request.is_sveltekit:
            script_hash = (
                _sveltekit_render_script_hash(data)
                if path.endswith("index.html")
                else None
            )
            response.headers["Content-Security-Policy"] = (
                _sveltekit_content_security_policy(
                    aqt.mw.mediaServer.getPort(), script_hash
                )
            )
        return response
    except FileNotFoundError:
        if dev_mode:
            print(f"404: {data_path}")
        resp = _text_response(HTTPStatus.NOT_FOUND, f"Invalid path: {path}")
        # we're including the path verbatim in our response, so we need to either use
        # plain text, or escape HTML characters to avoid reflecting untrusted input
        resp.headers["Content-type"] = "text/plain"
        return resp
    except Exception as error:
        if dev_mode:
            print(
                "Caught HTTP server exception,\n%s"
                % "".join(traceback.format_exception(*sys.exc_info())),
            )

        # swallow it - user likely surfed away from
        # review screen before an image had finished
        # downloading
        return _text_response(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))


@app.route("/<path:pathin>", methods=["GET", "POST"])
def handle_request(pathin: str) -> Response:
    if os.environ.get("ANKI_API_HOST") != "0.0.0.0":
        host = request.headers.get("Host", "").lower()
        origin = request.headers.get("Origin", "").lower()
        allowed_hosts = tuple(f"{h}:" for h in _LOCALHOST_HOSTS)
        if not any(host.startswith(h) for h in allowed_hosts):
            logger.warning("denied non-local host: %s", host)
            abort(403)
        if origin and not is_localhost_origin(origin):
            logger.warning("denied non-local origin: %s", origin)
            abort(403)

    req = _extract_request(pathin)
    logger.debug("%s /%s", flask.request.method, pathin)

    try:
        if isinstance(req, NotFound):
            print(req.message)
            return _text_response(HTTPStatus.NOT_FOUND, f"Invalid path: {pathin}")
        elif callable(req):
            return _handle_dynamic_request(req)
        elif isinstance(req, BundledFileRequest):
            return _handle_builtin_file_request(req)
        elif isinstance(req, LocalFileRequest):
            return _handle_local_file_request(req)
        else:
            return _text_response(HTTPStatus.FORBIDDEN, f"unexpected request: {pathin}")
    except UnsafePathException as exc:
        return _text_response(HTTPStatus.FORBIDDEN, str(exc))


def is_sveltekit_page(path: str) -> bool:
    page_name = path.split("/")[0]
    return page_name in [
        "addon-config",
        "addon-manager",
        "graphs",
        "congrats",
        "card-info",
        "change-notetype",
        "deck-options",
        "deck-description",
        "deck-chooser",
        "deck-browser",
        "deck-overview",
        "browse",
        "card-editor",
        "export",
        "import-anki-package",
        "import-csv",
        "import-page",
        "image-occlusion",
        "editor",
    ]


def _extract_internal_request(
    path: str,
) -> BundledFileRequest | DynamicRequest | NotFound | None:
    "Catch /_anki references and rewrite them to web export folder."
    is_sveltekit = is_sveltekit_page(path)
    if is_sveltekit:
        path = f"_anki/sveltekit/_app/{path}"
    if path.startswith("_app/"):
        path = path.replace("_app", "_anki/sveltekit/_app")

    prefix = "_anki/"
    if not path.startswith(prefix):
        return None

    dirname = os.path.dirname(path)
    filename = os.path.basename(path)
    additional_prefix = None

    if dirname == "_anki":
        if flask.request.method == "POST":
            return _extract_collection_post_request(filename)
        elif get_handler := _extract_dynamic_get_request(filename):
            return get_handler

        # remap legacy top-level references
        base, ext = os.path.splitext(filename)
        if ext == ".css":
            additional_prefix = "css/"
        elif ext == ".js":
            if base in ("jquery-ui", "jquery", "plot"):
                additional_prefix = "js/vendor/"
            else:
                additional_prefix = "js/"
    # handle requests for vendored libraries
    elif dirname == "_anki/js/vendor":
        base, ext = os.path.splitext(filename)

        if base == "jquery":
            base = "jquery.min"
            additional_prefix = "js/vendor/"

        elif base == "jquery-ui":
            base = "jquery-ui.min"
            additional_prefix = "js/vendor/"

    if additional_prefix:
        oldpath = path
        path = f"{prefix}{additional_prefix}{base}{ext}"
        print(f"legacy {oldpath} remapped to {path}")

    return BundledFileRequest(path=path[len(prefix) :], is_sveltekit=is_sveltekit)


def _extract_addon_request(path: str) -> LocalFileRequest | NotFound | None:
    "Catch /_addons references and rewrite them to addons folder."
    prefix = "_addons/"
    if not path.startswith(prefix):
        return None

    addon_path = path[len(prefix) :]

    try:
        manager = aqt.mw.addonManager
    except AttributeError as error:
        if dev_mode:
            print(f"_redirectWebExports: {error}")
        return None

    try:
        addon, sub_path = addon_path.split("/", 1)
    except ValueError:
        return None
    if not addon:
        return None

    pattern = manager.getWebExports(addon)
    if not pattern:
        return None

    if re.fullmatch(pattern, sub_path):
        return LocalFileRequest(
            root=manager.addonsFolder(), path=addon_path, untrusted=False
        )

    return NotFound(message=f"couldn't locate item in add-on folder {path}")


def _extract_request(
    path: str,
) -> LocalFileRequest | BundledFileRequest | DynamicRequest | NotFound:
    if internal := _extract_internal_request(path):
        return internal
    elif addon := _extract_addon_request(path):
        return addon

    if not aqt.mw.col:
        return NotFound(message=f"collection not open, ignore request for {path}")

    path = hooks.media_file_filter(path)
    return LocalFileRequest(root=aqt.mw.col.media.dir(), path=path)


def congrats_info() -> bytes:
    if not aqt.mw.col.sched._is_finished():
        aqt.mw.taskman.run_on_main(lambda: aqt.mw.moveToState("overview"))
    return raw_backend_request("congrats_info")()


def get_deck_configs_for_update() -> bytes:
    return aqt.mw.col._backend.get_deck_configs_for_update_raw(request.data)


def _on_update_deck_configs_success(input: UpdateDeckConfigs) -> None:
    is_compute_all = (
        input.mode == UpdateDeckConfigsMode.UPDATE_DECK_CONFIGS_MODE_COMPUTE_ALL_PARAMS
    )
    if not is_compute_all and isinstance(
        window := aqt.mw.app.activeModalWidget(), DeckOptionsDialog
    ):
        window.reject()


def update_deck_configs() -> bytes:
    # the regular change tracking machinery expects to be started on the main
    # thread and uses a callback on success, so we need to run this op on
    # main, and return immediately from the web request

    input = UpdateDeckConfigs()
    input.ParseFromString(request.data)

    def on_progress(progress: Progress, update: ProgressUpdate) -> None:
        if progress.HasField("compute_memory"):
            val = progress.compute_memory
            update.max = val.total_cards
            update.value = val.current_cards
            update.label = val.label
        elif progress.HasField("compute_params"):
            val2 = progress.compute_params
            # prevent an indeterminate progress bar from appearing at the start of each preset
            update.max = max(val2.total, 1)
            update.value = val2.current
            pct = str(int(val2.current / val2.total * 100) if val2.total > 0 else 0)
            label = tr.deck_config_optimizing_preset(
                current_count=val2.current_preset, total_count=val2.total_presets
            )
            if val2.reviews:
                reviews = tr.deck_config_percent_of_reviews(
                    pct=pct, reviews=val2.reviews
                )
            else:
                reviews = tr.qt_misc_processing()

            update.label = label + "\n" + reviews
        else:
            return
        if update.user_wants_abort:
            update.abort = True

    def handle_on_main() -> None:
        update_deck_configs_op(parent=aqt.mw, input=input).success(
            lambda _: _on_update_deck_configs_success(input)
        ).with_backend_progress(on_progress).run_in_background()

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def get_scheduling_states_with_context() -> bytes:
    return SchedulingStatesWithContext(
        states=aqt.mw.reviewer.get_scheduling_states(),
        context=aqt.mw.reviewer.get_scheduling_context(),
    ).SerializeToString()


def get_deck_browser_content() -> bytes:
    from anki.frontend_pb2 import DeckBrowserContent

    col = aqt.mw.col
    return DeckBrowserContent(
        tree=col.sched.deck_due_tree(),
        current_deck_id=col.decks.get_current_id(),
        studied_today=col.studied_today(),
    ).SerializeToString()


def get_deck_overview_content() -> bytes:
    from anki.frontend_pb2 import DeckOverviewContent

    col = aqt.mw.col
    deck = col.decks.current()
    did = col.decks.get_current_id()
    is_filtered = bool(deck["dyn"])

    counts = list(col.sched.counts())
    if col.v3_scheduler():
        node = col.sched.deck_due_tree(did)
        assert node is not None
        buried_new = node.new_count - counts[0]
        buried_learn = node.learn_count - counts[1]
        buried_review = node.review_count - counts[2]
    else:
        buried_new = buried_learn = buried_review = 0

    # Description, rendered server-side (matches the legacy overview's _desc).
    if is_filtered:
        desc = col.tr.studying_this_is_a_special_deck_for()
        desc += f" {col.tr.studying_cards_will_be_automatically_returned_to()}"
        desc += f" {col.tr.studying_deleting_this_deck_from_the_deck()}"
    else:
        desc = deck.get("desc", "")
        if deck.get("md", False):
            desc = col.render_markdown(desc)
    if desc:
        dyn = "dyn" if is_filtered else ""
        description_html = (
            f'<div class="descfont descmid description {dyn}">{desc}</div>'
        )
    else:
        description_html = ""

    return DeckOverviewContent(
        deck_name=deck["name"],
        is_filtered=is_filtered,
        description_html=description_html,
        shared_from=deck.get("sharedFrom") or 0,
        shared_ver=deck.get("ver") or 0,
        new_count=counts[0],
        learn_count=counts[1],
        review_count=counts[2],
        buried_new=buried_new,
        buried_learn=buried_learn,
        buried_review=buried_review,
        have_buried=col.sched.have_buried(),
    ).SerializeToString()


def get_browse_sidebar() -> bytes:
    from aqt.browser.sidebar.content import build_browse_sidebar

    return build_browse_sidebar(aqt.mw).SerializeToString()


def get_browser_rows() -> bytes:
    from anki.frontend_pb2 import BrowserRows, GetBrowserRowsRequest

    req = GetBrowserRowsRequest()
    req.ParseFromString(request.data)

    rows = BrowserRows()
    rows.rows.extend(aqt.mw.col._backend.browser_row_for_id(id) for id in req.ids)
    return rows.SerializeToString()


def set_scheduling_states() -> bytes:
    states = SetSchedulingStatesRequest()
    states.ParseFromString(request.data)
    aqt.mw.reviewer.set_scheduling_states(states)
    return b""


def import_done() -> bytes:
    def update_window_modality() -> None:
        if window := aqt.mw.app.activeModalWidget():
            from aqt.import_export.import_dialog import ImportDialog

            if isinstance(window, ImportDialog):
                window.hide()
                window.setWindowModality(Qt.WindowModality.NonModal)
                window.show()

    aqt.mw.taskman.run_on_main(update_window_modality)
    return b""


def search_in_browser() -> bytes:
    node = SearchNode()
    node.ParseFromString(request.data)

    def handle_on_main() -> None:
        aqt.dialogs.open("Browser", aqt.mw, search=(node,))

    aqt.mw.taskman.run_on_main(handle_on_main)

    return b""


def change_notetype() -> bytes:
    data = request.data

    def handle_on_main() -> None:
        window = aqt.mw.app.activeModalWidget()
        if isinstance(window, ChangeNotetypeDialog):
            window.save(data)

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def deck_options_require_close() -> bytes:
    def handle_on_main() -> None:
        window = aqt.mw.app.activeModalWidget()
        if isinstance(window, DeckOptionsDialog):
            window.require_close()

    # on certain linux systems, askUser's QMessageBox.question unsets the active window
    # so we wait for the next event loop before querying the next current active window
    aqt.mw.taskman.run_on_main(lambda: QTimer.singleShot(0, handle_on_main))
    return b""


def deck_options_ready() -> bytes:
    def handle_on_main() -> None:
        window = aqt.mw.app.activeModalWidget()
        if isinstance(window, DeckOptionsDialog):
            window.set_ready()

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def get_setting_json(getter: Callable[[str], Any]) -> bytes:
    req = generic_pb2.String()
    req.ParseFromString(request.data)
    value = getter(req.val)
    output = generic_pb2.Json(json=to_json_bytes(value)).SerializeToString()
    return output


def set_setting_json(setter: Callable[[str, Any], Any]) -> bytes:
    req = frontend_pb2.SetSettingJsonRequest()
    req.ParseFromString(request.data)
    setter(req.key, from_json_bytes(req.value_json))
    return b""


def get_profile_config_json() -> bytes:
    assert aqt.mw.pm.profile is not None
    return get_setting_json(aqt.mw.pm.profile.get)


def set_profile_config_json() -> bytes:
    assert aqt.mw.pm.profile is not None
    return set_setting_json(aqt.mw.pm.profile.__setitem__)


def get_meta_json() -> bytes:
    return get_setting_json(aqt.mw.pm.meta.get)


def set_meta_json() -> bytes:
    return set_setting_json(aqt.mw.pm.meta.__setitem__)


def get_config_json() -> bytes:
    try:
        return get_setting_json(aqt.mw.col.conf.get_immutable)
    except KeyError:
        return generic_pb2.Json(json=b"null").SerializeToString()


def set_config_json() -> bytes:
    return set_setting_json(aqt.mw.col.set_config)


def convert_pasted_image() -> bytes:
    req = frontend_pb2.ConvertPastedImageRequest()
    req.ParseFromString(request.data)
    image = QImage.fromData(req.data)
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.ReadWrite)
    if req.ext == "png":
        quality = 50
    else:
        quality = 80
    image.save(buffer, req.ext, quality)
    buffer.reset()
    data = bytes(cast(bytes, buffer.readAll()))
    return frontend_pb2.ConvertPastedImageResponse(data=data).SerializeToString()


AsyncRequestReturnType = TypeVar("AsyncRequestReturnType")


class AsyncRequestHandler(Generic[AsyncRequestReturnType]):
    def __init__(self, callback: Callable[[AsyncRequestHandler], None]) -> None:
        self.callback = callback
        self.loop = asyncio.get_running_loop()
        self.future = self.loop.create_future()

    def run(self) -> None:
        aqt.mw.taskman.run_on_main(lambda: self.callback(self))

    def set_result(self, result: AsyncRequestReturnType) -> None:
        self.loop.call_soon_threadsafe(self.future.set_result, result)

    async def get_result(self) -> AsyncRequestReturnType:
        return await self.future


async def open_file_picker() -> bytes:
    req = frontend_pb2.openFilePickerRequest()
    req.ParseFromString(request.data)

    def callback(request_handler: AsyncRequestHandler) -> None:
        from aqt.utils import getFile

        def cb(filename: str | None) -> None:
            request_handler.set_result(filename)

        window = aqt.mw.app.activeWindow()
        assert window is not None
        getFile(
            parent=window,
            title=req.title,
            cb=cast(Callable[[Any], None], cb),
            filter=f"{req.filter_description} ({' '.join(f'*.{ext}' for ext in req.extensions)})",
            key=req.key,
        )

    request_handler: AsyncRequestHandler[str | None] = AsyncRequestHandler(callback)
    request_handler.run()
    filename = await request_handler.get_result()

    return generic_pb2.String(val=filename if filename else "").SerializeToString()


def open_media() -> bytes:
    from aqt.utils import openFolder

    req = generic_pb2.String()
    req.ParseFromString(request.data)
    path = os.path.join(aqt.mw.col.media.dir(), req.val)
    aqt.mw.taskman.run_on_main(lambda: openFolder(path))

    return b""


def show_in_media_folder() -> bytes:
    from aqt.utils import show_in_folder

    req = generic_pb2.String()
    req.ParseFromString(request.data)
    path = os.path.join(aqt.mw.col.media.dir(), req.val)
    aqt.mw.taskman.run_on_main(lambda: show_in_folder(path))

    return b""


async def record_audio() -> bytes:
    def callback(request_handler: AsyncRequestHandler) -> None:
        from aqt.sound import record_audio

        def cb(path: str | None) -> None:
            request_handler.set_result(path)

        window = aqt.mw.app.activeWindow()
        assert window is not None
        record_audio(window, aqt.mw, True, cb)

    request_handler: AsyncRequestHandler[str | None] = AsyncRequestHandler(callback)
    request_handler.run()
    path = await request_handler.get_result()

    return generic_pb2.String(val=path if path else "").SerializeToString()


def read_clipboard() -> bytes:
    req = frontend_pb2.ReadClipboardRequest()
    req.ParseFromString(request.data)
    data = {}
    clipboard = aqt.mw.app.clipboard()
    assert clipboard is not None
    mime_data = clipboard.mimeData(QClipboard.Mode.Clipboard)
    assert mime_data is not None
    for type in req.types:
        data[type] = bytes(mime_data.data(type))  # type: ignore

    return frontend_pb2.ReadClipboardResponse(data=data).SerializeToString()


def write_clipboard() -> bytes:
    req = frontend_pb2.WriteClipboardRequest()
    req.ParseFromString(request.data)
    clipboard = aqt.mw.app.clipboard()
    assert clipboard is not None
    mime_data = clipboard.mimeData(QClipboard.Mode.Clipboard)
    assert mime_data is not None
    for type, data in req.data.items():
        mime_data.setData(type, data)
    return b""


def close_add_cards() -> bytes:
    req = generic_pb2.Bool()
    req.ParseFromString(request.data)

    def handle_on_main() -> None:
        from aqt.addcards import NewAddCards

        window = aqt.mw.app.activeWindow()
        if isinstance(window, NewAddCards):
            window._close_if_user_wants_to_discard_changes(req.val)

    aqt.mw.taskman.run_on_main(lambda: QTimer.singleShot(0, handle_on_main))
    return b""


def close_edit_current() -> bytes:
    def handle_on_main() -> None:
        from aqt.editcurrent import NewEditCurrent

        window = aqt.mw.app.activeWindow()
        if isinstance(window, NewEditCurrent):
            window.close()

    aqt.mw.taskman.run_on_main(lambda: QTimer.singleShot(0, handle_on_main))
    return b""


def open_link() -> bytes:
    req = generic_pb2.String()
    req.ParseFromString(request.data)
    url = req.val
    aqt.mw.taskman.run_on_main(lambda: openLink(url))
    return b""


async def ask_user() -> bytes:
    req = frontend_pb2.AskUserRequest()
    req.ParseFromString(request.data)

    def callback(request_handler: AsyncRequestHandler) -> None:
        kwargs: dict[str, Any] = dict(text=req.text)
        if req.HasField("help"):
            help_arg: Any
            if req.help.WhichOneof("value") == "help_page":
                help_arg = req.help.help_page
            else:
                help_arg = req.help.help_link
            kwargs["help"] = help_arg
        if req.HasField("title"):
            kwargs["title"] = req.title
        if req.HasField("default_no"):
            kwargs["defaultno"] = req.default_no
        answer = askUser(**kwargs)
        request_handler.set_result(answer)

    request_handler: AsyncRequestHandler[bool] = AsyncRequestHandler(callback)
    request_handler.run()
    answer = await request_handler.get_result()

    return generic_pb2.Bool(val=answer).SerializeToString()


async def show_message_box() -> bytes:
    req = frontend_pb2.ShowMessageBoxRequest()
    req.ParseFromString(request.data)

    def callback(request_handler: AsyncRequestHandler) -> None:
        kwargs: dict[str, Any] = dict(text=req.text)
        if req.type == frontend_pb2.MessageBoxType.INFO:
            icon = QMessageBox.Icon.Information
        elif req.type == frontend_pb2.MessageBoxType.WARNING:
            icon = QMessageBox.Icon.Warning
        elif req.type == frontend_pb2.MessageBoxType.CRITICAL:
            icon = QMessageBox.Icon.Critical
        kwargs["icon"] = icon
        if req.HasField("help"):
            help_arg: Any
            if req.help.WhichOneof("value") == "help_page":
                help_arg = req.help.help_page
            else:
                help_arg = req.help.help_link
            kwargs["help"] = help_arg
        if req.HasField("title"):
            kwargs["title"] = req.title
        if req.HasField("text_format"):
            kwargs["text_format"] = req.text_format
        show_info(**kwargs)
        request_handler.set_result(True)

    request_handler: AsyncRequestHandler[bool] = AsyncRequestHandler(callback)
    request_handler.run()
    answer = await request_handler.get_result()

    return generic_pb2.Bool(val=answer).SerializeToString()


def open_fields_dialog() -> bytes:
    def handle_on_main() -> None:
        from aqt.editor import NewEditor

        window = aqt.mw.app.activeWindow()
        assert window is not None
        if hasattr(window, "editor") and isinstance(window.editor, NewEditor):
            window.editor.onFields()

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def open_cards_dialog() -> bytes:
    def handle_on_main() -> None:
        from aqt.editor import NewEditor

        window = aqt.mw.app.activeWindow()
        assert window is not None
        if hasattr(window, "editor") and isinstance(window.editor, NewEditor):
            window.editor.onCardLayout()

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def save_custom_colours() -> bytes:
    colors = [
        QColorDialog.customColor(i).name(QColor.NameFormat.HexRgb)
        for i in range(QColorDialog.customCount())
    ]
    aqt.mw.col.set_config("customColorPickerPalette", colors)
    return b""


# Add-on manager handlers
# All mutations run on the Qt main thread via run_on_main so they can interact
# with the existing AddonManager, progress dialogs, and Qt file pickers.


def get_addons() -> bytes:
    from anki.addons_pb2 import Addon, AddonList
    from anki.utils import int_version_to_str
    from aqt.addons import _current_version

    mgr = aqt.mw.addonManager
    addons = []
    for meta in mgr.all_addon_meta():
        compat_summary = ""
        if not meta.compatible():
            min_v = meta.min_version
            if min_v and min_v > _current_version:
                compat_summary = f"Anki >= {int_version_to_str(min_v)}"
            else:
                max_v = abs(meta.max_version)
                compat_summary = f"Anki <= {int_version_to_str(max_v)}"
        addons.append(
            Addon(
                dir_name=meta.dir_name,
                human_name=meta.human_name(),
                enabled=meta.enabled,
                compatible=meta.compatible(),
                compat_summary=compat_summary,
                has_config=mgr.addonConfigDefaults(meta.dir_name) is not None,
                page_url=meta.page() or "",
                human_version=meta.human_version or "",
            )
        )
    return AddonList(addons=addons).SerializeToString()


def set_addon_enabled() -> bytes:
    from anki.addons_pb2 import SetAddonEnabledRequest

    inp = SetAddonEnabledRequest()
    inp.ParseFromString(request.data)

    def handle_on_main() -> None:
        from aqt.addons_dialog import AddonsWebDialog

        aqt.mw.addonManager.toggleEnabled(inp.dir_name, enable=inp.enabled)
        window = aqt.mw.app.activeModalWidget()
        if isinstance(window, AddonsWebDialog):
            window._require_restart = True
            window.refresh_list()

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def delete_addon() -> bytes:
    from anki.addons_pb2 import AddonId
    from aqt import gui_hooks

    inp = AddonId()
    inp.ParseFromString(request.data)

    def handle_on_main() -> None:
        from typing import cast

        from aqt.addons import AddonsDialog
        from aqt.addons_dialog import AddonsWebDialog

        mgr = aqt.mw.addonManager
        window = aqt.mw.app.activeModalWidget()
        if not isinstance(window, AddonsWebDialog):
            return
        # Cast so existing hook signatures remain satisfied; AddonsWebDialog has .mgr
        gui_hooks.addons_dialog_will_delete_addons(
            cast(AddonsDialog, window), [inp.dir_name]
        )
        mgr.deleteAddon(inp.dir_name)
        window._require_restart = True
        window.refresh_list()

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def open_addon_folder() -> bytes:
    from anki.addons_pb2 import AddonId

    inp = AddonId()
    inp.ParseFromString(request.data)

    def handle_on_main() -> None:
        from aqt.utils import openFolder

        mgr = aqt.mw.addonManager
        path = mgr.addonsFolder(inp.dir_name) if inp.dir_name else mgr.addonsFolder()
        openFolder(path)

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def open_addon_page() -> bytes:
    from anki.addons_pb2 import AddonId

    inp = AddonId()
    inp.ParseFromString(request.data)

    def handle_on_main() -> None:
        from aqt.utils import openLink

        meta = aqt.mw.addonManager.addon_meta(inp.dir_name)
        url = meta.page()
        if url:
            openLink(url)

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def _addon_form_properties(schema: Any) -> tuple[dict, bool] | None:
    """Extract the auto-form field map from a parsed config.schema.json.

    Returns ``(properties, validatable)`` or ``None`` if the schema can't drive a
    form. ``validatable`` is True only for a standard JSON Schema (with a
    ``properties`` map), where the file is also a usable jsonschema validator.

    Two layouts are supported:
    - Standard JSON Schema: ``{"properties": {key: {...}}, ...}``.
    - Flat descriptor map: top-level keys (minus ``$``-prefixed meta keys) each
      map to a VSCode-style field descriptor ``{"type": ..., ...}``.
    """
    if not isinstance(schema, dict):
        return None
    props = schema.get("properties")
    if isinstance(props, dict) and props:
        return props, True
    fields = {k: v for k, v in schema.items() if not k.startswith("$")}
    if fields and all(isinstance(v, dict) and "type" in v for v in fields.values()):
        return fields, False
    return None


def open_addon_config() -> bytes:
    from anki.addons_pb2 import AddonId

    inp = AddonId()
    inp.ParseFromString(request.data)

    def handle_on_main() -> None:
        import json
        import os
        from typing import cast

        from aqt.addons import AddonsDialog, ConfigEditor
        from aqt.addons_dialog import AddonConfigDialog, AddonsWebDialog
        from aqt.utils import tooltip

        mgr = aqt.mw.addonManager
        window = aqt.mw.app.activeModalWidget()
        if not isinstance(window, AddonsWebDialog):
            return
        act = mgr.configAction(inp.dir_name)
        if act is not None:
            ret = act()
            if ret is not False:
                return
        conf = mgr.getConfig(inp.dir_name)
        if conf is None:
            tooltip(tr.addons_addon_has_no_configuration())
            return
        # Use the auto-generated Svelte form when config.schema.json describes the
        # fields (either a standard JSON Schema with "properties", or a flat
        # descriptor map). Otherwise fall back to the raw-JSON ConfigEditor.
        use_schema_form = False
        schema_path = mgr._addon_schema_path(inp.dir_name)
        if os.path.exists(schema_path):
            try:
                with open(schema_path, encoding="utf-8") as f:
                    schema = json.load(f)
                if _addon_form_properties(schema) is not None:
                    use_schema_form = True
            except Exception:
                pass
        if use_schema_form:
            AddonConfigDialog(mgr, inp.dir_name)
        else:
            # Cast so ConfigEditor's AddonsDialog annotation is satisfied;
            # AddonsWebDialog has .mgr
            ConfigEditor(cast(AddonsDialog, window), inp.dir_name, conf)

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def get_addon_config() -> bytes:
    from anki.addons_pb2 import AddonConfigInfo

    mgr = aqt.mw.addonManager

    def resolve() -> AddonConfigInfo:
        import json

        from aqt.addons_dialog import AddonConfigDialog

        window = aqt.mw.app.activeModalWidget()
        if not isinstance(window, AddonConfigDialog):
            raise Exception("addon config dialog not open")
        dir_name = window.dir_name
        help_html = mgr.addonConfigHelp(dir_name) or ""

        with open(mgr._addon_schema_path(dir_name), encoding="utf-8") as f:
            schema = json.load(f)
        form = _addon_form_properties(schema)
        if form is None:
            raise Exception("addon schema does not describe a config form")
        properties, _validatable = form

        # config.json supplies the field defaults; getConfig() merges meta.json
        # user overrides on top. A descriptor's own "default" is the fallback for
        # any field missing from config.json.
        defaults_raw = mgr.addonConfigDefaults(dir_name) or {}
        config_raw = mgr.getConfig(dir_name) or {}
        defaults: dict = {}
        values: dict = {}
        for key, desc in properties.items():
            if key in defaults_raw:
                defaults[key] = defaults_raw[key]
            elif isinstance(desc, dict) and "default" in desc:
                defaults[key] = desc["default"]
            else:
                defaults[key] = None
            values[key] = config_raw.get(key, defaults[key])

        title = (schema.get("title") if isinstance(schema, dict) else None) or (
            mgr.addonName(dir_name)
        )
        return AddonConfigInfo(
            title=title,
            schema_json=json.dumps(properties),
            config_json=json.dumps(values),
            defaults_json=json.dumps(defaults),
            help_html=help_html,
        )

    import concurrent.futures

    future: concurrent.futures.Future[AddonConfigInfo] = concurrent.futures.Future()

    def on_main() -> None:
        try:
            future.set_result(resolve())
        except Exception as exc:
            future.set_exception(exc)

    aqt.mw.taskman.run_on_main(on_main)
    result = future.result(timeout=10)
    return result.SerializeToString()


def set_addon_config() -> bytes:
    from anki.addons_pb2 import SetAddonConfigRequest

    inp = SetAddonConfigRequest()
    inp.ParseFromString(request.data)

    def handle_on_main() -> None:
        import json

        from aqt import gui_hooks
        from aqt.addons_dialog import AddonConfigDialog

        window = aqt.mw.app.activeModalWidget()
        if not isinstance(window, AddonConfigDialog):
            return
        dir_name = window.dir_name
        mgr = aqt.mw.addonManager
        # Mirror ConfigEditor.accept(): run the will_update_json hook,
        # validate, and persist — so all add-on save hooks keep firing.
        txt = gui_hooks.addon_config_editor_will_update_json(inp.config_json, dir_name)
        new_conf = json.loads(txt)
        if not isinstance(new_conf, dict):
            raise Exception("Config must be a JSON object")
        # Only validate when config.schema.json is a standard JSON Schema. A flat
        # descriptor map isn't a validator for the saved flat values.
        schema = mgr._addon_schema(dir_name)
        form = _addon_form_properties(schema)
        if form is not None and form[1]:
            import jsonschema

            jsonschema.validate(new_conf, schema)
        old_conf = mgr.getConfig(dir_name) or {}
        if new_conf != old_conf:
            mgr.writeConfig(dir_name, new_conf)
            updated = mgr.configUpdatedAction(dir_name)
            if updated is not None:
                updated(new_conf)

    import concurrent.futures

    future: concurrent.futures.Future[None] = concurrent.futures.Future()

    def on_main() -> None:
        try:
            handle_on_main()
            future.set_result(None)
        except Exception as exc:
            future.set_exception(exc)

    aqt.mw.taskman.run_on_main(on_main)
    future.result(timeout=10)
    return b""


def close_addon_config() -> bytes:
    def handle_on_main() -> None:
        from aqt.addons_dialog import AddonConfigDialog

        window = aqt.mw.app.activeModalWidget()
        if isinstance(window, AddonConfigDialog):
            window.reject()

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def install_addons_from_files() -> bytes:
    def handle_on_main() -> None:
        from aqt.addons import installAddonPackages
        from aqt.addons_dialog import AddonsWebDialog
        from aqt.utils import getFile

        window = aqt.mw.app.activeModalWidget()
        if not isinstance(window, AddonsWebDialog):
            return
        paths = getFile(
            window,
            tr.addons_install_anki_addon(),
            cb=None,
            filter=tr.addons_packaged_anki_addon() + " (*.ankiaddon *.zip)",
            key="addons",
            multi=True,
        )
        if paths:
            installAddonPackages(
                aqt.mw.addonManager, list(paths), parent=window, force_enable=True
            )
            window.refresh_list()

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def get_addons_from_anki_web() -> bytes:
    def handle_on_main() -> None:
        from typing import cast

        from aqt.addons import (
            AddonsDialog,
            GetAddons,
            download_addons,
            show_log_to_user,
        )
        from aqt.addons_dialog import AddonsWebDialog

        window = aqt.mw.app.activeModalWidget()
        if not isinstance(window, AddonsWebDialog):
            return
        # Cast so GetAddons's AddonsDialog annotation is satisfied; AddonsWebDialog has .mgr
        obj = GetAddons(cast(AddonsDialog, window))
        if not obj.ids:
            return

        def after_downloading(log: list) -> None:
            window.refresh_list()
            show_log_to_user(window, log)

        download_addons(window, aqt.mw.addonManager, obj.ids, after_downloading)

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def check_for_addon_updates() -> bytes:
    def handle_on_main() -> None:
        from aqt.addons import check_and_prompt_for_updates, show_log_to_user
        from aqt.addons_dialog import AddonsWebDialog

        window = aqt.mw.app.activeModalWidget()
        if not isinstance(window, AddonsWebDialog):
            return

        def after_downloading(log: list) -> None:
            window.refresh_list()
            show_log_to_user(window, log)

        check_and_prompt_for_updates(window, aqt.mw.addonManager, after_downloading)

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


def addons_ready() -> bytes:
    def handle_on_main() -> None:
        from aqt.addons_dialog import AddonsWebDialog

        window = aqt.mw.app.activeModalWidget()
        if isinstance(window, AddonsWebDialog):
            window.set_ready()

    aqt.mw.taskman.run_on_main(handle_on_main)
    return b""


post_handler_list = [
    congrats_info,
    get_deck_configs_for_update,
    update_deck_configs,
    get_scheduling_states_with_context,
    set_scheduling_states,
    get_deck_browser_content,
    get_deck_overview_content,
    get_browse_sidebar,
    get_browser_rows,
    change_notetype,
    import_done,
    search_in_browser,
    deck_options_require_close,
    deck_options_ready,
    get_profile_config_json,
    set_profile_config_json,
    get_meta_json,
    set_meta_json,
    get_config_json,
    convert_pasted_image,
    open_file_picker,
    open_media,
    show_in_media_folder,
    record_audio,
    read_clipboard,
    write_clipboard,
    close_add_cards,
    close_edit_current,
    open_link,
    ask_user,
    show_message_box,
    open_fields_dialog,
    open_cards_dialog,
    save_custom_colours,
    # AddonsService
    get_addons,
    set_addon_enabled,
    delete_addon,
    open_addon_folder,
    open_addon_page,
    open_addon_config,
    install_addons_from_files,
    get_addons_from_anki_web,
    check_for_addon_updates,
    addons_ready,
    # AddonConfigService (schema-driven config editor)
    get_addon_config,
    set_addon_config,
    close_addon_config,
]


exposed_backend_list = [
    # CollectionService
    "latest_progress",
    "get_custom_colours",
    # DeckService
    "get_deck_names",
    "get_deck",
    "update_deck",
    "set_deck_collapsed",
    "reparent_decks",
    # ConfigService
    "set_config_bool",
    # SearchService
    "build_search_string",
    "search_cards",
    "search_notes",
    "join_search_nodes",
    "all_browser_columns",
    "set_active_browser_columns",
    "get_deck",
    # I18nService
    "i18n_resources",
    # ImportExportService
    "get_csv_metadata",
    "get_import_anki_package_presets",
    "import_csv",
    "import_anki_package",
    "import_json_file",
    "import_json_string",
    # NotesService
    "get_field_names",
    "get_note",
    "new_note",
    "note_fields_check",
    "defaults_for_adding",
    "default_deck_for_notetype",
    "add_note",
    "update_notes",
    "update_notetype",
    # NotetypesService
    "get_notetype",
    "get_notetype_names",
    "get_change_notetype_info",
    "get_cloze_field_ords",
    # StatsService
    "card_stats",
    "get_review_logs",
    "graphs",
    "get_graph_preferences",
    "set_graph_preferences",
    # TagsService
    "complete_tag",
    # ImageOcclusionService
    "get_image_for_occlusion",
    "add_image_occlusion_note",
    "get_image_occlusion_note",
    "update_image_occlusion_note",
    "get_image_occlusion_fields",
    # SchedulerService
    "compute_fsrs_params",
    "compute_optimal_retention",
    "set_wants_abort",
    "evaluate_params_legacy",
    "get_optimal_retention_parameters",
    "simulate_fsrs_review",
    "simulate_fsrs_workload",
    # DeckConfigService
    "get_ignored_before_count",
    "get_retention_workload",
    # CardRenderingService
    "encode_iri_paths",
    "decode_iri_paths",
    "html_to_text_line",
    # ConfigService
    "set_config_json",
    "get_config_bool",
    # MediaService
    "add_media_file",
    "add_media_from_path",
    "add_media_from_url",
    "get_absolute_media_path",
    "extract_media_files",
    # CardsService
    "get_card",
]


def raw_backend_request(endpoint: str) -> Callable[[], bytes]:
    # check for key at startup
    from anki._backend import RustBackend

    assert hasattr(RustBackend, f"{endpoint}_raw")

    def wrapped() -> bytes:
        output = getattr(aqt.mw.col._backend, f"{endpoint}_raw")(request.data)
        op_changes_type = int(request.headers.get("Anki-Op-Changes", "0"))
        if op_changes_type:
            op_message_types = (OpChanges, OpChangesOnly, NestedOpChanges)
            try:
                response = op_message_types[op_changes_type - 1]()
                response.ParseFromString(output)
                changes: Any = response
                for _ in range(op_changes_type - 1):
                    changes = changes.changes
            except IndexError:
                raise ValueError(f"unhandled op changes level: {op_changes_type}")

            def handle_on_main() -> None:
                handler = aqt.mw.app.activeWindow()
                on_op_finished(aqt.mw, changes, handler)

            aqt.mw.taskman.run_on_main(handle_on_main)

        return output

    return wrapped


# all methods in here require a collection
post_handlers = {
    stringcase.camelcase(handler.__name__): handler for handler in post_handler_list
} | {
    stringcase.camelcase(handler): raw_backend_request(handler)
    for handler in exposed_backend_list
}


def _extract_collection_post_request(path: str) -> DynamicRequest | NotFound:
    if not aqt.mw.col:
        return NotFound(message=f"collection not open, ignore request for {path}")
    if handler := post_handlers.get(path):
        # convert bytes/None into response
        def wrapped() -> Response:
            try:
                import inspect

                if inspect.iscoroutinefunction(handler):
                    data = asyncio.run(handler())
                else:
                    result = handler()
                    data = result
                if data:
                    response = flask.make_response(data)
                    response.headers["Content-Type"] = "application/binary"
                else:
                    response = _text_response(HTTPStatus.NO_CONTENT, "")
            except Exception as exc:
                print(traceback.format_exc())
                response = _text_response(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return response

        return wrapped
    else:
        return NotFound(message=f"{path} not found")


# Endpoints reachable from webview kinds without full API access (e.g. the
# shared main webview, which also hosts the reviewer and must not expose the
# full backend to note field HTML/third-party JS).
MAIN_WEBVIEW_API_WHITELIST = (
    "/_anki/getSchedulingStatesWithContext",
    "/_anki/setSchedulingStates",
    "/_anki/i18nResources",
    "/_anki/congratsInfo",
    "/_anki/getDeckBrowserContent",
    "/_anki/getDeckOverviewContent",
    "/_anki/setDeckCollapsed",
    "/_anki/reparentDecks",
    "/_anki/getNotetypeNames",
    "/_anki/getNotetype",
    "/_anki/getBrowseSidebar",
    "/_anki/getBrowserRows",
    "/_anki/buildSearchString",
    "/_anki/searchCards",
    "/_anki/searchNotes",
    "/_anki/joinSearchNodes",
    "/_anki/allBrowserColumns",
    "/_anki/setActiveBrowserColumns",
    "/_anki/setConfigBool",
    "/_anki/graphs",
    "/_anki/getGraphPreferences",
    "/_anki/setGraphPreferences",
)


def _check_dynamic_request_permissions():
    if request.method == "GET":
        return

    def warn() -> None:
        show_warning(
            "Unexpected API access. Please report this message on the Anki forums."
        )

    # check content type header to ensure this isn't an opaque request from another origin
    if request.headers["Content-type"] != "application/binary":
        aqt.mw.taskman.run_on_main(warn)
        abort(403)

    # does page have access to entire API?
    if _have_api_access():
        return

    # whitelisted API endpoints for reviewer/previewer
    if request.path in MAIN_WEBVIEW_API_WHITELIST:
        pass
    else:
        # other legacy pages may contain third-party JS, so we do not
        # allow them to access our API
        aqt.mw.taskman.run_on_main(warn)
        abort(403)


def _handle_dynamic_request(req: DynamicRequest) -> Response:
    _check_dynamic_request_permissions()
    try:
        return req()
    except Exception as e:
        return _text_response(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))


def legacy_page_data() -> Response:
    id = int(request.args["id"])
    page = aqt.mw.mediaServer.get_page(id)
    if page:
        response = Response(page.html, mimetype="text/html")
        # Prevent JS in field content from being executed in the editor, as it would
        # have access to our internal API, and is a security risk.
        if page.context == PageContext.EDITOR:
            response.headers["Content-Security-Policy"] = (
                _legacy_editor_content_security_policy(aqt.mw.mediaServer.getPort())
            )
        return response
    else:
        return _text_response(HTTPStatus.NOT_FOUND, "page not found")


_APIKEY = secrets.token_urlsafe(32)


def _have_api_access() -> bool:
    return (
        request.headers.get("Authorization") == f"Bearer {_APIKEY}"
        or os.environ.get("ANKI_API_HOST") == "0.0.0.0"
    )


# this currently only handles a single method; in the future, idempotent
# requests like i18nResources should probably be moved here
def _extract_dynamic_get_request(path: str) -> DynamicRequest | None:
    if path == "legacyPageData":
        return legacy_page_data
    else:
        return None
