# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from __future__ import annotations

import json
import os
import re
import time
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

import aqt.main
from anki.collection import (
    DeckIdLimit,
    ExportAnkiPackageOptions,
    ExportLimit,
    NoteIdsLimit,
    Progress,
)
from anki.decks import DeckId
from anki.notes import NoteId
from aqt import gui_hooks
from aqt.errors import show_exception
from aqt.operations import QueryOp
from aqt.progress import ProgressUpdate
from aqt.qt import *
from aqt.utils import (
    checkInvalidFilename,
    disable_help_button,
    getSaveFile,
    restoreGeom,
    saveGeom,
    showWarning,
    tooltip,
    tr,
)
from aqt.webview import AnkiWebView, AnkiWebViewKind


class ExportDialog(QDialog):
    """Format/options picker for exporting a collection, deck, or note selection.

    Renders a Svelte page inside an ``AnkiWebView``. The native save-file
    dialog and the actual export (via the ``Exporter`` subclasses below,
    unchanged) stay in Python; the page only collects the chosen format and
    options and sends them over the bridge as JSON.
    """

    TITLE = "export"
    silentlyClose = True

    def __init__(
        self,
        mw: aqt.main.AnkiQt,
        did: DeckId | None = None,
        nids: Sequence[NoteId] | None = None,
        parent: QWidget | None = None,
    ):
        QDialog.__init__(self, parent or mw, Qt.WindowType.Window)
        self.mw = mw
        self.did = did
        self.nids = nids
        disable_help_button(self)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.exporter_classes: list[type[Exporter]] = [
            ApkgExporter,
            ColpkgExporter,
            NoteCsvExporter,
            CardCsvExporter,
        ]
        gui_hooks.exporters_list_did_initialize(self.exporter_classes)

        self.setWindowTitle(tr.actions_export())
        self.setMinimumWidth(400)
        restoreGeom(self, self.TITLE, default_size=(500, 500))

        self.web = AnkiWebView(kind=AnkiWebViewKind.EXPORT)
        self.web.set_bridge_command(self._on_bridge_cmd, self)
        params = []
        if self.did is not None:
            params.append(f"did={self.did}")
        if self.nids is not None:
            params.append("nids=" + ",".join(str(n) for n in self.nids))
        query = f"?{'&'.join(params)}" if params else ""
        self.web.load_sveltekit_page(f"export{query}")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web)
        self.setLayout(layout)
        self.open()

    def _on_bridge_cmd(self, cmd: str) -> None:
        if cmd == "close":
            # defer so the webview isn't torn down from inside its own callback
            QTimer.singleShot(0, self.close)
        elif cmd.startswith("export:"):
            _, payload = cmd.split(":", 1)
            if self._export(json.loads(payload)):
                QTimer.singleShot(0, self.close)

    def _export(self, payload: dict) -> bool:
        self.exporter = self.exporter_classes[payload["formatId"]]()

        if not (out_path := self.get_out_path(payload)):
            return False

        limit: ExportLimit | None = None
        if self.nids:
            limit = NoteIdsLimit(self.nids)
        elif deck_id := payload.get("deckId"):
            limit = DeckIdLimit(DeckId(int(deck_id)))

        options = ExportOptions(
            out_path=out_path,
            include_scheduling=payload["includeScheduling"],
            include_deck_configs=payload["includeDeckConfigs"],
            include_media=payload["includeMedia"],
            include_tags=payload["includeTags"],
            include_html=payload["includeHtml"],
            include_deck=payload["includeDeck"],
            include_notetype=payload["includeNotetype"],
            include_guid=payload["includeGuid"],
            legacy_support=payload["legacySupport"],
            limit=limit,
            parent=self.parentWidget(),
        )
        self.exporter.export(self.mw, options)
        return True

    def get_out_path(self, payload: dict) -> str | None:
        filename = self.filename(payload)
        while True:
            path = getSaveFile(
                parent=self,
                title=tr.actions_export(),
                dir_description="export",
                key=self.exporter.name(),
                ext="." + self.exporter.extension,
                fname=filename,
            )
            if not path:
                return None
            if checkInvalidFilename(os.path.basename(path), dirsep=False):
                continue
            path = os.path.normpath(path)
            if os.path.commonprefix([self.mw.pm.base, path]) == self.mw.pm.base:
                showWarning("Please choose a different export location.")
                continue
            break
        return path

    def filename(self, payload: dict) -> str:
        if self.exporter.show_deck_list:
            deck_id = payload.get("deckId")
            if deck_id and (deck := self.mw.col.decks.get(DeckId(int(deck_id)))):
                deck_name = deck["name"]
            elif self.nids is not None:
                deck_name = tr.exporting_selected_notes()
            else:
                deck_name = tr.exporting_all_decks()
            stem = re.sub('[\\\\/?<>:*|"^]', "_", deck_name)
        else:
            time_str = time.strftime("%Y-%m-%d@%H-%M-%S", time.localtime(time.time()))
            stem = f"{tr.exporting_collection()}-{time_str}"
        return f"{stem}.{self.exporter.extension}"

    def reject(self) -> None:
        self.web.cleanup()
        self.web = None  # type: ignore
        saveGeom(self, self.TITLE)
        QDialog.reject(self)


@dataclass
class ExportOptions:
    out_path: str
    include_scheduling: bool
    include_deck_configs: bool
    include_media: bool
    include_tags: bool
    include_html: bool
    include_deck: bool
    include_notetype: bool
    include_guid: bool
    legacy_support: bool
    limit: ExportLimit | None
    parent: QWidget | None = None


def _export_parent(mw: aqt.main.AnkiQt, options: ExportOptions) -> QWidget:
    return options.parent or mw


def _show_exported_tooltip(
    mw: aqt.main.AnkiQt, options: ExportOptions, message: str
) -> None:
    tooltip(message, parent=_export_parent(mw, options))


class Exporter(ABC):
    extension: str
    show_deck_list = False
    show_include_scheduling = False
    show_include_deck_configs = False
    show_include_media = False
    show_include_tags = False
    show_include_html = False
    show_legacy_support = False
    show_include_deck = False
    show_include_notetype = False
    show_include_guid = False

    @abstractmethod
    def export(self, mw: aqt.main.AnkiQt, options: ExportOptions) -> None:
        pass

    @staticmethod
    @abstractmethod
    def name() -> str:
        pass


class ColpkgExporter(Exporter):
    extension = "colpkg"
    show_include_media = True
    show_legacy_support = True

    @staticmethod
    def name() -> str:
        return tr.exporting_anki_collection_package()

    def export(self, mw: aqt.main.AnkiQt, options: ExportOptions) -> None:
        options = gui_hooks.exporter_will_export(options, self)
        parent = _export_parent(mw, options)

        def on_success(_: None) -> None:
            mw.reopen()
            gui_hooks.exporter_did_export(options, self)
            _show_exported_tooltip(mw, options, tr.exporting_collection_exported())

        def on_failure(exception: Exception) -> None:
            mw.reopen()
            show_exception(parent=parent, exception=exception)

        gui_hooks.collection_will_temporarily_close(mw.col)
        QueryOp(
            parent=parent,
            op=lambda col: col.export_collection_package(
                options.out_path,
                include_media=options.include_media,
                legacy=options.legacy_support,
            ),
            success=on_success,
        ).with_backend_progress(export_progress_update).failure(
            on_failure
        ).run_in_background()


class ApkgExporter(Exporter):
    extension = "apkg"
    show_deck_list = True
    show_include_scheduling = True
    show_include_deck_configs = True
    show_include_media = True
    show_legacy_support = True

    @staticmethod
    def name() -> str:
        return tr.exporting_anki_deck_package()

    def export(self, mw: aqt.main.AnkiQt, options: ExportOptions) -> None:
        options = gui_hooks.exporter_will_export(options, self)
        parent = _export_parent(mw, options)

        def on_success(count: int) -> None:
            gui_hooks.exporter_did_export(options, self)
            _show_exported_tooltip(mw, options, tr.exporting_note_exported(count=count))

        QueryOp(
            parent=parent,
            op=lambda col: col.export_anki_package(
                out_path=options.out_path,
                limit=options.limit,
                options=ExportAnkiPackageOptions(
                    with_scheduling=options.include_scheduling,
                    with_deck_configs=options.include_deck_configs,
                    with_media=options.include_media,
                    legacy=options.legacy_support,
                ),
            ),
            success=on_success,
        ).with_backend_progress(export_progress_update).run_in_background()


class NoteCsvExporter(Exporter):
    extension = "txt"
    show_deck_list = True
    show_include_html = True
    show_include_tags = True
    show_include_deck = True
    show_include_notetype = True
    show_include_guid = True

    @staticmethod
    def name() -> str:
        return tr.exporting_notes_in_plain_text()

    def export(self, mw: aqt.main.AnkiQt, options: ExportOptions) -> None:
        options = gui_hooks.exporter_will_export(options, self)
        parent = _export_parent(mw, options)

        def on_success(count: int) -> None:
            gui_hooks.exporter_did_export(options, self)
            _show_exported_tooltip(mw, options, tr.exporting_note_exported(count=count))

        QueryOp(
            parent=parent,
            op=lambda col: col.export_note_csv(
                out_path=options.out_path,
                limit=options.limit,
                with_html=options.include_html,
                with_tags=options.include_tags,
                with_deck=options.include_deck,
                with_notetype=options.include_notetype,
                with_guid=options.include_guid,
            ),
            success=on_success,
        ).with_backend_progress(export_progress_update).run_in_background()


class CardCsvExporter(Exporter):
    extension = "txt"
    show_deck_list = True
    show_include_html = True

    @staticmethod
    def name() -> str:
        return tr.exporting_cards_in_plain_text()

    def export(self, mw: aqt.main.AnkiQt, options: ExportOptions) -> None:
        options = gui_hooks.exporter_will_export(options, self)
        parent = _export_parent(mw, options)

        def on_success(count: int) -> None:
            gui_hooks.exporter_did_export(options, self)
            _show_exported_tooltip(mw, options, tr.exporting_card_exported(count=count))

        QueryOp(
            parent=parent,
            op=lambda col: col.export_card_csv(
                out_path=options.out_path,
                limit=options.limit,
                with_html=options.include_html,
            ),
            success=on_success,
        ).with_backend_progress(export_progress_update).run_in_background()


def export_progress_update(progress: Progress, update: ProgressUpdate) -> None:
    if not progress.HasField("exporting"):
        return
    update.label = progress.exporting
    if update.user_wants_abort:
        update.abort = True
